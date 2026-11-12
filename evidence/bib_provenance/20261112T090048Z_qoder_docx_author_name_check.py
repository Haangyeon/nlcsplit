# -*- coding: utf-8 -*-
import sys, io, re, json, unicodedata
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import docx
ROOT = r'E:\Project\GAMESS'
txt = open(ROOT + r'\paper\references.bib', encoding='utf-8').read()

ACC = {'\'': '́', '"': '̈', '^': '̂', '`': '̀', '~': '̃',
       'v': '̌', 'r': '̊', 'c': '̧', 'u': '̆', 'H': '̋'}
def latex2uni(s):
    s = s.replace(r'{\i}', 'i').replace(r'{\j}', 'j')
    def rep(m):
        cmd, arg = m.group(1), m.group(2)
        if cmd in ACC:
            return arg + ACC[cmd]
        return {'ss': 'ß', 'o': 'ø', 'O': 'Ø', 'l': 'ł', 'L': 'Ł', 'ae': 'æ',
                'AA': 'Å', 'aa': 'å', 'i': 'ı', 'j': 'ȷ'}.get(cmd, arg)
    s = re.sub(r"\\(['\"^`~vrcuH])\s*\{([a-zA-Z])\}", rep, s)
    s = re.sub(r"\\(['\"^`~vrcuH])\s*([a-zA-Z])", rep, s)
    s = re.sub(r"\\(ss|o|O|l|L|ae|AA|aa|i|j)\b\s*\{\}", lambda m: latex2uni('\\' + m.group(1)), s)
    s = re.sub(r"\\(ss|o|O|l|L|ae|AA|aa|i|j)\b", lambda m: {'ss': 'ß', 'o': 'ø', 'O': 'Ø', 'l': 'ł', 'L': 'Ł', 'ae': 'æ', 'AA': 'Å', 'aa': 'å', 'i': 'i', 'j': 'j'}[m.group(1)], s)
    s = s.replace('{', '').replace('}', '')
    return unicodedata.normalize('NFC', s)

entries = []
for m in re.finditer(r'@(\w+)\{([^,]+),([^@]*)', txt):
    body = m.group(3)
    am = re.search(r'author\s*=\s*[{"](.+?)[}"]\s*,?\s*\n', body, re.S)
    if am:
        entries.append((m.group(2).strip(), am.group(1)))
d = docx.Document(ROOT + r'\paper\VV10-pair-attribution.docx')
full = unicodedata.normalize('NFC', '\n'.join(p.text for p in d.paragraphs))
missing = []
SKIP = {'sabatini2013', 'barca2020gamess', 'peng2011repro', 'smith2016software'}
for key, auth in entries:
    if key in SKIP:
        continue
    for name in re.split(r'\s+and\s+', auth):
        name = name.strip()
        if name.lower() in ('others', 'et al.'):
            continue
        uni = latex2uni(name)
        if uni not in full:
            surname = uni.split()[-1]
            ctx = ''
            i = full.find(surname)
            if i >= 0:
                ctx = full[max(0, i - 30):i + len(surname) + 10]
            missing.append((key, name, uni, ctx))
print('bib author names checked (main-cited):', sum(len(re.split(r'\s+and\s+', a)) for k, a in entries if k not in SKIP))
print('MISSING in DOCX:', len(missing))
for key, raw, uni, ctx in missing:
    print(' ', key, '| expected:', uni, '| DOCX actual:', repr(ctx))
json.dump(missing, open(ROOT + r'\scratch\docx_name_missing_20261112.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)