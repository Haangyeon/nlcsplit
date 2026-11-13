// 第零波 P0-a：四条"定性先例"的 Crossref 核验与 bib 生成
//
// 为什么是脚本而不是手打 bib：本仓搬错过一次姓名的拼写法（Crossref 用 ı+组合尖音符拼 `Jiřı́`），
// 而这四句是先例断言，作者串与卷页年全靠手抄就会成为新的差错源。条目文本一律从 Crossref 的
// JSON 现场生成，脚本同时把原始返回落盘，谁都能重放。
//
// 判据（沿用本仓既有 bib 核验的口径）：
//   * 已知对象走 DOI 精确回查；主题召回只用来记"没找到"，不用它支撑"没有先例"这种判断
//     （RESEARCH-20260929-lit §9/§11 实测开放索引的主题召回不合格）；
//   * 年份取 published-print（与本仓既有 25 条同口径），print 缺失才退回 issued 并如实标注；
//   * 题名相似度低于阈值即拒绝写入；
//   * 负控一：拿一条真存在但不是本文对象的 DOI（gnomAD 那篇）当靶，题名闸必须拒——
//     守卫不证明自己能失败就等于没守卫；
//   * 负控二（转义自证）：故意喂一个未映射码点，residual() 必须报出来。转义表按码点写，
//     源码里不出现任何一个手打的重音字符——手打它们本身就是差错源。
//   * "查不到"也是结论：第四条（计划记作 Keller 2025 JCP "cannot be decomposed into
//     atom-pair"）多条检索式跑过，命中不了同一对象，就不建条目，只留检索记录进待核清单。
//
// 只写 paper/references.bib（追加），不动 main.md 及其余稿件；不重生成任何 MANIFEST。
// UA 的 mailto 运行时从 paper/main.md 读，读数里只印来源指针，不印账号串（撞 gateB_intranet）。
//
// 跑法：
//   node <本文件>            # 干跑：核验 + 打印将要追加的条目，不落笔
//   node <本文件> --write    # 全部通过才追加进 paper/references.bib
// 读数：stdout 由调用者重定向进 <TS>_p0a_precedents_crossref_summary.out，退出码另存 .out.rc。
'use strict';
const fs = require('fs');
const path = require('path');

// 时间戳从本文件名自己取，免得"档名"和"脚本里写死的 stamp"两处各说一遍、过期一处。
const TS = path.basename(__filename).split('_')[0];
if (!/^\d{8}T\d{6}Z$/.test(TS)) { console.error('档名前缀不是 UTC 时间戳，无法自证：' + TS); process.exit(3); }
const RUN_UTC = new Date().toISOString().replace(/\.\d+Z$/, 'Z');
const ROOT = '<REPO>';
const BIB = path.join(ROOT, 'paper', 'references.bib');
const OUTDIR = path.join(ROOT, 'evidence', 'bib_provenance');
const RAW_JSON = path.join(OUTDIR, TS + '_p0a_precedents_crossref_result.json');
const CR = 'https://api.crossref.org';
const THRESH = 0.80;
const WRITE = process.argv.includes('--write');

const mainTxt = fs.readFileSync(path.join(ROOT, 'paper', 'main.md'), 'utf8');
const MAILTO_HIT = mainTxt.match(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/);
if (!MAILTO_HIT) { console.error('paper/main.md 里没读到通讯邮箱：不臆造一个顶上'); process.exit(3); }
const MAILTO = MAILTO_HIT[0];
const UA = 'refcheck/1.0 (mailto:' + MAILTO + ')';

// 三个已知对象：DOI 是计划/交接件给的线索，一律回查后才落笔
const TARGETS = [
  { key: 'lehtola2022illbehaved', doi: '10.1063/5.0121187',
    expectTitle: 'Many recent density functionals are numerically ill-behaved',
    claim: '近期泛函在常用数值求积下能量收敛得极慢（Lehtola & Marques, JCP 157, 174114 (2022)）' },
  { key: 'andres2019ninequestions', doi: '10.1002/jcc.26003',
    expectTitle: 'Nine questions on energy decomposition analysis',
    claim: 'EDA 分区方案之所以多元并存，是因为许多化学概念的定义本就不精确（Andres 等 30 人，JCC 40, 2248 (2019)）' },
  { key: 'rezac2016bench', doi: '10.1021/acs.chemrev.5b00526',
    expectTitle: 'Benchmark Calculations of Interaction Energies in Noncovalent Complexes and Their Applications',
    claim: '计划记作"Chem. Rev. 2016：atomic contributions is not well-defined"的那条，按卷页 116, 5038-5071 '
      + '定位到 Rezac & Hobza 的这篇综述。原句是否逐字如此本脚本无从判（Crossref 无摘要、ACS 全文不在本机）：'
      + '只能引"这篇综述里的这段讨论"，不得加引号当逐字引用' },
];

const UNLOCATED = {
  asStated: 'Keller 2025 JCP：能量"cannot be decomposed into atom-pair contributions"',
  probeTitle: 'cannot be decomposed into atom-pair contributions',
  queries: [
    'energy decomposition atom-pair contributions',
    'cannot be decomposed into atom-pair contributions',
    'decomposition into atom-pair contributions is not possible',
    'pairwise additive energy decomposition not unique',
  ],
  authorFilters: ['Keller', 'Keller, Stefan'],
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let apiCalls = 0;
const apiErrors = [];

async function crGet(url, label) {
  for (const wait of [0, 2000, 5000]) {
    if (wait) await sleep(wait);
    await sleep(300);
    apiCalls++;
    let r;
    try {
      r = await fetch(url, { headers: { 'User-Agent': UA, Accept: 'application/json' },
        signal: AbortSignal.timeout(45000) });
    } catch (e) { apiErrors.push(label + ' network: ' + String(e.message || e).slice(0, 120)); continue; }
    if (r.status === 404) return { notFound: true };
    if (r.status === 429 || r.status >= 500) { apiErrors.push(label + ' HTTP ' + r.status); continue; }
    if (!r.ok) { apiErrors.push(label + ' HTTP ' + r.status + ' (final)'); return { error: 'HTTP ' + r.status }; }
    try { return { message: (await r.json()).message }; }
    catch (e) { apiErrors.push(label + ' bad json: ' + e.message); }
  }
  return { error: 'exhausted retries' };
}

// ---------------------------------------------------------------- 题名归一化与相似度
function deLatex(s) {
  return String(s == null ? '' : s).replace(/<[^>]*>/g, ' ').replace(/&[a-z#0-9]+;/gi, ' ')
    .replace(/\s+/g, ' ').trim();
}
function norm(s) {
  return deLatex(s).normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/[^a-z0-9]/g, '');
}
function grams(s, n) { const g = new Set(); if (s.length < n) { if (s) g.add(s); return g; }
  for (let i = 0; i + n <= s.length; i++) g.add(s.slice(i, i + n)); return g; }
function titleSim(a, b) {
  const x = norm(a), y = norm(b);
  if (!x || !y) return 0;
  if (x === y) return 1;
  if (x.includes(y) || y.includes(x)) return 0.93;
  const A = grams(x, 4), B = grams(y, 4);
  let inter = 0; for (const v of A) if (B.has(v)) inter++;
  return inter / (A.size + B.size - inter);
}

// ---------------------------------------------------------------- Crossref -> BibTeX
// 码点 -> LaTeX 转义（源码里不出现手打的重音字符；写它们本身就是差错源）。
const TEX_MAP = {
  0x00E1: "\\'{a}", 0x00C1: "\\'{A}",
  0x00E9: "\\'{e}", 0x00C9: "\\'{E}",
  0x00ED: "\\'{i}", 0x00CD: "\\'{I}",
  0x00F3: "\\'{o}", 0x00D3: "\\'{O}",
  0x00FA: "\\'{u}", 0x00DA: "\\'{U}",
  0x00E0: "\\`{a}", 0x00C0: "\\`{A}",
  0x00E8: "\\`{e}", 0x00C8: "\\`{E}",
  0x00EC: "\\`{i}", 0x00CC: "\\`{I}",
  0x00F2: "\\`{o}", 0x00D2: "\\`{O}",
  0x00F9: "\\`{u}", 0x00D9: "\\`{U}",
  0x00E2: "\\\\^{a}", 0x00C2: "\\\\^{A}",
  0x00EA: "\\\\^{e}", 0x00CA: "\\\\^{E}",
  0x00EE: "\\\\^{i}", 0x00CE: "\\\\^{I}",
  0x00F4: "\\\\^{o}", 0x00D4: "\\\\^{O}",
  0x00FB: "\\\\^{u}", 0x00DB: "\\\\^{U}",
  0x00C4: '\\"{A}', 0x00D6: '\\"{O}', 0x00DC: '\\"{U}',
  0x015A: "\\'{S}", 0x015B: "\\'{s}",
  0x0154: "\\'{R}", 0x0155: "\\'{r}",
  0x0139: "\\'{L}", 0x013A: "\\'{l}",
  0x017D: '\\v{Z}', 0x017E: '\\v{z}',
  0x010C: '\\v{C}', 0x010D: '\\v{c}',
  0x0158: '\\v{R}', 0x0159: '\\v{r}',
  0x0160: '\\v{S}', 0x0161: '\\v{s}',
  0x010E: '\\v{N}', 0x010F: '\\v{n}',
  0x0141: '\\L{}', 0x0142: '\\l{}',
  0x00D7: 'x', 0x00F7: '/',
};
// U+2010 HYPHEN / U+2011 NON-BREAKING / U+2012 FIGURE DASH / U+2013 EN / U+2014 EM /
// U+2212 MINUS / U+00AD SOFT：Crossref 把 Carbo-Dorca 这类姓用 U+2010 拼，只列一个字符会漏。
const DASH = '[\\u2010-\\u2015\\u2212\\u00ad]';
const SPACE = '[\\u00a0\\u2007\\u202f\\u3000]';

function tex(s) {
  let t = deLatex(s).replace(new RegExp(DASH, 'g'), '-').replace(new RegExp(SPACE, 'g'), ' ');
  t = t.normalize('NFC');
  let outStr = '';
  for (const ch of t) {
    const rep = TEX_MAP[ch.codePointAt(0)];
    outStr += rep === undefined ? ch : rep;
  }
  return outStr;
}
// 转义自证：还剩非 ASCII 就是错，码点印出来，别让它静默进 .bib 等 biber 才炸。
function residual(s) {
  return [...new Set(String(s).split('').filter((c) => c.charCodeAt(0) > 127)
    .map((c) => 'U+' + c.codePointAt(0).toString(16).toUpperCase().padStart(4, '0')))].join(',');
}
function bibTitle(s) { return '{' + tex(s) + '}'; }   // 整串护起来，保护大小写与专名

function yearOf(m) {
  const p = m['published-print'] && m['published-print']['date-parts'] && m['published-print']['date-parts'][0][0];
  const i = m.issued && m.issued['date-parts'] && m.issued['date-parts'][0][0];
  return { print: p || null, issued: i || null, used: p || i || null,
    note: p ? 'published-print' : (i ? 'issued（该记录没有 print 日期）' : '无日期') };
}
function bibEntry(key, m) {
  const authors = (m.author || []).map((a) => [tex(a.given || ''), tex(a.family || '')]
    .filter(Boolean).join(' ')).join(' and ');
  const y = yearOf(m);
  const pages = m.page ? tex(m.page) : (m['article-number'] ? tex(m['article-number']) : '');
  const lines = [
    '@article{' + key + ',',
    '  author  = {' + authors + '},',
    '  title   = ' + bibTitle((m.title || [''])[0]) + ',',
    '  journal = {' + tex((m['container-title'] || [])[0]) + '},',
  ];
  if (m.volume) lines.push('  volume  = {' + tex(m.volume) + '},');
  if (pages) lines.push('  pages   = {' + pages + '},');
  if (y.used) lines.push('  year    = {' + y.used + '},');
  lines.push('  doi     = {' + m.DOI + '},');
  lines.push('}');
  const text = lines.join('\n');
  return { text, year: y, nAuthors: (m.author || []).length,
    journalArticle: m.type === 'journal-article', pages, resid: residual(text) };
}

// ---------------------------------------------------------------- 主流程
(async () => {
  const raw = {};
  const rows = [];
  for (const t of TARGETS) {
    const res = await crGet(CR + '/works/' + encodeURIComponent(t.doi) + '?mailto=' + encodeURIComponent(MAILTO), 'doi ' + t.doi);
    raw[t.doi] = res.message || res;
    const m = res.message;
    if (!m) { rows.push({ ...t, verdict: 'FETCH-FAILED', detail: res.error || '404' }); continue; }
    const sim = titleSim(t.expectTitle, (m.title || [])[0]);
    const y = yearOf(m);
    const e = bibEntry(t.key, m);
    const ok = sim >= THRESH && e.journalArticle && y.used && (m.volume || e.pages) && !e.resid;
    rows.push({ ...t, verdict: ok ? 'ACCEPT' : 'REJECT', sim: +sim.toFixed(4), doi: m.DOI,
      crossrefTitle: deLatex((m.title || [])[0]), journal: deLatex((m['container-title'] || [])[0]),
      type: m.type, volume: m.volume || null, pages: e.pages || null, yearUsed: y.used,
      yearPrint: y.print, yearIssued: y.issued, yearBasis: y.note, nAuthors: e.nAuthors,
      citedBy: m['is-referenced-by-count'], resid: e.resid, entry: e.text });
  }

  // 负控一：真存在但不是本文对象的 DOI，必须被题名闸拒掉
  const NEG_DOI = '10.1038/s41586-020-2308-7';
  const neg = await crGet(CR + '/works/' + encodeURIComponent(NEG_DOI) + '?mailto=' + encodeURIComponent(MAILTO), 'negative-control');
  raw[NEG_DOI] = neg.message || neg;
  const negSim = neg.message ? titleSim(TARGETS[0].expectTitle, (neg.message.title || [])[0]) : null;
  const negPass = negSim != null && negSim < THRESH;

  // 负控二：转义自证。U+0117（带点的 e）刻意不进表，residual() 必须把它报出来
  const fake = bibEntry('selftest', { DOI: 'x', type: 'journal-article',
    author: [{ given: 'A', family: 'Z\u0117' }], title: ['T'], 'container-title': ['J'],
    volume: '1', page: '1', issued: { 'date-parts': [[2000]] } });
  const escapePass = fake.resid === 'U+0117';

  // 未定位那条：检索式全跑一遍，命中结果记进档，判"未定位"
  const unlocated = [];
  for (const q of UNLOCATED.queries) {
    const url = CR + '/works?rows=5&mailto=' + encodeURIComponent(MAILTO) + '&query.bibliographic=' + encodeURIComponent(q);
    const r = await crGet(url, 'search ' + q);
    raw['search:' + q] = r.message ? { total: r.message['total-results'],
      items: (r.message.items || []).map((it) => ({ DOI: it.DOI, type: it.type,
        title: (it.title || [])[0], container: (it['container-title'] || [])[0],
        volume: it.volume, page: it.page, year: it.issued && it.issued['date-parts'][0][0] })) } : r;
    const items = (r.message && r.message.items) || [];
    const scored = items.map((it) => ({ doi: it.DOI, type: it.type,
      sim: +titleSim(UNLOCATED.probeTitle, (it.title || [])[0]).toFixed(3),
      title: deLatex((it.title || [])[0] || '').slice(0, 72) })).sort((a, b) => b.sim - a.sim);
    unlocated.push({ via: 'bibliographic', q, best: scored[0] || null, nItems: items.length });
  }
  for (const a of UNLOCATED.authorFilters) {
    const url = CR + '/works?rows=8&mailto=' + encodeURIComponent(MAILTO) +
      '&query.author=' + encodeURIComponent(a) +
      '&query.bibliographic=' + encodeURIComponent('energy decomposition atom-pair') +
      '&filter=' + encodeURIComponent('type:journal-article,from-pub-date:2023-06-01');
    const r = await crGet(url, 'author ' + a);
    raw['author:' + a] = r.message ? { total: r.message['total-results'],
      items: (r.message.items || []).map((it) => ({ DOI: it.DOI, title: (it.title || [])[0],
        container: (it['container-title'] || [])[0], year: it.issued && it.issued['date-parts'][0][0] })) } : r;
    const items = (r.message && r.message.items) || [];
    const scored = items.map((it) => ({ doi: it.DOI,
      sim: +titleSim(UNLOCATED.probeTitle, (it.title || [])[0]).toFixed(3),
      title: deLatex((it.title || [])[0] || '').slice(0, 72) })).sort((a, b) => b.sim - a.sim);
    unlocated.push({ via: 'author', q: a, best: scored[0] || null, nItems: items.length });
  }

  fs.writeFileSync(RAW_JSON, JSON.stringify({ meta: {
    stamp_utc: TS, run_utc: RUN_UTC,
    stamp_note: 'stamp 取自本档名前缀；run_utc 是本次真正取数的 UTC 时刻，重放时以 run_utc 为准',
    ua_note: 'UA = refcheck/1.0 (mailto:<通讯邮箱，取自 paper/main.md 第 8 行>；本档不写账号串)',
    api_calls: apiCalls, api_errors: apiErrors, threshold: THRESH,
    year_basis: 'published-print 优先（与本仓既有 25 条同口径），无 print 才退回 issued 并标注',
    escape_selftest: { unmapped_codepoint: 'U+0117', got: fake.resid, pass: escapePass },
    write_mode: WRITE ? 'write' : 'dry-run' }, raw }, null, 1), 'utf8');

  const L = [];
  L.push('第零波 P0-a —— 四条定性先例的 Crossref 回查与 bib 生成（' + (WRITE ? '已落笔' : '干跑，未落笔') + '）');
  L.push('stamp ' + TS + ' (UTC，取自档名) | 本次取数 ' + RUN_UTC + ' | 阈值 ' + THRESH +
    ' | API ' + apiCalls + ' 次 | 原始返回 → ' + path.basename(RAW_JSON));
  L.push('');
  L.push('='.repeat(96));
  L.push('A. 逐条回查');
  L.push('='.repeat(96));
  let allAccept = true;
  for (const r of rows) {
    if (r.verdict !== 'ACCEPT') allAccept = false;
    L.push('  [' + r.verdict + '] ' + r.key + '   sim=' + (r.sim == null ? 'n/a' : r.sim));
    L.push('      断言: ' + r.claim);
    L.push('      DOI: ' + r.doi + '  type=' + r.type + '  ' + (r.journal || '-') +
      ' v' + (r.volume || '-') + ' p' + (r.pages || '-'));
    L.push('      年份: ' + (r.yearUsed || '-') + '（判据 ' + (r.yearBasis || '-') +
      '；print=' + (r.yearPrint || '-') + ' issued=' + (r.yearIssued || '-') + '）');
    L.push('      作者 ' + (r.nAuthors || 0) + ' 人 | 转义残留: ' + (r.resid || '无') +
      ' | Crossref 被引 ' + (r.citedBy == null ? '-' : r.citedBy) + ' 次（本次读数，会随时间变，别当定值引）');
    if (r.verdict === 'REJECT') L.push('      拒绝原因: sim < 阈值 / 非 journal-article / 缺卷页年 / 有转义残留');
  }
  L.push('');
  L.push('='.repeat(96));
  L.push('B. 计划 §五 待核那条"被引 63"');
  L.push('='.repeat(96));
  const lr = rows.find((r) => r.key === 'lehtola2022illbehaved');
  L.push('  计划里那个 63 来自死会话的网页检索，没有落原始证据。Crossref 本次 is-referenced-by-count = '
    + (lr && lr.citedBy) + '。两个数口径不同，正文不许引"被引 N 次"，除非连口径和读数日期一起写。');
  L.push('');
  L.push('='.repeat(96));
  L.push('C. 第四条（计划记作 Keller 2025 JCP）—— 未定位，不建条目');
  L.push('='.repeat(96));
  L.push('  原样断言: ' + UNLOCATED.asStated);
  for (const u of unlocated) {
    L.push('  [' + u.via + '] ' + u.q + '   返回 ' + u.nItems + ' 条');
    if (u.best) L.push('        最佳候选 sim=' + u.best.sim + ' [' + (u.best.type || '?') + '] '
      + u.best.title + ' (' + u.best.doi + ')');
    else L.push('        无返回');
  }
  L.push('  结论: Crossref 上没定位到这个对象。它留在待核清单里，不进 bib、不进正文；'
    + '要引这条得先由作者给出可核对的出处（卷/页/DOI 之一）。');
  L.push('');
  L.push('='.repeat(96));
  L.push('D. 负控 / 自证（守卫必须能失败）');
  L.push('='.repeat(96));
  L.push('  [' + (negPass ? 'PASS' : 'FAIL') + '] D1 题名闸：拿 ' + NEG_DOI + '（gnomAD，真存在但错对象）冒充靶条目，'
    + '必须拒 → sim=' + (negSim == null ? 'n/a' : negSim.toFixed(4)) + '（阈值 ' + THRESH + '）');
  L.push('  [' + (escapePass ? 'PASS' : 'FAIL') + '] D2 转义自证：故意喂未映射码点 U+0117，'
    + 'residual() 必须报出来 → 实报 "' + (fake.resid || '(空)') + '"');
  L.push('');
  L.push('='.repeat(96));
  L.push('E. 将要追加进 paper/references.bib 的条目');
  L.push('='.repeat(96));
  for (const r of rows) if (r.entry) { L.push(r.entry); L.push(''); }
  console.log(L.join('\n'));

  const gatesOk = allAccept && negPass && escapePass;
  if (WRITE) {
    if (!gatesOk) { console.log('\n[不落笔] 核验/负控未全过，references.bib 保持原样。'); process.exitCode = 1; return; }
    const before = fs.readFileSync(BIB, 'utf8');
    const keys = rows.map((r) => r.key);
    if (keys.some((k) => before.includes('@article{' + k + ','))) {
      console.log('\n[不落笔] references.bib 里已有同名键，拒绝重复追加。'); process.exitCode = 1; return;
    }
    const block = '\n' + rows.map((r) => r.entry).join('\n') + '\n';
    const after = before.replace(/\s*$/, '\n') + block;
    fs.writeFileSync(BIB, after, 'utf8');
    console.log('\n[已落笔] 追加 ' + keys.length + ' 条：' + keys.join(', '));
    console.log('  追加前 @ 行数 ' + (before.match(/^@/gm) || []).length + ' → 追加后 '
      + (after.match(/^@/gm) || []).length);
    process.exitCode = 0;
    return;
  }
  process.exitCode = gatesOk ? 0 : 1;
  console.log('\n[EXIT] ' + process.exitCode + ' = 0 全部通过 / 1 有拒绝或负控未触发');
})().catch((e) => { console.error('FATAL ' + ((e && e.stack) || e)); process.exitCode = 1; });
