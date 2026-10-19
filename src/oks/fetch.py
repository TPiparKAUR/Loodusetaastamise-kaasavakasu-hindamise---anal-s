"""Failide allalaadimine arhiivist (jätkamise ja suuruse kontrolliga)."""

from __future__ import annotations

import http.client
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from . import config

log = logging.getLogger(__name__)

_CHUNK = 8 * 1024 * 1024


def url_for(rel: str) -> str:
    """Arhiivisisese suhtelise tee (nt ``Sidusus/x.tif``) täis-URL."""
    return config.ARCHIVE_BASE + config.ARCHIVE_ROOT + urllib.parse.quote(rel)


def remote_size(rel: str) -> int:
    """Serveri teatatud faili suurus baitides (HEAD)."""
    req = urllib.request.Request(url_for(rel), method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


def download(rel: str, dest: Path, retries: int = 4) -> Path:
    """Laadi fail alla ``dest``-i (jätkab pooleli faili, kontrollib lõppsuurust).

    Parameters
    ----------
    rel
        Tee arhiivi juurest, nt ``"Baaskaart/seisund_uldine_2022_5m.tif"``.
    dest
        Sihtfail.
    retries
        Katsete arv võrguvea korral (ootus 2, 4, 8, 16 s).

    Raises
    ------
    OSError
        Kui lõppsuurus ei vasta serveri teatatule.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    total = remote_size(rel)
    if dest.exists() and dest.stat().st_size == total:
        return dest
    part = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(retries + 1):
        have = part.stat().st_size if part.exists() else 0
        if have == total:
            break
        if have > total:
            part.unlink()
            have = 0
        req = urllib.request.Request(url_for(rel))
        if have:
            req.add_header("Range", f"bytes={have}-")
        try:
            with urllib.request.urlopen(req, timeout=120) as r, part.open("ab" if have else "wb") as f:
                while chunk := r.read(_CHUNK):
                    f.write(chunk)
        except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException) as exc:
            log.warning("allalaadimine katkes (%s)", exc)
        if part.exists() and part.stat().st_size == total:
            break
        if attempt < retries:
            wait = 2 ** (attempt + 1)
            log.warning(
                "%s: %d/%d baiti, jätkan %d s pärast",
                rel,
                part.stat().st_size if part.exists() else 0,
                total,
                wait,
            )
            time.sleep(wait)
    if not part.exists() or part.stat().st_size != total:
        raise OSError(f"{rel}: suurus {part.stat().st_size if part.exists() else 0} != {total}")
    part.replace(dest)
    return dest
