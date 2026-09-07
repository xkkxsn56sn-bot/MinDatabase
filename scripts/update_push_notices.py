#!/usr/bin/env python3
"""Update homepage push notices from the GitHub push event payload.

The script reads files added or modified in the latest push, extracts a
human-friendly title, and stores the most recent MAX_NOTICES entries for
homepage and newsletter display.

TAG [skip notices]
    Un commit di manutenzione — rinomina di campi, riformattazioni, aggiunte
    di frontmatter — tocca `Content/**/*.md` senza che la scheda sia stata
    davvero aggiornata, e senza questo tag finirebbe in homepage e in
    newsletter come se lo fosse. Se la PRIMA RIGA — l'oggetto — di uno
    qualsiasi dei commit del push contiene `[skip notices]` (o
    `[skip-notices]`, maiuscole indifferenti), lo script esce subito senza
    generare notizie e senza toccare i JSON.

    Solo la prima riga. Il corpo del messaggio e' prosa e deve poter nominare
    il tag per esteso — spiegarlo, citarlo, motivare perche' non lo si usa —
    senza per questo attivarlo. Un commit che nel corpo scriveva «nessun
    [skip notices]» ha soppresso notizia e newsletter della scheda che stava
    pubblicando: la regola sull'oggetto nasce da li'.

    Non scrivendo `push_notices.json`, la firma delle notizie resta quella
    dell'invio precedente: `send_newsletter_updates.py` la confronta con
    `newsletter_last_notified.json`, la trova identica e non spedisce nulla.
    Il tag silenzia quindi anche la newsletter, che e' il vero scopo.

ORDINE DELLE NOTIZIE
    Le voci si ordinano per `pushed_at` decrescente, poi — a parita' di
    timestamp, che e' la norma quando un push tocca piu' schede — per tipo di
    modifica, con `created` prima di `modified`, e infine per path in ordine
    alfabetico. I tre livelli danno un ordine totale, quindi il ramo payload e
    il ramo di fallback su git producono lo stesso risultato sugli stessi
    input: senza il secondo livello i due rami divergevano, perche' il payload
    elenca gli `added` prima dei `modified` mentre `git log --name-status`
    elenca in ordine di path.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parents[1]
EVENT_PATH = Path(__import__("os").environ.get("GITHUB_EVENT_PATH", ""))
NOTICES_PATH = REPO_ROOT / "assets" / "data" / "push_notices.json"
MAX_NOTICES = 3

# Secondo livello di ordinamento: una scheda nuova conta piu' di una ritoccata.
CHANGE_RANK = {"created": 0, "modified": 1}

SKIP_TAG_RE = re.compile(r"\[skip[ _-]?notices\]", re.IGNORECASE)

FRONT_MATTER_TITLE_RE = re.compile(r"^title\s*:\s*[\"']?(.*?)[\"']?\s*$", re.IGNORECASE)
HTML_TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _safe_iso(value: str | None) -> str:
    if not value:
        return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    return value


def _normalize_title(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.endswith("- Medieval Visions"):
        cleaned = cleaned.replace("- Medieval Visions", "").strip()
    if cleaned:
        return cleaned
    return "Untitled"


def _title_from_file(file_path: Path) -> str:
    if not file_path.exists() or not file_path.is_file():
        return file_path.stem.replace("_", " ").replace("-", " ").strip() or "Untitled"

    ext = file_path.suffix.lower()
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return file_path.stem.replace("_", " ").replace("-", " ").strip() or "Untitled"

    if ext in {".md", ".markdown"} and text.startswith("---"):
        lines = text.splitlines()
        for line in lines[1:120]:
            if line.strip() == "---":
                break
            match = FRONT_MATTER_TITLE_RE.match(line.strip())
            if match:
                return _normalize_title(match.group(1))

    if ext in {".html", ".htm"}:
        match = HTML_TITLE_RE.search(text)
        if match:
            return _normalize_title(match.group(1))

    candidate = file_path.stem.replace("_", " ").replace("-", " ").strip()
    return candidate or "Untitled"


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {"notices": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"notices": []}


def _is_markdown_path(relative_path: str) -> bool:
    lower = relative_path.lower()
    return lower.endswith(".md") or lower.endswith(".markdown")


def _section_from_path(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/")
    if normalized.startswith("Content/Artists/"):
        return "Artists"
    if normalized.startswith("Content/Churches/") or normalized.startswith("churches"):
        return "Churches"
    if normalized.startswith("Content/Codex/") or normalized.startswith("codices"):
        return "Codices"
    if normalized.startswith("Content/Papers/") or normalized.startswith("papers"):
        return "Papers"
    return "Other"


def _page_url_from_path(relative_path: str) -> str:
    normalized = relative_path.replace("\\", "/").strip()
    if not normalized:
        return "/"
    if normalized.lower().endswith((".md", ".markdown")):
        normalized = re.sub(r"\.(md|markdown)$", ".html", normalized, flags=re.IGNORECASE)
    return f"/{quote(normalized, safe='/')}"


def _notice_with_metadata(notice: dict) -> dict:
    # Keep output schema minimal for sidebar consumption.
    normalized_path = notice.get("path") or ""
    normalized_page_url = _page_url_from_path(normalized_path) if normalized_path else (notice.get("page_url") or "/")
    return {
        "title": notice.get("title") or "Untitled",
        "section": notice.get("section") or "Other",
        "path": normalized_path,
        "page_url": normalized_page_url,
        "change_type": notice.get("change_type") or "modified",
        "pushed_at": notice.get("pushed_at") or _safe_iso(None),
    }


def _parse_event_payload(path: Path) -> tuple[str, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    commits = payload.get("commits") or []
    entries: list[dict] = []

    for commit in commits:
        timestamp = _safe_iso(commit.get("timestamp"))
        typed_paths: dict[str, str] = {}

        for added_path in commit.get("added") or []:
            typed_paths[str(added_path).strip()] = "created"

        for modified_path in commit.get("modified") or []:
            normalized = str(modified_path).strip()
            if normalized and normalized not in typed_paths:
                typed_paths[normalized] = "modified"

        # Some webhook payloads expose explicit rename metadata.
        # Accept common shapes and capture only the destination path.
        for renamed in commit.get("renamed") or []:
            if isinstance(renamed, str):
                typed_paths[renamed] = "modified"
                continue

            if isinstance(renamed, dict):
                new_path = (
                    renamed.get("new")
                    or renamed.get("to")
                    or renamed.get("new_path")
                    or renamed.get("path")
                )
                if new_path:
                    typed_paths[str(new_path).strip()] = "modified"

        for changed_path, change_type in typed_paths.items():
            rel_path = str(changed_path).strip()
            if not rel_path:
                continue
            if not _is_markdown_path(rel_path):
                continue
            absolute = REPO_ROOT / rel_path
            title = _title_from_file(absolute)
            entries.append(
                {
                    "title": title,
                    "section": _section_from_path(rel_path),
                    "path": rel_path,
                    "page_url": _page_url_from_path(rel_path),
                    "change_type": change_type,
                    "pushed_at": timestamp,
                }
            )

    updated_at = _safe_iso(payload.get("head_commit", {}).get("timestamp"))
    return updated_at, entries


def _parse_git_history_fallback(limit_commits: int = 30) -> tuple[str, list[dict]]:
    """Build notices from recent git history when no webhook payload is available."""
    command = [
        "git",
        "log",
        "--date=iso-strict",
        f"--pretty=format:__COMMIT__%cI",
        "--name-status",
        f"-n{limit_commits}",
    ]

    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return _safe_iso(None), []

    entries: list[dict] = []
    current_timestamp: str | None = None

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("__COMMIT__"):
            current_timestamp = _safe_iso(line.replace("__COMMIT__", "", 1).strip())
            continue

        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        status, rel_path = parts
        if not _is_markdown_path(rel_path):
            continue
        if rel_path == "assets/data/push_notices.json":
            continue

        absolute = REPO_ROOT / rel_path
        if not absolute.exists() or not absolute.is_file():
            continue
        title = _title_from_file(absolute)
        entries.append(
            {
                "title": title,
                "section": _section_from_path(rel_path),
                "path": rel_path,
                "page_url": _page_url_from_path(rel_path),
                "change_type": "created" if status == "A" else "modified",
                "pushed_at": current_timestamp or _safe_iso(None),
            }
        )

    return _safe_iso(None), entries


def _change_rank(notice: dict) -> int:
    return CHANGE_RANK.get(str(notice.get("change_type") or "modified"), 1)


def _dedupe_and_sort(entries: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for item in entries:
        enriched = _notice_with_metadata(item)
        key = enriched.get("path") or f"{enriched.get('title', '')}::{enriched.get('section', '')}"
        if not key:
            continue
        existing = merged.get(key)
        if existing is None:
            merged[key] = enriched
            continue
        # Stesso file due volte nello stesso push: vince il timestamp piu'
        # recente e, a parita', 'created' su 'modified'.
        newer = enriched.get("pushed_at", "") > existing.get("pushed_at", "")
        same_time = enriched.get("pushed_at", "") == existing.get("pushed_at", "")
        if newer or (same_time and _change_rank(enriched) < _change_rank(existing)):
            merged[key] = enriched

    values = list(merged.values())
    # Due passate stabili: l'ultima e' la chiave primaria. A parita' di
    # 'pushed_at' sopravvive l'ordine della prima passata — created prima di
    # modified, poi path alfabetico — e l'ordine e' totale.
    values.sort(key=lambda x: (_change_rank(x), x.get("path", "")))
    values.sort(key=lambda x: x.get("pushed_at", ""), reverse=True)
    return values


def _commit_messages() -> list[str]:
    """Messaggi dei commit del push, dal payload o, in mancanza, da git.

    Nel payload si guardano sia `head_commit` sia l'elenco `commits`: un push
    di manutenzione puo' portare piu' di un commit e il tag basta che compaia
    nell'oggetto di uno. I messaggi tornano interi: e' `_skip_requested` a
    ridurli alla prima riga, con la stessa regola per entrambi i rami.
    """
    messages: list[str] = []

    if EVENT_PATH.exists() and EVENT_PATH.is_file():
        try:
            payload = json.loads(EVENT_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            payload = {}

        head = payload.get("head_commit") or {}
        if isinstance(head, dict) and head.get("message"):
            messages.append(str(head["message"]))

        for commit in payload.get("commits") or []:
            if isinstance(commit, dict) and commit.get("message"):
                messages.append(str(commit["message"]))

    if messages:
        return messages

    # Fuori da Actions (esecuzione locale) il payload non c'e': vale il
    # messaggio di HEAD.
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []

    return [result.stdout]


def _subject_line(message: str) -> str:
    """La prima riga del messaggio, cioe' l'oggetto del commit."""
    return (message or "").lstrip("\n").split("\n", 1)[0]


def _skip_requested() -> bool:
    """Vero se il tag compare nell'oggetto di almeno un commit del push.

    La regola e' una sola e vale per entrambi i rami di `_commit_messages`,
    quello del payload e quello di ripiego su git: si guarda la prima riga e
    nient'altro, cosi' il corpo resta prosa libera.
    """
    return any(SKIP_TAG_RE.search(_subject_line(message)) for message in _commit_messages())


def main() -> int:
    if _skip_requested():
        print("Commit tagged [skip notices]: leaving notices and newsletter state untouched.")
        return 0

    previous = _load_json(NOTICES_PATH)
    previous_entries = previous.get("notices") or []

    updated_at, new_entries = (None, [])
    if EVENT_PATH.exists() and EVENT_PATH.is_file():
        updated_at, new_entries = _parse_event_payload(EVENT_PATH)

    # Il payload di GitHub non popola sempre 'added'/'modified' nei commit
    # (la chiave puo' mancare del tutto): in quel caso si ricostruisce dalla
    # storia git, che e' comunque la fonte piu' affidabile.

    if not new_entries:
        print("Payload without usable file lists. Falling back to git history.")
        updated_at, new_entries = _parse_git_history_fallback()

    if not new_entries:
        print("No newly added or modified files found in this push.")
        return 0

    combined = _dedupe_and_sort(new_entries + previous_entries)
    output = {
        "updated_at": updated_at,
        "notices": combined[:MAX_NOTICES],
    }

    NOTICES_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTICES_PATH.write_text(json.dumps(output, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {NOTICES_PATH.relative_to(REPO_ROOT)} with {len(output['notices'])} notice(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
