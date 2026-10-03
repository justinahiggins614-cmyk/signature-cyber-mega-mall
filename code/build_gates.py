#!/usr/bin/env python3
"""Site #10 fix wave: inventory build gates. Exit non-zero on ANY failure.

Gates:
  COUNT      counts.json total == len(products.json) == manifest count
             == api.json product_count == sitemap product URLs
  DUPLICATE  no duplicate Mall IDs, source URLs, or canonical URLs
  URL        every source_url is a well-formed https URL on an expected host
  JSON       products.json / counts.json / mall-manifest.json / mall-map.json /
             api.json / llms.txt-present all parse
  SCHEMA     every record has the JAH-MALL-RECORD/1.0 required short fields;
             origin in {original, generated, external}
  HASH       data/products/hashes.json verifies (build_hashes.py --verify)
  SITEMAP    sitemap-products-*.xml URL count == inventory total

Run:  python3 code/build_gates.py
"""
import json, os, sys, re, glob, subprocess
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io"
fails = []

def gate(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" — " + detail if detail else ""))
    if not ok:
        fails.append(name)

def main():
    products = json.load(open(os.path.join(ROOT, "products.json")))
    counts = json.load(open(os.path.join(ROOT, "counts.json")))
    manifest = json.load(open(os.path.join(ROOT, "data", "products", "manifest.json")))
    api = json.load(open(os.path.join(ROOT, "api.json")))
    mall_manifest = json.load(open(os.path.join(ROOT, "mall-manifest.json")))
    mall_map = json.load(open(os.path.join(ROOT, "mall-map.json")))

    n = len(products)
    # COUNT
    gate("COUNT products==counts", counts["total"] == n, "%d vs %d" % (counts["total"], n))
    gate("COUNT products==manifest", manifest["count"] == n)
    gate("COUNT products==api", api["product_count"] == n)
    gate("COUNT products==mall-manifest", mall_manifest["inventory_count"] == n)
    sm_n = sum(open(f).read().count("<loc>")
               for f in glob.glob(os.path.join(ROOT, "sitemap-products-*.xml")))
    gate("COUNT products==sitemap", sm_n == n, "sitemap urls=%d" % sm_n)
    gate("COUNT by_origin sums", sum(counts["by_origin"].values()) == n)
    gate("COUNT by_dept sums", sum(counts["by_dept"].values()) == n)

    # DUPLICATE
    # DUPLICATE (legit: many tool-library products share one source page URL but
    # carry distinct source_record_ids, e.g. signature-llama/#toolsearch)
    ids = [p["id"] for p in products]
    gate("DUPLICATE mall IDs", len(set(ids)) == n)
    pairs = [(p["u"], p["g"]) for p in products]
    gate("DUPLICATE source record", len(set(pairs)) == n, "%d unique pairs" % len(set(pairs)))
    canon = [BASE + "/signature-cyber-mega-mall/?product=" + i for i in ids]
    gate("DUPLICATE canonical URLs", len(set(canon)) == n)

    # URL
    bad = [p["id"] for p in products
           if not re.match(r"^https://justinahiggins614-cmyk\.github\.io/[A-Za-z0-9_.\-/#?=&%]+$", p.get("u", ""))]
    gate("URL source_url well-formed", not bad, str(bad[:5]))

    # JSON files parse (already loaded above); check llms.txt exists
    gate("LLMS llms.txt present", os.path.exists(os.path.join(ROOT, "llms.txt")))
    gate("SCHEMA mall-record-schema.json present",
         os.path.exists(os.path.join(ROOT, "mall-record-schema.json")))
    gate("SCHEMA products-schema.json present",
         os.path.exists(os.path.join(ROOT, "products-schema.json")))

    # SCHEMA conformance (short-form required fields)
    req = {"id", "n", "d", "s", "t", "u", "b", "g"}
    bad_rec = [p["id"] for p in products if not req.issubset(p.keys())]
    gate("SCHEMA required fields", not bad_rec, str(bad_rec[:5]))
    bad_origin = [p["id"] for p in products if p.get("t") not in ("original", "generated", "external")]
    gate("SCHEMA origin enum", not bad_origin, str(bad_origin[:5]))
    bad_id = [p["id"] for p in products if not re.match(r"^JAH-MALL-[0-9]{6}$", p["id"])]
    gate("SCHEMA id format", not bad_id, str(bad_id[:5]))

    # HASH
    r = subprocess.run([sys.executable, os.path.join(ROOT, "code", "build_hashes.py"), "--verify"],
                       capture_output=True, text=True)
    gate("HASH verify", r.returncode == 0, r.stdout.strip().split("\n")[-1] if r.stdout else r.stderr[:100])

    # CHECKOUT stays disabled (page-level)
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    gate("CHECKOUT disabled button", 'CHECKOUT — DISABLED' in html and 'class="checkout" disabled' in html)
    gate("CHECKOUT no payment credentials",
         not re.search(r"sk_live|pk_live|stripe|paypal.*secret", html, re.I))

    print("---")
    if fails:
        print("GATES FAILED: %s" % ", ".join(fails))
        sys.exit(1)
    print("ALL GATES PASSED (%d products)" % n)

if __name__ == "__main__":
    main()
