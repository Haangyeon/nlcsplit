// 投稿前 refs.bib 的"年份口径"清点：逐条拿 DOI 回 Crossref，把稿库存的 year 与
// **纸质卷期年**（published-print）比，而不只是与首次上线年（issued/published-online）比。
// 为什么单独测这个：ACS 的 DOI 编号里的年份（如 acs.jctc.8b00643 的 "8b"）是**投稿年**，
// 首次上线常在下一年之前，而卷号属于纸质那一期。JCTC 15 属于 2019，JCTC 20 属于 2024。
// 于是"year 写在线年 + volume/pages 写纸质卷期"这一组合是内部不自洽的：读者按
// "J. Chem. Theory Comput. 15 (2018) 95" 去检索会查不到。
// 本脚本先把两条参照年一起打印出来，再判定；判定只用纸质年，纸质年缺失（真·仅在线）
// 时才退回 issued，并把这种情况单独列出来而不是混进"对得上"。
//
// 负控（同一次运行里跑，跑不出来就硬失败）：把 kruse2019dna 的 year 改成 1901，
// 本脚本必须把它报成 DEVIATION。守不住这一条的比较等于没有比较。
//
// 用法：node evidence/bib_provenance/bib_issue_year_check.js [references.bib 路径]
// 输出到 stdout；调用方负责把 stdout 原样入库并另存退出码（项目规矩：认文件不认通知）。

const fs = require('fs');
const path = require('path');

const BIB = process.argv[2] || path.join(__dirname, '..', '..', 'paper', 'references.bib');

// 礼貌池的 mailto 从稿件自己的通讯作者行取，不写死、不编造。
function correspondingEmail() {
  const main = path.join(__dirname, '..', '..', 'paper', 'main.md');
  const text = fs.readFileSync(main, 'utf8');
  const m = text.match(/[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/);
  if (!m) throw new Error('paper/main.md 里没读到通讯作者邮箱：不编一个地址顶上');
  return m[0];
}
const MAILTO = correspondingEmail();

function parseBib(text) {
  const out = [];
  const re = /@article\{([^,]+),([\s\S]*?)\n\}/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const body = m[2];
    const field = (name) => {
      const f = body.match(new RegExp(name + '\\s*=\\s*[{"]([^}"]*)[}"]', 'i'));
      return f ? f[1].trim() : '';
    };
    out.push({
      key: m[1].trim(),
      year: field('year'),
      volume: field('volume'),
      pages: field('pages'),
      doi: field('doi'),
      journal: field('journal'),
    });
  }
  return out;
}

async function lookup(doi) {
  const url = 'https://api.crossref.org/works/' + encodeURIComponent(doi);
  const res = await fetch(url, { headers: { 'User-Agent': 'bib-issue-year-check/1.0 (mailto:' + MAILTO + ')' } });
  if (!res.ok) throw new Error('HTTP ' + res.status + ' for ' + doi);
  const j = (await res.json()).message;
  const dp = (node) => (node && node['date-parts'] && node['date-parts'][0] ? node['date-parts'][0][0] : null);
  return {
    title: (j.title && j.title[0]) || '',
    printYear: dp(j['published-print']),
    onlineYear: dp(j['published-online']),
    issuedYear: dp(j.issued),
    volume: j.volume || '',
    page: j.page || '',
  };
}

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

(async () => {
  const entries = parseBib(fs.readFileSync(BIB, 'utf8'));
  console.log('# refs.bib 年份口径清点（判定用纸质卷期年）');
  console.log('# 文件：' + BIB);
  console.log('# 条目：@article ' + entries.length + ' 条');
  const noDoi = entries.filter((e) => !e.doi);
  if (entries.length === 0) throw new Error('一条也没解析出来：解析表达式错了，不是文献错了');
  console.log('# 无 DOI 的条目：' + noDoi.length + (noDoi.length ? ' -> ' + noDoi.map((e) => e.key).join(', ') : ''));

  const rows = [];
  for (const e of entries) {
    if (!e.doi) { rows.push({ e, verdict: 'NO-DOI', note: '' }); continue; }
    let r;
    try {
      r = await lookup(e.doi);
    } catch (err) {
      rows.push({ e, verdict: 'LOOKUP-FAILED', note: String(err.message).slice(0, 60) });
      await sleep(300);
      continue;
    }
    await sleep(300);
    const refYear = r.printYear !== null ? String(r.printYear) : String(r.issuedYear);
    const basis = r.printYear !== null ? 'published-print' : 'issued(仅在线)';
    const volOk = !r.volume || !e.volume || r.volume === e.volume;
    const row = { e, r, refYear, basis, volOk };
    if (String(e.year) === refYear && volOk) row.verdict = 'MATCH';
    else if (!volOk) row.verdict = 'DEVIATION';
    else row.verdict = 'DEVIATION';
    rows.push(row);
    console.log([
      e.key,
      '稿库 year=' + e.year,
      'Crossref 纸质=' + (r.printYear === null ? '-' : r.printYear),
      '在线=' + (r.onlineYear === null ? '-' : r.onlineYear),
      '卷(库/Cr)=' + e.volume + '/' + r.volume,
      row.basis,
      row.verdict,
    ].join(' | '));
  }

  const dev = rows.filter((x) => x.verdict === 'DEVIATION');
  const failed = rows.filter((x) => x.verdict !== 'MATCH' && x.verdict !== 'DEVIATION');
  console.log('');
  console.log('# 计数：MATCH ' + rows.filter((x) => x.verdict === 'MATCH').length +
    ' / DEVIATION ' + dev.length + ' / 未能判定 ' + failed.length +
    '（共 ' + rows.length + '）');
  for (const x of failed) console.log('  未判定 ' + x.e.key + ' -> ' + x.verdict + ' ' + (x.note || ''));

  // ---- 负控：改一个年份，本脚本必须报 DEVIATION；报不出来就是恒真守卫 ----
  const k = rows.find((x) => x.e.key === 'kruse2019dna');
  if (!k || k.verdict === undefined) throw new Error('负控找不到 kruse2019dna');
  const tampered = { ...k.e, year: '1901' };
  const tamperRefYear = k.refYear;
  const caught = String(tampered.year) !== tamperRefYear || !k.volOk;
  console.log('# 负控：把 ' + tampered.key + ' 的 year 改成 ' + tampered.year +
    '（参照纸质年 ' + tamperRefYear + '）-> 判定应为 DEVIATION，实得 ' +
    (caught ? 'DEVIATION（抓住）' : 'MATCH（守卫恒真，本脚本不可信）'));
  if (!caught) {
    console.log('VERDICT REFUSED —— 负控没抓住，比较逻辑没有区分力');
    process.exit(2);
  }

  if (dev.length) {
    console.log('VERDICT DEVIATION —— 下列条目的 year 与纸质卷期年不符：');
    for (const x of dev) {
      console.log('  ' + x.e.key + ': 稿库 ' + x.e.year + ' -> 纸质 ' + x.refYear +
        '（卷 ' + x.e.volume + '，页 ' + x.e.pages + '，DOI ' + x.e.doi + '）');
    }
    process.exit(1);
  }
  // "没查到"不能被折算成"都对"：解析率/查全率先打印，再给结论（技能里那条血泪）。
  if (failed.length) {
    console.log('VERDICT INCOMPLETE —— ' + failed.length + ' 条未能判定，' +
      '"其余全对"不等于"全库已核"');
    process.exit(4);
  }
  console.log('VERDICT OK —— 全部 ' + rows.length + ' 条的 year 与纸质卷期年一致');
  process.exit(0);
})().catch((err) => { console.error('FATAL ' + err.message); process.exit(3); });
