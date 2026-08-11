#!/usr/bin/env python3
"""Valida la coerenza tra Content/*.md e gli indici JSON in assets/data/.

Sola lettura: non modifica alcun file. Controlli eseguiti:

1. Ogni .md sotto Content/ (esclusa prompts/ e Saints/, vedi NO_INDEX_DIRS
   sotto) ha una voce nel JSON della sua sezione (Artists ->
   artists-directory.json per "<secolo> Century"; Churches/Codex/Papers ->
   il rispettivo JSON mono-sezione).
2. Ogni href nei quattro JSON risolve a un .md esistente (gestendo %20 e le
   forme Unicode composte/decomposte, NFC/NFD).
3. Ogni .md (Saints/ inclusa) ha un frontmatter delimitato da "---" chiuso,
   con "layout" e "title" non vuoti. Non essendo disponibile un parser YAML
   in libreria standard, la validazione è una verifica strutturale leggera
   (righe di primo livello nella forma "chiave: valore"), non un parser
   YAML completo.
4. Le voci di ogni sezione sono ordinate alfabeticamente per "name",
   replicando la logica di sort_artists_directory.js (localeCompare "it",
   sensitivity "base"): confronto case-insensitive e senza diacritici,
   tramite normalizzazione NFKD + casefold.
5. Nessun basename di file .md (Saints/ inclusa) contiene spazi.
6. Ogni .md in Content/Saints/ è linkato (via href "Content/...html", in
   markdown o in frontmatter) da almeno un'altra scheda sotto Content/.
   Saints/ non ha una pagina elenco: le schede dei santi sono raggiungibili
   solo per link da altre schede, quindi una scheda non linkata da nessuno
   è di fatto irraggiungibile.

Non confronta "name" (JSON) con "title" (frontmatter): le divergenze fra i
due sono scelte editoriali volute e non un errore da segnalare qui.

Uscita: codice 1 se vengono trovate anomalie, 0 altrimenti.
"""

import json
import re
import sys
import unicodedata
import urllib.parse
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "Content"
DATA_DIR = REPO_ROOT / "assets" / "data"

EXCLUDED_TOP_DIRS = {"prompts"}

# Cartelle di primo livello sotto Content/ che hanno un JSON di indice
# associato, e il relativo file.
SECTION_JSON = {
    "Artists": DATA_DIR / "artists-directory.json",
    "Churches": DATA_DIR / "churches-directory.json",
    "Codex": DATA_DIR / "codices-directory.json",
    "Papers": DATA_DIR / "papers-directory.json",
}

# Content/Saints/ è, per scelta editoriale, una sezione senza pagina elenco:
# le schede dei santi sono raggiungibili solo tramite link da altre schede,
# non da un JSON di indice dedicato. Va quindi esclusa dal controllo 1
# (presenza in un JSON di sezione) e non compare in SECTION_JSON; resta
# invece soggetta a tutti gli altri controlli (frontmatter, layout/title,
# basename senza spazi) e al controllo 6, che verifica che sia comunque
# raggiungibile tramite almeno un link da un'altra scheda.
NO_INDEX_DIRS = {"Saints"}

# Riconosce riferimenti ad altre schede sotto Content/ sia nei link markdown
# (es. "[testo](/Content/Saints/Saint-Ambrose.html)") sia nei campi
# frontmatter tipo `url: "/Content/Saints/Saint-Cuthbert.html"`.
LINK_RE = re.compile(r"/?Content/[^\s\"'()<>]+\.html")

CENTURY_FOLDER_RE = re.compile(r"^([IVXLCDM]+)-c$", re.IGNORECASE)


def folder_to_century_key(folder_name):
    """'VII-c' -> 'VII Century' (chiave attesa in artists-directory.json)."""
    m = CENTURY_FOLDER_RE.match(folder_name)
    if not m:
        return None
    return f"{m.group(1).upper()} Century"


def href_to_rel_path(href):
    """Converte un href del JSON nel percorso relativo al repo del .md."""
    decoded = urllib.parse.unquote(href)
    decoded = decoded.lstrip("/")
    if decoded.endswith(".html"):
        decoded = decoded[:-5] + ".md"
    return decoded


def resolve_existing_path(rel_path):
    """Risolve rel_path su disco provando anche le forme Unicode NFC/NFD."""
    candidates = {
        rel_path,
        unicodedata.normalize("NFC", rel_path),
        unicodedata.normalize("NFD", rel_path),
    }
    for candidate in candidates:
        p = REPO_ROOT / candidate
        if p.exists():
            return p.resolve()
    return None


def path_key(p):
    """Chiave stabile per confrontare percorsi indipendentemente dalla forma
    Unicode (NFC/NFD) restituita da .resolve(): il filesystem su cui gira
    questo script (macOS) è normalization-insensitive per l'esistenza dei
    file, ma Path.resolve() preserva la forma della stringa di partenza
    invece di restituire sempre quella effettiva su disco. Normalizzando a
    NFC entrambi i lati del confronto si evita un falso negativo (o un
    esito non deterministico, perché la scelta del candidato in
    resolve_existing_path avviene iterando su un set non ordinato).
    """
    return unicodedata.normalize("NFC", str(p))


def it_sort_key(s):
    """Chiave di ordinamento che approssima localeCompare('it', {sensitivity:'base'}):
    case-insensitive e indifferente ai diacritici."""
    normalized = unicodedata.normalize("NFKD", s or "")
    without_marks = "".join(c for c in normalized if not unicodedata.combining(c))
    return without_marks.casefold()


def strip_quotes(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def parse_frontmatter(text):
    """Verifica strutturale leggera del frontmatter (non un parser YAML completo).

    Ritorna (dizionario_chiavi_primo_livello, errore). errore è None se il
    frontmatter è aperto e chiuso correttamente; altrimenti una stringa che
    descrive il problema.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "manca il delimitatore di apertura '---'"

    closing_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing_idx = i
            break
    if closing_idx is None:
        return None, "frontmatter non chiuso (manca il secondo '---')"

    data = {}
    malformed = []
    for line in lines[1:closing_idx]:
        if not line.strip():
            continue
        if line[0] in (" ", "\t", "-"):
            # riga annidata (liste, mappe innestate): fuori dallo scope
            # di questa verifica leggera.
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            malformed.append(line.strip())
            continue
        key, value = m.group(1), strip_quotes(m.group(2))
        data[key] = value

    if malformed:
        preview = "; ".join(malformed[:3])
        return data, f"righe di primo livello non in forma 'chiave: valore': {preview}"

    return data, None


def main():
    anomalies = defaultdict(list)

    # --- Carica i quattro JSON e costruisce l'indice href -> percorso reale ---
    json_data = {}
    href_index = {}  # percorso assoluto risolto -> (nome_json, chiave_sezione)

    for section_name, json_path in SECTION_JSON.items():
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            anomalies["JSON mancante"].append(str(json_path.relative_to(REPO_ROOT)))
            continue
        except json.JSONDecodeError as e:
            anomalies["JSON non valido"].append(f"{json_path.relative_to(REPO_ROOT)}: {e}")
            continue

        json_data[section_name] = data

        if not isinstance(data, dict):
            anomalies["Struttura JSON inattesa"].append(
                f"{json_path.relative_to(REPO_ROOT)}: atteso un oggetto di primo livello"
            )
            continue

        for section_key, entries in data.items():
            if not isinstance(entries, list):
                anomalies["Struttura JSON inattesa"].append(
                    f"{json_path.relative_to(REPO_ROOT)} [{section_key}]: atteso un array di voci"
                )
                continue
            for entry in entries:
                href = entry.get("href") if isinstance(entry, dict) else None
                if not href:
                    anomalies["Voce JSON senza href"].append(
                        f"{json_path.relative_to(REPO_ROOT)} [{section_key}]: {entry!r}"
                    )
                    continue
                rel_path = href_to_rel_path(href)
                resolved = resolve_existing_path(rel_path)
                if resolved is None:
                    anomalies["href non risolvibile a un .md esistente"].append(
                        f"{json_path.relative_to(REPO_ROOT)} [{section_key}]: "
                        f"href='{href}' -> atteso '{rel_path}'"
                    )
                else:
                    href_index[path_key(resolved)] = (section_name, section_key)

    # --- Elenca tutti i .md sotto Content/ (esclusa prompts/) ---
    all_md = [
        p
        for p in sorted(CONTENT_DIR.rglob("*.md"))
        if p.relative_to(CONTENT_DIR).parts[0] not in EXCLUDED_TOP_DIRS
    ]

    # --- Regola 5: nessun basename con spazi ---
    for p in all_md:
        if " " in p.name:
            anomalies["Basename .md con spazi"].append(str(p.relative_to(REPO_ROOT)))

    # --- Regola 3: frontmatter valido, chiuso, layout/title non vuoti ---
    for p in all_md:
        text = p.read_text(encoding="utf-8")
        data, error = parse_frontmatter(text)
        rel = str(p.relative_to(REPO_ROOT))
        if error is not None:
            anomalies["Frontmatter non valido/non chiuso"].append(f"{rel}: {error}")
            continue
        layout = data.get("layout", "")
        title = data.get("title", "")
        if not layout.strip():
            anomalies["Campo 'layout' mancante o vuoto"].append(rel)
        if not title.strip():
            anomalies["Campo 'title' mancante o vuoto"].append(rel)

    # --- Regola 1: ogni .md ha una voce nel JSON della sua sezione ---
    # (Saints/ è esclusa di proposito: vedi commento su NO_INDEX_DIRS.)
    for p in all_md:
        rel_parts = p.relative_to(CONTENT_DIR).parts
        top = rel_parts[0]
        rel = str(p.relative_to(REPO_ROOT))

        if top in NO_INDEX_DIRS:
            continue

        if top not in SECTION_JSON:
            anomalies["Cartella senza JSON di indice associato"].append(rel)
            continue

        entry_info = href_index.get(path_key(p.resolve()))
        if entry_info is None:
            anomalies["File .md senza voce nel JSON di sezione"].append(rel)
            continue

        section_name, section_key = entry_info

        if top == "Artists":
            if len(rel_parts) < 3:
                anomalies["Struttura cartelle Artists inattesa"].append(
                    f"{rel}: atteso Content/Artists/<secolo>/<file>.md"
                )
                continue
            century_folder = rel_parts[1]
            expected_key = folder_to_century_key(century_folder)
            if expected_key is None:
                anomalies["Nome cartella secolo inatteso"].append(
                    f"{rel}: cartella '{century_folder}' non nella forma '<romano>-c'"
                )
            elif section_key != expected_key:
                anomalies["Sezione JSON non corrispondente alla cartella"].append(
                    f"{rel}: la voce è nella sezione '{section_key}', "
                    f"attesa '{expected_key}' in base alla cartella"
                )

    # --- Regola 4: ordinamento alfabetico per name in ogni sezione ---
    for section_name, data in json_data.items():
        if not isinstance(data, dict):
            continue
        json_path = SECTION_JSON[section_name]
        for section_key, entries in data.items():
            if not isinstance(entries, list):
                continue
            names = [e.get("name", "") if isinstance(e, dict) else "" for e in entries]
            keys = [it_sort_key(n) for n in names]
            for i in range(len(keys) - 1):
                if keys[i] > keys[i + 1]:
                    anomalies["Ordine alfabetico non rispettato"].append(
                        f"{json_path.relative_to(REPO_ROOT)} [{section_key}]: "
                        f"'{names[i]}' precede '{names[i + 1]}' (ordine errato)"
                    )

    # --- Regola 6: ogni scheda in Saints/ è linkata da almeno un'altra scheda ---
    # Saints/ non ha una pagina elenco (vedi NO_INDEX_DIRS): una scheda non
    # referenziata da nessun href altrove sotto Content/ è irraggiungibile.
    linked_from = defaultdict(set)
    for p in all_md:
        text = p.read_text(encoding="utf-8")
        source_key = path_key(p.resolve())
        for match in LINK_RE.findall(text):
            rel_path = href_to_rel_path(match)
            target = resolve_existing_path(rel_path)
            if target is None:
                continue
            target_key = path_key(target)
            if target_key == source_key:
                continue
            linked_from[target_key].add(source_key)

    for p in all_md:
        rel_parts = p.relative_to(CONTENT_DIR).parts
        if rel_parts[0] not in NO_INDEX_DIRS:
            continue
        rel = str(p.relative_to(REPO_ROOT))
        if not linked_from.get(path_key(p.resolve())):
            anomalies["Scheda in Saints/ non linkata da nessun'altra scheda"].append(rel)

    # --- Report ---
    total_anomalies = sum(len(v) for v in anomalies.values())

    total_json_entries = sum(
        len(entries)
        for data in json_data.values()
        if isinstance(data, dict)
        for entries in data.values()
        if isinstance(entries, list)
    )
    print(f"File .md esaminati sotto Content/ (esclusa prompts/): {len(all_md)}")
    print(f"Voci JSON esaminate: {total_json_entries}")
    print()

    if total_anomalies == 0:
        print("Nessuna anomalia trovata.")
        return 0

    for category in sorted(anomalies):
        items = anomalies[category]
        print(f"=== {category} ({len(items)}) ===")
        for item in items:
            print(f"  - {item}")
        print()

    print(f"TOTALE anomalie: {total_anomalies}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
