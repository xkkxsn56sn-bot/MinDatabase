#!/usr/bin/env python3
"""Verifica che ogni zoom del manifest risponda da R2.

Gli zoom ad alta risoluzione non stanno nel repository: sono nel bucket R2
mindatabase-zoom, pubblicato su https://zoom.medievalvisions.com, e il
repository ne tiene solo l'elenco in assets/data/zoom-manifest.json (scritto
da scripts/sync_zoom_r2.sh). Il controllo 9b verifica le schede contro il
manifest; questo script verifica il manifest contro R2.

Per ogni voce: risposta 200, Content-Type image/jpeg, Content-Length uguale ai
byte del manifest. Con --sha scarica ogni file e confronta anche lo sha256
(lento: la verifica completa si fa a mano ogni tanto, per esempio una volta al
mese). Senza --sha fa solo HEAD, ed e' il passo che gira in CI su ogni push
(validate.yml).

Con --sha --only <percorso> (ripetibile, percorsi completi come in
sync_zoom_r2.sh: Images/<Cartella>/<file>, anche con Zoom/ davanti) scarica e
confronta lo sha256 solo dei file indicati, e fa HEAD (stato, Content-Type,
Content-Length) su tutti gli altri: e' la verifica di routine dopo un lotto.
Un percorso di --only che non e' nel manifest e' un errore. Senza --sha,
--only non cambia nulla: e' gia' tutto HEAD.

Ogni richiesta porta il Referer del sito (SITE_REFERER): una regola WAF di
Cloudflare su zoom.medievalvisions.com blocca le richieste il cui Referer non
inizia con l'indirizzo del sito, comprese quelle senza Referer.

Gli errori transitori (rete: connessione chiusa, timeout; HTTP 5xx e 429)
si ritentano fino a tre volte, con attese di 1, 3 e 9 secondi; un 403, un 404
o un altro 4xx restano errori subito, e cosi' un redirect (R2 non ne manda).
Il riepilogo dice quanti file hanno avuto bisogno di un nuovo tentativo e
quante risposte 429 (troppe richieste) sono arrivate.

Connessioni: ogni thread tiene aperta una sua connessione HTTPS (keep-alive,
http.client) e la riusa per tutte le sue richieste, invece di aprirne una
nuova per file: la stretta di mano TLS costava piu' della HEAD. Se una
connessione riusata risulta chiusa dal server, la richiesta si ripete subito
su una connessione nuova, senza contarla come nuovo tentativo; su una
connessione appena aperta un errore e' un errore, e segue i nuovi tentativi.
Le richieste partono al massimo dodici alla volta (--workers, default
MAX_WORKERS). Fino al 24 novembre 2026 erano quattro, con una connessione nuova
per richiesta: in CI raffiche piu' larghe di connessioni nuove ricevevano a
caso "Connection reset by peer"; con il keep-alive le connessioni sono al
piu' una per thread.

Zero dipendenze. Esce con 1 se una voce non risponde come atteso.

Uso:
    python3 scripts/check_zoom_r2.py [--sha [--only PATH ...]] [--workers N] [--manifest PATH]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import http.client
import json
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "assets" / "data" / "zoom-manifest.json"
USER_AGENT = "MinDatabase-zoom-check/1.0"
SITE_REFERER = "https://www.medievalvisions.com/"
MAX_WORKERS = 12
TIMEOUT = 60  # secondi, per connessione e lettura
RETRY_DELAYS = (1, 3, 9)  # secondi prima del 2o, 3o e 4o tentativo


def zoom_url(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + urllib.parse.quote(path.lstrip("/"))


def build_request(url: str, full: bool) -> urllib.request.Request:
    """GET se full, altrimenti HEAD; con User-Agent e Referer del sito."""
    return urllib.request.Request(url, method="GET" if full else "HEAD",
                                  headers={"User-Agent": USER_AGENT, "Referer": SITE_REFERER})


_local = threading.local()  # connessioni aperte del thread: {(schema, host): conn}


def _connections() -> dict:
    if not hasattr(_local, "conns"):
        _local.conns = {}
    return _local.conns


def _drop(key) -> None:
    conn = _connections().pop(key, None)
    if conn is not None:
        conn.close()


def _send(req: urllib.request.Request, key, fresh: bool):
    """Una richiesta sulla connessione del thread (aperta ora se manca)."""
    conns = _connections()
    if fresh or key not in conns:
        _drop(key)
        cls = http.client.HTTPSConnection if key[0] == "https" else http.client.HTTPConnection
        conns[key] = cls(key[1], timeout=TIMEOUT)
    conn = conns[key]
    conn.request(req.get_method(), req.selector, headers=dict(req.header_items()))
    resp = conn.getresponse()
    body = resp.read()  # anche per HEAD (vuoto): libera la connessione per la prossima
    headers = {k.lower(): v for k, v in resp.getheaders()}
    if resp.will_close:
        _drop(key)
    return resp.status, headers, body


def fetch(url: str, full: bool):
    """(status, headers, body|None) per l'URL; HEAD se full e' falso.

    Riusa la connessione del thread. Se quella connessione, gia' usata, e'
    stata chiusa dal server nel frattempo, ripete subito su una nuova."""
    req = build_request(url, full)
    key = (req.type, req.host)
    reused = key in _connections()
    try:
        try:
            status, headers, body = _send(req, key, fresh=False)
        except (OSError, http.client.HTTPException):
            if not reused:
                raise
            status, headers, body = _send(req, key, fresh=True)
    except (OSError, http.client.HTTPException) as exc:
        _drop(key)
        return f"error: {type(exc).__name__} {exc}"[:80], {}, None
    return status, headers, body if full else None


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


def normalize_only(paths) -> set[str]:
    """Percorsi di --only nella forma del manifest (Images/...), senza Zoom/ o /."""
    out = set()
    for raw in paths or ():
        path = raw.strip().lstrip("/")
        if path.startswith("Zoom/"):
            path = path[len("Zoom/"):]
        if path:
            out.add(path)
    return out


def plan(entries: list[dict], sha: bool, only: set[str]) -> list[tuple[dict, bool]]:
    """(voce, full) per ogni voce: full (GET + sha256) con --sha, solo sulle
    voci di --only se --only c'e'; HEAD altrimenti."""
    return [(e, sha and (not only or e["path"] in only)) for e in entries]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sha", action="store_true", help="scarica e confronta lo sha256")
    parser.add_argument("--only", action="append", metavar="PATH",
                        help="con --sha: GET + sha256 solo su questo file "
                             "(Images/<Cartella>/<file>, ripetibile); HEAD sugli altri")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, metavar="N",
                        help=f"richieste contemporanee (default {MAX_WORKERS})")
    parser.add_argument("--manifest", default=str(MANIFEST))
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers deve essere almeno 1")

    data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    base, entries = data["zoom_base"], data["files"]
    only = normalize_only(args.only)
    unknown = sorted(only - {e["path"] for e in entries})
    for path in unknown:
        print(f"FAIL {path}: non e' nel manifest (--only)")
    if only and not args.sha:
        print("--only ha effetto solo con --sha: tutto in HEAD")

    def run(item):
        entry, full = item
        statuses = []

        def recording_fetch(url, full):
            response = fetch(url, full)  # globale: i test lo sostituiscono
            statuses.append(response[0])
            return response

        response, attempts = fetch_with_retry(zoom_url(base, entry["path"]), full,
                                              fetcher=recording_fetch)
        return entry, entry_problems(entry, response, full), attempts, statuses

    work = plan(entries, args.sha, only)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(run, work))

    bad = [(e["path"], p, n) for e, p, n, _ in results if p]
    retried = [(e["path"], n, st) for e, _, n, st in results if n > 1]
    n429 = sum(st.count(429) for *_, st in results)
    for path, n, st in retried:
        print(f"RETRY {path}: {n} tentativi ({', '.join(map(str, st))})")
    for path, problems, n in bad:
        print(f"FAIL {path}: {', '.join(problems)} (dopo {n} tentativi)")
    n_full = sum(1 for _, full in work if full)
    if n_full == len(work):
        mode = "GET + sha256"
    elif n_full:
        mode = f"GET + sha256 su {n_full}, HEAD sugli altri {len(work) - n_full}"
    else:
        mode = "HEAD"
    print(f"{len(entries) - len(bad)}/{len(entries)} zoom ok da {base} ({mode}, "
          f"{args.workers} alla volta); {len(retried)} con nuovi tentativi; "
          f"risposte 429: {n429}")
    return 1 if bad or unknown else 0


if __name__ == "__main__":
    sys.exit(main())
