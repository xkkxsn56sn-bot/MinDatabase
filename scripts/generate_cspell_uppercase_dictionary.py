#!/usr/bin/env python3
"""Generate a CSpell dictionary with uppercase/acronym tokens.

This avoids repeated false positives for ALL-CAPS words by collecting them
from project content and writing them to .vscode/cspell-uppercase-words.txt.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".vscode" / "cspell-uppercase-words.txt"

INCLUDE_GLOBS = [
    "Content/**/*.md",
    "_layouts/**/*.html",
    "*.html",
    "assets/**/*.js",
    "assets/**/*.css",
]

EXCLUDE_PARTS = {
    ".git",
    ".venv",
    ".jekyll-cache",
    "_site",
    "node_modules",
}

# Matches uppercase words and common acronym-like tokens:
# API, XML, CE, UTF-8, C14N, II, III, etc.
UPPER_TOKEN_RE = re.compile(r"\b[A-Z][A-Z0-9-]{1,}\b")


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_PARTS for part in path.parts)


def collect_tokens(root: Path) -> list[str]:
    tokens: set[str] = set()

    for pattern in INCLUDE_GLOBS:
        for path in root.glob(pattern):
            if not path.is_file() or is_excluded(path):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            for token in UPPER_TOKEN_RE.findall(text):
                # Keep at least 2 chars and skip long numeric-like fragments.
                if len(token) < 2:
                    continue
                if token.replace("-", "").isdigit():
                    continue
                tokens.add(token)

    return sorted(tokens)


def write_dictionary(tokens: list[str], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Auto-generated uppercase words for CSpell",
        "# Regenerate with: python scripts/generate_cspell_uppercase_dictionary.py",
        "",
        *tokens,
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate .vscode/cspell-uppercase-words.txt from project files"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output dictionary path (default: .vscode/cspell-uppercase-words.txt)",
    )
    args = parser.parse_args()

    tokens = collect_tokens(ROOT)
    write_dictionary(tokens, args.output)
    print(f"Wrote {len(tokens)} uppercase words to {args.output}")


if __name__ == "__main__":
    main()
