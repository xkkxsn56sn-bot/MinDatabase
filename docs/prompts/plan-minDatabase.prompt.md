## Plan: Add Repo-Level Copilot Instructions

This repo is a content-only Markdown knowledge base with long-form academic essays under Content/.github/Artists (century subfolders), Content/.github/Churches, Content/.github/Codex, and Content/.github/Papirer. You want a root instructions file at MinDatabase - AI Agent Instructions.md covering the entire repo, while leaving any existing Papirer-specific instructions in place. The plan is to draft a concise, repo-wide instruction set that reflects the observed structure, writing conventions, and citation patterns, and to reference any Papirer-specific instructions for that subarea.

**Steps**
1. Review the current content patterns and structure in the main content folders to codify repo-wide norms, and note any Papirer-specific instructions for reuse or pointers: Content/.github/Artists/, Content/.github/Churches/, Content/.github/Codex/, and Content/.github/Papirer/.
2. Draft a root instruction file that captures: content-only scope, folder conventions, filename patterns, section/heading variance, citation/footnote preservation, image handling preferences, and "do not normalize or restructure" guidance, with a brief note to consult any Papirer-specific instructions when editing that subtree: MinDatabase - AI Agent Instructions.md.
3. Sanity-check the new instructions for clarity, brevity, and alignment with the existing content style and Markdown validation settings (no tests/builds).

**Verification**
Open the instructions file to confirm it reads cleanly and matches the repo’s observed conventions: MinDatabase - AI Agent Instructions.md.

**Decisions**
- Scope: entire repo.
- Location: add a root-level MinDatabase - AI Agent Instructions.md.
