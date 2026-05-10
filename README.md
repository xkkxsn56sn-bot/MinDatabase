# Personal Python Scripts

Questa cartella contiene script Python personali e un launcher unico (`main.py`) per eseguirli rapidamente.

## Setup veloce

1. Crea/attiva ambiente virtuale:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Installa dipendenze Python:

```bash
pip install -r requirements.txt
```

3. Installa dipendenze di sistema (richieste da alcuni script):

```bash
brew install pandoc libreoffice
```

Per conversione PDF con `xelatex`, installa anche una distribuzione TeX (es. MacTeX).

## Uso di main.py

Elenca gli script disponibili:

```bash
python main.py list
```

Esegui uno script tramite chiave:

```bash
python main.py run md_to_pdf_batch -- --help
```

Note:
- Le chiavi sono generate automaticamente dai nomi file in `scripts/`.
- In alternativa puoi passare il nome file esatto (incluso `.py`).
- Tutti gli argomenti dopo `--` vengono inoltrati allo script scelto.

## Task VS Code

Sono disponibili task in `.vscode/tasks.json`:

- Python: List Personal Scripts
- Python: Run Personal Script

Uso:

1. Apri Command Palette e avvia Run Task.
2. Seleziona Python: List Personal Scripts per vedere le chiavi disponibili.
3. Seleziona Python: Run Personal Script e inserisci:
	- scriptKey: la chiave script mostrata dalla task list
	- scriptArgs: argomenti opzionali (esempio: `--help`)

## Visitor Counter (private)

Il sito usa ora uno script invisibile per contare le visite pagina tramite CountAPI.

- Tracker client: `assets/js/visitor-counter.js`
- Script lettura totale: `scripts/get_visitor_count.py`
- Script delta settimanale/mensile: `scripts/visitor_count_deltas.py`

Leggere il totale visite:

```bash
python scripts/get_visitor_count.py
```

Cambiare namespace/key (facoltativo):

```bash
python scripts/get_visitor_count.py --namespace my-namespace --key my-key
```

Leggere delta 7/30 giorni (usa snapshot locali salvati a ogni esecuzione):

```bash
python scripts/visitor_count_deltas.py
```

Percorso storico personalizzato (facoltativo):

```bash
python scripts/visitor_count_deltas.py --history-file scripts/.visitor_count_history.json
```

Se vuoi cambiare il contatore usato dal sito, modifica le costanti `COUNTER_NAMESPACE` e `COUNTER_KEY` in `assets/js/visitor-counter.js`.

## Newsletter CSV auto-sync

Per popolare automaticamente `newsletter_subscribers.csv` dai messaggi ricevuti su `contact@medievalvisions.com`:

- Script: `scripts/sync_newsletter_subscribers.py`
- Workflow GitHub Actions: `.github/workflows/sync-newsletter-subscribers.yml`

Il workflow gira ogni ora (e anche manualmente via `workflow_dispatch`), legge le mail non lette con oggetto:

- `Medieval Visions newsletter registration`

estrae gli indirizzi e-mail trovati nel corpo della mail, evita duplicati e aggiorna `newsletter_subscribers.csv`.

### Secrets richiesti (Repository Settings -> Secrets and variables -> Actions)

- `IMAP_HOST` (es. `imap.mail.me.com` per iCloud)
- `IMAP_PORT` (tipicamente `993`)
- `IMAP_USERNAME`
- `IMAP_PASSWORD` (per iCloud: app-specific password)

### Note operative

- Il workflow committa automaticamente solo se il CSV cambia.
- Le righe aggiunte usano:
	- `consent`: `yes`
	- `source`: `formsubmit_email`
	- `created_at`: timestamp UTC ISO-8601

## Newsletter update notifications

Per inviare notifiche e-mail agli iscritti quando vengono aggiunte/modificate entry (`.md`), il workflow:

- `.github/workflows/update-push-notices.yml`

esegue anche:

- `scripts/send_newsletter_updates.py`

Lo script legge:

- `assets/data/push_notices.json` (ultime modifiche contenuti)
- `newsletter_subscribers.csv` (destinatari)

e invia una e-mail per ogni nuovo aggiornamento non ancora notificato. Lo stato di deduplica viene salvato in:

- `assets/data/newsletter_last_notified.json`

### Secrets SMTP richiesti

- `SMTP_HOST`
- `SMTP_PORT` (tipicamente `587` con STARTTLS, oppure `465` con SSL)
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_FROM` (facoltativo, default: `SMTP_USERNAME`)
- `SMTP_SECURE` (facoltativo: `starttls` default, oppure `ssl`)

### Fallback automatico

Se i secret SMTP non sono configurati, `scripts/send_newsletter_updates.py` prova a usare:

- `IMAP_HOST` -> host SMTP derivato (`imap.` -> `smtp.`)
- `IMAP_USERNAME`
- `IMAP_PASSWORD`

Questo permette di inviare notifiche anche con la sola configurazione IMAP (tipico per iCloud con app password).

## Astronomical CSV datasets

The repository root also contains downloadable astronomy CSV files used as reference material for chronological and calendrical comparisons.

- `fasi_lunari_2026_otto_fasi_doppia_data.csv`: 2026 moon phases with Gregorian dates and the corresponding Julian dates, preserving the same event sequence and lunar intervals.
- `fasi_lunari_2026_otto_fasi_doppia_data_validation.csv`: English validation summary confirming the file schema, chronological continuity, and the consistent 13-day Gregorian-to-Julian offset applied throughout the dataset.

