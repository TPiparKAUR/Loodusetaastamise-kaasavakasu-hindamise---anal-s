"""Teenuse raster -> 1 km plokkide tabel ``(plokk, detailne klass)``: n, Σx, Σx².

Iga teenuse raster loetakse ploki-ridade kaupa (mälu on piiratud). Baaskaart
(``OS_det_seisund_det``) taasproovitakse teenuse ruudustikule lähima naabri meetodil,
nii et teenuse väärtusi ei interpoleerita. Ploki kuuluvus määratakse piksli keskpunkti
järgi EPSG:3301 1000 m ruudustikus.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import polars as pl
import rasterio
from numpy.typing import NDArray
from rasterio.transform import Affine
from rasterio.warp import Resampling, reproject
from rasterio.windows import Window

from . import config
from .hist import HistSpec, bin_index

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LayerSpec:
    """Aggregeeritava rastri kirjeldus."""

    id: str
    rel: str
    invalid: tuple[float, ...] = field(default_factory=tuple)
    zero_values: tuple[float, ...] = field(default_factory=tuple)


#: Veerud klassitabelis ``cls_stats`` (kujuga ``(klasse, N_CLS_STATS)``).
CLS_STATS = ("n_total", "n_valid", "n_zero", "n_pos", "n_neg", "sum", "sumsq")
N_CLS_STATS = len(CLS_STATS)


def validity(
    val: NDArray[np.generic],
    mask: NDArray[np.bool_],
    invalid: NDArray[np.float64],
    zero_values: tuple[float, ...],
) -> tuple[NDArray[np.bool_], NDArray[np.generic]]:
    """Kehtivate pikslite mask ja väärtused (``zero_values`` loetakse kehtivaks nulliks).

    Parameters
    ----------
    val
        Rastri väärtused.
    mask
        GDAL-i kehtivuse mask (``read_masks > 0``); NoData väärtuse pikslid on ``False``.
    invalid
        Lisaks välistatavad sentinel-väärtused.
    zero_values
        Väärtused, mis tähendavad „teenust ei ole“ ja loetakse nulliks (ka siis, kui need on NoData).

    Returns
    -------
    tuple[NDArray[np.bool_], NDArray[np.generic]]
        ``ok`` ja väärtused, kus ``zero_values`` on asendatud nulliga.
    """
    ok = mask.copy()
    if val.dtype.kind == "f":
        ok &= np.isfinite(val)
    if invalid.size:
        ok &= ~np.isin(val, invalid.astype(val.dtype))
    if zero_values:
        zero = np.isin(val, np.asarray(zero_values, dtype=val.dtype))
        ok |= zero
        if val.dtype.kind == "f":
            ok &= np.isfinite(val) | zero
        val = np.where(zero, np.zeros((), dtype=val.dtype), val)
    return ok, val


def _row_runs(ds: rasterio.DatasetReader) -> list[tuple[int, int, int]]:
    """Jaga rastri read 1 km ploki-ridadeks: ``(r0, r1, ploki_rida_n_km)``."""
    t = ds.transform
    cy = t.f + (np.arange(ds.height) + 0.5) * t.e
    brow = np.floor(cy / config.BLOCK_M).astype(np.int64)
    edges = np.flatnonzero(np.diff(brow)) + 1
    starts = np.concatenate(([0], edges))
    ends = np.concatenate((edges, [ds.height]))
    return [(int(a), int(b), int(brow[a])) for a, b in zip(starts, ends, strict=True)]


def _baas_chunk(
    baas: rasterio.DatasetReader, ds: rasterio.DatasetReader, r0: int, r1: int, same_grid: bool
) -> NDArray[np.uint16]:
    """Baaskaardi koodid teenuse rastri ridadele ``r0:r1``."""
    win = Window(0, r0, ds.width, r1 - r0)
    if same_grid:
        return baas.read(1, window=win)
    dst = np.zeros((r1 - r0, ds.width), dtype=np.uint16)
    reproject(
        source=rasterio.band(baas, 1),
        destination=dst,
        dst_transform=ds.transform @ Affine.translation(0, r0),
        dst_crs=ds.crs,
        resampling=Resampling.nearest,
        src_nodata=0,
        dst_nodata=0,
    )
    return dst


def _accumulate_classes(
    codes: NDArray[np.uint16],
    val: NDArray[np.generic],
    ok: NDArray[np.bool_],
    lut_all: NDArray[np.int16],
    cls_stats: NDArray[np.float64],
) -> None:
    """Lisa ühe ploki-rea klassistatistika (kõik baaskaardi klassid) massiivi ``cls_stats``."""
    n_cls = cls_stats.shape[0]
    ci = lut_all[codes].astype(np.int64)
    inside = ci >= 0
    if not inside.any():
        return
    cls_stats[:, 0] += np.bincount(ci[inside], minlength=n_cls)
    sel = inside & ok
    if not sel.any():
        return
    c = ci[sel]
    x = val[sel].astype(np.float64)
    cls_stats[:, 1] += np.bincount(c, minlength=n_cls)
    cls_stats[:, 2] += np.bincount(c[x == 0], minlength=n_cls)
    cls_stats[:, 3] += np.bincount(c[x > 0], minlength=n_cls)
    cls_stats[:, 4] += np.bincount(c[x < 0], minlength=n_cls)
    cls_stats[:, 5] += np.bincount(c, weights=x, minlength=n_cls)
    cls_stats[:, 6] += np.bincount(c, weights=x * x, minlength=n_cls)


def aggregate_layer(
    spec: LayerSpec,
    src: Path,
    baas_det: Path,
    lut: NDArray[np.int16],
    n_classes: int,
    hist: HistSpec | None = None,
    hist_counts: NDArray[np.int64] | None = None,
    lut_all: NDArray[np.int16] | None = None,
    cls_stats: NDArray[np.float64] | None = None,
) -> pl.DataFrame:
    """Koonda üks teenuse raster plokkide kaupa.

    Parameters
    ----------
    spec
        Kihi kirjeldus (``invalid`` = lisaks NoData-le välistatavad sentinel-väärtused).
    src
        Teenuse rastri kohalik fail.
    baas_det
        ``OS_det_seisund_det_2022_5m.tif`` kohalik fail.
    lut
        Tulemus ``baas.class_lut``-ist.
    n_classes
        Klasside arv (``lut`` max väärtus + 1).
    hist, hist_counts
        Valikuline jaotus: ``hist`` on vahemikud (``hist.choose_spec``) ja ``hist_counts`` täidetav
        massiiv kujuga ``(n_classes, hist.n_bins + 1)``; viimane veerg on täpsete nullide arv.
    lut_all, cls_stats
        Valikuline klassitabel KÕIGI baaskaardi klasside kohta (ka seisundita ja rannik): ``lut_all`` on
        ``kood -> klassiindeks`` (``-1`` = klassita) ja ``cls_stats`` täidetav massiiv kujuga
        ``(klasse, N_CLS_STATS)`` (veerud ``CLS_STATS``): pikslid kokku, kehtivad, nullid, positiivsed,
        negatiivsed, Σx, Σx².

    Returns
    -------
    pl.DataFrame
        Veerud ``e_km, n_km`` (ploki lääne-/lõunanurk km-des), ``cls`` (klassiindeks),
        ``n`` (pikslite arv), ``sum``, ``sumsq`` (Float64).
    """
    parts: list[pl.DataFrame] = []
    with rasterio.open(src) as ds, rasterio.open(baas_det) as baas:
        if ds.crs is None or ds.crs.to_epsg() != 3301:
            raise ValueError(f"{spec.id}: CRS ei ole EPSG:3301 ({ds.crs})")
        if ds.transform.e >= 0 or ds.transform.b != 0 or ds.transform.d != 0:
            raise ValueError(f"{spec.id}: ootamatu (mitte põhja-suunaline) transform")
        t = ds.transform
        cx = t.c + (np.arange(ds.width) + 0.5) * t.a
        bcol = np.floor(cx / config.BLOCK_M).astype(np.int64)
        col_vals, col_inv = np.unique(bcol, return_inverse=True)
        same_grid = ds.transform == baas.transform and ds.shape == baas.shape
        invalid = np.asarray(spec.invalid, dtype=np.float64)
        for r0, r1, brow in _row_runs(ds):
            win = Window(0, r0, ds.width, r1 - r0)
            val = ds.read(1, window=win)
            ok, val = validity(val, ds.read_masks(1, window=win) > 0, invalid, spec.zero_values)
            codes = _baas_chunk(baas, ds, r0, r1, same_grid)
            if lut_all is not None and cls_stats is not None:
                _accumulate_classes(codes, val, ok, lut_all, cls_stats)
            idx = lut[codes]
            ok &= idx >= 0
            if not ok.any():
                continue
            col = np.broadcast_to(col_inv, val.shape)[ok].astype(np.int64)
            key = idx[ok].astype(np.int64) + n_classes * col
            x = val[ok].astype(np.float64)
            if hist is not None and hist_counts is not None:
                cls_ok = idx[ok].astype(np.int64)
                nb = hist.n_bins
                hist_counts[:, :nb] += np.bincount(
                    cls_ok * nb + bin_index(x, hist), minlength=n_classes * nb
                ).reshape(n_classes, nb)
                zero = x == 0
                if zero.any():
                    hist_counts[:, nb] += np.bincount(cls_ok[zero], minlength=n_classes)
            size = n_classes * col_vals.size
            n = np.bincount(key, minlength=size)
            s1 = np.bincount(key, weights=x, minlength=size)
            s2 = np.bincount(key, weights=x * x, minlength=size)
            nz = np.flatnonzero(n)
            parts.append(
                pl.DataFrame(
                    {
                        "e_km": col_vals[nz // n_classes].astype(np.int16),
                        "n_km": np.full(nz.size, brow, dtype=np.int16),
                        "cls": (nz % n_classes).astype(np.int16),
                        "n": n[nz].astype(np.int32),
                        "sum": s1[nz],
                        "sumsq": s2[nz],
                    }
                )
            )
    if not parts:
        return pl.DataFrame(
            schema={
                "e_km": pl.Int16,
                "n_km": pl.Int16,
                "cls": pl.Int16,
                "n": pl.Int32,
                "sum": pl.Float64,
                "sumsq": pl.Float64,
            }
        )
    return pl.concat(parts)
