#!/usr/bin/env python3
"""
validate_reachability.py

Verifica che le pagine deliberatamente escluse dalla navigazione principale
abbiano almeno un link entrante dal resto del sito.

Contesto: alcune pagine sono raggiungibili solo per link contestuale, per
scelta editoriale — le schede in Content/Saints/, piu' gli indici
painters.html e scholars.html. Se l'ultimo link entrante sparisce durante
una revisione, quelle pagine diventano invisibili senza che nulla lo segnali.

USCITA
    exit 0  ogni target ha almeno un link entrante
    exit 1  almeno un target e' irraggiungibile

Le pagine con un solo link entrante producono un avviso, non un errore.

USO
    python3 scripts/validate_reachability.py
Eseguire dalla radice del repo.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Cartelle i cui file .md sono target da sorvegliare.
WATCHED_DIRS = ["Content/Saints"]

# Singole pagine da sorvegliare (path relativi alla radice del repo).
WATCHED_PAGES = ["painters.html", "scholars.html"]

# Dove cercare i link entranti.
SEARCH_GLOBS = ["Content/**/*.md", "Content/**/*.html", "*.html"]

# Cartelle da ignorare nella ricerca.
SKIP_PARTS = {"_site", ".git", "node_modules", "__pycache__"}

WARN_THRESHOLD = 2  # sotto questa soglia: avviso, non errore


def collect_targets():
    """Restituisce una lista di (etichetta, pattern_di_ricerca, path_sorgente)."""
    targets = []

    for rel_dir in WATCHED_DIRS:
        directory = REPO / rel_dir
        if not directory.is_dir():
            print(f"[ATTENZIONE] cartella assente: {rel_dir}")
            continue
        for md in sorted(directory.glob("*.md")):
            # Il link punta all'output .html, non al sorgente .md.
            pattern = f"/{rel_dir}/{md.stem}.html"
            targets.append((md.stem, pattern, md))

    for rel_page in WATCHED_PAGES:
        page = REPO / rel_page
        if not page.is_file():
            print(f"[ATTENZIONE] pagina assente: {rel_page}")
            continue
        targets.append((rel_page, f"/{rel_page}", page))

    return targets


def collect_sources():
    """Tutti i file in cui cercare link entranti."""
    seen = set()
    for pattern in SEARCH_GLOBS:
        for path in REPO.glob(pattern):
            if not path.is_file():
                continue
            if SKIP_PARTS & set(path.parts):
                continue
            seen.add(path)
    return sorted(seen)


def count_inbound(pattern, source_path, sources):
    """Conta i file distinti che contengono il pattern, escluso il target stesso."""
    # Confine a destra: il pattern non deve essere prefisso di un path piu' lungo.
    regex = re.compile(re.escape(pattern) + r'(?=["\'#?\s>)]|$)')
    linkers = []
    for path in sources:
        if path == source_path:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if regex.search(text):
            linkers.append(path.relative_to(REPO))
    return linkers


def main():
    if not (REPO / "Content").is_dir():
        print("Eseguire dalla radice del repo.")
        return 2

    targets = collect_targets()
    if not targets:
        print("Nessun target da verificare.")
        return 2

    sources = collect_sources()
    print(f"Sorgenti esaminate: {len(sources)}")
    print(f"Target sorvegliati: {len(targets)}\n")

    errors, warnings = [], []
    width = max(len(label) for label, _, _ in targets)

    for label, pattern, source_path in targets:
        linkers = count_inbound(pattern, source_path, sources)
        n = len(linkers)

        if n == 0:
            status = "IRRAGGIUNGIBILE"
            errors.append((label, pattern))
        elif n < WARN_THRESHOLD:
            status = "fragile"
            warnings.append((label, linkers))
        else:
            status = "ok"

        print(f"{label:<{width}}  {n:>3}  {status}")

    if warnings:
        print("\nPagine con un solo link entrante:")
        for label, linkers in warnings:
            print(f"  {label} <- {linkers[0]}")
        print("Se quel riferimento venisse rimosso, la pagina sparirebbe.")

    if errors:
        print("\nERRORE: pagine senza alcun link entrante:")
        for label, pattern in errors:
            print(f"  {label}  (cercato: {pattern})")
        print(
            "\nQueste pagine sono escluse dalla navigazione per scelta editoriale,\n"
            "quindi senza link contestuali non sono raggiungibili in alcun modo."
        )
        return 1

    print("\nTutti i target hanno almeno un link entrante.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
