#!/bin/bash
# Full backup of the repository folder (.git, drafts/, untracked files
# included) onto an external volume, with rsync --delete confined to the
# destination. Regenerable folders (_site, caches, node_modules) are skipped.
#
# The destination is read from the untracked file .backup_path (first line,
# e.g. /Volumes/Prog/Sites/MinDatabase). If the volume is not mounted the
# script exits quietly with status 0 and never creates anything on the
# internal disk.
#
# Usage: scripts/backup_to_volume.sh [--dry-run] [--quiet]
#
# Log: .git/backup_to_volume.log (last 200 lines).

set -uo pipefail
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE

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

REPO="$(cd "$(dirname "$0")/.." && pwd -P)"
CONFIG="$REPO/.backup_path"
LOG="$REPO/.git/backup_to_volume.log"
LOCK="$REPO/.git/backup_to_volume.lock"

log() {
  [ "$DRY" -eq 1 ] && return 0
  [ -d "$REPO/.git" ] || return 0
  printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG" 2>/dev/null || return 0
  if [ "$(wc -l < "$LOG")" -gt 200 ]; then
    tail -n 200 "$LOG" > "$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG"
  fi
}

fail() { echo "backup_to_volume: $*" >&2; log "ERROR $*"; exit 1; }

[ -f "$CONFIG" ] || fail "missing $CONFIG (write the destination path in it); nothing done"
DEST="$(head -n 1 "$CONFIG" | tr -d '\r')"
DEST="${DEST/#\~/$HOME}"
DEST="${DEST%/}"

# --- destination sanity ------------------------------------------------------
[ -n "$DEST" ] || fail ".backup_path is empty; nothing done"
case "$DEST" in
  /*) ;;
  *) fail "destination must be an absolute path: $DEST" ;;
esac
case "$DEST" in
  *"/.."|*"/../"*|*"/./"*|*"/.") fail "destination contains . or .. components: $DEST" ;;
esac
HOME_REAL="$(cd "$HOME" && pwd -P)"
if [ "$DEST" = "/" ] || [ "$DEST" = "$HOME" ] || [ "$DEST" = "$HOME_REAL" ]; then
  fail "refusing destination $DEST"
fi
case "$DEST/" in
  "$REPO/"*) fail "destination is the repository or inside it: $DEST" ;;
esac
case "$REPO/" in
  "$DEST/"*) fail "destination contains the repository: $DEST" ;;
esac

# Destination must live on an external volume: /Volumes/<name>/<subfolder>.
case "$DEST" in
  /Volumes/*/*) ;;
  *) fail "destination must be inside /Volumes/<volume>/...: $DEST" ;;
esac
VOLUME="/Volumes/$(echo "${DEST#/Volumes/}" | cut -d/ -f1)"

# Not mounted: nothing to do, not an error, never create anything.
if ! mount | grep -q " on $VOLUME ("; then
  say "backup_to_volume: $VOLUME not mounted; nothing done"
  log "SKIP $VOLUME not mounted"
  exit 0
fi

# --- lock --------------------------------------------------------------------
if [ "$DRY" -eq 0 ]; then
  if ! mkdir "$LOCK" 2>/dev/null; then
    OLD_PID="$(cat "$LOCK/pid" 2>/dev/null || true)"
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
      say "backup_to_volume: another backup is running (pid $OLD_PID); nothing done"
      exit 0
    fi
    rm -rf "$LOCK"
    mkdir "$LOCK" 2>/dev/null || exit 0
  fi
  echo $$ > "$LOCK/pid"
  trap 'rm -rf "$LOCK"' EXIT
fi

[ -d "$DEST" ] || { [ "$DRY" -eq 1 ] || mkdir -p "$DEST" || fail "cannot create $DEST"; }

RSYNC_OPTS=(-a --delete --itemize-changes
  --exclude=/_site/ --exclude=/.jekyll-cache/ --exclude=/.sass-cache/
  --exclude=node_modules/ --exclude=.DS_Store
  --exclude=/.git/backup_to_volume.lock/)

# Trailing slash on the source: copy the contents of the repo into DEST.
# With --delete, rsync only removes files inside DEST.
count() { # $1 = itemize output
  COPIED="$(printf '%s\n' "$1" | grep -c '^[<>]f' || true)"
  DELETED="$(printf '%s\n' "$1" | grep -c '^\*deleting' || true)"
}

# Dry run first (also the whole job with --dry-run).
if [ -d "$DEST" ]; then
  PLAN="$(rsync "${RSYNC_OPTS[@]}" -n "$REPO/" "$DEST/" 2>&1)" || fail "dry-run failed: $(printf '%s' "$PLAN" | tail -n 3)"
  count "$PLAN"
else
  COPIED="(new destination)"; DELETED=0
fi

if [ "$DRY" -eq 1 ]; then
  say "backup_to_volume (dry-run): $COPIED file(s) to copy, $DELETED to delete -> $DEST"
  [ "$QUIET" -eq 1 ] || printf '%s\n' "${PLAN:-}" | head -n 40
  exit 0
fi

OUT="$(rsync "${RSYNC_OPTS[@]}" "$REPO/" "$DEST/" 2>&1)"
RC=$?
if [ "$RC" -ne 0 ]; then
  fail "rsync exited $RC: $(printf '%s' "$OUT" | tail -n 3)"
fi
count "$OUT"
say "backup_to_volume: OK, $COPIED file(s) copied, $DELETED deleted -> $DEST"
log "OK copied=$COPIED deleted=$DELETED dest=$DEST"
exit 0
