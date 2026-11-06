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
    # Inline math must survive the brace-stripping below verbatim: dropping the group
    # braces of "_{\rm MP2}" turns valid TeX into "_\rm MP2", which pandoc refuses
    # ("unexpected control sequence \rm") and silently renders as literal TeX.
    # Park every $...$ span, flatten the rest, then restore.
    spans = []

    def park(m):
        spans.append(m.group(0))
        return '\x00%d\x00' % (len(spans) - 1)

    t = re.sub(r'\$[^$]*\$', park, t)
    t = re.sub(r'\\emph\{([^}]*)\}', r'\1', t)
    t = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', t)
    t = t.replace('{', '').replace('}', '')
    t = re.sub(r'\x00(\d+)\x00', lambda m: spans[int(m.group(1))], t)
    # `\rm X` is plain TeX; pandoc's math reader rejects it ("unexpected control
    # sequence \rm") and falls back to printing the source TeX. Convert the restored
    # math spans to the LaTeX form pandoc does parse, leaving the .bbl and the PDF
    # (which are built from the .bib by bibtex/pdflatex) untouched.
    def fix_rm(m):
        s = m.group(0)
        # The real shape is ^{\rm CCSD(T)} — the brace precedes \rm, so the group form
        # is what has to be rewritten, not "_" + "\rm".
        s = re.sub(r'\{\\rm\s+([A-Za-z0-9()]+)\}', r'{\\mathrm{\1}}', s)
        s = re.sub(r'([_^])\\rm\s+([A-Za-z0-9()]+)',
                   lambda mm: mm.group(1) + r'{\mathrm{' + mm.group(2) + '}}', s)
        return s

    t = re.sub(r'\$[^$]*\$', fix_rm, t)
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
# pandoc's markdown reader treats `[N]($...$)` as a link start and silently drops the
# math; a single space between the bracket and the parenthesis breaks the link reading.
# Lookahead only -- the `$` is not consumed.
md2 = re.sub(r'(\[[0-9]+\])(\()(?=\$)', r'\1 \2', md2)
md2 = re.sub(r'!\[[^\]]*\]\(', '![](', md2)
md2 = md2.replace('](figs/', '](E:/Project/GAMESS/figs/')
md2 += '\n\n## References\n\n' + '\n\n'.join(refs) + '\n'
io.open('_docx_source.md', 'w', encoding='utf-8', newline='\n').write(md2)
print('bib entries:', len(entries))
print('missing keys:', sorted(missing) if missing else 'none')
print('remaining [[ markers:', len(re.findall(r'\[\[', md2)))
