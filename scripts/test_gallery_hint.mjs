// Test della galleria: il lightbox e l'invito al click.
//
// A differenza di test_update_push_notices.py, che gira senza dipendenze,
// questo carica gallery.html in un DOM vero e ha bisogno di jsdom:
//
//   npm install && node scripts/test_gallery_hint.mjs
//
// Non gira in CI - nessun workflow monta Node - ed e' pensato per la
// verifica locale prima di toccare la galleria.

import { JSDOM } from "jsdom";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const html = fs.readFileSync(ROOT + "/gallery.html", "utf8");
const index = JSON.parse(
  fs.readFileSync(ROOT + "/assets/data/gallery-index.json", "utf8")
);
let pass = 0,
  fail = 0;
const ok = (c, m) => {
  c
    ? (pass++, console.log("  ok   " + m))
    : (fail++, console.log("  FAIL " + m));
};
const dom = new JSDOM(html, {
  runScripts: "dangerously",
  pretendToBeVisual: true,
  url: "http://localhost/gallery.html",
  beforeParse(w) {
    w.fetch = () =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(index),
      });
    w.Image = class {
      set src(v) {
        this._s = v;
      }
      get src() {
        return this._s;
      }
    };
  },
});
const { window } = dom,
  d = window.document;
await new Promise((r) => window.addEventListener("load", r));
await new Promise((r) => setTimeout(r, 300));

console.log("\n1. L'ETICHETTA");
const zooms = [...d.querySelectorAll(".gallery-item__zoom")];
const hints = [...d.querySelectorAll(".gallery-item__hint")];
ok(
  hints.length === zooms.length,
  `un'etichetta per card: ${hints.length} su ${zooms.length}`
);
ok(
  hints.every((h) => h.textContent === "Click to view full image"),
  "testo «Click to view full image»"
);
ok(
  hints.every((h) => h.getAttribute("aria-hidden") === "true"),
  "aria-hidden su tutte"
);
ok(
  hints.every((h) => h.parentElement.classList.contains("gallery-item__zoom")),
  "dentro il button, quindi dentro gallery-item__frame"
);
ok(
  hints.every((h) => h.previousElementSibling?.tagName === "IMG"),
  "dopo la <img>, sopra di essa nello stacking"
);

console.log("\n2. IL NOME ACCESSIBILE");
const withAlt = zooms.filter(
  (z) =>
    z.getAttribute("aria-label") ===
    "View full image: " + z.querySelector("img").alt
);
ok(
  withAlt.length === zooms.length,
  `aria-label = "View full image: <alt>" su tutte e ${zooms.length}`
);
ok(
  !zooms.some((z) => z.getAttribute("aria-label") === "See the whole image"),
  "il vecchio label generico non c'e' piu'"
);
const distinct = new Set(zooms.map((z) => z.getAttribute("aria-label")));
ok(
  distinct.size > zooms.length * 0.5,
  `${distinct.size} nomi distinti su ${zooms.length}: le card si distinguono da lettore di schermo`
);
console.log("     es. " + JSON.stringify(zooms[0].getAttribute("aria-label")));
ok(
  hints.every((h) => !h.hasAttribute("role")),
  "l'etichetta non introduce ruoli"
);

console.log("\n3. IL CSS SERVITO");
const css = html.match(/<style>([\s\S]*?)<\/style>/)[1];
const hintCss = css.match(/\.gallery-item__hint \{[^}]+\}/)[0];
ok(
  /opacity: 0;/.test(hintCss),
  "a riposo opacity: 0 — invisibile finche' non serve"
);
ok(
  /pointer-events: none;/.test(hintCss),
  "pointer-events: none — non puo' intercettare il click"
);
ok(/transition: opacity 0\.15s/.test(hintCss), "dissolvenza 150ms");
ok(
  /rgba\(20, 16, 10/.test(hintCss),
  "nero caldo rgba(20,16,10,…), lo stesso del lightbox"
);
ok(/linear-gradient\(\s*to top/.test(hintCss), "gradiente dal basso");
ok(
  /@media \(hover: hover\) \{\s*\.gallery-item__zoom:hover \.gallery-item__hint/.test(
    css
  ),
  "l'hover e' dietro @media (hover: hover): su touch non compare mai"
);
ok(
  /\.gallery-item__zoom:focus-visible \.gallery-item__hint \{\s*opacity: 1;/.test(
    css
  ),
  "compare anche su :focus-visible del button (tastiera)"
);
// Il rientro distingue top-level (6 spazi) da dentro-blocco (8): la regola
// tastiera deve stare fuori dalla media query, o su touch il focus da
// tastiera esterna non mostrerebbe nulla.
ok(
  /\n {6}\.gallery-item__zoom:focus-visible \.gallery-item__hint \{/.test(css),
  "la regola tastiera e' al livello esterno, fuori da @media (hover: hover)"
);
ok(
  /\n {8}\.gallery-item__zoom:hover \.gallery-item__hint \{/.test(css),
  "la regola hover e' rientrata, dentro la media query"
);
ok(
  /@media \(prefers-reduced-motion: reduce\) \{\s*\.gallery-item__hint \{\s*transition: none;/.test(
    css
  ),
  "prefers-reduced-motion rispettato"
);
ok(
  /\.gallery-item__zoom \{\s*position: relative;/.test(css),
  "il button e' position: relative, l'etichetta ci si ancora"
);
ok(
  /\.gallery-item__frame \{[^}]*overflow: hidden/.test(css),
  "la cornice ha overflow: hidden, il gradiente non deborda"
);

console.log("\n4. QUANTO COPRE  (limite: un quarto della cornice)");
const REM = 16,
  PT = 1.1 * REM,
  PB = 0.45 * REM,
  LINE = 0.76 * REM * 1.3;
const H = PT + LINE + PB;
console.log(
  `     altezza etichetta = ${PT.toFixed(1)} + ${LINE.toFixed(1)} + ${PB.toFixed(1)} = ${H.toFixed(1)}px`
);
let worst = 0;
for (const [name, vw] of [
  ["desktop 1440", 1440],
  ["laptop 1024", 1024],
  ["tablet 768", 768],
  ["iPhone 390", 390],
  ["iPhone SE 375", 375],
  ["Galaxy Fold 320", 320],
]) {
  const small = vw <= 600;
  const pad = small ? 1 * REM : 2 * REM,
    gap = small ? 1 * REM : 1.5 * REM,
    min = small ? 220 : 260;
  const content = Math.min(vw, 1440) - 2 * pad;
  let n = Math.max(1, Math.floor((content + gap) / (min + gap)));
  const col = (content - (n - 1) * gap) / n;
  const frame = col * 0.75;
  const pct = (H / frame) * 100;
  worst = Math.max(worst, pct);
  console.log(
    `     ${name.padEnd(16)} ${n} colonne x ${Math.round(col)}px -> cornice ${Math.round(frame)}px, etichetta ${pct.toFixed(0)}%`
  );
}
ok(worst <= 25, `il caso peggiore copre il ${worst.toFixed(0)}% (<= 25%)`);

console.log("\n5. NESSUNA REGRESSIONE SUL LIGHTBOX");
const click = (el) =>
  el.dispatchEvent(
    new window.MouseEvent("click", { bubbles: true, cancelable: true })
  );
const lb = d.getElementById("gallery-lightbox");
click(zooms[0]);
ok(!lb.hidden, "il click apre ancora il lightbox");
ok(
  d.getElementById("gallery-lightbox-img").getAttribute("src") ===
    zooms[0].querySelector("img").getAttribute("src"),
  "mostra l'immagine giusta"
);
// il click atterra sull'etichetta: deve comunque aprire (bolla al button)
d.getElementById("gallery-lightbox-close").dispatchEvent(
  new window.MouseEvent("click", { bubbles: true, cancelable: true })
);
click(hints[3]);
ok(
  !lb.hidden,
  "un click che atterra sull'etichetta apre lo stesso: bolla al button"
);
console.log(`\n=== ${pass} passati, ${fail} falliti ===`);
process.exit(fail ? 1 : 0);
