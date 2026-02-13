# MinDatabase

"I saw the angel in the marble and carved until I set him free." (Michelangelo)

## Repository Structure

MinDatabase is a scholarly knowledge repository documenting medieval Italian artists (13th-14th centuries, Duecento/Trecento periods) through detailed academic essays.

### Content Organization

All content is organized under the **`Content/.github/`** directory:

- **`Content/.github/Artists/`** - Artist biographies organized by century (VII, VIII, X, XI, XII, XIII, XIII-XIV, XIV)
- **`Content/.github/Churches/`** - Church and institutional essays
- **`Content/.github/Codex/`** - Historical documents
- **`Content/.github/Papirer/`** - Artwork or paper studies
- **`Content/.github/prompts/`** - Planning and prompt templates

### Documentation

For complete guidelines on contributing to this repository, including content structure, file naming conventions, and commit workflows, please refer to:

**[MinDatabase - AI Agent Instructions.md](MinDatabase%20-%20AI%20Agent%20Instructions.md)**

### Note on Repository Reorganization

The `docs/` folder has been deprecated and should be removed. All content is maintained exclusively in `Content/.github/`. To complete the reorganization:

```bash
git rm -r docs/
git commit -m "Remove deprecated docs/ folder - use Content/.github as single source"
git push
```
