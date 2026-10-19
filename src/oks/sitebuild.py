"""Veebilehe ehitus: ``site_src/`` + tulemused -> ``site/`` (kaustana ja ühe failina)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from . import config, export


def build(out: Path, results: Path | None = None) -> Path:
    """Ehita staatiline sait ``out``-i.

    Loob ``out/index.html`` (+ ``styles.css``, ``app.js``, ``data/*.json``) ja ühefailse variandi
    ``out/oks-seisund.html``, mille andmed on lehe sisse põimitud (avaneb ka ``file://`` kaudu).

    Parameters
    ----------
    out
        Väljundkaust.
    results
        Tulemuste kaust (vaikimisi ``data/tulemused``).
    """
    results = results or config.RESULTS
    src = config.ROOT / "site_src"
    out.mkdir(parents=True, exist_ok=True)
    for name in ("index.html", "styles.css", "app.js"):
        shutil.copyfile(src / name, out / name)
    export.build_data(results, out / "data", results / "tundlikkus.csv")
    data = {
        n: json.loads((out / "data" / f"{n}.json").read_text(encoding="utf-8"))
        for n in ("meta", "paarid", "lahtrid", "klassid")
    }
    html = (src / "index.html").read_text(encoding="utf-8")
    css = (src / "styles.css").read_text(encoding="utf-8")
    js = (src / "app.js").read_text(encoding="utf-8")
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace('<link rel="stylesheet" href="styles.css">', f"<style>{css}</style>")
    html = html.replace(
        '<script src="app.js"></script>', f"<script>window.__OKS__={payload};</script>\n<script>{js}</script>"
    )
    single = out / "oks-seisund.html"
    single.write_text(html, encoding="utf-8")
    return single
