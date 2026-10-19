"""Baaskaardi (ökosüsteemid ja seisund) klassitabelid ja täisresolutsiooni ristiks.

Baaskaardi kihid (kõik 5 m, EPSG:3301, ühine ruudustik):

* ``OS_det_seisund_det_2022_5m``  - detailne ökosüsteem + algne seisundiklass (263 koodi, RAT .aux.xml-is)
* ``OS_detailne_2022_5m``         - detailne ökosüsteem (alamökosüsteem), 62 koodi
* ``seisund_uldine_2022_5m``      - ühtlustatud seisund 1..5

Andmetest tuletatud (vt ``docs/metoodika.md``): ``seisund_uldine`` 1 = hea, 2 = keskmine,
3 = vilets, 4 = seisundita (ökosüsteemid 1-4), 5 = seisundita (rannik, asustus ja muu).
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import polars as pl
import rasterio
from numpy.typing import NDArray

log = logging.getLogger(__name__)

#: Ökosüsteemirühm = detailse koodi esimene number (10000-kohaline).
ECOSYSTEM_NAMES: dict[int, str] = {
    1: "Rohumaad",
    2: "Sood",
    3: "Metsad",
    4: "Põllumaad",
    5: "Rannikud",
    6: "Asustus ja muu",
}

_LETTER = re.compile(r"\s(A-C|A-B|[A-F][12]?)$")


def read_rat(aux_xml: Path) -> pl.DataFrame:
    """Loe GDAL-i rasteri atribuuttabel (RAT) ``.aux.xml`` failist.

    Parameters
    ----------
    aux_xml
        Tee ``OS_det_seisund_det_2022_5m.tif.aux.xml`` faili.

    Returns
    -------
    pl.DataFrame
        Veerud ``kood`` (Int32) ja ``nimi`` (String).
    """
    root = ET.parse(aux_xml).getroot()
    rows = [[f.text or "" for f in r.findall("F")] for r in root.iter("Row")]
    if not rows or any(len(r) != 2 for r in rows):
        raise ValueError(f"Ootamatu RAT-i struktuur failis {aux_xml}")
    return pl.DataFrame(
        {"kood": [int(r[0]) for r in rows], "nimi": [r[1].strip() for r in rows]},
        schema={"kood": pl.Int32, "nimi": pl.String},
    )


def split_class_name(nimi: str) -> tuple[str, str]:
    """Eralda klassinimest ökosüsteemi tüübi nimi ja algne seisundiklass.

    Parameters
    ----------
    nimi
        Nt ``"6410 sinihelmikaniidud  A"`` või ``"Salumets seisundita"``.

    Returns
    -------
    tuple[str, str]
        ``(tüüp, seisund)``; seisund on ``"A"``, ``"D1"``, ``"A-C"`` jne või ``"seisundita"``.
    """
    s = re.sub(r"\s+", " ", nimi).strip()
    if s.endswith("seisundita"):
        return s.removesuffix("seisundita").strip(), "seisundita"
    m = _LETTER.search(s)
    if m is None:
        raise ValueError(f"Seisundiklassi ei leitud nimest: {nimi!r}")
    return s[: m.start()].strip(), m.group(1)


def class_table(aux_xml: Path) -> pl.DataFrame:
    """Koosta detailsete koodide tabel (ökosüsteem, alamökosüsteem, algne seisund).

    Alamökosüsteem on ``kood // 100 * 100`` (vastab ``OS_detailne`` rasteri väärtusele).
    """
    rat = read_rat(aux_xml)
    parts = [split_class_name(n) for n in rat["nimi"]]
    return rat.with_columns(
        pl.Series("tuup", [p[0] for p in parts], dtype=pl.String),
        pl.Series("seisund_algne", [p[1] for p in parts], dtype=pl.String),
        (pl.col("kood") // 10000).alias("okosusteem_kood"),
        (pl.col("kood") // 100 * 100).alias("alam_kood"),
    ).with_columns(
        pl.col("okosusteem_kood").replace_strict(ECOSYSTEM_NAMES, return_dtype=pl.String).alias("okosusteem")
    )


def crosstab_full(
    det_path: Path, alam_path: Path, uld_path: Path, rows_per_stripe: int = 1024
) -> tuple[pl.DataFrame, int]:
    """Täisresolutsiooni ristiks ``(detailne kood, seisund_uldine)`` ja järjepidevuse kontroll.

    Loeb kolme 5 m rastrit ribade kaupa (mälu on piiratud) ning loendab piksleid.

    Parameters
    ----------
    det_path, alam_path, uld_path
        ``OS_det_seisund_det``, ``OS_detailne`` ja ``seisund_uldine`` rastrid.
    rows_per_stripe
        Ühe riba kõrgus pikslites.

    Returns
    -------
    tuple[pl.DataFrame, int]
        Tabel ``kood, uld, n_pix`` ja nende pikslite arv, kus
        ``OS_detailne != OS_det_seisund_det // 100 * 100`` (peaks olema 0).
    """
    counts: NDArray[np.int64] = np.zeros(65536 * 8, dtype=np.int64)
    mismatch = 0
    with rasterio.open(det_path) as d, rasterio.open(alam_path) as a, rasterio.open(uld_path) as u:
        if not (d.shape == a.shape == u.shape and d.transform == a.transform == u.transform):
            raise ValueError("Baaskaardi kihtide ruudustikud ei ühti")
        h, w = d.shape
        for r0 in range(0, h, rows_per_stripe):
            win = rasterio.windows.Window(0, r0, w, min(rows_per_stripe, h - r0))
            dv = d.read(1, window=win)
            av = a.read(1, window=win)
            uv = u.read(1, window=win)
            m = dv != 0
            mismatch += int(np.count_nonzero(av[m] != (dv[m] // 100 * 100)))
            mismatch += int(np.count_nonzero((av != 0) != m))
            key = dv[m].astype(np.int64) * 8 + uv[m].astype(np.int64)
            counts += np.bincount(key, minlength=counts.size)
            log.info("riba %d/%d", r0 // rows_per_stripe + 1, -(-h // rows_per_stripe))
    idx = np.flatnonzero(counts)
    out = pl.DataFrame(
        {"kood": (idx // 8).astype(np.int32), "uld": (idx % 8).astype(np.int8), "n_pix": counts[idx]}
    )
    return out, mismatch


def state_table(classes: pl.DataFrame, crosstab: pl.DataFrame) -> pl.DataFrame:
    """Lisa klassitabelile ühtlustatud seisund (``seisund_uldine``) ristiksist.

    Kontrollib, et iga detailne kood kaardistub täpselt ühele seisundile (mapping on
    funktsioon); vastasel juhul tõstatab ``ValueError``.

    Parameters
    ----------
    classes
        Tulemus ``class_table``-ist.
    crosstab
        Tulemus ``crosstab_full``-ist (veerud ``kood``, ``uld``, ``n_pix``).

    Returns
    -------
    pl.DataFrame
        ``classes`` + ``uld`` (Int8), ``seisund`` (hea/keskmine/vilets või null),
        ``pindala_km2`` (5 m piksel = 25 m²).
    """
    per_code = crosstab.group_by("kood").agg(
        pl.col("uld").n_unique().alias("n_uld"),
        pl.col("uld").first().alias("uld"),
        pl.col("n_pix").sum().alias("n_pix"),
    )
    bad = per_code.filter(pl.col("n_uld") > 1)
    if bad.height:
        raise ValueError(f"Koodid mitme seisundiga: {bad['kood'].to_list()}")
    names = {1: "hea", 2: "keskmine", 3: "vilets"}
    return (
        classes.join(per_code.drop("n_uld"), on="kood", how="left")
        .with_columns(
            pl.col("uld").cast(pl.Int8),
            pl.col("uld").replace_strict(names, default=None, return_dtype=pl.String).alias("seisund"),
            (pl.col("n_pix") * 25 / 1e6).alias("pindala_km2"),
        )
        .sort("kood")
    )


def class_lut(table: pl.DataFrame) -> tuple[NDArray[np.int16], pl.DataFrame]:
    """Koosta kiire otsingutabel ``kood -> klassiindeks`` (ainult seisundiga klassid).

    Returns
    -------
    tuple[NDArray[np.int16], pl.DataFrame]
        ``lut`` pikkusega 65536 (``-1`` = klass ilma seisundita) ja tabel ``idx, kood, ...``
        kasutatud klassidega.
    """
    used = table.filter(pl.col("seisund").is_not_null()).sort("kood").with_row_index("idx")
    lut = np.full(65536, -1, dtype=np.int16)
    lut[used["kood"].to_numpy()] = used["idx"].to_numpy().astype(np.int16)
    return lut, used


def class_lut_all(table: pl.DataFrame) -> tuple[NDArray[np.int16], pl.DataFrame]:
    """Otsingutabel ``kood -> klassiindeks`` KÕIGILE baaskaardi klassidele (ka seisundita ja rannik).

    Returns
    -------
    tuple[NDArray[np.int16], pl.DataFrame]
        ``lut`` pikkusega 65536 (``-1`` = klassita) ja sorteeritud klassitabel veeruga ``idx``.
    """
    allc = table.sort("kood").with_row_index("idx")
    lut = np.full(65536, -1, dtype=np.int16)
    lut[allc["kood"].to_numpy()] = allc["idx"].to_numpy().astype(np.int16)
    return lut, allc
