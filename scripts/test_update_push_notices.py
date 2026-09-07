#!/usr/bin/env python3
"""Batteria di test per update_push_notices.py.

Sei casi, tutti presi dalla storia reale del repository. Non serve pytest:
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


def fallback_entries(timestamp: str, name_status: list[tuple[str, str]]) -> list[dict]:
    """Esegue il ramo di fallback su un output di `git log` simulato.

    Si sostituisce `subprocess.run` invece di riscrivere la storia del
    repository: cosi' il test esercita la funzione vera, comprese le regole
    su file spariti e path non markdown.
    """
    lines = [f"__COMMIT__{timestamp}"] + [f"{status}\t{path}" for status, path in name_status]
    original = upn.subprocess.run

    def fake_run(*_args, **_kwargs):
        return SimpleNamespace(stdout="\n".join(lines), stderr="", returncode=0)

    upn.subprocess.run = fake_run
    try:
        _, entries = upn._parse_git_history_fallback()
    finally:
        upn.subprocess.run = original
    return entries


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

print()
if FAILURES:
    print(f"{len(FAILURES)} test falliti: " + "; ".join(FAILURES))
    sys.exit(1)
print("Tutti i test passati.")
