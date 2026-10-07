#!/usr/bin/env python3
"""Batteria di test per il check 7 di validate_content_indexes.py.

Si esegue senza dipendenze — `python3 scripts/test_validate_content_indexes.py` —
e stampa una riga per caso, uscendo con codice 1 se qualcosa fallisce.

Il check 7 e' nato guardando i soli link che finivano in '.html'. Per mesi
tutto il resto gli e' passato accanto: la scheda di Andrea di Bonaiuto ha
portato online due rimandi morti,
'/Content/Churches/Santa%20Maria%20Novella.md' e
'/Content/Churches/Camposanto%20Monumentale%20Pisa.md', che nessun controllo
poteva vedere perche' non finivano in '.html'. La scansione che ha esteso il
check ne ha trovati altri sette della stessa famiglia — vecchia nomenclatura
con gli spazi, nessuna estensione — su tre schede.

I casi qui sotto fissano il contratto nuovo, e i primi sono letteralmente
quei due link.

a. I due morti di Bonaiuto: '.md' e '%20' verso un file che non esiste.
   Rosso. Sono il caso di regressione che da' il nome alla batteria.
b. I due bersagli veri, nella forma canonica '.html'. Verde.
c. Un link '.md' verso un file che esiste: rosso lo stesso. Il sito pubblica
   pagine, GitHub mostra sorgenti: '.md' funziona la' e non qui, e quando il
   .md esiste il bersaglio giusto esiste per definizione con l'altra
   estensione. Il messaggio deve proporla.
d. La forma senza estensione, quella dei sette trovati dalla scansione.
   Rosso, con la forma canonica dedotta dalla rinomina spazi -> trattini.
e. L'URL-encoding si scioglie prima del confronto: '%20' e lo spazio sono lo
   stesso bersaglio, e un '.html' encoded che risolve e' verde.
f. Le maiuscole si confrontano esatte. exists() su macOS direbbe di si' a un
   nome che GitHub Pages non trova, ed e' l'errore che il check 9 gia'
   combatte sulle immagini: qui vale la stessa logica.
g. L'ancora si scarta prima del confronto: il bersaglio e' il file, le ancore
   dei contenitori hanno il check 8.
h. Estrazione: i link si leggono dalle tre sedi reali. Il caso '- url:' in
   linea e' una regressione vera — Maestro-di-Vico-lAbate.md scrive cosi', e
   una regex tarata sul solo 'url:' a inizio riga perderebbe due link che il
   check vecchio invece vedeva.
i. Estrazione, verso opposto: la prosa che nomina percorsi come `Content/**`
   non e' fatta di link e non va verificata, altrimenti il file di istruzioni
   diventa rosso da solo.
j. Il grafo di raggiungibilita' del check 6 si costruisce sui soli link
   validi: un link rotto o non canonico non rende raggiungibile nulla.
k. Check 12, i nomi delle immagini dei codici: il nome deriva dalla
   didascalia. Il caso di regressione e' l'Armagh con `armagh-f32v.jpg`, la
   forma senza zeri e col prefisso corto che ha dato il nome alla regola;
   poi aperture, numeri romani, pagine, la larghezza a quattro cifre
   dell'Amiatinus, le etichette senza foglio e il Godescalc 07 (f. 4v).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_content_indexes as v  # noqa: E402
import codex_image_names as cin  # noqa: E402

FAILURES = []


def check(label, condition, detail=""):
    if condition:
        print(f"ok    {label}")
    else:
        print(f"FAIL  {label}" + (f"  [{detail}]" if detail else ""))
        FAILURES.append(label)


def category(raw):
    verdict = v.classify_content_link(raw)
    return None if verdict is None else verdict[0]


def detail_of(raw):
    verdict = v.classify_content_link(raw)
    return "" if verdict is None else verdict[1]


# --- a. i due morti di Bonaiuto -----------------------------------------
BONAIUTO_DEAD = (
    "/Content/Churches/Santa%20Maria%20Novella.md",
    "/Content/Churches/Camposanto%20Monumentale%20Pisa.md",
)
for dead in BONAIUTO_DEAD:
    check(
        f"a. morto di Bonaiuto segnalato: {dead}",
        category(dead) is not None,
        "il check lo lascia passare",
    )

check(
    "a. e il vecchio filtro non li vedeva (finivano in .md, non in .html)",
    all(not d.endswith(".html") for d in BONAIUTO_DEAD),
)

# --- b. i bersagli veri, in forma canonica ------------------------------
for good in (
    "/Content/Churches/Basilica-Santa-Maria-Novella.html",
    "/Content/Papers/Battistero-San-Giovanni-Camposanto-Monumentale-Pisa.html",
    "/Content/Artists/XIV-c/Andrea-di-Bonaiuto.html",
):
    check(f"b. link canonico verde: {good}", category(good) is None, category(good) or "")

# --- c. .md verso file esistente: rosso comunque ------------------------
EXISTING_MD = "/Content/Churches/Basilica-Santa-Maria-Novella.md"
check(
    "c. .md verso file esistente e' rosso lo stesso",
    category(EXISTING_MD) == "Link interno con estensione .md",
    category(EXISTING_MD) or "verde",
)
check(
    "c. e il messaggio propone la forma .html",
    "/Content/Churches/Basilica-Santa-Maria-Novella.html" in detail_of(EXISTING_MD),
    detail_of(EXISTING_MD),
)

# --- d. la forma senza estensione dei sette trovati ---------------------
NO_EXT = "/Content/Churches/Cappella Bardi"
check(
    "d. link senza estensione segnalato",
    category(NO_EXT) == "Link interno senza estensione .html",
    category(NO_EXT) or "verde",
)
check(
    "d. e la forma canonica viene dedotta (spazi -> trattini)",
    "/Content/Churches/Cappella-Bardi.html" in detail_of(NO_EXT),
    detail_of(NO_EXT),
)

# --- e. URL-decode prima del confronto ----------------------------------
check(
    "e. '%20' e lo spazio sono lo stesso bersaglio",
    category("/Content/Churches/Cappella%20Bardi") == category(NO_EXT),
)
ENCODED_OK = "/Content/Artists/XIII-c/Giunta-Pisano.html"
check(
    "e. un .html encoded che risolve resta verde",
    category(ENCODED_OK.replace("-", "%2D")) is None,
    category(ENCODED_OK.replace("-", "%2D")) or "",
)

# --- f. maiuscole esatte -------------------------------------------------
WRONG_CASE = "/Content/Churches/basilica-santa-maria-novella.html"
check(
    "f. maiuscole sbagliate: rosso anche se il Mac troverebbe il file",
    category(WRONG_CASE) == "Link interno con maiuscole errate",
    category(WRONG_CASE) or "verde",
)
check(
    "f. e il messaggio nomina il file vero su disco",
    "Basilica-Santa-Maria-Novella.md" in detail_of(WRONG_CASE),
    detail_of(WRONG_CASE),
)

# --- g. l'ancora si scarta prima del confronto --------------------------
check(
    "g. l'ancora non entra nel confronto",
    category("/Content/Churches/Basilica-Santa-Maria-Novella.html#nave") is None,
)
check(
    "g. e un bersaglio rotto resta rotto anche con l'ancora",
    category("/Content/Churches/Non-Esiste.html#x")
    == "Link interno a pagina inesistente",
)

# --- h. estrazione dalle tre sedi ---------------------------------------
SAMPLE = """---
meta:
  - title: "RELATED ENTRIES"
    links:
      - title: "Tizio"
        url: "/Content/Artists/XIII-c/Giotto-di-Bondone.html"
      - url: "/Content/Artists/XIII-c/Maestro-del-Bigallo.html"
      - url: /Content/Artists/XIII-c/Ugolino di Tedice
---

Prosa con [un link](/Content/Churches/Cappella-Bardi.html) e un
<a href="/Content/Saints/Saint-Ambrose.html">href inline</a>.
"""
extracted = [t for t in v.iter_link_targets(SAMPLE) if "Content/" in t]
check(
    "h. la sede 'url:' quotata e' letta senza virgolette",
    "/Content/Artists/XIII-c/Giotto-di-Bondone.html" in extracted,
    str(extracted),
)
check(
    "h. la forma '- url:' in linea non si perde (caso Maestro-di-Vico-lAbate)",
    "/Content/Artists/XIII-c/Maestro-del-Bigallo.html" in extracted,
    str(extracted),
)
check(
    "h. un url non quotato con spazi arriva intero, non troncato",
    "/Content/Artists/XIII-c/Ugolino di Tedice" in extracted,
    str(extracted),
)
check(
    "h. il link markdown viene letto",
    "/Content/Churches/Cappella-Bardi.html" in extracted,
    str(extracted),
)
check(
    "h. l'href inline viene letto",
    "/Content/Saints/Saint-Ambrose.html" in extracted,
    str(extracted),
)

# --- i. la prosa non e' fatta di link -----------------------------------
PROSE = "I markdown sotto `Content/Artists/`, `Content/**/*.md` e `Content/prompts/`."
check(
    "i. i percorsi citati in prosa non vengono estratti",
    [t for t in v.iter_link_targets(PROSE) if "Content/" in t] == [],
    str(list(v.iter_link_targets(PROSE))),
)

# --- j. il grafo del check 6 usa i soli link validi ---------------------
check(
    "j. un link canonico e risolvibile e' un arco del grafo",
    v.content_link_target("/Content/Saints/Saint-Ambrose.html") is not None,
)
for broken in BONAIUTO_DEAD + (NO_EXT, WRONG_CASE, "/Content/Churches/Non-Esiste.html"):
    check(
        f"j. un link non valido non e' un arco: {broken}",
        v.content_link_target(broken) is None,
    )

# --- k. i nomi delle immagini dei codici --------------------------------
def nm(base, folder, fn, cap):
    return cin.check_name(base, folder, fn, cap)


A = "Book-of-Armagh"
check("k. foglio con zeri e slug intero: verde",
      nm(A, A, "book-of-armagh-f032v.jpg", "..., fol. 32v. Armagh") is None)
check("k. l'Armagh vecchio (prefisso corto, senza zeri): rosso",
      nm(A, A, "armagh-f32v.jpg", "fol. 32v") is not None)
check("k. senza zeri con lo slug giusto: rosso",
      nm(A, A, "book-of-armagh-f32v.jpg", "fol. 32v") is not None)
check("k. foglio diverso dalla didascalia: rosso",
      "f053r" in (nm(A, A, "book-of-armagh-f054v.jpg", "fol. 53r") or ""))
check("k. cartella diversa dal nome della scheda: rosso",
      nm("Lindisfarne-Gospels", "Lindisfarne", "lindisfarne-gospels-f025v.jpg", "folio 25v") is not None)
check("k. maiuscola nel nome: rosso",
      nm("Codex-Usserianus-Primus", "Codex-Usserianus-Primus", "Usserianus-01.jpg", "fol. 149v") is not None)
AM = "Codex-Amiatinus"
check("k. Amiatinus a quattro cifre: verde",
      nm(AM, AM, "codex-amiatinus-f0796v.jpg", "fol. 796v") is None)
check("k. Amiatinus a tre cifre: rosso",
      nm(AM, AM, "codex-amiatinus-f796v.jpg", "fol. 796v") is not None)
check("k. apertura: verde",
      nm(AM, AM, "codex-amiatinus-f0002v-0003r.jpg", "fol. 2v-3r") is None)
LO = "Codex-Aureus-of-Lorsch"
check("k. pagina: verde", nm(LO, LO, "codex-aureus-of-lorsch-p026.jpg", "Pal. lat. 50, p. 26") is None)
check("k. numero romano: verde", nm(LO, LO, "codex-aureus-of-lorsch-f-i-v.jpg", "fol. Iv.") is None)
check("k. dettaglio: verde", nm(A, A, "book-of-armagh-f032v-d01.jpg", "fol. 32v") is None)
check("k. seconda fonte: verde", nm(A, A, "book-of-armagh-f032v-alt.jpg", "fol. 32v") is None)
M = "Book-of-Mulling"
check("k. etichetta senza foglio: verde", nm(M, M, "book-of-mulling-shrine.jpg", "Shrine (cumdach)") is None)
check("k. etichetta con un foglio in didascalia: rosso",
      nm(M, M, "book-of-mulling-shrine.jpg", "folio 94v") is not None)
check("k. etichetta fuori lista: rosso", nm(M, M, "book-of-mulling-cumdach.jpg", "Shrine") is not None)
check("k. contesto: verde", nm(AM, AM, "codex-amiatinus-context-jarrow-dedication.jpg", "Inscription") is None)
check("k. foglio nel nome, nessuno in didascalia: rosso", nm(M, M, "book-of-mulling-f001r.jpg", "Shrine") is not None)
G = "Godescalc-Evangelistary"
check("k. Godescalc 07 corretto al f. 4v: verde", nm(G, G, "godescalc-evangelistary-f004v.jpg", "folio 4v") is None)
check("k. Godescalc 07 col vecchio nome: rosso", nm(G, G, "godescalc-evangelistary-07.jpg", "folio 4v") is not None)
check("k. nessun conflitto aperto", cin.OPEN_CONFLICTS == set())

print()
if FAILURES:
    print(f"{len(FAILURES)} test falliti: " + "; ".join(FAILURES))
    sys.exit(1)
print("Tutti i test passati.")
