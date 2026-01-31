# MinDatabase - AI Agent Instructions

**Version**: 2.0 | **Last Updated**: 31 January 2026

## Quick Start for AI Agents

This is a **scholarly knowledge repository**, NOT a software project. No builds, tests, or deployments—only rich historical prose.

**Core Task**: Write detailed (1000-4000+ word) academic essays on medieval Italian artists (13th-14th century) using:
- Multi-paragraph sections (2-6+ paragraphs each) with archival evidence and art historical analysis
- Standard structure: Early Life → Patrons → Artistic Style → Influences → Travels → Legacy → Major Works
- Technical vocabulary: fresco techniques, "Maniera Greca," chiaroscuro, volumetric modeling, patronage networks
- Cross-reference existing artists to document family workshops, training lineages, and patronage relationships

**Key Files**: `.github/Artists/[Artist Name].md` | `.github/Churches/[Church Name].md` | `.github/Artists/README.md` (master index)

**Commit Pattern**: Incremental commits per section: `"Add Early Life section to [Artist Name]"` | Update `.github/Artists/README.md` when adding new artists

**Critical**: Preserve scholarly tone, archival specificity, and narrative flow. This is academic writing, not technical documentation.

---

## Project Overview
MinDatabase is a scholarly database of detailed historical essays on medieval Italian artists. This is NOT a software project but a knowledge repository focused on art history, particularly Tuscan painters and sculptors from the 13th-14th centuries (Duecento and Trecento periods).

## Core Architecture & Content Patterns

### File Structure
- Individual artist profile files: `[Artist Name].md` (in .github/Artists/ directory)
- Church/institutional essays: `[Church Name].md` (in .github/Churches/ directory - architectural and art historical analysis)
- Codex documentation: Historical documents (in .github/Codex/ directory)
- Utility script: `add_sections.py` - automates section heading insertion into markdown files (located in .github/Artists/)
- Main entry point: `.github/Artists/README.md` (comprehensive artist index organized by period, region, and medium)

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

### Standard Church/Institutional Essay Structure
Church and institutional essays (in Churches/ directory) follow a distinct architectural/art historical format:
1. **History of the [Frescoes/Decoration]** - Construction chronology, patronage origins, building campaigns, architectural phasing, commissioning circumstances
2. **Materials and Techniques** - Technical execution (fresco vs. secco), pigment analysis, scientific studies (SEM-EDS, infrared reflectography), preparation methods (arriccio, giornata), conservation findings
3. **Artists and Their Background** - Workshop organization, regional stylistic affiliations (e.g., "Angevin style"), itinerant painter networks, anonymity vs. documented masters, training lineages
4. **Religious Art and Church Furnishings** - Liturgical function (Benedictine Divine Office, monastic ceremonial), spatial organization (choir, transept, crypt), reliquary shrines, lost furnishings (altar cloths, metalwork)
5. **Illuminated Manuscripts and Pictorial Arts** - Relationship between mural painting and manuscript illumination, iconographic model transmission, scriptoria connections, shared pigment palettes
6. **External Influences** - Carolingian/Ottonian precedents, Byzantine transmissions, regional schools (Angevin, Poitevin), pilgrimage route networks, transalpine Gothic influences
7. **Preservation and Conservation** - Destruction/survival history (Wars of Religion, French Revolution), 19th-century rescue campaigns (Mérimée), modern conservation science, UNESCO designation

Note: Church essays emphasize **anonymous workshop traditions** and **architectural integration**, contrasting with artist essays' focus on individual biography and patronage networks. Cross-reference artists when documented (e.g., "Giotto worked here circa 1290"), but accept anonymity as historical norm for monumental decoration.

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
<<<<<<< HEAD
The following artists are mentioned extensively across existing articles but lack dedicated entries:
- ✅ **Duccio di Buoninsegna** - NOW COMPLETE (foundational Sienese master)
- ✅ **Cimabue** - NOW COMPLETE (critical link between Coppo/Giunta and Giotto)
- ✅ **Simone Martini** - NOW COMPLETE (son-in-law of Memmo; major Sienese painter)
- ❌ **Lippo Memmi** - Son of Memmo; collaborated with father and Simone Martini; mentioned in 10+ files
- ❌ **Pietro Cavallini** - Roman master; influenced spatial developments; mentioned in 8+ files (Cimabue, Corso di Buono, Maestro delle Storie di Isacco)
- ❌ **Salerno di Coppo** - Son/collaborator of Coppo; documented 1274 crucifix work
=======
The following artists are mentioned extensively across existing articles but still lack dedicated entries:
- **Lippo Memmi** - Son of Memmo; collaborated with father and Simone Martini; co-signed 1333 Annunciation
- **Pietro Cavallini** - Roman master; influenced spatial developments; mentioned in Giotto and other contexts
- **Salerno di Coppo** - Son/collaborator of Coppo; documented 1274 crucifix work
- **Ambrogio Lorenzetti** - Major Sienese painter; Palazzo Pubblico frescoes
- **Pietro Lorenzetti** - Brother of Ambrogio; important Sienese master
- **Andrea Pisano** - Sculptor; Florence Baptistery bronze doors

**Recently Added (Now Complete):**
- ✓ Duccio di Buoninsegna - Foundational Sienese master
- ✓ Cimabue - Critical link between Coppo/Giunta and Giotto
- ✓ Simone Martini - Son-in-law of Memmo; major Sienese painter
>>>>>>> fb4075e (Reorganize repository structure and update documentation to v2.0)

### Patronage & Geographic Hubs
- **Siena**: Artistic capital; home to Duccio, Simone Martini, Memmo family
- **San Gimignano**: Secondary hub; Memmo as "Pictor Civicus"; civic commissions dominate
- **Assisi (Basilica of San Francesco)**: International workshop; Giotto, Cimabue, Memmo worked here
- **Padua**: Intellectual center; Giotto's Arena Chapel (1303–1306)

### Stylistic Evolution Tracked
Medieval pattern: "Maniera Greca" (Byzantine) → Proto-Renaissance (Giotto) → Gothic refinement (Simone Martini) → International Gothic. Each artist's work documents one phase of this transition.

### Cross-Reference Patterns: Churches ↔ Artists
Church essays and artist essays interlink through shared geographic/temporal contexts:

**From Church → Artist** (when documented masters worked on site):
- Direct attribution: "Giotto di Bondone executed the Arena Chapel frescoes (1303-1306)" → link to Giotto essay
- Workshop attribution: "The Assisi Upper Church frescoes, attributed to the workshop of Cimabue or possibly the young Giotto" → mention both with caveats
- Documented presence: "Payment records confirm Memmo di Filippuccio's work in San Gimignano's Palazzo del Popolo"

**From Church → Anonymous Masters** (establish pattern for future artist entries):
- Use scholarly designation: "The Saint-Savin murals were executed by an anonymous Romanesque Painter, French (active c. 1100)"
- Describe workshop characteristics: "Itinerant professional painters traveling among ecclesiastical building sites"
- Regional stylistic affiliation: "The Angevin style, characterized by linear designs and flat compositional arrangements"
- This establishes nomenclature for potential future artist entries on anonymous masters

**From Artist → Churches** (when artist worked at documented sites):
- Narrative integration: In "Travels and Career" section, mention specific commissions: "Giotto's journey to Padua resulted in the revolutionary Arena Chapel frescoes"
- Patronage documentation: In "Patrons and Commissions," cite institutional records: "The Franciscan order at Assisi commissioned Giotto for the Upper Church narrative cycles"
- Cross-regional influence: "Exposure to French Gothic architectural sculpture at Rheims influenced Anselmo da Campione's later work"

**Maintaining Cross-Reference Consistency**:
- When adding new church essay, search existing artist files for mentions of that site
- When adding artist who worked at documented church, verify church essay exists or add to priority list
- Use consistent terminology: "Assisi (Basilica of San Francesco)" not "Assisi Basilica" or "San Francesco d'Assisi"
- Anonymous masters: Use scholarly convention ("Maestro di [Location]") to enable future dedicated entries

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
- **Church/institutional essays**: Use full formal title: `The Abbey Church of Saint-Savin-sur-Gartempe.md` (stored in .github/Churches/ directory)
- **Historical documents**: Use full formal title if needed: `Codex Aureus of Saint Emmeram.md` (stored in .github/Codex/ directory)
- **Supporting documentation**: Lowercase with hyphens for technical files: `add_sections.py`, `README.md`
- **Geographic/institutional surveys**: Format as `[Institution/Location] - [Topic].md` or `The [Full Name].md`

### Organization Principles
- All artist files reside directly in `.github/Artists/` directory (no subdirectories by period, region, or medium)
- Church/institutional essays reside in `.github/Churches/` directory
- Codex documentation resides in `.github/Codex/` directory
- Alphabetical sorting by first name (medieval convention; "Giotto" not "Bondone")
- Utility scripts remain at root level of `.github/Artists/` directory
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
<<<<<<< HEAD
- **add_sections.py**: Python utility script for inserting section headings into markdown files
  - Located in: `Artists/add_sections.py`
  - Usage: `python3 add_sections.py "Artist Name.md" [--dry-run]`
  - Configuration: Edit REPLACEMENTS dictionary in script to define exact text patterns for each file
  - Pattern: Uses exact string matching to find paragraph boundaries and insert `## Section Title` markers
  - Workflow: Add replacement patterns to REPLACEMENTS dict → run with --dry-run to preview → run without flag to apply
  - Important: Modifies files in-place; review generated structure for accuracy before committing
  - Example: Script detects "early fourteenth-century Italy.\n\nGiotto's reputation drew" and inserts section heading between paragraphs
=======

### add_sections.py - Section Heading Insertion Utility
**Purpose**: Automates insertion of `## Section Title` headings into flowing prose that lacks formal structure.

**Location**: `.github/Artists/add_sections.py`

**Command-Line Usage**:
```bash
# Navigate to the script directory first
cd .github/Artists/

# Preview changes without modifying file (recommended first step)
python3 add_sections.py "Giotto di Bondone.md" --dry-run

# Apply changes to file (modifies in-place)
python3 add_sections.py "Coppo di Marcovaldo.md"

# Process file with absolute path
python3 add_sections.py "/Users/.../MinDatabase/.github/Artists/Simone Martini.md"
```

**Configuration**: Edit the `REPLACEMENTS` dictionary within the script before running:
```python
REPLACEMENTS = {
    "Giotto di Bondone.md": [
        ("early fourteenth-century Italy.\n\nGiotto's reputation drew", 
         "early fourteenth-century Italy.\n\n## Patrons and Commissions\n\nGiotto's reputation drew"),
        # Add more replacement tuples...
    ],
}
```

**Pattern**: Uses exact string matching to find paragraph boundaries (double newlines) and insert section headings. Include sufficient context (typically full sentences before/after break point) to ensure unique matches.

**Workflow**:
1. Read target artist file to identify natural section breaks in flowing prose
2. Edit `REPLACEMENTS` dictionary with exact text matches for that specific file
3. Run with `--dry-run` to preview changes
4. Review output carefully—script is structural aid, not semantic analyzer
5. Run without `--dry-run` to apply changes (modifies file in-place)
6. Commit script changes separately from content changes
7. Verify section accuracy by reading modified file; adjust manually if needed

**Important Limitations**:
- Requires manual identification of section boundaries
- String matching must be exact (whitespace, punctuation, spelling)
- Cannot detect semantic meaning—may insert headings at inappropriate breaks
- Works best for prose already organized logically but lacking explicit markers
- Each target file requires custom `REPLACEMENTS` configuration
>>>>>>> fb4075e (Reorganize repository structure and update documentation to v2.0)

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

## Practical Examples

### Example 1: Adding a New Artist Entry

**Task**: Create entry for "Lippo Memmi" (son of Memmo di Filippuccio, mentioned in 3+ existing articles)

**Workflow**:
1. Create `.github/Artists/Lippo Memmi.md`
2. Research cross-references: Read [Memmo di Filippuccio.md](.github/Artists/Memmo%20di%20Filippuccio.md), [Simone Martini.md](.github/Artists/Simone%20Martini.md) for documented relationships
3. Write sections in order: Early Life ("son of Memmo, trained under father's supervision") → Patrons (San Gimignano commissions) → Artistic Style (Gothic sophistication, collaboration with Simone Martini) → etc.
4. Commit incrementally: `"Add Early Life section to Lippo Memmi"` → `"Add Patrons section to Lippo Memmi"` → etc.
5. Update `.github/Artists/README.md`: Add to Sienese School section, Master-Pupil Lineages, Family Workshops, Geographic Hubs
6. Update cross-references: Add mentions in Memmo and Simone Martini files: `"His son Lippo Memmi later collaborated with Simone Martini..."`
7. Final commit: `"Update cross-references: Memmo ↔ Lippo Memmi ↔ Simone Martini"`

**Before** (Memmo di Filippuccio.md - insufficient detail):
```markdown
Memmo's son Lippo became a painter.
```

**After** (Memmo di Filippuccio.md - scholarly richness):
```markdown
Lippo Memmi, the elder and more famous of the two sons, was trained directly under 
Memmo's supervision, inheriting his father's linear elegance while eventually surpassing 
him in fame through his association with Simone Martini. The training Memmo provided to 
his sons was comprehensive, encompassing both the monumental fresco techniques he mastered 
at Assisi and the delicate miniature work of the Sienese tradition. In 1317, the Commune 
of San Gimignano recorded a payment to "Memmo pittore e Lippo suo figliuolo" for the 
painting in the Council Hall, indicating that while Memmo was the legal contractor, Lippo 
was the primary executant.
```

### Example 2: Using add_sections.py to Structure Flowing Prose

**Task**: Artist file exists as continuous prose without section headings

**Workflow**:
1. Read file to identify natural section breaks:
   - "Born in Siena..." (Early Life paragraph) → "The Commune of San Gimignano commissioned..." (Patrons paragraph)
2. Edit `.github/Artists/add_sections.py` REPLACEMENTS dictionary:
```python
REPLACEMENTS = {
    "New Artist.md": [
        ("goldsmith father.\n\nThe Commune of San Gimignano commissioned",
         "goldsmith father.\n\n## Patrons and Commissions\n\nThe Commune of San Gimignano commissioned"),
    ],
}
```
3. Run script:
```bash
cd .github/Artists/
python3 add_sections.py "New Artist.md" --dry-run  # Preview
python3 add_sections.py "New Artist.md"            # Apply
```
4. Review output, manually adjust if section placement incorrect
5. Commit: `"Add section headings to New Artist"`

### Example 3: Cross-Referencing Church and Artist Entries

**Task**: Document Giotto's work at Assisi in both his artist file and a church essay

**In [Giotto di Bondone.md](.github/Artists/Giotto%20di%20Bondone.md)** (Travels section):
```markdown
A critical chapter in his itinerary was the sojourn to Assisi, the epicentre of modern 
Italian painting at the turn of the century. Travelling to Umbria to work at the Basilica 
of San Francesco was a rite of passage for ambitious artists of his generation. In Assisi, 
he lived and worked in the scaffolding of the Upper Church, executing the revolutionary 
fresco cycles (c. 1290-1295) that demonstrated his mastery of spatial naturalism and 
narrative clarity.
```

**In [The Basilica of San Francesco.md](.github/Churches/) essay** (Artists section):
```markdown
Giotto di Bondone executed the Upper Church frescoes circa 1290-1295, though attribution 
remains debated between Giotto and the anonymous Maestro delle Storie di Isacco. Payment 
records confirm Franciscan patronage, and the revolutionary spatial treatment—volumetric 
figures occupying convincing architectural settings—marks a decisive break from Byzantine 
flatness. The workshop organization at Assisi exposed Giotto to Roman, Florentine, and 
Umbrian traditions simultaneously, an international environment that accelerated his 
stylistic evolution.
```

### Example 4: Handling Misattributions and Historiographical Complexity

**Task**: Correct common confusion between Lippo Memmi and Memmo di Filippuccio

**Before** (overly simplified):
```markdown
Lippo Memmi painted the Maestà in San Gimignano.
```

**After** (acknowledges historiographical complexity):
```markdown
Although signed by his son Lippo Memmi, documents prove the 1317 Maestà was a joint 
commission paid to "Memmo and Lippo," representing the culmination of Memmo's civic 
career. Early chroniclers like Vasari famously confused the relationships, sometimes 
conflating Lippo and Memmo or misidentifying their connection to Simone Martini. Modern 
archival research has disentangled their individual contributions: Memmo's hand appears 
most evident in the underlying compositional structure and spatial logic, while Lippo's 
contribution emerges in the delicacy of ornamental details and the refinement of facial 
features. The fact that Lippo alone signed the work may indicate that the primary 
executant for the visible surface was the younger artist, while Memmo retained 
intellectual control over the conception.
```

---

## When in Doubt
- Consult the structural patterns in existing files (especially [Memmo di Filippuccio.md](.github/Artists/Memmo%20di%20Filippuccio.md) and [Giotto di Bondone.md](.github/Artists/Giotto%20di%20Bondone.md))
- Prioritize historical accuracy and nuance over editing brevity
- Ask: "Does this change serve the reader's understanding of medieval Italian art history?"

## Repository Structure
```
MinDatabase/
├── .github/
│   ├── copilot-instructions.md    # This file - AI agent guidance
<<<<<<< HEAD
│   └── Codex/
│       └── Codex Aureus of Saint Emmeram.md  # Historical document
├── Artists/
│   ├── add_sections.py            # Section heading insertion utility
│   ├── README.md                  # Project entry point (comprehensive)
│   └── [Artist Name].md           # Individual artist essays (22 files)
└── .gitignore                     # Git ignore patterns
=======
│   ├── Artists/
│   │   ├── add_sections.py        # Section heading insertion utility
│   │   ├── README.md              # Project entry point (comprehensive artist index)
│   │   └── [Artist Name].md       # Individual artist essays (22+ files)
│   ├── Churches/
│   │   └── [Church Name].md       # Church/institutional essays (1+ files)
│   └── Codex/
│       └── [Historical Document].md  # Historical documents
├── .gitignore                     # Excludes .DS_Store, Python cache, etc.
└── .vscode/                       # VS Code workspace settings
>>>>>>> fb4075e (Reorganize repository structure and update documentation to v2.0)
```

## README.md Maintenance and Organizational Structure

### Current README Organization (.github/Artists/README.md)
The main entry point follows a hierarchical organizational structure:

**Primary Organization** (By Period & Region):
- **Duecento (13th Century)**: Pisan School → Florentine School → Sienese School → Umbrian & Central Italian
- **Trecento (14th Century)**: Florentine Innovations → Sienese School → Sculptors & Architects
- Within each period: Group by regional school or stylistic affiliation
- Within each school: Alphabetical by artist first name
- Include brief identifying details: "[Artist Name] - [Key work/date/defining characteristic]"

**Secondary Organization** (By Medium):
- Panel Painters, Fresco Masters, Sculptors & Stoneworkers, Manuscript Illuminators
- Facilitates finding artists by technical specialization
- Artists may appear in multiple medium categories

**Tertiary Organization** (By Patronage Networks):
- Franciscan Commissions, Dominican Patrons, Civic/Communal Patrons, Servite Order
- Reveals institutional patronage patterns across multiple artists
- Helps identify cross-artist collaboration opportunities at shared sites

**Network Mapping Sections**:
- **Master-Pupil Lineages**: Document training relationships ("Byzantine → Proto-Renaissance: Coppo → Cimabue → Giotto")
- **Family Workshops**: Track dynastic transmission ("Berlinghieri Family: Father + sons")
- **Geographic Hubs**: List artists active at major centers (Assisi, Pisa, Florence, Siena, San Gimignano)

**Stylistic Evolutions Documented**:
- Crucifixion Iconography (Christus triumphans → patiens), Spatial Representation, Marian Imagery
- Traces technical/iconographic innovations across artist entries

### When Adding New Artists to README
1. **Add to Period & Region section**: Determine century (Duecento/Trecento), identify regional school affiliation
2. **Add to Medium section**: Classify by primary technique (panel painter, sculptor, etc.)
3. **Add to Patronage Networks** (if applicable): Identify major institutional patron
4. **Update Network Mapping**: Add to Master-Pupil Lineages if training relationship documented, Family Workshops if dynastic connection exists, Geographic Hubs for primary working location
5. **Update Stylistic Evolutions**: If artist contributed to tracked technical innovations
6. **Update Priority Additions list**: Remove from "forthcoming" if completing that artist; add newly discovered cross-references
7. **Maintain alphabetical order within sections**: Sort by first name (medieval convention)
8. **Use consistent formatting**: `[Artist Name](Artist%20Name.md) - [Brief identifier]`
9. **Encode spaces in links**: Use `%20` for filenames with spaces
10. **Update cross-reference markers**: Use `[Artist Name]*` pattern for missing entries, remove `*` when completed

### README Commit Patterns
- Update README simultaneously with artist file additions: "Add [Artist Name] with README index entry"
- Batch README updates for reorganization: "Reorganize README: Add Patronage Networks section"
- Cross-reference corrections: "Update README: Correct [Artist A]'s relationship to [Artist B]"
- New organizational sections: "Add 'Stylistic Evolutions' tracking section to README"

## Workspace Maintenance Notes
<<<<<<< HEAD
- **Ignore system files**: `.DS_Store` (macOS) and other system files are excluded via `.gitignore`
- **Python script workflow**: When using `add_sections.py`, edit the REPLACEMENTS dictionary to add patterns for the target file, then run with filename argument
=======
- **Ignore system files**: `.DS_Store` (macOS) is already in `.gitignore` to prevent accidental commits
- **Python script modifications**: When updating `add_sections.py`, configuration should be changed to target file before running
>>>>>>> fb4075e (Reorganize repository structure and update documentation to v2.0)
- **Commit discipline**: Follow incremental commit workflow (see "Commit and Versioning Workflow" section) rather than batch commits
- **README updates**: Keep .github/Artists/README.md synchronized with new artist additions; update all relevant organizational sections
