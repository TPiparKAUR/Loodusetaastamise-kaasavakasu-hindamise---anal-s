"""Aggregeerimise testid tehisrastritega (teada vastus)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from oks import aggregate

N_CLASSES = 2


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
    det = np.zeros((400, 400), dtype=np.uint16)  # 5 m, 2 km x 2 km
    det[:, :200] = 10110  # lääne pool: hea
    det[:, 200:] = 10141  # ida pool: vilets
    p = tmp_path / "baas.tif"
    _write(p, det, 5.0, 400_000.0, 6_501_000.0, 0)
    return p


@pytest.fixture
def lut() -> np.ndarray:
    lut = np.full(65536, -1, dtype=np.int16)
    lut[10110] = 0
    lut[10141] = 1
    return lut


def _by_key(df):  # noqa: ANN001, ANN202
    return {(r["e_km"], r["n_km"], r["cls"]): r for r in df.iter_rows(named=True)}


def test_aligned_10m_layer_sums(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    rows = np.arange(200, dtype=np.float32)[:, None] * np.ones((1, 200), dtype=np.float32)
    src = tmp_path / "svc.tif"
    _write(src, rows, 10.0, 400_000.0, 6_501_000.0, -9999.0)
    df = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, N_CLASSES)
    d = _by_key(df)
    assert len(d) == 4  # 2 plokki ida-läänes x 2 põhja-lõunas
    top_west = d[(400, 6500, 0)]
    assert top_west["n"] == 100 * 100
    assert top_west["sum"] == pytest.approx(100 * sum(range(100)))
    assert top_west["sumsq"] == pytest.approx(100 * sum(r * r for r in range(100)))
    bottom_east = d[(401, 6499, 1)]
    assert bottom_east["sum"] == pytest.approx(100 * sum(range(100, 200)))
    assert df["n"].sum() == 200 * 200


def test_nodata_and_extra_invalid_are_excluded(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    arr = np.full((200, 200), 5.0, dtype=np.float32)
    arr[0, 0] = -9999.0  # deklareeritud NoData
    arr[0, 1] = np.nan
    arr[0, 2] = 255.0  # sentinel, antud invalid-i kaudu
    src = tmp_path / "svc.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, -9999.0)
    df = aggregate.aggregate_layer(
        aggregate.LayerSpec("t", "t.tif", invalid=(255.0,)), src, baas, lut, N_CLASSES
    )
    assert df["n"].sum() == 200 * 200 - 3
    assert df["sum"].sum() == pytest.approx(5.0 * (200 * 200 - 3))


def test_same_grid_5m_layer(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    arr = np.ones((400, 400), dtype=np.uint8)
    src = tmp_path / "svc5.tif"
    _write(src, arr, 5.0, 400_000.0, 6_501_000.0, 255.0)
    df = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, N_CLASSES)
    assert df["n"].sum() == 400 * 400
    assert set(df["cls"].to_list()) == {0, 1}


def test_shifted_grid_uses_nearest_class_and_keeps_totals(
    tmp_path: Path, baas: Path, lut: np.ndarray
) -> None:
    arr = np.full((190, 190), 2.0, dtype=np.float32)
    src = tmp_path / "shifted.tif"
    _write(src, arr, 10.0, 400_003.0, 6_500_997.0, -9999.0)  # nihutatud 3 m
    df = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, N_CLASSES)
    assert df["n"].sum() == 190 * 190
    assert df["sum"].sum() == pytest.approx(2.0 * 190 * 190)
    west = df.filter(df["cls"] == 0)["n"].sum()
    east = df.filter(df["cls"] == 1)["n"].sum()
    assert west + east == 190 * 190
    # piir 401000: x-keskpunktid 400008..400998 (<401000) -> 100 veergu läände
    assert west == 100 * 190


def test_pixels_without_state_are_dropped(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    lut2 = lut.copy()
    lut2[10141] = -1  # ida pool ilma seisundita
    arr = np.ones((200, 200), dtype=np.float32)
    src = tmp_path / "svc.tif"
    _write(src, arr, 10.0, 400_000.0, 6_501_000.0, -9999.0)
    df = aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut2, N_CLASSES)
    assert set(df["cls"].to_list()) == {0}
    assert df["n"].sum() == 100 * 200


def test_rejects_wrong_crs(tmp_path: Path, baas: Path, lut: np.ndarray) -> None:
    src = tmp_path / "bad.tif"
    with rasterio.open(
        src,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(0, 0, 0.1, 0.1),
    ) as ds:
        ds.write(np.ones((10, 10), dtype=np.float32), 1)
    with pytest.raises(ValueError, match="CRS"):
        aggregate.aggregate_layer(aggregate.LayerSpec("t", "t.tif"), src, baas, lut, N_CLASSES)
