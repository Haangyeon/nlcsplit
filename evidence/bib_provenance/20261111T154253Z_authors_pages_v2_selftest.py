# -*- coding: utf-8 -*-
import sys
src = open(r'<REPO>\scratch\verify_bib_authors_pages_v2.py', encoding='utf-8').read()
head = src.split("ts = datetime")[0]
g = {'__name__': 'v2test'}
exec(head, g)
tokens, bib_names = g['tokens'], g['bib_names']
cases = [
    (r'Andreas He{\ss}elmann', 'Heßelmann Andreas', True),
    (r'Poul J{\o}rgensen', 'Jørgensen Poul', True),
    (r'Elsebeth Schr{\"o}der', 'Schröder Elsebeth', True),
    (r'Jeanne G. C. M. van Duijneveldt-van de Rijdt', 'van Duijneveldt-van de Rijdt Jeanne G. C. M.', True),
    (r"Jaime Fern{\'a}ndez del R{\'i}o", 'del Río Jaime Fernández', True),
    (r'Marta W\l{}och', 'Włoch Marta', True),
    (r"Jan \v{R}ez\'{a}\v{c}", 'Řezáč Jan', True),
    (r'{FORCE11 Software Citation Working Group}', 'FORCE11 Software Citation Working Group', True),
    (r'Pavel Hobza', 'Hobza Pavel X', False),
    (r'Pavel Hobza', 'Hobza Pavel', True),
    (r'Charles R. Harris', 'Harris Charles R.', True),
    (r'K. Jarrod Millman', 'Millman K. Jarrod', True),
    (r"Ji\v{r}\'{\i} \v{S}poner", 'Šponer Jiřı́', True),
    (r'U\u{g}ur Bozkaya', 'Bozkaya Uğur', True),
    (r'Taku Takatani', 'Takatani Tait', False),
]
fail = 0
for bib, cr, want in cases:
    bn, tr = bib_names(bib)
    cn = [tokens(cr)]
    got = (bn == cn)
    if got != want:
        fail += 1
        print('SELFTEST FAIL', repr(bib), '->', bn, 'vs', cn, 'want', want)
print('selftest cases:', len(cases), 'failures:', fail)
sys.exit(1 if fail else 0)