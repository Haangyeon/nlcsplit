#!/bin/sh
# Build paper/<doc>.pdf from paper/<doc>.md and fail loudly if the build is not clean.
#
# Usage: sh tools/build_pdf.sh [main|p2|software]   (default: main)
#
# Why a script and not a remembered command sequence: the first build here produced a
# 14-page PDF while the log contained three "! LaTeX Error: Unicode character" lines.
# A PDF exists either way, so "it built" is not a check. Exit status is.
#
# MiKTeX is installed on D: and is NOT on the Git Bash PATH, hence the absolute path.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MIKTEX="/d/Program Files/MiKTeX/miktex/bin/x64"
DOC="${1:-main}"
[ -x "$MIKTEX/pdflatex.exe" ] || { echo "no pdflatex at $MIKTEX"; exit 127; }

cd "$ROOT" || exit 1
node tools/md2tex.js "$DOC" || { echo "FAIL: md2tex (see its stderr)"; exit 1; }

cd paper || exit 1
export PATH="$MIKTEX:$PATH"
rm -f "$DOC".aux "$DOC".bbl "$DOC".blg "$DOC".out "$DOC".log
for pass in 1 2 3; do
  pdflatex -interaction=nonstopmode "$DOC".tex >/dev/null 2>&1
  [ -f "$DOC".log ] || { echo "FAIL: pass $pass produced no log"; exit 1; }
  if [ "$pass" = 1 ]; then
    bibtex "$DOC" > bibtex.log 2>&1 || echo "note: bibtex exited nonzero, see paper/bibtex.log"
  fi
done

errs=$(grep -c '^!' "$DOC".log || true)
over=$(grep -c 'Overfull \\hbox' "$DOC".log || true)
cites=$(grep -c 'citation' "$DOC".aux || true)
# tail -1: a log can carry more than one "Output written" line (p2's does), and a
# multi-line $pages breaks the integer test below into a silent skip.
pages=$(grep -o "Output written on $DOC.pdf ([0-9]* page" "$DOC".log | grep -o '[0-9]*' | tail -1)

echo "pdf: ${pages:-0} pages | latex errors: $errs | overfull hboxes: $over | \\citation lines in aux: $cites"
if [ "${pages:-0}" -lt 1 ]; then echo "FAIL: no pages"; exit 1; fi
if [ "$errs" != 0 ]; then echo "FAIL: $errs LaTeX error lines:"; grep -A2 '^!' "$DOC".log | head -40; exit 1; fi
if [ "$cites" = 0 ]; then echo "FAIL: bibliography is present but nothing cites it"; exit 1; fi
if grep -q "Couldn't load" bibtex.log 2>/dev/null; then echo "FAIL: bibtex could not load a file"; cat bibtex.log; exit 1; fi
echo "clean"
