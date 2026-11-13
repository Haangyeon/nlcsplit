# -*- coding: utf-8 -*-
import sys, io, shutil
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import docx
SHIP = r'<REPO>\paper\VV10-pair-attribution.docx'
BAK = r'<REPO>\scratch\VV10_backup_before_qoder_namefix.docx'
APPLY = '--apply' in sys.argv
REPL = [
    ('Jiř Klimeš', 'Jiří Klimeš'),
    ('Pavel Banás, and Jiří Sponer', 'Pavel Banáš, and Jiří Šponer'),
    ('Petr Jurecka, Jiří Sponer', 'Petr Jurečka, Jiří Šponer'),
    ('Jiř Šponer', 'Jiří Šponer'),
    ('Ugur Bozkaya', 'Uğur Bozkaya'),
    ('Miquel Sol`a', 'Miquel Solà'),
    ("and 'Emilie Laure Zins", 'and Émilie-Laure Zins'),
    ('Elsebeth Schr"oder', 'Elsebeth Schröder'),
]
d = docx.Document(SHIP)
before = [p.text for p in d.paragraphs]
hits = {old: 0 for old, _ in REPL}
for p in d.paragraphs:
    for old, new in REPL:
        if old in p.text:
            hits[old] += 1
            done = False
            for r in p.runs:
                if old in r.text:
                    r.text = r.text.replace(old, new); done = True
            if not done:
                p.runs[0].text = p.text.replace(old, new)
                for r in p.runs[1:]:
                    r.text = ''
                print('WARN merged runs for', old)
after = [p.text for p in d.paragraphs]
diff = [i for i in range(len(before)) if before[i] != after[i]]
print('hits per pattern:', hits)
print('paragraphs changed:', len(diff), diff)
assert all(v == 1 for v in hits.values()), 'each pattern must hit exactly once'
if APPLY:
    shutil.copyfile(SHIP, BAK)
    d.save(SHIP)
    print('saved; backup', BAK)
else:
    print('dry run')