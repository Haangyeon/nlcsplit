// main.md -> main.tex, plus the [S#] provenance audit.
//
// Scope is deliberately narrow: keep every quoted number intact, make the document
// compile, and prove that each provenance tag resolves to a file that is in the repo.
//
// Why not reuse the paper/main.tex that was already here: it was produced by a cloud
// model through a subagent that had no TeX compiler available, so it was never built,
// and it predates today's edits to main.md. This script replaces it, and the compiler
// is the referee.
const fs = require('fs');

const SRC = 'paper/main.md';
const OUT = 'paper/main.tex';
const md = fs.readFileSync(SRC, 'utf8');

const ESC = { '&': '\\&', '%': '\\%', '#': '\\#', _: '\\_', $: '\\$', '~': '\\textasciitilde{}', '^': '\\textasciicircum{}' };

// Superscript/subscript runs collapse into one math group, so 10^-10 becomes $^{-10}$
// rather than four adjacent groups. U+00B9/B2/B3 are included: they live in Latin-1,
// not in the U+2070 block, and main.md uses both.
const SUP = new Map([['⁰', '0'], ['¹', '1'], ['²', '2'], ['³', '3'], ['⁴', '4'],
  ['⁵', '5'], ['⁶', '6'], ['⁷', '7'], ['⁸', '8'], ['⁹', '9'], ['⁻', '-'],
  ['¹', '1'], ['²', '2'], ['³', '3']]);
const SUP_RE = new RegExp('[' + [...SUP.keys()].join('') + ']+', 'g');
const SUB = { '₀': 0, '₁': 1, '₂': 2, '₃': 3, '₄': 4, '₅': 5, '₆': 6, '₇': 7, '₈': 8, '₉': 9 };
function scripts(t) {
  return t.replace(SUP_RE, r => '$^{' + [...r].map(c => SUP.get(c)).join('') + '}$')
    .replace(/[₀-₉]+/g, r => '$_{' + [...r].map(c => SUB[c]).join('') + '}$');
}

// pdflatex cannot typeset these, so each maps to LaTeX. Anything unmapped is a hard stop
// rather than a silent drop: "this string is absent" has been mistaken three times today
// for "this quantity is absent", and a PDF that compiles with mangled characters is the
// same mistake pointing the other way.
const SYM = [
  [/∝/g, '$\\propto$'], [/Δ/g, '$\\Delta$'], [/ρ/g, '$\\rho$'],
  [/Φ/g, '$\\Phi$'], [/β/g, '$\\beta$'], [/κ/g, '$\\kappa$'], [/γ/g, '$\\gamma$'],
  [/ω/g, '$\\omega$'], [/π/g, '$\\pi$'], [/σ/g, '$\\sigma$'], [/μ/g, '$\\mu$'],
  [/∇/g, '$\\nabla$'], [/√/g, '$\\surd$'], [/′/g, "$^{\\prime}$"],
  [/∫/g, '$\\int$'], [/∬/g, '$\\iint$'], [/Σ/g, '$\\Sigma$'], [/∈/g, '$\\in$'],
  [/≈/g, '$\\approx$'], [/⇒/g, '$\\Rightarrow$'], [/·/g, '$\\cdot$'],
  [/→/g, '$\\rightarrow$'], [/←/g, '$\\leftarrow$'], [/≤/g, '$\\leq$'], [/≥/g, '$\\geq$'],
  [/×/g, '$\\times$'], [/÷/g, '$\\div$'], [/±/g, '$\\pm$'], [/−/g, '$-$'],
  [/½/g, '$\\frac{1}{2}$'], [/¼/g, '$\\frac{1}{4}$'],
  [/Å/g, '\\AA{}'], [/§/g, '\\S{}'], [/…/g, '\\ldots{}'], [/†/g, '\\dag{}'],
  [/—/g, '---'], [/–/g, '--'], [/“/g, '``'], [/”/g, "''"], [/‘/g, '`'], [/’/g, "'"],
  // <br> is markdown-only glue for multi-path table cells; in a tabular it would print
  // literally, so it becomes a comma.
  [/<br\s*\/?>/g, ', '],
];
function symize(t) {
  t = scripts(t);
  for (const [re, to] of SYM) t = t.replace(re, to);
  return t;
}

// inputenc + utf8 with T1 fontenc typesets precomposed Latin letters natively, so the
// guard in the tail of this file must not demand a mapping for them.
function isSafeNonAscii(ch) {
  const c = ch.codePointAt(0);
  return c >= 0x00C0 && c <= 0x024F && ch !== '×' && ch !== '÷';
}

// Inline: backticked runs are code or grid names (underscores are legal inside them);
// everything else gets escaping, bold/italic, and the [S#] tag.
//
// [[bibkey]] becomes \citep{bibkey}. An unknown key stops the build: the first successful
// compile here produced 13 pages with 16 bib entries and zero \citation commands, because
// every work was named in prose and by [S#] instead, and a mistyped key would do the same
// thing quietly.
const BIBKEYS = new Set((fs.readFileSync('paper/references.bib', 'utf8')
  .match(/^@\w+\{[^,]+/gm) || []).map(l => l.slice(l.indexOf('{') + 1)));
const badKeys = new Set();
function cite(s) {
  return s.replace(/\[\[([A-Za-z0-9_]+)\]\]/g, (_, k) => {
    if (!BIBKEYS.has(k)) badKeys.add(k);
    return '\\citep{' + k + '}';
  });
}
function inline(s) {
  const parts = s.split(/(`[^`]*`)/);
  return symize(parts.map(p => {
    if (p.startsWith('`') && p.endsWith('`') && p.length > 2) {
      // Underscores stay literal-ish (escaped), and # must be escaped here too: the
      // first build died on \texttt{[S#]} with "macro parameter character #".
      return '\\texttt{' + p.slice(1, -1)
        .replace(/\\/g, '\\textbackslash{}')
        .replace(/([_&#%$])/g, '\\$1') + '}';
    }
    let t = p;
    t = cite(t);
    t = t.replace(/\[S(\d+)\]/g, (_, n) => '\\prov{S' + n + '}');
    t = t.replace(/\*\*([^*]+)\*\*/g, '\\textbf{$1}');
    t = t.replace(/(^|[\s(])\*([^*\n]+?)\*(?=[\s.,):]|$)/g, '$1\\emph{$2}');
    return t.replace(/[&%#$_~^]/g, c => ESC[c]);
  }).join(''));
}

function isTable(lines, i) {
  return lines[i].includes('|') && lines[i + 1] && /^\s*\|?[\s:|-]+\|[\s:|-]*$/.test(lines[i + 1]);
}
function splitRow(l) {
  return l.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split(/(?<!\\)\|/).map(c => c.trim());
}
function table(block) {
  const head = splitRow(block[0]);
  const body = block.slice(2).map(splitRow);
  const cols = head.length;
  // A column carrying long content (the provenance appendix does) cannot be an `l`
  // column: the first build's appendix table ran off the page. Those become tabularx
  // X columns, which wrap; narrow columns stay `l` so numbers do not get stretched.
  const wide = head.map((_, j) => Math.max(...[head, ...body].map(r => (r[j] || '').length)) > 40);
  const wrap = wide.some(Boolean);
  const spec = wrap ? wide.map(w => w ? 'X' : 'l').join('') : 'l'.repeat(cols);
  const env = wrap ? 'tabularx' : 'tabular';
  const lines = [];
  lines.push('\\begin{table}[htbp]', '\\centering', wrap ? '\\footnotesize' : '',
    '\\begin{' + env + '}' + (wrap ? '{\\textwidth}' : '') + '{' + spec + '}', '\\toprule',
    head.map(c => '\\textbf{' + inline(c) + '}').join(' & ') + ' \\\\ \\midrule');
  for (const r of body) {
    const cells = r.slice(0, cols);
    while (cells.length < cols) cells.push('');
    lines.push(cells.map(c => inline(c)).join(' & ') + ' \\\\');
  }
  lines.push('\\bottomrule', '\\end{' + env + '}', '\\end{table}');
  return lines.filter(x => x !== '').join('\n');
}

const out = [];
const seenH = [];
let TITLE = null;
let i = 0;
const lines = md.split(/\r?\n/);
while (i < lines.length) {
  const l = lines[i];
  // \title has to precede \begin{document}, so hold it and splice it into the preamble.
  if (/^# /.test(l)) { TITLE = inline(l.slice(2)); i++; continue; }
  if (/^## /.test(l)) {
    const t = l.slice(3);
    if (/^\s*Draft\b/i.test(t)) { out.push('% draft status line, intentionally not typeset'); i++; continue; }
    seenH.push(t); out.push('\\section{' + inline(t) + '}'); i++; continue;
  }
  if (/^### /.test(l)) { out.push('\\subsection{' + inline(l.slice(4)) + '}'); i++; continue; }
  if (/^#### /.test(l)) { out.push('\\subsubsection{' + inline(l.slice(5)) + '}'); i++; continue; }
  if (/^---+\s*$/.test(l)) { i++; continue; }
  if (isTable(lines, i)) {
    const blk = [];
    while (i < lines.length && lines[i].includes('|') && lines[i].trim()) blk.push(lines[i++]);
    out.push(table(blk));
    continue;
  }
  if (!l.trim()) { i++; continue; }
  const para = [];
  while (i < lines.length && lines[i].trim() && !/^#/.test(lines[i]) && !/^---+\s*$/.test(lines[i])
    && !isTable(lines, i)) para.push(lines[i++]);
  out.push(inline(para.join(' ')));
}

if (!TITLE) throw new Error('no level-1 "# " heading in main.md, so \\title would be empty');
const body = out.join('\n\n');

const stray = new Map();
for (const ch of body + TITLE) {
  if (ch.charCodeAt(0) > 127 && !isSafeNonAscii(ch)) stray.set(ch, (stray.get(ch) || 0) + 1);
}
if (stray.size) {
  console.error('FAIL: characters with no LaTeX mapping (extend SYM, or fix main.md):');
  for (const [ch, n] of [...stray].sort((a, b) => b[1] - a[1])) {
    console.error('  U+' + ch.codePointAt(0).toString(16).toUpperCase().padStart(4, '0') + '  x' + n);
  }
  process.exit(1);
}
if (badKeys.size) {
  console.error('FAIL: [[key]] not present in references.bib: ' + [...badKeys].join(', '));
  process.exit(1);
}
const citedKeys = new Set([...body.matchAll(/\\citep\{([A-Za-z0-9_]+)\}/g)].map(m => m[1]));
const uncitedBib = [...BIBKEYS].filter(k => !citedKeys.has(k)).sort();

const pre = '%% Generated by tools/md2tex.js from paper/main.md. Do not edit by hand: edit\n'
  + '%% main.md, then run  node tools/md2tex.js  and recompile.\n'
  + '\\documentclass[11pt]{article}\n'
  + '\\usepackage[T1]{fontenc}\n'
  + '\\usepackage{lmodern}\n'
  + '\\usepackage[utf8]{inputenc}\n'
  + '\\usepackage[margin=1in]{geometry}\n'
  + '\\usepackage{booktabs,graphicx,amsmath,amssymb}\n'
  + '\\usepackage{tabularx}\n'
  + '\\usepackage[numbers,sort&compress]{natbib}\n'
  + '\\usepackage{threeparttablex}\n'
  + '\\usepackage[british]{babel}\n'
  + '\\usepackage[hidelinks]{hyperref}\n'
  + '\\setlength{\\bibsep}{4pt}\n'
  + '% [S#] is a provenance tag. Each one resolves to a row of the appendix table in\n'
  + '% main.md, which paper/tex_audit.md re-checks file by file. It is rendered as a\n'
  + '% small superscript rather than dropped, so an unresolved tag stays visible.\n'
  + '\\newcommand{\\prov}[1]{\\textsuperscript{\\,#1}}\n'
  + '\\widowpenalty=10000\n\\clubpenalty=10000\n'
  + '\\tolerance=2000\n\\emergencystretch=2em\n'
  + '\\title{' + TITLE + '}\n'
  + '\\author{Angran Xia\\thanks{Correspondence address to be supplied at submission.}}\n'
  + '\\date{Draft --- 29 September 2026}\n'
  + '\\begin{document}\n\\maketitle\n';

const tail = '\n\\bibliographystyle{unsrtnat}\n\\bibliography{references}\n\\end{document}\n';
fs.writeFileSync(OUT, pre + body + tail);

// ---- provenance audit: every tag cited in the body must name a file that is here ----
const cut = md.indexOf('## Appendix');
const appendix = cut < 0 ? '' : md.slice(cut);
const usedInBody = [...new Set(md.slice(0, cut < 0 ? md.length : cut).match(/\[S\d+\]/g) || [])]
  .map(x => x.slice(1, -1)).sort((a, b) => +a.slice(1) - +b.slice(1));
const defMap = new Map([...appendix.matchAll(/^\| (S\d+) \|(.*)$/gm)].map(m => [m[1], m[2]]));

const rows = [];
for (const t of usedInBody) {
  const row = defMap.get(t);
  if (row === undefined) { rows.push([t, '(no appendix row)', '**FAIL**']); continue; }
  const paths = [...row.matchAll(/`([^`]+)`/g)].map(m => m[1])
    .filter(x => /[/.]|\.(out|json|py|md|js|txt|bib)$/.test(x) && !/^(DOI|arXiv|§)/.test(x));
  const miss = paths.filter(p => !fs.existsSync(p));
  const secs = [...new Set((row.match(/§\s*[\d.]+(?:\s*--\s*§?[\d.]+)?/g) || []).map(s => s.replace(/\s+/g, '')))];
  const note = secs.length ? '; also §' + secs.map(s => s.replace(/^§/, '')).join(', §') + ' of the same file' : '';
  rows.push([t, paths.map(p => '`' + p + '`').join('<br>') || '(prose reference only)',
    (miss.length ? '**FAIL, missing: ' + miss.join(', ') + '**' : 'exists')
      + (paths.length ? note : '')]);
}
const uncited = [...defMap.keys()].filter(t => !usedInBody.includes(t)).sort();
const fails = rows.filter(r => /FAIL/.test(r[2])).length + uncited.length;

fs.writeFileSync('paper/tex_audit.md',
  '# LaTeX build and `[S#]` provenance audit\n\n'
  + 'Written by `tools/md2tex.js`. Regenerate with `node tools/md2tex.js`; do not edit here.\n\n'
  + '- source `paper/main.md`: ' + md.length + ' chars, ' + lines.length + ' lines\n'
  + '- output `paper/main.tex`: title from the level-1 heading, ' + seenH.length + ' sections\n'
  + '- characters with no mapping: ' + stray.size + ' (a nonzero count stops the script)\n'
  + '- tags cited in the body: ' + usedInBody.length + '\n'
  + '- appendix rows never cited in the body: ' + (uncited.length ? uncited.join(' ') + ' **FAIL**' : 'none') + '\n'
  + '- artefact checks that failed: ' + (fails ? fails + ' **FAIL**' : '0') + '\n'
  + '- bib entries cited: ' + citedKeys.size + ' of ' + BIBKEYS.size
  + (uncitedBib.length ? '; **not cited anywhere in the body: ' + uncitedBib.join(', ') + '**' : '') + '\n\n'
  + '| tag | artefact | check |\n|---|---|---|\n'
  + rows.map(r => '| ' + r.join(' | ') + ' |').join('\n') + '\n');

console.log('wrote', OUT, '| tags cited:', usedInBody.length, '| sections:', seenH.length,
  '| failed checks:', fails);

