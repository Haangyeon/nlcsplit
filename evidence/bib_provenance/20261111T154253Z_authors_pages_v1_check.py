# -*- coding: utf-8 -*-
import sys, io, re, json, time, urllib.request, urllib.parse
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

def norm(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\\[a-zA-Z]+', ' ', s)
    s = re.sub(r'[{}$\\~^_]', ' ', s)
    return re.sub(r'[^a-z0-9]+', '', s.lower())

def bib_families(a):
    if not a:
        return None, False
    parts = [p.strip() for p in re.split(r'\s+and\s+', a)]
    truncated = False
    if parts and parts[-1].lower() in ('others', 'et al.', 'et al'):
        truncated = True
        parts = parts[:-1]
    fams = []
    for p in parts:
        p = re.sub(r'[{}]', '', p)
        if ',' in p:
            fam = p.split(',')[0]
        else:
            toks = p.split()
            fam = toks[-1] if toks else ''
            if len(toks) > 1 and toks[-2].lower() in ('van', 'von', 'de', 'der', 'di', 'la', 'del', 'della', 'st', 'st.'):
                fam = toks[-2] + ' ' + fam
        fams.append(norm(fam))
    return fams, truncated

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'bib-check/1.0 (mailto:<OPERATOR>@<CLUSTER>.edu.cn)'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

results = []
for e in entries:
    rec = {'key': e['key'], 'status': '', 'detail': ''}
    try:
        if e['doi']:
            doi = e['doi'].replace('https://doi.org/', '')
            j = get('https://api.crossref.org/works/' + urllib.parse.quote(doi))['message']
        else:
            q = get('https://api.crossref.org/works?query.bibliographic=' + urllib.parse.quote(e['title']) + '&rows=1')['message']['items']
            if not q:
                rec['status'] = 'NOT_FOUND'; results.append(rec); continue
            j = q[0]
        probs = []
        cr_auth = j.get('author', [])
        bf, trunc = bib_families(e['author'])
        if bf is None:
            probs.append('bib has no author field')
        elif not cr_auth:
            rec['status'] = 'AUTHORS_UNVERIFIABLE'
        else:
            cf = [norm(a.get('family', '')) for a in cr_auth]
            if trunc:
                okA = bf == cf[:len(bf)]
            else:
                okA = bf == cf
            if not okA:
                probs.append('bib Authors=%s | cr Authors=%s' % (
                    '; '.join(x for x in re.split(r'\s+and\s+', e['author'])),
                    '; '.join(a.get('family', '') + ' ' + a.get('given', '') for a in cr_auth)))
        bp = e['pages'].replace('--', '-').replace(' ', '')
        cp = str(j.get('page', '') or j.get('article-number', '') or '').replace(' ', '')
        if not bp:
            pass
        elif not cp:
            if rec['status'] != 'AUTHORS_UNVERIFIABLE':
                rec['status'] = 'PAGES_UNVERIFIABLE'
        elif norm(bp) != norm(cp):
            probs.append('bib pages=%s | cr pages=%s' % (e['pages'], cp))
        if probs:
            rec['status'] = 'MISMATCH'
            rec['detail'] = ' || '.join(probs)
        elif not rec['status']:
            rec['status'] = 'OK'
            rec['detail'] = 'authors=%d pages=%s' % (len(cr_auth), cp or '(none)')
    except Exception as ex:
        rec['status'] = 'ERROR'; rec['detail'] = str(ex)[:120]
    results.append(rec)
    time.sleep(0.15)

ok = sum(r['status'] == 'OK' for r in results)
print('TOTAL', len(results), 'OK', ok)
for r in results:
    if r['status'] != 'OK':
        print(r['status'], r['key'], '::', r['detail'])
ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out = r"<REPO>\evidence\bib_provenance\%s_bib_all92_authors_pages_result.json" % ts
json.dump(results, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('saved', out)