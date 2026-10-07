#!/usr/bin/env python3
"""rename_codex_images.py

Rinomina le immagini di Content/Codex/ secondo la regola «Codex Image Names»
del file delle istruzioni, ricavando il nome dalla didascalia di ogni figura.

Gemello di rename_images.py (che toglie gli spazi): stesso passo, stessa
sicurezza. Dry-run per default, nessuna scrittura senza --apply.

I casi che la didascalia non risolve (oggetti senza foglio, doppioni di
foglio) stanno in OVERRIDES, a mano, con il motivo.

USO
    python3 scripts/rename_codex_images.py           # dry-run
    python3 scripts/rename_codex_images.py --apply

Eseguire dalla radice del repo. Dopo --apply: build_gallery_index.py.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_image_names as cin  # noqa: E402
import rename_images as ri  # noqa: E402

REPO = Path.cwd()
CODEX = REPO / "Content" / "Codex"

# (scheda, nome file attuale) -> etichetta al posto del foglio
OVERRIDES = {
    ("Codex-Amiatinus", "amiatinus-01.jpg"): "context-jarrow-dedication",
    ("Codex-Aureus-of-Echternach", "echternach-01.jpg"): "binding",
    ("Book-of-Mulling", "book-of-mulling-04.jpg"): "shrine",
}

FIGURE_RE = re.compile(r"<figure>(.*?)</figure>", re.S)
SRC_RE = re.compile(r'<(?:img|video)\b[^>]*\bsrc="([^"]+)"')
CAP_RE = re.compile(r"<figcaption>(.*?)</figcaption>", re.S)


def plan():
    mapping, problems, seen = {}, [], {}
    for md in sorted(CODEX.glob("*.md")):
        base = md.stem
        slug, width = cin.slug_of(base), cin.width_of(base)
        text = md.read_text(encoding="utf-8")
        for fig in FIGURE_RE.findall(text):
            m = SRC_RE.search(fig)
            if not m:
                continue
            src = m.group(1)
            cap = CAP_RE.search(fig)
            cap = cap.group(1) if cap else ""
            old = src.lstrip("/")
            parts = old.split("/")
            fname = parts[-1]
            ext = fname.rsplit(".", 1)[1].lower().replace("jpeg", "jpg")
            if (base, fname) in cin.OPEN_CONFLICTS:
                continue
            label = OVERRIDES.get((base, fname))
            loc = label or cin.locator_from_caption(cap, width)
            if loc is None:
                problems.append(f"{base}: {fname}: nessun foglio nella didascalia e nessun override")
                continue
            folder = "Video" if parts[0] == "Video" else f"Images/{base}"
            new = f"{folder}/{slug}-{loc}.{ext}"
            if new in seen and seen[new] != old:
                problems.append(f"{base}: {fname} e {seen[new].split('/')[-1]} -> stesso nome {new}")
                continue
            seen[new] = old
            if old != new:
                mapping[old] = new
    return mapping, problems


def main():
    apply_changes = "--apply" in sys.argv
    mapping, problems = plan()
    if problems:
        print(f"DA RISOLVERE A MANO ({len(problems)})")
        for p in problems:
            print("  " + p)
        print()
    print(f"RINOMINE PREVISTE: {len(mapping)}")
    for old, new in sorted(mapping.items()):
        print(f"  {old}  ->  {new}")
    print()
    total, touched = ri.rewrite_references(mapping, apply_changes)
    print(f"RIFERIMENTI DA AGGIORNARE: {total} in {len(touched)} file")
    for path, n in sorted(touched, key=lambda t: -t[1]):
        print(f"  {n:5d}  {path.relative_to(REPO)}")
    print()
    if problems:
        print("Nessuna scrittura: risolvere prima i punti sopra.")
        return 1
    if not apply_changes:
        print("Dry-run: nessun file scritto.")
        return 0
    ri.do_renames(mapping)
    # cartelle rimaste vuote (Images/Lindisfarne)
    for d in sorted({Path(o).parent for o in mapping if o.startswith("Images/")}):
        if (REPO / d).is_dir() and not any((REPO / d).iterdir()):
            (REPO / d).rmdir()
    print("Fatto. Ora: python3 scripts/build_gallery_index.py e validate_content_indexes.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
