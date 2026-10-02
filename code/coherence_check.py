#!/usr/bin/env python3
"""Coherence check: every AI the mega-mall presents vs the phone-book canon.

Canon: /home/hatch/workspace/jah-ai-models/ai-catalog.json
Rule: the 260 AI & Software products sourced from "The Signature AI
Telephone Book" carry the canon ID in field `g`; their presented name (n)
and description (b) must match the canon NAME + DESCRIPTION exactly
(whitespace-normalized). The Finder Host concierge is a site helper and
must NOT claim a canon ID. Exit 0 = coherent, 1 = drift found (loud).
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON_PATHS = [
    "/home/hatch/workspace/jah-ai-models/ai-catalog.json",
    os.path.expanduser("~/workspace/jah-ai-models/ai-catalog.json"),
]
ID_RE = re.compile(r"JAH-AI-[A-Z0-9-]+")

def ws(s):
    return re.sub(r"\s+", " ", str(s or "")).strip()

def load_canon():
    for p in CANON_PATHS:
        if os.path.exists(p):
            c = json.load(open(p, encoding="utf-8"))
            return {r["ID"]: r for r in c.get("records", []) if r.get("ID")}
    return None

def main():
    canon = load_canon()
    issues = []
    checked = 0
    if canon is None:
        print("COHERENCE FAIL: canon file not found — cannot verify.")
        return 1
    products = json.load(open(os.path.join(ROOT, "products.json"), encoding="utf-8"))
    ai_products = [p for p in products
                   if p.get("d") == "AI & Software"
                   and "Telephone Book" in str(p.get("s", ""))]
    for p in ai_products:
        gid = str(p.get("g", "")).strip()
        if not gid:
            issues.append("AI product %s (%s) has no canon link in `g`"
                          % (p.get("id"), p.get("n")))
            continue
        rec = canon.get(gid)
        if rec is None:
            issues.append("AI product %s links unknown canon ID %s"
                          % (p.get("id"), gid))
            continue
        checked += 1
        if ws(p.get("n")) != ws(rec.get("NAME")):
            issues.append("name mismatch: mall %s shows %r, canon %s is %r"
                          % (p.get("id"), p.get("n"), gid, rec.get("NAME")))
        if ws(p.get("b")) != ws(rec.get("DESCRIPTION")):
            issues.append("description drift: mall %s vs canon %s"
                          % (p.get("id"), gid))
    # Finder Host must not claim a canon ID anywhere in the page scripts.
    for fn in ("index.html",):
        txt = open(os.path.join(ROOT, fn), encoding="utf-8", errors="replace").read()
        for m in ID_RE.findall(txt):
            if "jah-talk-fallback" in txt[max(0, txt.find(m)-60):txt.find(m)]:
                continue
            issues.append("canon ID %s appears in %s outside the product data"
                          % (m, fn))
            break
    print("=" * 64)
    print("COHERENCE REPORT — signature-cyber-mega-mall")
    print("=" * 64)
    print("AI products linked to canon: %d checked" % checked)
    print("Helper AIs (no canon ID, JAHtalk voice):")
    print("  - Finder Host (mall concierge chat strip + product-modal host)")
    if issues:
        print("\n*** DRIFT DETECTED (%d) ***" % len(issues))
        for i in issues[:30]:
            print("  ! " + i)
        if len(issues) > 30:
            print("  ... and %d more" % (len(issues) - 30))
        return 1
    print("\nOK: all %d canon-linked AI products match name + description exactly." % checked)
    return 0

if __name__ == "__main__":
    sys.exit(main())
