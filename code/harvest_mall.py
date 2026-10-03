#!/usr/bin/env python3
"""Signature Cyber Mega-Mall inventory harvester.
Samples REAL records from Manon's existing site clones and emits
JAH-MALL-###### product records. Deterministic: sorted (dept, source, sid)
ordering => stable IDs across runs. No invented source records."""
import json, gzip, glob, os, math, html
from datetime import date
from urllib.parse import quote

W = os.path.expanduser('~/workspace')
MALL = os.path.join(W, 'signature-cyber-mega-mall')
OUT = os.path.join(MALL, 'data', 'products')

BASE = 'https://justinahiggins614-cmyk.github.io'
SRC = {
    'specs':   ('Signature Spec Catalog', f'{BASE}/signature-one-archive/specs.html'),
    'patents': ('Globally Rejustered Patent Catalog', f'{BASE}/cyber-patent-catalog/catalog.html'),
    'ai':      ('The Signature AI Telephone Book', f'{BASE}/jah-ai-models/'),
    'calc':    ('Signature Universal Paradox Immune Calculator', f'{BASE}/jah-calculator/index.html'),
    'dict':    ('The Signature Dictionary', f'{BASE}/jah-dictionary/'),
    'pc':      ('The Signature PC System Depository', f'{BASE}/jah-computer-systems/'),
    'llama':   ('Signature Llama', f'{BASE}/signature-llama/'),
}

DEPTS = ['AI & Software', 'Knowledge', 'Inventions', 'Compute', 'Tools', 'Books & Courses']
products = []

def add(dept, src_key, sid, name, stype, url, blurb, seed_tag=''):
    products.append({
        'dept': dept, 'src': SRC[src_key][0], 'src_key': src_key,
        'sid': sid, 'name': (name or '').strip()[:160] or sid,
        'stype': stype, 'url': url, 'blurb': (blurb or '').strip()[:240],
        'seed_tag': seed_tag or sid,
    })

def sample_lines(path, want):
    """Reservoir-free deterministic stride sample of a jsonl(.gz) file."""
    opener = gzip.open if path.endswith('.gz') else open
    recs = []
    with opener(path, 'rt') as f:
        for line in f:
            line = line.strip()
            if line:
                recs.append(line)
    n = len(recs)
    if n <= want:
        return [json.loads(x) for x in recs]
    step = n / want
    return [json.loads(recs[int(i * step)]) for i in range(want)]

def harvest_specs():
    chunks = sorted(glob.glob(f'{W}/signature-one-archive/data/volumes/specs-c*.jsonl.gz'))
    # stride across chunk list: pick 25 chunks spread across the whole range
    want_chunks, want_specs = 25, 2500
    idxs = [int(i * len(chunks) / want_chunks) for i in range(want_chunks)]
    per = math.ceil(want_specs / want_chunks)
    for i in idxs:
        for r in sample_lines(chunks[i], per):
            sid = r.get('spec_id', '')
            add('Inventions', 'specs', sid, r.get('title'), 'original',
                f"{SRC['specs'][1]}?spec={sid}",
                r.get('abstract') or r.get('autoread_block'))

def harvest_wordspecs():
    chunks = sorted(glob.glob(f'{W}/signature-one-archive/data/volumes/words-c*.jsonl.gz'))
    if not chunks:
        return
    want_chunks, want_specs = 8, 500
    idxs = [int(i * len(chunks) / want_chunks) for i in range(want_chunks)]
    per = math.ceil(want_specs / want_chunks)
    for i in idxs:
        for r in sample_lines(chunks[i], per):
            sid = r.get('spec_id', '')
            add('Inventions', 'specs', sid, r.get('title'), 'original',
                f"{SRC['specs'][1]}?spec={sid}",
                r.get('abstract') or r.get('autoread_block'))

def harvest_patents():
    for r in sample_lines(f'{W}/cyber-patent-catalog/data/patents.jsonl', 1500):
        pn = r.get('publication_number', '')
        add('Inventions', 'patents', pn, r.get('title'), 'external',
            f"{SRC['patents'][1]}?patent={quote(pn)}",
            r.get('abstract_snippet'))

def harvest_ai():
    c = json.load(open(f'{W}/jah-ai-models/ai-catalog.json'))
    for r in c['records']:
        aid = r.get('ID', '')
        add('AI & Software', 'ai', aid, r.get('NAME'), 'original',
            f"{SRC['ai'][1]}#{quote(aid)}", r.get('DESCRIPTION'))

def harvest_calc():
    chunks = sorted(glob.glob(f'{W}/jah-calculator/data/equations/eq-c*.jsonl.gz'))
    want_chunks, want_eq = 10, 2000
    idxs = [int(i * len(chunks) / want_chunks) for i in range(want_chunks)]
    per = math.ceil(want_eq / want_chunks)
    for i in idxs:
        for r in sample_lines(chunks[i], per):
            eid = r.get('id', '')
            add('Tools', 'calc', eid, r.get('title') or eid, 'generated',
                f"{SRC['calc'][1]}?tab=eq&eq={quote(eid)}",
                f"{r.get('equation','')} — {r.get('solution','')}")

def harvest_dict():
    chunks = sorted(glob.glob(f'{W}/jah-dictionary/data/dict/dict-c*.jsonl.gz'))
    want_chunks, want_w = 12, 2000
    idxs = [int(i * len(chunks) / want_chunks) for i in range(want_chunks)]
    per = math.ceil(want_w / want_chunks)
    for i in idxs:
        for r in sample_lines(chunks[i], per):
            w = (r.get('w') or '').strip()
            if not w:
                continue
            d = r.get('d') or ''
            if isinstance(d, list):
                d = ' '.join(str(x) for x in d)
            stype = 'external' if str(d).startswith('Public patent') else 'original'
            name = w if len(w) <= 80 else w[:77] + '...'
            add('Knowledge', 'dict', r.get('st') or w, name, stype,
                f"{SRC['dict'][1]}?w={quote(w)}", str(d))

def harvest_llm_dict():
    d = json.load(open(f'{W}/signature-llama/data/llm-dictionary.json'))
    for t in d['terms']:
        term = t.get('t', '')
        add('Knowledge', 'llama', f"llmterm:{term}", term, 'original',
            f"{SRC['llama'][1]}?term={quote(term)}", t.get('d'))

def harvest_tools():
    t = json.load(open(f'{W}/signature-llama/data/tool-libraries.json'))
    for lib in t['libraries']:
        lid = lib.get('id', '')
        add('Tools', 'llama', f"toollib:{lid}", lib.get('name'), 'original',
            f"{SRC['llama'][1]}#toolsearch", lib.get('desc'))

def harvest_pc():
    pcs = json.load(open(f'{W}/jah-computer-systems/data/systems.json'))
    for p in pcs:
        pid = p.get('id', '')
        add('Compute', 'pc', pid, p.get('name'), 'original',
            f"{SRC['pc'][1]}?system={quote(pid)}", p.get('desc'))

def main():
    harvest_specs(); harvest_wordspecs(); harvest_patents(); harvest_ai()
    harvest_calc(); harvest_dict(); harvest_llm_dict(); harvest_tools(); harvest_pc()
    # dedupe by (src_key, sid)
    seen, uniq = set(), []
    for p in products:
        k = (p['src_key'], p['sid'])
        if k in seen:
            continue
        seen.add(k); uniq.append(p)
    # deterministic order -> stable JAH-MALL IDs
    order = {d: i for i, d in enumerate(DEPTS)}
    srcorder = {k: i for i, k in enumerate(SRC)}
    uniq.sort(key=lambda p: (order[p['dept']], srcorder[p['src_key']], p['sid']))
    n = len(uniq)
    os.makedirs(OUT, exist_ok=True)
    dept_dir = os.path.join(OUT, 'by-dept')
    os.makedirs(dept_dir, exist_ok=True)
    CHUNK = 500
    index = []
    recs = []
    for i, p in enumerate(uniq, 1):
        pid = f'JAH-MALL-{i:06d}'
        rec = {'id': pid, 'name': p['name'], 'dept': p['dept'], 'price': 0.00,
               'src': p['src'], 'stype': p['stype'], 'sid': p['sid'],
               'url': p['url'], 'blurb': p['blurb'], 'seed': p['seed_tag']}
        recs.append(rec)
        index.append({'id': pid, 'n': p['name'], 'd': p['dept'], 's': p['src'],
                      't': p['stype'], 'u': p['url'], 'b': p['blurb'], 'g': p['seed_tag']})
    for ci in range(math.ceil(n / CHUNK)):
        with gzip.open(os.path.join(OUT, f'products-c{ci:05d}.json.gz'), 'wt') as f:
            for rec in recs[ci * CHUNK:(ci + 1) * CHUNK]:
                f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    # per-department lazy-load chunks
    slug = lambda d: d.lower().replace(' ', '-').replace('&', 'and')
    for d in DEPTS:
        dre = [r for r in recs if r['dept'] == d]
        for ci in range(math.ceil(len(dre) / CHUNK)) or [0]:
            with gzip.open(os.path.join(dept_dir, f'{slug(d)}-c{ci:05d}.json.gz'), 'wt') as f:
                for rec in dre[ci * CHUNK:(ci + 1) * CHUNK]:
                    f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    manifest = {'generated': 'mall-harvest', 'harvested': date.today().isoformat(), 'count': n, 'chunks': math.ceil(n / CHUNK),
                'per_chunk': CHUNK, 'depts': DEPTS,
                'by_dept': {d: sum(1 for p in uniq if p['dept'] == d) for d in DEPTS},
                'by_src': {SRC[k][0]: sum(1 for p in uniq if p['src_key'] == k) for k in SRC}}
    json.dump(index, gzip.open(os.path.join(OUT, 'index.json.gz'), 'wt'), ensure_ascii=False)
    json.dump(manifest, open(os.path.join(OUT, 'manifest.json'), 'w'), indent=1)
    json.dump(index, open(os.path.join(MALL, 'products.json'), 'w'), ensure_ascii=False)
    print(f'HARVESTED {n} products')
    print(json.dumps(manifest['by_dept'], indent=1))
    print(json.dumps(manifest['by_src'], indent=1))

if __name__ == '__main__':
    main()
