#!/usr/bin/env python3
"""Aggiunge un iscritto alla newsletter (comunicato da Formspree) con finestre macOS.

Flusso:
  1. finestra «Nuovo iscritto — Email» (osascript);
  2. finestra «Data di iscrizione (UTC)», precompilata con l'ora UTC attuale;
  3. controllo doppioni (senza distinzione maiuscole/minuscole);
  4. conferma riassuntiva;
  5. backup del CSV, aggiunta della riga;
  6. `gh secret set NEWSLETTER_SUBSCRIBERS` (se fallisce, il CSV torna com'era);
  7. dry run della newsletter e notifica «Iscritto aggiunto — Recipients N».

Regola: nessun indirizzo email su stdout/stderr. L'indirizzo in chiaro compare
solo dentro la finestra di conferma; altrove si usa la forma mascherata.

Opzioni di test:
  --csv FILE       lavora su un CSV diverso (il backup va in FILE.parent/_backup)
  --no-secret      salta l'aggiornamento del secret
  --no-dry-run     salta il dry run della newsletter

Codici d'uscita: 0 aggiunto o annullato dall'utente; 3 doppione;
4 gh non disponibile/non autenticato; 5 aggiornamento del secret fallito
(CSV ripristinato); 6 dry run fallito; 1 altri errori.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CSV = REPO_ROOT / "newsletter_subscribers.csv"
DEFAULT_BACKUP_DIR = REPO_ROOT / "drafts" / "_backup"
SECRET_NAME = "NEWSLETTER_SUBSCRIBERS"
DRY_RUN_SCRIPT = REPO_ROOT / "scripts" / "send_newsletter_updates.py"

HEADER = ["email", "consent", "source", "created_at", "notes"]
# Valori delle righe Formspree gia' presenti nel CSV.
ROW_DEFAULTS = {
    "consent": "yes",
    "source": "formspree",
    "notes": "subject=Medieval Visions newsletter registration",
}

TITLE = "Nuovo iscritto"

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_DUPLICATE = 3
EXIT_GH = 4
EXIT_SECRET = 5
EXIT_DRY_RUN = 6

EMAIL_RE = re.compile(
    r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}$"
)
DATE_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?(Z|\+00:00|\+0000)?$"
)


class Cancelled(Exception):
    pass


class Stop(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


# --------------------------------------------------------------------------
# Finestre: osascript, oppure risposte simulate (--script-answers, solo test)
# --------------------------------------------------------------------------

class UI:
    def __init__(self, scripted: list | None = None):
        self.scripted = scripted

    def _osascript(self, script: str, *args: str) -> subprocess.CompletedProcess:
        # Gli argomenti passano per argv di osascript, non vengono interpolati
        # nel sorgente AppleScript: nessun problema di virgolette.
        return subprocess.run(
            ["osascript", "-", *args],
            input=script,
            capture_output=True,
            text=True,
        )

    def _next(self, kind: str):
        if not self.scripted:
            raise Stop(EXIT_ERROR, f"risposte simulate esaurite alla finestra «{kind}»")
        return self.scripted.pop(0)

    def ask(self, title: str, prompt: str, default: str = "") -> str:
        if self.scripted is not None:
            answer = self._next(title)
            if answer is None:
                raise Cancelled()
            return str(answer)
        script = (
            "on run argv\n"
            "  set r to display dialog (item 1 of argv) default answer (item 2 of argv) "
            "with title (item 3 of argv) buttons {\"Annulla\", \"OK\"} "
            "default button \"OK\" cancel button \"Annulla\"\n"
            "  return text returned of r\n"
            "end run\n"
        )
        proc = self._osascript(script, prompt, default, title)
        if proc.returncode != 0:
            if "-128" in proc.stderr:
                raise Cancelled()
            raise Stop(EXIT_ERROR, "osascript non ha potuto aprire la finestra")
        return proc.stdout.rstrip("\n")

    def confirm(self, message: str, ok_label: str) -> None:
        if self.scripted is not None:
            if self._next("conferma") is None:
                raise Cancelled()
            return
        script = (
            "on run argv\n"
            "  display dialog (item 1 of argv) with title (item 2 of argv) "
            "buttons {\"Annulla\", (item 3 of argv)} default button (item 3 of argv) "
            "cancel button \"Annulla\" with icon note\n"
            "end run\n"
        )
        proc = self._osascript(script, message, TITLE, ok_label)
        if proc.returncode != 0:
            if "-128" in proc.stderr:
                raise Cancelled()
            raise Stop(EXIT_ERROR, "osascript non ha potuto aprire la finestra")

    def alert(self, title: str, message: str, critical: bool = False) -> None:
        # Mai indirizzi in chiaro qui: il messaggio finisce anche su stderr.
        print(f"[avviso] {title}: {message}", file=sys.stderr)
        if self.scripted is not None:
            return
        script = (
            "on run argv\n"
            "  display alert (item 1 of argv) message (item 2 of argv) as "
            + ("critical" if critical else "warning")
            + "\nend run\n"
        )
        self._osascript(script, title, message)

    def notify(self, title: str, message: str) -> None:
        print(f"[notifica] {title}: {message}")
        if self.scripted is not None:
            return
        script = (
            "on run argv\n"
            "  display notification (item 2 of argv) with title (item 1 of argv)\n"
            "end run\n"
        )
        self._osascript(script, title, message)


# --------------------------------------------------------------------------
# Validazione
# --------------------------------------------------------------------------

def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:1]}•••@{domain}" if domain else "•••"


def normalize_email(raw: str) -> str | None:
    email = re.sub(r"\s+", "", raw).lower()
    if len(email) > 254 or not EMAIL_RE.match(email):
        return None
    return email


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def format_utc(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def parse_utc(raw: str, now: dt.datetime) -> tuple[str | None, str]:
    """Restituisce (data canonica, "") oppure (None, motivo)."""
    match = DATE_RE.match(raw.strip())
    if not match:
        return None, (
            "formato non riconosciuto. Usa AAAA-MM-GGTHH:MM:SS+00:00, "
            "AAAA-MM-GG HH:MM o AAAA-MM-GGTHH:MM (anche con Z)."
        )
    year, month, day, hour, minute, second, _ = match.groups()
    try:
        value = dt.datetime(
            int(year), int(month), int(day), int(hour), int(minute),
            int(second or 0), tzinfo=dt.timezone.utc,
        )
    except ValueError:
        return None, "data inesistente."
    if value > now:
        return None, "la data e' nel futuro."
    return format_utc(value), ""


# --------------------------------------------------------------------------
# CSV
# --------------------------------------------------------------------------

def read_csv(path: Path) -> tuple[list[str], list[dict], str, bytes]:
    if not path.exists():
        raise Stop(EXIT_ERROR, f"CSV non trovato: {path.name}")
    data = path.read_bytes()
    text = data.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"
    reader = csv.DictReader(io.StringIO(text, newline=""))
    header = list(reader.fieldnames or [])
    if "email" not in header or "created_at" not in header:
        raise Stop(EXIT_ERROR, "intestazione del CSV inattesa (mancano email/created_at)")
    return header, list(reader), newline, data


def build_row(header: list[str], email: str, created_at: str, newline: str) -> str:
    values = {**ROW_DEFAULTS, "email": email, "created_at": created_at}
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator=newline).writerow([values.get(col, "") for col in header])
    return buffer.getvalue()


def append_row(path: Path, original: bytes, row: str, newline: str) -> None:
    prefix = "" if not original or original.endswith(b"\n") else newline
    with path.open("ab") as handle:
        handle.write((prefix + row).encode("utf-8"))


def backup_csv(path: Path, backup_dir: Path, stamp: str) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / f"{path.stem}-{stamp}{path.suffix}"
    shutil.copy2(path, target)
    return target


# --------------------------------------------------------------------------
# gh e dry run
# --------------------------------------------------------------------------

def github_repo() -> str:
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "remote", "get-url", "origin"],
        capture_output=True, text=True,
    )
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", proc.stdout.strip())
    if proc.returncode != 0 or not match:
        raise Stop(EXIT_GH, "impossibile ricavare il repository GitHub dal remote origin")
    return match.group(1)


def check_gh() -> str:
    if shutil.which("gh") is None:
        raise Stop(EXIT_GH, "gh non trovato nel PATH. Nessuna modifica al CSV.")
    proc = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise Stop(EXIT_GH, "gh non e' autenticato (gh auth login). Nessuna modifica al CSV.")
    return github_repo()


def set_secret(csv_path: Path, repo: str) -> bool:
    with csv_path.open("rb") as handle:
        proc = subprocess.run(
            ["gh", "secret", "set", SECRET_NAME, "--repo", repo],
            stdin=handle, capture_output=True, text=True,
        )
    return proc.returncode == 0


def run_dry_run() -> int | None:
    proc = subprocess.run(
        [sys.executable, str(DRY_RUN_SCRIPT), "--dry-run"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise Stop(EXIT_DRY_RUN, f"il dry run della newsletter e' uscito con codice {proc.returncode}")
    match = re.search(r"Recipients: (\d+)", proc.stdout)
    return int(match.group(1)) if match else None


def count_recipients(csv_path: Path) -> int:
    """Stesso criterio di send_newsletter_updates._load_recipients."""
    _, rows, _, _ = read_csv(csv_path)
    seen = set()
    for row in rows:
        email = (row.get("email") or "").strip().lower()
        if email and "@" in email:
            seen.add(email)
    return len(seen)


# --------------------------------------------------------------------------
# Flusso principale
# --------------------------------------------------------------------------

def ask_email(ui: UI) -> str:
    while True:
        email = normalize_email(ui.ask("Nuovo iscritto — Email", "Email del nuovo iscritto (da Formspree):"))
        if email:
            return email
        ui.alert("Email non valida", "Controlla l'indirizzo e riprova.")


def ask_date(ui: UI) -> str:
    while True:
        now = now_utc()
        raw = ui.ask(
            "Data di iscrizione (UTC)",
            "Data di iscrizione (UTC)\nCopiala dall'email di Formspree, "
            "oppure lascia l'ora attuale.",
            format_utc(now),
        )
        value, reason = parse_utc(raw, now_utc())
        if value:
            return value
        ui.alert("Data non valida", reason)


def run(args: argparse.Namespace, ui: UI) -> int:
    csv_path = Path(args.csv).expanduser().resolve() if args.csv else DEFAULT_CSV
    backup_dir = DEFAULT_BACKUP_DIR if csv_path == DEFAULT_CSV else csv_path.parent / "_backup"

    header, rows, newline, original = read_csv(csv_path)

    repo = None
    if not args.no_secret:
        repo = check_gh()  # prima di toccare qualsiasi cosa

    email = ask_email(ui)
    existing = {(row.get("email") or "").strip().lower() for row in rows}
    if email in existing:
        ui.alert("Gia' iscritto", f"{mask_email(email)} e' gia' nel CSV. Nessuna modifica.")
        return EXIT_DUPLICATE

    created_at = ask_date(ui)
    before = count_recipients(csv_path)
    ui.confirm(
        f"Email: {email}\nData (UTC): {created_at}\nNuovo totale iscritti: {before + 1}",
        "Aggiungi",
    )

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backup_csv(csv_path, backup_dir, stamp)
    try:
        append_row(csv_path, original, build_row(header, email, created_at, newline), newline)
    except OSError as exc:
        shutil.copy2(backup, csv_path)
        raise Stop(EXIT_ERROR, f"scrittura del CSV fallita ({exc.__class__.__name__}); CSV ripristinato")
    print(f"Aggiunto {mask_email(email)} ({created_at}). Backup: {backup.name}")

    if repo:
        if not set_secret(csv_path, repo):
            shutil.copy2(backup, csv_path)
            raise Stop(EXIT_SECRET, "aggiornamento del secret fallito; CSV ripristinato dal backup")
        print(f"Secret {SECRET_NAME} aggiornato su {repo}.")
    else:
        print("Secret non aggiornato (--no-secret).")

    after = count_recipients(csv_path)
    recipients = after
    if not args.no_dry_run:
        if csv_path != DEFAULT_CSV:
            print("Attenzione: il dry run legge newsletter_subscribers.csv, non il file indicato con --csv.")
        reported = run_dry_run()
        if reported is None:
            print("Il dry run non riporta Recipients (nessuna notizia nel push corrente): uso il conteggio del CSV.")
        else:
            recipients = reported
            print(f"Dry run: Recipients {reported}")
        if csv_path == DEFAULT_CSV and recipients != before + 1:
            ui.alert("Controllo Recipients", f"Atteso {before + 1}, trovato {recipients}.")
            return EXIT_DRY_RUN

    ui.notify("Iscritto aggiunto", f"Recipients {recipients}")
    return EXIT_OK


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggiunge un iscritto alla newsletter.")
    parser.add_argument("--csv", help="CSV da modificare (default: newsletter_subscribers.csv)")
    parser.add_argument("--no-secret", action="store_true", help="non aggiornare il secret GitHub")
    parser.add_argument("--no-dry-run", action="store_true", help="non lanciare il dry run della newsletter")
    parser.add_argument("--script-answers", help=argparse.SUPPRESS)  # solo test: JSON con le risposte
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    scripted = None
    if args.script_answers:
        scripted = json.loads(Path(args.script_answers).read_text(encoding="utf-8"))
    ui = UI(scripted)
    try:
        return run(args, ui)
    except Cancelled:
        print("Annullato: nessuna modifica.")
        return EXIT_OK
    except Stop as exc:
        ui.alert(f"Errore (codice {exc.code})", exc.message, critical=True)
        return exc.code
    except Exception as exc:  # noqa: BLE001
        ui.alert(f"Errore (codice {EXIT_ERROR})", f"errore imprevisto: {exc.__class__.__name__}", critical=True)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
