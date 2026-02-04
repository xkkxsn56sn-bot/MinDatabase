# AI Agent Instructions — MinePapirer / Papirer

## Repository Overview

This is a **content-only** repository containing curated long-form Markdown essays about artworks. No builds, tests, or runtime code. All content files live at repository root.

Example: [Giunta Pisano. Crucifix of Saint Dominic.md](Giunta%20Pisano.%20Crucifix%20of%20Saint%20Dominic.md) — a 100-paragraph art historical analysis (29,000+ words).

**Active development**: More artwork essays are planned for future addition.

## File Structure & Naming

### Naming Pattern
- **Format**: `Artist. Title.md` (period after artist name, Title Case throughout)
- **Example**: `Giunta Pisano. Crucifix of Saint Dominic.md`
- Preserve spaces, punctuation, and diacritical marks
- Files stored at repository root (no subdirectories for content)

### Content Structure
Each artwork essay follows academic art history format:
- **H1**: Artist and artwork title
- **H2 sections**: History, Stylistic Analysis, Materials and Techniques, Iconography
- Dense scholarly prose with extensive citations and technical terminology
- Typical length: 5,000–30,000 words per essay

### Images & Assets
- Place images in `images/` directory OR adjacent to the Markdown file
- Use relative paths: `![description](images/artwork-detail.jpg)`
- **Copyright**: Only use public domain or properly licensed images (no copyrighted images)
- Currently no images exist in repository

## Editing Guidelines

### Content Edits
- **Preserve tone**: Academic, formal, art historical register
- **Section structure**: Maintain existing H1/H2/H3 hierarchy
- **Typography**: Keep diacritics (Cennino Cennini), specialized terms (gesso, bole, cymatium)
- **Citations**: Use MLA format for all references and sources
- **Factual corrections**: Small edits welcome (dates, dimensions, provenance)
- **Large rewrites**: Ask before changing entire paragraphs or sections

### What AI Should NOT Do
- ❌ Bulk rename files without confirmation
- ❌ Add build systems, linters, or CI without discussion
- ❌ Rewrite entire essays in a different tone
- ❌ Normalize filename patterns automatically
- ❌ Add generic boilerplate (CODE_OF_CONDUCT, etc.) without asking

### What AI SHOULD Do
- ✅ Fix typos, factual errors, citation formatting
- ✅ Add missing metadata (dates, dimensions, locations)
- ✅ Clarify confusing passages while preserving academic tone
- ✅ Add properly sourced images with citations
- ✅ Create new essays following established pattern

## Git Workflow

**All changes must go through Pull Requests** — no direct commits to main.

### Branch Strategy
```bash
git checkout -b fix/artwork-title-brief-desc
# OR
git checkout -b add/new-artwork-name
```

### Commit Messages
```bash
# Format: "Edit: <filename>: brief description"
git commit -m "Edit: Giunta Pisano. Crucifix of Saint Dominic.md: correct consecration date"

# OR for new files
git commit -m "Add: Leonardo da Vinci. Mona Lisa.md: comprehensive analysis"
```

### Push & PR
```bash
git add <file.md>
git commit -m "Edit: <file>: concise summary"
git push --set-upstream origin <branch-name>
# Then open PR with: list of changed files + brief rationale
```

## Quick Start for AI Agents

1. **Read an existing essay** to understand tone, structure, and depth
2. **Identify the task**: factual correction, new content, or clarification?
3. **Make focused edits**: preserve academic voice and section structure
4. **Test image paths** if adding images (relative paths from root)
5. **Commit with clear message** following format above
6. **Open PR** with concise description of changes

## Technical Details

- **Encoding**: UTF-8 (preserve all diacritics and special characters)
- **Line endings**: LF (Unix-style, configured in `.vscode/settings.json`)
- **No linting/formatting**: Manual prose, no automated tooling
- **Git ignore**: Standard (see `.git/info/exclude` if needed)

## Examples of Good Edits

✅ **Factual correction**:
- Change "1254" to "1251" for basilica consecration date (with source)

✅ **Metadata addition**:
- Add provenance note: "Currently in Basilica di San Domenico, Bologna"

✅ **Image addition**:
- Create `images/giunta-pisano-crucifix-detail.jpg`
- Reference: `![Detail of Christ's face](images/giunta-pisano-crucifix-detail.jpg)`
- Add caption: "Detail showing Giunta's use of verdaccio for flesh tones (Photo: Author, 2025)"

✅ **Clarification**:
- Add footnote explaining "Christus Patiens" vs "Christus Triumphans" for general readers

## Questions Before Proceeding?

If unclear about:
- **Scope**: How much rewriting is acceptable?
- **Sources**: What citation style to use?
- **Images**: Where to find/store artwork photographs?
- **Filenames**: Uncertain about artist/title format?

→ Ask the repository owner before making changes.
