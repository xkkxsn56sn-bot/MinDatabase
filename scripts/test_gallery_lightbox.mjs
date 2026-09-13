// Test della galleria: il lightbox e l'invito al click.
//
// A differenza di test_update_push_notices.py, che gira senza dipendenze,
// questo carica gallery.html in un DOM vero e ha bisogno di jsdom:
//
//   npm install && node scripts/test_gallery_lightbox.mjs
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
const { window } = dom;

await new Promise((r) => window.addEventListener("load", r));
await new Promise((r) => setTimeout(r, 300));

const d = window.document;
const $ = (s) => d.querySelector(s);
const key = (k, opts = {}) =>
  d.dispatchEvent(
    new window.KeyboardEvent("keydown", {
      key: k,
      bubbles: true,
      cancelable: true,
      ...opts,
    })
  );
const click = (el) =>
  el.dispatchEvent(
    new window.MouseEvent("click", { bubbles: true, cancelable: true })
  );

const lb = $("#gallery-lightbox");
const img = $("#gallery-lightbox-img");
const cards = [...d.querySelectorAll(".gallery-item__zoom")];

console.log("\n--- 1. struttura della card ---");
ok(cards.length > 0, `${cards.length} card renderizzate nel primo batch`);
ok(
  !d.querySelector(".gallery-item__frame a"),
  "nessun <a> residuo attorno all'immagine"
);
ok(
  cards[0].tagName === "BUTTON" && cards[0].type === "button",
  "l'immagine e' in un <button type=button>"
);
ok(cards[0].querySelector("img") !== null, "il <button> contiene la <img>");
ok(
  cards[0].getAttribute("aria-label") ===
    "View full image: " + cards[0].querySelector("img").alt,
  "aria-label della card nomina l'immagine: " +
    JSON.stringify(cards[0].getAttribute("aria-label"))
);
ok(
  cards[0].querySelector(".gallery-item__hint")?.getAttribute("aria-hidden") ===
    "true",
  "l'etichetta visiva non si aggiunge al nome accessibile"
);
ok(
  $(".gallery-group__title a")?.getAttribute("href")?.startsWith("/Content/"),
  "il titolo del gruppo linka ancora la scheda"
);

console.log("\n--- 2. apertura ---");
ok(lb.hidden === true, "overlay chiuso all'avvio");
click(cards[0]);
ok(lb.hidden === false, "click sulla card: overlay aperto");
const first = index.find((f) => f.src === img.getAttribute("src"));
ok(
  !!first,
  "src dell'overlay = src di una voce dell'indice (originale, nessun thumbnail)"
);
ok(
  img.getAttribute("src") === cards[0].querySelector("img").getAttribute("src"),
  "stessa URL della card: nessuna mappa da risolvere"
);
ok(img.alt.length > 0, "alt popolato");
ok($("#gallery-lightbox-text").textContent.length > 0, "didascalia popolata");
ok(
  $("#gallery-lightbox-entry").getAttribute("href").startsWith("/Content/"),
  "link alla scheda presente nel lightbox"
);
ok(
  $("#gallery-lightbox-entry").textContent.includes("→"),
  "il link porta la freccia"
);
ok(
  d.activeElement === $("#gallery-lightbox-close"),
  "focus sul bottone di chiusura all'apertura"
);
ok(
  d.body.style.overflow === "hidden" &&
    d.documentElement.style.overflow === "hidden",
  "scroll di fondo bloccato"
);
ok(
  lb.getAttribute("role") === "dialog" &&
    lb.getAttribute("aria-modal") === "true",
  "role=dialog + aria-modal"
);

console.log("\n--- 3. conteggio e ordine = set filtrato intero ---");
const total = index.length;
ok(
  $("#gallery-lightbox-count").textContent === `1 / ${total}`,
  `contatore 1 / ${total} (tutto il set, non il batch)`
);
ok(
  total > cards.length,
  `il set (${total}) eccede le card renderizzate (${cards.length}): le frecce vanno oltre il batch`
);

console.log("\n--- 4. frecce ---");
key("ArrowRight");
ok(
  $("#gallery-lightbox-count").textContent === `2 / ${total}`,
  "ArrowRight avanza"
);
key("ArrowLeft");
ok(
  $("#gallery-lightbox-count").textContent === `1 / ${total}`,
  "ArrowLeft indietreggia"
);
key("ArrowLeft");
ok(
  $("#gallery-lightbox-count").textContent === `${total} / ${total}`,
  "wrap all'indietro dall'inizio all'ultima"
);
key("ArrowRight");
ok(
  $("#gallery-lightbox-count").textContent === `1 / ${total}`,
  "wrap in avanti dall'ultima alla prima"
);
click($("#gallery-lightbox-next"));
ok(
  $("#gallery-lightbox-count").textContent === `2 / ${total}`,
  "bottone > funziona (tap, non hover)"
);
click($("#gallery-lightbox-prev"));
ok(
  $("#gallery-lightbox-count").textContent === `1 / ${total}`,
  "bottone < funziona"
);

console.log("\n--- 5. ordine di scorrimento = ordine della pagina ---");
const domOrder = cards.map((c) => c.querySelector("img").getAttribute("src"));
let seqOk = true;
for (let i = 0; i < Math.min(30, domOrder.length); i++) {
  const c = d.querySelector(`[data-gallery-index="${i}"]`);
  if (!c || c.querySelector("img").getAttribute("src") !== domOrder[i]) {
    seqOk = false;
    break;
  }
}
ok(seqOk, "data-gallery-index segue l'ordine visivo della pagina");

console.log("\n--- 6. chiusura ---");
key("Escape");
ok(lb.hidden === true, "Esc chiude");
ok(
  d.body.style.overflow === "" && d.documentElement.style.overflow === "",
  "scroll ripristinato"
);
ok(d.activeElement === cards[0], "focus tornato alla card di partenza");

click(cards[2]);
ok(lb.hidden === false, "riapertura da un'altra card");
click($("#gallery-lightbox-close"));
ok(lb.hidden === true, "bottone x chiude");
ok(d.activeElement === cards[2], "focus tornato alla card giusta");

click(cards[1]);
click(lb);
ok(lb.hidden === true, "click sul fondo chiude (= tap fuori da telefono)");

click(cards[1]);
click($("#gallery-lightbox-figure"));
ok(lb.hidden === true, "click sul margine del riquadro chiude");

click(cards[1]);
click(img);
ok(lb.hidden === false, "click SULL'IMMAGINE non chiude");
click($("#gallery-lightbox-text"));
ok(lb.hidden === false, "click sulla didascalia non chiude");
key("Escape");

console.log(
  "\n--- 7. focus torna alla card dell'immagine su cui ci si ferma ---"
);
click(cards[0]);
key("ArrowRight");
key("ArrowRight");
key("Escape");
ok(
  d.activeElement === cards[2],
  "aperto su 0, chiuso su 2 -> focus sulla card 2"
);

console.log("\n--- 8. tasti inerti a lightbox chiuso ---");
const before = d.activeElement;
key("ArrowRight");
key("Escape");
ok(
  lb.hidden === true && d.activeElement === before,
  "frecce/Esc non fanno nulla se chiuso"
);

console.log("\n--- 9. i filtri chiudono e riallineano ---");
click(cards[0]);
const sel = $("#gallery-century");
sel.value = "XIV";
sel.dispatchEvent(new window.Event("change", { bubbles: true }));
await new Promise((r) => setTimeout(r, 100));
ok(lb.hidden === true, "cambio filtro chiude l'overlay (gli indici cambiano)");
const n14 = index.filter((f) => f.century === "XIV").length;
const cards14 = [...d.querySelectorAll(".gallery-item__zoom")];
click(cards14[0]);
ok(
  $("#gallery-lightbox-count").textContent === `1 / ${n14}`,
  `dentro il filtro Century=XIV il set e' ${n14}, non ${total}`
);
const all14 = new Set(
  index.filter((f) => f.century === "XIV").map((f) => f.src)
);
let stayed = true;
for (let i = 0; i < 40; i++) {
  key("ArrowRight");
  if (!all14.has(img.getAttribute("src"))) {
    stayed = false;
    break;
  }
}
ok(stayed, "40 passi di freccia restano dentro il filtro attivo");
key("Escape");

console.log(
  "\n--- 10. verticali estreme e orizzontali larghe presenti nel set ---"
);
ok(
  index.some((f) => f.src.includes("maestro-santa-caterina-gualino-06")),
  "la verticale peggiore (211x800) e' nell'indice"
);
ok(
  index.some((f) => f.src.includes("luca-di-tomme-16")),
  "l'orizzontale peggiore (800x124) e' nell'indice"
);

console.log(`\n=== ${pass} passati, ${fail} falliti ===`);
process.exit(fail ? 1 : 0);
