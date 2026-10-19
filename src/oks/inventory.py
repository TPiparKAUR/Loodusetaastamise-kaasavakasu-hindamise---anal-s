"""Arhiivi failide inventuur (HTML-indeksi rekursiivne läbikäimine)."""

from __future__ import annotations

import html
import logging
import re
import urllib.parse
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import polars as pl

from . import config

log = logging.getLogger(__name__)

_ROW = re.compile(
    r'<tr><td[^>]*><a href="([^"]+)">([^<]+)</a></td><td[^>]*>([^<]*)</td><td[^>]*>([^<]*)</td>'
)
_UNITS = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}


def _listing(path: str) -> list[tuple[str, str, str]]:
    url = config.ARCHIVE_BASE + urllib.parse.quote(path, safe="/%")
    with urllib.request.urlopen(url, timeout=60) as r:
        txt = r.read().decode()
    out: list[tuple[str, str, str]] = []
    for href, _name, size, date in _ROW.findall(txt):
        href = html.unescape(href)
        # ülemkataloogi link ja iseenda link jäetakse välja (väldib tsüklit)
        if href.startswith(path) and href != path:
            out.append((href, size.strip(), date.strip()))
    return out


def _walk(path: str, seen: set[str]) -> Iterator[tuple[str, str, str]]:
    if path in seen:
        return
    seen.add(path)
    for href, size, date in _listing(path):
        if href.endswith("/"):
            yield from _walk(href, seen)
        else:
            yield href, size, date


def parse_size(text: str) -> int | None:
    """Teisenda indeksi suuruse tekst (``"492.4 MB"``) ligikaudseks baitideks."""
    m = re.fullmatch(r"([\d.]+)\s*(B|KB|MB|GB)", text.strip())
    return None if m is None else int(float(m.group(1)) * _UNITS[m.group(2)])


def crawl() -> pl.DataFrame:
    """Käi arhiiv läbi ja tagasta failide tabel (``tee, suurus_tekst, suurus_b, muudetud``)."""
    rows = [
        {
            "tee": href.removeprefix(config.ARCHIVE_ROOT),
            "suurus_tekst": size,
            "suurus_b": parse_size(size),
            "muudetud": date,
        }
        for href, size, date in _walk(config.ARCHIVE_ROOT, set())
    ]
    return pl.DataFrame(rows).sort("tee")


def write_inventory(dest: Path) -> pl.DataFrame:
    """Kirjuta inventuur CSV-na ``dest``-i."""
    df = crawl()
    dest.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(dest)
    log.info("inventuur: %d faili -> %s", df.height, dest)
    return df
