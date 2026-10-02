#!/usr/bin/env python3
"""Static crawlable browse pages for the Signature Cyber Mega-Mall (AI/crawler accessibility).

Generates browse/products-NNN.html (1,000 products per shard, plain <a href>
?product= deep links, prev/next) + browse/departments.html + browse/dept-*.html
+ browse/index.html.
Re-run any time the catalog changes; then add the pages to sitemap-pages.xml.
Purely additive — does not touch index.html's look or behavior.
"""
import gzip, json, os, html, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://justinahiggins614-cmyk.github.io/signature-cyber-mega-mall/"
OUT = os.path.join(ROOT, "browse")
PER = 1000

CSS = """body{font-family:"Segoe UI",system-ui,sans-serif;background:#05070f;color:#d7e3ff;margin:0;line-height:1.6}
.wrap{max-width:900px;margin:0 auto;padding:28px 18px}
h1{color:#00f0ff;font-size:1.5em}h2{color:#ffcf4d;margin-top:1.6em}
a{color:#9fc2ff}.meta{color:#8b98b8;font-size:.9em}.price{color:#4dff9d;font-weight:700}
.nav{display:flex;justify-content:space-between;margin:18px 0;flex-wrap:wrap;gap:8px}
ul{list-style:none;padding:0}li{margin:.35em 0}
.top{border-bottom:1px solid #1c2745;padding-bottom:10px;margin-bottom:16px}"""

def slug(d):
    return d.lower().replace(" ", "-").replace("&", "and")

def page(title, desc, body, canon):
    return ("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            f"<title>{html.escape(title)}</title>\n"
            f"<meta name=\"description\" content=\"{html.escape(desc)}\">\n"
            f"<link rel=\"canonical\" href=\"{canon}\">\n"
            f"<style>{CSS}</style>\n</head>\n<body>\n<div class=\"wrap\">\n{body}\n</div>\n</body>\n</html>\n")

def li(r):
    return (f'<li><a href="../?product={r["id"]}">{html.escape(r["n"])}</a> '
            f'<span class="meta">{html.escape(r["d"])} &middot; {r["id"]} &middot; '
            f'source: {html.escape(r["s"])}</span> <span class="price">$0.00</span></li>')

def main():
    os.makedirs(OUT, exist_ok=True)
    with gzip.open(os.path.join(ROOT, "data", "products", "index.json.gz"), "rt") as f:
        idx = json.load(f)
    man = json.load(open(os.path.join(ROOT, "data", "products", "manifest.json")))
    depts = man["depts"]
    n = len(idx)
    shards = math.ceil(n / PER)
    crumb = ('<p class="meta"><a href="../">Signature Cyber Mega-Mall</a> &middot; '
             '<a href="index.html">Browse index</a> &middot; <a href="departments.html">Departments</a></p>')

    # product shard pages
    for s in range(shards):
        chunk = idx[s*PER:(s+1)*PER]
        first, last = chunk[0]["id"], chunk[-1]["id"]
        items = "\n".join(li(r) for r in chunk)
        prev_ = (f'<a href="products-{s:03d}.html">&larr; Previous 1,000</a>' if s > 0
                 else '<span class="meta">First page</span>')
        next_ = (f'<a href="products-{s+2:03d}.html">Next 1,000 &rarr;</a>' if s < shards-1
                 else '<span class="meta">Last page</span>')
        body = (f'<div class="top">{crumb}\n<h1>Product catalog \u2014 page {s+1} of {shards}</h1>\n'
                f"<p>{first} through {last} \u2014 grand opening: every product <b>$0.00</b>. "
                f"Each link opens the product's full page (details, source record, read-aloud) at its permanent link.</p></div>\n"
                f'<div class="nav">{prev_}{next_}</div>\n<ul>\n{items}\n</ul>\n'
                f'<div class="nav">{prev_}{next_}</div>')
        t = f"Signature Cyber Mega-Mall products {first}\u2013{last}"
        with open(os.path.join(OUT, f"products-{s+1:03d}.html"), "w") as f:
            f.write(page(t, f"{len(chunk)} Mega-Mall products, {first} to {last} \u2014 all $0.00, each with a permanent product page.", body, BASE+f"browse/products-{s+1:03d}.html"))

    # per-department pages
    dept_pages = []
    for d in depts:
        items = [r for r in idx if r["d"] == d]
        if not items:
            continue
        sl = slug(d)
        dept_pages.append((d, sl, len(items)))
        lis = "\n".join(li(r) for r in items)
        body = (f'<div class="top">{crumb}\n<h1>{html.escape(d)} \u2014 {len(items):,} products</h1>\n'
                f"<p>Every product in this department, all <b>$0.00</b> for the grand opening. "
                f"Each link opens the product's full page at its permanent link.</p></div>\n<ul>\n{lis}\n</ul>")
        with open(os.path.join(OUT, f"dept-{sl}.html"), "w") as f:
            f.write(page(f"Signature Cyber Mega-Mall \u2014 {d}",
                         f"{len(items):,} {d} products at the Signature Cyber Mega-Mall \u2014 all $0.00.",
                         body, BASE+f"browse/dept-{sl}.html"))

    # departments index
    ditems = "\n".join(
        f'<li><a href="dept-{sl}.html">{html.escape(d)}</a> <span class="meta">{c:,} products</span></li>'
        for d, sl, c in dept_pages)
    soon = "".join(f'<li><span class="meta">{html.escape(d)} \u2014 opening soon</span></li>'
                   for d in depts if not any(x[0] == d for x in dept_pages))
    dbody = (f'<div class="top"><p class="meta"><a href="../">Signature Cyber Mega-Mall</a> &middot; '
             f'<a href="index.html">Browse index</a></p>\n<h1>Departments</h1>\n'
             f"<p>{len(depts)} departments, {n:,} products \u2014 everything <b>$0.00</b>.</p></div>\n"
             f"<ul>\n{ditems}\n{soon}\n</ul>")
    with open(os.path.join(OUT, "departments.html"), "w") as f:
        f.write(page("Signature Cyber Mega-Mall \u2014 departments",
                     f"The {len(depts)} departments of the Signature Cyber Mega-Mall: {n:,} products, all $0.00.",
                     dbody, BASE+"browse/departments.html"))

    # browse index
    shards_links = " ".join(f'<a href="products-{s+1:03d}.html">{s+1}</a>' for s in range(shards))
    ibody = (f'<div class="top"><p class="meta"><a href="../">Signature Cyber Mega-Mall</a></p>\n'
             f"<h1>Browse the mall</h1>\n"
             f"<p>Static, crawler-friendly index of all {n:,} products. Every link is a permanent product URL. "
             f"Grand opening: everything <b>$0.00</b>.</p></div>\n"
             f"<h2>Product pages</h2><p>{shards_links}</p>\n"
             f'<h2>By department</h2><p><a href="departments.html">Departments</a></p>')
    with open(os.path.join(OUT, "index.html"), "w") as f:
        f.write(page("Signature Cyber Mega-Mall \u2014 browse index",
                     f"Static browse index: all {n:,} Mega-Mall products and departments.",
                     ibody, BASE+"browse/"))
    print(f"wrote {shards} product shards + {len(dept_pages)} dept pages + departments + index ({n} products)")

if __name__ == "__main__":
    main()
