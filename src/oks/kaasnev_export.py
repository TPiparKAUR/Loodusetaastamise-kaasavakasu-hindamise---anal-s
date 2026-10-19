"""Kaasneva kasu tulemused -> veebilehe JSON ja allalaaditavad CSV-d / Excel.

Väljund (``site/data``):

* ``kaasnev.json`` – indikaatorid, kihid, tüüp × seisund ja suurte ökosüsteemide keskväärtused;
* ``tendus.json`` – ökosüsteemi/tüübi tasemel muutus vilets → hea ja keskmine → hea (paaritatud ja paaritamata)
  koos hüve suuna ja tugevuse ettepanekuga (kvalitatiivse raamistiku tõendusbaas);
* ``kaasnev_tuup_seisund.csv``, ``kaasnev_suured.csv`` – pikad tabelid täpsete väärtustega.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import polars as pl

from . import catalog, config, indikaatorid, kaasnev, nouded

#: Staatuse koodid JSON-is (indeks = kood).
STATUSES: list[str] = [
    kaasnev.STATUS_OK,
    kaasnev.STATUS_PARTIAL,
    kaasnev.STATUS_NONE,
    kaasnev.STATUS_MISSING,
    kaasnev.STATUS_MIXED,
]

#: Kihid, mille seos seisundiga on hinnatud ainult segumudeliga ökosüsteemi tasemel (uuriv).
MIXED_LAYERS: frozenset[str] = frozenset(
    {
        "vee_puhastamise_potentsiaal_p_kg_ha_a_2022_930m",
        "vee_puhastamise_potentsiaal_p_eur_ha_2022_930m",
        "lamm_grd1000_am_drained_2022",
    }
)


def _r(x: object, sig: int = 5) -> object:
    if x is None:
        return None
    if isinstance(x, float):
        if not math.isfinite(x):
            return None
        if x == 0:
            return 0
        return round(x, sig - 1 - int(math.floor(math.log10(abs(x)))))
    return x


def layer_info(cat: pl.DataFrame) -> list[dict[str, Any]]:
    """Kihtide kirjeldused indikaatorite järjekorras (roll: ``bio``, ``raha`` või ``lisa``)."""
    out: list[dict[str, Any]] = []
    for ind in indikaatorid.INDICATORS:
        for lid in ind.layers:
            rows = cat.filter(pl.col("id") == lid)
            if rows.is_empty():
                continue
            r = rows.row(0, named=True)
            roll = "bio" if lid == ind.bio else "raha" if lid in ind.raha else "lisa"
            out.append(
                {
                    "id": lid,
                    "nimi": r["nimi"],
                    "uhik": r["uhik"],
                    "omadus": r["omadus"],
                    "ind": ind.key,
                    "roll": roll,
                    "res": r["spatial_resolution"],
                    "aasta": next((int(s) for s in lid.split("_") if s.isdigit() and len(s) == 4), None),
                    "markus": r["markus"],
                    "tabeli_markus": r["comments"],
                    "definitsiooniline": lid in catalog.DEFINITIONAL,
                    "uuriv": lid in MIXED_LAYERS,
                    "lisakiht": lid in catalog.BRIEF_EXTRA,
                }
            )
    return out


def _cells(df: pl.DataFrame, keys: list[str], layers: list[str]) -> dict[tuple[Any, ...], list[Any]]:
    """Sõnastik ``võti -> [rakk kihi kohta]``; rakk = ``[mean, sd, kate, esineb_osa, staatuse indeks]``."""
    by_layer: dict[str, dict[tuple[Any, ...], list[Any]]] = {}
    sub = df.filter(pl.col("layer_id").is_not_null())
    for r in sub.iter_rows(named=True):
        key = tuple(r[k] for k in keys)
        cell = [
            _r(r["mean"]),
            _r(r["sd"]),
            _r(r["kate"], 4),
            _r(r["esineb_osa"], 4),
            STATUSES.index(r["staatus"]),
        ]
        by_layer.setdefault(r["layer_id"], {})[key] = cell
    keys_all = {k for d in by_layer.values() for k in d}
    return {k: [by_layer.get(lid, {}).get(k) for lid in layers] for k in keys_all}


def _mixed_cells(lahtrid: pl.DataFrame, layers: list[str]) -> dict[tuple[int, str], dict[str, list[Any]]]:
    """Segumudeli kihtide hinnangud ökosüsteemi tasemel: ``(eco_kood, seisund) -> {kiht: rakk}``."""
    out: dict[tuple[int, str], dict[str, list[Any]]] = {}
    sub = lahtrid.filter(
        pl.col("layer_id").is_in([x for x in layers if x in MIXED_LAYERS])
        & (pl.col("unit_level") == "okosusteem")
    )
    for r in sub.iter_rows(named=True):
        out.setdefault((int(r["unit_code"]), r["state"]), {})[r["layer_id"]] = [
            _r(r["mean"]),
            None,
            None,
            None,
            STATUSES.index(kaasnev.STATUS_MIXED),
        ]
    return out


def build_json(results: Path, out: Path) -> dict[str, Any]:
    """Kirjuta ``kaasnev.json``, ``tendus.json`` ja pikad CSV-d.

    Parameters
    ----------
    results
        ``data/tulemused`` (``kaasnev_*.parquet``, ``paarid.parquet``, ``lahtrid.parquet``).
    out
        Väljundkaust (``site/data``).

    Returns
    -------
    dict[str, Any]
        ``kaasnev.json`` sisu.
    """
    out.mkdir(parents=True, exist_ok=True)
    cat = catalog.build_catalogue(
        config.ROOT / "alusmaterjalid/metaandmed/layer_definition_checked_vrs2.csv",
        config.ROOT / "data/arhiiv_failid.csv",
    )
    info = layer_info(cat)
    layers = [x["id"] for x in info]
    ts = pl.read_parquet(results / "kaasnev_tuup_seisund.parquet")
    big = pl.read_parquet(results / "kaasnev_suured.parquet")
    lahtrid = pl.read_parquet(results / "lahtrid.parquet")

    keys_t = ["okosusteem_kood", "alam_kood", "tuup", "uld", "seisund_nimi"]
    cells_t = _cells(ts, keys_t, layers)
    area_t = {tuple(r[k] for k in keys_t): r["pindala_ha"] for r in ts.unique(keys_t).iter_rows(named=True)}
    eco_name = dict(zip(ts["okosusteem_kood"], ts["okosusteem"], strict=True))
    rows_t = []
    for key in sorted(area_t, key=lambda k: (k[0], k[1], k[3])):
        ok, alam, tuup, uld, sn = key
        rows_t.append([ok, alam, tuup, uld, sn, _r(area_t[key], 6), cells_t.get(key, [None] * len(layers))])

    keys_b = ["okosusteem_kood", "seisund_nimi"]
    cells_b = _cells(big, keys_b, layers)
    mixed = _mixed_cells(lahtrid, layers)
    area_b = {tuple(r[k] for k in keys_b): r["pindala_ha"] for r in big.unique(keys_b).iter_rows(named=True)}
    rows_b = []
    for key in sorted(area_b, key=lambda k: (k[0], list(big["seisund_nimi"].unique()).index(k[1]))):
        ok, sn = key
        cs = list(cells_b.get(key, [None] * len(layers)))
        for lid, cell in mixed.get((ok, sn), {}).items():
            cs[layers.index(lid)] = cell
        rows_b.append([ok, sn, _r(area_b[key], 6), cs])
    order = {
        s: i
        for i, s in enumerate([*kaasnev.STATE_ORDER, "kokku (hea+keskmine+vilets)", "kokku (kõik seisundid)"])
    }
    rows_b.sort(key=lambda r: (r[0], order.get(r[1], 99)))

    data = {
        "indikaatorid": [
            {
                "key": i.key,
                "nimi": i.nimi,
                "sektsioon": i.sektsioon,
                "grupp": i.grupp,
                "tuup": i.tuup,
                "suund": i.suund,
                "ajaraam": i.ajaraam,
                "ulatus": i.ulatus,
                "ekstreem": i.ekstreem,
                "raha_meetod": i.raha_meetod,
                "kulukasu": i.kulukasu,
                "topelt": i.topelt,
                "ebakindlus": i.ebakindlus,
                "markus": i.markus,
                "kihid": list(i.layers),
            }
            for i in indikaatorid.INDICATORS
        ],
        "kihid": info,
        "staatused": STATUSES,
        "eco": {str(k): v for k, v in eco_name.items()},
        "suured_nimed": {str(k): v for k, v in kaasnev.BIG_CLASSES.items()},
        "tuubid": rows_t,
        "suured": rows_b,
        "parameetrid": {
            "positiivse_osa_lävi": catalog.POSITIVE_MIN,
            "kate_min": kaasnev.COVER_MIN,
            "kate_taielik": kaasnev.COVER_FULL,
            "tugevuse_lavendid": list(indikaatorid.STRENGTH_BREAKS),
        },
    }
    (out / "kaasnev.json").write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    (out / "nouded.json").write_text(
        json.dumps(
            {"nouded": nouded.REQUIREMENTS, "kriitika": nouded.CRITIQUE, "kusimused": nouded.QUESTIONS},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    ts.write_csv(out / "kaasnev_tuup_seisund.csv")
    big.write_csv(out / "kaasnev_suured.csv")
    ev = evidence(results)
    (out / "tendus.json").write_text(
        json.dumps(
            {"cols": ev.columns, "rows": [[_r(v) for v in row] for row in ev.iter_rows()]},
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    return data


def evidence(results: Path) -> pl.DataFrame:
    """Muutus vilets → hea ja keskmine → hea ökosüsteemi- ja alamökosüsteemi tasemel hüve suuna ja tugevusega.

    ``hyve_suund``: ``positiivne`` / ``negatiivne`` / ``ebaselge`` (ei ole oluline või ei piisa andmeid), arvestades
    indikaatori suunda (``vaiksem_parem``: väärtuse vähenemine on hüve kasv). ``tugevus`` on ettepanek
    (``indikaatorid.STRENGTH_BREAKS``); ``oluline`` = paaritatud hinnang, FDR q < α.
    """
    paarid = pl.read_parquet(results / "paarid.parquet")
    units = pl.read_parquet(results / "uhikud.parquet")
    unit_name = {(r["unit_level"], r["unit_code"]): r["nimi"] for r in units.iter_rows(named=True)}
    unit_eco = {(r["unit_level"], r["unit_code"]): r["eco_code"] for r in units.iter_rows(named=True)}
    sign = {
        lid: (1 if i.suund == "suurem_parem" else -1) for i in indikaatorid.INDICATORS for lid in i.layers
    }
    rows: list[dict[str, Any]] = []
    for r in paarid.iter_rows(named=True):
        lid = r["layer_id"]
        if lid not in indikaatorid.LAYER_TO_INDICATOR:
            continue
        d, rel = r.get("delta_m"), r.get("rel_m")
        if not r.get("enough_m") or d is None:
            d, rel, est = r.get("delta_u"), r.get("rel_u"), "paaritamata"
            sig = bool(r.get("oluline_u")) if r.get("enough_u") else False
            ok = bool(r.get("enough_u")) and d is not None
        else:
            est = "paaritatud"
            sig = bool(r.get("oluline_m"))
            ok = True
        direction = "ebaselge"
        if ok and sig and d is not None and d != 0:
            direction = "positiivne" if d * sign[lid] > 0 else "negatiivne"
        key = (r["unit_level"], r["unit_code"])
        rows.append(
            {
                "kiht": lid,
                "indikaator": indikaatorid.LAYER_TO_INDICATOR[lid],
                "tase": r["unit_level"],
                "uksus": unit_name[key],
                "eco": int(unit_eco[key]),
                "paar": r["pair"],
                "hinnang": est if ok else "",
                "delta": _r(d) if ok else None,
                "rel": _r(rel, 4) if ok else None,
                "oluline": sig and ok,
                "q": _r(r.get("q_m") if est == "paaritatud" else r.get("q_u")) if ok else None,
                "hyve_suund": direction,
                "tugevus": indikaatorid.strength(rel) if ok and sig else "",
                "paare": int(r["n_strata"]) if est == "paaritatud" and r.get("n_strata") else None,
            }
        )
    return pl.DataFrame(rows)
