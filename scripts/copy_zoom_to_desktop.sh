#!/bin/bash
# Copy every Zoom/Images/**/*-zoom.jpg into ~/Desktop/Zoom/<folder>/,
# keeping the file name (e.g. ~/Desktop/Zoom/Tino-di-Camaino/tino-di-camaino-23-zoom.jpg).
#
# rsync without --delete: a zoom file removed from the repository keeps its
# copy on the Desktop. The destination is created if missing.
#
# Called by scripts/sync_zoom_r2.sh after a successful --apply (the zoom
# files are no longer in git, so the commit hooks no longer trigger it); it
# can also be run by hand. On any error it logs and exits 0.
#
# Usage: scripts/copy_zoom_to_desktop.sh [--dry-run] [--quiet]
#
# Log: .git/copy_zoom.log (last 200 lines).

set -uo pipefail
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE

DRY=0
QUIET=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    --quiet) QUIET=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 0 ;;
  esac
done

say() { [ "$QUIET" -eq 1 ] || echo "$@"; }

REPO="$(cd "$(dirname "$0")/.." && pwd -P)"
DEST="$HOME/Desktop/Zoom"
LOG="$REPO/.git/copy_zoom.log"

log() {
  [ -d "$REPO/.git" ] || return 0
  printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG" 2>/dev/null || return 0
  if [ "$(wc -l < "$LOG")" -gt 200 ]; then
    tail -n 200 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
  fi
  return 0
}

cd "$REPO" || { log "ERROR cannot cd to $REPO"; exit 0; }

# Gli zoom non stanno piu' in git: la sorgente e' la cartella locale Zoom/Images
# (ignorata da git, sincronizzata con R2 da scripts/sync_zoom_r2.sh).
SRC="$REPO/Zoom/Images"
FILES="$(cd "$SRC" 2>/dev/null && find . -type f -name '*-zoom.jpg' | sed 's#^\./##' | LC_ALL=C sort)"
if [ -z "$FILES" ]; then
  log "no zoom files in $SRC"
  say "No zoom files in $SRC."
  exit 0
fi

if [ "$DRY" -eq 0 ]; then
  mkdir -p "$DEST" 2>/dev/null || { log "ERROR cannot create $DEST"; exit 0; }
fi

# <folder>/<file>, relative to Zoom/Images/, so rsync recreates the
# per-scheda subfolders under $DEST.
LIST="$FILES"
OPTS=(-a --itemize-changes)
[ "$DRY" -eq 1 ] && OPTS+=(--dry-run)

OUT="$(printf '%s\n' "$LIST" | rsync "${OPTS[@]}" --files-from=- "$SRC/" "$DEST/" 2>&1)"
RC=$?
COPIED="$(printf '%s\n' "$OUT" | grep -c '^>f' || true)"
TOTAL="$(printf '%s\n' "$LIST" | wc -l | tr -d ' ')"

if [ "$RC" -ne 0 ]; then
  log "ERROR rsync rc=$RC: $(printf '%s' "$OUT" | tr '\n' ' ' | cut -c1-300)"
  say "rsync failed (rc=$RC), see $LOG"
  exit 0
fi

TAG=""; [ "$DRY" -eq 1 ] && TAG="[dry-run] "
log "${TAG}ok: $TOTAL local, $COPIED copied/updated -> $DEST"
printf '%s\n' "$OUT" | grep '^>f' | sed "s#^>f[^ ]* #${TAG}  + #" | while read -r line; do log "$line"; done
say "${TAG}$TOTAL local zoom files, $COPIED copied/updated -> $DEST"
exit 0
