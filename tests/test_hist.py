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


def test_distributions_aggregate_to_units_and_match_cells(tmp_path: Path) -> None:
    import json

    import polars as pl

    from oks import analysis, stats

    used = pl.DataFrame(
        [(0, 10110, 10100, 1, 1), (1, 10130, 10100, 1, 2), (2, 10141, 10100, 1, 3)],
        schema=["idx", "kood", "alam_kood", "okosusteem_kood", "uld"],
        orient="row",
    ).with_columns(pl.col("idx").cast(pl.UInt32))
    u = stats.make_units(used)
    spec = hist.HistSpec("lut", values=(0.0, 1.0))  # n_bins = 3, nullide veerg = indeks 3
    # klass 0 = hea, 1 = keskmine, 2 = vilets
    h = pl.DataFrame(
        {"cls": [0, 0, 1, 2, 2, 2], "bin": [0, 1, 1, 0, 1, 3], "n": [5, 7, 4, 2, 9, 2]},
        schema={"cls": pl.Int16, "bin": pl.Int16, "n": pl.Int64},
    )
    h.write_parquet(tmp_path / "x__hist.parquet")
    (tmp_path / "x__hist.json").write_text(json.dumps(spec.to_dict()))
    dist, specs = analysis.distributions(u, ["x"], tmp_path)
    eco = dist.filter(pl.col("unit_level") == "okosusteem")
    vilets = eco.filter(pl.col("state") == "vilets").sort("bin")
    assert vilets["bin"].to_list() == [0, 1, 3] and vilets["n"].to_list() == [2, 9, 2]
    assert set(dist["unit_level"].unique()) == {"okosusteem", "alam"}
    base = {
        "layer_id": ["x"] * 3,
        "state": ["hea", "keskmine", "vilets"],
        "n": [12, 4, 11],
    }  # nullid ei kuulu summasse
    cells = pl.concat(
        [
            pl.DataFrame({**base, "unit_level": ["okosusteem"] * 3, "unit_code": [1] * 3}),
            pl.DataFrame({**base, "unit_level": ["alam"] * 3, "unit_code": [10100] * 3}),
        ]
    )
    assert analysis.check_distributions(dist, specs, cells).is_empty()
    cells_bad = cells.with_columns(
        pl.when(pl.col("state") == "hea").then(13).otherwise(pl.col("n")).alias("n")
    )
    assert analysis.check_distributions(dist, specs, cells_bad).height >= 1


def test_choose_spec_ignores_nodata_even_with_overviews(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    """NoData (65535) ei tohi sattuda vahemiku valikusse ka siis, kui failil on pyramiidid."""
    from rasterio.enums import Resampling

    rng = np.random.default_rng(1)
    arr = rng.integers(0, 300, (200, 200)).astype(np.uint16)
    arr[::2, ::2] = 65535  # NoData ruudumustris: pyramiidi keskmistatud mask ei lange andmetega kokku
    arr[:, 150:] = 65535
    src = tmp_path / "ovr.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, 65535)
    with rasterio.open(src, "r+") as ds:
        ds.build_overviews([2, 4], Resampling.average)
    spec = hist.choose_spec(src, baas, lut, max_pixels=2_000)
    assert spec.kind in ("linear", "sqrt") and spec.hi < 400
