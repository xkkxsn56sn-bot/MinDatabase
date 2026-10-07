#!/usr/bin/env python3
"""Regola dei nomi delle immagini sotto Content/Codex/ (vedi «Codex Image Names»
nel file delle istruzioni).

Modulo condiviso, senza dipendenze, da due consumatori:
  - scripts/rename_codex_images.py ricava i nomi dalle didascalie;
  - scripts/validate_content_indexes.py (check 12) verifica che i nomi
    esistenti rispettino la regola e coincidano con il foglio della didascalia.

La didascalia e' la fonte: il nome ne deriva, mai il contrario.
"""
import re

DEFAULT_WIDTH = 3
WIDTH = {"Codex-Amiatinus": 4}

# Conflitti di foglio aperti nelle schede: due didascalie rivendicano lo stesso
# foglio senza essere dettaglio o seconda fonte. Il file resta col nome che ha,
# il controllo lo salta, finche' la scheda non decide (vedi pending-checks).
OPEN_CONFLICTS = {("Godescalc-Evangelistary", "godescalc-evangelistary-07.jpg")}

LABELS = ("cover-front", "cover-back", "spine", "binding", "shrine", "satchel")
CONTEXT_RE = r"context-[a-z0-9]+(?:-[a-z0-9]+)*"

FOL = r"(?:fols?\.?|folios?)"
OPENING_RE = re.compile(FOL + r"\s*(\d+)([rv])\s*[-–]\s*(\d+)([rv])\b", re.I)
LEAF_RE = re.compile(FOL + r"\s*(\d+)([rv])\b", re.I)
ROMAN_RE = re.compile(r"\bfols?\.?\s*([IVXLC]+)([rv])\b")
PAGE_RE = re.compile(r"\bpp?\.\s*(\d+)\b", re.I)
RANGE_RE = re.compile(FOL + r"\s*(\d+)\s*[-–]\s*(\d+)\b", re.I)


def slug_of(basename):
    return basename.lower()


def width_of(basename):
    return WIDTH.get(basename, DEFAULT_WIDTH)


def locator_from_caption(caption, width):
    """Il luogo del foglio nella didascalia, nella forma dei nomi, o None."""
    text = re.sub(r"<[^>]+>", "", caption)
    m = OPENING_RE.search(text)
    if m:
        return f"f{int(m[1]):0{width}d}{m[2].lower()}-{int(m[3]):0{width}d}{m[4].lower()}"
    m = LEAF_RE.search(text)
    if m:
        return f"f{int(m[1]):0{width}d}{m[2].lower()}"
    m = ROMAN_RE.search(text)
    if m:
        return f"f-{m[1].lower()}-{m[2]}"
    m = PAGE_RE.search(text)
    if m:
        return f"p{int(m[1]):0{width}d}"
    m = RANGE_RE.search(text)
    if m:
        return f"f{int(m[1]):0{width}d}-{int(m[2]):0{width}d}"
    return None


def name_re(basename):
    slug = re.escape(slug_of(basename))
    return re.compile(
        rf"^{slug}-(?:(?P<loc>f\d+[rv](?:-\d+[rv])?|f-[ivxlc]+-[rv]|f\d+-\d+|p\d+)"
        rf"(?P<suf>(?:-d\d{{2}}|-alt)*)"
        rf"|(?P<label>{'|'.join(LABELS)}|{CONTEXT_RE})|(?P<num>\d{{2}}))"
        rf"\.(?:jpe?g|png|webp|mp4)$"
    )


def check_name(basename, folder, filename, caption):
    """Messaggio di errore, o None se il nome rispetta la regola."""
    if (basename, filename) in OPEN_CONFLICTS:
        return None
    if folder != basename:
        return f"cartella '{folder}' invece di '{basename}'"
    m = name_re(basename).match(filename)
    if not m:
        return f"'{filename}' non rispetta la forma {slug_of(basename)}-<foglio|etichetta>"
    expected = locator_from_caption(caption, width_of(basename))
    if expected is None:
        if m["loc"]:
            return f"'{filename}' nomina un foglio, la didascalia no"
        return None
    if not m["loc"]:
        return f"la didascalia dice {expected}, il nome no"
    if m["loc"] != expected:
        return f"la didascalia dice {expected}, il nome {m['loc']}"
    return None
