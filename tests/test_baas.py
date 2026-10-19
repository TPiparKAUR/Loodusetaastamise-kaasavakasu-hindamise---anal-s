"""Baaskaardi klassinimede ja seisundi kaardistuse testid."""

from __future__ import annotations

import polars as pl
import pytest

from oks import baas


@pytest.mark.parametrize(
    ("nimi", "oodatud"),
    [
        ("1630* rannaniidud A", ("1630* rannaniidud", "A")),
        ("6410 sinihelmikaniidud  D1", ("6410 sinihelmikaniidud", "D1")),
        ("Lammisoo A2", ("Lammisoo", "A2")),
        ("Salumets A-C", ("Salumets", "A-C")),
        ("Madalsoo seisundita", ("Madalsoo", "seisundita")),
        ("Muu (metsa)kooslus (andmed puudulikud) A-B", ("Muu (metsa)kooslus (andmed puudulikud)", "A-B")),
        ("Veekogud seisundita", ("Veekogud", "seisundita")),
    ],
)
def test_split_class_name(nimi: str, oodatud: tuple[str, str]) -> None:
    assert baas.split_class_name(nimi) == oodatud


def test_split_class_name_raises_without_state() -> None:
    with pytest.raises(ValueError):
        baas.split_class_name("Kummaline nimi")


def _classes() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "kood": [10110, 10130, 10141, 60400],
            "nimi": ["x A", "x C", "x D1", "Veekogud seisundita"],
            "tuup": ["x", "x", "x", "Veekogud"],
            "seisund_algne": ["A", "C", "D1", "seisundita"],
            "okosusteem_kood": [1, 1, 1, 6],
            "alam_kood": [10100, 10100, 10100, 60400],
        },
        schema_overrides={"kood": pl.Int32},
    )


def test_state_table_maps_codes_to_states() -> None:
    ct = pl.DataFrame(
        {"kood": [10110, 10130, 10141, 60400], "uld": [1, 2, 3, 5], "n_pix": [4, 4, 4, 4]},
        schema_overrides={"kood": pl.Int32, "uld": pl.Int8},
    )
    t = baas.state_table(_classes(), ct)
    assert t.filter(pl.col("kood") == 10141)["seisund"].item() == "vilets"
    assert t.filter(pl.col("kood") == 10110)["seisund"].item() == "hea"
    assert t.filter(pl.col("kood") == 60400)["seisund"].item() is None
    assert t.filter(pl.col("kood") == 10110)["pindala_km2"].item() == pytest.approx(4 * 25 / 1e6)


def test_state_table_rejects_ambiguous_mapping() -> None:
    ct = pl.DataFrame(
        {"kood": [10110, 10110], "uld": [1, 2], "n_pix": [1, 1]},
        schema_overrides={"kood": pl.Int32, "uld": pl.Int8},
    )
    with pytest.raises(ValueError, match="mitme seisundiga"):
        baas.state_table(_classes(), ct)


def test_class_lut_only_for_states() -> None:
    ct = pl.DataFrame(
        {"kood": [10110, 10130, 10141, 60400], "uld": [1, 2, 3, 5], "n_pix": [4, 4, 4, 4]},
        schema_overrides={"kood": pl.Int32, "uld": pl.Int8},
    )
    lut, used = baas.class_lut(baas.state_table(_classes(), ct))
    assert used.height == 3
    assert lut[60400] == -1
    assert lut[10110] == 0
    assert lut[10141] == 2
