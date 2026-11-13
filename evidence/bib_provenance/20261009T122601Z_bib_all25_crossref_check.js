// 20261009T122601Z_bib_all25_crossref_check.js   (rev2)
//
// paper/references.bib 全部 25 条 —— Crossref 外部元数据核验（投稿前 bibliography QA）。
// 方法依据本地 skill：~/.agents/skills/reference-metadata-crossref-check/SKILL.md
//   核心纪律：先自证字段解析率，再谈比对结论；解析率过低时"0 mismatch"是空转出来的假结论。
//
// 本文件就是"实际跑过的代码"，可直接重放：
//   node 20261009T122601Z_bib_all25_crossref_check.js > <TS>_bib_all25_crossref_summary.out
// 产物：
//   stdout                            -> <TS>_bib_all25_crossref_summary.out（调用者重定向）
//   <TS>_bib_all25_crossref_result.json -> 本脚本自己写
// 退出码含义（读 .rc 时先看这里，别把"有发现"当成"跑挂了"）：
//   0 = 运行方法学有效（解析地板 + 全部负控通过 + 无取数失败），且未发现硬 MISMATCH
//   1 = 方法学失败（解析地板未达 / 某条负控未触发 / API 取数失败）=> 本次结论不可用
//   2 = 运行有效，但发现了 MISMATCH 或 DOI 硬问题（这是发现，不是崩溃）
//
// rev1 -> rev2 改了什么（重要，因为这四条全是**本工具的假警报**，不是稿件的错）：
//   R1 APS 题名里带整段 MathML，标签长度超过 40 字符时没被剥掉 => hamada2011c60au 相似度掉到 0.50，
//      被误报 WRONG-OBJECT。改成无长度上限地剥标签 + 实体解码。
//   R2 Crossref 主题检索的 rows=3 会被 ACS **支撑信息文件**（type=component，题名与正文论文完全相同、
//      但没有卷/页/年）占满 => kruse2019dna / dasgupta2023 曾被判成"MATCH"却一个字段都没比过——
//      这正是 skill 点名的空转结论。现在：候选池按类型白名单过滤，且 **MATCH 必须真比过 ≥2 个硬字段**。
//   R3 "Review of 《题名》"/"Faculty Opinions recommendation of 《题名》"这类评审对象
//      （type=peer-review 等）会把原论文题名整串括进去，子串规则给它 0.93 => harris2020numpy 曾被误报
//      year MISMATCH。同 R2 用类型白名单排除。
//   R4 候选排序改为"同一对象优先"：存储 DOI 自身解析出的记录 = 对象级铁证，排在检索候选之前；
//      其余按 类型可信度 -> 可比字段数 -> 题名相似度。这防的是"题名够像但不是同一篇"
//      （本轮实例：剑桥某书里一章的题名就叫《NumPy》，2015 年 184-279 页，sim 也过阈值）。
//
// 三条历史踩坑（本次设计要防的东西）：
//   (a) 记忆的 DOI 属于另一篇 —— NumPy 那篇曾被记成 gnomAD 文章的 DOI（对照串见常量 GNOMAD_DOI，
//       其实测读数在摘要 G 段 C4/C5）
//   (b) 猜的 DOI 解析到了另一篇论文
//   (c) 子代理自信引用的条目，DOI 在 Crossref 返回 404
// 所以除了 skill 规定的"题名字相似度匹配后比硬字段"，本脚本对每条**存储的 DOI 做独立回查**，
// 并把 gnomAD 那篇真实记录当负控喂进去，证明这道闸门真能失败（不是恒真守卫）。
//
// 只读 paper/references.bib，不写 paper/ 下任何文件；不动 MANIFEST.sha256。

'use strict';
const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------- 配置
const TS = '20261009T122601Z';
const ROOT = '<REPO>';
const BIB = path.join(ROOT, 'paper', 'references.bib');
const OUTDIR = path.join(ROOT, 'evidence', 'bib_provenance');
const OUT_JSON = path.join(OUTDIR, TS + '_bib_all25_crossref_result.json');

// mailto 取自仓内既有通讯邮箱（paper/main.md 第 8 行、paper/p2.md 第 15 行、
// paper/software.md front matter、evidence/claims_audit/D_p2_bib_mapping.md 第 15 行同 UA）。
// 不使用/不臆造其它邮箱。
// 2026-10-09 由调用方改：原来这一行把地址硬编码成字面量，于是这份代码里烙着登录名，
// 导出闸门 B 判"账号串"拒绝出货（同一条规矩 09-30 就为"讲脱敏的证据文件自己没过脱敏"立过）。
// 改成运行时从 main.md 取，读不到就硬失败——这样任何读者重放这份脚本用的是他自己的地址，
// 而公开副本里不再出现账号。实际发出去的 UA 值见本目录那两份读数档案的抬头（已同样改为来源指针）。
const fs0 = require('fs');
const mainTxt = fs0.readFileSync(require('path').join(__dirname, '..', '..', 'paper', 'main.md'), 'utf8');
const MAILTO_HIT = mainTxt.match(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/);
if (!MAILTO_HIT) { console.error('paper/main.md 里没读到通讯邮箱：不臆造一个顶上'); process.exit(3); }
const MAILTO = MAILTO_HIT[0];
const UA = 'refcheck/1.0 (mailto:' + MAILTO + ')';
const DELAY_MS = 250;              // skill 规定的礼貌间隔
const ROWS = 3;                    // skill 规定 rows=3
const THRESH = 0.80;               // skill 规定标题相似度阈值
const CR = 'https://api.crossref.org';
// 负控用的"真实错对象"：当年被误记成 NumPy 那篇的那个 DOI，Crossref 上是 gnomAD 的 Nature 文章。
// 写成代码常量（不是注释里的句子），因为它参与实际断言。
const GNOMAD_DOI = '10.1038/s41586-020-2308-7';

// 可作为"被引对象"的 Crossref 类型。R2/R3 的假警报全部来自这里没列出的类型。
const CITEABLE = new Set(['journal-article', 'book-chapter', 'book-section', 'proceedings-article',
  'proceedings-series', 'report', 'book', 'monograph', 'dissertation', 'article', 'reference-book']);
const SECONDARY = new Set(['posted-content']);        // 预印本：可作候选，但排在正式刊之后
// 明确排除（这些会携带/括引正论文题名，是空字段记录的主要来源）
const DENIED = new Set(['component', 'peer-review', 'similar-chapter', 'abstract', 'erratum',
  'editorial', 'journal-issue', 'data-set', 'dataset', 'software', 'other', 'repository-article']);

// ---------------------------------------------------------------- 文本清洗
const MACROS = [
  [/\\ss(?![a-zA-Z])/g, 'ss'], [/\\SS(?![a-zA-Z])/g, 'SS'],
  [/\\o(?![a-zA-Z])/g, 'o'], [/\\O(?![a-zA-Z])/g, 'O'],
  [/\\l(?![a-zA-Z])/g, 'l'], [/\\L(?![a-zA-Z])/g, 'L'],
  [/\\(?:ae|AE)(?![a-zA-Z])/g, 'ae'],
  [/\\(?:textendash|textemdash|endash|emdash)\s*/g, '-'],
  [/\\(?:quad|qquad|hspace|newline|linebreak)\s*/g, ' '],
  [/\\[,;:!]\s*/g, ''],
  [/\\%/g, '%'], [/\\&/g, 'and'], [/\\#/g, '#'], [/\\\$/g, '$'],
];

// R1：剥标签不再有长度上限（APS 的 MathML 属性串很长），并解常用实体
function stripMarkup(s) {
  return String(s)
    .replace(/<!--[\s\S]*?-->/g, ' ')
    .replace(/<[^>]*>/g, '')
    .replace(/&(?:amp|lt|gt|quot|apos|nbsp|#x?[0-9a-fA-F]{1,6});/g, ' ')
    .replace(/\s+/g, ' ');
}

// 把 LaTeX 装饰拆掉，只留可读文字。反复迭代到不动点，能吃下 {\v{C}} / {\'{i}} / \textbf{...}
function deLatex(raw) {
  let s = stripMarkup(raw == null ? '' : String(raw));
  for (const [re, rep] of MACROS) s = s.replace(re, rep);
  s = s.replace(/---+/g, '-').replace(/--+/g, '-');
  for (let k = 0; k < 8; k++) {
    const t = s.replace(/\\([a-zA-Z]+|.)([^\S\r\n]*)\{([^{}]*)\}/g, '$3');
    if (t === s) break;
    s = t;
  }
  s = s.replace(/\\([a-zA-Z]+|.)/g, (m0, a) => (/^[a-zA-Z]$/.test(String(a)) ? ' ' : String(a || ' ')));
  s = s.replace(/[{}$\\_^&~]/g, '');
  return s.replace(/\s+/g, ' ').trim();
}

// 归一化：小写 + 去变音符 + 只留字母数字（skill："小写、去非字母数字"，故空格也被去掉，n-gram 走字符级）
function norm(s) {
  return deLatex(s).normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9]/g, '');
}

function grams(s, n) {
  const g = new Set();
  if (s.length < n) { if (s) g.add(s); return g; }
  for (let i = 0; i + n <= s.length; i++) g.add(s.slice(i, i + n));
  return g;
}
function jaccard4(a, b) {
  const A = grams(norm(a), 4), B = grams(norm(b), 4);
  if (!A.size || !B.size) return 0;
  let inter = 0;
  for (const x of A) if (B.has(x)) inter++;
  return inter / (A.size + B.size - inter);
}
// skill：相等记 1.0，含子串记 0.93，否则 4-gram Jaccard
function titleSim(t1, t2) {
  const a = norm(t1), b = norm(t2);
  if (!a || !b) return 0;
  if (a === b) return 1;
  if (a.includes(b) || b.includes(a)) return 0.93;
  return jaccard4(t1, t2);
}

// ---------------------------------------------------------------- BibTeX 解析
function matchBrace(text, openIdx) {
  let depth = 0;
  for (let i = openIdx; i < text.length; i++) {
    if (text[i] === '{') depth++;
    else if (text[i] === '}') { depth--; if (depth === 0) return i; }
  }
  return -1;
}
function parseFields(body) {
  const out = {};
  const re = /([A-Za-z]+)\s*=\s*([{"])/g;
  let m;
  while ((m = re.exec(body))) {
    const name = m[1].toLowerCase();
    const q = m[2];
    const open = body.indexOf(q, m.index + m[0].length - 1);
    let end;
    if (q === '{') { end = matchBrace(body, open); if (end < 0) break; }
    else { end = body.indexOf('"', open + 1); if (end < 0) break; }
    out[name] = body.slice(open + 1, end);
    re.lastIndex = end + 1;
  }
  return out;
}
function parseBib(text) {
  const entries = [];
  const re = /@[ \t]*(\w+)[ \t]*\{[ \t]*([^,\n]+?)[ \t]*,/g;
  let m;
  while ((m = re.exec(text))) {
    const open = text.indexOf('{', m.index);
    const close = matchBrace(text, open);
    if (close < 0) { re.lastIndex = open + 1; continue; }
    entries.push({
      type: m[1].toLowerCase(),
      key: m[2].trim(),
      fields: parseFields(text.slice(open + 1, close)),
    });
    re.lastIndex = close + 1;
  }
  return entries;
}

function firstAuthorFamily(authorField) {
  const grp = String(authorField || '').split(/(?:^|\})\s+and\s+(?:\{|$)/);
  const one = deLatex(grp[0] || '').replace(/[{}]/g, '').trim();
  if (!one) return '';
  const toks = one.split(/\s+/).filter((t) => /[A-Za-z\xc0-\u024f]/.test(t));
  return toks.length ? toks[toks.length - 1] : one;
}

// ---------------------------------------------------------------- 字段比对
// 页码缩写还原：'23578-83' -> 23578 / 23583 ；'4435--41' -> 4435 / 4441（skill 假警报第 1 行）
function expandEnd(start, end) {
  if (end == null || end === '') return null;
  if (/^[0-9]+$/.test(String(end)) && /^[0-9]+$/.test(String(start)) &&
      String(end).length < String(start).length) {
    return String(start).slice(0, String(start).length - String(end).length) + String(end);
  }
  return String(end);
}
function pageTokens(v) {
  const s = deLatex(v).trim();
  if (!s) return null;
  const m = s.match(/^(.{1,24}?)\s*(?:--|-|–|—)\s*(.{1,24})$/);
  if (m) return { start: m[1].trim(), endRaw: m[2].trim(), end: expandEnd(m[1].trim(), m[2].trim()) };
  return { start: s, endRaw: null, end: null };
}
const looseEq = (a, b) => {
  if (a == null || b == null) return false;
  const x = String(a).trim(), y = String(b).trim();
  if (x.toLowerCase() === y.toLowerCase()) return true;
  const xn = x.replace(/^0+(?=.)/, ''), yn = y.replace(/^0+(?=.)/, '');
  return xn === yn && /^[0-9]+$/.test(xn);
};

function comparePages(bibPages, crRec) {
  const crSrc = crRec.page ? 'page' : (crRec['article-number'] ? 'article-number' : null);
  if (!crSrc) return { status: 'NO-DATA', note: 'Crossref 无 page 也无 article-number，此字段无从比对' };
  const a = pageTokens(bibPages);
  const b = crSrc === 'page' ? pageTokens(crPage(crRec)) : { start: String(crRec['article-number']), endRaw: null, end: null };
  if (!a) return { status: 'NO-DATA', note: '稿件未存页码' };
  if (!b) return { status: 'NO-DATA', note: 'Crossref 页码无法解析' };
  if (!looseEq(a.start, b.start)) return { status: 'MISMATCH', note: '起页 ' + a.start + ' vs ' + b.start };
  if (a.end && b.end && !looseEq(a.end, b.end)) return { status: 'MISMATCH', note: '末页(还原后) ' + a.end + ' vs ' + b.end };
  if (b.end && !a.end) return { status: 'OK', note: '稿件只记起页，Crossref 给 ' + b.start + '-' + b.end + '（非错：风格上省略末页）' };
  if (a.end && !b.end) return { status: 'OK', note: 'Crossref 只给起页/文章号（非错：库侧缺末页）' };
  if (!a.end && !b.end) return { status: 'OK', note: '单值（文章号或起页）相等' };
  return { status: 'OK', note: '起末均一致（缩写已还原）' };
}
const crPage = (r) => r.page;
const crVol = (r) => String(r.volume || '');
function compareVolume(bibVol, crRec) {
  const b = crRec.volume;
  if (bibVol == null || String(bibVol).trim() === '') return { status: 'NO-DATA', note: '稿件未存卷号' };
  if (b == null || String(b).trim() === '') return { status: 'NO-DATA', note: 'Crossref 未给卷号' };
  return looseEq(bibVol, b) ? { status: 'OK', note: '' } : { status: 'MISMATCH', note: '卷 ' + bibVol + ' vs ' + b };
}
function crYears(crRec) {
  const y = (o) => (o && o['date-parts'] && o['date-parts'][0] && o['date-parts'][0][0]) || null;
  return { issued: y(crRec.issued), print: y(crRec['published-print']), online: y(crRec['published-online']), accepted: y(crRec.accepted) };
}
function compareYear(bibYear, crRec) {
  const yy = crYears(crRec);
  if (bibYear == null || String(bibYear).trim() === '') return { status: 'NO-DATA', years: yy, note: '稿件未存年份' };
  const cand = [yy.issued, yy.print, yy.online].filter(Boolean).map(String);
  if (!cand.length) return { status: 'NO-DATA', years: yy, note: 'Crossref 该记录未给任何日期（多为支撑信息/评审对象）' };
  const distinct = [...new Set(cand)];
  if (!distinct.includes(String(bibYear).trim())) {
    return { status: 'MISMATCH', years: yy, note: '年 ' + bibYear + ' 不等于 Crossref 任一年份 [' + distinct.join(', ') + ']' };
  }
  if (distinct.length > 1 && yy.print && String(bibYear) !== String(yy.print) && String(crRec.volume || '').trim() !== '') {
    return { status: 'OK', years: yy, note: '软提示：稿件年 ' + bibYear + ' 命中的是**在线首发/issued**年，' +
      '而卷 ' + crRec.volume + ' 所属正刊(print)年为 ' + yy.print + '。两个写法都站得住，但"卷-年配对"按惯例应以 print 年为准，需人工定夺。' };
  }
  return { status: 'OK', years: yy, note: distinct.length > 1 ? 'Crossref 存在多个年份（issued ' + yy.issued + ' / print ' + yy.print + ' / online ' + yy.online + '），稿件值命中其一' : '' };
}
// 期刊：缩写感知（首字母序列 + 词集重合率），只作证据列，不当硬字段（skill 假警报第 5 行）
const STOPW = new Set(['the', 'of', 'and', 'in', 'for', 'a', 'an', 'to', 'on', 'comptes', 'revue']);
function journalSig(j) {
  const words = deLatex(j).toLowerCase().replace(/[^a-z0-9 ]/g, ' ').split(/\s+/).filter((w) => w && !STOPW.has(w));
  return { words: new Set(words), init: words.map((w) => w[0]).join('') };
}
function journalAgree(bibJ, crJ) {
  if (!bibJ || !crJ) return { agree: null, note: '缺一侧期刊名，无从缩写比对' };
  const A = journalSig(bibJ), B = journalSig(crJ);
  let inter = 0;
  for (const w of A.words) if (B.words.has(w)) inter++;
  const overlap = inter / Math.max(1, Math.min(A.words.size, B.words.size));
  const initEq = A.init === B.init && A.init.length >= 2;
  const agree = initEq || overlap >= 0.6;
  return { agree, note: 'bib[' + A.init + '] vs cr[' + B.init + '] 词集重合 ' + overlap.toFixed(2) + (initEq ? '，首字母序列相同' : '') };
}

// ---------------------------------------------------------------- Crossref 取数
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let apiCalls = 0; const apiErrors = [];

async function crFetch(url, label) {
  const backoffs = [0, 2000, 5000, 9000];
  for (let i = 0; i < backoffs.length; i++) {
    if (i) await sleep(backoffs[i]);
    await sleep(DELAY_MS);
    apiCalls++;
    let r;
    try {
      r = await fetch(url, { headers: { 'User-Agent': UA, Accept: 'application/json' }, signal: AbortSignal.timeout(45000) });
    } catch (e) {
      apiErrors.push(label + ' attempt' + (i + 1) + ' network: ' + String(e.message || e).slice(0, 120));
      continue;
    }
    if (r.status === 404) return { notFound: true };
    if (r.status === 429 || r.status >= 500) {           // 429 绝不当成"没查到"
      apiErrors.push(label + ' attempt' + (i + 1) + ' HTTP ' + r.status);
      continue;
    }
    if (!r.ok) { apiErrors.push(label + ' HTTP ' + r.status + ' (final)'); return { error: 'HTTP ' + r.status }; }
    try { return { message: (await r.json()).message }; } catch (e) { apiErrors.push(label + ' bad json: ' + e.message); }
  }
  return { error: 'exhausted retries' };
}
async function searchBibliographic(title, family) {
  const q = deLatex(title) + (family ? ' ' + family : '');
  const url = CR + '/works?rows=' + ROWS + '&mailto=' + encodeURIComponent(MAILTO) +
    '&query.bibliographic=' + encodeURIComponent(q);
  const res = await crFetch(url, 'search[' + q.slice(0, 30) + ']');
  if (res.notFound) return { items: [], query: q, note: 'search HTTP 404' };
  if (res.error) return { items: [], query: q, error: res.error };
  return { items: (res.message && res.message.items) || [], query: q };
}
function crRecordOf(m) {
  return {
    doi: m.DOI, title: (m.title || [])[0] || '', altTitle: (m['alternative-title'] || [])[0] || '',
    journal: (m['container-title'] || [])[0] || '', volume: m.volume || '', page: m.page || '',
    'article-number': m['article-number'] || '', type: m.type || '',
    issued: m.issued, 'published-print': m['published-print'], 'published-online': m['published-online'], accepted: m.accepted,
  };
}
async function lookupDoi(doi) {
  const url = CR + '/works/' + encodeURIComponent(doi) + '?mailto=' + encodeURIComponent(MAILTO);
  const res = await crFetch(url, 'doi ' + doi);
  if (res.notFound) return { notFound: true };
  if (res.error) return { error: res.error };
  if (!res.message) return { error: 'empty message' };
  return { rec: crRecordOf(res.message) };
}
const doiNorm = (d) => String(d || '').trim().toLowerCase().replace(/^https?:\/\/(dx\.)?doi\.org\//, '').replace(/^doi:\s*/, '');

// ---------------------------------------------------------------- 候选池与判定
const typePriority = (t) => CITEABLE.has(t) ? 3 : (SECONDARY.has(t) ? 2 : 0);
function evidenceScore(rec) {
  const yy = crYears(rec);
  return (yy.issued || yy.print || yy.online ? 1 : 0) + (String(rec.volume || '').trim() ? 1 : 0) +
    (String(rec.page || '').trim() || String(rec['article-number'] || '').trim() ? 1 : 0);
}
// R4：同一对象优先（存储 DOI 自证），再比类型可信度 / 可比字段数 / 题名相似度
function pickCandidate(pool, storedDoi) {
  let best = null, bestKey = null;
  for (const c of pool) {
    if (!c.rec) continue;
    const denied = DENIED.has(c.rec.type);
    const key = [
      doiNorm(c.rec.doi) === doiNorm(storedDoi) ? 1 : 0,
      denied ? 0 : 1,
      typePriority(c.rec.type),
      evidenceScore(c.rec),
      +c.sim.toFixed(4),
    ];
    const cmp = (a, b) => { for (let i = 0; i < a.length; i++) { if (a[i] !== b[i]) return a[i] - b[i]; } return 0; };
    if (!best || cmp(key, bestKey) > 0) { best = c; bestKey = key; }
  }
  return best;
}
function decide(entry, cand) {
  const f = entry.fields;
  const out = { hard: [], soft: [] };
  const Y = compareYear(f.year, cand.rec);
  const V = compareVolume(f.volume, cand.rec);
  const P = comparePages(f.pages, cand.rec);
  if (Y.status === 'MISMATCH') out.hard.push('year: ' + Y.note);
  if (V.status === 'MISMATCH') out.hard.push('volume: ' + V.note);
  if (P.status === 'MISMATCH') out.hard.push('pages: ' + P.note);
  const okCmp = [['year', Y], ['volume', V], ['pages', P]].filter(([, x]) => x.status === 'OK').length;
  for (const [nm, x] of [['year', Y], ['volume', V], ['pages', P]]) if (x.note) out.soft.push(nm + '/' + x.status + ': ' + x.note);
  // R2：一个字段都没比过的"MATCH"是没有内容的结论。要求 年 + (卷 或 页) 至少两项真比过。
  const substantive = Y.status === 'OK' && (V.status === 'OK' || P.status === 'OK');
  return { ...out, fields: { year: Y, volume: V, pages: P }, okCmp, substantive };
}
// 存储 DOI 独立回查：防"能解析但指向错对象"（本项目被烧的三条都在这里）
function doiCheck(entry, doiRes) {
  const stored = doiNorm(entry.fields.doi);
  if (!stored) return { flag: 'ABSENT', detail: '稿件未存 DOI，无从回查' };
  if (doiRes.notFound) return { flag: 'DOI-404', detail: 'Crossref 对该 DOI 返回 404 —— 存储值根本不存在（历史踩坑 c）' };
  if (doiRes.error) return { flag: 'QUERY-FAILED', detail: 'DOI 回查取数失败：' + doiRes.error };
  const rec = doiRes.rec;
  const s = titleSim(entry.fields.title, rec.title);
  const ja = journalAgree(entry.fields.journal, rec.journal);
  if (s < THRESH) {
    return { flag: 'WRONG-OBJECT', sim: s, journalAgree: ja.agree, rec,
      detail: 'DOI 能解析，但题名不匹配（sim ' + s.toFixed(3) + '）。Crossref 在该 DOI 上的记录是：「' +
        deLatex(rec.title) + '」' + rec.journal + ' ' + (crVol(rec) || '-') + ' ' + (rec.page || rec['article-number'] || '-') +
        '（' + (crYears(rec).print || crYears(rec).issued || '?') + '）—— 正是历史踩坑 a/b 的形状。' };
  }
  const Y = compareYear(entry.fields.year, rec);
  const V = compareVolume(entry.fields.volume, rec);
  const P = comparePages(entry.fields.pages, rec);
  const bad = [['year', Y], ['volume', V], ['pages', P]].filter(([, x]) => x.status === 'MISMATCH');
  return {
    flag: bad.length ? 'FIELD-DISAGREE' : 'OK', sim: s, journalAgree: ja.agree, rec,
    detail: bad.length ? bad.map(([n, x]) => n + '(' + x.note + ')').join('; ')
      : 'DOI 解析到同一对象（题名 sim ' + s.toFixed(3) + '），年/卷/页与稿件一致' + (ja.agree === false ? '；但期刊名两侧差异较大，见证据列' : ''),
  };
}

// ---------------------------------------------------------------- 主流程
(async () => {
  const bibText = fs.readFileSync(BIB, 'utf8');
  const all = parseBib(bibText);
  const entries = all.filter((e) => e.type === 'article' && e.fields.title);

  // ---- 0) 解析率（先自证，再看结论）
  const has = (k) => entries.filter((e) => e.fields[k] != null && String(e.fields[k]).trim() !== '').length;
  const rate = { entriesFound: entries.length, title: has('title'), author: has('author'), journal: has('journal'), year: has('year'), volume: has('volume'), pages: has('pages'), doi: has('doi') };

  // ---- 解析器自证锚点：不是"非空就行"，而是必须提出**对的**值（防空转守卫）
  const anchors = [
    ['kruse2019dna', { year: '2018', volume: '15', pages: '95-115', doi: '10.1021/acs.jctc.8b00643' }],
    ['dion2004', { year: '2004', volume: '92', pages: '246401' }],
    ['sun2018pyscf', { volume: '8', pages: 'e1340', year: '2018' }],
    ['vydrov2009vv10', { year: '2009', volume: '103', pages: '063004' }],
    ['altun2018dlpno', { year: '2018', volume: '14', pages: '919-929' }],
    ['hamada2011c60au', { year: '2011', volume: '83', pages: '245437' }],
  ];
  const byKey = Object.fromEntries(entries.map((e) => [e.key, e]));
  const anchorResults = anchors.map(([k, exp]) => {
    const got = byKey[k] ? byKey[k].fields : null;
    const bad = !got ? ['entry-missing'] : Object.keys(exp).filter((f) => String(got[f] || '').trim() !== exp[f]);
    return { key: k, expected: exp, ok: !bad.length, mismatchedFields: bad };
  });
  const anchorsOk = anchorResults.every((r) => r.ok);

  // ---- 1) 逐条：主题检索 + 存储 DOI 回查，共同构成候选池
  const rows = [];
  for (const e of entries) {
    const f = e.fields;
    const family = firstAuthorFamily(f.author);
    const sr = await searchBibliographic(f.title, family);
    const dr = f.doi ? await lookupDoi(f.doi) : { notFound: false, error: 'none' };
    const dc = doiCheck(e, dr);

    const pool = [];
    const cands = [];
    for (const it of sr.items) {
      const rec = crRecordOf(it);
      let s = titleSim(f.title, rec.title);
      if (rec.altTitle) s = Math.max(s, titleSim(f.title, rec.altTitle));
      cands.push({ doi: rec.doi, type: rec.type, title: deLatex(rec.title), journal: rec.journal, volume: rec.volume,
        page: rec.page, articleNumber: rec['article-number'], years: crYears(rec), sim: +s.toFixed(4),
        usable: !DENIED.has(rec.type) && CITEABLE.has(rec.type) });
      pool.push({ rec, sim: s, via: 'bibliographic-search' });
    }
    if (dc.rec) pool.push({ rec: dc.rec, sim: dc.sim || 0, via: 'stored-doi' });

    const best = pickCandidate(pool, f.doi);
    const bestSim = best ? best.sim : 0;
    const matched = !!best && bestSim >= THRESH && !DENIED.has(best.rec.type);
    let d = { hard: [], soft: [], okCmp: 0, substantive: false, fields: { year: { status: 'N/A' }, volume: { status: 'N/A' }, pages: { status: 'N/A' } } };
    if (matched) d = decide(e, best);

    let verdict;
    if (!matched) {
      verdict = 'UNVERIFIED';
      const topDenied = cands.filter((c) => DENIED.has(c.type) && c.sim >= THRESH).length;
      if (topDenied) d.soft.push('检索返回的高相似候选全是被排除的空壳对象（type=component/peer-review），无卷页年可比');
    } else if (!d.substantive) {
      verdict = 'UNVERIFIED';
      d.soft.push('题名匹配但候选记录缺少可比的卷/页/年（type=' + best.rec.type + '），不构成有内容的核验');
    } else {
      verdict = d.hard.length ? 'MISMATCH' : 'MATCH';
    }
    // DOI 回查发现的硬问题一律计入
    if (dc.flag === 'FIELD-DISAGREE') d.hard.push('via-stored-DOI: ' + dc.detail);
    if (dc.flag === 'DOI-404' || dc.flag === 'WRONG-OBJECT') d.hard.push('stored-DOI: ' + dc.detail);
    if (dc.flag === 'DOI-404' || dc.flag === 'WRONG-OBJECT') verdict = 'MISMATCH';
    if (dc.flag === 'QUERY-FAILED') d.soft.push('stored-DOI: ' + dc.detail);

    const ja = journalAgree(f.journal, matched ? best.rec.journal : '');
    rows.push({
      key: e.key,
      cite: { title: deLatex(f.title), titleRaw: f.title, journal: f.journal, volume: f.volume || null,
        pages: f.pages || null, year: f.year || null, doiStored: f.doi || null, firstAuthorFamily: family },
      crossref: matched ? {
        doi: best.rec.doi, title: deLatex(best.rec.title), titleRawCr: best.rec.title, journal: best.rec.journal,
        volume: best.rec.volume || null, page: best.rec.page || null, articleNumber: best.rec['article-number'] || null,
        yearIssued: crYears(best.rec).issued, yearPrint: crYears(best.rec).print, yearOnline: crYears(best.rec).online,
        type: best.rec.type, comparableFieldCount: evidenceScore(best.rec),
      } : null,
      matchedVia: matched ? best.via : null, similarity: +Number(bestSim).toFixed(4), threshold: THRESH,
      fieldsComparedOK: d ? d.okCmp : 0,
      fieldCheck: d ? { year: d.fields.year.status, volume: d.fields.volume.status, pages: d.fields.pages.status } : null,
      storedDoiCheck: { flag: dc.flag, similarity: dc.sim != null ? +Number(dc.sim).toFixed(4) : null,
        journalAgree: dc.journalAgree == null ? null : dc.journalAgree, detail: dc.detail,
        doiRecordTitle: dc.rec ? deLatex(dc.rec.title) : null,
        doiRecordJournal: dc.rec ? dc.rec.journal : null, doiRecordVolume: dc.rec ? (dc.rec.volume || null) : null,
        doiRecordPage: dc.rec ? (dc.rec.page || dc.rec['article-number'] || null) : null,
        doiRecordYear: dc.rec ? crYears(dc.rec).print || crYears(dc.rec).issued : null },
      journalAgree: ja.agree, journalEvidence: ja.note,
      searchCandidates: cands, searchQuery: sr.query, searchError: sr.error || null,
      verdict, mismatchHard: d ? d.hard : [], notesSoft: d ? d.soft : [],
    });
    process.stderr.write('  . ' + e.key + ' sim=' + Number(bestSim).toFixed(3) + ' fieldsOK=' + (d ? d.okCmp : 0) + ' ' + verdict + '\n');
  }

  // ---- 2) 负控：证明这套比对**能**失败（两任守卫都是空转的教训）
  const matchedRows = rows.filter((r) => r.verdict === 'MATCH');
  const controls = [];
  if (matchedRows.length) {
    const sample = matchedRows.find((r) => r.key === 'becke1988') || matchedRows[0];
    const e = byKey[sample.key];
    const cy = sample.crossref;
    const rec = crRecordOf({
      DOI: cy.doi, title: [cy.titleRawCr || cy.title], 'container-title': [cy.journal],
      volume: cy.volume, page: cy.page, 'article-number': cy.articleNumber, type: cy.type,
      issued: { 'date-parts': [[Number(cy.yearIssued)]] },
      'published-print': cy.yearPrint ? { 'date-parts': [[Number(cy.yearPrint)]] } : undefined,
    });
    const cand = { rec, sim: 1, via: 'control' };
    const base = decide(e, cand);
    const mk = (over) => ({ key: e.key, fields: Object.assign({}, e.fields, over) });
    const c1 = decide(mk({ year: '1901' }), cand);
    const c2 = decide(mk({ volume: '9999' }), cand);
    const c3 = decide(mk({ pages: '1-2' }), cand);
    controls.push(
      { id: 'C0-baseline', desc: '同一条未篡改记录（证明 C1–C3 的差异只来自篡改）', expect: '无硬分歧且≥2字段可比', got: 'hard=' + base.hard.length + ' fieldsOK=' + base.okCmp, detail: base.hard.join(' / '), pass: base.hard.length === 0 && base.substantive },
      { id: 'C1-year-1901', desc: '把 ' + sample.key + ' 的 year 改成 1901 后重跑比对', expect: 'MISMATCH', got: c1.hard.length ? 'MISMATCH' : 'NO-FLAG', detail: c1.hard.join(' / '), pass: c1.hard.length > 0 },
      { id: 'C2-volume-9999', desc: '把 ' + sample.key + ' 的 volume 改成 9999', expect: 'MISMATCH', got: c2.hard.length ? 'MISMATCH' : 'NO-FLAG', detail: c2.hard.join(' / '), pass: c2.hard.length > 0 },
      { id: 'C3-pages-1-2', desc: '把 ' + sample.key + ' 的 pages 改成 1-2', expect: 'MISMATCH', got: c3.hard.length ? 'MISMATCH' : 'NO-FLAG', detail: c3.hard.join(' / '), pass: c3.hard.length > 0 },
    );
  } else {
    controls.push({ id: 'C1-year-1901', desc: '没有 MATCH 记录可用于构造负控', expect: 'MISMATCH', got: 'SKIPPED', pass: false });
  }

  // C4/C5：真实"错对象"——gnomAD 那篇（本项目曾记错成 NumPy 的 DOI）
  const g = await lookupDoi(GNOMAD_DOI);
  if (g.rec) {
    const np = byKey['harris2020numpy'];
    const s = np ? titleSim(np.fields.title, g.rec.title) : null;
    controls.push({ id: 'C4-title-sim-rejects-wrong-object', desc: 'harris2020numpy 题名 vs gnomAD 题名相似度必须 < ' + THRESH,
      expect: 'sim<' + THRESH, got: 'sim=' + (s == null ? 'n/a' : s.toFixed(4)), detail: 'gnomAD 题名：' + deLatex(g.rec.title), pass: s != null && s < THRESH });
    const dcg = np ? doiCheck(np, { rec: g.rec }) : { flag: 'SKIP', detail: 'no numpy entry' };
    controls.push({ id: 'C5-stored-doi-wrong-object', desc: '把 gnomAD 记录冒充 harris2020numpy 的 DOI 回查结果，闸门必须报 WRONG-OBJECT 并印出真题名',
      expect: 'WRONG-OBJECT', got: dcg.flag, detail: dcg.detail, pass: dcg.flag === 'WRONG-OBJECT' });
  } else {
    controls.push({ id: 'C4/C5-gnomad-unavailable', desc: 'gnomAD DOI 取数失败，负控无法构造：' + (g.error || 'unknown'), expect: 'WRONG-OBJECT', got: 'FETCH-FAILED', pass: false });
  }
  // C6：R2/R3 回归控制 —— 空壳对象必须被踢出候选池（上一轮的假警报就是它造成的）
  const shell = {
    doi: '10.1021/acs.jctc.8b00643.s001', type: 'component', title: entries[0].fields.title,
    journal: '', volume: '', page: '', 'article-number': '', issued: null, 'published-print': null, 'published-online': null,
  };
  const peerRec = { doi: '10.14293/x.y.z', type: 'peer-review', title: 'Review of "' + entries[0].fields.title + '"', journal: '', volume: '', page: '', 'article-number': '', issued: { 'date-parts': [[2021]] } };
  const chosen = pickCandidate([
    { rec: shell, sim: 1, via: 'bibliographic-search' },
    { rec: peerRec, sim: 0.93, via: 'bibliographic-search' },
    { rec: crRecordOf({ DOI: '10.1021/acs.jctc.8b00643', title: ['x'], 'container-title': ['Journal of Chemical Theory and Computation'], volume: '15', page: '95-115', type: 'journal-article', issued: { 'date-parts': [[2018, 11, 29]] }, 'published-print': { 'date-parts': [[2019, 1, 8]] } }), sim: 0.9, via: 'stored-doi' },
  ], '10.1021/acs.jctc.8b00643');
  controls.push({ id: 'C6-candidate-ranking-beats-shells', desc: '给候选池同时喂 component(type空壳,sim=1.0) / peer-review(括引题名,sim=0.93) / 存储DOI的journal-article(sim=0.9)，必须选中后者',
    expect: 'journal-article + 存储DOI', got: chosen ? chosen.rec.type + ' + ' + (doiNorm(chosen.rec.doi) === '10.1021/acs.jctc.8b00643' ? 'stored-doi' : 'other-doi') : 'none',
    detail: '被选中的是 ' + (chosen ? chosen.rec.doi + ' [' + chosen.rec.type + ']' : '无'),
    pass: !!chosen && chosen.rec.type === 'journal-article' && doiNorm(chosen.rec.doi) === '10.1021/acs.jctc.8b00643' });
  // C7：页码缩写还原的单元断言（skill 假警报第 1 行）
  const p1 = pageTokens('23578-83'), p2 = pageTokens('4435--41'), p3 = pageTokens('95-115');
  controls.push({ id: 'C7-page-abbrev-expansion', desc: '缩写还原：23578-83 -> 23578/23583、4435--41 -> 4435/4441、95-115 -> 95/115',
    expect: '23583,4441,115', got: [p1.end, p2.end, p3.end].join(','), pass: p1.end === '23583' && p2.end === '4441' && p3.end === '115' });
  // C8：MathML 剥离（R1 回归）
  const hrow = rows.find((r) => r.key === 'hamada2011c60au');
  controls.push({ id: 'C8-mathml-title-normalizes', desc: 'APS 题名里的 MathML 必须被剥掉：hamada2011c60au 相似度应 >= ' + THRESH,
    expect: 'sim>=' + THRESH, got: hrow ? 'sim=' + hrow.similarity.toFixed(3) + ' doiFlag=' + hrow.storedDoiCheck.flag : 'n/a',
    detail: hrow ? deLatex(hrow.storedDoiCheck.doiRecordTitle || '').slice(0, 90) : '',
    pass: !!hrow && hrow.similarity >= THRESH && hrow.storedDoiCheck.flag === 'OK' });
  // C9：解析地板（skill 核心：解析率过低则结论无意义）
  const floorOk = rate.entriesFound === 25 && rate.year >= 20 && rate.volume >= 20 && rate.pages >= 20;
  controls.push({ id: 'C9-parse-floor', desc: '条目数=25 且 year/volume/pages 解析数各 ≥20', expect: '25/≥20/≥20/≥20',
    got: rate.entriesFound + '/' + rate.year + '/' + rate.volume + '/' + rate.pages, pass: floorOk });
  controls.push({ id: 'C10-parser-anchor-values', desc: '解析器必须提出**正确的**字段值（不是只提出非空值）', expect: 'all anchors ok',
    got: anchorResults.map((r) => r.key + (r.ok ? ':OK' : ':BAD(' + r.mismatchedFields.join(',') + ')')).join(' '), pass: anchorsOk });

  const controlsPass = controls.every((c) => c.pass);
  const noFetchFailure = rows.every((r) => !r.searchError) && !apiErrors.some((x) => /final|exhausted|bad json/.test(x));
  const nMatch = rows.filter((r) => r.verdict === 'MATCH').length;
  const nMismatch = rows.filter((r) => r.verdict === 'MISMATCH');
  const nUnverified = rows.filter((r) => r.verdict === 'UNVERIFIED');

  // ---- 3) 写 JSON
  const payload = {
    meta: {
      stamp_utc: TS, rev: 'rev2',
      host_clock_note: '文件名时间戳由宿主 Git Bash `date -u +%Y%m%dT%H%M%SZ` 计算；未采用 WSL 时钟（本机 WSL 钟被观测到会慢几天）',
      generated_from: 'paper/references.bib（只读，本脚本不写 paper/ 下任何文件）',
      method: 'skill reference-metadata-crossref-check：/works?query.bibliographic&rows=3 主题检索 -> 题名归一化字符 4-gram Jaccard ≥0.80 匹配 -> 只比 年/卷/页 硬字段；页码缩写还原；期刊名缩写感知（仅证据列）。另对每条**存储 DOI 独立回查**作对象级交叉核验，两者同入候选池，同对象优先。',
      user_agent: UA, rows: ROWS, threshold: THRESH, delay_ms: DELAY_MS, api_calls: apiCalls, api_errors: apiErrors,
      mailto_source: 'paper/main.md L8 / paper/p2.md L15 / paper/software.md front matter（仓内既有通讯邮箱，未臆造）',
      candidate_rule: 'CITEABLE 类型白名单 + 排除 component/peer-review 等空壳对象；排序键 = [是否等于存储DOI, 类型是否被排除, 类型优先级, 可比字段数, 题名相似度]',
      match_requirement: 'MATCH 必须真比过「年」且「卷或页」之一（≥2 个硬字段），否则记 UNVERIFIED 而不是 MATCH',
      parse_rates: rate, parser_anchor_selftest: anchorResults,
      counts: { entries: entries.length, matched: nMatch, mismatch: nMismatch.length, unverified: nUnverified.length },
      exit_code_meaning: { '0': '方法学有效且无 MISMATCH', '1': '方法学失败（解析地板/负控/取数）——本次结论不可用', '2': '方法学有效，发现 MISMATCH 或 DOI 硬问题' },
      controls,
    },
    rows,
  };
  fs.writeFileSync(OUT_JSON, JSON.stringify(payload, null, 1), 'utf8');

  // ---- 4) 打印摘要（顺序强制：解析率先行 -> 匹配数 -> MISMATCH -> UNVERIFIED）
  const L = [];
  const pad = (s, n) => String(s == null ? '' : s).slice(0, n) + ' '.repeat(Math.max(0, n - String(s == null ? '' : s).length));
  L.push('Crossref 外部元数据核验 —— paper/references.bib 全 ' + entries.length + ' 条   (rev2)');
  L.push('stamp ' + TS + ' (UTC, 宿主 Git Bash 时钟) | UA ' + UA + ' | rows=' + ROWS + ' | 阈值 ' + THRESH + ' | API 调用 ' + apiCalls + ' 次');
  L.push('');
  L.push('='.repeat(100));
  L.push('A. 字段解析率（先自证，再看结论 —— skill 核心纪律）');
  L.push('='.repeat(100));
  L.push('  条目解析出来：' + rate.entriesFound + ' 条 @article');
  for (const k of ['title', 'author', 'journal', 'year', 'volume', 'pages', 'doi']) {
    L.push('  ' + pad(k, 8) + ' ' + rate[k] + '/' + rate.entriesFound + (rate[k] === rate.entriesFound ? '  (全)' : '  <-- 有缺'));
  }
  L.push('  解析器取值自检（防空转守卫，不只是"非空"）：' + (anchorsOk ? 'PASS' : 'FAIL') + ' —— ' + anchorResults.map((r) => r.key + (r.ok ? ' OK' : ' FAIL:' + r.mismatchedFields.join(','))).join(', '));
  L.push('  地板判定：' + (floorOk ? 'PASS（解析率足够，下面的比对有意义）' : 'FAIL（解析率不足，任何"0 mismatch"都不可信）'));
  L.push('');
  L.push('='.repeat(100));
  L.push('B. 高置信匹配（题名相似度 ≥ ' + THRESH + ' 且真比过 ≥2 个硬字段）');
  L.push('='.repeat(100));
  L.push('  MATCH ' + nMatch + ' / MISMATCH ' + nMismatch.length + ' / UNVERIFIED ' + nUnverified.length + '  （合计 ' + entries.length + '）');
  L.push('  匹配来源：检索 ' + rows.filter((r) => r.matchedVia === 'bibliographic-search').length + ' 条 / 存储DOI ' + rows.filter((r) => r.matchedVia === 'stored-doi').length + ' 条');
  L.push('  存储 DOI 对象级回查：OK ' + rows.filter((r) => r.storedDoiCheck.flag === 'OK').length + ' / 异常 ' + rows.filter((r) => r.storedDoiCheck.flag !== 'OK').length +
    '（' + rows.filter((r) => r.storedDoiCheck.flag === 'DOI-404').length + ' 条 404、' + rows.filter((r) => r.storedDoiCheck.flag === 'WRONG-OBJECT').length + ' 条指错对象、' +
    rows.filter((r) => r.storedDoiCheck.flag === 'FIELD-DISAGREE').length + ' 条字段不符、' + rows.filter((r) => r.storedDoiCheck.flag === 'QUERY-FAILED').length + ' 条取数失败）');
  L.push('');
  L.push('='.repeat(100));
  L.push('C. MISMATCH —— 硬字段（年/卷/页）实质不符，或存储 DOI 指错对象/404');
  L.push('='.repeat(100));
  if (!nMismatch.length) L.push('  （无）');
  for (const r of nMismatch) {
    L.push('  * ' + r.key + '   sim=' + r.similarity.toFixed(3) + ' via=' + (r.matchedVia || 'n/a'));
    L.push('      DOI: stored=' + (r.cite.doiStored || '-') + ' | matched=' + (r.crossref ? r.crossref.doi : '-') + ' | DOI回查=' + r.storedDoiCheck.flag);
    L.push('      稿件: year=' + (r.cite.year || '-') + ' vol=' + (r.cite.volume || '-') + ' pages=' + (r.cite.pages || '-') + ' journal=' + (r.cite.journal || '-'));
    if (r.crossref) {
      L.push('      检索/匹配记录: year(issued/print/online)=' + r.crossref.yearIssued + '/' + r.crossref.yearPrint + '/' + r.crossref.yearOnline +
        ' vol=' + (r.crossref.volume || '-') + ' page=' + (r.crossref.page || r.crossref.articleNumber || '-') +
        ' journal=' + (r.crossref.journal || '-') + ' type=' + r.crossref.type);
    }
    if (r.storedDoiCheck.rec || r.storedDoiCheck.doiRecordTitle) {
      L.push('      存储DOI实际指向: 「' + String(r.storedDoiCheck.doiRecordTitle).slice(0, 90) + '」 ' + (r.storedDoiCheck.doiRecordJournal || '-') +
        ' ' + (r.storedDoiCheck.doiRecordVolume || '-') + ' ' + (r.storedDoiCheck.doiRecordPage || '-') + ' (' + (r.storedDoiCheck.doiRecordYear || '?') + ')');
    }
    for (const h of r.mismatchHard) L.push('      -> ' + h);
    L.push('');
  }
  L.push('='.repeat(100));
  L.push('D. UNVERIFIED —— Crossref 无高置信匹配 / 无可比字段。这不是"错"，多为新文未收录或仅预印本');
  L.push('='.repeat(100));
  if (!nUnverified.length) L.push('  （无）');
  for (const r of nUnverified) {
    L.push('  * ' + pad(r.key, 26) + ' 最佳相似度=' + r.similarity.toFixed(3) + ' | 存储DOI回查=' + r.storedDoiCheck.flag);
    L.push('      检索词: ' + r.searchQuery + (r.searchError ? ' [取数错误 ' + r.searchError + ']' : ''));
    if (r.searchCandidates.length) {
      const b = r.searchCandidates[0];
      L.push('      Top1 候选: [' + b.type + '] ' + b.title.slice(0, 70) + ' | ' + (b.journal || '-') + ' ' + (b.volume || '-') + ' ' + (b.page || b.articleNumber || '-') + ' (' + (b.years.print || b.years.issued || '?') + ') sim=' + b.sim);
    } else L.push('      Top1 候选: 无返回');
    L.push('      未判读依据: ' + r.storedDoiCheck.detail.slice(0, 240));
    for (const s of r.notesSoft) L.push('      note: ' + s);
    L.push('');
  }
  L.push('='.repeat(100));
  L.push('E. 全表（稿件值 vs Crossref 值；Y/V/P 列格式 = 稿件值 -> 库值，比对状态见末尾括号）');
  L.push('='.repeat(100));
  L.push('  ' + pad('key', 25) + pad('verdict', 12) + pad('sim', 7) + pad('year st->cr', 21) + pad('vol st->cr', 13) + pad('pages st->cr', 23) + pad('nOK', 4) + 'doi');
  for (const r of rows) {
    const cy = r.crossref;
    const yv = cy ? cy.yearIssued + '/' + (cy.yearPrint || '-') : '-';
    L.push('  ' + pad(r.key, 25) + pad(r.verdict, 12) + pad(r.similarity.toFixed(3), 7) +
      pad((r.cite.year || '-') + ' -> ' + yv, 21) +
      pad((r.cite.volume || '-') + ' -> ' + (cy ? (cy.volume || '-') : '-'), 13) +
      pad((r.cite.pages || '-') + ' -> ' + (cy ? ((cy.page || cy.articleNumber) || '-') : '-'), 23) +
      pad(String(r.fieldsComparedOK), 4) + r.storedDoiCheck.flag);
  }
  L.push('');
  L.push('='.repeat(100));
  L.push('F. 软提示 / 需人工定夺（未计入 MISMATCH）');
  L.push('='.repeat(100));
  let anySoft = false;
  for (const r of rows) {
    const soft = r.notesSoft.filter((s) => !/^year\/OK: $/.test(s));
    if (soft.length || r.journalAgree === false) {
      anySoft = true;
      L.push('  * ' + r.key + ' [' + r.verdict + ']');
      for (const s of soft) L.push('      - ' + s);
      if (r.journalAgree === false) L.push('      - 期刊名缩写感知比对未通过（仅作证据，不判错）：' + r.journalEvidence);
    }
  }
  if (!anySoft) L.push('  （无）');
  L.push('');
  L.push('='.repeat(100));
  L.push('G. 负控 / 自检（证明这套比对能失败，不是恒真守卫）');
  L.push('='.repeat(100));
  for (const c of controls) {
    L.push('  [' + (c.pass ? 'PASS' : 'FAIL') + '] ' + pad(c.id, 34) + ' 期望 ' + c.expect + ' | 实得 ' + c.got);
    if (c.desc) L.push('        说明: ' + c.desc);
    if (c.detail) L.push('        读数: ' + String(c.detail).slice(0, 240));
  }
  L.push('  负控总体: ' + (controlsPass ? 'ALL PASS' : 'SOME FAILED —— 本次结论不可用') + ' | 取数总体: ' + (noFetchFailure ? '全部成功' : '有失败，见 meta.api_errors'));
  L.push('');
  L.push('='.repeat(100));
  L.push('H. 方法局限（明确写出，别把没验的说成验了）');
  L.push('='.repeat(100));
  L.push('  1) 比对只覆盖 年/卷/页 三个硬字段（skill 规定）。作者名单、题名拼写、期号只作证据列，未判错。');
  L.push('  2) 期刊名用缩写感知匹配（首字母序列 / 词集重合 ≥0.6），只报 agree=true/false，不参与 verdict，因为 RSC/IOP 缩写 vs 全名是已知假警报。');
  L.push('  3) ACS/Elsevier 的"在线首发年 ≠ 正刊(print)年"在 F 段给软提示，不自动判 MISMATCH —— 卷-年配对该写哪个年份是编辑决定，不是元数据错。');
  L.push('  4) Crossref 的 type 过滤器不支持 OR（实测 filter=type:journal-article,book-chapter 返回 0 条），');
  L.push('     所以只能拿 rows=3 原始检索结果 + 本地类型白名单；这导致部分条目（题名检索被 SI 空壳占满时）');
  L.push('     的匹配来源是"存储 DOI 精确回查"而不是主题检索，matchedVia 列已逐条标明。');
  L.push('  5) UNVERIFIED 是"未验证"而不是"错"；本核验也不构成"某文献不存在"的论证——只对这 25 条做已知条目核验。');
  L.push('  6) 希腊字母（如 ωB97X-V 的 ω）在归一化两侧同时被丢弃（skill 的"去非字母数字"），不影响这 25 条的判定。');
  L.push('  7) 本脚本只读 paper/references.bib，不修改任何稿件文件，不重生成 MANIFEST.sha256。');

  console.log(L.join('\n'));

  let code;
  if (!floorOk || !anchorsOk || !controlsPass || !noFetchFailure) code = 1;
  else code = nMismatch.length ? 2 : 0;
  process.exitCode = code;
  console.log('\n[EXIT-MEANING] ' + code + ' = ' + payload.meta.exit_code_meaning[String(code)]);
})().catch((e) => {
  console.error('FATAL ' + ((e && e.stack) || e));
  process.exitCode = 1;
});
