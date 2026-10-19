"""Jämedate ruudustike (930 m rastrid, 1 km vektorruudud) analüüs segumudeliga.

Kui teenuse ruut on suurem kui seisundiüksus, koosneb ruut mitmest ökosüsteemist ja
seisundist ning ruutu ei saa ühele seisundile omistada. Eeldades, et ruudu väärtus on
klasside pindalaosade lineaarne segu::

    y_c = Σ_k f_ck · β_k + ε_c,   k = ökosüsteem × seisund (12 klassi) + "muu" (13. klass)

hinnatakse β_k vähimruutudega (ilma vabaliikmeta; Σ_k f_ck = 1). Seisundimuutus
ökosüsteemis e on Δ = β_(e,parem) - β_(e,halvem). Ebakindlus: klastrite (10 km) bootstrap
normaalvõrrandite tasemel (X'X ja X'y klastri kaupa).

Piirang: mudel eeldab, et pikslite väärtus sõltub ainult (ökosüsteem, seisund)-klassist.
Tulemus on **uuriv** ja kandub üle ainult siis, kui see eeldus on kihi puhul mõistlik.
"""

from __future__ import annotations

import contextlib
import logging
from pathlib import Path

import numpy as np
import polars as pl
import rasterio
from numpy.typing import NDArray

from . import stats

log = logging.getLogger(__name__)

N_ECO, N_COLS = 4, 13  # 4 ökosüsteemi x 3 seisundit + "muu"


def composition(
    baas_det: Path,
    lut: NDArray[np.int16],
    cls_eco: NDArray[np.int32],
    cls_state: NDArray[np.int8],
    x0: float,
    y0: float,
    res: float,
    shape: tuple[int, int],
) -> NDArray[np.float64]:
    """Baaskaardi klasside pikslite arv ``res`` m ruudustiku igas ruudus.

    Parameters
    ----------
    baas_det
        ``OS_det_seisund_det`` 5 m raster.
    lut, cls_eco, cls_state
        Klassi otsingutabel ja kaardistused (``stats.make_units``).
    x0, y0
        Ruudustiku vasak ülemine nurk (EPSG:3301).
    res
        Ruudu külg meetrites.
    shape
        ``(rida, veerg)``.

    Returns
    -------
    NDArray[np.float64]
        ``(rida, veerg, 13)``: veerg ``eco*3 + state`` või ``12`` ("muu"; kehtiv, kuid ilma seisundita).
    """
    rows, cols = shape
    out = np.zeros((rows, cols, N_COLS))
    col_of = np.empty(0)
    with rasterio.open(baas_det) as ds:
        t = ds.transform
        cx = t.c + (np.arange(ds.width) + 0.5) * t.a
        col_of = np.floor((cx - x0) / res).astype(np.int64)
        cy = t.f + (np.arange(ds.height) + 0.5) * t.e
        row_of = np.floor((y0 - cy) / res).astype(np.int64)
        valid_col = (col_of >= 0) & (col_of < cols)
        # klass -> veerg (0..12)
        cls_col = np.where(cls_state >= 0, cls_eco * 3 + cls_state, 12).astype(np.int64)
        for r in range(rows):
            idx = np.flatnonzero(row_of == r)
            if idx.size == 0:
                continue
            win = rasterio.windows.Window(0, int(idx[0]), ds.width, int(idx.size))
            det = ds.read(1, window=win)
            ci = lut[det]
            col = np.where(ci >= 0, cls_col[np.maximum(ci, 0)], np.where(det > 0, 12, -1))
            ok = (col >= 0) & valid_col[None, :]
            key = np.broadcast_to(col_of, det.shape)[ok] * N_COLS + col[ok]
            out[r] = np.bincount(key, minlength=cols * N_COLS).reshape(cols, N_COLS)
    return out


def fit_mixing(
    y: NDArray[np.float64],
    counts: NDArray[np.float64],
    cluster: NDArray[np.int64],
    n_clusters: int,
    W: NDArray[np.float64],
    min_share_cells: int = 30,
) -> dict[str, NDArray[np.float64]]:
    """Hinda segumudel ja bootstrap-jaotus.

    Parameters
    ----------
    y
        Ruutude väärtused (``n``).
    counts
        Ruutude klasside pikslite arvud (``n`` x 13).
    cluster
        Ruutude klastri indeks.
    n_clusters
        Klastrite koguarv.
    W
        Bootstrap-kaalud (``B`` x ``n_clusters``).
    min_share_cells
        Veerg loetakse hinnatavaks, kui vähemalt nii mitmes ruudus on tema osa >= 10 %.

    Returns
    -------
    dict[str, NDArray[np.float64]]
        ``beta`` (13,), ``boot`` (B, 13), ``cells_ok`` (13,) ruutude arv, kus klassi osa >= 10 %.
    """
    tot = counts.sum(1, keepdims=True)
    f = np.divide(counts, tot, out=np.zeros_like(counts), where=tot > 0)
    ok = np.isfinite(y) & (tot[:, 0] > 0)
    f, yy, cl = f[ok], y[ok], cluster[ok]
    cells_ok = (f >= 0.10).sum(0).astype(np.float64)
    k = f.shape[1]
    xtx = np.zeros((n_clusters, k, k))
    xty = np.zeros((n_clusters, k))
    np.add.at(xtx, cl, f[:, :, None] * f[:, None, :])
    np.add.at(xty, cl, f * yy[:, None])
    keep = cells_ok >= min_share_cells

    def solve(a: NDArray[np.float64], b: NDArray[np.float64]) -> NDArray[np.float64]:
        beta = np.full(k, np.nan)
        sub = np.flatnonzero(keep)
        if sub.size == 0:
            return beta
        aa = a[np.ix_(sub, sub)] + 1e-9 * np.eye(sub.size)
        with contextlib.suppress(np.linalg.LinAlgError):
            beta[sub] = np.linalg.solve(aa, b[sub])
        return beta

    beta = solve(xtx.sum(0), xty.sum(0))
    A = np.tensordot(W, xtx, axes=(1, 0))  # (B, k, k)
    Bv = np.tensordot(W, xty, axes=(1, 0))  # (B, k)
    boot = np.stack([solve(A[i], Bv[i]) for i in range(W.shape[0])])
    return {"beta": beta, "boot": boot, "cells_ok": cells_ok}


def pair_table(
    res: dict[str, NDArray[np.float64]], eco_codes: tuple[int, ...], layer_id: str
) -> pl.DataFrame:
    """Ökosüsteemi sisese seisundimuutuse tabel (Δ, CI, p) segumudeli tulemusest."""
    rows: list[dict[str, object]] = []
    beta, boot = res["beta"], res["boot"]
    for ei, code in enumerate(eco_codes):
        for pi, (a, b) in enumerate(stats.PAIRS):
            ia, ib = ei * 3 + a, ei * 3 + b
            d = beta[ib] - beta[ia]
            bd = boot[:, ib] - boot[:, ia]
            lo, hi, p = stats._boot_summary(np.array([d]), bd[:, None])
            rows.append(
                {
                    "layer_id": layer_id,
                    "unit_level": "okosusteem",
                    "unit_code": int(code),
                    "pair": stats.PAIR_NAMES[pi],
                    "mean_a": beta[ia],
                    "mean_b": beta[ib],
                    "delta_m": d,
                    "rel_m": d / abs(beta[ia]) if np.isfinite(beta[ia]) and abs(beta[ia]) > 1e-12 else np.nan,
                    "ci_m_lo": lo[0],
                    "ci_m_hi": hi[0],
                    "p_m": p[0],
                    "cells_a": int(res["cells_ok"][ia]),
                    "cells_b": int(res["cells_ok"][ib]),
                }
            )
    return pl.DataFrame(rows)
