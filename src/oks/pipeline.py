"""Raster-teenuste töötlusliin: allalaadimine -> plokkidesse agregeerimine -> toorfaili kustutamine."""

from __future__ import annotations

import logging
import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import polars as pl

from . import aggregate, baas, catalog, config, fetch

log = logging.getLogger(__name__)

#: Rastrid, mille eraldusvõime on jämedam kui see (m), ei sobi ökosüsteem x seisund analüüsiks.
MAX_RES_M = 10


def _load_lut() -> tuple[object, int]:
    used = pl.read_parquet(config.DERIVED / "klassid_kasutusel.parquet")
    classes = pl.read_parquet(config.DERIVED / "klassid.parquet")
    lut, _ = baas.class_lut(classes)
    return lut, used.height


def process_layer(
    layer_id: str, rel: str, invalid: tuple[float, ...], keep_raw: bool = False
) -> dict[str, object]:
    """Töötle üks raster; tagasta manifestirida (ajad, ridade arv, suurus)."""
    out = config.BLOCKS / f"{layer_id}.parquet"
    t0 = time.time()
    lut, n_cls = _load_lut()
    dest = config.CACHE / rel
    fetch.download(rel, dest)
    t1 = time.time()
    baas_det = fetch.download(config.BAAS_DET, config.CACHE / config.BAAS_DET)
    df = aggregate.aggregate_layer(aggregate.LayerSpec(layer_id, rel, invalid), dest, baas_det, lut, n_cls)  # type: ignore[arg-type]
    config.BLOCKS.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out, compression="zstd")
    if not keep_raw:
        dest.unlink(missing_ok=True)
    t2 = time.time()
    return {
        "id": layer_id,
        "fail": rel,
        "ridu": df.height,
        "pikslid": int(df["n"].cast(pl.Int64).sum()) if df.height else 0,
        "alla_s": round(t1 - t0, 1),
        "agg_s": round(t2 - t1, 1),
        "parquet_b": out.stat().st_size,
    }


def run(workers: int = 3, only: set[str] | None = None, force: bool = False) -> pl.DataFrame:
    """Töötle kõik analüüsitavad rastrid (eval=TRUE, eraldusvõime <= ``MAX_RES_M``)."""
    cat = catalog.build_catalogue(
        config.ROOT / "alusmaterjalid/metaandmed/layer_definition_checked_vrs2.csv",
        config.ROOT / "data/arhiiv_failid.csv",
    )
    ev = catalog.evaluated(cat).filter(
        (pl.col("tyyp") == "raster") & (pl.col("spatial_resolution") <= MAX_RES_M)
    )
    jobs = []
    for r in ev.iter_rows(named=True):
        if only and r["id"] not in only:
            continue
        if not force and (config.BLOCKS / f"{r['id']}.parquet").exists():
            continue
        jobs.append((r["id"], r["fail"], catalog.EXTRA_INVALID.get(r["id"], ())))
    log.info("%d kihti töötlemisel", len(jobs))
    rows: list[dict[str, object]] = []
    # 'spawn': Polars + fork võib ummistuda
    with ProcessPoolExecutor(workers, mp_context=mp.get_context("spawn")) as ex:
        futs = {ex.submit(process_layer, *j): j[0] for j in jobs}
        for f in as_completed(futs):
            try:
                row = f.result()
            except Exception:
                log.exception("kiht %s ebaõnnestus", futs[f])
                continue
            log.info("valmis: %s", row)
            rows.append(row)
    man = pl.DataFrame(rows)
    if man.height:
        path = config.BLOCKS / "_manifest.csv"
        if path.exists():
            man = pl.concat([pl.read_csv(path), man], how="diagonal_relaxed").unique("id", keep="last")
        man.write_csv(path)
    return man


#: Rasteriseeritud põllumassiivide atribuudid: (kihi id, gpkg, väli, tulemuse fail). ``vaartusklass``
#: on ainult diagnostika (võrdlus baaskaardi põllumaa seisundiga) ja ei ole teenuse hinnang.
FIELD_LAYERS: tuple[tuple[str, str, str, str], ...] = (
    ("toiduteenus_2022", "Toit_soot_pollult/toiduteenus_2022.gpkg", "boniteet", "toiduteenus_boniteet.tif"),
    (
        "biotorje_2022",
        "Bioloogiline_torje/biotorje_2022.gpkg",
        "pestits_vahenemine",
        "biotorje_pestits_vahenemine.tif",
    ),
    (
        "toiduteenus_2022__vaartusklass",
        "Toit_soot_pollult/toiduteenus_2022.gpkg",
        "vaartusklass",
        "toiduteenus_vaartusklass.tif",
    ),
)


def run_fields(force: bool = False) -> pl.DataFrame:
    """Rasteriseeri ja aggregeeri põllumassiivide vektorkihid (``fields``) samale plokitabelile."""
    from . import fields  # hilinenud import: shapely vajalik ainult siin

    lut, n_cls = _load_lut()
    baas_det = fetch.download(config.BAAS_DET, config.CACHE / config.BAAS_DET)
    rows = []
    for lid, gpkg, attr, tif in FIELD_LAYERS:
        out = config.BLOCKS / f"{lid}.parquet"
        if out.exists() and not force:
            continue
        t0 = time.time()
        src = config.DERIVED / "vektor_raster" / tif
        if not src.exists():
            mapper = fields.value_class_to_number if attr == "vaartusklass" else None
            fields.rasterize_attribute(fields.cached_gpkg(gpkg), attr, src, mapper)
        df = aggregate.aggregate_layer(aggregate.LayerSpec(lid, tif), src, baas_det, lut, n_cls)  # type: ignore[arg-type]
        config.BLOCKS.mkdir(parents=True, exist_ok=True)
        df.write_parquet(out, compression="zstd")
        rows.append(
            {
                "id": lid,
                "fail": gpkg,
                "ridu": df.height,
                "pikslid": int(df["n"].cast(pl.Int64).sum()),
                "agg_s": round(time.time() - t0, 1),
            }
        )
        log.info("valmis: %s", rows[-1])
    return pl.DataFrame(rows)
