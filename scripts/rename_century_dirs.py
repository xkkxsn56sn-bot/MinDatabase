#!/usr/bin/env python3
"""
rename_century_dirs.py

Rinomina le directory dei secoli in Content/Artists/ da "IX century" a "IX-c"
e aggiorna di conseguenza tutti i link entranti nel repository.

PERCHE' NON UN SED
    La stringa "IX century" compare sia negli URL sia nel testo discorsivo
    delle schede. Una sostituzione globale corromperebbe la prosa. Questo
    script sostituisce SOLO dentro il valore degli attributi href/src e dei
    link Markdown; le occorrenze in prosa vengono elencate ma non toccate.

FORME RICONOSCIUTE NEGLI URL
    IX%20century   spazio percent-encoded
    IX century     spazio letterale
    IX+century     spazio come plus
    IX_century     underscore
    maiuscolo/minuscolo indifferente su "century"

USO
    python3 rename_century_dirs.py            # dry-run, non scrive nulla
    python3 rename_century_dirs.py --apply    # esegue le modifiche

Eseguire dalla radice del repo (~/Sites/MinDatabase).
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path.cwd()
ARTISTS_DIR = REPO / "Content" / "Artists"

# Dove cercare i link entranti.
SEARCH_GLOBS = ["**/*.md", "**/*.html", "**/*.css", "**/*.js", "**/*.yml", "**/*.json"]

# Cartelle da ignorare.
SKIP_PARTS = {"_site", ".git", "node_modules", "__pycache__", ".jekyll-cache"}

# Nome di directory da rinominare: numero romano + "century".
DIR_PATTERN = re.compile(r"^([IVXLC]+)\s+centur(?:y|ies)$", re.IGNORECASE)

# Estrazione dei valori di URL: attributi HTML e link Markdown.
ATTR_RE = re.compile(r'(?P<attr>\b(?:href|src|content|url)\s*=\s*")(?P<val>[^"]*)(?P<end>")')
ATTR_SQ_RE = re.compile(r"(?P<attr>\b(?:href|src|content|url)\s*=\s*')(?P<val>[^']*)(?P<end>')")
MD_RE = re.compile(r"(?P<open>\]\()(?P<val>[^)\s]*)(?P<end>[)\s])")

# YAML/JSON: url: "/Content/Artists/..." oppure "href": "..." (chiave tra virgolette o no).
YAML_URL_RE = re.compile(
    r'(?P<attr>^\s*-?\s*["\']?(?:url|link|href|permalink)["\']?\s*:\s*["\']?)(?P<val>[^"\'\n]*)(?P<end>["\']?\s*,?\s*$)',
    re.MULTILINE,
)


def build_mapping():
    """Legge le directory esistenti e costruisce {vecchio_nome: nuovo_nome}."""
    if not ARTISTS_DIR.is_dir():
        sys.exit(f"ERRORE: {ARTISTS_DIR} non trovata. Esegui dalla radice del repo.")

    mapping = {}
    for entry in sorted(ARTISTS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        m = DIR_PATTERN.match(entry.name)
        if m:
            roman = m.group(1).upper()
            mapping[entry.name] = f"{roman}-c"
    return mapping


def url_patterns(mapping):
    """Regex per ciascun secolo, ordinate per numero romano piu' lungo prima.

    L'ordine conta: senza di esso "XIV" rischia di essere intercettato da una
    regola scritta per "XI". I lookaround impediscono match parziali.
    """
    pats = []
    for old, new in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
        roman = DIR_PATTERN.match(old).group(1)
        pat = re.compile(
            r"(?<![A-Za-z0-9])" + re.escape(roman) + r"(?:%20|\s|\+|_)+[Cc]entur(?:y|ies)(?![A-Za-z0-9])"
        )
        pats.append((pat, new, old))
    return pats


def rewrite_urls(text, pats):
    """Sostituisce dentro i soli valori di URL. Restituisce (nuovo_testo, n_sost)."""
    count = 0

    def fix_value(value):
        nonlocal count
        for pat, new, _old in pats:
            value, n = pat.subn(new, value)
            count += n
        return value

    def repl(m):
        return m.group("attr") + fix_value(m.group("val")) + m.group("end")

    def repl_md(m):
        return m.group("open") + fix_value(m.group("val")) + m.group("end")

    text = ATTR_RE.sub(repl, text)
    text = ATTR_SQ_RE.sub(repl, text)
    text = MD_RE.sub(repl_md, text)
    text = YAML_URL_RE.sub(repl, text)
    return text, count


def find_prose_hits(text, pats):
    """Occorrenze fuori dagli attributi: solo per segnalazione, non modificate."""
    # Rimuove i valori di attributo e i link Markdown, poi cerca nel resto.
    stripped = ATTR_RE.sub("", text)
    stripped = ATTR_SQ_RE.sub("", stripped)
    stripped = MD_RE.sub("", stripped)
    stripped = YAML_URL_RE.sub("", stripped)
    hits = []
    for pat, _new, _old in pats:
        for m in pat.finditer(stripped):
            hits.append(m.group(0))
    return hits


def iter_files():
    seen = set()
    for glob in SEARCH_GLOBS:
        for path in REPO.glob(glob):
            if not path.is_file():
                continue
            if SKIP_PARTS & set(path.parts):
                continue
            if path in seen:
                continue
            seen.add(path)
            yield path


def main():
    apply_changes = "--apply" in sys.argv

    mapping = build_mapping()
    if not mapping:
        sys.exit("Nessuna directory nella forma '<romano> century' trovata. Nulla da fare.")

    print("RINOMINE PREVISTE")
    for old, new in mapping.items():
        print(f"  Content/Artists/{old!r}  ->  Content/Artists/{new!r}")
    print()

    pats = url_patterns(mapping)

    touched = []
    total_subs = 0
    prose_report = {}

    for path in iter_files():
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        new_text, n = rewrite_urls(original, pats)
        prose = find_prose_hits(original, pats)
        if prose:
            prose_report[path] = prose

        if n:
            total_subs += n
            touched.append((path, n))
            if apply_changes:
                path.write_text(new_text, encoding="utf-8")

    print(f"LINK AGGIORNATI: {total_subs} in {len(touched)} file")
    for path, n in sorted(touched, key=lambda t: -t[1]):
        print(f"  {n:4d}  {path.relative_to(REPO)}")
    print()

    if prose_report:
        print("OCCORRENZE IN PROSA (non modificate, da rivedere a mano se serve)")
        for path, hits in sorted(prose_report.items()):
            uniq = sorted(set(hits))
            print(f"  {path.relative_to(REPO)}: {', '.join(uniq)}")
        print()

    if not apply_changes:
        print("Dry-run: nessun file scritto, nessuna directory rinominata.")
        print("Per eseguire davvero:  python3 rename_century_dirs.py --apply")
        return 0

    print("RINOMINA DIRECTORY")
    for old, new in mapping.items():
        src = ARTISTS_DIR / old
        dst = ARTISTS_DIR / new
        if dst.exists():
            print(f"  SALTATA: {dst} esiste gia'")
            continue
        result = subprocess.run(
            ["git", "mv", str(src), str(dst)],
            cwd=REPO, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"  ok: {old!r} -> {new!r}")
        else:
            print(f"  ERRORE su {old!r}: {result.stderr.strip()}")

    print()
    print("Fatto. Prossimi passi: jekyll build, poi controllo dei 404.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
