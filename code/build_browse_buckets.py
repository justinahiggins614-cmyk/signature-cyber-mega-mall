#!/usr/bin/env python3
"""A-Z archive buckets for the Signature Cyber Mega-Mall product archive (browse.html).

Reads products.json (the canonical catalog) and writes:
  data/browse/index.json               manifest: departments -> letters -> bucket files, counts
  data/browse/<dept-slug>-<letter>.json compact product rows for that bucket
  data/browse/search-compact.json.gz   [id, name, dept] rows, fetched only on first search keystroke

browse.html lazy-loads ONE bucket file at a time when the user opens a
department > letter <details>. The full catalog is NEVER loaded at once.

Deterministic: same input => byte-identical output (except generated_at).
Run any time products.json changes:  python3 code/build_browse_buckets.py
(Wired into code/build_counts.py, which runs AFTER the harvest flushes
products.json — never one run behind.)

Purely additive — does not touch index.html's look or behavior.
"""
import gzip, json, os
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "browse")


def slug(d):
    return d.lower().replace(" ", "-").replace("&", "and")


def letter_of(name):
    for ch in (name or "").upper():
        if "A" <= ch <= "Z":
            return ch
    return "#"


def compact(p):
    # id, name, dept, store, source url, blurb — everything a bucket row needs
    return {"id": p["id"], "n": p.get("n", ""), "d": p.get("d", ""),
            "s": p.get("s", ""), "u": p.get("u", ""), "b": p.get("b", "")}


def main():
    prods = json.load(open(os.path.join(ROOT, "products.json"), encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # floor mapping = dept order of mall-map.json (floors are 1:1 with departments)
    map_path = os.path.join(ROOT, "mall-map.json")
    floors = {}
    if os.path.exists(map_path):
        for f in json.load(open(map_path, encoding="utf-8")).get("floors", []):
            floors[f["department"]] = f["floor_number"]

    buckets = {}  # (dept, letter) -> [rows]
    for p in prods:
        key = (p.get("d", "?"), letter_of(p.get("n", "")))
        buckets.setdefault(key, []).append(compact(p))
    for rows in buckets.values():
        rows.sort(key=lambda r: (r["n"].upper(), r["id"]))

    depts_out = []
    # floor order = mall-map floor_number (F1..Fn map 1:1 onto departments)
    dept_order = sorted({d for d, _ in buckets},
                        key=lambda d: (floors.get(d) or 99, d))
    for d in dept_order:
        letters = []
        for L in sorted({l for dd, l in buckets if dd == d}):
            rows = buckets[(d, L)]
            fname = "%s-%s.json" % (slug(d), L.lower())
            with open(os.path.join(OUT, fname), "w", encoding="utf-8") as f:
                json.dump({"dept": d, "letter": L, "count": len(rows),
                           "generated_at": now, "rows": rows},
                          f, ensure_ascii=False, separators=(",", ":"))
                f.write("\n")
            letters.append({"letter": L, "count": len(rows), "file": fname})
        depts_out.append({
            "dept": d, "slug": slug(d),
            "floor": floors.get(d),
            "count": sum(l["count"] for l in letters),
            "letters": letters,
        })

    with open(os.path.join(OUT, "index.json"), "w", encoding="utf-8") as f:
        json.dump({"generated_at": now, "total": len(prods),
                   "depts": depts_out},
                  f, ensure_ascii=False, indent=1)
        f.write("\n")

    # compact search rows: [id, name, dept] — fetched only when the user types
    search_rows = [[p["id"], p.get("n", ""), p.get("d", "")] for p in prods]
    with gzip.open(os.path.join(OUT, "search-compact.json.gz"), "wt",
                   encoding="utf-8") as f:
        json.dump({"generated_at": now, "count": len(search_rows),
                   "rows": search_rows}, f, ensure_ascii=False,
                  separators=(",", ":"))
    print("browse buckets: %d buckets, %d products, %d depts"
          % (len(buckets), len(prods), len(depts_out)))


if __name__ == "__main__":
    main()
