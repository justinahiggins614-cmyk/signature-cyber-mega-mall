#!/usr/bin/env python3
"""Site #10 fix wave: build the ONE authoritative inventory count source.

Reads products.json (+ data/products/manifest.json) and writes:
  counts.json            -- the single source of truth every page reads
  mall-manifest.json     -- root-level mall manifest (JAH-MALL-MANIFEST/1.0)
  mall-map.json          -- machine-readable mall map (floors/departments/stores)
  api.json               -- regenerated from counts.json (never hand-edited)
Also re-stamps the build-time count into index.html's static fallback chips
and the JSON-LD description so crawlers / no-JS see a labeled snapshot,
rebuilds data/browse/ A-Z bucket files (same run — never one run behind),
and re-stamps browse.html's header chips.

Deterministic: same input => byte-identical output (except generated_at).
Run any time products.json changes:  python3 code/build_counts.py
"""
import json, os, hashlib, re
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_VERSION = "JAH-MALL-RECORD/1.0"
BASE = "https://justinahiggins614-cmyk.github.io/signature-cyber-mega-mall/"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(65536), b""):
            h.update(blk)
    return h.hexdigest()

def main():
    pj = os.path.join(ROOT, "products.json")
    products = json.load(open(pj))
    manifest_path = os.path.join(ROOT, "data", "products", "manifest.json")
    manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else {}

    total = len(products)
    ids = [p["id"] for p in products]
    assert len(set(ids)) == total, "duplicate product IDs"
    assert ids == sorted(ids), "product IDs not in order"

    by_origin, by_dept, by_src = {}, {}, {}
    for p in products:
        by_origin[p.get("t", "?")] = by_origin.get(p.get("t", "?"), 0) + 1
        by_dept[p.get("d", "?")] = by_dept.get(p.get("d", "?"), 0) + 1
        by_src[p.get("s", "?")] = by_src.get(p.get("s", "?"), 0) + 1

    now = datetime.now(timezone.utc)
    inv_sha = sha256_file(pj)
    harvested = manifest.get("harvested", "")

    counts = {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "dataset_version": "mall-harvest-" + (harvested or now.strftime("%Y-%m-%d")),
        "schema_version": SCHEMA_VERSION,
        "inventory_version": manifest.get("generated", "mall-harvest"),
        "inventory_snapshot": harvested or now.strftime("%Y-%m-%d"),
        "inventory_sha256": inv_sha,
        "last_harvest": harvested,
        "next_expected_harvest": "on demand — manual harvest; inventory regenerates when code/harvest_mall.py is re-run",
        "total": total,
        "by_origin": by_origin,
        "by_dept": by_dept,
        "by_src": by_src,
        "checkout": {
            "enabled": False,
            "payments_enabled": False,
            "orders_enabled": False,
            "cart_enabled": True,
            "price_display": True,
        },
        "price": {"status": "FREE_NOW", "price": 0, "currency": "USD"},
    }
    with open(os.path.join(ROOT, "counts.json"), "w") as f:
        json.dump(counts, f, indent=1, ensure_ascii=False)
        f.write("\n")

    # ---- root mall manifest ----
    mall_manifest = {
        "spec": "JAH-MALL-MANIFEST/1.0",
        "mall_id": "JAH-MALL",
        "mall_name": "The Signature Cyber Mega-Mall",
        "mall_version": "1.0",
        "network_site_number": 10,
        "network_site_count": 25,
        "inventory_version": counts["inventory_version"],
        "inventory_count": total,
        "inventory_sha256": inv_sha,
        "schema_version": SCHEMA_VERSION,
        "generator_version": "mall-harvest",
        "last_updated": counts["generated_at"],
        "departments": [
            {"id": d, "name": d, "product_count": by_dept.get(d, 0),
             "canonical_url": BASE + "browse/dept-" + d.lower().replace(" ", "-").replace("&", "and") + ".html"}
            for d in manifest.get("depts", sorted(by_dept))
        ],
        "origin_types": sorted(by_origin),
        "product_types": ["catalog record"],
        "license": "Free-use license in the name of Justin Addam Higgins (see site). Source records keep their own owners/licenses.",
        "price_status": "FREE_NOW",
        "checkout_status": "DISABLED",
        "canonical_url": BASE,
        "counts": BASE + "counts.json",
        "inventory": BASE + "products.json",
        "schema": BASE + "mall-record-schema.json",
    }
    with open(os.path.join(ROOT, "mall-manifest.json"), "w") as f:
        json.dump(mall_manifest, f, indent=1, ensure_ascii=False)
        f.write("\n")

    # ---- machine-readable mall map ----
    mall_map = {
        "spec": "JAH-MALL-MAP/1.0",
        "generated_at": counts["generated_at"],
        "entrance": {"label": "main entrance", "marker": "YOU ARE HERE"},
        "floors": [
            {
                "floor_id": "F%d" % (i + 1),
                "floor_number": i + 1,
                "department": d,
                "department_id": d.lower().replace(" ", "-").replace("&", "and"),
                "product_count": by_dept.get(d, 0),
                "status": "open" if by_dept.get(d, 0) > 0 else "opening_soon",
                "canonical_url": BASE + "browse/dept-" + d.lower().replace(" ", "-").replace("&", "and") + ".html",
            }
            for i, d in enumerate(manifest.get("depts", sorted(by_dept)))
        ],
        "note": "Floor F1..Fn map 1:1 onto departments in manifest order. "
                "Product mall location: floor = department index+1, aisle = deterministic hash of product ID.",
    }
    with open(os.path.join(ROOT, "mall-map.json"), "w") as f:
        json.dump(mall_map, f, indent=1, ensure_ascii=False)
        f.write("\n")

    # ---- api.json regenerated from counts.json (single source) ----
    api = {
        "site": "Signature Cyber Mega-Mall",
        "site_url": BASE,
        "creator": "Justin Addam Higgins",
        "description": "Universal storefront layer over the JAH Network. Every product deep-links to its live source record. Grand opening: everything $0.00. Checkout inactive.",
        "for_bots": True,
        "product_count": total,
        "counts": "counts.json",
        "departments": by_dept,
        "sources": by_src,
        "origins": by_origin,
        "index": "data/products/index.json.gz",
        "products_json": "products.json",
        "manifest": "mall-manifest.json",
        "map": "mall-map.json",
        "schema": "mall-record-schema.json",
        "deep_link_pattern": BASE + "?product=JAH-MALL-######",
        "checkout": "INACTIVE — credit-card support held until the site goes active",
    }
    with open(os.path.join(ROOT, "api.json"), "w") as f:
        json.dump(api, f, indent=1, ensure_ascii=False)
        f.write("\n")

    stamp_index_html(counts)
    rebuild_browse_buckets()
    stamp_browse_html(counts)
    print("counts.json: total=%d origins=%s" % (total, by_origin))
    print("inventory sha256: %s" % inv_sha)

def stamp_index_html(counts):
    """Re-stamp build-time count into index.html's static fallback + JSON-LD.
    Markers keep the stamped regions deterministic and labeled as snapshots."""
    p = os.path.join(ROOT, "index.html")
    h = open(p, encoding="utf-8").read()
    total_fmt = "%s" % f"{counts['total']:,}"
    snap = counts["inventory_snapshot"]

    # 1) static fallback inside #livecounts (labeled snapshot, replaced by JS on boot)
    new_fallback = (
        '<div class="counts" id="livecounts">'
        '<span class="chip">%s products on shelf</span>'
        '<span class="chip">snapshot %s</span>'
        '<span class="chip">Grand-opening price: <b>$0.00</b> everything</span></div>'
    ) % (total_fmt, snap)
    h2, n1 = re.subn(r'<div class="counts" id="livecounts">.*?</div>',
                     lambda m: new_fallback, h, count=1, flags=re.S)
    assert n1 == 1, "livecounts marker not found"

    # 2) JSON-LD WebSite description count
    h2, n2 = re.subn(r"The universal storefront layer over the JAH Network: [0-9,]+ products",
                     "The universal storefront layer over the JAH Network: %s products" % total_fmt, h2, count=1)
    assert n2 == 1, "JSON-LD description marker not found"

    open(p, "w", encoding="utf-8").write(h2)
    print("index.html re-stamped: %s products (snapshot %s)" % (total_fmt, snap))

def rebuild_browse_buckets():
    """Rebuild the browse.html A-Z bucket files from products.json.

    Runs in the SAME invocation as the count stamp (never one run behind):
    products.json is already flushed by the harvest, so buckets and counts
    always agree.
    """
    import build_browse_buckets
    build_browse_buckets.main()

def stamp_browse_html(counts):
    """Re-stamp the build-time count into browse.html's header chips + JSON-LD.
    Same labeled-snapshot convention as stamp_index_html."""
    p = os.path.join(ROOT, "browse.html")
    h = open(p, encoding="utf-8").read()
    total_fmt = "%s" % f"{counts['total']:,}"
    snap = counts["inventory_snapshot"]

    h2, n1 = re.subn(r'<span class="bchip" id="browsetotal">.*?</span>',
                     '<span class="bchip" id="browsetotal">%s products on the shelves</span>'
                     % total_fmt, h, count=1)
    assert n1 == 1, "browsetotal marker not found"
    h2, n2 = re.subn(r'<span class="bchip" id="browsesnap">.*?</span>',
                     '<span class="bchip" id="browsesnap">snapshot %s</span>'
                     % snap, h2, count=1)
    assert n2 == 1, "browsesnap marker not found"
    h2, n3 = re.subn(r"The full product archive of the Signature Cyber Mega-Mall: [0-9,]+ products",
                     "The full product archive of the Signature Cyber Mega-Mall: %s products"
                     % total_fmt, h2, count=1)
    assert n3 == 1, "browse JSON-LD marker not found"

    open(p, "w", encoding="utf-8").write(h2)
    print("browse.html re-stamped: %s products (snapshot %s)" % (total_fmt, snap))

if __name__ == "__main__":
    main()
