#!/usr/bin/env python3
"""
frontmatter_census.py

Censimento, in sola lettura, della forma del front matter delle schede sotto
Content/. E' il gemello di endnote_forms.py: quello guarda i rimandi a
endnotes.html nel corpo, questo guarda il front matter. Sostituisce il
censimento scritto a mano (che si fotografava e poi divergeva).

FORMA CANONICA («nuova»)
    Chiavi di primo livello layout, title, subtitle, dates, meta, scholars;
    esattamente otto blocchi `meta`, in quest'ordine: CORE DATA, IDENTITY AND
    LIMITS, CHRONOLOGY, KEY WORKS, DISPUTED AND REJECTED ATTRIBUTIONS, STYLE
    AND FORMATION, PATRONAGE AND SETTING, RECEPTION AND LEGACY; `scholars:` a
    coppie title/url; niente thematic_keywords, RELATED ENTRIES, Reference
    Links.

MARCATORI (una scheda ne porta zero o piu')
    T    thematic_keywords, come chiave o come blocco THEMATIC KEYWORDS
    K    KEY SCHOLARS, come chiave o come blocco
    S0   nessun `scholars:`
    Sx   `scholars:` con almeno una voce che non e' una coppia title/url:
         una stringa nuda o un titolo senza url (lo studioso non e' linkabile)
    P    primo blocco diverso da CORE DATA
    Rl   RELATED ENTRIES con `links:` e tutte le voci con url
    Rn   RELATED ENTRIES con `links:` e almeno una voce senza url
    Rs   RELATED ENTRIES con `list:` di stringhe nude (non risolve)
    Rf   Reference Links
    Rl, Rn e Rs si escludono a vicenda; quando nessuno e' presente la
    scheda non ha RELATED ENTRIES.

CLASSI
    nuova    il set canonico dei blocchi e nessun marcatore
    vecchia  T e P insieme
    mista    tutto il resto
    Fra le miste si segnalano le «quasi nuove»: nessun marcatore, ma blocchi
    non canonici o senza il blocco delle contese.

USO
    python3 scripts/frontmatter_census.py          totali e schede nuove
    python3 scripts/frontmatter_census.py --all    anche l'elenco per sezione

COSA NON FA
    Non scrive, non modifica, non fallisce: e' un censimento e non un
    validatore. Esce sempre con codice 0. Il front matter e' letto con
    espressioni regolari e non con un parser YAML, per restare senza
    dipendenze come gli altri script; il formato delle schede e' abbastanza
    regolare da permetterlo.
"""

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path.cwd()
CONTENT = REPO / "Content"
EXCLUDED_TOP_DIRS = {"prompts"}

CANONICAL_BLOCKS = [
    "CORE DATA",
    "IDENTITY AND LIMITS",
    "CHRONOLOGY",
    "KEY WORKS",
    "DISPUTED AND REJECTED ATTRIBUTIONS",
    "STYLE AND FORMATION",
    "PATRONAGE AND SETTING",
    "RECEPTION AND LEGACY",
]
MARKERS = ["T", "K", "S0", "Sx", "P", "Rl", "Rn", "Rs", "Rf"]

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
TOP_KEY_RE = re.compile(r"^([A-Za-z_][\w-]*):", re.M)
BLOCK_TITLE_RE = re.compile(r"^  - title:\s*(.+?)\s*$", re.M)


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def top_level_section(front: str, key: str):
    """Il testo sotto una chiave di primo livello, fino alla chiave seguente."""
    match = re.search(rf"^{re.escape(key)}:[ \t]*(.*)$", front, re.M)
    if not match:
        return None
    start = match.end()
    following = TOP_KEY_RE.search(front, start)
    return front[start : following.start() if following else len(front)]


def meta_blocks(front: str):
    """Elenco (titolo, corpo) dei blocchi di `meta`, nell'ordine del file."""
    meta = top_level_section(front, "meta")
    if meta is None:
        return []
    blocks = []
    matches = list(BLOCK_TITLE_RE.finditer(meta))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(meta)
        blocks.append((unquote(m.group(1)), meta[m.end() : end]))
    return blocks


def scholars_form(front: str) -> str:
    section = top_level_section(front, "scholars")
    if section is None:
        return "S0"
    items = []
    for line in section.splitlines():
        if line.startswith("  - "):
            items.append([line])
        elif items and line.strip():
            items[-1].append(line)
    if not items:
        return "S0"
    for item in items:
        is_pair = item[0].startswith("  - title:") and any(
            ln.strip().startswith("url:") for ln in item[1:]
        )
        if not is_pair:
            return "Sx"
    return "pairs"


def classify(front: str):
    blocks = meta_blocks(front)
    titles = [t for t, _ in blocks]
    upper = [t.upper() for t in titles]
    keys = set(TOP_KEY_RE.findall(front))

    markers = set()
    if "thematic_keywords" in keys or "THEMATIC KEYWORDS" in upper:
        markers.add("T")
    if "key_scholars" in {k.lower() for k in keys} or "KEY SCHOLARS" in upper:
        markers.add("K")
    form = scholars_form(front)
    if form == "S0":
        markers.add("S0")
    elif form == "Sx":
        markers.add("Sx")
    if upper and upper[0] != "CORE DATA":
        markers.add("P")
    if "REFERENCE LINKS" in upper:
        markers.add("Rf")
    for title, body in blocks:
        if title.upper() != "RELATED ENTRIES":
            continue
        if re.search(r"^\s+list:", body, re.M):
            markers.add("Rs")
        elif re.search(r"^\s+links:", body, re.M):
            entries = len(re.findall(r"^\s+- title:", body, re.M))
            urls = len(re.findall(r"^\s+url:", body, re.M))
            markers.add("Rl" if entries and urls >= entries else "Rn")

    canonical = titles == CANONICAL_BLOCKS
    if canonical and not markers:
        cls = "nuova"
    elif "T" in markers and "P" in markers:
        cls = "vecchia"
    else:
        cls = "mista"
    quasi = cls == "mista" and not markers
    return {
        "class": cls,
        "markers": markers,
        "canonical": canonical,
        "blocks": len(blocks),
        "quasi": quasi,
        "has_related": bool({"Rl", "Rn", "Rs"} & markers),
    }


def section_of(rel: Path) -> str:
    parts = rel.parts
    if parts[0] == "Artists" and len(parts) > 2:
        return f"Artists {parts[1]}"
    return parts[0]


def main() -> int:
    if not CONTENT.is_dir():
        print("Content/ non trovata: eseguire dalla radice del repo.", file=sys.stderr)
        return 0
    show_all = "--all" in sys.argv[1:]

    rows = []
    without_front = []
    for path in sorted(CONTENT.rglob("*.md")):
        rel = path.relative_to(CONTENT)
        if rel.parts[0] in EXCLUDED_TOP_DIRS:
            continue
        match = FRONT_MATTER_RE.match(path.read_text(encoding="utf-8"))
        if not match:
            without_front.append(rel)
            continue
        info = classify(match.group(1))
        info["rel"] = rel
        info["name"] = path.stem
        rows.append(info)

    classes = Counter(r["class"] for r in rows)
    markers = Counter(m for r in rows for m in r["markers"])
    total = len(rows)

    print(f"Schede con front matter: {total}")
    if without_front:
        print(f"Senza front matter: {len(without_front)}")
    print()
    print("Classi")
    for cls in ("nuova", "vecchia", "mista"):
        print(f"  {cls:<8} {classes[cls]:>4}")
    print(f"  di cui quasi nuove (miste senza marcatori): "
          f"{sum(1 for r in rows if r['quasi'])}")
    print()
    print("Marcatori")
    for m in MARKERS:
        print(f"  {m:<3} {markers[m]:>4}")
    print(f"  nessun RELATED ENTRIES: {sum(1 for r in rows if not r['has_related'])}")
    print()
    print(f"Set canonico dei blocchi: {sum(1 for r in rows if r['canonical'])}")
    print(f"Con otto blocchi meta:    {sum(1 for r in rows if r['blocks'] == 8)}")
    print(f"CORE DATA per primo:      {total - markers['P']}")

    print()
    print("Nuove")
    for r in rows:
        if r["class"] == "nuova":
            print(f"  {r['rel'].as_posix()}")
    quasi = [r for r in rows if r["quasi"]]
    if quasi:
        print()
        print("Quasi nuove")
        for r in quasi:
            print(f"  {r['rel'].as_posix()}  ({r['blocks']} blocchi)")

    if show_all:
        print()
        print("Elenco per sezione")
        by_section = defaultdict(list)
        for r in rows:
            by_section[section_of(r["rel"])].append(r)
        for section in sorted(by_section):
            items = by_section[section]
            print(f"\n{section} ({len(items)})")
            for r in items:
                tags = "·".join(m for m in MARKERS if m in r["markers"])
                print(f"  {r['name']:<50} {r['class']:<8} {tags}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
