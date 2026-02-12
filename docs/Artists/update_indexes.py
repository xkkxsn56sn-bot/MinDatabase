#!/usr/bin/env python3
"""
Update index.html files for Artists.

- Updates per-century index.html lists from .md files.
- Updates docs/Artists/index.html list from subdirectories.
"""

import argparse
import re
from pathlib import Path
from urllib.parse import quote

LIST_RE = re.compile(r"(\s*<ul class=\"links\">)(.*?)(\s*</ul>)", re.DOTALL)


def roman_to_int(value):
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for ch in reversed(value.upper()):
        val = values.get(ch, 0)
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    return total


def century_sort_key(name):
    token = name.split(" ")[0]
    if "-" in token:
        start, end = token.split("-", 1)
    else:
        start = end = token
    return (roman_to_int(start), roman_to_int(end), name)


def build_list_items(items, indent):
    return "\n".join(
        f'{indent}<li><a href="{href}">{label}</a></li>' for label, href in items
    )


def update_links(file_path, items):
    content = file_path.read_text(encoding="utf-8")
    match = LIST_RE.search(content)
    if not match:
        raise ValueError(f"Missing <ul class=\"links\"> in {file_path}")
    
    ul_indent = re.match(r"\s*", match.group(1)).group(0)
    li_indent = ul_indent + "  "
    
    list_items = "\n".join(
        f'{li_indent}<li><a href="{href}">{label}</a></li>'
        for label, href in items
    )
    
    new_block = f"{match.group(1)}\n{list_items}\n{ul_indent}</ul>"
    new_content = content[: match.start()] + new_block + content[match.end() :]
    
    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def md_items_in(dir_path):
    items = []
    for path in dir_path.iterdir():
        if path.is_file() and path.suffix == ".md" and path.stem != "index":
            label = path.stem
            href = quote(f"{label}.html")
            items.append((label, href))
    items.sort(key=lambda x: x[0].casefold())
    return items


def century_dirs(base_dir):
    dirs = [p for p in base_dir.iterdir() if p.is_dir() and (p / "index.html").exists()]
    dirs.sort(key=lambda p: century_sort_key(p.name))
    return dirs


def main():
    parser = argparse.ArgumentParser(description="Update Artists index.html link lists.")
    parser.add_argument(
        "--skip-root", action="store_true", help="Skip docs/Artists/index.html"
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent
    changed = 0

    for dir_path in century_dirs(base_dir):
        items = md_items_in(dir_path)
        if update_links(dir_path / "index.html", items):
            changed += 1

    if not args.skip_root:
        items = [(d.name, f"{quote(d.name)}/") for d in century_dirs(base_dir)]
        if update_links(base_dir / "index.html", items):
            changed += 1

    print(f"Updated {changed} index.html file(s).")


if __name__ == "__main__":
    main()