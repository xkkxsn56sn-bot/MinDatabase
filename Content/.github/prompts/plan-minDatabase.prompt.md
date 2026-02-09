## Plan: Add Repo-Level Copilot Instructions

This repo is a content-only Markdown knowledge base with long-form academic essays under .github/Artists (century subfolders), .github/Churches, .github/Codex, and .github/Papirer. You want a new root instructions file at .github/copilot-instructions.md covering the entire repo, while leaving the existing Papirer instructions in place. The plan is to draft a concise, repo-wide instruction set that reflects the observed structure, writing conventions, and citation patterns, and to reference the Papirer-specific instructions for that subarea.

**Steps**
1. Review the current content patterns and structure in the main content folders to codify repo-wide norms, and note the existing Papirer instructions for reuse or pointers: .github/Artists/, .github/Churches/, .github/Codex/, and .github/Papirer/, and .github/Papirer/.github/copilot-instructions.md.
2. Draft a new root instruction file that captures: content-only scope, folder conventions, filename patterns, section/heading variance, citation/footnote preservation, image handling preferences, and "do not normalize or restructure" guidance, with a brief note to consult Papirer-specific instructions when editing that subtree: .github/copilot-instructions.md.
3. Sanity-check the new instructions for clarity, brevity, and alignment with the existing content style and Markdown validation settings (no tests/builds).

**Verification**
Open the new instructions file to confirm it reads cleanly and matches the repo’s observed conventions: .github/copilot-instructions.md.

**Decisions**
- Scope: entire repo.
- Location: add a new root-level .github/copilot-instructions.md.
