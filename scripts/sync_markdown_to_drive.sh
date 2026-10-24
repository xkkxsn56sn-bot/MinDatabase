#!/bin/bash
# Mirror the published Markdown files (git-tracked *.md under Content/) into a
# dedicated subfolder of Google Drive, keeping the folder structure. Files
# renamed or deleted in the repo disappear from Drive too, but only inside
# that subfolder.
#
# The Drive root is read from the untracked file .sync_drive_path (first line,
# e.g. ~/Library/CloudStorage/GoogleDrive-.../Il mio Drive).
#
# Usage: scripts/sync_markdown_to_drive.sh [--dry-run] [--quiet]

set -euo pipefail

DEST_NAME="MinDatabase-Markdown"
DRY=0
QUIET=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --quiet) QUIET=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

say() { [ "$QUIET" -eq 1 ] || echo "$@"; }
die() { echo "sync_markdown_to_drive: $*" >&2; exit 1; }

REPO="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
CONFIG="$REPO/.sync_drive_path"
[ -f "$CONFIG" ] || die "missing $CONFIG (write the Google Drive root path in it); nothing done"

ROOT="$(head -n 1 "$CONFIG")"
ROOT="${ROOT/#\~/$HOME}"
[ -n "$ROOT" ] || die ".sync_drive_path is empty; nothing done"
[ -d "$ROOT" ] || die "Google Drive folder not reachable: $ROOT (app off or path changed); nothing done"

DEST="$ROOT/$DEST_NAME"
[ "$DRY" -eq 1 ] || mkdir -p "$DEST"
[ "$DRY" -eq 1 ] && [ ! -d "$DEST" ] && say "(destination does not exist yet: $DEST)"

# Tracked, existing, published Markdown only, relative to Content/
# (prompts/ holds working files, excluded from the content checks too).
LIST="$(mktemp)"
trap 'rm -f "$LIST"' EXIT
cd "$REPO/Content"
git -c core.quotepath=off ls-files -z -- '*.md' ':!prompts/' | while IFS= read -r -d '' f; do
  [ -f "$f" ] && printf '%s\0' "$f"
done > "$LIST"
COUNT="$(tr -cd '\0' < "$LIST" | wc -c | tr -d ' ')"
[ "$COUNT" -gt 0 ] || die "no Markdown files found under Content/; refusing to mirror (would empty Drive)"

# Only the dedicated subfolder is ever touched.
RSYNC=(rsync -rt --from0 --files-from="$LIST" --delete --itemize-changes)
[ "$DRY" -eq 1 ] && RSYNC+=(--dry-run)
OUT="$("${RSYNC[@]}" "$REPO/Content/" "$DEST/" 2>&1)" || { echo "$OUT" >&2; die "rsync failed"; }

COPIED="$(printf '%s\n' "$OUT" | grep -c '^[<>]f' || true)"
DELETED="$(printf '%s\n' "$OUT" | grep -c '^\*deleting' || true)"
if [ "$DRY" -eq 1 ]; then
  printf '%s\n' "$OUT"
  say "Dry run: $COUNT source files, $COPIED to copy, $DELETED to delete (dest: $DEST)"
else
  say "Synced: $COUNT source files, $COPIED copied, $DELETED deleted (dest: $DEST)"
fi
