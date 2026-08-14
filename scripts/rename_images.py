#!/usr/bin/env python3
"""
rename_images.py

Elimina gli spazi dai nomi di cartelle e file sotto Images/, e aggiorna tutti
i riferimenti nel repository.

TRASFORMAZIONE
    Images/Alberto Sozio/image 1.jpg  ->  Images/Alberto-Sozio/alberto-sozio-01.jpg
    Images/Giotto/image 3.jpg         ->  Images/Giotto/giotto-03.jpg

    Cartella: gli spazi diventano trattini, il resto del nome non si tocca.
    File nella forma 'image N.<est>': prende il nome dalla cartella (in
    minuscolo) piu' il numero a due cifre. Lo zero iniziale serve a mantenere
    l'ordinamento oltre la decima immagine.
    File in altre forme: solo spazi -> trattini, nome invariato. Non si inventa
    una struttura per casi non previsti.

    NOTA DI SCOPO: questo script risolve solo il problema degli spazi. Non
    allinea i nomi delle cartelle a quelli delle schede (Images/Giotto resta
    Giotto anche se la scheda e' Giotto-di-Bondone): quella e' catalogazione,
    va decisa caso per caso e non e' automatizzabile.

CONFLITTI
    Se due file di una stessa cartella pretendono lo stesso nome nuovo, lo
    script NON rinomina nulla in quella cartella e segnala il conflitto.

USO
    python3 scripts/rename_images.py            # dry-run, non scrive nulla
    python3 scripts/rename_images.py --apply    # esegue

Eseguire dalla radice del repo.
"""

import re
import subprocess
import sys
import unicodedata
import urllib.parse
from collections import defaultdict
from pathlib import Path

REPO = Path.cwd()
IMAGES = REPO / "Images"

# Dove cercare i riferimenti alle immagini.
SEARCH_GLOBS = ["Content/**/*.md", "Content/**/*.html", "*.html",
                "_layouts/*.html", "_includes/*.html", "assets/**/*.json",
                "assets/**/*.js", "assets/**/*.css"]

SKIP_PARTS = {"_site", ".git", "node_modules", "__pycache__", ".jekyll-cache"}

IMAGE_N_RE = re.compile(r"^image\s+(\d+)\.(\w+)$", re.IGNORECASE)


def slugify_folder(name):
    """'Alberto Sozio' -> 'Alberto-Sozio'. Solo spazi, nient'altro."""
    return re.sub(r"\s+", "-", name.strip())


def slug_lower(name):
    """'Alberto-Sozio' -> 'alberto-sozio', per comporre i nomi dei file."""
    return slugify_folder(name).lower()


def plan():
    """Costruisce la mappa {percorso_vecchio: percorso_nuovo}, relativa al repo.

    Restituisce (mapping, conflitti). I percorsi sono stringhe con '/'.
    """
    mapping = {}
    conflicts = []

    if not IMAGES.is_dir():
        sys.exit(f"ERRORE: {IMAGES} non trovata. Esegui dalla radice del repo.")

    for folder in sorted(p for p in IMAGES.iterdir() if p.is_dir()):
        new_folder_name = slugify_folder(folder.name)
        base = slug_lower(folder.name)

        proposed = {}   # nuovo_nome_file -> [vecchi_nomi]
        for f in sorted(folder.iterdir()):
            if not f.is_file():
                continue
            m = IMAGE_N_RE.match(f.name)
            if m:
                new_name = f"{base}-{int(m.group(1)):02d}.{m.group(2).lower()}"
            else:
                new_name = re.sub(r"\s+", "-", f.name)
            proposed.setdefault(new_name, []).append(f.name)

        clash = {k: v for k, v in proposed.items() if len(v) > 1}
        if clash:
            for new_name, olds in sorted(clash.items()):
                conflicts.append(
                    f"Images/{folder.name}: {', '.join(olds)} -> tutti '{new_name}'"
                )
            continue  # cartella intera saltata

        for new_name, olds in proposed.items():
            old_name = olds[0]
            if old_name == new_name and folder.name == new_folder_name:
                continue
            mapping[f"Images/{folder.name}/{old_name}"] = \
                f"Images/{new_folder_name}/{new_name}"

        # File assenti a parte, la cartella va comunque rinominata.
        if folder.name != new_folder_name:
            mapping.setdefault(f"Images/{folder.name}",
                               f"Images/{new_folder_name}")

    return mapping, conflicts


def reference_forms(path_str):
    """Le forme in cui un percorso puo' comparire nei file di testo.

    Uno spazio nel filesystem puo' essere scritto come spazio letterale o come
    %20 in un URL. Entrambe vanno sostituite.
    """
    forms = {path_str, urllib.parse.quote(path_str, safe="/.")}
    forms.add(path_str.replace(" ", "%20"))
    return {f for f in forms if f}


def iter_files():
    seen = set()
    for glob in SEARCH_GLOBS:
        for path in REPO.glob(glob):
            if not path.is_file() or path in seen:
                continue
            if SKIP_PARTS & set(path.parts):
                continue
            seen.add(path)
            yield path


def rewrite_references(mapping, apply_changes):
    """Sostituisce i percorsi vecchi con i nuovi. Ordine: i piu' lunghi prima,
    cosi' un percorso di file non viene spezzato dalla regola della cartella."""
    ordered = sorted(mapping.items(), key=lambda kv: -len(kv[0]))

    touched = []
    total = 0

    for path in iter_files():
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        text = original
        n = 0
        for old, new in ordered:
            for form in reference_forms(old):
                if form in text:
                    count = text.count(form)
                    text = text.replace(form, new)
                    n += count

        if n:
            total += n
            touched.append((path, n))
            if apply_changes:
                path.write_text(text, encoding="utf-8")

    return total, touched


def is_tracked(rel_path):
    r = subprocess.run(["git", "ls-files", "--error-unmatch", rel_path],
                       cwd=REPO, capture_output=True, text=True)
    return r.returncode == 0


def do_renames(mapping):
    """Rinomina prima i file, poi le cartelle: altrimenti i percorsi dei file
    puntano a una cartella che non esiste piu'."""
    files = {k: v for k, v in mapping.items() if (REPO / k).is_file()}
    dirs = {k: v for k, v in mapping.items() if (REPO / k).is_dir()}

    for old, new in sorted(files.items()):
        src, dst = REPO / old, REPO / new
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            print(f"  SALTATO (esiste): {new}")
            continue
        if is_tracked(old):
            r = subprocess.run(["git", "mv", old, new], cwd=REPO,
                               capture_output=True, text=True)
            if r.returncode != 0:
                print(f"  ERRORE git mv {old}: {r.stderr.strip()}")
        else:
            src.rename(dst)

    for old, new in sorted(dirs.items()):
        src, dst = REPO / old, REPO / new
        if not src.exists():
            continue
        if dst.exists():
            # I file sono gia' stati spostati; se resta vuota, si rimuove.
            try:
                src.rmdir()
            except OSError:
                print(f"  ATTENZIONE: {old} non vuota, non rimossa")
            continue
        if is_tracked(old):
            subprocess.run(["git", "mv", old, new], cwd=REPO,
                           capture_output=True, text=True)
        else:
            src.rename(dst)


def main():
    apply_changes = "--apply" in sys.argv

    mapping, conflicts = plan()

    if conflicts:
        print(f"CONFLITTI DI NOME ({len(conflicts)}) - cartelle saltate per intero")
        for c in conflicts:
            print(f"  {c}")
        print()

    print(f"RINOMINE PREVISTE: {len(mapping)}")
    for old, new in sorted(mapping.items())[:15]:
        print(f"  {old}  ->  {new}")
    if len(mapping) > 15:
        print(f"  ... e altre {len(mapping) - 15}")
    print()

    total, touched = rewrite_references(mapping, apply_changes)
    print(f"RIFERIMENTI DA AGGIORNARE: {total} in {len(touched)} file")
    for path, n in sorted(touched, key=lambda t: -t[1])[:15]:
        print(f"  {n:5d}  {path.relative_to(REPO)}")
    if len(touched) > 15:
        print(f"  ... e altri {len(touched) - 15} file")
    print()

    if not apply_changes:
        print("Dry-run: nessun file scritto, nessuna rinomina eseguita.")
        print("Per eseguire:  python3 scripts/rename_images.py --apply")
        return 0

    print("RINOMINA IN CORSO")
    do_renames(mapping)
    print()
    print("Fatto. Verifica con: jekyll build, poi controllo dei riferimenti.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
