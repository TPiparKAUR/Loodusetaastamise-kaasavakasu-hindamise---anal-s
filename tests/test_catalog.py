"""Kataloogi, inventuuri ja eksporditööriistade testid."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from oks import catalog, export, fields, inventory


def _meta(tmp_path: Path) -> Path:
    rows = [
        {
            "layer_name": "Foo_2022_10m",
            "title": "Foo 2022 10 m",
            "title_unchangeable": "Foo",
            "layer_group": "loodusannid_taiendavad",
            "properties": "biofüüsikalinefüüsikaline",
            "data_type": "Pidev",
            "spatial_resolution": 10,
            "eval": True,
            "comments": None,
            "abstract": "x",
            "data_origin": "ELME2",
        },
        {
            "layer_name": "bar_2022",
            "title": "Bar",
            "title_unchangeable": "Bar",
            "layer_group": "puhverdavad_teenused",
            "properties": "rahaline",
            "data_type": None,
            "spatial_resolution": None,
            "eval": True,
            "comments": "märkus",
            "abstract": "y",
            "data_origin": "ELME2",
        },
        {
            "layer_name": "OS_det_seisund_det_2022_5m",
            "title": "Baas",
            "title_unchangeable": "Baas",
            "layer_group": "baaskaart",
            "properties": "ökosüsteemide andmestik",
            "data_type": "Nominaal",
            "spatial_resolution": 5,
            "eval": True,
            "comments": None,
            "abstract": "z",
            "data_origin": "ELME2",
        },
        {
            "layer_name": "ignored",
            "title": "I",
            "title_unchangeable": "I",
            "layer_group": "loodusannid",
            "properties": "muu",
            "data_type": None,
            "spatial_resolution": None,
            "eval": False,
            "comments": None,
            "abstract": "",
            "data_origin": None,
        },
    ]
    p = tmp_path / "meta.csv"
    pl.DataFrame(rows).write_csv(p)
    return p


def _inv(tmp_path: Path) -> Path:
    p = tmp_path / "inv.csv"
    pl.DataFrame(
        {
            "tee": [
                "Loodusannid/Foo_2022_10m.tif",
                "Loodusannid/Foo_2022_10m.tif.aux.xml",
                "Puhverdavad_teenused/bar_2022.gpkg",
                "x/unmatched.tif",
            ],
            "suurus_tekst": ["1 MB"] * 4,
            "suurus_b": [1] * 4,
            "muudetud": ["2026"] * 4,
        }
    ).write_csv(p)
    return p


def test_catalogue_matches_files_and_types(tmp_path: Path) -> None:
    cat = catalog.build_catalogue(_meta(tmp_path), _inv(tmp_path))
    foo = cat.filter(pl.col("layer_name") == "Foo_2022_10m").row(0, named=True)
    assert foo["tyyp"] == "raster"
    assert foo["fail"] == "Loodusannid/Foo_2022_10m.tif"
    assert foo["grupp_kood"] == "loodusannid"  # "_taiendavad" eemaldatud
    assert foo["omadus"] == "biofüüsikaline"  # allika kirjaviga parandatud
    bar = cat.filter(pl.col("layer_name") == "bar_2022").row(0, named=True)
    assert bar["tyyp"] == "vektor"
    assert cat.filter(pl.col("layer_name") == "ignored")["tyyp"].item() == "puudub"


def test_evaluated_excludes_basemap_and_eval_false(tmp_path: Path) -> None:
    cat = catalog.build_catalogue(_meta(tmp_path), _inv(tmp_path))
    assert sorted(catalog.evaluated(cat)["layer_name"].to_list()) == ["Foo_2022_10m", "bar_2022"]


def test_units_keys_are_lowercase_ids() -> None:
    assert all(k == k.lower() for k in catalog.UNITS)


@pytest.mark.parametrize(
    ("txt", "expected"),
    [
        ("492.4 MB", int(492.4 * 1024**2)),
        ("1.8 GB", int(1.8 * 1024**3)),
        ("125.2 KB", int(125.2 * 1024)),
        ("-", None),
    ],
)
def test_parse_size(txt: str, expected: int | None) -> None:
    assert inventory.parse_size(txt) == expected


def test_export_rounding() -> None:
    assert export._r(float("nan")) is None
    assert export._r(math.inf) is None
    assert export._r(0.0) == 0
    assert export._r(123456.789) == 123460
    assert export._r(0.000123456) == pytest.approx(0.00012346)
    assert export._r(True) is True
    assert export._r(None) is None


def test_value_class_to_number() -> None:
    out = fields.value_class_to_number(np.array(["A", "B", "C", "D", "X", None], dtype=object))
    assert out[:4].tolist() == [1.0, 2.0, 3.0, 4.0]
    assert np.isnan(out[4]) and np.isnan(out[5])
