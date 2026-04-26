#!/usr/bin/env python3
"""Validate scholar citations in entry bodies are mirrored in YAML front matter.

Rule enforced:
- If a content file contains scholar links in body text (e.g. /scholars.html#id),
  every cited scholar anchor must also appear somewhere in YAML front matter.

This script is intentionally schema-agnostic: it searches the raw front matter
text for scholar URLs so it works with both:
- top-level scholars: [{title, url}]
- meta blocks containing SCHOLARS links.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SCHOLAR_LINK_RE = re.compile(r"/scholars\.html#([a-z0-9][a-z0-9-]*)", re.IGNORECASE)
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
SCHOLAR_ENTRY_RE = re.compile(
    r'<div class="scholar-entry" id="([^"]+)">.*?<h3>([^<]+)</h3>',
    re.DOTALL | re.IGNORECASE,
)


@dataclass
class ValidationError:
    file_path: Path
    message: str


@dataclass
class FileAnalysis:
    has_front_matter: bool
    missing_ids: list[str]


def extract_front_matter_and_body(text: str) -> tuple[str, str]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return "", text
    return match.group(1), text[match.end() :]


def extract_scholar_ids(text: str) -> set[str]:
    return {m.group(1).lower() for m in SCHOLAR_LINK_RE.finditer(text)}


def extract_top_level_scholars_block(front_matter: str) -> str:
    lines = front_matter.splitlines()

    scholars_start = None
    for idx, line in enumerate(lines):
        if re.match(r"^scholars:\s*$", line):
            scholars_start = idx
            break

    if scholars_start is None:
        return ""

    scholars_end = len(lines)
    for idx in range(scholars_start + 1, len(lines)):
        if re.match(r"^[A-Za-z0-9_-]+:\s*.*$", lines[idx]):
            scholars_end = idx
            break

    return "\n".join(lines[scholars_start:scholars_end])


def iter_content_files(root: Path) -> Iterable[Path]:
    content_root = root / "Content"
    if not content_root.exists():
        return []
    return content_root.rglob("*.md")


def load_scholar_titles(root: Path) -> dict[str, str]:
    scholars_file = root / "scholars.html"
    if not scholars_file.exists():
        return {}

    text = scholars_file.read_text(encoding="utf-8")
    titles: dict[str, str] = {}
    for match in SCHOLAR_ENTRY_RE.finditer(text):
        scholar_id = match.group(1).strip().lower()
        title = match.group(2).strip()
        titles[scholar_id] = title
    return titles


def anchor_to_title(anchor: str, title_map: dict[str, str]) -> str:
    if anchor in title_map:
        return title_map[anchor]
    return anchor.replace("-", " ").title()


def analyze_file(path: Path) -> FileAnalysis:
    text = path.read_text(encoding="utf-8")
    front_matter, body = extract_front_matter_and_body(text)
    if not front_matter:
        return FileAnalysis(has_front_matter=False, missing_ids=[])

    body_ids = extract_scholar_ids(body)
    if not body_ids:
        return FileAnalysis(has_front_matter=True, missing_ids=[])

    front_matter_ids = extract_scholar_ids(extract_top_level_scholars_block(front_matter))
    missing = sorted(body_ids - front_matter_ids)
    return FileAnalysis(has_front_matter=True, missing_ids=missing)


def add_missing_to_front_matter(
    front_matter: str, missing_ids: list[str], title_map: dict[str, str]
) -> str:
    if not missing_ids:
        return front_matter

    lines = front_matter.splitlines()

    scholars_start = None
    for idx, line in enumerate(lines):
        if re.match(r"^scholars:\s*$", line):
            scholars_start = idx
            break

    def build_entries(ids: list[str]) -> list[str]:
        entry_lines: list[str] = []
        for scholar_id in ids:
            title = anchor_to_title(scholar_id, title_map).replace('"', '\\"')
            entry_lines.extend(
                [
                    f'  - title: "{title}"',
                    f'    url: "/scholars.html#{scholar_id}"',
                ]
            )
        return entry_lines

    if scholars_start is not None:
        scholars_end = len(lines)
        for idx in range(scholars_start + 1, len(lines)):
            line = lines[idx]
            if re.match(r"^[A-Za-z0-9_-]+:\s*.*$", line):
                scholars_end = idx
                break

        existing_ids = extract_scholar_ids("\n".join(lines[scholars_start:scholars_end]))
        to_add = [sid for sid in missing_ids if sid not in existing_ids]
        if not to_add:
            return front_matter

        new_lines = lines[:scholars_end] + build_entries(to_add) + lines[scholars_end:]
        return "\n".join(new_lines)

    insert_idx = len(lines)
    for idx, line in enumerate(lines):
        if re.match(r"^category:\s*", line):
            insert_idx = idx
            break

    block = ["scholars:"] + build_entries(missing_ids)
    if insert_idx > 0 and lines[insert_idx - 1].strip() != "":
        block = [""] + block
    block.append("")

    new_lines = lines[:insert_idx] + block + lines[insert_idx:]
    return "\n".join(new_lines)


def normalize_scholars_block(front_matter: str, title_map: dict[str, str]) -> str:
    lines = front_matter.splitlines()

    scholars_start = None
    for idx, line in enumerate(lines):
        if re.match(r"^scholars:\s*$", line):
            scholars_start = idx
            break

    if scholars_start is None:
        return front_matter

    scholars_end = len(lines)
    for idx in range(scholars_start + 1, len(lines)):
        if re.match(r"^[A-Za-z0-9_-]+:\s*.*$", lines[idx]):
            scholars_end = idx
            break

    scholars_block_text = "\n".join(lines[scholars_start:scholars_end])
    scholar_ids = sorted(extract_scholar_ids(scholars_block_text))
    if not scholar_ids:
        return front_matter

    sorted_ids = sorted(scholar_ids, key=lambda sid: anchor_to_title(sid, title_map).lower())
    canonical_block: list[str] = ["scholars:"]
    for scholar_id in sorted_ids:
        title = anchor_to_title(scholar_id, title_map).replace('"', '\\"')
        canonical_block.extend(
            [
                f'  - title: "{title}"',
                f'    url: "/scholars.html#{scholar_id}"',
            ]
        )

    base_lines = lines[:scholars_start] + lines[scholars_end:]

    # Trim extra blank lines where scholars block was removed.
    while base_lines and base_lines[-1].strip() == "":
        base_lines.pop()

    insert_idx = len(base_lines)
    for idx, line in enumerate(base_lines):
        if re.match(r"^category:\s*", line):
            insert_idx = idx
            break

    block_with_spacing: list[str] = []
    if insert_idx > 0 and base_lines[insert_idx - 1].strip() != "":
        block_with_spacing.append("")
    block_with_spacing.extend(canonical_block)
    if insert_idx < len(base_lines) and base_lines[insert_idx].strip() != "":
        block_with_spacing.append("")

    new_lines = base_lines[:insert_idx] + block_with_spacing + base_lines[insert_idx:]
    return "\n".join(new_lines)


def apply_fix(path: Path, missing_ids: list[str], title_map: dict[str, str]) -> bool:
    text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return False

    old_front_matter = match.group(1)
    new_front_matter = add_missing_to_front_matter(old_front_matter, missing_ids, title_map)
    if new_front_matter == old_front_matter:
        return False

    updated = text[: match.start(1)] + new_front_matter + text[match.end(1) :]
    path.write_text(updated, encoding="utf-8")
    return True


def apply_normalize(path: Path, title_map: dict[str, str]) -> bool:
    text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return False

    old_front_matter = match.group(1)
    new_front_matter = normalize_scholars_block(old_front_matter, title_map)
    if new_front_matter == old_front_matter:
        return False

    updated = text[: match.start(1)] + new_front_matter + text[match.end(1) :]
    path.write_text(updated, encoding="utf-8")
    return True


def validate_file(path: Path, root: Path) -> list[ValidationError]:
    analysis = analyze_file(path)
    if not analysis.missing_ids:
        return []

    rel = path.relative_to(root)
    return [
        ValidationError(
            file_path=rel,
            message=(
                "Missing scholar links in top-level scholars YAML front matter for anchors: "
                + ", ".join(analysis.missing_ids)
            ),
        )
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate that scholar citations in content bodies also appear in the top-level scholars YAML front matter block."
        )
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Repository root path (default: current directory).",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix files by adding missing scholar links to YAML front matter.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help=(
            "Normalize existing scholars blocks (placement before category and alphabetical order)."
        ),
    )
    args = parser.parse_args()

    root = args.root.resolve()
    files = sorted(iter_content_files(root))

    if args.fix or args.normalize:
        title_map = load_scholar_titles(root)

    if args.fix:
        fixed_count = 0
        for path in files:
            analysis = analyze_file(path)
            if analysis.missing_ids and apply_fix(path, analysis.missing_ids, title_map):
                fixed_count += 1
        print(f"Auto-fix completed. Updated {fixed_count} file(s).")

    if args.normalize:
        normalized_count = 0
        for path in files:
            if apply_normalize(path, title_map):
                normalized_count += 1
        print(f"Normalization completed. Updated {normalized_count} file(s).")

    errors: list[ValidationError] = []
    checked_files = 0

    for path in files:
        checked_files += 1
        errors.extend(validate_file(path, root))

    if errors:
        print("Scholar front matter validation failed.\n")
        for err in errors:
            print(f"- {err.file_path}: {err.message}")
        print(
            f"\nChecked {checked_files} Markdown files under Content/. "
            f"Found {len(errors)} file(s) with missing front matter scholar links."
        )
        return 1

    print(
        "Scholar front matter validation passed. "
        f"Checked {checked_files} Markdown files under Content/."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
