# MinDatabase - AI Agent Instructions

**Version**: 4.0 | **Last Updated**: 16 April 2026

## Project Scope

MinDatabase is a scholarly, content-only repository of long-form art historical essays.

- Primary focus: medieval Italian art and related institutional contexts
- Output type: narrative academic prose in Markdown
- No software build/test/deploy workflow is required for normal content work

## Canonical Repository Structure

Use this structure as authoritative:

```text
MinDatabase/
├── Content/
│   ├── Artists/
│   │   ├── VII century/
│   │   ├── VIII century/
│   │   ├── IX century/
│   │   ├── X century/
│   │   ├── XI century/
│   │   ├── XII century/
│   │   ├── XIII century/
│   │   │   └── [Artist Name].md
│   │   └── XIV century/
│   ├── Churches/
│   ├── Codex/
│   ├── Papers/
│   ├── Saints/
│   └── prompts/
├── Images/
└── MinDatabase - AI Agent Instructions.md
```

## Naming and Placement Rules

- Use `Papers` as the canonical folder name (never `Papirer`).
- Place artist files in the century folder matching the artist's primary documented activity period.
- Supported artist folders: `VII, VIII, IX, X, XI, XII, XIII, XIV`.
- Do not use `XIII-XIV` as a folder convention.

### File Naming

- Artist files: `[Name].md` with historically standard naming, using hyphens in place of spaces (e.g., `Giotto-di-Bondone.md`).
- Anonymous masters: full scholarly label, hyphenated (e.g., `Maestro-di-San-Martino.md`).
- Churches, Codex, Papers, Saints: descriptive scholarly titles.
- Legacy `.html` pages at the old, space-based paths are preserved as static redirect stubs pointing to the current hyphenated URL. Do not remove or modify these redirect files.

## Writing Model

- Write coherent, multi-paragraph academic prose.
- Integrate archival evidence, historiographical uncertainty, and stylistic analysis.
- Maintain cross-file consistency for dates, family ties, patronage, and attributions.
- Prefer narrative flow over bullet-point decomposition inside article bodies.

## Standard Artist Section Flow

Use and adapt as needed by discipline:

1. Early life and family
2. Patronage and commissions
3. Artistic style / technical characteristics
4. Artistic influences
5. Travels and career geography
6. Death and legacy
7. Works / major works

## Front Matter Policy

The repository currently includes YAML front matter in many content types, including Artist files.

- Preserve existing front matter when present.
- For new files, follow front matter patterns already used in the target folder.
- Do not remove valid existing front matter to force uniformity.

## Footnote Conventions (Mandatory Site-Wide)

All footnotes must use HTML anchor syntax and one ordered list block:

- Inline reference pattern: `id="fnref:N"` linking to `href="#fn:N"`
- Footnote block pattern: a single `<ol class="footnotes">` at the end of the file
- Each item: `<li id="fn:N"> ... <a href="#fnref:N" class="footnote__back" ...>↩</a>`
- Markdown footnotes (`[^1]`, `[^1]: ...`) are not allowed

### Required Pattern

```html
Inline note<a id="fnref:1" href="#fn:1" class="footnote"><sup>1</sup></a>

<ol class="footnotes">
  <li id="fn:1">
    <p>Footnote text. <a href="#fnref:1" class="footnote__back" aria-label="Back to reference">↩</a></p>
  </li>
</ol>
```

## Endnote Conventions (Page-End Notes)

Use endnotes for supplemental notes that should appear after the main text and after any footnotes, but remain visually distinct from the footnote list.

- Inline reference pattern: `id="enref:N"` linking to `href="#en:N"`
- Endnote block pattern: a single `<ol class="endnotes">` at the end of the content
- Each item: `<li id="en:N"> ... <a href="#enref:N" class="endnote__back" ...>↩</a>`
- Endnotes may appear on the same page as footnotes, but they should use a separate list and separate class names

### Required Pattern

```html
Main text with a note<a id="enref:1" href="#en:1" class="endnote"><sup>1</sup></a>

<ol class="footnotes">
  <li id="fn:1">
    <p>Footnote text. <a href="#fnref:1" class="footnote__back" aria-label="Back to reference">↩</a></p>
  </li>
</ol>

<ol class="endnotes">
  <li id="en:1">
    <p>Endnote text. <a href="#enref:1" class="endnote__back" aria-label="Back to endnote reference">↩</a></p>
  </li>
</ol>
```

## Images and Figures

This repository already contains embedded images in content files.

- Keep existing `<figure>`, `<img>`, and `<figcaption>` patterns where used.
- Use consistent image paths (typically `/Images/...` in content markup, matching site conventions).
- Add clear alt text and concise scholarly captions.
- Prefer legally reusable/public-domain or properly credited sources.

## Cross-Reference Consistency

- Keep artist-to-artist and church-to-artist relationships consistent across files.
- When updating a key relationship (e.g., workshop lineage, marriage, patronage), verify related entries.
- Preserve uncertainty wording where evidence is debated (e.g., "likely", "possibly", "scholars debate").

## Editing and Commit Workflow

- Make focused, incremental commits by section or topic.
- Separate content edits from tooling edits when tooling changes are involved.
- Commit message style examples:
  - `Add Early Life section to [Artist]`
  - `Update patronage chronology in [Artist]`

## Tooling Note: add_sections.py

**Removed — this tool is no longer available in the repository.** It was previously documented at `Content/Artists/XIII century/add_sections.py` (purpose: insert `##` headings into prose lacking explicit section markers via exact string replacements), but the file is no longer present. Do not reference or attempt to run it. Insert missing section headings via direct manual edits instead.

## Tooling Note: validate_content_indexes.py

`scripts/validate_content_indexes.py` checks the consistency between the `.md` files in `Content/` and the JSON directory indexes in `assets/data/` (matching entries, resolvable hrefs, valid front matter, alphabetical ordering, basename rules). It runs read-only and is executed automatically by the `validate-content-indexes.yml` workflow on every push touching `Content/**`, `assets/data/*.json`, or the script itself.

`Content/Saints/` is, by editorial choice, an unindexed section: saint entries are reachable only via links from other entries, not from a listing page. The script excludes `Saints/` from the "has a JSON entry" check, but flags any Saints entry that isn't linked from any other entry, since such an entry would otherwise be unreachable.

## Quality Checklist Before Finalizing

1. Folder and filename match canonical structure (`Papers`, current century folders).
2. Dates, names, relationships, and attributions are internally consistent.
3. Prose remains scholarly and readable, not flattened into outline form.
4. Footnotes use the required `<ol class="footnotes">` format.
5. Images/figures (if present) are formatted consistently and captioned clearly.
6. Related entries affected by major factual edits are updated or reviewed.

## Automazioni

Il repository si mantiene da solo attraverso cinque workflow GitHub Actions.
Conoscerne l'ordine evita di inseguire problemi che hanno una causa nota.

### La catena di pubblicazione

Un push che tocca `Content/**/*.md` avvia, in parallelo:

1. **Update Push Notices** — genera `assets/data/push_notices.json` con la
   notizia della scheda pubblicata, poi invia la newsletter agli iscritti e
   registra l'invio in `newsletter_last_notified.json`.
2. **Update Gallery Index** — rigenera `assets/data/gallery-index.json`
   estraendo le `<figure>` da tutte le schede.

Entrambi committano e, in coda, invocano esplicitamente **Deploy Site**.

I tre validatori — contenuti, indici, frontmatter degli studiosi — girano in
parallelo e non scrivono nulla.

### Tre vincoli da ricordare

**I commit fatti con `GITHUB_TOKEN` non generano eventi.** È la protezione di
GitHub contro i cicli infiniti. Conseguenza pratica: quando un workflow
committa un indice aggiornato, il deploy *non* riparte da solo, e il sito
resta indietro di un giro. Per questo entrambi i workflow che scrivono
terminano con una chiamata esplicita:

gh workflow run deploy-pages.yml

Serve `actions: write` fra i permessi del workflow che la esegue.

**I workflow che scrivono condividono un gruppo di concorrenza.** Girando in
parallelo si contendevano il ramo, e uno dei due falliva con
`cannot lock ref 'refs/heads/main'`. Il gruppo `repo-writes` con
`cancel-in-progress: false` li mette in fila.

**Il payload dell'evento non elenca sempre i file modificati.** La chiave
`modified` puo' mancare del tutto. `update_push_notices.py` ricade allora
sulla storia git, e il checkout usa `fetch-depth: 30` perche' quel fallback
abbia storia su cui lavorare.

### Il deploy

`deploy-pages.yml` costruisce con `bundle exec jekyll build`, non con
`actions/jekyll-build-pages`: quest'ultima ignora il `Gemfile` e usa le
versioni che GitHub decide. Con bundler la produzione usa le stesse versioni
fissate in `Gemfile.lock`, cioe' quelle con cui si costruisce in locale.

Conseguenza: in locale i comandi Jekyll vanno sempre preceduti da
`bundle exec`.

`vendor/` e' escluso in `_config.yml`: bundler vi installa le gem, e Jekyll vi
troverebbe il template di esempio con data segnaposto, che fa fallire la
build.

### Passi manuali rimasti

**L'iscrizione alla newsletter.** Formspree raccoglie gli indirizzi nella sua
interfaccia; vanno copiati a mano nel Secret `NEWSLETTER_SUBSCRIBERS` e in
`newsletter_subscribers.csv` (fuori dal repo, escluso anche dalla build).
Il sistema regge fino a una trentina di iscritti: oltre, il limite non e'
GitHub ma iCloud Mail, che non e' un servizio di invio in massa.

**L'indice della galleria in locale.** Non committarlo dal Mac: lo rigenera il
workflow, e committarlo da entrambe le parti produce conflitti.

### I nove controlli

`scripts/validate_content_indexes.py` contiene tutti i controlli sul
contenuto; il docstring in cima li elenca. Tre meritano una nota:

- **7** verifica i link fra pagine, **8** le ancore ai due contenitori
  (`endnotes.html`, `scholars.html`), **9** le immagini.
- Il check 8 esiste perche' i contenitori sono due: un link puo' nominare
  un'ancora reale ma cercarla nel file sbagliato. Le note del mondo antico
  stavano in un terzo contenitore, `ancient-world.html`, fuso in
  `endnotes.html`: quel path ora e' solo uno stub di redirect che conserva
  l'hash, e non va piu' usato nei rimandi.
- Il check 9 confronta le maiuscole in modo esplicito, senza affidarsi a
  `exists()`: il filesystem di macOS non distingue maiuscole e minuscole,
  GitHub Pages si'. Un `Armagh-01.jpg` che punta ad `armagh-01.jpg` funziona
  sul Mac e produce un'immagine vuota in produzione.

Tutti coprono `Content/**/*.md` piu' i `.md` nella radice (glossary,
dating-systems), esclusa la cartella `drafts/`.

### Convenzioni

Nessuno spazio nei nomi di file e cartelle: gli spazi diventano `%20` negli
URL e hanno gia' rotto centinaia di link. Le immagini seguono la forma
`<soggetto>-NN.jpg`, tutta minuscola, con lo zero iniziale per mantenere
l'ordinamento oltre la decima.

I link interni sono sempre root-relative (`/Content/...`, `/endnotes.html`):
i percorsi relativi dipendono dalla profondita' della cartella e si rompono a
ogni riorganizzazione.

Le schede in lavorazione stanno in `drafts/`, esclusa dai controlli e dalla
build. Si spostano in `Content/` solo alla pubblicazione: da quel momento ogni
commit fa partire una notifica agli iscritti, e una email non si ritira.
