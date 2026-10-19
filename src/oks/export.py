"""Tulemused -> veebilehe andmed (kompaktne JSON) ja allalaaditavad CSV-d."""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Any

import polars as pl

from . import catalog, config, stats

#: Ümardus (olulisi numbreid) JSON-is; täpsed väärtused on CSV-s.
SIG = 5


def _r(x: object) -> object:
    """Ümarda ujukomaarv ``SIG`` olulise numbrini; ``NaN``/``inf`` -> ``None``."""
    if x is None:
        return None
    if isinstance(x, bool):
        return x
    if isinstance(x, float):
        if not math.isfinite(x):
            return None
        if x == 0:
            return 0
        return round(x, SIG - 1 - int(math.floor(math.log10(abs(x)))))
    return x


def _rows(df: pl.DataFrame, cols: list[str]) -> list[list[object]]:
    return [[_r(v) for v in row] for row in df.select(cols).iter_rows()]


def build_data(results: Path, out: Path, sensitivity: Path | None = None) -> dict[str, Any]:
    """Koosta ``meta.json``, ``paarid.json``, ``lahtrid.json``, ``klassid.json`` ja CSV-d.

    Parameters
    ----------
    results
        ``data/tulemused`` (``analysis.run`` väljund).
    out
        Väljundkaust (``site/data``).
    sensitivity
        Valikuline tundlikkuse kokkuvõtte CSV.
    """
    out.mkdir(parents=True, exist_ok=True)
    paarid = pl.read_parquet(results / "paarid.parquet")
    lahtrid = pl.read_parquet(results / "lahtrid.parquet")
    klassid = pl.read_parquet(results / "klassid.parquet")
    diag = pl.read_parquet(results / "diagnostika.parquet")
    units = pl.read_parquet(results / "uhikud.parquet").with_row_index("ui")
    classes = pl.read_parquet(config.DERIVED / "klassid_kasutusel.parquet")
    cat = catalog.build_catalogue(
        config.ROOT / "alusmaterjalid/metaandmed/layer_definition_checked_vrs2.csv",
        config.ROOT / "data/arhiiv_failid.csv",
    )
    extra = results / "teenused_lisa.csv"
    layer_ids = sorted(set(paarid["layer_id"].unique().to_list()))
    cat = cat.filter(pl.col("id").is_in(layer_ids))
    order = {lid: i for i, lid in enumerate(cat.sort(["grupp", "nimi"])["id"].to_list())}
    layer_ids = sorted(layer_ids, key=lambda i: order[i])
    li = {lid: i for i, lid in enumerate(layer_ids)}
    unit_ix = {(r["unit_level"], r["unit_code"]): r["ui"] for r in units.iter_rows(named=True)}

    methods: dict[str, str] = {}
    if extra.exists():
        methods = dict(pl.read_csv(extra).select("id", "meetod").iter_rows())

    teenused = []
    for lid in layer_ids:
        r = cat.filter(pl.col("id") == lid).row(0, named=True)
        d = diag.filter(pl.col("layer_id") == lid)
        eta = {
            str(row["eco_code"]): [_r(row["eta2_det"]), _r(row["eta2_alam"]), _r(row["eta2_state_in_alam"])]
            for row in d.iter_rows(named=True)
        }
        teenused.append(
            {
                "id": lid,
                "nimi": r["nimi"],
                "pealkiri": r["title"],
                "grupp": r["grupp"],
                "grupp_kood": r["grupp_kood"],
                "omadus": r["omadus"],
                "tuup": r["vaartuse_tuup"],
                "uhik": r["uhik"],
                "markus": r["markus"],
                "tabeli_markus": r["comments"],
                "res": r["spatial_resolution"],
                "allikas": r["data_origin"],
                "kirjeldus": r["abstract"],
                "eta2": eta,
                "meetod": methods.get(lid, "paaritatud"),
                "definitsiooniline": lid in catalog.DEFINITIONAL,
                "aasta": next((int(s) for s in lid.split("_") if s.isdigit() and len(s) == 4), None),
            }
        )

    uhikud = [
        {
            "tase": r["unit_level"],
            "kood": r["unit_code"],
            "nimi": r["nimi"],
            "eco": r["eco_code"],
            "pind": [_r(r[f"pind_{s}"]) for s in stats.STATES],
        }
        for r in units.iter_rows(named=True)
    ]
    cl = classes.select(
        "idx", "kood", "tuup", "seisund_algne", "seisund", "alam_kood", "okosusteem_kood"
    ).sort("idx")
    cols_p = [
        "layer_id",
        "unit_level",
        "unit_code",
        "pair",
        "n_a",
        "n_b",
        "mean_a",
        "mean_b",
        "sd_a",
        "sd_b",
        "delta_u",
        "rel_u",
        "ci_u_lo",
        "ci_u_hi",
        "p_u",
        "q_u",
        "cliff_u",
        "mw_p",
        "blocks_a",
        "blocks_b",
        "n_strata",
        "n_clusters_m",
        "delta_m",
        "rel_m",
        "ci_m_lo",
        "ci_m_hi",
        "p_m",
        "q_m",
        "median_d_m",
        "share_pos_m",
        "wilcoxon_p",
        "q_wilcoxon",
        "enough_m",
        "enough_u",
        "oluline_m",
        "oluline_u",
        "kooskolas",
    ]
    cols_p = [c for c in cols_p if c in paarid.columns]
    pr = paarid.with_columns(
        pl.col("layer_id").replace_strict(li, return_dtype=pl.Int64).alias("layer_id"),
        pl.struct("unit_level", "unit_code")
        .map_elements(lambda s: unit_ix[(s["unit_level"], s["unit_code"])], return_dtype=pl.Int64)
        .alias("unit_code"),
        pl.col("pair")
        .replace_strict({n: i for i, n in enumerate(stats.PAIR_NAMES)}, return_dtype=pl.Int64)
        .alias("pair"),
    ).with_columns(pl.col("unit_level").replace_strict({"okosusteem": 0, "alam": 1}, return_dtype=pl.Int64))
    lr = lahtrid.with_columns(
        pl.col("layer_id").replace_strict(li, return_dtype=pl.Int64),
        pl.struct("unit_level", "unit_code")
        .map_elements(lambda s: unit_ix[(s["unit_level"], s["unit_code"])], return_dtype=pl.Int64)
        .alias("unit_code"),
        pl.col("state").replace_strict({s: i for i, s in enumerate(stats.STATES)}, return_dtype=pl.Int64),
    )
    cols_l = [
        "layer_id",
        "unit_code",
        "state",
        "n",
        "mean",
        "sd",
        "blocks",
        "q05",
        "q25",
        "q50",
        "q75",
        "q95",
    ]
    kr = klassid.with_columns(pl.col("layer_id").replace_strict(li, return_dtype=pl.Int64)).join(
        cl.select("idx", "kood"), left_on="cls", right_on="idx"
    )
    cols_k = ["layer_id", "kood", "n", "mean", "sd"]

    params = pl.read_csv(results / "parameetrid.csv").row(0, named=True)
    meta = {
        "koostatud": date.today().isoformat(),
        "parameetrid": params,
        "seisundid": list(stats.STATES),
        "paarid": list(stats.PAIR_NAMES),
        "teenused": teenused,
        "uhikud": uhikud,
        "klassid": [
            {
                "kood": r["kood"],
                "tuup": r["tuup"],
                "seisund_algne": r["seisund_algne"],
                "seisund": r["seisund"],
                "alam": r["alam_kood"],
                "eco": r["okosusteem_kood"],
            }
            for r in cl.iter_rows(named=True)
        ],
        "paarid_veerud": cols_p,
        "lahtrid_veerud": cols_l,
        "klassid_veerud": cols_k,
    }
    (out / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    (out / "paarid.json").write_text(json.dumps(_rows(pr, cols_p), separators=(",", ":")), encoding="utf-8")
    (out / "lahtrid.json").write_text(json.dumps(_rows(lr, cols_l), separators=(",", ":")), encoding="utf-8")
    (out / "klassid.json").write_text(json.dumps(_rows(kr, cols_k), separators=(",", ":")), encoding="utf-8")
    if sensitivity is not None and sensitivity.exists():
        (out / "tundlikkus.json").write_text(
            json.dumps(pl.read_csv(sensitivity).to_dicts(), ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
    # allalaaditav täpse väärtustega CSV (inimloetavate nimedega)
    names = {lid: t["nimi"] for lid, t in zip(layer_ids, teenused, strict=True)}
    unames = {(r["unit_level"], r["unit_code"]): r["nimi"] for r in units.iter_rows(named=True)}
    csv = paarid.with_columns(
        pl.col("layer_id").replace_strict(names, return_dtype=pl.String).alias("teenus"),
        pl.struct("unit_level", "unit_code")
        .map_elements(lambda s: unames[(s["unit_level"], s["unit_code"])], return_dtype=pl.String)
        .alias("uhik_nimi"),
    )
    csv.write_csv(out / "tulemused_paarid.csv")
    return meta
