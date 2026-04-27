#!/usr/bin/env python3
"""Update homepage push notices from the GitHub push event payload.

The script reads files added in the latest push, extracts a human-friendly title,
merges them with existing notices, and keeps only the 3 most recent entries.
"""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EVENT_PATH = Path(__import__("os").environ.get("GITHUB_EVENT_PATH", ""))
NOTICES_PATH = REPO_ROOT / "assets" / "data" / "push_notices.json"
MAX_NOTICES = 3

SECTION_PRIORITY = {
    "Artists": 0,
    "Churches": 1,
    "Codices": 2,
    "Papers": 3,
    "Other": 4,
}


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
        return {"updated_at": None, "notices": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"updated_at": None, "notices": []}


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


def _notice_with_metadata(notice: dict) -> dict:
    cloned = dict(notice)
    path = str(cloned.get("path", ""))
    section = cloned.get("section") or _section_from_path(path)
    cloned["section"] = section
    return cloned


def _parse_event_payload(path: Path) -> tuple[str, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    commits = payload.get("commits") or []
    entries: list[dict] = []

    for commit in commits:
        timestamp = _safe_iso(commit.get("timestamp"))
        for added_path in commit.get("added") or []:
            rel_path = str(added_path).strip()
            if not rel_path:
                continue
            absolute = REPO_ROOT / rel_path
            title = _title_from_file(absolute)
            entries.append(
                {
                    "title": title,
                    "path": rel_path,
                    "section": _section_from_path(rel_path),
                    "pushed_at": timestamp,
                }
            )

    updated_at = _safe_iso(payload.get("head_commit", {}).get("timestamp"))
    return updated_at, entries


def _dedupe_and_sort(entries: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for item in entries:
        enriched = _notice_with_metadata(item)
        key = enriched.get("path", "")
        if not key:
            continue
        existing = merged.get(key)
        if not existing or enriched.get("pushed_at", "") >= existing.get("pushed_at", ""):
            merged[key] = enriched

    values = list(merged.values())
    values.sort(key=lambda x: x.get("pushed_at", ""), reverse=True)
    return values


def main() -> int:
    if not EVENT_PATH.exists():
        print("GITHUB_EVENT_PATH not found, skipping push notices update.")
        return 0

    previous = _load_json(NOTICES_PATH)
    previous_entries = previous.get("notices") or []

    updated_at, new_entries = _parse_event_payload(EVENT_PATH)
    if not new_entries:
        print("No newly added files found in this push.")
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
