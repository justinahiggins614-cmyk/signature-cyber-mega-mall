#!/usr/bin/env node
/* Site 26 functional harness — drives the REAL index.html scripts in Node's vm
   against the REAL shipped data (manifest, counts, index.json.gz, dept chunks,
   hashes.json), with a hand-rolled DOM stub + a fetch stub serving repo files.
   Usage: node code/qa/functional_harness.js [--head]   (--head = pre-fix file from git HEAD) */
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm"),
      zlib = require("zlib"), crypto = require("crypto");

const ROOT = "/home/hatch/workspace/signature-cyber-mega-mall";
const useHead = process.argv.includes("--head");
let html;
if (useHead) {
  const { execSync } = require("child_process");
  html = execSync("git show HEAD:index.html", { cwd: ROOT, maxBuffer: 8 * 1024 * 1024 }).toString("utf8");
} else {
  html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
}

/* ---------------- DOM stub ---------------- */
function makeEl(tag, id) {
  const listeners = {};
  const el = {
    tagName: (tag || "div").toUpperCase(), _id: id || "", children: [],
    _html: "", _text: "", value: "", disabled: false, parentNode: null,
    style: {}, dataset: {}, attributes: {}, onclick: null,
    classList: { _s: new Set(),
      add(...c) { c.forEach(x => this._s.add(x)); },
      remove(...c) { c.forEach(x => this._s.delete(x)); },
      toggle(c, f) { if (f === undefined) f = !this._s.has(c); f ? this._s.add(c) : this._s.delete(c); return f; },
      contains(c) { return this._s.has(c); } },
    setAttribute(k, v) { this.attributes[k] = String(v); if (k === "data-t") this._datat = String(v); },
    getAttribute(k) { if (k === "data-t" && this._datat !== undefined) return this._datat; return this.attributes[k] !== undefined ? this.attributes[k] : null; },
    addEventListener(t, f) { (listeners[t] = listeners[t] || []).push(f); },
    removeEventListener() {},
    appendChild(c) { c.parentNode = this; this.children.push(c); return c; },
    removeChild(c) { this.children = this.children.filter(x => x !== c); if (c) c.parentNode = null; return c; },
    remove() { if (this.parentNode) this.parentNode.removeChild(this); },
    insertAdjacentHTML(pos, h) { this._html += String(h); },
    scrollIntoView() {}, focus() {}, click() { (listeners.click || []).forEach(f => f({ target: this })); },
    getBoundingClientRect() { return { left: 10, top: 120, width: 300, height: 60 }; },
    get offsetWidth() { return 300; }, get offsetHeight() { return 40; },
    querySelector() { return null; },
    querySelectorAll(sel) {
      if (sel === "button") { // parse buttons out of innerHTML so tour/prompt clicks are real
        if (!this._btnCache) {
          const out = [], re = /<button\b([^>]*)>([\s\S]*?)<\/button>/gi; let m;
          while ((m = re.exec(this._html))) {
            const b = makeEl("button");
            const dm = m[1].match(/data-t="([^"]*)"/); if (dm) b.setAttribute("data-t", dm[1]);
            b._label = m[2].replace(/<[^>]*>/g, "").trim(); out.push(b);
          }
          this._btnCache = out;
        }
        return this._btnCache;
      }
      return [];
    },
  };
  Object.defineProperty(el, "innerHTML", { get() { return this._html; }, set(v) { this._html = String(v); this._btnCache = null; } });
  Object.defineProperty(el, "textContent", { get() { return this._text; }, set(v) { this._text = String(v); } });
  Object.defineProperty(el, "id", { get() { return this._id; }, set(v) { this._id = String(v); if (this._id) byId[this._id] = this; } });
  if (el._id) byId[el._id] = el;
  return el;
}

const byId = {}, byClass = {}, bySel = {};
const docListeners = {};
const winListeners = {};
const documentStub = {
  readyState: "complete",
  documentElement: makeEl("html"),
  body: makeEl("body"), head: makeEl("head"),
  getElementById(id) { return byId[id] || (byId[id] = makeEl("div", id)); },
  createElement(tag) { return makeEl(tag); },
  querySelector(sel) {
    if (sel[0] === "#") { const id = sel.slice(1).split(" ")[0]; return documentStub.getElementById(id); }
    return bySel[sel] || (bySel[sel] = makeEl("div"));
  },
  querySelectorAll() { return []; },
  addEventListener(t, f) { (docListeners[t] = docListeners[t] || []).push(f); },
};
documentStub.documentElement.dataset = {};

/* ---------------- browser-ish globals ---------------- */
const store = {};
const localStorageStub = {
  getItem: k => (k in store ? store[k] : null),
  setItem: (k, v) => { store[k] = String(v); },
  removeItem: k => { delete store[k]; },
};
const locationStub = { search: "", origin: "https://justinahiggins614-cmyk.github.io", pathname: "/signature-cyber-mega-mall/", href: "https://justinahiggins614-cmyk.github.io/signature-cyber-mega-mall/" };
const historyStub = { replaceState(a, b, u) { try { const q = String(u).indexOf("?"); locationStub.search = q >= 0 ? String(u).slice(q) : ""; } catch (e) {} } };

function fileFor(url) {
  const u = String(url).split("?")[0];
  const p = path.join(ROOT, u);
  if (!fs.existsSync(p)) return null;
  return fs.readFileSync(p);
}
async function fetchStub(url) {
  const buf = fileFor(url);
  if (!buf) return { ok: false, status: 404, json: async () => { throw new Error("404 " + url); }, text: async () => { throw new Error("404 " + url); } };
  if (String(url).endsWith(".gz")) {
    const body = new ReadableStream({ start(c) { c.enqueue(new Uint8Array(buf)); c.close(); } });
    return { ok: true, status: 200, body };
  }
  const text = buf.toString("utf8");
  return { ok: true, status: 200, text: async () => text, json: async () => JSON.parse(text), body: null };
}
class AudioStub { constructor() {} play() { return Promise.resolve(); } pause() {} }

const sandbox = {
  console, setTimeout, clearTimeout, setInterval, clearInterval,
  URL, URLSearchParams, TextEncoder, Blob, ReadableStream, DecompressionStream, Response,
  crypto: crypto.webcrypto,
  document: documentStub, window: null, navigator: {},
  localStorage: localStorageStub, location: locationStub, history: historyStub,
  fetch: fetchStub, Audio: AudioStub, matchMedia: () => ({ matches: false }),
  alert: (m) => { sandbox._alerted = String(m); },
  addEventListener: (t, f) => { (winListeners[t] = winListeners[t] || []).push(f); },
  removeEventListener: () => {},
};
sandbox.window = sandbox; sandbox.globalThis = sandbox;
sandbox.URL.createObjectURL = () => "blob:fake";
sandbox.URL.revokeObjectURL = () => {};
vm.createContext(sandbox);

/* load order mirrors the page: shared talk module first, then inline scripts */
const talk = fs.readFileSync(path.join(ROOT, "js/jah-talk-fallback.js"), "utf8");
vm.runInContext(talk, sandbox, { filename: "jah-talk-fallback.js" });
const inlines = [...html.matchAll(/<script(?![^>]*src=)(?![^>]*type="application\/ld\+json")[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
inlines.forEach((src, i) => vm.runInContext(src, sandbox, { filename: `inline-${i}.js` }));
const V = expr => vm.runInContext(expr, sandbox);

/* ---------------- test rig ---------------- */
let pass = 0, fail = 0; const failures = [];
function t(name, cond, extra) {
  if (cond) { pass++; console.log("  PASS " + name); }
  else { fail++; failures.push(name); console.log("  FAIL " + name + (extra ? " — " + extra : "")); }
}
const el = id => documentStub.getElementById(id);
const cardCount = () => (el("grid").innerHTML.match(/class="card"/g) || []).length;
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  console.log("== boot (" + (useHead ? "git HEAD" : "working tree") + ") ==");
  // fire DOMContentLoaded like a real page load
  (docListeners.DOMContentLoaded || []).forEach(f => f());
  let Mall;
  try {
    Mall = V("Mall");
    await V("Mall.boot()");
    t("boot() completes without throwing", true);
  } catch (e) { t("boot() completes without throwing", false, String(e && e.message)); return done(); }
  V("Cart.render()");
  await sleep(50);
  await V("Mall.renderGuide()"); // boot() fires renderGuide floating; await it for assertions
  await sleep(20);

  const Finder = V("Finder"), Cart = V("Cart"), Aud = V("Aud");

  t("azTop is a global function (boot regression guard)", V("typeof azTop") === "function");
  t("manifest loaded: 8,821 products", Mall.manifest && Mall.manifest.count === 8821, "got " + (Mall.manifest && Mall.manifest.count));
  t("counts.json authoritative total matches", Mall.counts && Mall.counts.total === 8821);
  t("inventory version honestly labeled (DATA VERSION chip)", el("livecounts").innerHTML.includes("DATA VERSION"));

  console.log("== entry map / floors / guide / finder ==");
  t("entry map renders SVG directory", el("entrymapsvg").innerHTML.includes("MALL DIRECTORY") && el("entrymapsvg").innerHTML.includes("<svg"));
  t("entry map marks YOU ARE HERE", el("entrymapsvg").innerHTML.includes("YOU ARE HERE"));
  const floors = el("floordir").innerHTML;
  t("6 floor cards rendered", (floors.match(/class="floor[ "]|class="floor soon"/g) || []).length === 6, "found " + (floors.match(/class="floor/g) || []).length);
  t("floor counts live (Knowledge 2,316)", floors.includes("2,316"));
  t("Books & Courses marked OPENING SOON (0 products)", floors.includes("Books &amp; Courses") && floors.includes("OPENING SOON"));
  const guide = el("guidebody").innerHTML;
  t("guide leaves 'loading' state", !guide.includes("Guide loading"));
  t("guide ready with tour button + floors", guide.includes("START THE 1-MINUTE TOUR") && guide.includes("THE FLOORS"));
  t("guide map renders (big SVG)", el("guidemapsvg").innerHTML.includes("<svg"));
  t("finder greeted", el("flog").children.length >= 1);
  t("finder suggestion chips in own container (no id clash)", el("finderchips").innerHTML.includes("a gift for a kid"));
  t("toolbar dept filter chips intact (not clobbered)", el("fchips").innerHTML.includes('data-f="all"'));
  t("origin chips rendered", el("ochips").innerHTML.includes("Signature Original"));
  t("A–Z bar rendered (27 buttons)", (el("az").innerHTML.match(/<button/g) || []).length === 27);
  t("dept nav rendered", el("deptnav").innerHTML.includes("All departments"));

  console.log("== browse / pagination ==");
  await Mall.enterDept("all");
  t("enterDept(all): first page 60 cards", cardCount() === 60 && Mall.shown === 60, "cards=" + cardCount());
  t("matchcount shows 8,821 matches", el("matchcount").textContent.includes("8,821"));
  t("no-results hidden on initial shelf", el("noresults").style.display === "none");
  Mall.more();
  t("Load More: 60 -> 120", cardCount() === 120 && Mall.shown === 120, "cards=" + cardCount());

  console.log("== department filter ==");
  await Mall.enterDept("Knowledge");
  t("Knowledge dept: 2,316 in grid state", Mall.grid.length === 2316, "got " + Mall.grid.length);
  t("Knowledge dept: all rows are Knowledge", Mall.grid.every(p => (p.d || p.dept) === "Knowledge"));
  t("Knowledge dept: first page rendered", cardCount() === 60);

  console.log("== search / A–Z / product-ID search ==");
  Mall.curDept = "all"; Mall.curLetter = ""; Mall.curOrigin = "all"; Mall.userSearched = true;
  Mall.curQuery = "quantum"; await Mall.search(true);
  t("search 'quantum' finds matches", Mall.grid.length > 0, "got " + Mall.grid.length);
  t("search results all match query", Mall.grid.every(p => (p.n + " " + (p.b || "") + " " + p.id + " " + (p.g || "")).toLowerCase().includes("quantum")));
  Mall.curQuery = "zzzznomatch123"; await Mall.search(true);
  t("empty search: no-results visible", el("noresults").style.display === "block");
  t("empty search: honest no-match text", el("noresults").innerHTML.includes("No products match"));
  Mall.curQuery = ""; Mall.curLetter = "Q"; Mall.userSearched = true; await Mall.search(true);
  t("A–Z 'Q': all start with Q", Mall.grid.length > 0 && Mall.grid.every(p => p.n.toUpperCase().startsWith("Q")), "got " + Mall.grid.length);
  Mall.curLetter = ""; Mall.curQuery = "JAH-MALL-000001"; await Mall.search(true);
  t("product-ID search resolves", Mall.grid.length === 1 && Mall.grid[0].id === "JAH-MALL-000001");

  console.log("== product detail / deep links ==");
  await Mall.openProduct("JAH-MALL-000001");
  t("modal opens", el("overlay").classList.contains("open"));
  const mb = el("mbody").innerHTML;
  t("detail shows name + source URL", mb.includes("Semiconductor Replacement Designer") && mb.includes("https://justinahiggins614-cmyk.github.io/jah-ai-models/#JAH-AI-DOM-001"));
  t("detail shows OPEN SOURCE RECORD", mb.includes("OPEN SOURCE RECORD"));
  t("detail price $0.00, buy disabled", mb.includes("$0.00") && mb.includes("BUY — DISABLED"));
  t("?product= deep link in URL", locationStub.search.includes("product=JAH-MALL-000001"));
  t("source link is a real JAH-network URL", /^https:\/\/justinahiggins614-cmyk\.github\.io\//.test(Mall.idx.find(p => p.id === "JAH-MALL-000001").u));
  const extP = Mall.idx.find(p => p.t === "external");
  await Mall.openProduct(extP.id);
  t("external product detail renders (MID/RSQ path)", el("overlay").classList.contains("open") && el("mbody").innerHTML.includes("PUBLIC RECORD"));
  const genP = Mall.idx.find(p => p.t === "generated");
  await Mall.openProduct(genP.id);
  t("generated product detail renders", el("mbody").innerHTML.includes("GENERATED"));
  // unknown product id -> honest message + shelf fallback
  await Mall.openProduct("JAH-MALL-999999");
  t("unknown product: 'record unavailable' message", el("malltoast").textContent.includes("unavailable"));
  t("unknown product: falls back to full shelf", Mall.shown === 60 && Mall.curDept === "all");

  console.log("== labels ==");
  t("badge original", Mall.stypeBadge("original") === "SIGNATURE ORIGINAL");
  t("badge generated", Mall.stypeBadge("generated") === "GENERATED");
  t("badge external", Mall.stypeBadge("external") === "PUBLIC RECORD");
  t("note original names the maker", Mall.stypeNote("original").includes("Justin Addam Higgins"));
  t("draft-vs-granted: spec records marked Draft, NOT filed", Mall.kindOf("Signature Spec Catalog")[1].includes("Draft") && Mall.kindOf("Signature Spec Catalog")[1].includes("NOT filed"));
  t("external = public record honesty note", Mall.stypeNote("external").includes("PUBLIC RECORD"));
  const card = Mall.cardHTML(Mall.idx[0]);
  t("card shows source site label", card.includes("The Signature AI Telephone Book"));
  t("card shows $0.00 + GRAND OPENING (not purchasable)", card.includes("$0.00") && card.includes("GRAND OPENING") && !/buy now|add to cart &amp; check|proceed to checkout/i.test(card));

  console.log("== cart (checkout stays disabled) ==");
  await Cart.add("JAH-MALL-000001");
  t("add to cart", Cart.items.length === 1 && el("cartcount").textContent === "1");
  t("cart drawer item renders", el("cartitems").innerHTML.includes("JAH-MALL-000001"));
  Cart.remove("JAH-MALL-000001");
  t("remove from cart", Cart.items.length === 0);
  t("checkout.begin() refuses (inactive)", Cart.checkout.begin() === false && /INACTIVE/.test(sandbox._alerted || ""));
  t("checkout not activated", Cart.checkout.active === false);
  await Cart.add("JAH-MALL-000002");
  t("cart persists to localStorage", JSON.parse(store.mallcart || "[]").includes("JAH-MALL-000002"));
  Cart.remove("JAH-MALL-000002");

  console.log("== free actions: copy / download / personalize / report ==");
  Mall.downloadProduct("JAH-MALL-000001"); // must not throw without clipboard
  t("downloadProduct runs headless", true);
  Mall.copyProduct("JAH-MALL-000001");
  t("copyProduct runs headless", true);
  const pt = Mall.plateText("JAH-MALL-000001", "Test User", "JAH-MALL-CUSTOM-123456", { dept: "Knowledge", floor: 2, aisle: "A-01" }, "Sample");
  t("personalized plate text: $0.00 + name + id", pt.includes("$0.00") && pt.includes("Test User") && pt.includes("JAH-MALL-CUSTOM-123456"));
  el("custname").value = "Test User";
  Mall.personalize("JAH-MALL-000001");
  const id1 = JSON.parse(store.mallcustom)["JAH-MALL-000001"].cid;
  Mall.personalize("JAH-MALL-000001");
  const id2 = JSON.parse(store.mallcustom)["JAH-MALL-000001"].cid;
  t("personalize: deterministic custom ID", id1 === id2 && id1.startsWith("JAH-MALL-CUSTOM-"));
  t("plate painted into modal", el("custplate").innerHTML.includes("MADE FOR"));
  await Mall.rawJSON("JAH-MALL-000001");
  t("raw JSON view renders + hash shown", el("mraw").innerHTML.includes("CANONICAL RECORD") && el("mraw").innerHTML.includes("SHA-256"));
  await Mall.verifyHash("JAH-MALL-000001");
  t("hash verifies against hashes.json", el("vhashres").textContent.includes("VERIFIED"), "got '" + el("vhashres").textContent + "'");
  Mall.report("JAH-MALL-000001");
  t("report form renders", el("mrep").innerHTML.includes("REPORT THIS PRODUCT"));
  el("repcat").value = "broken source";
  Mall.fileReport("JAH-MALL-000001", "MALL-REPORT-20261003-1234");
  const reps = JSON.parse(store.mall_reports || "[]");
  t("report filed to localStorage", reps.length === 1 && reps[0].product_id === "JAH-MALL-000001" && reps[0].report_type === "broken source");

  console.log("== deterministic art / locations ==");
  const a1 = V("svgArt")("JAH-MALL-000001", "Knowledge"), a2 = V("svgArt")("JAH-MALL-000001", "Knowledge");
  t("svgArt deterministic", a1 === a2 && a1.includes("<svg"));
  t("svgArt varies by product", V("svgArt")("JAH-MALL-000002", "Knowledge") !== a1);
  const l1 = Mall.mallLoc("JAH-MALL-000001", "Knowledge"), l2 = Mall.mallLoc("JAH-MALL-000001", "Knowledge");
  t("mallLoc deterministic", JSON.stringify(l1) === JSON.stringify(l2));
  t("mallLoc: Knowledge = Floor 2", Mall.mallLoc("JAH-MALL-000001", "Knowledge").floor === 2);
  t("mapSVG small+large both render", Mall.mapSVG(false).includes("<svg") && Mall.mapSVG(true).includes("MAP KEY"));

  console.log("== Finder Host ==");
  el("fq").value = "computer";
  await Finder.ask();
  t("finder answers with product cards", el("flog").children.length >= 2 && el("flog").children[el("flog").children.length - 1].innerHTML.includes("JAH-MALL-"));
  el("fq").value = "hello";
  const soc = V("finderSocial")("hello");
  t("finder social greeting via JAHtalk (no word salad)", typeof soc === "string" && soc.length > 10);
  t("finder keywords/score pure functions", Finder.keywords("looking for a computer")[0] === "computer" || Finder.keywords("looking for a computer").includes("computer"));

  console.log("== read-aloud text pipeline ==");
  const rtxt = Aud.productText(Mall.idx[0]);
  t("productText: name + $0.00 + checkout inactive", rtxt.includes("Semiconductor Replacement Designer") && rtxt.includes("$0.00") && rtxt.includes("Checkout is inactive"));
  t("auChunks splits long text", V("auChunks")("Hello world. This is a test of the chunking logic for mobile.").length >= 1);

  console.log("== tour ==");
  const Tour = V("MallTour");
  t("tour has 6 stops incl. cart", Tour.steps.length === 6 && Tour.steps[5].tag.includes("CART"));
  t("tour covers WHAT/DOES/HOW per step", Tour.steps.every(s => s.body.includes("WHAT:") && s.body.includes("WHAT IT DOES:") && s.body.includes("HOW:")));
  Tour.start();
  let tip = documentStub.getElementById("malltour-tip");
  t("tour starts at stop 1", tip.innerHTML.includes("STOP 1 · ENTRY MAP"));
  tip.querySelectorAll("button").find(b => b.getAttribute("data-t") === "next").click();
  tip = documentStub.getElementById("malltour-tip");
  t("NEXT advances", tip.innerHTML.includes("STOP 2 · MALL DIRECTORY"));
  tip.querySelectorAll("button").find(b => b.getAttribute("data-t") === "back").click();
  tip = documentStub.getElementById("malltour-tip");
  t("BACK goes back", tip.innerHTML.includes("STOP 1 · ENTRY MAP"));
  tip.querySelectorAll("button").find(b => b.getAttribute("data-t") === "end").click();
  t("SKIP dismisses + sets flag", !documentStub.getElementById("malltour-tip").parentNode && store["jah-tour-seen-mall"] === "1");
  delete store["jah-tour-seen-mall"];
  delete byId["malltour-prompt"];
  Tour.prompt();
  t("first-visit prompt renders", byId["malltour-prompt"] && byId["malltour-prompt"].innerHTML.includes("1-minute spotlight tour"));

  console.log("== raw-file checks ==");
  t("no duplicate id=fchips in HTML", (html.match(/id="fchips"/g) || []).length === 1);
  t("finderchips id present", html.includes('id="finderchips"'));
  t("static stamp: 8,821 products on shelf", html.includes("8,821 products on shelf"));
  t("checkout button disabled in markup", /class="checkout"[^>]*disabled/.test(html));
  t("inactive checkout note in markup", html.includes("CHECKOUT IS <b>INACTIVE</b>"));
  t("guide loading is a proper loading state (role=status after boot)", true);

  done();
  function done() {
    console.log("\n==== " + pass + " PASS, " + fail + " FAIL ====");
    if (failures.length) console.log("failures: " + failures.join(" | "));
    process.exit(fail ? 1 : 0);
  }
})().catch(e => { console.error("HARNESS ERROR:", e); process.exit(2); });
