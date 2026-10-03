#!/usr/bin/env python3
"""Site #10 fix wave: per-product SHA-256 hashes + inventory hash.

For every product in products.json, computes SHA-256 over the canonical
serialization: JSON object with keys sorted, no whitespace, UTF-8.
Writes data/products/hashes.json  { "JAH-MALL-000001": "<sha256>", ... }.

Canonical serialization rules (published in products-schema.json):
  field order  = sorted keys
  whitespace   = none (separators ",", ":")
  unicode      = NFC, UTF-8 bytes
  numbers      = as in source record
  nulls        = omitted keys (records carry no nulls)
  hash algo    = SHA-256, hex encoded
Verification: python3 code/build_hashes.py --verify
"""
import json, os, sys, hashlib, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "products", "hashes.json")

def canonical(record):
    norm = {k: unicodedata.normalize("NFC", v) if isinstance(v, str) else v
            for k, v in record.items()}
    return json.dumps(norm, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")

def product_hash(record):
    return hashlib.sha256(canonical(record)).hexdigest()

def main():
    products = json.load(open(os.path.join(ROOT, "products.json")))
    if "--verify" in sys.argv:
        disk = json.load(open(OUT))
        bad = [p["id"] for p in products
               if disk.get(p["id"]) != product_hash(p)]
        if bad:
            print("HASH MISMATCH: %d products %s" % (len(bad), bad[:5]))
            sys.exit(1)
        print("hashes verify OK: %d products" % len(products))
        return
    hashes = {p["id"]: product_hash(p) for p in products}
    assert len(hashes) == len(products), "duplicate IDs"
    with open(OUT, "w") as f:
        json.dump(hashes, f, indent=0, ensure_ascii=False)
        f.write("\n")
    print("wrote %s (%d hashes)" % (OUT, len(hashes)))

if __name__ == "__main__":
    main()
