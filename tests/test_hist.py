"""Jaotuse (histogrammi) testid."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from oks import aggregate, hist


def _write(path: Path, arr: np.ndarray, res: float, x0: float, y0: float, nodata: float | None) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=arr.shape[0],
        width=arr.shape[1],
        count=1,
        dtype=arr.dtype,
        crs="EPSG:3301",
        transform=from_origin(x0, y0, res, res),
        nodata=nodata,
    ) as ds:
        ds.write(arr, 1)


@pytest.fixture
def baas(tmp_path: Path) -> Path:
    det = np.zeros((400, 400), dtype=np.uint16)
    det[:, :200] = 10110  # lääs: hea (klass 0)
    det[:, 200:] = 10141  # ida: vilets (klass 1)
    p = tmp_path / "baas.tif"
    _write(p, det, 5.0, 400_000.0, 6_501_000.0, 0)
    return p


@pytest.fixture
def lut() -> np.ndarray:
    lut = np.full(65536, -1, dtype=np.int16)
    lut[10110], lut[10141] = 0, 1
    return lut


def test_bin_index_linear_edges() -> None:
    spec = hist.HistSpec("linear", 0.0, 10.0, 5)
    x = np.array([-1.0, 0.0, 0.5, 1.99, 2.0, 5.0, 9.99, 10.0, 100.0])
    assert hist.bin_index(x, spec).tolist() == [0, 1, 1, 1, 2, 3, 5, 6, 6]
    assert spec.n_bins == 7
    assert spec.edges() == pytest.approx([0, 2, 4, 6, 8, 10])


def test_bin_index_sqrt_resolves_small_values() -> None:
    spec = hist.HistSpec("sqrt", 0.0, 100.0, 10)
    b = hist.bin_index(np.array([0.0, 0.5, 1.0, 4.0, 100.0]), spec)
    assert b.tolist() == [1, 1, 2, 3, 11]
    assert spec.edges()[1] == pytest.approx(1.0)  # sqrt-skaala esimene serv = 1^2


def test_bin_index_lut_exact_values_and_other() -> None:
    spec = hist.HistSpec("lut", values=(1.0, 2.0, 3.0))
    assert hist.bin_index(np.array([1.0, 2.0, 3.0, 7.0, 2.5]), spec).tolist() == [0, 1, 2, 3, 3]
    nonint = hist.HistSpec("lut", values=(0.5, 2.5))
    assert hist.bin_index(np.array([0.5, 2.5, 1.0]), nonint).tolist() == [0, 1, 2]


def test_spec_roundtrip() -> None:
    spec = hist.HistSpec("sqrt", 0.0, 50.0, 20)
    assert hist.HistSpec.from_dict(spec.to_dict()) == spec


def test_choose_spec_discrete_and_continuous(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    disc = tmp_path / "disc.tif"
    _write(
        disc, (np.arange(200 * 200).reshape(200, 200) % 4).astype(np.uint8), 10.0, 400_000.0, 6_501_000.0, 255
    )
    s = hist.choose_spec(disc, baas, lut)
    assert s.kind == "lut" and s.values == (0.0, 1.0, 2.0, 3.0)
    cont = tmp_path / "cont.tif"
    rng = np.random.default_rng(0)
    _write(cont, rng.normal(50, 5, (200, 200)).astype(np.float32), 10.0, 400_000.0, 6_501_000.0, -9999.0)
    s2 = hist.choose_spec(cont, baas, lut)
    assert s2.kind == "linear" and 35 < s2.lo < 45 and 55 < s2.hi < 65
    skew = tmp_path / "skew.tif"
    _write(
        skew, rng.exponential(1.0, (200, 200)).astype(np.float32) ** 3, 10.0, 400_000.0, 6_501_000.0, -9999.0
    )
    assert hist.choose_spec(skew, baas, lut).kind == "sqrt"


def test_histogram_counts_match_block_table(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    arr = np.zeros((200, 200), dtype=np.float32)
    arr[:, :100] = 1.0  # lääs: väärtus 1
    arr[:, 100:] = 3.0  # ida: väärtus 3
    arr[0, :10] = 0.0  # 10 täpset nulli läänepoolses osas
    src = tmp_path / "svc.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, -9999.0)
    spec = hist.HistSpec("lut", values=(0.0, 1.0, 3.0))
    counts = np.zeros((2, spec.n_bins + 1), dtype=np.int64)
    df = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, 2, spec, counts)
    # klass 0 (hea, lääs): 10 nulli, 100*200-10 ühte; klass 1 (vilets, ida): 100*200 kolme
    assert counts[0].tolist() == [10, 100 * 200 - 10, 0, 0, 10]
    assert counts[1].tolist() == [0, 0, 100 * 200, 0, 0]
    # histogrammi koguarv klassis = ploki-tabeli pikslite arv klassis
    for c in (0, 1):
        assert counts[c, : spec.n_bins].sum() == df.filter(df["cls"] == c)["n"].cast(int).sum()
