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

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class LayerSpec:
    """Aggregeeritava rastri kirjeldus."""

    id: str
    rel: str
    invalid: tuple[float, ...] = field(default_factory=tuple)


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


def aggregate_layer(
    spec: LayerSpec, src: Path, baas_det: Path, lut: NDArray[np.int16], n_classes: int
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
            ok = ds.read_masks(1, window=win) > 0
            if val.dtype.kind == "f":
                ok &= np.isfinite(val)
            if invalid.size:
                ok &= ~np.isin(val, invalid.astype(val.dtype))
            idx = lut[_baas_chunk(baas, ds, r0, r1, same_grid)]
            ok &= idx >= 0
            if not ok.any():
                continue
            col = np.broadcast_to(col_inv, val.shape)[ok].astype(np.int64)
            key = idx[ok].astype(np.int64) + n_classes * col
            x = val[ok].astype(np.float64)
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
