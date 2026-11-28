#!/usr/bin/env python3
"""
build_entry_pdf.py

Produce il PDF di una scheda, con lo stesso contenuto della pagina.

USO
    .venv/bin/python scripts/build_entry_pdf.py Content/Churches/Modena-Cathedral.md

COSA FA
    1. Build Jekyll locale in una cartella temporanea (non tocca _site).
    2. Serve la build su localhost e apre la pagina con Playwright, sul
       Google Chrome installato (channel "chrome": nessun browser scaricato).
    3. Stampa con il CSS @media print di assets/css/entry.css: una colonna,
       intestazione, blocchi della sidebar e studiosi, saggio e catalogo con
       didascalie e crediti, bibliografia, nota sui diritti. Restano fuori i
       comandi dell'interfaccia (menu, navigazione, audio, tema, pulsante PDF,
       iscrizione) e l'indice laterale.
    4. Toglie le figure con data-no-download o con «©» nella didascalia: al
       loro posto non resta nulla. Le immagini sono quelle base (src), mai gli
       zoom (data-zoom-src).
    5. I link relativi diventano assoluti su https://www.medievalvisions.com,
       cosi' nel PDF non puntano a localhost.
    6. A4; nel piede di pagina solo il numero di pagina, a destra.

    Il file va in drafts/pdf/<slug>.pdf. Elenca a fine corsa le figure escluse.
    Non carica niente su R2: il caricamento e' un passo separato.

REQUISITI
    pip install playwright pypdf (nel .venv del repo); Google Chrome.
    Nella shell dell'agente il build Jekyll vuole anche GEM_PATH (vedi la
    memoria sul build locale); LANG/LC_ALL UTF-8 li imposta lo script.
"""

import functools
import http.server
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent.parent
PUBLIC_BASE = "https://www.medievalvisions.com"
OUT_DIR = REPO / "drafts" / "pdf"

# Richieste da non fare durante la stampa: il contatore delle visite e
# l'audio gregoriano.
BLOCKED_HOSTS = ("gc.zgo.at", "goatcounter.com", "/assets/audio/")

PREPARE_JS = r"""
(base) => {
  const excluded = [];
  document.querySelectorAll(".entry__content figure").forEach((fig) => {
    const cap = fig.querySelector("figcaption");
    const capText = cap ? cap.textContent.trim() : "";
    const noDl = fig.hasAttribute("data-no-download");
    const copyright = capText.includes("©");
    if (noDl || copyright) {
      const img = fig.querySelector("img");
      excluded.push({
        src: img ? img.getAttribute("src") : "",
        reason: noDl ? "data-no-download" : "© nella didascalia",
        caption: capText.slice(0, 160),
      });
      fig.remove();
    }
  });
  // Mai gli zoom: l'immagine resta quella base.
  document.querySelectorAll("img[data-zoom-src]").forEach((img) =>
    img.removeAttribute("data-zoom-src"));
  document.querySelectorAll("img").forEach((img) => {
    img.loading = "eager";
    img.removeAttribute("srcset");
  });
  // Link relativi -> assoluti sul sito pubblico.
  document.querySelectorAll("a[href]").forEach((a) => {
    const raw = a.getAttribute("href");
    if (/^(https?:|mailto:|tel:)/i.test(raw)) return;
    if (raw.startsWith("#")) {
      a.setAttribute("href", base + location.pathname + raw);
      return;
    }
    const u = new URL(raw, location.href);
    a.setAttribute("href", base + u.pathname + u.search + u.hash);
  });
  document.documentElement.setAttribute("data-theme", "light");
  return excluded;
}
"""

WAIT_IMAGES_JS = r"""
async () => {
  const imgs = Array.from(document.images).filter(
    (i) => i.getAttribute("src") && i.offsetParent !== null);
  await Promise.all(imgs.map((img) => img.complete ? null :
    new Promise((r) => { img.onload = img.onerror = r; })));
  await document.fonts.ready;
  return imgs.filter((i) => !i.naturalWidth).map((i) => i.src);
}
"""


# Il piede di pagina di Chrome e' un documento a parte che non carica i font
# web (neanche incorporati in base64): si usa Georgia, il primo ripiego del
# CSS del sito.
FOOTER_TEMPLATE = (
    '<div style="width:100%;font-size:8pt;'
    "font-family:Georgia,'Times New Roman',serif;"
    'color:#555;padding:0 18mm;text-align:right;">'
    '<span class="pageNumber"></span>'
    "</div>"
)


def jekyll_build(dest: Path) -> None:
    env = dict(os.environ, LANG="en_US.UTF-8", LC_ALL="en_US.UTF-8")
    cmd = ["bundle", "exec", "jekyll", "build", "-q", "-d", str(dest)]
    print("Build Jekyll...", flush=True)
    subprocess.run(cmd, cwd=REPO, env=env, check=True)


def serve(root: Path):
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(QuietHandler, directory=str(root))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    md = Path(sys.argv[1]).resolve()
    if not md.is_file() or md.suffix != ".md":
        print(f"Non trovo il file .md: {sys.argv[1]}")
        return 2
    rel = md.relative_to(REPO)
    page_path = "/" + rel.with_suffix(".html").as_posix()
    slug = md.stem

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{slug}.pdf"

    with tempfile.TemporaryDirectory(prefix="entry-pdf-") as tmp:
        site = Path(tmp) / "site"
        jekyll_build(site)
        if not (site / page_path.lstrip("/")).is_file():
            print(f"La build non contiene {page_path}")
            return 1
        httpd = serve(site)
        local_url = f"http://127.0.0.1:{httpd.server_address[1]}{page_path}"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel="chrome")
                page = browser.new_page(viewport={"width": 1100, "height": 1400})
                page.route(
                    "**/*",
                    lambda route: route.abort()
                    if any(h in route.request.url for h in BLOCKED_HOSTS)
                    else route.continue_(),
                )
                page.goto(local_url, wait_until="networkidle")
                page.emulate_media(media="print")
                excluded = page.evaluate(PREPARE_JS, PUBLIC_BASE)
                broken = page.evaluate(WAIT_IMAGES_JS)
                page.pdf(
                    path=str(out),
                    format="A4",
                    print_background=True,
                    display_header_footer=True,
                    header_template="<span></span>",
                    footer_template=FOOTER_TEMPLATE,
                    margin={"top": "18mm", "bottom": "20mm",
                            "left": "18mm", "right": "18mm"},
                )
                browser.close()
        finally:
            httpd.shutdown()

    pages = "?"
    try:
        from pypdf import PdfReader

        pages = len(PdfReader(str(out)).pages)
    except ImportError:
        pass
    size_kb = out.stat().st_size / 1024
    print(f"PDF: {out.relative_to(REPO)}")
    print(f"Pagine: {pages}; peso: {size_kb:,.0f} KB ({size_kb / 1024:.1f} MB)")
    if broken:
        print("Immagini non caricate:")
        for s in broken:
            print(f"  {s}")
    if excluded:
        print(f"Figure escluse ({len(excluded)}):")
        for f in excluded:
            print(f"  {f['src']}  [{f['reason']}]")
    else:
        print("Figure escluse: nessuna")
    return 0


if __name__ == "__main__":
    sys.exit(main())
