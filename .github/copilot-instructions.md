# MinDatabase - AI Agent Instructions

## Project Overview
MinDatabase is a scholarly database of detailed historical essays on medieval Italian artists. This is NOT a software project but a knowledge repository focused on art history, particularly Tuscan painters and sculptors from the 13th-14th centuries (Duecento and Trecento periods).

## Core Architecture & Content Patterns

### File Structure
- Individual artist profile files: `[Artist Name].md`
- Historical documents: `.github/Codex/Codex Aureus of Saint Emmeram.md`
- Utility script: `add_sections.py` - automates section heading insertion into markdown files
- Main entry point: `README.md` (comprehensive guide with artist indexes by period/region/medium/patronage, usage guidelines, temporal scope)

### Standard Artist Article Structure
Each artist essay follows a consistent section format:
1. **Early Life and Family** - Birth, family background, apprenticeship context, family workshop dynamics, economic status
2. **Patrons and Commissions** - Institutional and private patronage relationships, contractual arrangements, payment structures
3. **Artistic Innovations** (or **Sculptural Style and Technical Characteristics**) - Technical innovations, stylistic evolution, material mastery, influence on later art
4. **Artistic Influences** - Predecessor artists, schools, and cultural movements, synthesis of diverse traditions
5. **Travels and Career** (or **Geographic Movements and Workshop Locations**) - Geographic movement, workshop practices, professional network, trade route connectivity
6. **Death and Legacy** - Historical impact, influence on Renaissance artists, family continuity
7. **Major Works and Masterpieces** (variable) - Documentation of key works with detailed compositional and iconographic analysis
8. **Additional Institutional Sections** (sculpture/architecture contexts) - May include "Architectural Sculpture and Integration," "Institutional Patronage Structure" for major commissions

Note: Section titles vary by artist discipline (sculptors use "Sculptural Style"; painters have additional institutional analysis sections). The section structure supports narrative coherence while documenting complex patronage networks.

### Writing Style & Conventions
- **Highly detailed, academic prose**: Multi-paragraph sections (2-6+ paragraphs per section) with extensive contextual information; each paragraph develops a single argument with supporting evidence
- **Medieval Italian focus**: Emphasis on Siena, Florence, Umbria; Byzantine-to-Renaissance transition; Tuscan workshop dynamics (goldsmith families, guild structures)
- **Named figures as network nodes**: Detailed patronage relationships, family workshops, artistic dynasties; emphasize who trained whom, family marriages (e.g., "Giovanna married Simone Martini"), financial interdependence
- **Technical art history vocabulary**: Fresco techniques ("giornata," true fresco), "Maniera Greca," chiaroscuro, sfumato, volumetric modeling, drapery treatment, altarpieces, polychromy, relief carving
- **Archival detail**: Specific dates (where documented), payment records, institutional documentation; e.g., "The Commune of San Gimignano recorded a payment to 'Memmo pittore e Lippo suo figliuolo'" establishes both patronage and family hierarchy
- **Contextual richness**: Each artist situated within broader systems—guilds, trade routes, ecclesiastical structures, political regimes, pilgrimage routes (Via Francigena), economic patronage cycles
- **Bibliographic literacy**: References to medieval chronicles (Vasari, Boccaccio), modern scholarship; acknowledgment of historiographical gaps and misattributions
- **Reciprocal causality**: Explain not just what happened but why—e.g., why Memmo's goldsmith father mattered to his painting technique, why Podestà's 6-month terms influenced fresco subject matter
- **Physical and sensory specificity**: Describe materials (lapis lazuli, ultramarine, marble types), light effects, viewer positioning; e.g., "The cathedral's clerestory windows illuminate the polychromed surfaces"

## Key Project Workflows

### Commit and Versioning Workflow
- **Incremental commits**: Commit changes after completing each major section (e.g., "Add Early Life section to [Artist Name]") rather than waiting for entire article completion
- **Commit message format**: Use descriptive messages following pattern: "Add [Section Name] to [Artist Name]" or "Update [specific detail] in [Artist Name]"
- **Work-in-progress articles**: Acceptable to commit incomplete articles with clear indication in README or commit message (e.g., "WIP: [Artist Name] - sections 1-3 complete")
- **Factual corrections**: Prioritize commits that fix dates, attributions, or archival references; message format: "Correct [specific error] in [Artist Name]"
- **Cross-reference updates**: When adding/modifying an artist, review and update cross-references in related artist files; commit as: "Update cross-references: [Artist A] ↔ [Artist B]"
- **Script modifications**: Changes to `add_sections.py` should be committed separately from content changes; include test run results in commit message
- **Batch updates**: When applying consistent formatting or structural changes across multiple files, use batch commit: "Standardize [specific element] across [number] artist files"
- **Restoration of deleted content**: If reverting changes, explain reasoning in commit message: "Restore [content] in [Artist Name] - original formulation more historically accurate"

### Content Additions & Maintenance
- **New artist files**: Create markdown following the standard section structure above. Begin with "Early Life and Family" using biographical/genealogical evidence; progressively build outward to geography and legacy
- **Section organization**: Use `add_sections.py` to inject `##` heading markers into flowing prose that lacks structure
  - Script pattern: Opens file → defines replacement tuples (old_text → new_text) with exact string matching → writes back
  - Example: Detect phrase like "early fourteenth-century Italy.\n\nGiotto's reputation drew" and insert "## Patrons and Commissions\n\n" between paragraphs
  - Usage: `python3 add_sections.py "Artist Name.md" --dry-run` (accepts filename as argument; use --dry-run to preview changes)
  - Configuration: Edit REPLACEMENTS dictionary in script to add patterns for new files before running
  - Important: Review the generated sections for accuracy; the script is a structural aid, not semantic analyzer
- **Updating existing files**: Preserve existing structure and tone. When expanding a section, maintain paragraph-length explanations rather than bullet points
- **Cross-reference verification**: When adding names or dates, cross-check against existing artist files to ensure consistency (e.g., Memmo's relationship to Lippo, Simone Martini's connection to San Gimignano)

### Content Priority Criteria for New Artists

When deciding which artists to add to the database, prioritize based on:

**Tier 1 - Immediate Priority (4000+ words target)**
- **Foundational masters**: Artists who defined stylistic movements (e.g., Duccio, Cimabue, Pietro Cavallini)
- **Documented workshop dynasties**: Artists with well-documented family workshops and patronage networks
- **Cross-referenced figures**: Artists mentioned in 3+ existing articles but lacking dedicated entries
- **Archival richness**: Artists with substantial surviving contracts, payment records, or contemporary documentation
- **Major civic/ecclesiastical commissions**: Artists who executed significant works for Siena, Florence, Assisi, or major cathedrals

**Tier 2 - High Priority (2000-4000 words target)**
- **Regional school representatives**: Key figures in Sienese, Florentine, Umbrian, or Pisan traditions
- **Transitional figures**: Artists bridging Byzantine to Proto-Renaissance or Romanesque to Gothic
- **Documented collaborators**: Artists who worked alongside Tier 1 masters with clear attribution evidence
- **Pilgrimage route artists**: Masters active along Via Francigena or other major pilgrimage routes
- **Workshop successors**: Second-generation masters who perpetuated established traditions

**Tier 3 - Standard Priority (1000-2000 words target)**
- **Specialized craftsmen**: Goldsmiths, miniaturists, or sculptors with distinct technical contributions
- **Provincial masters**: Artists working in secondary Tuscan or Umbrian towns with surviving works
- **Fragmentary attribution cases**: Anonymous masters identified through stylistic analysis ("Maestro di...")
- **Single major work survivors**: Artists known primarily through one significant surviving commission
- **Guild and institutional figures**: Artists documented in guild records but with limited surviving work

**Tier 4 - Contextual Priority (500-1000 words target)**
- **Apprentices and assistants**: Documented workshop members with minimal independent work
- **Family members**: Relatives of major artists with supporting roles (e.g., Memmo's son Federico)
- **Cross-reference completeness**: Minor figures mentioned in existing articles requiring brief biographical entries
- **Archival mentions**: Artists appearing in payment records but lacking attributed works

**Exclusion Criteria**
- Artists with no surviving works AND no substantial archival documentation
- Renaissance masters post-1400 (outside database temporal scope)
- Artists whose attribution remains highly contested with no scholarly consensus
- Non-Italian masters unless directly involved in Italian commissions (e.g., French masters at Avignon papal court)

**Evidence Threshold**
- Minimum requirement: Either 1 surviving attributed work OR 2+ independent archival mentions OR consistent scholarly recognition
- Preferred: Combination of attributed works + documentary evidence + established art historical literature

### Critical Decision: Human-Centric Design
This database is **not optimized for machine indexing or structured data extraction**. It prioritizes:
- Rich contextual narrative over rigid schema
- Prose readability over metadata tagging
- Historical accuracy and nuance over standardization
- Scholarly authority over accessibility features (no glossaries, indices, or semantic markup)

**Implication for AI agents**: Any proposed structural changes must preserve narrative quality and scholarly tone. Consider whether standardization serves readers or just machines.

## Content Cross-References & Interconnections

### Artist Network Map (partial)
- **Memmo di Filippuccio** (father) → **Lippo Memmi** (son, pupil of Simone Martini)
- **Memmo di Filippuccio** → **Simone Martini** (son-in-law, via daughter Giovanna)
- **Giotto di Bondone** (teacher/influence) → influenced **Memmo di Filippuccio**, **Simone Martini**, **Maestro delle Storie di Isacco** (possibly Giotto himself)
- **Duccio di Buoninsegna** → foundational to **Memmo di Filippuccio** and all Sienese painters; influenced later repainting of **Coppo di Marcovaldo**'s Madonna del Bordone
- **Coppo di Marcovaldo** → influenced **Cimabue** (stylistic debate ongoing); father-son workshop with **Salerno di Coppo**
- **Giunta Pisano** → influenced **Coppo di Marcovaldo** and **Cimabue**; established Christus patiens iconography
- **Cimabue** (teacher) → **Giotto di Bondone**; possibly trained **Maestro delle Storie di Isacco**
- **Berlinghiero Berlinghieri** → contemporary/predecessor to **Giunta Pisano** in Pisan tradition

### Priority Artist Additions (Heavily Cross-Referenced but Missing)
The following artists are mentioned extensively across existing articles but lack dedicated entries:
- ✅ **Duccio di Buoninsegna** - NOW COMPLETE (foundational Sienese master)
- ✅ **Cimabue** - NOW COMPLETE (critical link between Coppo/Giunta and Giotto)
- ✅ **Simone Martini** - NOW COMPLETE (son-in-law of Memmo; major Sienese painter)
- ❌ **Lippo Memmi** - Son of Memmo; collaborated with father and Simone Martini; mentioned in 10+ files
- ❌ **Pietro Cavallini** - Roman master; influenced spatial developments; mentioned in 8+ files (Cimabue, Corso di Buono, Maestro delle Storie di Isacco)
- ❌ **Salerno di Coppo** - Son/collaborator of Coppo; documented 1274 crucifix work

### Patronage & Geographic Hubs
- **Siena**: Artistic capital; home to Duccio, Simone Martini, Memmo family
- **San Gimignano**: Secondary hub; Memmo as "Pictor Civicus"; civic commissions dominate
- **Assisi (Basilica of San Francesco)**: International workshop; Giotto, Cimabue, Memmo worked here
- **Padua**: Intellectual center; Giotto's Arena Chapel (1303–1306)

### Stylistic Evolution Tracked
Medieval pattern: "Maniera Greca" (Byzantine) → Proto-Renaissance (Giotto) → Gothic refinement (Simone Martini) → International Gothic. Each artist's work documents one phase of this transition.

## Guidelines for Content Modifications

1. **Preserve scholarly depth**: Avoid simplifying complex patronage or stylistic arguments. If simplification is necessary, add clarifying context rather than deleting nuance.
2. **Maintain narrative flow**: Don't break flowing prose into bullet points unless the original article already uses them. Multi-paragraph explanations are preferred.
3. **Honor archival specificity**: Dates, names, and documentary references are intentional. Verify exact dates against existing files before modifying (e.g., payment records to "Memmo pittore e Lippo suo figliuolo" in 1317).
4. **Respect artist hierarchy**: Giotto and Duccio merit expansive treatment (4000+ words); mid-tier artists 2000–4000 words; lesser-known masters 1000–2000 words. Match new content to artist's documented historical significance.
5. **Check cross-references**: When mentioning another artist, verify consistency with that artist's file. Family relationships, patronage timelines, and stylistic influences should align across files (e.g., Simone Martini married Giovanna, daughter of Memmo).
6. **Avoid anachronistic terminology**: Use period-appropriate language and historical frameworks. "Renaissance" is acceptable for later figures; earlier artists use "Proto-Renaissance" or "Romanesque" as appropriate.
7. **Document uncertainty transparently**: When dates or attributions are debated, acknowledge the historiography: "Scholars debate whether..." or "The date remains uncertain, though documentary evidence suggests..." Don't flatten ambiguity.

## File Naming and Organization Conventions

### Artist File Naming
- **Standard format**: `[First Name] [Patronymic/Family Name].md` (e.g., `Memmo di Filippuccio.md`, `Giotto di Bondone.md`)
- **Italian name order**: Maintain historical Italian naming conventions; keep patronymics intact ("di", "da", "del", "della")
- **Capitalization**: Capitalize first letter of each significant word: `Giovanni d'Apparecchiato.md` (lowercase "d'" is acceptable for articles/prepositions)
- **Anonymous masters**: Use full scholarly designation: `Maestro di [Location/Attribution].md` (e.g., `Maestro di Sant'Alò.md`)
- **Multiple name variants**: Choose the most historically documented form; note variants in first paragraph of article
- **Special characters**: Use standard apostrophes and accents as they appear in scholarly sources (e.g., `Sant'Alò`, not `Sant-Alo`)
- **Disambiguation**: If two artists share names, append birth/death dates in parentheses: `Giovanni Pisano (c.1250-1315).md`
- **Family workshop attributions**: For collective works, file under most prominent family member with notation in content

### Non-Artist Files
- **Historical documents**: Use full formal title: `Codex Aureus of Saint Emmeram.md`
- **Supporting documentation**: Lowercase with hyphens for technical files: `add_sections.py`, `README.md`
- **Geographic/institutional surveys**: Format as `[Institution/Location] - [Topic].md`

### Organization Principles
- All artist files reside directly in `Artists/` directory (no subdirectories by period, region, or medium)
- Alphabetical sorting by first name (medieval convention; "Giotto" not "Bondone")
- Utility scripts remain at root level of `Artists/` directory
- No numerical prefixes or date-based sorting (defeats scholarly findability)

## File Format Notes
- All markdown files use UTF-8 encoding with multiline prose paragraphs (typically 3-8 sentences per paragraph)
- No YAML front matter or structured metadata layers
- Section headings marked with `##` (markdown level 2 only; no level-1 or level-3+ headings within article body)
- Emphasis via italics (*text*) for key concepts (e.g., *pontile*, *Massaro*, *giornata*), bold for titles/proper names requiring emphasis
- Internal cross-references via artist names (not markdown links); e.g., "Following the style of Giotto di Bondone" rather than "[Giotto](./Giotto%20di%20Bondone.md)"
- Paragraph breaks: Double newlines between paragraphs; single newlines within continuous prose
- Long quotations from archival sources embedded inline with context; no separate blockquote formatting

## Media and Image Guidelines

### Current State: Text-Only Repository
MinDatabase currently operates as a **text-only scholarly resource** with no embedded images, photographs, or multimedia elements. This decision reflects:
- Focus on dense analytical prose over visual documentation
- Copyright complexities for medieval artworks photographed in situ
- Bandwidth efficiency for academic research contexts
- Emphasis on art historical description as primary interpretive mode

### Image Integration Policy (If Future Implementation)
Should images be added in future, follow these principles:

**Permitted Image Types**
- Public domain photographs of artworks pre-1900
- Creative Commons licensed images with proper attribution
- Own photography of artworks where permitted by institutions
- Line drawings, diagrams, or reconstructions created for the project
- Archival document reproductions (contracts, payment records) where legally obtained

**Image Organization**
- Store images in dedicated `/images/[Artist Name]/` subdirectories
- Naming convention: `[Artist Name] - [Work Title] - [Detail Description].jpg`
- Example: `Memmo di Filippuccio - Camera del Podestà - Bath Scene Detail.jpg`
- Include `images/README.md` with licensing information and source citations

**Markdown Integration**
- Place image references at END of relevant section, never interrupting prose flow
- Format: `![Figure: Work Title, Location, Date](../images/[path])` with caption following
- Caption format: "**Figure [number]**: [Work Title], [Artist], [Date], [Current Location]. [Medium and dimensions]. [Photo credit/source]."
- Example:
  ```markdown
  ![Figure: Maestà, Palazzo del Popolo](../images/Lippo-Memmi/Maesta-San-Gimignano.jpg)
  
  **Figure 1**: Maestà, Lippo Memmi (signed 1317), Sala di Dante, Palazzo del Popolo, San Gimignano. Fresco. Photo: Scala/Art Resource, NY.
  ```

**Copyright and Attribution Requirements**
- Every image requires documented copyright status or public domain verification
- Museum/institutional photo credits mandatory even for PD works
- Maintain `images/LICENSE.md` listing every image source and copyright status
- Prefer photographs from Wikimedia Commons, Artstor (if licensed), or institutional open access collections
- When in doubt about copyright, **do not include the image**—detailed prose description is preferable to legal risk

**Alternative to Images: Enhanced Descriptions**
Given the current text-only approach, compensate through:
- Precise spatial descriptions ("upper left quadrant," "central register," "right terminal of cross")
- Color terminology ("ultramarine blue mantle," "vermilion accents," "burnished gold ground")
- Compositional analysis ("figures arranged in strict isocephaly," "pyramidal composition," "axial symmetry")
- Comparative references ("following the Sienese convention of...," "departing from Giotto's approach in...")
- Viewer positioning ("visible to congregations in the nave," "at eye level for medieval observers")

**Technical Specifications (If Implemented)**
- Format: JPEG for photographs, PNG for diagrams/line art
- Resolution: 1200px longest dimension (sufficient for screen viewing, not print reproduction)
- Compression: Balance quality vs. file size (target <500KB per image)
- Color space: sRGB for web compatibility
- Metadata: Embed EXIF copyright and creator information

**When Adding Images, Update:**
- Repository README noting transition from text-only to illustrated
- `.gitattributes` to handle binary files appropriately
- `images/.gitignore` if excluding high-resolution originals
- Citation style guide to include figure reference conventions

### Embedded Video/Audio: Not Recommended
- Repository designed for static, archival scholarly content
- Multimedia files increase repository size exponentially
- Hosting platforms (YouTube, Vimeo) more appropriate for video content
- If video demonstrations needed (e.g., fresco technique explanations), link to external hosted content rather than embedding

## Technical Tools
- **add_sections.py**: Python utility script for inserting section headings into markdown files
  - Located in: `Artists/add_sections.py`
  - Usage: `python3 add_sections.py "Artist Name.md" [--dry-run]`
  - Configuration: Edit REPLACEMENTS dictionary in script to define exact text patterns for each file
  - Pattern: Uses exact string matching to find paragraph boundaries and insert `## Section Title` markers
  - Workflow: Add replacement patterns to REPLACEMENTS dict → run with --dry-run to preview → run without flag to apply
  - Important: Modifies files in-place; review generated structure for accuracy before committing
  - Example: Script detects "early fourteenth-century Italy.\n\nGiotto's reputation drew" and inserts section heading between paragraphs

## Common Content Patterns by Section

**Early Life and Family**: Establish father's profession/reputation → family's social standing → training environment → sibling/dynastic context. Example: "Memmo di Filippuccio was born into a specialised artisan family in Siena, the son of the goldsmith Filippuccio..."

**Patrons and Commissions**: Lead with most prestigious patron → detail specific commissions with dates → describe negotiation/collaboration → financial arrangements → list secondary patrons (ecclesiastical, civic, private). Each patron gets dedicated paragraph(s).

**Artistic Style** (painters/sculptors): Identify foundational influences (e.g., "Maniera Greca") → describe technical evolution → cite specific works as evidence → emphasize synthesis of traditions. Use comparative analysis: "unlike Wiligelmo's more archaic style" vs. "inheriting Duccio's lyrical line."

**Major Works**: Each masterpiece gets dedicated paragraph with location, date (c. 1303–1310), historical context, technical details, and iconographic analysis. Structure: Opening hook → visual description → technique/materials → interpretation → legacy/influence.

**Travels and Career**: Trace geographic movement as career progression, not random movement. Connect travel to patronage opportunities and stylistic development: "The journey from Campione d'Italia to Provence exposed him to Provençal sculpture, fundamentally shaping his compositional approach."

## Handling Misattributions and Historiographical Confusion

Early art historical sources (Vasari, Ghiberti, medieval chronicles) frequently conflate artists, confuse family relationships, or misidentify works. When addressing such errors:

- **Acknowledge the confusion transparently**: "Early chroniclers like Vasari famously confused the relationships, sometimes conflating Lippo and Memmo or misidentifying their connection to Simone Martini."
- **Document the correction through archival evidence**: Ground corrections in specific payment records, contract dates, or stylistic analysis rather than dismissing older sources outright
- **Explain *why* confusion arose**: Was it generational proximity? Shared workshop practices? Family name ambiguity (e.g., "Memmi" as patronymic)?
- **Preserve the historiographical narrative**: Show how modern scholarship disentangled the confusion; this demonstrates the evolution of art historical knowledge
- **Cross-check against multiple existing files**: If clarifying Lippo's relationship to Memmo, verify consistency across entries for Memmo, Lippo, and Simone Martini

Example pattern: "It has taken modern archival research to disentangle Memmo di Filippuccio's individual contributions from the collective output of his 'bottega'. We now recognise Memmo not merely as 'Lippo's father' but as a pivotal figure..."

## Documenting Lesser-Studied Artists with Fragmentary Evidence

When archival documentation is sparse or artistic output is fragmentary, employ these strategies:

- **Lead with documented facts, however minimal**: Establish what *is* certain (a single payment record, one surviving work, association with a major patron) before addressing gaps
- **Use institutional connections as scaffolding**: If individual biography is obscure, reconstruct activity through the patron's records. Example: "The cathedral chapter's financial records document payments to 'Maestro X' for specific tasks, though personal details remain elusive."
- **Contextualize through workshop networks**: Discuss the artist in relation to documented masters and patrons who employed them. Stylistic analysis of surviving works can infer training lineage
- **Distinguish documented vs. inferred relationships**: Use phrases like "likely trained," "probably worked," "possibly influenced" to signal levels of certainty
- **Highlight what we *don't* know**: "The date of birth remains unknown, though guild records suggest activity beginning circa 1290."
- **Compare fragmentary output to documented contemporaries**: If few works survive, analyze them against established stylistic evolutions (e.g., Byzantine → Proto-Renaissance transition) to establish chronological placement
- **Proportionality**: Lesser-known masters receive 1000–2000 words; focus on quality of available evidence rather than padding with speculation

Example opening: "Maestro di Sant'Alò remains among the most elusive masters of the Trecento, known through a single documented commission and two or three surviving works that exhibit stylistic characteristics suggesting training within the Sienese tradition..." This immediately signals both the evidence limit and the analytical framework.

## When in Doubt
- Consult the structural patterns in existing files (especially [Memmo di Filippuccio.md](Artists/Memmo%20di%20Filippuccio.md) and [Giotto di Bondone.md](Artists/Giotto%20di%20Bondone.md))
- Prioritize historical accuracy and nuance over editing brevity
- Ask: "Does this change serve the reader's understanding of medieval Italian art history?"

## Repository Structure
```
MinDatabase/
├── .github/
│   ├── copilot-instructions.md    # This file - AI agent guidance
│   └── Codex/
│       └── Codex Aureus of Saint Emmeram.md  # Historical document
├── Artists/
│   ├── add_sections.py            # Section heading insertion utility
│   ├── README.md                  # Project entry point (comprehensive)
│   └── [Artist Name].md           # Individual artist essays (22 files)
└── .gitignore                     # Git ignore patterns
```

## Workspace Maintenance Notes
- **Ignore system files**: `.DS_Store` (macOS) and other system files are excluded via `.gitignore`
- **Python script workflow**: When using `add_sections.py`, edit the REPLACEMENTS dictionary to add patterns for the target file, then run with filename argument
- **Commit discipline**: Follow incremental commit workflow (see "Commit and Versioning Workflow" section) rather than batch commits
