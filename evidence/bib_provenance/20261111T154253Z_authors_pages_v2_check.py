# -*- coding: utf-8 -*-
import sys, io, re, json, time, unicodedata, urllib.request, urllib.parse
from datetime import datetime, timezone
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BIB = r"<REPO>\paper\references.bib"
txt = open(BIB, encoding='utf-8').read()
entries = []
for m in re.finditer(r'@(\w+)\{([^,]+),([^@]*)', txt):
    typ, key, body = m.group(1), m.group(2).strip(), m.group(3)
    def field(n):
        mm = re.search(n + r'\s*=\s*[\{"\'](.+?)[\}"\']\s*,?\s*\n', body, re.S)
        return mm.group(1).strip() if mm else ''
    entries.append({'key': key, 'doi': field('doi'), 'title': field('title'),
                    'pages': field('pages'), 'author': field('author')})

UNI = str.maketrans({'ø': 'o', 'Ø': 'O', 'ł': 'l', 'Ł': 'L', 'ß': 'ss',
                     'æ': 'ae', 'œ': 'oe', 'đ': 'd', 'ð': 'd', 'þ': 'th', 'ı': 'i'})
def latex2ascii(s):
    s = s.replace(r'{\i}', 'i').replace(r'{\j}', 'j')
    s = re.sub(r"\\['\"^`~vrtcHu]\s*\{([a-zA-Z])\}", r'\1', s)
    s = re.sub(r"\\['\"^`~vrtcHu]\s*([a-zA-Z])", r'\1', s)
    for cmd, rep in [(r'\ss', 'ss'), (r'\o', 'o'), (r'\O', 'O'), (r'\l', 'l'), (r'\L', 'L'),
                     (r'\ae', 'ae'), (r'\AE', 'AE'), (r'\oe', 'oe'), (r'\OE', 'OE'),
                     (r'\aa', 'a'), (r'\AA', 'A'), (r'\i', 'i'), (r'\j', 'j')]:
        s = s.replace(cmd + '{}', rep).replace(cmd, rep)
    s = re.sub(r'\\[a-zA-Z]+', ' ', s)
    return s.replace('{', '').replace('}', '')

def tokens(s):
    s = latex2ascii(s)
    s = unicodedata.normalize('NFD', s).translate(UNI)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    return sorted(t for t in re.split(r'[^a-z0-9]+', s) if t)

def bib_names(a):
    if not a:
        return None, False
    parts = [p.strip() for p in re.split(r'\s+and\s+', a)]
    trunc = False
    if parts and parts[-1].lower() in ('others', 'et al.', 'et al'):
        trunc = True
        parts = parts[:-1]
    return [tokens(p) for p in parts], trunc

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'bib-check/2.0 (mailto:<OPERATOR>@<CLUSTER>.edu.cn)'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def fetch(e):
    last = None
    for attempt in range(3):
        try:
            if e['doi']:
                doi = e['doi'].replace('https://doi.org/', '')
                return get('https://api.crossref.org/works/' + urllib.parse.quote(doi))['message'], None
            q = get('https://api.crossref.org/works?query.bibliographic=' + urllib.parse.quote(e['title']) + '&rows=1')['message']['items']
            if not q:
                return None, 'NOT_FOUND'
            return q[0], None
        except Exception as ex:
            last = str(ex)[:100]
            time.sleep(1 + attempt * 2)
    return None, 'ERROR: ' + last

import threading
from concurrent.futures import ThreadPoolExecutor
ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
jsonl = r"<REPO>\evidence\bib_provenance\%s_bib_authors_pages_v2.jsonl" % ts
fh = open(jsonl, 'w', encoding='utf-8')
lock = threading.Lock()
results = []

def process(e):
    rec = {'key': e['key'], 'status': '', 'detail': ''}
    j, err = fetch(e)
    if err:
        rec['status'] = err.split(':')[0]
        rec['detail'] = err
    else:
        probs = []
        cr_auth = j.get('author', [])
        bn, trunc = bib_names(e['author'])
        if bn is None:
            probs.append('bib has no author field')
        elif not cr_auth:
            rec['status'] = 'AUTHORS_UNVERIFIABLE'
        else:
            cn = []
            for a in cr_auth:
                if a.get('family') or a.get('given'):
                    cn.append(tokens((a.get('family', '') + ' ' + a.get('given', '')).strip()))
                else:
                    cn.append(tokens(a.get('name', '')))
            okA = (bn == cn[:len(bn)]) if trunc else (bn == cn)
            if not okA:
                probs.append('bib=%s | cr=%s' % (e['author'], ' ; '.join(
                    (a.get('family', '') + ' ' + a.get('given', '')) or a.get('name', '') for a in cr_auth)))
        bp = e['pages'].replace('--', '-').replace(' ', '')
        cp = str(j.get('page', '') or j.get('article-number', '') or '').replace(' ', '')
        if bp and cp and tokens(bp) != tokens(cp):
            probs.append('bib pages=%s | cr pages=%s' % (e['pages'], cp))
        elif bp and not cp:
            rec['status'] = 'PAGES_UNVERIFIABLE'
        if probs:
            rec['status'] = 'MISMATCH'
            rec['detail'] = ' || '.join(probs)
        elif not rec['status']:
            rec['status'] = 'OK'
            rec['detail'] = 'authors=%d pages=%s' % (len(cr_auth), cp or '(none)')
    with lock:
        fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
        fh.flush()
        print(rec['status'], rec['key'], '::', rec['detail'][:160], flush=True)
    return rec

with ThreadPoolExecutor(max_workers=8) as ex:
    for rec in ex.map(process, entries):
        results.append(rec)
fh.close()

ok = sum(r['status'] == 'OK' for r in results)
print('TOTAL', len(results), 'OK', ok)
out = r"<REPO>\evidence\bib_provenance\%s_bib_all92_authors_pages_v2_result.json" % ts
json.dump(results, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved', out)