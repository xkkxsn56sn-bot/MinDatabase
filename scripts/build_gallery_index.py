#!/usr/bin/env python3
"""
build_gallery_index.py

Estrae tutte le figure dalle schede sotto Content/ e scrive
assets/data/gallery-index.json, consumato dalla pagina gallery.html.

PERCHE' UNO SCRIPT E NON LIQUID
    Le figure sono HTML scritto dentro il Markdown, quindi Jekyll le tratta
    come testo opaco: Liquid non puo' leggerle come dati strutturati. Un
    estrattore in Python fa il lavoro una volta e produce un indice pulito,
    sullo stesso modello di update_push_notices.py.

CAMPI EMESSI PER OGNI FIGURA
    src       percorso dell'immagine
    alt       testo alternativo (descrizione visiva)
    caption   testo della figcaption (didascalia scientifica)
    entry     titolo della scheda di provenienza, dal frontmatter
    section   Artists, Churches, Codex, Papers, Saints
    century   solo per gli artisti, ricavato dalla cartella
    url       percorso della scheda pubblicata

USO
    python3 scripts/build_gallery_index.py

Eseguire dalla radice del repo. Va rilanciato quando si aggiungono figure;
in CI puo' essere agganciato allo stesso workflow che valida i contenuti.
"""

import json
import re
import sys
from pathlib import Path

REPO = Path.cwd()
CONTENT = REPO / "Content"
OUTPUT = REPO / "assets" / "data" / "gallery-index.json"

EXCLUDED_TOP_DIRS = {"prompts"}

# <figure> con eventuali classi, fino alla chiusura. re.S perche' il blocco
# si estende su piu' righe.
FIGURE_RE = re.compile(r"<figure\b[^>]*>(.*?)</figure>", re.S | re.I)
IMG_SRC_RE = re.compile(r'<img\b[^>]*\bsrc="([^"]+)"', re.S | re.I)
IMG_ALT_RE = re.compile(r'<img\b[^>]*\balt="([^"]*)"', re.S | re.I)
CAPTION_RE = re.compile(r"<figcaption\b[^>]*>(.*?)</figcaption>", re.S | re.I)

# Il titolo sta nel frontmatter, che qui si legge in modo minimale:
# non serve un parser YAML per una sola chiave di primo livello.
TITLE_RE = re.compile(r'^title:\s*"?(.*?)"?\s*$', re.M)

# Il secolo si ricava dal path solo per gli Artists, che sono organizzati in
# cartelle XIII-c, XIV-c e simili. Codex, Saints e Papers non hanno quella
# struttura, quindi possono dichiararlo nel frontmatter con una chiave
# century: (numero romano, stesso formato del path: "X", "XIV"). Quando c'e',
# vince sul fallback dal path.
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)
CENTURY_RE = re.compile(r'^century:\s*"?(.*?)"?\s*$', re.M)

# Markup residuo nelle didascalie: *corsivo*, <em>, entita'.
MD_EMPHASIS_RE = re.compile(r"\*{1,2}([^*]+)\*{1,2}")
TAG_RE = re.compile(r"<[^>]+>")


def clean_text(s):
    """Riduce la didascalia a testo semplice.

    Le figcaption contengono corsivi Markdown e talvolta tag inline; nella
    galleria servono come testo, non come markup.
    """
    s = MD_EMPHASIS_RE.sub(r"\1", s)
    s = TAG_RE.sub("", s)
    s = s.replace("&amp;", "&").replace("&nbsp;", " ")
    return " ".join(s.split())


def entry_title(text, fallback):
    m = TITLE_RE.search(text)
    return m.group(1).strip() if m else fallback


def front_matter(text):
    m = FRONT_MATTER_RE.match(text)
    return m.group(1) if m else ""


def declared_century(text):
    """Secolo dichiarato nel frontmatter, stringa vuota se assente.

    Si cerca solo dentro il frontmatter: una riga che comincia per 'century:'
    nel corpo della scheda non deve essere scambiata per un campo.
    """
    m = CENTURY_RE.search(front_matter(text))
    return m.group(1).strip() if m else ""


def page_url(md_path):
    rel = md_path.relative_to(REPO).as_posix()
    return "/" + rel[:-3] + ".html"


def main():
    if not CONTENT.is_dir():
        sys.exit(f"ERRORE: {CONTENT} non trovata. Esegui dalla radice del repo.")

    figures = []
    files_with_figures = 0

    md_files = [
        p
        for p in sorted(CONTENT.rglob("*.md"))
        if p.relative_to(CONTENT).parts[0] not in EXCLUDED_TOP_DIRS
    ]

    for md in md_files:
        try:
            text = md.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        blocks = FIGURE_RE.findall(text)
        if not blocks:
            continue
        files_with_figures += 1

        parts = md.relative_to(CONTENT).parts
        section = parts[0]
        century = declared_century(text)
        if not century and section == "Artists" and len(parts) > 2:
            century = parts[1].replace("-c", "")

        title = entry_title(text, md.stem.replace("-", " "))
        url = page_url(md)

        for block in blocks:
            src_m = IMG_SRC_RE.search(block)
            if not src_m:
                continue
            src = src_m.group(1).strip()

            alt_m = IMG_ALT_RE.search(block)
            cap_m = CAPTION_RE.search(block)

            figures.append(
                {
                    "src": src,
                    "alt": clean_text(alt_m.group(1)) if alt_m else "",
                    "caption": clean_text(cap_m.group(1)) if cap_m else "",
                    "entry": title,
                    "section": section,
                    "century": century,
                    "url": url,
                }
            )

    # Ordine: sezione, poi secolo, poi titolo della scheda. Le figure di una
    # stessa scheda restano nell'ordine in cui compaiono nel testo.
    section_order = {"Artists": 0, "Churches": 1, "Codex": 2, "Papers": 3, "Saints": 4}
    # Arco plausibile per il sito: dai Padri tardoantichi al Quattrocento.
    # Tenerlo largo evita di dover ritoccare la mappa a ogni nuova scheda.
    roman = {"IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10,
             "XI": 11, "XII": 12, "XIII": 13, "XIV": 14, "XV": 15}

    figures.sort(
        key=lambda f: (
            section_order.get(f["section"], 9),
            roman.get(f["century"], 99),
            f["entry"].lower(),
        )
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(figures, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    print(f"Schede esaminate: {len(md_files)}")
    print(f"Schede con figure: {files_with_figures}")
    print(f"Figure indicizzate: {len(figures)}")

    missing = [f["src"] for f in figures if not (REPO / f["src"].lstrip("/")).exists()]
    if missing:
        print()
        print(f"ATTENZIONE: {len(missing)} immagini referenziate ma non trovate:")
        for m in sorted(set(missing))[:20]:
            print(f"  {m}")

    no_caption = sum(1 for f in figures if not f["caption"])
    if no_caption:
        print(f"Figure senza didascalia: {no_caption}")

    print()
    print(f"Scritto: {OUTPUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
