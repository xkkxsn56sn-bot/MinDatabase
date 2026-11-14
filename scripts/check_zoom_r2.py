#!/usr/bin/env python3
"""Verifica che ogni zoom del manifest risponda da R2.

Gli zoom ad alta risoluzione non stanno nel repository: sono nel bucket R2
mindatabase-zoom, pubblicato su https://zoom.medievalvisions.com, e il
repository ne tiene solo l'elenco in assets/data/zoom-manifest.json (scritto
da scripts/sync_zoom_r2.sh). Il controllo 9b verifica le schede contro il
manifest; questo script verifica il manifest contro R2.

Per ogni voce: risposta 200, Content-Type image/jpeg, Content-Length uguale ai
byte del manifest. Con --sha scarica ogni file e confronta anche lo sha256
(lento: si usa a mano, dopo una sincronizzazione). Senza --sha fa solo HEAD,
ed e' il passo che gira in CI su ogni push (validate.yml).

Zero dipendenze. Esce con 1 se una voce non risponde come atteso.

Uso:
    python3 scripts/check_zoom_r2.py [--sha] [--manifest PATH]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "assets" / "data" / "zoom-manifest.json"
USER_AGENT = "MinDatabase-zoom-check/1.0"


def zoom_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + urllib.parse.quote(path.lstrip("/"))


def fetch(url: str, full: bool):
    """(status, headers, body|None) per l'URL; HEAD se full e' falso."""
    req = urllib.request.Request(url, method="GET" if full else "HEAD",
                                 headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            headers = {k.lower(): v for k, v in resp.getheaders()}
            return resp.status, headers, resp.read() if full else None
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, None
    except (urllib.error.URLError, OSError) as exc:
        return f"error: {exc}"[:80], {}, None


def entry_problems(entry: dict, response, full: bool) -> list[str]:
    """Problemi di una voce del manifest data la risposta (status, headers, body)."""
    status, headers, body = response
    if status != 200:
        return [f"status {status}"]
    out = []
    ctype = headers.get("content-type", "").split(";")[0].strip().lower()
    if ctype != "image/jpeg":
        out.append(f"content-type {ctype or '(none)'}")
    length = headers.get("content-length")
    if body is not None:
        length = str(len(body))
    if length is not None and int(length) != entry["bytes"]:
        out.append(f"bytes {length} != {entry['bytes']}")
    if full and body is not None and hashlib.sha256(body).hexdigest() != entry["sha256"]:
        out.append("sha256 diverso")
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sha", action="store_true", help="scarica e confronta lo sha256")
    parser.add_argument("--manifest", default=str(MANIFEST))
    args = parser.parse_args(argv)

    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    base, entries = data["zoom_base"], data["files"]

    def run(entry):
        return entry, entry_problems(entry, fetch(zoom_url(base, entry["path"]), args.sha), args.sha)

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(run, entries))

    bad = [(e["path"], p) for e, p in results if p]
    for path, problems in bad:
        print(f"FAIL {path}: {', '.join(problems)}")
    mode = "GET + sha256" if args.sha else "HEAD"
    print(f"{len(entries) - len(bad)}/{len(entries)} zoom ok da {base} ({mode})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
