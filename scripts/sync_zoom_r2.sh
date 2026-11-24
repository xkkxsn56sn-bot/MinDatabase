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
#   scripts/sync_zoom_r2.sh --only Images/<Cartella>/<file> [--apply]
#                                       limita tutto a quel file (ripetibile): gli
#                                       altri zoom locali non vengono toccati, ne'
#                                       caricati ne' segnalati. Serve quando in
#                                       Zoom/Images ci sono lotti non ancora
#                                       pubblicati.
#
# Nomi: <slug>-NN-zoom.jpg, oppure <slug>-NN-zoom-vN.jpg (N >= 2) per uno zoom
# che ne sostituisce uno gia' caricato. La vecchia versione non si cancella: si
# sposta in Zoom/Retired/Images/<Cartella>/ (fuori da Zoom/Images, quindi lo
# script non la vede piu'), se ne toglie la voce dal manifest e su R2 resta.
#
# Senza --delete nulla viene mai cancellato: uno zoom presente nel manifest ma
# mancante in locale e' solo segnalato. Il caricamento usa `wrangler r2 object
# put --remote` con la sessione di `wrangler login`: nessun token nel
# repository. Wrangler e' una devDependency a versione fissa (package.json e
# package-lock.json, `npm install` o `npm ci`): lo script usa
# node_modules/.bin/wrangler e, se manca, ripiega su `npx --yes wrangler@4`.
# I file nuovi o cambiati si caricano in parallelo, al massimo quattro alla
# volta (MAX_UPLOADS); ogni file ha la sua riga di esito, e il manifest prende
# solo i caricamenti riusciti. Ogni oggetto ha Content-Type image/jpeg e Cache-Control
# "public, max-age=31536000, immutable"; per questo uno zoom cambiato andrebbe
# rinominato, perche' le cache lo terrebbero per un anno.
#
# Procedura per un nuovo lotto di zoom: il file va in Zoom/Images/<Cartella>/
# <slug>-NN-zoom.jpg, si lancia questo script prima in prova e poi con --apply,
# e nel commit vanno solo il data-zoom-src della scheda e il manifest.

set -uo pipefail

APPLY=0
DELETE=0
ONLY=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --delete) DELETE=1 ;;
    --only)
      [ "$#" -ge 2 ] || { echo "--only needs a path (Images/<Cartella>/<file>)" >&2; exit 2; }
      ONLY="${ONLY}${2#Zoom/}"$'\n'; shift ;;
    -h|--help) sed -n '2,46p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
if [ "$DELETE" -eq 1 ] && [ "$APPLY" -eq 0 ]; then
  echo "--delete has effect only together with --apply; running as a dry run." >&2
fi

REPO="$(cd "$(dirname "$0")/.." && pwd -P)"
export REPO APPLY DELETE ONLY

python3 -I - <<'PY'
import concurrent.futures, hashlib, json, os, re, struct, subprocess, sys
from pathlib import Path

REPO = Path(os.environ["REPO"])
APPLY = os.environ["APPLY"] == "1"
DELETE = os.environ["DELETE"] == "1" and APPLY
BUCKET = "mindatabase-zoom"
ZOOM_BASE = "https://zoom.medievalvisions.com"
LOCAL_ROOT = REPO / "Zoom"
MANIFEST = REPO / "assets" / "data" / "zoom-manifest.json"
CACHE = "public, max-age=31536000, immutable"
MAX_UPLOADS = 4  # caricamenti contemporanei
LOCAL_WRANGLER = REPO / "node_modules" / ".bin" / "wrangler"
# La convenzione dei nomi e' quella del controllo 9b, importata dal validatore
# (non ricopiata): <slug>-NN-zoom.jpg o ...-zoom-vN.jpg (N >= 2); per i codici al
# posto di NN il foglio o l'etichetta del check 12 (f001v, p012, cover-front...).
sys.path.insert(0, str(REPO / "scripts"))
from validate_content_indexes import ZOOM_NAME_RE as ZOOM_FILE_RE  # noqa: E402
ONLY = {p.strip().lstrip("/") for p in os.environ.get("ONLY", "").splitlines() if p.strip()}


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
    for f in sorted((LOCAL_ROOT / "Images").rglob("*.jpg")):
        rel = f.relative_to(LOCAL_ROOT).as_posix()
        if not ZOOM_FILE_RE.match(f.name):
            continue
        if ONLY and rel not in ONLY:
            continue
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


def wrangler_cmd():
    """Wrangler fissato in node_modules; se manca, npx come prima."""
    if os.access(LOCAL_WRANGLER, os.X_OK):
        return [str(LOCAL_WRANGLER)]
    return ["npx", "--yes", "wrangler@4"]


def wrangler(*args):
    # cwd fuori dal repository: il wrangler.toml della radice e' di un altro Worker.
    cmd = [*wrangler_cmd(), "r2", "object", *args, "--remote"]
    res = subprocess.run(cmd, cwd="/tmp", capture_output=True, text=True)
    return res.returncode, (res.stdout + res.stderr)[-400:]


def last_line(out, rc):
    return out.strip().splitlines()[-1] if out.strip() else rc


if not (LOCAL_ROOT / "Images").is_dir():
    sys.exit(f"Missing {LOCAL_ROOT}/Images: nothing to sync.")

local = local_inventory()
manifest = load_manifest()
new = [p for p in local if p not in manifest]
changed = [p for p in local if p in manifest and manifest[p]["sha256"] != local[p]["sha256"]]
gone = [p for p in manifest if p not in local and (not ONLY or p in ONLY)]
missing_only = sorted(ONLY - set(local) - set(manifest))
tag = "" if APPLY else "[dry-run] "
if ONLY:
    print(f"{tag}--only: limited to {len(ONLY)} path(s)")
for p in missing_only:
    print(f"{tag}  ? {p}  not found in Zoom/ nor in the manifest")

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
uploads = new + changed
if uploads:
    via = "node_modules/.bin/wrangler" if wrangler_cmd()[0] == str(LOCAL_WRANGLER) else "npx wrangler@4"
    print(f"uploading {len(uploads)} file(s) with {via}, up to {MAX_UPLOADS} at a time")


def put(p):
    return wrangler("put", f"{BUCKET}/{p}", "--file", str(LOCAL_ROOT / p),
                    "--content-type", "image/jpeg", "--cache-control", CACHE)


# I caricamenti girano nei thread; manifest e stampa restano nel thread
# principale, un file alla volta, man mano che i caricamenti finiscono.
with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_UPLOADS) as pool:
    futures = {pool.submit(put, p): p for p in uploads}
    for fut in concurrent.futures.as_completed(futures):
        p = futures[fut]
        try:
            rc, out = fut.result()
        except Exception as exc:  # wrangler/npx mancante o altro errore locale
            rc, out = 1, f"{type(exc).__name__}: {exc}"
        if rc == 0:
            manifest[p] = local[p]
            print(f"uploaded {p}", flush=True)
        else:
            errors += 1
            print(f"ERROR uploading {p}: {last_line(out, rc)}", flush=True)
        write_manifest(manifest)

if DELETE:
    for p in gone:
        rc, out = wrangler("delete", f"{BUCKET}/{p}")
        if rc == 0:
            manifest.pop(p, None)
            print(f"deleted {p}")
        else:
            errors += 1
            print(f"ERROR deleting {p}: {last_line(out, rc)}")
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
