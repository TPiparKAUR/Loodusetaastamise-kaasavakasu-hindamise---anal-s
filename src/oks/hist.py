"""Väärtuste jaotuse (histogrammi) vahemikud ja pikslite jaotamine vahemikesse.

Jaotus arvutatakse samal läbikäigul nagu plokisummad (``aggregate``): iga piksel loetakse
tema baaskaardi klassi (detailne kood) ja väärtuse vahemiku kaupa. Klassidest saab hiljem
liita ökosüsteemi/alamökosüsteemi ja seisundi tasemele.

Vahemikud valitakse kihi enda väärtuste põhjal (``choose_spec``):

* ``lut`` – diskreetsed väärtused (skoorid, klassid; kuni ``max_discrete`` erinevat väärtust):
  iga väärtus on oma vahemik, lisaks viimane "muu" vahemik;
* ``linear`` – ``nbins`` võrdse laiusega vahemikku vahemikus ``[lo, hi)``;
* ``sqrt`` – sama ruutjuure skaalal (väga viltuste, mittenegatiivsete jaotuste jaoks).

``linear`` ja ``sqrt`` korral on vahemik 0 alumine ots (``x < lo``) ja viimane ülemine ots
(``x >= hi``). Täpsed nullid loetakse lisaks eraldi (zeroinflated kihid).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import rasterio
from numpy.typing import NDArray
from rasterio.transform import Affine
from rasterio.warp import Resampling, reproject

Kind = Literal["lut", "linear", "sqrt"]


@dataclass(frozen=True)
class HistSpec:
    """Histogrammi vahemike kirjeldus."""

    kind: Kind
    lo: float = 0.0
    hi: float = 1.0
    nbins: int = 40
    values: tuple[float, ...] = ()

    @property
    def n_bins(self) -> int:
        """Vahemike koguarv (``lut``: väärtused + "muu"; muidu: alumine ots + ``nbins`` + ülemine ots)."""
        return len(self.values) + 1 if self.kind == "lut" else self.nbins + 2

    def edges(self) -> list[float]:
        """Regulaarsete vahemike servad väärtuste skaalal (``linear``/``sqrt``); ``lut``: väärtused."""
        if self.kind == "lut":
            return list(self.values)
        if self.kind == "sqrt":
            s = np.linspace(np.sqrt(self.lo), np.sqrt(self.hi), self.nbins + 1)
            return (s**2).tolist()
        return np.linspace(self.lo, self.hi, self.nbins + 1).tolist()

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "lo": self.lo,
            "hi": self.hi,
            "nbins": self.nbins,
            "values": list(self.values),
            "edges": self.edges(),
            "n_bins": self.n_bins,
        }

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> HistSpec:
        return cls(
            kind=d["kind"],  # type: ignore[arg-type]
            lo=float(d["lo"]),  # type: ignore[arg-type]
            hi=float(d["hi"]),  # type: ignore[arg-type]
            nbins=int(d["nbins"]),  # type: ignore[call-overload]
            values=tuple(float(v) for v in d["values"]),  # type: ignore[attr-defined]
        )


def bin_index(x: NDArray[np.float64], spec: HistSpec) -> NDArray[np.int64]:
    """Vahemiku indeks igale väärtusele (``0 .. spec.n_bins - 1``)."""
    if spec.kind == "lut":
        v = np.asarray(spec.values, dtype=np.float64)
        other = v.size
        if v.size and np.all(v == np.floor(v)) and v.max() - v.min() < 70_000:
            vmin = int(v.min())
            table = np.full(int(v.max()) - vmin + 1, other, dtype=np.int64)
            table[(v - vmin).astype(np.int64)] = np.arange(v.size)
            ok = (x >= v.min()) & (x <= v.max()) & (x == np.floor(x))
            pos = np.where(ok, x - vmin, 0).astype(np.int64)
            return np.where(ok, table[pos], other)
        j = np.minimum(np.searchsorted(v, x), max(v.size - 1, 0))
        exact = v[j] == x if v.size else np.zeros(x.shape, dtype=bool)
        return np.where(exact, j, other).astype(np.int64)
    lo, hi = spec.lo, spec.hi
    if spec.kind == "sqrt":
        y = np.sqrt(np.maximum(x, 0.0))
        t = (y - np.sqrt(lo)) / (np.sqrt(hi) - np.sqrt(lo)) * spec.nbins
    else:
        t = (x - lo) / (hi - lo) * spec.nbins
    i = np.clip(np.floor(t).astype(np.int64) + 1, 1, spec.nbins)
    return np.where(x < lo, 0, np.where(x >= hi, spec.nbins + 1, i))


def choose_spec(
    src: Path,
    baas_det: Path,
    lut: NDArray[np.int16],
    invalid: tuple[float, ...] = (),
    max_pixels: int = 8_000_000,
    max_discrete: int = 40,
    nbins: int = 40,
) -> HistSpec:
    """Vali kihile histogrammi vahemikud ruudustiku hõredalt proovitud pikslitest.

    Proov: ``out_shape``-ile vähendatud lugemine (lähima naabriga, ilma pyramiidideta, et
    jaotust ei silutaks), piiratud pikslitega, millel on seisund ja kehtiv väärtus.

    Parameters
    ----------
    src
        Teenuse raster.
    baas_det
        Baaskaardi detailne raster.
    lut
        Klassi otsingutabel (``baas.class_lut``).
    invalid
        Lisaks NoData-le välistatavad väärtused.
    max_pixels
        Proovi suurus.
    max_discrete
        Kuni nii mitme erineva väärtuse korral kasutatakse ``lut`` vahemikke.
    nbins
        Pidevate jaotuste vahemike arv.
    """
    with rasterio.open(src, OVERVIEW_LEVEL="NONE") as ds, rasterio.open(baas_det) as baas:
        f = max(1, int(np.ceil(np.sqrt(ds.width * ds.height / max_pixels))))
        shape = (max(1, ds.height // f), max(1, ds.width // f))
        val = ds.read(1, out_shape=shape, resampling=Resampling.nearest)
        # NoData väärtuste järgi, mitte read_masks()-iga: allavalimisel (out_shape) tuletab GDAL maski
        # pyramiididest, mis ei lange kokku nearest-lugemisega.
        ok = np.ones(shape, dtype=bool)
        if ds.nodata is not None:
            nd = np.asarray(ds.nodata).astype(val.dtype)
            ok = ~np.isnan(val) if np.isnan(nd) else val != nd
        det = np.zeros(shape, dtype=np.uint16)
        reproject(
            source=rasterio.band(baas, 1),
            destination=det,
            dst_transform=ds.transform @ Affine.scale(ds.width / shape[1], ds.height / shape[0]),
            dst_crs=ds.crs,
            resampling=Resampling.nearest,
            src_nodata=0,
            dst_nodata=0,
        )
    if val.dtype.kind == "f":
        ok &= np.isfinite(val)
    if invalid:
        ok &= ~np.isin(val, np.asarray(invalid, dtype=val.dtype))
    ok &= lut[det] >= 0
    x = val[ok].astype(np.float64)
    if x.size == 0:
        return HistSpec("linear", 0.0, 1.0, nbins)
    uniq = np.unique(x)
    if uniq.size <= max_discrete:
        return HistSpec("lut", values=tuple(float(u) for u in uniq))
    lo, hi = (float(q) for q in np.percentile(x, [0.5, 99.5]))
    if not hi > lo:
        lo, hi = float(x.min()), float(x.max())
    if not hi > lo:
        lo, hi = lo - 0.5, hi + 0.5
    med = float(np.median(x))
    heavy = lo >= 0 and hi > 12 * max(med, 1e-12)
    return HistSpec("sqrt" if heavy else "linear", lo, hi, nbins)
