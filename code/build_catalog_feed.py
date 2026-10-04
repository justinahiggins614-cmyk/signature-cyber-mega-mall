#!/usr/bin/env python3
"""Standardized product catalog feed + per-department sitemap branches for the
Signature Cyber Mega-Mall (Site #10 diagnostic FIX-02).

Reads products.json (the canonical catalog) and writes:
  products-catalog.json      standardized machine-readable feed (id, name,
                             department, description, url, price, source)
  sitemap-dept-<slug>.xml    one sitemap per department (modular product
                             category branches)
  sitemap.xml                sitemap index refreshed to include the dept branches
  sitemap-pages.xml          adds the feed URL

Re-run any time the catalog changes (e.g. after code/harvest_mall.py).
Purely additive — does not touch index.html.
"""
import json, os, html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/signature-cyber-mega-mall/"
TODAY = date.today().isoformat()


def slug(d):
    return d.lower().replace(" ", "-").replace("&", "and")


def main():
    with open(os.path.join(ROOT, "products.json"), encoding="utf-8") as f:
        prods = json.load(f)

    depts = sorted({p["d"] for p in prods})

    KIND = {
        "Signature Spec Catalog": ("Draft specification",
            "Draft — ready to file · NOT filed · NOT a granted patent"),
        "The Signature Dictionary": ("Dictionary word record",
            "Original IWB definition with pronunciation, word history, and usage"),
        "Globally Rejustered Patent Catalog": ("Public patent record",
            "Real public patent, harvested from public sources"),
        "Signature Universal Paradox Immune Calculator": ("Solved equation record",
            "Deterministic solved-equation record"),
        "Signature Llama": ("LLM term / tool-library record",
            "Model documentation record"),
        "The Signature AI Telephone Book": ("AI profile",
            "AI file record — dial, chat, and download the AI's standalone file"),
        "The Signature PC System Depository": ("Computer system record",
            "System file record with specs and simulators"),
    }
    STYPE = {"original": "original — made by Justin Addam Higgins / the Signature system",
             "generated": "generated — produced by his deterministic generators",
             "external": "external — real public record harvested from public sources"}

    # 1. standardized feed
    feed = {
        "catalog": "The Signature Cyber Mega-Mall",
        "url": BASE,
        "creator": "Justin Addam Higgins",
        "updated": TODAY,
        "count": len(prods),
        "departments": [
            {"name": d, "count": sum(1 for p in prods if p["d"] == d)}
            for d in depts
        ],
        "products": [
            {
                "id": p["id"],
                "name": p["n"],
                "department": p["d"],
                "description": p.get("b", ""),
                "url": BASE + "?product=" + p["id"],
                "source_record": p.get("s", ""),
                "kind": KIND.get(p.get("s", ""), ("Catalog record", "Catalog record"))[0],
                "record_status": KIND.get(p.get("s", ""), ("Catalog record", "Catalog record"))[1],
                "origin": STYPE.get(p.get("t", ""), p.get("t", "")),
                "catalog_item": True,
                "commercial_product": False,
                "price": "0.00",
                "priceCurrency": "USD",
            }
            for p in prods
        ],
    }
    with open(os.path.join(ROOT, "products-catalog.json"), "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, separators=(",", ":"))
    print("wrote products-catalog.json (%d products)" % len(prods))

    # 2. per-department sitemap branches
    sm_names = []
    for d in depts:
        sl = slug(d)
        name = "sitemap-dept-%s.xml" % sl
        sm_names.append((name, d))
        urls = "\n".join(
            '<url><loc>%s?product=%s</loc><changefreq>monthly</changefreq></url>'
            % (BASE, p["id"])
            for p in prods if p["d"] == d
        )
        with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                    + urls + "\n</urlset>")
        print("wrote %s (%d urls)" % (name, sum(1 for p in prods if p["d"] == d)))

    # 3. refresh the sitemap index (keep existing product shards, add dept branches)
    entries = [
        "sitemap-pages.xml",
        "sitemap-products-1.xml",
        "sitemap-products-2.xml",
        "sitemap-products-3.xml",
    ] + [n for n, _ in sm_names]
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + "".join('<sitemap><loc>%s%s</loc></sitemap>\n' % (BASE, e) for e in entries)
                + "</sitemapindex>")
    print("refreshed sitemap.xml with %d entries" % len(entries))

    # 4. add the feed + the product archive (browse.html) to sitemap-pages.xml
    sp = os.path.join(ROOT, "sitemap-pages.xml")
    with open(sp, encoding="utf-8") as f:
        content = f.read()
    for url, label in ((BASE + "products-catalog.json", "products-catalog.json"),
                       (BASE + "browse.html", "browse.html")):
        if url not in content:
            content = content.replace(
                "</urlset>",
                '<url><loc>%s</loc><changefreq>weekly</changefreq></url>\n</urlset>' % url,
            )
            with open(sp, "w", encoding="utf-8") as f:
                f.write(content)
            print("added %s to sitemap-pages.xml" % label)
        else:
            print("%s already in sitemap-pages.xml" % label)


if __name__ == "__main__":
    main()
