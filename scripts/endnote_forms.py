#!/usr/bin/env python3
"""
endnote_forms.py

Censimento, in sola lettura, della forma dei rimandi a endnotes.html nelle
schede sotto Content/.

FORMA CANONICA
    Nome<a href="/endnotes.html#fn-slug" class="footnote"><sup>N</sup></a>
    numerata in ordine di documento (vedi le Instructions, «Footnote
    Conventions»). La forma nominale [Nome](/endnotes.html#fn-slug) non si usa.

COSA STAMPA
    Le schede che hanno ancora almeno un rimando nominale, in due gruppi:
    le nominali pure (nessun rimando numerico) e le miste (le due forme
    insieme, che vanno rinumerate per intero). Per ognuna, il numero di
    rimandi nominali e numerici. Chiude con i totali.

COSA NON FA
    Non scrive, non modifica, non fallisce: e' un censimento e non un fixer,
    e non e' un validatore. Esce sempre con codice 0. Il front matter e le
    liste <ol> di note locali non contano; i link a /scholars.html restano
    nominali per convenzione e non compaiono qui.

USO
    python3 scripts/endnote_forms.py

Eseguire dalla radice del repo. Utile a chi tocca una scheda: se e' in
elenco, il rimando si converte nello stesso commit.
"""

import re
import sys
from pathlib import Path

REPO = Path.cwd()
CONTENT = REPO / "Content"
EXCLUDED_TOP_DIRS = {"prompts"}

NUMERIC_RE = re.compile(
    r'<a href="/endnotes\.html#fn-[^"]+" class="footnote"><sup>\d+</sup></a>'
)
NAMED_RE = re.compile(r"\]\(/endnotes\.html#fn-[^)]+\)")
NOTE_LIST_RE = re.compile(r'<ol class="(?:footnotes|endnotes)".*?</ol>', re.S)
FRONT_MATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)


def body_of(text: str) -> str:
    text = FRONT_MATTER_RE.sub("", text, count=1)
    return NOTE_LIST_RE.sub("", text)


def main() -> int:
    if not CONTENT.is_dir():
        print("Content/ non trovata: eseguire dalla radice del repo.", file=sys.stderr)
        return 0
    pure, mixed = [], []
    total = with_links = 0
    for path in sorted(CONTENT.rglob("*.md")):
        rel = path.relative_to(CONTENT)
        if rel.parts[0] in EXCLUDED_TOP_DIRS:
            continue
        total += 1
        body = body_of(path.read_text(encoding="utf-8"))
        numeric = len(NUMERIC_RE.findall(body))
        named = len(NAMED_RE.findall(body))
        if numeric or named:
            with_links += 1
        if named and numeric:
            mixed.append((rel, named, numeric))
        elif named:
            pure.append((rel, named, numeric))

    def show(title, rows):
        print(f"{title} ({len(rows)})")
        for rel, named, numeric in rows:
            print(f"  {rel}  nominali {named}, numerici {numeric}")
        print()

    show("Nominali pure", pure)
    show("Miste (rinumerare per intero)", mixed)
    todo = len(pure) + len(mixed)
    links = sum(n for _, n, _ in pure + mixed)
    print(f"Schede da convertire: {todo} su {with_links} con rimandi "
          f"({total} schede in Content/); rimandi nominali: {links}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
