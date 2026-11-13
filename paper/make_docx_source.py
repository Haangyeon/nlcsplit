import io
import re

bbl = io.open('VV10-pair-attribution.bbl', encoding='utf-8').read()
entries = re.findall(r'\\bibitem\[[^\]]*\]\{([^}]+)\}(.*?)(?=\\bibitem\[|\\end\{thebibliography\})',
                     bbl, re.S)


_ACC = {
    'v': {'c': 'č', 'r': 'ř', 's': 'š', 'z': 'ž', 'e': 'ě', 'n': 'ň', 'a': 'ǎ',
          'C': 'Č', 'R': 'Ř', 'S': 'Š', 'Z': 'Ž', 'E': 'Ě'},
    "'": {'a': 'á', 'e': 'é', 'i': 'í', 'o': 'ó', 'u': 'ú', 'y': 'ý', 'n': 'ń',
          'A': 'Á', 'E': 'É', 'I': 'Í', 'O': 'Ó', 'U': 'Ú', 'Y': 'Ý'},
    '"': {'o': 'ö', 'u': 'ü', 'a': 'ä', 'O': 'Ö', 'U': 'Ü', 'A': 'Ä'},
    'u': {'g': 'ğ', 'G': 'Ğ'},
    'c': {'c': 'ç', 'C': 'Ç', 's': 'ş', 'S': 'Ş'},
    '~': {'n': 'ñ', 'N': 'Ñ', 'a': 'ã', 'o': 'õ'},
    '=': {'a': 'ā', 'e': 'ē', 'o': 'ō'},
    '`': {'a': 'à', 'e': 'è', 'i': 'ì', 'o': 'ò', 'u': 'ù',
          'A': 'À', 'E': 'È', 'O': 'Ò'},
}


def deaccent(t):
    # 2026-11-12: bbl carries LaTeX accents (\v{c}, \'i, \ss, {\o}); the PDF renders them
    # as Unicode, so the Word reference list must decode them too or names diverge.
    import unicodedata
    t = t.replace('\\ss', 'ß')
    t = t.replace('{\\o}', 'ø').replace('\\o{}', 'ø').replace('\\o ', 'ø')
    t = t.replace('\\l', 'ł').replace('\\L', 'Ł')
    t = t.replace('``', '"').replace("''", '"')
    for cmd, mp in _ACC.items():
        esc = re.escape(cmd)
        # bbl writes both \v{c} and \'{i} (letter inside the braces after the accent)
        t = re.sub(r'\\' + esc + r'\s*\{\s*([A-Za-z])\s*\}', lambda m: mp.get(m.group(1), m.group(1)), t)
        t = re.sub(r'\\' + esc + r'\s*\{([A-Za-z])\}', lambda m: mp.get(m.group(1), m.group(1)), t)
        t = re.sub(r'\\' + esc + r'[ \t]+([A-Za-z])', lambda m: mp.get(m.group(1), m.group(1)), t)
        # bbl's \'{i} loses its opening brace to the macro-stripper, leaving \'i}
        t = re.sub(r'\\' + esc + r'([A-Za-z])', lambda m: mp.get(m.group(1), m.group(1)), t)
    return unicodedata.normalize('NFC', t)


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
    t = t.replace('{\\o}', 'ø')  # before brace stripping, else \o is eaten as a macro
    # protect accent commands from the generic macro-stripper below (\' is not [a-zA-Z])
    t = re.sub(r"\\(['\"^~=vcu])\s*\{\s*\\?([A-Za-z])\}?\s*\}", lambda m: '\x01%s\x02%s\x03' % (m.group(1), m.group(2)), t)
    t = re.sub(r"\\(['\"^~=vcu])\\?([A-Za-z])", lambda m: '\x01%s\x02%s\x03' % (m.group(1), m.group(2)), t)
    t = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', t)
    t = t.replace('{', '').replace('}', '')
    t = re.sub(r'\x01(.)\x02([A-Za-z])\x03', lambda m: '\\' + m.group(1) + '{' + m.group(2) + '}', t)
    t = deaccent(t)
    # bibtex drops the hyphen in the compound given name Émilie-Laure (bbl writes
    # "Émilie Laure~Zins"); restore it so Word matches the bib/Crossref form.
    t = t.replace('Émilie Laure Zins', 'Émilie-Laure Zins')
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
    # C$_{60}$ would be parked as math and pandoc drops it to a bare C; Unicode subscript
    # renders identically to the PDF's typeset subscript in the Word reference list.
    t = t.replace('C$_{60}$', 'C₆₀')
    return re.sub(r'\s+', ' ', t).strip()


num = {}
refs = []
for i, (key, body) in enumerate(entries, 1):
    num[key] = i
    refs.append('[%d] %s' % (i, plain(body)))

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
md2 = re.sub(r'(\[[0-9]+\])(?=[A-Za-z(])', r'\1 ', md2)
md2 = re.sub(r'!\[[^\]]*\]\(', '![](', md2)
md2 = md2.replace('](figs/', '](E:/Project/GAMESS/figs/')
# 2026-11-12: standalone `---` is DROPPED by md2tex (block loop skips /^---+$/), so the
# PDFs carry no rule there. Deleting the lines keeps Word identical; a horizontal rule
# would be an element the LaTeX rendering does not have.
md2 = re.sub(r'(?m)^---+\s*$', '', md2)
# 2026-11-12: mirror md2tex's SI treatment so Word matches the rendered PDFs:
# appendix headings lose the "Appendix:" prefix (SI prints them as plain sections) and
# the three appendix tables carry the S numbers the SI uses (S1/S2/S3), not 5/6/7.
md2 = md2.replace('## Appendix: provenance of every quoted number',
                  '## Provenance of every quoted number')
md2 = md2.replace('## Appendix: the nlcsplit package', '## The nlcsplit package')
md2 = md2.replace('**Table 5.**', '**Table S1.**')
md2 = md2.replace('**Table 6.**', '**Table S2.**')
md2 = md2.replace('**Table 7.**', '**Table S3.**')
md2 = md2.replace('this table is numbered Table S2 in the Supporting Information.',
                  'this table is Table S2 of the Supporting Information.')
md2 = md2.replace('This table is numbered Table S3 in the Supporting Information.',
                  'This table is Table S3 of the Supporting Information.')
# affiliation: md2tex breaks it into two \small\textit lines; mirror the break so the
# Word byline matches the rendered PDF line for line.
md2 = md2.replace("School of Chemistry & Chemical Engineering, Shaanxi Normal University, Chang'an Campus,\nXi'an 710119, Shaanxi, China",
                  "*School of Chemistry & Chemical Engineering, Shaanxi Normal University,*\\\n*Chang'an Campus, Xi'an 710119, Shaanxi, China*")
md2 += '\n\n## References\n\n' + '\n\n'.join(refs) + '\n'
io.open('_docx_source.md', 'w', encoding='utf-8', newline='\n').write(md2)
print('bib entries:', len(entries))
print('missing keys:', sorted(missing) if missing else 'none')
print('remaining [[ markers:', len(re.findall(r'\[\[', md2)))
