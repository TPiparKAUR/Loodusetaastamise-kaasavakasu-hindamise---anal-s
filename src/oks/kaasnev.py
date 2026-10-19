"""Kaasneva kasu kvantitatiivsed tulemustabelid lähtekasu järgi.

Lähtekas (``docs/lahteulesanne.md``) nõuab:

* iga detailse ökosüsteemitüübi (nt rannaniit, loopealne, sinihelmikaniit) kohta teenuse keskväärtust
  seisundiklassides hea / keskmine / vilets (+ määramata) ja tüübi pindala (ha);
* suurte ökosüsteemide (mets, soo, niit, põld, rannik) väljundit pindalaga kaalutud keskmistena;
* keskväärtusi **kogu klassi pindala kohta**, nullid kaasa arvatud (loogikakontroll: kui 100 ha palumetsast
  25 ha-l kasvavad mustikad, arvutatakse keskmine kogu 100 ha kohta);
* märget, kui teenust tüübis ei esine, ja järeldust „ei paku“, kui seda on väga-väga vähe.

Sisendiks on klassitabelid (``pipeline.write_cls``): iga kihi kohta kõigi 264 baaskaardi klassi pikslite arv,
kehtivate, nullide, positiivsete ja negatiivsete arv ning Σx, Σx².
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

import polars as pl

from . import catalog, config

log = logging.getLogger(__name__)

#: Klass loetakse „teenust ei hinnatud“, kui kehtivate pikslite osa klassi pikslitest on väiksem.
COVER_MIN = 0.05
#: Märge „osaline kate“, kui kehtivate pikslite osa on väiksem (keskmine kehtib katvale osale).
COVER_FULL = 0.9

#: Baaskaardi seisundikoodid ``seisund_uldine`` (lähtekas, tabel „Taustaks“).
STATE_LABELS: dict[int, str] = {1: "hea", 2: "keskmine", 3: "vilets", 4: "määramata", 5: "hindamata"}
STATE_ORDER: list[str] = ["hea", "keskmine", "vilets", "määramata", "hindamata"]

#: Suured ökosüsteemid (lähtekasu „mets, soo, niit, põld, rannik“); asustus ja muu ei liideta.
BIG_CLASSES: dict[int, str] = {
    1: "Niit (rohumaad)",
    2: "Soo",
    3: "Mets",
    4: "Põld",
    5: "Rannik",
}
OTHER_CLASS = 6

STATUS_OK = "ok"
STATUS_PARTIAL = "osaline kate"
STATUS_NONE = "ei paku"
STATUS_MISSING = "ei hinnatud"
STATUS_MIXED = "uuriv (segumudel)"


def class_table() -> pl.DataFrame:
    """Kõik 264 baaskaardi klassi: kood, tüüp, ökosüsteem, seisund (märgend) ja pindala (ha)."""
    cls = pl.read_parquet(config.DERIVED / "klassid.parquet")
    return cls.with_columns(
        pl.col("uld").replace_strict(STATE_LABELS, return_dtype=pl.String).alias("seisund_nimi"),
        (pl.col("n_pix") * 25 / 10_000).alias("pindala_ha"),
    )


def load_class_stats(layer_ids: Sequence[str], blocks: Path | None = None) -> pl.DataFrame:
    """Loe kihtide klassitabelid üheks pikaks tabeliks (``layer_id`` + ``kood`` + loendused).

    Parameters
    ----------
    layer_ids
        Kihtide id-d.
    blocks
        Kaust (vaikimisi ``config.BLOCKS``).

    Returns
    -------
    pl.DataFrame
        Kihid, mille klassitabelit ei ole, jäetakse välja (hoiatus logis).
    """
    base = blocks or config.BLOCKS
    parts = []
    for lid in layer_ids:
        p = base / f"{lid}__cls.parquet"
        if not p.exists():
            log.warning("klassitabel puudub: %s", lid)
            continue
        parts.append(pl.read_parquet(p).with_columns(pl.lit(lid).alias("layer_id")))
    return pl.concat(parts) if parts else pl.DataFrame()


def summarise(stats: pl.DataFrame, group: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    """Liida klassitabelid gruppidesse ja arvuta keskmine, katvus, esinemise osa ja staatus.

    Parameters
    ----------
    stats
        Tulemus ``load_class_stats``-ist.
    group
        Tabel ``kood`` + ``keys`` (mis klass kuhu gruppi kuulub).
    keys
        Grupeerimisveerud (nt ``["okosusteem_kood", "alam_kood", "uld"]``).

    Returns
    -------
    pl.DataFrame
        Veerud ``keys`` + ``layer_id``, ``n_total``, ``n_valid``, ``kate`` (kehtivate osa), ``esineb_osa``
        (nullist erinevate osa kehtivatest), ``mean``, ``sd`` (pikslitasemel, kirjeldav), ``staatus``.
    """
    j = stats.join(group.select("kood", *keys), on="kood", how="inner")
    g = j.group_by([*keys, "layer_id"]).agg(
        pl.col("n_total").sum(),
        pl.col("n_valid").sum(),
        pl.col("n_zero").sum(),
        (pl.col("n_pos").sum() + pl.col("n_neg").sum()).alias("n_nonzero"),
        pl.col("sum").sum(),
        pl.col("sumsq").sum(),
    )
    g = g.with_columns(
        (pl.col("n_valid") / pl.col("n_total")).alias("kate"),
        pl.when(pl.col("n_valid") > 0).then(pl.col("n_nonzero") / pl.col("n_valid")).alias("esineb_osa"),
        pl.when(pl.col("n_valid") > 0).then(pl.col("sum") / pl.col("n_valid")).alias("mean"),
    ).with_columns(
        pl.when(pl.col("n_valid") > 0)
        .then(((pl.col("sumsq") / pl.col("n_valid") - pl.col("mean") ** 2).clip(lower_bound=0)).sqrt())
        .alias("sd")
    )
    return g.with_columns(
        pl.when((pl.col("n_valid") == 0) | (pl.col("kate") < COVER_MIN))
        .then(pl.lit(STATUS_MISSING))
        .when(pl.col("esineb_osa") < catalog.POSITIVE_MIN)
        .then(pl.lit(STATUS_NONE))
        .when(pl.col("kate") < COVER_FULL)
        .then(pl.lit(STATUS_PARTIAL))
        .otherwise(pl.lit(STATUS_OK))
        .alias("staatus")
    ).drop("n_nonzero", "n_zero", "sum", "sumsq")


def type_state(stats: pl.DataFrame, classes: pl.DataFrame) -> pl.DataFrame:
    """Teenuse keskväärtus iga detailse ökosüsteemitüübi ja seisundi kohta.

    Rida = ``(ökosüsteem, tüüp, seisund)``; ``pindala_ha`` on baaskaardi pindala (kõik klassi pikslid).
    """
    keys = ["okosusteem_kood", "okosusteem", "alam_kood", "tuup", "uld", "seisund_nimi"]
    area = classes.group_by(keys).agg(pl.col("pindala_ha").sum(), pl.len().alias("klasse"))
    s = summarise(stats, classes, keys)
    return area.join(s, on=keys, how="left").sort("okosusteem_kood", "alam_kood", "uld")


def big_classes(stats: pl.DataFrame, classes: pl.DataFrame) -> pl.DataFrame:
    """Suurte ökosüsteemide (niit, soo, mets, põld, rannik) pindalaga kaalutud keskmised seisundi kaupa.

    Kaal on kehtiv pindala (Σ pikslid), st tüübi keskmine kaalutakse sama tüübi kehtiva pindalaga; tüübid,
    kus teenust ei hinnatud, kaalu ei anna. Lisarida ``kokku (hea+keskmine+vilets)`` ja ``kokku (kõik)``.
    ``Asustus ja muu`` ei liideta (lähtekas: „Klassi MUUD pole vaja kokku liita“).
    """
    base = classes.filter(pl.col("okosusteem_kood").is_in(list(BIG_CLASSES)))
    keys = ["okosusteem_kood", "okosusteem", "seisund_nimi"]
    out = [_big(stats, base, keys)]
    for label, ulds in (
        ("kokku (hea+keskmine+vilets)", [1, 2, 3]),
        ("kokku (kõik seisundid)", [1, 2, 3, 4, 5]),
    ):
        sub = base.filter(pl.col("uld").is_in(ulds)).with_columns(pl.lit(label).alias("seisund_nimi"))
        out.append(_big(stats, sub, keys))
    res = pl.concat(out)
    return (
        res.with_columns(
            pl.col("seisund_nimi")
            .replace_strict(
                {
                    s: i
                    for i, s in enumerate(
                        [*STATE_ORDER, "kokku (hea+keskmine+vilets)", "kokku (kõik seisundid)"]
                    )
                },
                default=99,
                return_dtype=pl.Int64,
            )
            .alias("_o")
        )
        .sort("okosusteem_kood", "_o")
        .drop("_o")
    )


def _big(stats: pl.DataFrame, classes: pl.DataFrame, keys: list[str]) -> pl.DataFrame:
    area = classes.group_by(keys).agg(pl.col("pindala_ha").sum())
    return area.join(summarise(stats, classes, keys), on=keys, how="left")


def build(layer_ids: Sequence[str], out_dir: Path | None = None) -> dict[str, pl.DataFrame]:
    """Koosta ja kirjuta tulemustabelid (``kaasnev_tuup_seisund``, ``kaasnev_suured``).

    Parameters
    ----------
    layer_ids
        Kihtide id-d (sama järjekord veergudes).
    out_dir
        Väljund (vaikimisi ``config.RESULTS``).
    """
    out_dir = out_dir or config.RESULTS
    classes = class_table()
    stats = load_class_stats(layer_ids)
    res = {"tuup_seisund": type_state(stats, classes), "suured": big_classes(stats, classes)}
    for k, v in res.items():
        v.write_parquet(out_dir / f"kaasnev_{k}.parquet")
    return res
