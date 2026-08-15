#!/usr/bin/env python3
"""
validate_nav_consistency.py

Verifica che le pagine con la navigazione scritta a mano abbiano lo stesso
menu di _includes/nav.html.

Contesto: cinque layout usano {% include nav.html %} e restano allineati da
soli. Tre pagine di primo livello (artists.html, codices.html, papers.html)
non passano da Jekyll e replicano il menu nel proprio markup: se una voce
viene aggiunta o rimossa dalla include, quelle tre restano indietro senza
che nulla lo segnali.

Il confronto e' sul nome del file di destinazione e sull'etichetta, non sulla
forma del link: la include scrive {{ '/index.html' | relative_url }}, le
pagine autonome scrivono index.html. Sono equivalenti e vanno trattate tali.

USCITA
    exit 0  tutte le nav coincidono con la include
    exit 1  almeno una diverge

USO
    python3 scripts/validate_nav_consistency.py
Eseguire dalla radice del repo.
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

INCLUDE = REPO / "_includes" / "nav.html"

# Pagine che replicano il menu invece di usare la include.
INLINE_PAGES = ["artists.html", "codices.html", "papers.html"]

NAV_OPEN = re.compile(r'<nav[^>]*aria-label="Main navigation"[^>]*>', re.I)
LINK = re.compile(r'<a\s+[^>]*href="([^"]*)"[^>]*>(.*?)</a>', re.I | re.S)


def extract_nav_block(text, source):
    """Estrae il contenuto del <nav> principale. None se assente."""
    match = NAV_OPEN.search(text)
    if not match:
        return None
    rest = text[match.end():]
    close = rest.lower().find("</nav>")
    if close == -1:
        print(f"[ERRORE] {source}: <nav> aperto e mai chiuso.")
        return None
    return rest[:close]


def normalize_href(href):
    """
    Riduce un href al solo nome del file di destinazione, ignorando lo slash finale.

    Riconosce sia i letterali (index.html, /index.html) sia i filtri Liquid
    ({{ '/index.html' | relative_url }}). Un href puo' finire con '/'
    (glossary/, /dating-systems/): senza il rstrip lo split restituirebbe
    stringa vuota, e il confronto fra due voci diverse passerebbe perche'
    entrambe collassano a ''.
    """
    href = href.strip()
    liquid = re.search(r"""['"]([^'"]+)['"]""", href)
    if liquid:
        href = liquid.group(1)
    return href.lstrip("/").rstrip("/").split("/")[-1]


def extract_entries(text, source):
    """Lista di (file_destinazione, etichetta) dal blocco nav."""
    block = extract_nav_block(text, source)
    if block is None:
        return None
    entries = []
    for href, label in LINK.findall(block):
        entries.append((normalize_href(href), " ".join(label.split())))
    return entries


def describe(entries):
    return ", ".join(f"{label} -> {target}" for target, label in entries)


def main():
    if not INCLUDE.is_file():
        print(f"[ERRORE] manca {INCLUDE.relative_to(REPO)}")
        return 2

    reference = extract_entries(INCLUDE.read_text(encoding="utf-8"), "nav.html")
    if not reference:
        print("[ERRORE] nessun link trovato in _includes/nav.html.")
        return 2

    print(f"Riferimento ({len(reference)} voci): {describe(reference)}\n")

    failures = []

    for rel_page in INLINE_PAGES:
        page = REPO / rel_page
        if not page.is_file():
            print(f"{rel_page:<16} ASSENTE")
            failures.append((rel_page, "file assente", None))
            continue

        entries = extract_entries(page.read_text(encoding="utf-8"), rel_page)

        if entries is None:
            print(f"{rel_page:<16} nessun <nav> principale")
            failures.append((rel_page, "nav principale assente", None))
        elif entries == reference:
            print(f"{rel_page:<16} ok")
        else:
            print(f"{rel_page:<16} DIVERGE")
            failures.append((rel_page, "menu diverso", entries))

    if failures:
        print("\nERRORE: navigazione non allineata.\n")
        for rel_page, reason, entries in failures:
            print(f"  {rel_page}: {reason}")
            if entries is not None:
                missing = [e for e in reference if e not in entries]
                extra = [e for e in entries if e not in reference]
                if missing:
                    print(f"    mancano:  {describe(missing)}")
                if extra:
                    print(f"    in piu':  {describe(extra)}")
                if not missing and not extra:
                    print("    stesse voci, ordine diverso")
        print(
            "\nQueste pagine non passano da Jekyll e replicano il menu nel loro\n"
            "markup: vanno aggiornate a mano quando cambia _includes/nav.html."
        )
        return 1

    print("\nTutte le nav inline coincidono con la include.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
