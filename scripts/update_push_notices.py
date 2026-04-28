#!/usr/bin/env python3
"""Update homepage push notices from the GitHub push event payload.

The script reads files added or modified in the latest push, extracts a
human-friendly title, merges them with existing notices, and keeps only the
3 most recent entries.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
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


def _notice_with_metadata(notice: dict) -> dict:
    # Keep output schema minimal for sidebar consumption.
    return {
        "title": notice.get("title") or "Untitled",
        "section": notice.get("section") or "Other",
        "pushed_at": notice.get("pushed_at") or _safe_iso(None),
    }


def _parse_event_payload(path: Path) -> tuple[str, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))

    commits = payload.get("commits") or []
    entries: list[dict] = []

    for commit in commits:
        timestamp = _safe_iso(commit.get("timestamp"))
        changed_paths = set(list(commit.get("added") or []) + list(commit.get("modified") or []))

        # Some webhook payloads expose explicit rename metadata.
        # Accept common shapes and capture only the destination path.
        for renamed in commit.get("renamed") or []:
            if isinstance(renamed, str):
                changed_paths.add(renamed)
                continue

            if isinstance(renamed, dict):
                new_path = (
                    renamed.get("new")
                    or renamed.get("to")
                    or renamed.get("new_path")
                    or renamed.get("path")
                )
                if new_path:
                    changed_paths.add(new_path)

        for changed_path in changed_paths:
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
        "--name-only",
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

        rel_path = line
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
                "pushed_at": current_timestamp or _safe_iso(None),
            }
        )

    return _safe_iso(None), entries


def _dedupe_and_sort(entries: list[dict]) -> list[dict]:
    merged: dict[str, dict] = {}
    for item in entries:
        enriched = _notice_with_metadata(item)
        key = f"{enriched.get('title', '')}::{enriched.get('section', '')}"
        if not key:
            continue
        existing = merged.get(key)
        if not existing or enriched.get("pushed_at", "") >= existing.get("pushed_at", ""):
            merged[key] = enriched

    values = list(merged.values())
    values.sort(key=lambda x: x.get("pushed_at", ""), reverse=True)
    return values


def main() -> int:
    previous = _load_json(NOTICES_PATH)
    previous_entries = previous.get("notices") or []

    if EVENT_PATH.exists() and EVENT_PATH.is_file():
        updated_at, new_entries = _parse_event_payload(EVENT_PATH)
    else:
        print("GITHUB_EVENT_PATH not found. Falling back to recent git history.")
        updated_at, new_entries = _parse_git_history_fallback()

    if not new_entries:
        print("No newly added or modified files found in this push.")
        return 0

    combined = _dedupe_and_sort(new_entries + previous_entries)
    output = {
        "notices": combined[:MAX_NOTICES],
    }

    NOTICES_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTICES_PATH.write_text(json.dumps(output, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {NOTICES_PATH.relative_to(REPO_ROOT)} with {len(output['notices'])} notice(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
