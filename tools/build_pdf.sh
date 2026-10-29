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
case "$DOC" in
  main) JOB="VV10-pair-attribution" ;;
  software) JOB="nlcsplit" ;;
  si) JOB="VV10-pair-attribution-SI" ;;
  *) JOB="$DOC" ;;
esac
[ -x "$MIKTEX/pdflatex.exe" ] || { echo "no pdflatex at $MIKTEX"; exit 127; }

cd "$ROOT" || exit 1
if [ "$DOC" = "si" ]; then
  # main.md is the source of the provenance appendix; regenerate the standalone SI .tex
  # from it, then compile only the SI.  Build main separately so its PDF stays current.
  node tools/md2tex.js main || { echo "FAIL: md2tex (see its stderr)"; exit 1; }
  cd paper || exit 1
  export PATH="$MIKTEX:$PATH"
  rm -f "$JOB".aux "$JOB".log "$JOB".pdf
  for pass in 1 2; do
    pdflatex -jobname="$JOB" -interaction=nonstopmode supporting_information.tex >/dev/null 2>&1
    [ -f "$JOB.log" ] || { echo "FAIL: SI pass $pass produced no log"; exit 1; }
  done
  errs=$(grep -c '^!' "$JOB".log || true)
  over=$(grep -c 'Overfull \\hbox' "$JOB".log || true)
  pages=$(grep -o "Output written on $JOB.pdf ([0-9]* page" "$JOB".log | grep -o '[0-9]*' | tail -1)
  echo "SI pdf: ${pages:-0} pages | latex errors: $errs | overfull hboxes: $over"
  [ "${pages:-0}" -lt 1 ] && { echo "FAIL: no SI pages"; exit 1; }
  [ "$errs" != 0 ] && { echo "FAIL: $errs SI LaTeX error lines:"; grep -A2 '^!' "$JOB".log | head -40; exit 1; }
  echo "clean"
  exit 0
fi
node tools/md2tex.js "$DOC" || { echo "FAIL: md2tex (see its stderr)"; exit 1; }

cd paper || exit 1
export PATH="$MIKTEX:$PATH"
rm -f "$JOB".aux "$JOB".bbl "$JOB".blg "$JOB".out "$JOB".log
# 先删旧 PDF：没有这一步，pdflatex 写不进去时旧件会留在原地冒充"这次构建的产物"。
rm -f "$JOB".pdf || { echo "FAIL: cannot replace $JOB.pdf (locked)"; exit 1; }
for pass in 1 2 3; do
  pdflatex -jobname="$JOB" -interaction=nonstopmode "$DOC".tex >/dev/null 2>&1
  [ -f "$JOB".log ] || { echo "FAIL: pass $pass produced no log"; exit 1; }
  if [ "$pass" = 1 ]; then
    bibtex "$JOB" > bibtex.log 2>&1 || echo "note: bibtex exited nonzero, see paper/bibtex.log"
  fi
done

errs=$(grep -c '^!' "$JOB".log || true)
over=$(grep -c 'Overfull \\hbox' "$JOB".log || true)
cites=$(grep -c 'citation' "$JOB".aux || true)
# tail -1: a log can carry more than one "Output written" line (p2's does), and a
# multi-line $pages breaks the integer test below into a silent skip.
pages=$(grep -o "Output written on $JOB.pdf ([0-9]* page" "$JOB".log | grep -o '[0-9]*' | tail -1)

echo "pdf: ${pages:-0} pages | latex errors: $errs | overfull hboxes: $over | \\citation lines in aux: $cites"
if [ "${pages:-0}" -lt 1 ]; then echo "FAIL: no pages"; exit 1; fi
if [ "$errs" != 0 ]; then echo "FAIL: $errs LaTeX error lines:"; grep -A2 '^!' "$JOB".log | head -40; exit 1; fi
if [ "$cites" = 0 ]; then echo "FAIL: bibliography is present but nothing cites it"; exit 1; fi
if grep -q "Couldn't load" bibtex.log 2>/dev/null; then echo "FAIL: bibtex could not load a file"; cat bibtex.log; exit 1; fi
echo "clean"
# 建完把正本重新打开：阅读器里那份是旧版会误导读者（作者要求"关掉再打开"）。
# 由 PreToolUse 的 pdf-lock-gate 负责先关掉旧窗口；这里只负责打开新件。
if [ "${PDF_NO_OPEN:-0}" != 1 ] && command -v powershell >/dev/null 2>&1; then
  powershell -NoProfile -Command "Start-Process '$(cygpath -w "$ROOT/paper/$JOB.pdf")'" >/dev/null 2>&1 || true
fi
