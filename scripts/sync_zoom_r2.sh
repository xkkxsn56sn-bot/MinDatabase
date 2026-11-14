#!/bin/bash
# Sincronizza gli zoom ad alta risoluzione con R2 e aggiorna il manifest.
#
# Gli zoom non stanno nel repository: vivono in locale in Zoom/Images/<Cartella>/
# (cartella ignorata da git, copiata dal backup su Prog) e su R2, nel bucket
# mindatabase-zoom, pubblicato come https://zoom.medievalvisions.com. Il
# repository tiene solo assets/data/zoom-manifest.json: percorso, dimensioni in
# pixel, byte e sha256 di ogni zoom caricato. Il controllo 9b e la verifica in
# CI leggono il manifest.
#
# Uso:
#   scripts/sync_zoom_r2.sh             prova (default): dice cosa farebbe
#   scripts/sync_zoom_r2.sh --apply     carica i file nuovi o cambiati, aggiorna
#                                       il manifest, poi copia in ~/Desktop/Zoom
#   scripts/sync_zoom_r2.sh --apply --delete
#                                       cancella anche da R2 (e dal manifest) gli
#                                       zoom che non esistono piu' in Zoom/Images
#
# Senza --delete nulla viene mai cancellato: uno zoom presente nel manifest ma
# mancante in locale e' solo segnalato. Il caricamento usa `npx wrangler@4 r2
# object put --remote` con la sessione di `wrangler login`: nessun token nel
# repository. Ogni oggetto ha Content-Type image/jpeg e Cache-Control
# "public, max-age=31536000, immutable"; per questo uno zoom cambiato andrebbe
# rinominato, perche' le cache lo terrebbero per un anno.
#
# Procedura per un nuovo lotto di zoom: il file va in Zoom/Images/<Cartella>/
# <slug>-NN-zoom.jpg, si lancia questo script prima in prova e poi con --apply,
# e nel commit vanno solo il data-zoom-src della scheda e il manifest.

set -uo pipefail

APPLY=0
DELETE=0
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --delete) DELETE=1 ;;
    -h|--help) sed -n '2,28p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done
if [ "$DELETE" -eq 1 ] && [ "$APPLY" -eq 0 ]; then
  echo "--delete has effect only together with --apply; running as a dry run." >&2
fi

REPO="$(cd "$(dirname "$0")/.." && pwd -P)"
export REPO APPLY DELETE

python3 -I - <<'PY'
import hashlib, json, os, struct, subprocess, sys
from pathlib import Path

REPO = Path(os.environ["REPO"])
APPLY = os.environ["APPLY"] == "1"
DELETE = os.environ["DELETE"] == "1" and APPLY
BUCKET = "mindatabase-zoom"
ZOOM_BASE = "https://zoom.medievalvisions.com"
LOCAL_ROOT = REPO / "Zoom"
MANIFEST = REPO / "assets" / "data" / "zoom-manifest.json"
CACHE = "public, max-age=31536000, immutable"


def jpeg_size(data: bytes):
    """(width, height) dal primo segmento SOF di un JPEG, senza dipendenze."""
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        length = struct.unpack(">H", data[i + 2:i + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height, width = struct.unpack(">HH", data[i + 5:i + 9])
            return width, height
        i += 2 + length
    return None, None


def local_inventory():
    out = {}
    for f in sorted((LOCAL_ROOT / "Images").rglob("*-zoom.jpg")):
        rel = f.relative_to(LOCAL_ROOT).as_posix()
        data = f.read_bytes()
        width, height = jpeg_size(data)
        out[rel] = {"path": rel, "width": width, "height": height,
                    "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return out


def load_manifest():
    if not MANIFEST.exists():
        return {}
    return {e["path"]: e for e in json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]}


def write_manifest(entries):
    payload = {
        "zoom_base": ZOOM_BASE,
        "bucket": BUCKET,
        "files": [entries[k] for k in sorted(entries)],
    }
    MANIFEST.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def wrangler(*args):
    cmd = ["npx", "--yes", "wrangler@4", "r2", "object", *args, "--remote"]
    res = subprocess.run(cmd, cwd="/tmp", capture_output=True, text=True)
    return res.returncode, (res.stdout + res.stderr)[-400:]


if not (LOCAL_ROOT / "Images").is_dir():
    sys.exit(f"Missing {LOCAL_ROOT}/Images: nothing to sync.")

local = local_inventory()
manifest = load_manifest()
new = [p for p in local if p not in manifest]
changed = [p for p in local if p in manifest and manifest[p]["sha256"] != local[p]["sha256"]]
gone = [p for p in manifest if p not in local]
tag = "" if APPLY else "[dry-run] "

print(f"{tag}local zoom files: {len(local)}; manifest: {len(manifest)}")
print(f"{tag}new: {len(new)}, changed: {len(changed)}, missing locally: {len(gone)}")
for p in new:
    print(f"{tag}  + {p}")
for p in changed:
    print(f"{tag}  ~ {p}  (cached for a year: renaming is safer than overwriting)")
for p in gone:
    print(f"{tag}  ! {p}  missing in Zoom/" + ("  -> will be deleted from R2" if DELETE else "  (kept; use --apply --delete to remove)"))

if not APPLY:
    sys.exit(0)

errors = 0
for p in new + changed:
    rc, out = wrangler("put", f"{BUCKET}/{p}", "--file", str(LOCAL_ROOT / p),
                       "--content-type", "image/jpeg", "--cache-control", CACHE)
    if rc == 0:
        manifest[p] = local[p]
        print(f"uploaded {p}")
    else:
        errors += 1
        print(f"ERROR uploading {p}: {out.strip().splitlines()[-1] if out.strip() else rc}")
    write_manifest(manifest)

if DELETE:
    for p in gone:
        rc, out = wrangler("delete", f"{BUCKET}/{p}")
        if rc == 0:
            manifest.pop(p, None)
            print(f"deleted {p}")
        else:
            errors += 1
            print(f"ERROR deleting {p}: {out.strip().splitlines()[-1] if out.strip() else rc}")
        write_manifest(manifest)

if not MANIFEST.exists():
    write_manifest(manifest)
print(f"manifest: {len(manifest)} entries -> {MANIFEST.relative_to(REPO)}; errors: {errors}")
sys.exit(1 if errors else 0)
PY
RC=$?

# La copia in ~/Desktop/Zoom parte dopo la sincronizzazione, non dopo il commit.
if [ "$APPLY" -eq 1 ] && [ "$RC" -eq 0 ]; then
  "$REPO/scripts/copy_zoom_to_desktop.sh" || true
fi
exit "$RC"
