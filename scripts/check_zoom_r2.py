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

Ogni richiesta porta il Referer del sito (SITE_REFERER): una regola WAF di
Cloudflare su zoom.medievalvisions.com blocca le richieste il cui Referer non
inizia con l'indirizzo del sito, comprese quelle senza Referer.

Gli errori transitori (rete: connessione chiusa, timeout; HTTP 5xx e 429)
si ritentano fino a tre volte, con attese di 1, 3 e 9 secondi; un 403, un 404
o un altro 4xx restano errori subito. Le richieste partono al massimo quattro
alla volta (MAX_WORKERS): in CI raffiche piu' larghe ricevevano a caso
"Connection reset by peer", un file diverso a ogni giro. Il riepilogo dice
quanti file hanno avuto bisogno di un nuovo tentativo.

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
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "assets" / "data" / "zoom-manifest.json"
USER_AGENT = "MinDatabase-zoom-check/1.0"
SITE_REFERER = "https://www.medievalvisions.com/"
MAX_WORKERS = 4
RETRY_DELAYS = (1, 3, 9)  # secondi prima del 2o, 3o e 4o tentativo


def zoom_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + urllib.parse.quote(path.lstrip("/"))


def build_request(url: str, full: bool) -> urllib.request.Request:
    """GET se full, altrimenti HEAD; con User-Agent e Referer del sito."""
    return urllib.request.Request(url, method="GET" if full else "HEAD",
                                  headers={"User-Agent": USER_AGENT, "Referer": SITE_REFERER})


def fetch(url: str, full: bool):
    """(status, headers, body|None) per l'URL; HEAD se full e' falso."""
    req = build_request(url, full)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            headers = {k.lower(): v for k, v in resp.getheaders()}
            return resp.status, headers, resp.read() if full else None
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, None
    except (urllib.error.URLError, OSError) as exc:
        return f"error: {exc}"[:80], {}, None


def is_transient(status) -> bool:
    """Vero per gli esiti da ritentare: errore di rete, 5xx, 429."""
    if isinstance(status, str):
        return True
    return status == 429 or 500 <= status <= 599


def fetch_with_retry(url: str, full: bool, fetcher=None, sleep=time.sleep,
                     delays=RETRY_DELAYS):
    """(risposta, tentativi): ritenta gli esiti transitori con attese crescenti."""
    fetcher = fetcher or fetch
    response = fetcher(url, full)
    attempts = 1
    for delay in delays:
        if not is_transient(response[0]):
            break
        sleep(delay)
        response = fetcher(url, full)
        attempts += 1
    return response, attempts


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
        response, attempts = fetch_with_retry(zoom_url(base, entry["path"]), args.sha)
        return entry, entry_problems(entry, response, args.sha), attempts

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        results = list(pool.map(run, entries))

    bad = [(e["path"], p, n) for e, p, n in results if p]
    retried = [(e["path"], n) for e, _, n in results if n > 1]
    for path, n in retried:
        print(f"RETRY {path}: {n} tentativi")
    for path, problems, n in bad:
        print(f"FAIL {path}: {', '.join(problems)} (dopo {n} tentativi)")
    mode = "GET + sha256" if args.sha else "HEAD"
    print(f"{len(entries) - len(bad)}/{len(entries)} zoom ok da {base} ({mode}); "
          f"{len(retried)} con nuovi tentativi")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
