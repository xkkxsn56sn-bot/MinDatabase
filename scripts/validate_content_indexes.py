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

7. Ogni link a /Content/...html scritto dentro un .md punta a una pagina
   esistente. Il check 2 copre solo gli href degli indici JSON; questo copre
   i link contestuali nelle schede — blocchi "related artists", rimandi in
   prosa, campi url: nel frontmatter — che sono la maggioranza dei link del
   sito.
8. Ogni rimando a un contenitore di ancore (endnotes.html, scholars.html)
    punta a un'ancora esistente nel file indicato, in forma canonica
    '/<file>.html'. I contenitori sono due, quindi un link puo' nominare un
    id reale ma cercarlo nel file sbagliato; il path relativo e' vietato
    perche' dipende dalla profondita' della cartella. In ciascun contenitore
    nessun id e' duplicato, e nella pagina di note ogni voce ha esattamente
    un <h3>. Anche 'ancient-world.html' resta riconosciuto dal pattern: e'
    un path dismesso, e un rimando che lo nomina va segnalato come non
    canonico invece di passare inosservato.

9. Ogni immagine citata in una scheda esiste, con le maiuscole esatte. Il
    confronto e' sensibile alle maiuscole anche su filesystem che non lo
    sono: 'Armagh-01.jpg' trova 'armagh-01.jpg' su macOS e fallisce su
    GitHub Pages. Le immagini non passano da nessun altro controllo.

10. Dentro ogni sezione-lettera di endnotes.html le voci sono ordinate per
    slug. La lettera di sezione segue invece il titolo visualizzato, che
    puo' cominciare con un onorifico: 'Pope Gregory IX' sta in P con slug
    fn-gregory-ix. Le divergenze fra le due chiavi sono volute e non sono
    un'anomalia; il check guarda solo l'ordine interno.

Non confronta "name" (JSON) con "title" (frontmatter): le divergenze fra i
due sono scelte editoriali volute e non un errore da segnalare qui.

Uscita: codice 1 se vengono trovate anomalie, 0 altrimenti.
"""
import os
import json
import re
import sys
import unicodedata
import urllib.parse
from collections import defaultdict, Counter
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


def check_md_outgoing_links(md_files, anomalies):
    """Verifica che i link a /Content/...html dentro i .md abbiano un bersaglio reale.

    Il check sugli href dei JSON copre gli indici; questo copre i link
    contestuali scritti nelle schede (blocchi 'related artists', rimandi in
    prosa, frontmatter). Sono la maggioranza dei link del sito e finora
    nessuno li verificava.
    """
    for md_path in md_files:
        try:
            text = md_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        rel_src = md_path.relative_to(REPO_ROOT)
        seen = set()

        for href in LINK_RE.findall(text):
            if href in seen:
                continue
            seen.add(href)

            rel_target = href_to_rel_path(href)
            if resolve_existing_path(rel_target) is None:
                anomalies["Link interno a pagina inesistente"].append(
                    f"{rel_src}: '{href}' -> {rel_target} non trovato"
                )


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


# --- Check 8: ancore ai contenitori del sito ----------------------------
# Il sito ha due pagine-contenitore a cui le schede rimandano per ancora:
#   endnotes.html  -> note, ogni voce e' <li id="fn-...">
#   scholars.html  -> studiosi, ogni voce e' un elemento di classe
#                     'scholar-entry' con id '<cognome>-<nome>'
# Le note del mondo antico stavano in un terzo contenitore, ancient-world.html,
# fuso in endnotes.html: quel path ora e' solo uno stub di redirect.
# In scholars.html vanno ignorati i raggruppamenti alfabetici (.scholar-section)
# e gli id di interfaccia come themeToggle: non sono voci.
NOTE_FILES = ("endnotes.html",)
SCHOLAR_FILE = "scholars.html"
ANCHOR_FILES = NOTE_FILES + (SCHOLAR_FILE,)

# Forma canonica di un rimando: /endnotes.html#fn-qualcosa
# Il path relativo (../../endnotes.html) funziona ma dipende dalla profondita'
# della cartella, quindi si rompe a ogni riorganizzazione: e' vietato.
# Solo i rimandi che nominano uno dei contenitori sono di competenza di questo
# check; le ancore interne a una pagina restano fuori.
# 'ancient-world' resta nella regex ma non in NOTE_FILES: il path e' dismesso
# (fuso in endnotes.html), cosi' un link futuro al path morto viene flaggato
# come non-canonico invece di sfuggire silenziosamente al check.
FN_LINK_RE = re.compile(
    r'([^\s"\'()<>]*(?:endnotes|ancient-world|scholars)\.html)#([A-Za-z0-9_.\-]+)'
)

NOTE_ID_RE = re.compile(r'<li[^>]*\bid="(fn-[^"]+)"')
NOTE_TITLE_RE = re.compile(r'endnotes-list__item-title')

# Tag di apertura generico, poi si ispezionano gli attributi: cosi' l'ordine
# fra class e id non conta.
TAG_RE = re.compile(r'<(?:div|li|section|article)\b([^>]*)>')
CLASS_ATTR_RE = re.compile(r'\bclass="([^"]*)"')
ID_ATTR_RE = re.compile(r'\bid="([^"]*)"')


def extract_scholar_ids(text):
    """Restituisce la lista degli id delle voci di scholars.html, in ordine."""
    found = []
    for attrs in TAG_RE.findall(text):
        class_m = CLASS_ATTR_RE.search(attrs)
        if not class_m or "scholar-entry" not in class_m.group(1).split():
            continue
        id_m = ID_ATTR_RE.search(attrs)
        if id_m:
            found.append(id_m.group(1))
    return found


def load_anchor_ids(anomalies):
    """Legge i tre contenitori e restituisce {nome_file: set_di_id}.

    Segnala per strada difetti strutturali che nessun altro controllo vede:
      - id duplicati: l'ancora risolve sempre alla prima occorrenza, quindi la
        seconda voce e' irraggiungibile pur esistendo (caso fn-clement-v);
      - nelle sole note, voci con un numero di <h3> diverso da uno: titolo
        ripetuto per copia-incolla, o voce priva di titolo (caso dei dogi).
        Le voci di scholars.html hanno struttura diversa e sono escluse.
    """
    ids_by_file = {}

    for fname in ANCHOR_FILES:
        path = REPO_ROOT / fname
        if not path.exists():
            anomalies["Contenitore di ancore mancante"].append(fname)
            ids_by_file[fname] = set()
            continue

        text = path.read_text(encoding="utf-8")

        if fname == SCHOLAR_FILE:
            found = extract_scholar_ids(text)
        else:
            found = NOTE_ID_RE.findall(text)

        ids_by_file[fname] = set(found)

        for anchor_id, count in Counter(found).items():
            if count > 1:
                anomalies["id duplicato in un contenitore"].append(
                    f"{fname}: '{anchor_id}' definito {count} volte"
                )

        if fname not in NOTE_FILES:
            continue

        # Conteggio dei titoli entro ciascun <li id="fn-...">.
        current_id = None
        title_count = 0
        for line in text.splitlines():
            opening = NOTE_ID_RE.search(line)
            if opening:
                if current_id is not None and title_count != 1:
                    anomalies["Voce di nota con numero di titoli inatteso"].append(
                        f"{fname}: '{current_id}' ha {title_count} <h3>, atteso 1"
                    )
                current_id = opening.group(1)
                title_count = 0
                continue
            if current_id is None:
                continue
            if NOTE_TITLE_RE.search(line):
                title_count += 1
            elif "</li>" in line:
                if title_count != 1:
                    anomalies["Voce di nota con numero di titoli inatteso"].append(
                        f"{fname}: '{current_id}' ha {title_count} <h3>, atteso 1"
                    )
                current_id = None
                title_count = 0

    return ids_by_file


def check_anchor_links(md_files, ids_by_file, anomalies):
    """Verifica ogni rimando a un contenitore presente nei .md.

    Due controlli distinti, perche' due bug diversi:
      - forma del path: deve essere '/<file>.html', non un relativo con '../'
        (che dipende dalla profondita' della cartella);
      - esistenza dell'ancora NEL FILE INDICATO: i contenitori sono tre, e un
        link puo' nominare un id reale ma cercarlo nel file sbagliato
        (caso fn-dietrich-ii-meissen).

    Il confronto sugli id e' esatto, mai per sottostringa: 'fn-clement-viii'
    contiene 'fn-clement-v' e un match parziale li confonderebbe.
    """
    canonical = {f"/{name}" for name in ANCHOR_FILES}

    for md_path in md_files:
        try:
            text = md_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        rel_src = str(md_path.relative_to(REPO_ROOT))
        seen = set()

        for link_path, anchor in FN_LINK_RE.findall(text):
            if (link_path, anchor) in seen:
                continue
            seen.add((link_path, anchor))

            if link_path not in canonical:
                anomalies["Rimando a contenitore in forma non canonica"].append(
                    f"{rel_src}: '{link_path}#{anchor}' "
                    f"(attesa una fra {', '.join(sorted(canonical))})"
                )
                continue

            fname = link_path.lstrip("/")
            if anchor not in ids_by_file.get(fname, set()):
                other = [f for f in ANCHOR_FILES if anchor in ids_by_file.get(f, set())]
                hint = f" (definita invece in {other[0]})" if other else ""
                anomalies["Ancora inesistente"].append(
                    f"{rel_src}: '{anchor}' non trovata in {fname}{hint}"
                )

# --- Check 9: riferimenti alle immagini ---------------------------------
# Le immagini non passano da nessun altro controllo: non sono link a pagine
# (check 7) ne' ancore (check 8), e il loro percorso non compare nei JSON di
# sezione. Un riferimento sbagliato produce quindi una figura vuota che nessuno
# segnala.
#
# Il confronto e' deliberatamente sensibile alle maiuscole. Il filesystem di
# macOS non lo e', quindi 'Armagh-01.jpg' trova 'armagh-01.jpg' sul Mac e
# fallisce su GitHub Pages, che gira su Linux. Path.exists() riprodurrebbe il
# comportamento della macchina su cui gira; qui si confronta invece il nome
# esatto contro il contenuto reale della cartella.
IMG_REF_RE = re.compile(r'(?:src|href)="(/?Images/[^"]+)"')


def resolve_case_sensitive(rel_path):
    """True se rel_path esiste con esattamente queste maiuscole.

    Si scende componente per componente confrontando con il contenuto della
    directory, invece di affidarsi a exists(): su un filesystem
    case-insensitive quest'ultimo direbbe di si' anche a una maiuscola
    sbagliata, ed e' proprio l'errore che questo check deve cogliere.
    """
    parts = Path(rel_path).parts
    current = REPO_ROOT
    for part in parts:
        try:
            entries = os.listdir(current)
        except (NotADirectoryError, FileNotFoundError, PermissionError):
            return False
        if part not in entries:
            return False
        current = current / part
    return True


def check_image_references(md_files, anomalies):
    """Verifica che ogni immagine citata nelle schede esista, maiuscole incluse."""
    for md_path in md_files:
        try:
            text = md_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        rel_src = str(md_path.relative_to(REPO_ROOT))
        seen = set()

        for ref in IMG_REF_RE.findall(text):
            if ref in seen:
                continue
            seen.add(ref)

            rel_path = urllib.parse.unquote(ref).lstrip("/")

            if resolve_case_sensitive(rel_path):
                continue

            # Se il file esiste ignorando le maiuscole, il messaggio lo dice:
            # e' l'errore che sul Mac non si vede e in produzione rompe.
            actual = None
            parent = REPO_ROOT / Path(rel_path).parent
            name = Path(rel_path).name
            if parent.is_dir():
                for entry in os.listdir(parent):
                    if entry.lower() == name.lower():
                        actual = entry
                        break

            if actual:
                anomalies["Immagine con maiuscole errate"].append(
                    f"{rel_src}: '{ref}' -> il file su disco e' '{actual}'"
                )
            else:
                anomalies["Immagine inesistente"].append(f"{rel_src}: '{ref}'")

# --- Check 10: ordine delle voci dentro le sezioni di endnotes.html ------
# La pagina di note raggruppa le voci in sezioni-lettera, e dentro ogni
# sezione le ordina per slug. Le due cose seguono chiavi diverse di
# proposito: la lettera di sezione segue il titolo visualizzato (la voce
# "Pope Gregory IX" sta in P), lo slug invece lascia cadere gli onorifici
# (fn-gregory-ix). Le divergenze fra le due sono quindi volute e non vanno
# segnalate: questo check guarda solo l'ordine interno, mai la lettera.
#
# Serve perche' nessun altro controllo copre questa sequenza: il check 4
# ordina gli indici JSON, il check 8 verifica che le ancore esistano e siano
# uniche, ma una voce inserita fuori posto non fa rumore da nessuna parte.
NOTE_SECTION_RE = re.compile(r'<section class="endnotes-section" id="endnotes-([A-Z])">')


def notes_by_section(text):
    """Voci di endnotes.html raggruppate per sezione, in ordine di documento.

    Restituisce {lettera: [slug, ...]}. Si scorrono insieme gli attacchi di
    sezione e le voci, ordinati per offset, cosi' ogni voce eredita la
    sezione che la precede.
    """
    events = [(m.start(), "sec", m.group(1)) for m in NOTE_SECTION_RE.finditer(text)]
    events += [(m.start(), "note", m.group(1)) for m in NOTE_ID_RE.finditer(text)]
    events.sort()

    by_section = {}
    current = None
    for _, kind, value in events:
        if kind == "sec":
            current = value
            by_section.setdefault(current, [])
        elif current is not None:
            by_section[current].append(value)
    return by_section


def out_of_place(slugs):
    """Indici delle voci da spostare perche' la sequenza torni ordinata.

    Si cerca la piu' lunga sottosequenza gia' in ordine e si segnalano le
    voci che ne restano fuori: e' l'insieme minimo da muovere. Segnalare
    invece ogni coppia invertita accuserebbe anche la voce corretta che
    precede quella fuori posto, che e' il modo piu' rapido per far spostare
    la voce sbagliata. Le sezioni hanno poche decine di voci, quindi il
    quadratico e' piu' che sufficiente e si legge meglio.
    """
    n = len(slugs)
    if n < 2:
        return []

    best = [1] * n
    prev = [-1] * n
    for i in range(1, n):
        for j in range(i):
            if slugs[j] <= slugs[i] and best[j] + 1 > best[i]:
                best[i] = best[j] + 1
                prev[i] = j

    end = max(range(n), key=lambda i: best[i])
    keep = set()
    while end != -1:
        keep.add(end)
        end = prev[end]
    return [i for i in range(n) if i not in keep]


def check_note_ordering(anomalies):
    """Verifica che dentro ogni sezione di endnotes.html gli slug siano ordinati."""
    path = REPO_ROOT / NOTE_FILES[0]
    if not path.exists():
        return

    for letter, slugs in sorted(notes_by_section(path.read_text(encoding="utf-8")).items()):
        misplaced = out_of_place(slugs)
        if not misplaced:
            continue

        ordered = sorted(slugs)
        for index in misplaced:
            slug = slugs[index]
            target = ordered.index(slug)
            before = ordered[target - 1] if target > 0 else None
            after = ordered[target + 1] if target + 1 < len(ordered) else None

            if before and after:
                where = f"fra '{before}' e '{after}'"
            elif after:
                where = f"prima di '{after}' (in testa alla sezione)"
            else:
                where = f"dopo '{before}' (in coda alla sezione)"

            anomalies["Voce di nota fuori ordine nella sua sezione"].append(
                f"{NOTE_FILES[0]}: sezione {letter}, '{slug}' e' alla posizione "
                f"{index + 1} di {len(slugs)} ma va {where}"
            )


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

    # --- Pagine .md nella radice (glossary, dating-systems...) ---
    # Non sono schede: restano fuori dai check 1/3/4/5, che presuppongono una
    # voce nel JSON di sezione. Entrano solo nei check 7 e 8, che verificano
    # i link uscenti e le ancore, validi per qualsiasi pagina.
    root_md = [
        p
        for p in sorted(REPO_ROOT.glob("*.md"))
        if p.name != "MinDatabase - AI Agent Instructions.md"
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

    check_md_outgoing_links(all_md + root_md, anomalies)

    ids_by_file = load_anchor_ids(anomalies)
    check_anchor_links(all_md + root_md, ids_by_file, anomalies)
    check_image_references(all_md + root_md, anomalies)
    check_note_ordering(anomalies)

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
