"""Read-only Crossref check of paper/references.bib.

For every entry with a DOI, fetch api.crossref.org/works/<doi> and compare
year / volume / first page / title.  Prints one line per entry and a summary.
Exit 1 if any entry is DOI-fetchable but disagrees, 2 if a DOI is missing or
unfetchable, 0 otherwise.

ASCII output only: this box renders cp936 and dies on box-drawing characters.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

BIB = "paper/references.bib"
MAIL = "xiaangran@<CLUSTER>.edu.cn"


def parse_bib(path):
    text = open(path, encoding="utf-8").read()
    entries = []
    for m in re.finditer(r"@(\w+)\{([^,]+),", text):
        key, typ = m.group(2).strip(), m.group(1).lower()
        i = m.end()
        depth = 1
        start = i
        while i < len(text) and depth:
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        body = text[start:i - 1]
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{", body):
            name = fm.group(1).lower()
            j = fm.end()
            d = 1
            s = j
            while j < len(body) and d:
                if body[j] == "{":
                    d += 1
                elif body[j] == "}":
                    d -= 1
                j += 1
            fields[name] = body[s:j - 1]
        entries.append((typ, key, fields))
    return entries


def norm_title(s):
    s = re.sub(r"P\s*<scp>SI4</scp>", "Psi4", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", " ", s)
    s = s.replace("$", " ").replace("{", "").replace("}", "")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def grams(s, n=4):
    t = norm_title(s).replace(" ", "")
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def fetch(doi):
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi)
    req = urllib.request.Request(url, headers={
        "User-Agent": "nlcsplit-bibcheck/1.0 (mailto:%s)" % MAIL})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)["message"]


def year_of(m):
    for k in ("published-print", "published-online", "issued", "created"):
        if k in m and m[k].get("date-parts"):
            return str(m[k]["date-parts"][0][0])
    return ""


def first_page(p):
    if not p:
        return ""
    p = p.strip()
    m = re.match(r"([A-Za-z]?\d+)", p)
    return m.group(1) if m else p


def main():
    entries = parse_bib(BIB)
    rows = []
    bad = 0
    unknown = 0
    for typ, key, f in entries:
        doi = f.get("doi", "").strip()
        if not doi:
            rows.append((key, "NO_DOI", "", ""))
            unknown += 1
            continue
        try:
            m = fetch(doi)
        except Exception as e:
            rows.append((key, "DOI_FAIL", doi, str(e)[:60]))
            unknown += 1
            continue
        notes = []
        cy = year_of(m)
        if f.get("year", "").strip() != cy:
            notes.append("YEAR %s!=%s" % (f.get("year"), cy))
        cv = str(m.get("volume", "")).strip()
        if cv and f.get("volume", "").strip() != cv:
            notes.append("VOL %s!=%s" % (f.get("volume"), cv))
        cp = first_page(m.get("page", ""))
        fp = first_page(f.get("pages", "") or f.get("page", ""))
        if cp and fp and cp != fp:
            notes.append("PAGE %s!=%s" % (fp, cp))
        g1, g2 = grams(f.get("title", "")), grams(m.get("title", [""])[0])
        jac = len(g1 & g2) / max(1, len(g1 | g2))
        if jac < 0.80:
            notes.append("TITLE jaccard=%.2f" % jac)
        status = "OK" if not notes else "; ".join(notes)
        if notes:
            bad += 1
        rows.append((key, status, doi, m.get("title", [""])[0][:70]))
        time.sleep(0.25)
    print("entries=%d  ok=%d  mismatch=%d  unverifiable=%d"
          % (len(entries), len(entries) - bad - unknown, bad, unknown))
    for key, status, doi, extra in rows:
        print("%-28s %-45s %s" % (key, status, doi))
    return 1 if bad else (2 if unknown else 0)


if __name__ == "__main__":
    sys.exit(main())
