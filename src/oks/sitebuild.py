"""Veebilehe ehitus: ``site_src/`` + tulemused -> ``site/`` (kaustana ja ühe failina)."""

from __future__ import annotations

import json
import re
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
        for n in ("meta", "paarid", "lahtrid", "klassid", "jaotused")
        if (out / "data" / f"{n}.json").exists()
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
    (out / "oks-seisund-artifact.html").write_text(_artifact_variant(html), encoding="utf-8")
    return single


def _artifact_variant(html: str) -> str:
    """Muuda ühefailne leht artefakti-platvormi sisuks (ilma ``html/head/body`` siltideta)."""
    title = re.search(r"<title>.*?</title>", html, re.S)
    head = re.search(r"<head>(.*?)</head>", html, re.S)
    body = re.search(r"<body>(.*?)</body>", html, re.S)
    if not (title and head and body):
        raise ValueError("Ootamatu HTML-struktuur")
    head_rest = re.sub(
        r"<title>.*?</title>|<meta charset[^>]*>|<meta name=\"viewport\"[^>]*>", "", head.group(1), flags=re.S
    ).strip()
    return f'{title.group(0)}\n<meta name="claude:viewport-fit-sides" content="cover">\n{head_rest}\n{body.group(1).strip()}\n'
