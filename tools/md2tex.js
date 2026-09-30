// Markdown -> LaTeX, plus the [S#] provenance audit. Driven by a document name.
//
//   node tools/md2tex.js                ==  node tools/md2tex.js main
//   node tools/md2tex.js p2
//   node tools/md2tex.js software
//
// `main` is the default because tools/build_pdf.sh invokes this script bare, and because
// paper/main.tex is a tracked artefact that must not shift one byte when the script is
// restructured. Everything that differs between the three manuscripts (source file, output
// file, .bib file, audit file) lives in DOCS below; the converter itself is shared.
//
// Scope is deliberately narrow: keep every quoted number intact, make the document
// compile, and prove that each provenance tag resolves to a file that is in the repo.
//
// Why not reuse the paper/main.tex that was already here: it was produced by a cloud
// model through a subagent that had no TeX compiler available, so it was never built,
// and it predates today's edits to main.md. This script replaces it, and the compiler
// is the referee.
const fs = require('fs');
const path = require('node:path');

// ---- document registry ---------------------------------------------------------------
// bibName is not stored: it is derived from the .bib filename, because `\bibliography{}`
// takes a path relative to the .tex file (both live in paper/) and a hand-kept second copy
// of the name is one more thing that can silently disagree with the file it points at.
const DOCS = {
  main: {
    src: 'paper/main.md', out: 'paper/main.tex',
    bib: 'paper/references.bib', audit: 'paper/tex_audit.md',
  },
  p2: {
    src: 'paper/p2.md', out: 'paper/p2.tex',
    bib: 'paper/references-p2.bib', audit: 'paper/tex_audit-p2.md',
  },
  software: {
    // software.md declares its own bibliography in its YAML front matter: `references.bib`.
    src: 'paper/software.md', out: 'paper/software.tex',
    bib: 'paper/references.bib', audit: 'paper/tex_audit-software.md',
  },
};

// --src/--out/--bib/--audit override the registry. They exist for two reasons: the bib path
// was the thing asked to be a parameter, and a gate that cannot be fed a deliberate bad
// input is a gate that has never been tested (see the self-tests at the bottom).
const argv = process.argv.slice(2);
const flags = {};
const positional = [];
for (const a of argv) {
  const m = a.match(/^--([^=]+)(?:=([\s\S]*))?$/);
  if (m) { flags[m[1]] = m[2] === undefined ? true : m[2]; } else positional.push(a);
}
const DOC = (positional[0] || 'main').toLowerCase();
if (!DOCS[DOC]) {
  console.error('FATAL [E-DOC-UNKNOWN] 未知文档名 `' + DOC + '`。可用：'
    + Object.keys(DOCS).join(', ') + '。  （用法：node tools/md2tex.js <main|p2|software>）');
  process.exit(2);
}
const cfg = { ...DOCS[DOC] };
for (const k of ['src', 'out', 'bib', 'audit']) if (flags[k]) cfg[k] = flags[k];
cfg.bibName = path.basename(cfg.bib).replace(/\.bib$/, '');
// `main` prints no argument: bare invocation is what build_pdf.sh does, and the string ends
// up inside paper/main.tex, which has to keep matching byte for byte.
const RUN = 'node tools/md2tex.js' + (DOC === 'main' ? '' : ' ' + DOC);

const SRC = cfg.src;
const OUT = cfg.out;

// ---- build-blocking diagnostics -------------------------------------------------------
// Every gate below appends to `problems` instead of exiting where it stands, so one run
// tells the author everything that has to be fixed rather than the first thing only. The
// behaviour is unchanged in kind: a non-empty list means nothing is written.
const problems = [];
let auditText = null;
function block(code, detail, fix) { problems.push({ code, detail, fix }); }

if (!fs.existsSync(SRC)) {
  block('E-SRC-MISSING', '源文件不存在：' + SRC, '检查文档名是否拼对，或用 --src= 指定。');
  dieIfBlocked();
}
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

// A combining tilde (U+0303) is not a character, it is an accent on the one before it, and
// pdflatex has no glyph for it. This rule has to run BEFORE the base-symbol rules: done the
// other way round, κ̃ would first become $\kappa$̃ and the accent would have nowhere to land.
// The output re-enters math mode exactly once, because $ ... $ does not nest.
const ACCENTED = { 'κ': '\\kappa', 'μ': '\\mu', 'ρ': '\\rho', 'σ': '\\sigma', 'τ': '\\tau',
  'ω': '\\omega', 'π': '\\pi', 'β': '\\beta', 'γ': '\\gamma', 'λ': '\\lambda',
  'Φ': '\\Phi', 'Σ': '\\Sigma', 'Δ': '\\Delta' };

// pdflatex cannot typeset these, so each maps to LaTeX. Anything unmapped is a hard stop
// rather than a silent drop: "this string is absent" has been mistaken three times today
// for "this quantity is absent", and a PDF that compiles with mangled characters is the
// same mistake pointing the other way.
const SYM = [
  [/([A-Za-zΑ-Ωα-ω])\u0303/g, (_, b) => '$\\widetilde{' + (ACCENTED[b] || b) + '}$'],
  [/∝/g, '$\\propto$'], [/Δ/g, '$\\Delta$'], [/ρ/g, '$\\rho$'],
  [/Φ/g, '$\\Phi$'], [/β/g, '$\\beta$'], [/κ/g, '$\\kappa$'], [/γ/g, '$\\gamma$'],
  [/ω/g, '$\\omega$'], [/π/g, '$\\pi$'], [/σ/g, '$\\sigma$'], [/μ/g, '$\\mu$'],
  // U+00B5 MICRO SIGN and U+03BC GREEK SMALL LETTER MU are different codepoints that print
  // identically; p2.md uses the first where main.md uses the second.
  [/µ/g, '$\\mu$'], [/τ/g, '$\\tau$'],
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
//
// The bib file is named by the document, never inherited. If it is not on disk the build is
// refused: substituting paper/references.bib because "there is a bib somewhere" is how p2.tex
// would end up with P1's sixteen works typeset under P2's reference heading, compiling clean
// and citing the wrong literature.
let BIBKEYS = null;
if (fs.existsSync(cfg.bib)) {
  BIBKEYS = new Set((fs.readFileSync(cfg.bib, 'utf8')
    .match(/^@\w+\{[^,]+/gm) || []).map(l => l.slice(l.indexOf('{') + 1)));
  if (!BIBKEYS.size) {
    block('E-BIB-EMPTY', 'bib 文件存在但一条 @ 条目也没有：' + cfg.bib,
      '要么把条目写进去，要么把 ' + cfg.out + ' 里对应的 \\bibliography 去掉。');
  }
} else {
  block('E-BIB-MISSING', cfg.bib + ' 不存在，' + DOC + ' 的参考文献未就位'
    + '（本脚本不会退回去用 paper/references.bib 顶替）。',
    '先产出 ' + cfg.bib + '，或显式指定 --bib=<路径>；未写出前不生成 ' + cfg.out + '。');
}
const badKeys = new Set();
const citeTokens = { n: 0 };
function cite(s) {
  return s.replace(/\[\[([A-Za-z0-9_]+)\]\]/g, (_, k) => {
    citeTokens.n++;
    if (BIBKEYS && !BIBKEYS.has(k)) badKeys.add(k);
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
let figNo = 1;
const FIGS = [];
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
  // A block that starts with an image is a figure: `![short description](path.png)`,
  // optionally followed by a `**Figure N.** caption` paragraph that becomes the caption.
  if (/^!\[/.test(l)) {
    const m = l.match(/^!\[([^\]]*)\]\(([^)]+)\)/);
    if (!m) {
      block('E-IMAGE-MALFORMED', '图片行无法解析：' + l, '需要 `![说明](路径.png)` 的写法。');
      i++; continue;
    }
    i++;
    let cap = m[1] || '';
    while (i < lines.length && !lines[i].trim()) i++;
    if (i < lines.length && /^\*\*Figure\s+\d+\.\*\*/.test(lines[i])) {
      const cp = [];
      while (i < lines.length && lines[i].trim() && !/^#/.test(lines[i])) cp.push(lines[i++]);
      cap = cp.join(' ');
    }
    const label = (cap.match(/^\*\*Figure\s+(\d+)\.\*\*/) || [, String(figNo)])[1];
    figNo++;
    if (!fs.existsSync(m[2])) {
      block('E-FIGURE-MISSING', '正文引用了图但盘上没有这个文件：' + m[2],
        '把图放进仓库，或删掉这一处图片引用。');
    }
    FIGS.push(m[2]);
    out.push('\\begin{figure}[htbp]\n\\centering\n'
      + '\\includegraphics[width=0.92\\textwidth]{' + m[2] + '}\n'
      + '\\caption{' + inline(cap) + '}\n\\label{fig:' + label + '}\n\\end{figure}');
    continue;
  }
  const para = [];
  while (i < lines.length && lines[i].trim() && !/^#/.test(lines[i]) && !/^---+\s*$/.test(lines[i])
    && !/^!\[/.test(lines[i]) && !isTable(lines, i)) para.push(lines[i++]);
  out.push(inline(para.join(' ')));
}

// The title is taken from the document's own level-1 heading and from nothing else.
// software.md has no `# ` line at all - its heading lives in the YAML front matter as
// `title:` - and front matter is not a heading this script is allowed to promote: a title
// assembled from metadata, or invented to let the build pass, is a title the author never
// wrote. So this names the gap and stops.
if (!TITLE) {
  const fm = /^---\r?\n[\s\S]*?title:\s*(.+?)\r?\n/.exec(md);
  block('E-NO-LEVEL1-HEADING',
    SRC + ' 没有一级标题（以 `# ` 开头的行，实测 '
    + (md.match(/^# [^\n]/gm) || []).length + ' 个），\\title 无从取值。',
    '在 ' + SRC + ' 里补一行 `# <标题>` 再重跑。'
    + (fm ? '（front matter 里有一条 `title: ' + fm[1].trim().slice(0, 60) + '…`，'
      : '（') + '本脚本有意不拿它当标题：那是元数据，不是稿件的正文标题。）');
}
const body = out.join('\n\n');

const stray = new Map();
for (const ch of body + (TITLE || '')) {
  if (ch.charCodeAt(0) > 127 && !isSafeNonAscii(ch)) stray.set(ch, (stray.get(ch) || 0) + 1);
}
if (stray.size) {
  // Line numbers come with the character, because "this document has 137 characters pdflatex
  // cannot typeset" is not something an author can act on; "line 177 and line 185" is.
  const where = ch => {
    const hit = [];
    for (let n = 0; n < lines.length && hit.length < 3; n++) {
      if (lines[n].includes(ch)) hit.push(n + 1);
    }
    return SRC + ':' + hit.join(',');
  };
  const listed = [...stray].sort((a, b) => b[1] - a[1]).slice(0, 12)
    .map(([ch, n]) => 'U+' + ch.codePointAt(0).toString(16).toUpperCase().padStart(4, '0')
      + '(' + ch + ') x' + n + ' @' + where(ch)).join(', ');
  block('E-CHAR-UNMAPPED',
    SRC + ' 里有 pdflatex 排不出的字符，共 ' + stray.size + ' 种：' + listed
    + (stray.size > 12 ? '…（另 ' + (stray.size - 12) + ' 种，按次数排在后面）' : ''),
    '要么是工具该扩 SYM 映射（本脚本尾部），要么是稿件得改措辞；'
    + '脚本拒绝静默丢字，因为"PDF 里少了这一串"经常被读成"这个量不存在"。');
}
if (badKeys.size) {
  block('E-CITE-UNKNOWN', '[[key]] 在 ' + cfg.bib + ' 里查不到：' + [...badKeys].join(', '),
    '补进 bib，或改回正文点名；不允许把不认识的关键字默默写成 \\citep。');
}
// A gate that could not run has to say so with its denominator: "no unknown key was found"
// and "no key was checked at all" print almost identically, and only one of them is a pass.
if (!BIBKEYS && citeTokens.n) {
  block('E-CITE-UNCHECKED', '正文里有 ' + citeTokens.n
    + ' 个 [[key]]，但 bib 文件缺失，cite 闸门这轮一条都没有核对（不是通过，是没跑）。',
    'bib 就位后重跑，未知键会照常拦下来。');
}
const citedKeys = new Set([...body.matchAll(/\\citep\{([A-Za-z0-9_]+)\}/g)].map(m => m[1]));
const uncitedBib = BIBKEYS ? [...BIBKEYS].filter(k => !citedKeys.has(k)).sort() : [];

const pre = '%% Generated by tools/md2tex.js from ' + SRC + '. Do not edit by hand: edit\n'
  + '%% ' + path.basename(SRC) + ', then run  ' + RUN + '  and recompile.\n'
  + '\\documentclass[11pt]{article}\n'
  + '\\usepackage[T1]{fontenc}\n'
  + '\\usepackage{lmodern}\n'
  + '\\usepackage[utf8]{inputenc}\n'
  + '\\usepackage[margin=1in]{geometry}\n'
  + '\\usepackage{booktabs,graphicx,amsmath,amssymb}\n'
  + '\\graphicspath{{../}}\n'
  + '\\usepackage{tabularx}\n'
  + '\\usepackage[numbers,sort&compress]{natbib}\n'
  + '\\usepackage{threeparttablex}\n'
  + '\\usepackage[british]{babel}\n'
  + '\\usepackage[hidelinks]{hyperref}\n'
  + '\\setlength{\\bibsep}{4pt}\n'
  + '% [S#] is a provenance tag. Each one resolves to a row of the appendix table in\n'
  + '% ' + path.basename(SRC) + ', which ' + cfg.audit + ' re-checks file by file. It is rendered as a\n'
  + '% small superscript rather than dropped, so an unresolved tag stays visible.\n'
  + '\\newcommand{\\prov}[1]{\\textsuperscript{\\,#1}}\n'
  + '\\widowpenalty=10000\n\\clubpenalty=10000\n'
  + '\\tolerance=2000\n\\emergencystretch=2em\n'
  + '\\title{' + TITLE + '}\n'
  // 署名与单位来自本人 2026-09-30 给的"陕西师范大学化学化工学院 夏盎然"，第二作者王长崴
  // 同院。中文名字**不进 LaTeX**——本文用 pdflatex + 默认字族，CJK 会直接编译失败；中文名
  // 留在 main.md 的署名行与 CITATION.cff 里。通讯邮箱由本人给出；ORCID 仍缺，缺的留 PENDING。
  // 三篇稿件作者相同，所以作者块整块共用；只有 \title 各取自己 md 的一级标题。
  + '\\author{Angran Xia\\thanks{Corresponding author; e-mail in the byline.}'
  + ' \\\\ \\small \\textit{School of Chemistry \\& Chemical Engineering, '
  + "Shaanxi Normal University, Xi'an 710119, Shaanxi, China}"
  + ' \\\\ \\small \\texttt{haangyeon@snnu.edu.cn}'
  + ' \\and Changwei Wang \\\\ \\small \\textit{School of Chemistry \\& Chemical Engineering, '
  + "Shaanxi Normal University, Xi'an 710119, Shaanxi, China}}\n"
  + '\\date{Draft --- 29 September 2026\\\\ \\small \\textit{ORCIDs PENDING, author-supplied}}\n'
  + '\\begin{document}\n\\maketitle\n';

const tail = '\n\\bibliographystyle{unsrtnat}\n\\bibliography{' + cfg.bibName + '}\n\\end{document}\n';

// 前言的花括号必须配平。上一轮给 \author 加单位时少写了一个 `}`：pdflatex 照样吐出
// 20 页 PDF，而 main.log 里 30 条错误、正文全被推进了前言。**"生成了 PDF"不等于稿子没坏**，
// 所以这里当场数一遍，配不平就不写文件。注释里的括号不算（先按未转义的 % 切掉）。
function braceBalance(s) {
  const noComments = s.replace(/(^|[^\\])%[^\n]*/g, '$1');
  let d = 0;
  for (let i = 0; i < noComments.length; i++) {
    const c = noComments[i];
    if (c === '\\') { i++; continue; }              // \{ \} \\ 都不是定界符
    if (c === '{') d++;
    else if (c === '}') { d--; if (d < 0) return d; }
  }
  return d;
}
// 自证非恒真：**少一个闭括号**必须数出净差 1，配平的必须数成 0。
// （第一版把"少括号"写成了 '\\author{Angran Xia}'，那串其实是配平的——
// 一个空转的反证会拦住好构建，比没有反证更糟，所以这里用不带闭括号的串。）
if (braceBalance('\\author{X') !== 1 || braceBalance('\\author{X}') !== 0) {
  throw new Error('md2tex 的括号检查自己失效了 —— 它现在是装饰，不放行');
}
// 另外两个闸门同样自证非恒真，每次运行都跑，不用外部 fixture 才想起来验一次：
// cite 闸门必须**拦得住一个不存在的键、且不误拦一个存在的键**；bib 闸门用的
// fs.existsSync 必须还能读出"不存在"。把 existsSync 换成常量 true，这里就会响。
if (BIBKEYS && BIBKEYS.size) {
  const probe = '__md2tex_selftest_unknown_key__';
  const known = [...BIBKEYS][0];
  const savedBad = new Set(badKeys); badKeys.clear();
  const savedN = citeTokens.n;
  const rendered = cite('[[' + probe + ']] and [[' + known + ']]');
  const caught = badKeys.has(probe);
  const spared = !badKeys.has(known);
  badKeys.clear(); savedBad.forEach(k => badKeys.add(k)); citeTokens.n = savedN;
  if (!caught || !spared || !rendered.includes('\\citep{' + probe + '}')) {
    throw new Error('md2tex 的 [[key]] 闸门自己失效了（未知键 ' + (caught ? '被拦' : '漏过')
      + ' / 已知键 ' + (spared ? '未误报' : '被误报') + '）—— 不放行');
  }
}
if (fs.existsSync(cfg.bib + '.selftest-no-such-file')) {
  throw new Error('md2tex 的 bib 存在性检查自己失效了（哨兵文件本不该存在）—— 不放行');
}
if (TITLE) {
  const preBal = braceBalance(pre);
  if (preBal !== 0) {
    block('E-PREAMBLE-BRACE-UNBALANCED',
      'preamble 花括号不配平（净差 ' + preBal + '）。',
      '净差不为 0 就绝不写出 ' + OUT + '：这是硬闸门。');
  }
} else {
  console.error('note: 标题缺失，preamble 尚未成形，括号闸门本轮无从检查（见 E-NO-LEVEL1-HEADING）。');
}

// ---- provenance audit: every tag cited in the body must name a file that is HERE ----
// "Here" means **tracked by git**, not merely present on this disk. The first version used
// fs.existsSync, which passed `ref/h2o_wb97x.out` - a file that exists locally but is
// excluded by `.gitignore`, so the public repo would ship a text citing an artefact nobody
// can fetch. Same failure mode as the withdrawn ORCA claim, so existence is now only a
// diagnostic ("exists but not tracked"), never the verdict.
const { spawnSync } = require('node:child_process');
const TRACKED = new Set((spawnSync('git', ['ls-files'], { encoding: 'utf8' }).stdout || '')
  .split('\n').filter(Boolean));
const looksLikePath = x => /[/.]|\.(out|json|py|md|js|txt|bib)$/.test(x) && !/^(DOI|arXiv|§)/.test(x);
// Two shapes look like paths but are not: a file *plus a line range* (`x.md:700-707`), and
// a glob (`evidence/**`). Checking the whole token as a path produced false FAILs, and a
// gate that cries wolf gets ignored, which is worse than no gate.
const stripLines = x => x.replace(/:\d+(?:[,-]{1,2}\d+)*$/, '');
const globish = x => /[*?\s]/.test(x);
const pathToken = x => !globish(x) && looksLikePath(stripLines(x)) && !stripLines(x).startsWith('/');
function verdict(paths) {
  const bad = paths.map(stripLines).filter(p => !TRACKED.has(p));
  if (!bad.length) return 'tracked';
  const onDisk = bad.filter(p => fs.existsSync(p));
  const gone = bad.filter(p => !fs.existsSync(p));
  const bits = [];
  if (onDisk.length) bits.push('**FAIL, exists but NOT tracked: ' + onDisk.join(', ') + '**');
  if (gone.length) bits.push('**FAIL, missing: ' + gone.join(', ') + '**');
  return bits.join('; ');
}

const cut = md.indexOf('## Appendix');
const appendix = cut < 0 ? '' : md.slice(cut);
const bodyText = md.slice(0, cut < 0 ? md.length : cut);
// `[S1, S5]` cites two tags. Matching only the single-tag form made every multi-tag
// bracket invisible, which under-counted the citations and would have let a genuinely
// uncited appendix row through as "never cited -> FAIL" for the wrong reason.
// The empty-match fallback has to be `[]`, not `''`: p2.md carries no `[S#]` tags at all,
// so the null branch is the normal path there, and `('').join` is a TypeError, not a zero.
// For main.md the match is non-null, so this fixes a crash without moving its audit.
const usedInBody = [...new Set((bodyText.match(/\[(S\d+(?:\s*,\s*S\d+)*)\]/g) || [])
  .join(' ').match(/S\d+/g) || [])]
  .map(x => x).sort((a, b) => +a.slice(1) - +b.slice(1));
// Inline paths cited in the running text carry no tag, so the appendix gate cannot see
// them - that is exactly how the `ref/` citation slipped past once. The filter has to be
// stricter here than in the appendix: backticked text in prose is usually an API name
// (`numint.nr_nlc_vxc`, `step_f_dispersion.terms`), so a token counts as a file only if it
// has a directory separator, or if a file by that name actually exists in the tree.
// Two shapes are excluded because they are not repo artefacts: a leading `/` marks an
// endpoint path on somebody else's server, and `<...>` marks a written-out pattern.
// A glob and a `file:lines` range are handled by globish/stripLines above.
const inlinePaths = [...new Set((bodyText.match(/`([^`]+)`/g) || []).map(s => s.slice(1, -1)))]
  .filter(x => pathToken(x) && !x.includes('<') && !x.includes('>')
    && (stripLines(x).includes('/') || fs.existsSync(stripLines(x))));
const inlineBad = verdict(inlinePaths);
const defMap = new Map([...appendix.matchAll(/^\| (S\d+) \|(.*)$/gm)].map(m => [m[1], m[2]]));

const rows = [];
for (const t of usedInBody) {
  const row = defMap.get(t);
  if (row === undefined) { rows.push([t, '(no appendix row)', '**FAIL**']); continue; }
  const paths = [...row.matchAll(/`([^`]+)`/g)].map(m => m[1]).filter(pathToken);
  const secs = [...new Set((row.match(/§\s*[\d.]+(?:\s*--\s*§?[\d.]+)?/g) || []).map(s => s.replace(/\s+/g, '')))];
  const note = secs.length ? '; also §' + secs.map(s => s.replace(/^§/, '')).join(', §') + ' of the same file' : '';
  rows.push([t, paths.map(p => '`' + p + '`').join('<br>') || '(prose reference only)',
    verdict(paths) + (paths.length ? note : '')]);
}
const uncited = [...defMap.keys()].filter(t => !usedInBody.includes(t)).sort();
const fails = rows.filter(r => /FAIL/.test(r[2])).length + uncited.length
  + (inlineBad === 'tracked' ? 0 : 1) + (verdict(FIGS) === 'tracked' ? 0 : 1);

// `main` renders the two header strings exactly as the pre-refactor script did, because
// paper/main.tex and paper/tex_audit.md are tracked artefacts and their current bytes are
// the regression baseline for this change. The other documents say which document they are.
auditText = '# LaTeX build and `[S#]` provenance audit'
  + (DOC === 'main' ? '' : ' --- ' + DOC) + '\n\n'
  + 'Written by `tools/md2tex.js`. Regenerate with `' + RUN + '`; do not edit here.\n\n'
  + '- source `' + SRC + '`: ' + md.length + ' chars, ' + lines.length + ' lines\n'
  + '- output `' + OUT + '`: title from the level-1 heading, ' + seenH.length + ' sections\n'
  + '- characters with no mapping: ' + stray.size + ' (a nonzero count stops the script)\n'
  + '- tags cited in the body: ' + usedInBody.length + '\n'
  + '- figures pulled in: ' + FIGS.length + ' -> ' + verdict(FIGS) + '\n'
  + '- inline backticked paths in the body text: ' + inlinePaths.length + ' scanned -> '
  + inlineBad + '\n'
  + '- appendix rows never cited in the body: ' + (uncited.length ? uncited.join(' ') + ' **FAIL**' : 'none') + '\n'
  + '- artefact checks that failed: ' + (fails ? fails + ' **FAIL**' : '0') + '\n'
  + '- bib entries cited: ' + citedKeys.size + ' of '
  + (BIBKEYS ? BIBKEYS.size : 'MISSING (' + cfg.bib + ')')
  + (uncitedBib.length ? '; **not cited anywhere in the body: ' + uncitedBib.join(', ') + '**' : '') + '\n\n'
  + '| tag | artefact | check |\n|---|---|---|\n'
  + rows.map(r => '| ' + r.join(' | ') + ' |').join('\n') + '\n';

dieIfBlocked();
fs.writeFileSync(OUT, pre + body + tail);
fs.writeFileSync(cfg.audit, auditText);

console.log('wrote', OUT, '| tags cited:', usedInBody.length, '| sections:', seenH.length,
  '| failed checks:', fails);

// ---- helpers that have to exist before the checks above can call them -----------------
// Hoisted function declaration: `dieIfBlocked` is used as soon as the first gate has data.
function dieIfBlocked() {
  if (!problems.length) return;
  console.error('FATAL [' + DOC + ']: ' + problems.length + ' 个问题拦住了 ' + OUT
    + '，未写出任何产物。');
  for (const p of problems) {
    console.error('  [' + p.code + '] ' + p.detail);
    if (p.fix) console.error('        修法：' + p.fix);
  }
  // The audit numbers are printed rather than written, so a blocked document still tells
  // the author where its provenance stands without leaving a half-trusted artefact behind.
  if (auditText) {
    console.error('\n--- 审计结果（仅打印，未写出 ' + cfg.audit + '）---\n' + auditText);
  }
  process.exit(1);
}
