import io
import re

bbl = io.open('VV10-pair-attribution.bbl', encoding='utf-8').read()
entries = re.findall(r'\\bibitem\[[^\]]*\]\{([^}]+)\}(.*?)(?=\\bibitem\[|\\end\{thebibliography\})',
                     bbl, re.S)


def plain(t):
    t = t.replace('\\newblock', ' ')
    t = re.sub(r'\\penalty0\s*', '', t)
    t = re.sub(r'\\doi\{([^}]*)\}', r'doi: \1', t)
    t = re.sub(r'\{\$\\omega\$\}', 'ω', t)
    t = t.replace('\\&', '&').replace('~', ' ')
    t = re.sub(r'\\emph\{([^}]*)\}', r'\1', t)
    t = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', t)
    t = t.replace('{', '').replace('}', '')
    return re.sub(r'\s+', ' ', t).strip()


num = {}
refs = []
for i, (key, body) in enumerate(entries, 1):
    num[key] = i
    refs.append('%d. %s' % (i, plain(body)))

missing = set()


def cite(m):
    keys = re.findall(r'\[\[([^\]]+)\]\]', m.group(0))
    out = []
    for k in keys:
        if k in num:
            out.append('[%d]' % num[k])
        else:
            missing.add(k)
            out.append('[?%s]' % k)
    return ' '.join(out)


md = io.open('main.md', encoding='utf-8').read()
md2 = re.sub(r'(?:\[\[[^\]]+\]\]\s*)+', cite, md)
md2 = re.sub(r'!\[[^\]]*\]\(', '![](', md2)
md2 = md2.replace('](figs/', '](E:/Project/GAMESS/figs/')
md2 += '\n\n## References\n\n' + '\n\n'.join(refs) + '\n'
io.open('_docx_source.md', 'w', encoding='utf-8', newline='\n').write(md2)
print('bib entries:', len(entries))
print('missing keys:', sorted(missing) if missing else 'none')
print('remaining [[ markers:', len(re.findall(r'\[\[', md2)))
