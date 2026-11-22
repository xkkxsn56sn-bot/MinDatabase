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

## Push notices

Il workflow `.github/workflows/update-push-notices.yml` gira a ogni push che tocca `Content/**/*.md` (e anche manualmente via `workflow_dispatch`) ed esegue:

- `scripts/update_push_notices.py`

che rigenera `assets/data/push_notices.json` con l'elenco delle modifiche recenti ai contenuti, usato dal sito per mostrare gli aggiornamenti più recenti. Il workflow committa automaticamente solo se il file cambia. Non invia notifiche e-mail: non richiede secret SMTP.

## Aggiungere un iscritto da Formspree

1. Arriva l'email di Formspree: controllare che sia davvero una richiesta di iscrizione.
2. Doppio clic su `scripts/Aggiungi-iscritto.command` (o sul suo alias nel Dock/Desktop).
3. Finestra «Nuovo iscritto — Email»: incollare l'indirizzo (viene messo in minuscolo, senza spazi).
4. Finestra «Data di iscrizione (UTC)»: è precompilata con l'ora UTC attuale; sostituirla con quella dell'email di Formspree. Valgono `AAAA-MM-GGTHH:MM:SS+00:00`, `AAAA-MM-GG HH:MM`, `AAAA-MM-GGTHH:MM`, anche con `Z`; non sono ammesse date future.
5. Conferma riassuntiva (email, data, nuovo totale) → «Aggiungi».
6. Lo script fa il backup del CSV in `drafts/_backup/`, aggiunge la riga a `newsletter_subscribers.csv` (non tracciato), aggiorna il secret `NEWSLETTER_SUBSCRIBERS` con `gh secret set` e lancia il dry run.
7. Controllare la notifica finale «Iscritto aggiunto — Recipients N»: N deve essere salito di uno.

Se l'indirizzo è già presente lo script si ferma senza modifiche; se `gh` non è autenticato si ferma prima di toccare il CSV; se l'aggiornamento del secret fallisce ripristina il CSV dal backup. In ogni errore compare un avviso con il codice d'uscita. Nel terminale gli indirizzi compaiono solo mascherati (`a•••@dominio.it`).

Per le prove: `python3 scripts/add_subscriber.py --csv copia.csv --no-secret --no-dry-run` (il backup va in `_backup/` accanto alla copia).

**Alias nel Dock o sul Desktop.** Nel Finder, tasto Opzione+Comando mentre si trascina `Aggiungi-iscritto.command` sul Desktop crea un alias (oppure clic destro → «Crea alias» e spostarlo). Per il Dock, trascinare il file (o l'alias) nella parte destra del Dock, accanto al Cestino: i documenti stanno lì, non tra le app.

## Astronomical CSV datasets

The repository root also contains downloadable astronomy CSV files used as reference material for chronological and calendrical comparisons.

- `fasi_lunari_2026_otto_fasi_doppia_data.csv`: 2026 moon phases with Gregorian dates and the corresponding Julian dates, preserving the same event sequence and lunar intervals.
- `fasi_lunari_2026_otto_fasi_doppia_data_validation.csv`: English validation summary confirming the file schema, chronological continuity, and the consistent 13-day Gregorian-to-Julian offset applied throughout the dataset.

