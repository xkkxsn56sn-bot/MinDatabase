#!/usr/bin/env python3
"""Batteria di test per update_push_notices.py.

Dieci gruppi di casi, tutti presi dalla storia reale del repository. Non serve pytest:
si esegue con `python3 scripts/test_update_push_notices.py` e stampa una riga
per caso, uscendo con codice 1 al primo fallimento.

I casi coprono le due regole che il giro di manutenzione ha cambiato — il tag
di soppressione ristretto all'oggetto e l'ordinamento allineato fra i due rami
— piu' l'effetto di MAX_NOTICES = 3.

a. Il commit 8a63d7f tocca 24 schede con lo stesso timestamp, tutte
   'modified'. Non potendo distinguerle ne' per data ne' per tipo, decide il
   path: le prime tre in ordine alfabetico. Prima ne sarebbe uscita una sola.
b. Il commit 8fc8936 rinomina Giselbertus in Gislebertus (D + A) e ritocca
   Autun. La scheda nuova precede quella modificata, ed entrambe entrano.
c. Il push del 7 settembre 2026 porta Traini 'modified' e la scheda di Pisa
   'created'. Passando dal ramo di fallback, l'ordine di `git log` metteva
   Traini per primo e MAX_NOTICES = 1 lo lasciava solo in newsletter: la
   scheda pubblicata non veniva annunciata. Ora vince Pisa.
d. Un messaggio che nomina il tag nel corpo ma non nell'oggetto non sopprime
   piu' nulla. E' l'errore che ha causato il caso c.
e. Il tag nell'oggetto sopprime, come sempre.
f. I due rami — payload e fallback — sugli stessi input danno lo stesso
   output. E' la proprieta' che il caso c aveva smentito.
g. L'oggetto della newsletter si costruisce sulle notizie: una sola porta
   titolo ed etichetta, due o piu' portano la prima e il conteggio delle
   altre, e un titolo lungo viene troncato qui invece che dal client di
   posta. La firma anti-reinvio non lo guarda.
i. Il ripiego su git guarda i commit del push — `before..after` dell'evento —
   e non piu' gli ultimi trenta. Leggendo trenta commit, il push della Fontana
   Maggiore del 16 settembre 2026 ripesco' quello di Pisa di dieci commit
   prima: tre notizie invece di una, e una newsletter che riannunciava roba
   gia' annunciata. I casi limite — ramo appena creato, `before` fuori dal
   checkout, esecuzione locale senza evento — ripiegano sul solo commit di
   punta, mai sulla storia intera.

   NOTA DI CONTRATTO: `fallback_entries` non passa piu' un range, e i casi
   storici da a a h restano validi perche' provano ordinamento e
   classificazione, non la scelta dei commit. Il default senza range vale
   «solo HEAD», che e' anche il contratto dell'esecuzione locale.

j. La firma anti-reinvio e' funzione dell'elenco intero, nel suo ordine, e non
   della sola testa: due errori simmetrici — testa nuova con compagne gia'
   spedite, testa gia' vista con compagne nuove — si chiudono insieme.

h. Le notizie annunciano schede e nient'altro. Un file non-scheda — un `.md`
   di radice, `Content/prompts/` — non produce notizia, e un push che tocca
   solo quelli non ne produce nessuna. Le schede di `Content/Saints/`, che il
   classificatore prima non riconosceva e lasciava cadere fra i non-contenuti,
   ora escono con la loro sezione: e' la garanzia contro la regressione che il
   filtro a tappeto avrebbe introdotto.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "update_push_notices", REPO_ROOT / "scripts" / "update_push_notices.py"
)
upn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(upn)

_spec_snu = importlib.util.spec_from_file_location(
    "send_newsletter_updates", REPO_ROOT / "scripts" / "send_newsletter_updates.py"
)
snu = importlib.util.module_from_spec(_spec_snu)
_spec_snu.loader.exec_module(snu)


FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    status = "ok  " if condition else "FAIL"
    print(f"{status}  {name}" + (f"\n        {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(name)


def payload_entries(timestamp: str, added: list[str], modified: list[str], message: str = "test") -> list[dict]:
    """Esegue il ramo payload su un evento sintetico."""
    payload = {
        "head_commit": {"message": message, "timestamp": timestamp},
        "commits": [
            {
                "message": message,
                "timestamp": timestamp,
                "added": added,
                "modified": modified,
            }
        ],
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
        json.dump(payload, handle)
        temp_path = Path(handle.name)
    try:
        _, entries = upn._parse_event_payload(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)
    return entries


def _run_fallback(lines: list[str], before=None, after=None) -> tuple[list[dict], list[list[str]]]:
    """Esegue il ripiego su un output di `git log` simulato, e ne cattura gli argv.

    Si sostituisce `subprocess.run` invece di riscrivere la storia del
    repository: cosi' il test esercita la funzione vera, comprese le regole
    su file spariti e path non markdown. Lo stub non solleva, quindi
    `_rev_is_present` risponde di si' e il range viene usato cosi' com'e' —
    che e' il caso da provare.
    """
    original = upn.subprocess.run
    seen: list[list[str]] = []

    def fake_run(args, *_a, **_kw):
        seen.append(list(args))
        return SimpleNamespace(stdout="\n".join(lines), stderr="", returncode=0)

    upn.subprocess.run = fake_run
    try:
        _, entries = upn._parse_git_history_fallback(before, after)
    finally:
        upn.subprocess.run = original
    return entries, seen


def fallback_entries(timestamp: str, name_status: list[tuple[str, str]]) -> list[dict]:
    """Il ripiego su un singolo commit simulato.

    Nessun range: fuori da Actions il contratto e' «il solo HEAD», e ai casi
    storici qui sotto — che provano ordinamento e classificazione, non la
    scelta dei commit — quel dettaglio non cambia nulla.
    """
    lines = [f"__COMMIT__{timestamp}"] + [f"{status}\t{path}" for status, path in name_status]
    entries, _ = _run_fallback(lines)
    return entries


def git_log_argv(seen: list[list[str]]) -> list[str]:
    """Gli argomenti dell'unica invocazione di `git log` fra quelle catturate."""
    return next(argv for argv in seen if argv[:2] == ["git", "log"])


def titles(notices: list[dict]) -> list[str]:
    return [n["title"] for n in notices]


def paths(notices: list[dict]) -> list[str]:
    return [n["path"] for n in notices]


# --------------------------------------------------------------------------
# a. 8a63d7f — 24 schede 'modified' a pari timestamp
# --------------------------------------------------------------------------
ARMAGH_TS = "2026-08-31T18:12:00+02:00"
ARMAGH_PATHS = [
    "Content/Codex/Book-of-Armagh.md",
    "Content/Codex/Book-of-Dimma.md",
    "Content/Codex/Book-of-Durrow.md",
    "Content/Codex/Book-of-Kells.md",
    "Content/Codex/Codex-Amiatinus.md",
    "Content/Codex/Codex-Aureus-of-Echternach.md",
    "Content/Codex/Codex-Usserianus-Primus.md",
    "Content/Codex/Codex-Usserianus-Secundus.md",
    "Content/Codex/Godescalc-Evangelistary.md",
    "Content/Codex/Lichfield-Gospels.md",
    "Content/Codex/Lindisfarne-Gospels.md",
    "Content/Codex/Morgan-Beatus.md",
    "Content/Papers/MSCandGaddoGaddi.md",
    "Content/Papers/Nerezi.md",
    "Content/Papers/San-Domenico-Crucifix.md",
    "Content/Papers/Scivias.md",
    "Content/Papers/The-Bandini-Crucifix.md",
    "Content/Saints/Angela-da-Foligno.md",
    "Content/Saints/Chiara-da-Montefalco.md",
    "Content/Saints/Saint-Ambrose.md",
    "Content/Saints/Saint-Cuthbert.md",
    "Content/Saints/Saint-Humility.md",
    "Content/Saints/Saint-John-Gualbert.md",
    "Content/Saints/San-Zanobi.md",
]

armagh = upn._dedupe_and_sort(payload_entries(ARMAGH_TS, [], ARMAGH_PATHS))
armagh_top = armagh[: upn.MAX_NOTICES]
check(
    "a. Armagh: 24 'modified' a pari timestamp -> ordine alfabetico di path",
    paths(armagh)[:3] == ARMAGH_PATHS[:3],
    f"attesi {ARMAGH_PATHS[:3]}, ottenuti {paths(armagh)[:3]}",
)
check(
    "a. Armagh: MAX_NOTICES = 3 pubblica tre voci, non una",
    len(armagh_top) == 3 and upn.MAX_NOTICES == 3,
    f"MAX_NOTICES={upn.MAX_NOTICES}, pubblicate {len(armagh_top)}",
)

# --------------------------------------------------------------------------
# b. 8fc8936 — Gislebertus D + A, Autun M
# --------------------------------------------------------------------------
GIS_TS = "2026-09-05T12:34:09+02:00"
gis_payload = upn._dedupe_and_sort(
    payload_entries(
        GIS_TS,
        added=["Content/Artists/XII-c/Gislebertus.md"],
        modified=["Content/Churches/Autun-Cathedral.md"],
    )
)
gis_fallback = upn._dedupe_and_sort(
    fallback_entries(
        GIS_TS,
        [
            ("D", "Content/Artists/XI-c/Giselbertus.md"),
            ("A", "Content/Artists/XII-c/Gislebertus.md"),
            ("M", "Content/Churches/Autun-Cathedral.md"),
        ],
    )
)
check(
    "b. Gislebertus (D+A) prima di Autun (M), entrambi dentro — ramo payload",
    paths(gis_payload)
    == ["Content/Artists/XII-c/Gislebertus.md", "Content/Churches/Autun-Cathedral.md"],
    str(paths(gis_payload)),
)
check(
    "b. idem dal fallback, e il path cancellato non produce una voce",
    paths(gis_fallback)
    == ["Content/Artists/XII-c/Gislebertus.md", "Content/Churches/Autun-Cathedral.md"],
    str(paths(gis_fallback)),
)
check(
    "b. la voce di Gislebertus e' 'created'",
    gis_fallback[0]["change_type"] == "created",
    gis_fallback[0]["change_type"],
)

# --------------------------------------------------------------------------
# c. Traini M + Pisa A — il push del 7 settembre 2026, passato dal fallback
# --------------------------------------------------------------------------
PISA_TS = "2026-09-07T16:57:32+02:00"
PISA = "Content/Papers/Battistero-San-Giovanni-Camposanto-Monumentale-Pisa.md"
TRAINI = "Content/Artists/XIV-c/Francesco-Traini.md"

pisa_fallback = upn._dedupe_and_sort(
    fallback_entries(PISA_TS, [("M", TRAINI), ("A", PISA)])
)
check(
    "c. Pisa (A) precede Traini (M) nel fallback, malgrado l'ordine di path",
    paths(pisa_fallback) == [PISA, TRAINI],
    str(paths(pisa_fallback)),
)
check(
    "c. la scheda pubblicata e' la notizia in testa",
    pisa_fallback[0]["change_type"] == "created"
    and pisa_fallback[0]["title"].startswith("The Baptistery of San Giovanni"),
    f"{pisa_fallback[0]['change_type']} / {pisa_fallback[0]['title']}",
)
check(
    "c. con MAX_NOTICES = 3 anche Traini resta annunciato",
    len(pisa_fallback[: upn.MAX_NOTICES]) == 2,
    str(len(pisa_fallback)),
)

# --------------------------------------------------------------------------
# d. tag nel corpo, non nell'oggetto -> non sopprime
# --------------------------------------------------------------------------
BODY_ONLY = (
    "Battistero e Camposanto di Pisa: new scheda (Papers), 15 images\n"
    "\n"
    "Nessun [skip notices]: il tag sopprimerebbe le notizie dell'intero push,\n"
    "compresa la pubblicazione di questa scheda.\n"
)
check(
    "d. tag citato nel corpo ma non nell'oggetto -> non sopprime",
    not upn.SKIP_TAG_RE.search(upn._subject_line(BODY_ONLY)),
    "l'oggetto e' stato giudicato taggato",
)
check(
    "d. e il tag nel corpo c'e' davvero (il test non passa per assenza)",
    bool(upn.SKIP_TAG_RE.search(BODY_ONLY)),
)

# --------------------------------------------------------------------------
# e. tag nell'oggetto -> sopprime, in tutte le varianti accettate
# --------------------------------------------------------------------------
SUBJECTS = [
    "maintenance: reorder fields [skip notices]",
    "maintenance: reorder fields [skip-notices]",
    "maintenance: reorder fields [SKIP NOTICES]",
    "[skip_notices] maintenance: reorder fields",
]
check(
    "e. tag nell'oggetto -> sopprime, in tutte le varianti accettate",
    all(upn.SKIP_TAG_RE.search(upn._subject_line(s)) for s in SUBJECTS),
    str([s for s in SUBJECTS if not upn.SKIP_TAG_RE.search(upn._subject_line(s))]),
)
check(
    "e. oggetto pulito con corpo pulito -> non sopprime",
    not upn.SKIP_TAG_RE.search(upn._subject_line("Pisa: new scheda\n\nprosa qualunque\n")),
)

# --------------------------------------------------------------------------
# f. i due rami sugli stessi input danno lo stesso output
# --------------------------------------------------------------------------
SAME_TS = "2026-09-07T16:57:32+02:00"
CASES = [
    # (added, modified) per il payload; il fallback riceve gli stessi file in
    # ordine di path, che e' come li elenca `git log --name-status`.
    ([PISA], [TRAINI]),
    (["Content/Artists/XII-c/Gislebertus.md"], ["Content/Churches/Autun-Cathedral.md"]),
    ([], ARMAGH_PATHS[:6]),
    (["Content/Codex/Book-of-Dimma.md"], ["Content/Codex/Book-of-Armagh.md", "Content/Papers/Nerezi.md"]),
]
divergent = []
for added, modified in CASES:
    from_payload = upn._dedupe_and_sort(payload_entries(SAME_TS, added, modified))
    name_status = sorted(
        [("A", p) for p in added] + [("M", p) for p in modified],
        key=lambda pair: pair[1],
    )
    from_fallback = upn._dedupe_and_sort(fallback_entries(SAME_TS, name_status))
    if from_payload != from_fallback:
        divergent.append((added, modified, paths(from_payload), paths(from_fallback)))
check(
    f"f. payload e fallback coincidono su {len(CASES)} input identici",
    not divergent,
    str(divergent),
)

# --------------------------------------------------------------------------
# g. oggetto della newsletter costruito sulle notizie
# --------------------------------------------------------------------------
PISA_TITLE = "The Baptistery of San Giovanni and the Camposanto Monumentale, Pisa"


def notice(title: str, change_type: str, path: str) -> dict:
    return {
        "title": title,
        "section": "Papers",
        "path": path,
        "page_url": "/x.html",
        "change_type": change_type,
        "pushed_at": PISA_TS,
    }


one_created = [notice("Francesco Traini", "modified", "b.md")]
check(
    "g. una notizia sola -> titolo ed etichetta nell'oggetto",
    snu._build_subject(one_created) == "Medieval Visions \u2014 [Updated] Francesco Traini",
    snu._build_subject(one_created),
)
check(
    "g. l'etichetta segue il change_type",
    snu._build_subject([notice("Nerezi", "created", "n.md")])
    == "Medieval Visions \u2014 [New] Nerezi",
    snu._build_subject([notice("Nerezi", "created", "n.md")]),
)

three = [
    notice(PISA_TITLE, "created", "a.md"),
    notice("Francesco Traini", "modified", "b.md"),
    notice("Book of Armagh", "modified", "c.md"),
]
subject_three = snu._build_subject(three)
check(
    "g. tre notizie -> prima notizia piu' conteggio, al plurale",
    subject_three.endswith(" and 2 more updates"),
    subject_three,
)
check(
    "g. due notizie -> singolare 'more update'",
    snu._build_subject(three[:2]).endswith(" and 1 more update"),
    snu._build_subject(three[:2]),
)

# Il titolo di Pisa e' il caso reale: 67 caratteri, sfora il limite di 60.
check(
    "g. il titolo di Pisa supera davvero il limite (il test non passa per difetto)",
    len(PISA_TITLE) > snu.SUBJECT_TITLE_MAX,
    f"{len(PISA_TITLE)} caratteri",
)
truncated = snu._truncate_title(PISA_TITLE)
check(
    "g. titolo lungo troncato con ellissi entro il limite",
    truncated.endswith("\u2026")
    and len(truncated) <= snu.SUBJECT_TITLE_MAX + 1
    and PISA_TITLE.startswith(truncated[:-1]),
    f"{truncated!r} ({len(truncated)} caratteri)",
)
check(
    "g. un titolo corto non viene toccato",
    snu._truncate_title("Francesco Traini") == "Francesco Traini",
    snu._truncate_title("Francesco Traini"),
)
check(
    "g. nessuna notizia -> oggetto di riserva",
    snu._build_subject([]) == "Medieval Visions update",
    snu._build_subject([]),
)

# La firma guarda path, pushed_at e change_type: cambiare i titoli cambia
# l'oggetto ma non la firma, quindi il subject dinamico non puo' provocare
# un reinvio. I titoli qui sono corti di proposito: su un titolo gia' troncato
# la differenza cadrebbe oltre l'ellissi e il confronto non proverebbe nulla.
short_three = [
    notice("Nerezi", "created", "a.md"),
    notice("Francesco Traini", "modified", "b.md"),
    notice("Book of Armagh", "modified", "c.md"),
]
retitled = [dict(item, title=item["title"] + " (ritoccato)") for item in short_three]
check(
    "g. titoli diversi -> oggetto diverso",
    snu._build_subject(short_three) != snu._build_subject(retitled),
    f"{snu._build_subject(short_three)!r} == {snu._build_subject(retitled)!r}",
)
check(
    "g. ma la firma anti-reinvio resta identica: non guarda l'oggetto",
    snu._signature_for_notices(short_three) == snu._signature_for_notices(retitled),
    f"{snu._signature_for_notices(short_three)!r} != {snu._signature_for_notices(retitled)!r}",
)

# --------------------------------------------------------------------------
# h. solo le schede producono notizie
# --------------------------------------------------------------------------
INSTRUCTIONS = "MinDatabase - AI Agent Instructions.md"
ROOT_MD = [INSTRUCTIONS, "glossary.md", "dating-systems.md", "README.md"]
SAINT = "Content/Saints/Saint-Ambrose.md"

mixed = upn._dedupe_and_sort(payload_entries(PISA_TS, added=[PISA], modified=[INSTRUCTIONS]))
check(
    "h. scheda + .md di radice -> una notizia sola, la scheda",
    paths(mixed) == [PISA],
    str(paths(mixed)),
)

root_only_payload = payload_entries(PISA_TS, added=[], modified=ROOT_MD)
root_only_fallback = fallback_entries(PISA_TS, [("M", p) for p in ROOT_MD])
check(
    "h. push di soli .md di radice -> zero notizie, ramo payload",
    root_only_payload == [],
    str(root_only_payload),
)
check(
    "h. idem dal fallback: niente da scrivere, quindi niente email",
    root_only_fallback == [],
    str(root_only_fallback),
)
check(
    "h. Content/prompts/ non e' contenuto",
    upn._section_from_path("Content/prompts/endnotes-pattern.md") == upn.NON_CONTENT_SECTION,
    upn._section_from_path("Content/prompts/endnotes-pattern.md"),
)

saints = upn._dedupe_and_sort(payload_entries(PISA_TS, added=[], modified=[SAINT]))
check(
    "h. una scheda Saints produce notizia, con sezione 'Saints'",
    len(saints) == 1 and saints[0]["section"] == "Saints" and saints[0]["path"] == SAINT,
    str([(n["section"], n["path"]) for n in saints]),
)
check(
    "h. e non finisce fra i non-contenuti",
    upn._section_from_path(SAINT) != upn.NON_CONTENT_SECTION,
    upn._section_from_path(SAINT),
)

# Il latente chiuso insieme al resto: i prefissi minuscoli di ripiego
# classificavano come schede i file di radice che cominciavano per il nome di
# una sezione. Ora conta solo 'Content/<cartella>/'.
check(
    "h. un .md di radice che comincia per 'papers' non e' una scheda",
    upn._section_from_path("papers-directory-notes.md") == upn.NON_CONTENT_SECTION,
    upn._section_from_path("papers-directory-notes.md"),
)
check(
    "h. tutte le cartelle di Content/ con schede sono classificate",
    {
        upn._section_from_path(f"Content/{folder}/x.md")
        for folder in ("Artists", "Churches", "Codex", "Papers", "Saints")
    }
    == {"Artists", "Churches", "Codices", "Papers", "Saints"},
    str({f: upn._section_from_path(f"Content/{f}/x.md") for f in ("Artists", "Churches", "Codex", "Papers", "Saints")}),
)

# --------------------------------------------------------------------------
# i. il ripiego guarda i commit del push, non la storia recente
# --------------------------------------------------------------------------
# Il 16 settembre 2026 il push della Fontana Maggiore porto' un commit solo.
# Il payload arrivo' senza liste di file — com'e' sempre successo su questo
# repository — e il ripiego, leggendo trenta commit, ripesco' il push di Pisa
# di dieci commit prima: tre notizie invece di una, e una newsletter che
# annunciava di nuovo roba gia' annunciata. Il range chiude la falla.
BEFORE = "b26206cf1111111111111111111111111111111a"
AFTER = "c70cf56497490a2bbd08ec149b21295d0ffd9221"
OLDER = "adf63351b8b13d428e1515701a0c3bf0e22599df"
FONTANA = "Content/Papers/Fontana-Maggiore-Perugia.md"
FONTANA_TS = "2026-09-16T09:34:41+02:00"

one_commit, seen_one = _run_fallback(
    [f"__COMMIT__{FONTANA_TS}", f"A\t{FONTANA}"], before=BEFORE, after=AFTER
)
check(
    "i. payload vuoto + range di un commit -> una notizia sola (il caso Fontana)",
    paths(upn._dedupe_and_sort(one_commit)) == [FONTANA],
    str(paths(upn._dedupe_and_sort(one_commit))),
)
check(
    "i. e il range finisce davvero negli argomenti di git log",
    f"{BEFORE}..{AFTER}" in git_log_argv(seen_one),
    str(git_log_argv(seen_one)),
)
check(
    "i. niente piu' -n30: la storia recente non entra nel comando",
    not any(a.startswith("-n3") for a in git_log_argv(seen_one)),
    str(git_log_argv(seen_one)),
)

# Un range che copre due push ne riporta entrambi i commit, e nient'altro:
# e' il range a decidere, non un conteggio fisso.
two_pushes, seen_two = _run_fallback(
    [
        f"__COMMIT__{FONTANA_TS}",
        f"A\t{FONTANA}",
        f"__COMMIT__{PISA_TS}",
        f"A\t{PISA}",
        f"M\t{TRAINI}",
    ],
    before=OLDER,
    after=AFTER,
)
check(
    "i. range su due push -> i soli commit del range, in ordine di notizia",
    paths(upn._dedupe_and_sort(two_pushes)) == [FONTANA, PISA, TRAINI],
    str(paths(upn._dedupe_and_sort(two_pushes))),
)
check(
    "i. anche qui il comando porta il range, non un limite di commit",
    git_log_argv(seen_two)[-1] == f"{OLDER}..{AFTER}",
    str(git_log_argv(seen_two)),
)

# I casi limite ripiegano sul solo commit di punta, mai sulla storia intera.
check(
    "i. ramo appena creato (before a zeri) -> solo il commit di punta",
    upn._fallback_revisions("0" * 40, AFTER) == ["-n1", AFTER],
    str(upn._fallback_revisions("0" * 40, AFTER)),
)
check(
    "i. fuori da Actions (nessun evento, nessun before) -> solo HEAD",
    upn._fallback_revisions(None, None) == ["-n1", "HEAD"],
    str(upn._fallback_revisions(None, None)),
)

# before irraggiungibile anche dopo --deepen: si degrada, non si esplode.
_orig_present = upn._rev_is_present
upn._rev_is_present = lambda _rev: False
try:
    _orig_run = upn.subprocess.run
    upn.subprocess.run = lambda *a, **k: SimpleNamespace(stdout="", stderr="", returncode=0)
    try:
        degraded = upn._fallback_revisions(OLDER, AFTER)
    finally:
        upn.subprocess.run = _orig_run
finally:
    upn._rev_is_present = _orig_present
check(
    "i. before fuori dal checkout anche dopo --deepen -> solo il commit di punta",
    degraded == ["-n1", AFTER],
    str(degraded),
)

# --------------------------------------------------------------------------
# j. la firma anti-reinvio guarda tutta la lista, non la sola testa
# --------------------------------------------------------------------------
# Una firma sulla sola testa lascerebbe passare due errori simmetrici: una
# testa nuova con compagne gia' spedite, e una testa gia' vista con compagne
# nuove. La firma sull'elenco intero li chiude entrambi.
head = notice("Fontana Maggiore", "created", FONTANA)
companions_a = [head, notice("Pisa", "created", PISA)]
companions_b = [head, notice("Francesco Traini", "modified", TRAINI)]
check(
    "j. stessa testa, compagne diverse -> firma diversa",
    snu._signature_for_notices(companions_a) != snu._signature_for_notices(companions_b),
    f"{snu._signature_for_notices(companions_a)!r}",
)
check(
    "j. lista identica -> firma identica, e l'invio si salta",
    snu._signature_for_notices(companions_a)
    == snu._signature_for_notices([dict(n) for n in companions_a]),
    f"{snu._signature_for_notices(companions_a)!r}",
)

print()
if FAILURES:
    print(f"{len(FAILURES)} test falliti: " + "; ".join(FAILURES))
    sys.exit(1)
print("Tutti i test passati.")
