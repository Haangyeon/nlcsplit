/* 占比闸门：把包自己那条规则推广到所有文字材料上。
 *
 * 规则来源：`nlcsplit/step_f_dispersion.py` —— 当 dxc == 0 或 |dnlc/dxc| > 2 时，
 * 打印"分母抵消 ⇒ 不报占比，只报两个绝对项"。理由是分母是两项相消后的小余量，
 * 此时百分数没有意义（甲烷二聚体：非局域 −0.517 对半局域余项 +0.285，
 * 比值算得出 222.8%，但那个数说的是"相消"，不是"占比"）。
 *
 * 这条规则原先只在代码里执行。2026-10-01 一次性抓出三处文字材料违反它：
 * 主篇结论段、software.md §4，以及我当天刚写进 README 的一句 —— 三处都在报 "223%"，
 * 而同一篇主篇的 §3.2 已经明确写着"报 223% 等于给一个分母会抵消的比做广告"。
 * 所以把它做成闸门，而不是记成一句"下次注意"。
 *
 * 判据两条：
 *   (1) 占比语境里出现 ≥200% 的百分数 ⇒ FAIL（唯一会走到这个量级的就是被抵消的甲烷行）；
 *   (2) 占比语境里出现的每一个百分数，必须等于 step_h.json 里某一行现算的值 ±1 个百分点，
 *       否则 FAIL（防"数字还在，指的东西换了"）。
 * 双向自证：--files= 可以喂一个故意写错的 fixture，它必须响；喂正确文本必须不响。
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const argv = process.argv.slice(2);
const filesFlag = (argv.find(a => a.startsWith('--files=')) || '').slice(8);
// 默认名单是**母仓**的六份材料。本文件现在随包发布（导出器把它列进 TOOLS，因为它就是
// 闸门 W 的被调用方），而在发布副本里 paper/** 与 MAIN-skeleton.md 按设计不存在——
// 直接照旧名单跑会得到"5 份读不到"，那是正确但无意义的红。所以：名单齐全用母仓名单，
// 否则退到发布形态里真有的两份。**这个退化不放松任何判据**：退化后仍有读不到的文件时，
// 下面 skippedFiles 那条 FAIL(0) 照旧触发；一份都不在 ⇒ 分母为 0，同样算失败。
const SRC_LIST = ['paper/main.md', 'paper/p2.md', 'paper/software.md', 'paper/joss/paper.md',
  'README.md', 'MAIN-skeleton.md'];
const SHIPPED_LIST = ['README.md', 'docs/tables_and_provenance.md', 'paper/joss/paper.md'];
const here = (r) => fs.existsSync(path.isAbsolute(r) ? r : path.join(ROOT, r));
const DEFAULT_LIST = SRC_LIST.every(here) ? SRC_LIST : SHIPPED_LIST;
if (!SRC_LIST.every(here)) console.error(`默认名单退化：用发布形态的 ${DEFAULT_LIST.length} 份材料`);
const DOCS = (filesFlag || DEFAULT_LIST.join(','))
  .split(',').map(s => s.trim()).filter(Boolean);
const SHARE_WORDS = /占比|份额|占\s*|share|proportion|of\s*d?E_xc|of\s*ΔE_xc|of\s*the\s*exchange-correlation/i;

// ---- 真值：从工件现算，不从任何文稿取 -------------------------------
const step = JSON.parse(fs.readFileSync(path.join(ROOT, 'nlcsplit/logs/step_h.json'), 'utf8'));
const rows = step.rows.map(r => {
  const semi = r.dxc - r.dnlc;
  const cancel = r.dxc === 0 || Math.abs(r.dnlc / r.dxc) > 2.0;
  return { name: r.name, natm: r.natm, dnlc: r.dnlc, dxc: r.dxc, semi,
           cancel, share_pct: cancel ? null : 100 * r.dnlc / r.dxc };
});
const quotable = rows.filter(r => !r.cancel).map(r => r.share_pct);
// 体系名 → 该行自己的占比。必须按"这行说的是哪个体系"比对：
// 只问"有没有哪个体系等于这个数"会让"水占 45%"通过（45.5% 恰好是苯···NH3 的占比），
// 而错位恰恰是本项目反复踩的那类错。
const shareOf = new Map(rows.filter(r => !r.cancel).map(r => [r.name, r.share_pct]));
const EN_NAME = {
  "水二聚体":   [/water\s+dimer/i, /\(H2O\)\s*2/i],
  "氨二聚体":   [/ammonia\s+dimer/i, /\(NH3\)\s*2/i],
  "甲烷二聚体": [/methane\s+dimer/i, /\(CH4\)\s*2/i],
  "苯二聚体(A)": [/benzene\s+dimer\s*\(?\s*a\s*\)?/i, /sandwich/i],
  "苯二聚体(B)": [/benzene\s+dimer\s*\(?\s*b\s*\)?/i, /parallel[- ]displaced/i],
  "苯-水":     [/benzene[.\u2026\u00b7]{1,3}\s*water/i, /benzene[.\u2026\u00b7]{1,3}\s*h2o/i],
  "苯-氨":     [/benzene[.\u2026\u00b7]{1,3}\s*ammonia/i, /benzene[.\u2026\u00b7]{1,3}\s*nh3/i],
  "苯-甲烷":   [/benzene[.\u2026\u00b7]{1,3}\s*methane/i, /benzene[.\u2026\u00b7]{1,3}\s*ch4/i],
};
// 中文名直接按字面找（写稿时两种都会用），英文名走上面的正则。
// 苯二聚体 A/B 必须分开认：只写 "benzene dimer" 时认不到是哪一行，
// 那时候宁可报"认不出"也不要挑一个数去比——挑错数比不检查更坏。
function namedSystems(line) {
  const hits = [];
  for (const [zh, res] of Object.entries(EN_NAME)) {
    if (line.includes(zh) || res.some(re => re.test(line))) hits.push(zh);
  }
  // "benzene dimer" 裸现且没带 A/B：同时排除两个 A/B 断言，交给 unattributed
  if (!hits.length && /benzene\s+dimer/i.test(line)) return [];
  return [...new Set(hits)];
}
const cancelled = rows.filter(r => r.cancel);
if (!cancelled.length) {
  console.error('注意：本次没有任何"分母抵消"的行，判据 (1) 无从生效（不是通过，是无对象）。');
}

// 具名豁免：同一行带 `share-rule-exempt: <理由>` 注释的，可以出现被禁的百分数——
// 唯一合法的理由是"这个数字正是被撤回的对象"（主篇 §3.2 需要写出它才能说明为什么不报它）。
// 豁免不是静默跳过：它逐条打印出来，所以这条规则不会被悄悄稀释。
let fails = 0, checked = 0, skippedFiles = 0;
const exemptLedger = [];
const unattributed = [];
const advisory = [];
for (const rel of DOCS) {
  // 绝对路径照原样用。这条本来会静默失效：调用方（导出闸门 W 的自检）传的是系统临时目录
  // 里的绝对路径，走 path.join(ROOT, abs) 会拼成一个不存在的路径，于是"跳过"并 exit 0 ——
  // 自检以为脏样例没响，其实是样例根本没被读到。
  const abs = path.isAbsolute(rel) ? rel : path.join(ROOT, rel);
  if (!fs.existsSync(abs)) { console.error(`跳过（文件不存在）：${rel}`); skippedFiles++; continue; }
  const lines = fs.readFileSync(abs, 'utf8').split(/\r?\n/);
  // 稿件是折行散文：百分数和它的体系名常常不在同一行。所以语境取**整个段落**
  // （空行分隔），体系名也按段落认。同一行太窄会把 14 处命中全推给"没核对"，
  // 那等于没有闸门；整段则会把表头的"占比"牵连到表体——所以表格行单独处理：
  // 表格行只认**本行**的名字，散文段落认整段。
  const paras = [];
  {
    let cur = [];
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].trim() === '' || /^\|/.test(lines[i]) !== /^\|/.test(lines[cur[0] ?? i])) {
        if (cur.length) paras.push(cur);
        cur = /^\|/.test(lines[i]) ? [i] : [];
        if (/^\|/.test(lines[i]) && cur.length === 0) cur = [i];
        continue;
      }
      if (cur.length === 0 || /^\|/.test(lines[i]) === /^\|/.test(lines[cur[0]])) cur.push(i);
      else { paras.push(cur); cur = [i]; }
    }
    if (cur.length) paras.push(cur);
  }
  const paraOf = new Map();
  for (const pr of paras) for (const i of pr) paraOf.set(i, pr);

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const exempt = /share-rule-exempt:\s*([^\-*>]*?)(?:-->)?\s*$/.exec(line);
    const para = paraOf.get(i) || [i];
    const paraText = para.map(n => lines[n]).join(' ');
    const inShareContext = SHARE_WORDS.test(line)
      || (!/^\|/.test(line) && SHARE_WORDS.test(paraText));
    // 必须整个数就是一个百分数，前面不能紧着数字或小数点。少了这道限定，
    // "0.067%–0.952%" 会被读成 67% 和 952%，闸门就会对着一句跨程序残差喊
    // "你在给分母抵消的体系报占比"。爱狼叫的门禁下一步就是被人关掉。
    for (const m of line.matchAll(/(?<![\d.])(\d{1,4}(?:\.\d+)?)\s*%/g)) {
      const val = parseFloat(m[1]);
      // ≥200% 不需要语境：本项目里合法的百分数都在 0-100 之间（占比、覆盖率、
      // 相对跨度、加速比），会冒出 200% 以上的只有那个分母相消后的比值。
      if (exempt) { checked++; exemptLedger.push(`${rel}:${i + 1}  ${val}%  理由：${exempt[1].trim() || '(未写理由)'}`); continue; }
      if (val >= 200) { fails++; checked++;
        console.log(`FAIL(1) ${rel}:${i + 1}  出现 ${val}% —— 分母抵消行（甲烷二聚体，`
          + `-0.517 对余项 +0.285）的比值；包内规则与 §3.2 都禁止把它当占比报出。`
          + `要表达"非局域项比总变化还大"，请并列两个绝对项。`);
        continue; }
      if (!inShareContext) continue;
      checked++;
      if (val >= 200) {
        console.log(`FAIL(1) ${rel}:${i + 1}  占比语境里报了 ${val}% —— `
          + `该行属于分母抵消（${cancelled.map(r => r.name).join('/')}），包内规则禁止报占比`);
        fails++; continue;
      }
      // 表格行：只看本行（表头的"占比"列不能替表体背书）。散文：看整段。
      const named = /^\|/.test(line) ? namedSystems(line) : namedSystems(paraText);
      if (!named.length) { unattributed.push(`${rel}:${i + 1}  ${val}%`); continue; }
      // 比对对象是**这一行点名的那个体系**的占比，不是"有没有哪个体系等于这个数"。
      // 前者能抓出错位（把水的 16% 写成 45%），后者不能：45.5% 恰好是苯···氨的占比，
      // 上一版就是这么放过自己造的假例句的。
      const wrong = named.filter(zh => !shareOf.has(zh) || Math.abs(shareOf.get(zh) - val) > 1);
      if (!wrong.length) continue;
      // 判据 (2) 只报告、不阻断。原因写清楚，别让它看起来像已经生效：
      // 散文是折行的，段落级认名会把同一句里的"相对跨度 7.2%""覆盖率 95.4%"
      // 也当成占比来比对，实测 46 个命中里 40 个是这种误伤。一个爱狼叫的门禁
      // 下一轮就被人整条关掉，比没有更坏。所以硬阻断只保留无歧义的 ≥200%。
      advisory.push(`${rel}:${i + 1}  ${val}%  ← 段内点名 ${wrong.join('/')}，其现算值 `
        + wrong.map(zh => shareOf.has(zh) ? shareOf.get(zh).toFixed(1) + '%' : 'n/a').join('/') + '（人工过一眼）');
    }
  }
}

// 读不到的材料算失败，不算通过：否则路径一坏，闸门就变成"零违规"，
// 而"零违规"和"零条被解析"打印出来长得一样。
if (skippedFiles) {
  console.log(`FAIL(0) 指定要扫的 ${DOCS.length} 份材料里有 ${skippedFiles} 份读不到 —— `
    + '这不是通过，是这条判据今天没跑。');
  fails++;
}
console.log('---');
console.log(`判据 (2) 仅报告、不阻断：${advisory.length} 条可疑（误伤来自折行散文与表体列名，见代码注释）`);
for (const a of advisory.slice(0, 10)) console.log('  ADVISORY ' + a);
if (advisory.length > 10) console.log(`  …另 ${advisory.length - 10} 条`);
console.log(`段内认不出体系名、因此**完全没比对**的占比：${unattributed.length} 个`
  + (unattributed.length ? '（' + unattributed.slice(0, 8).join('; ') + (unattributed.length > 8 ? ' …' : '') + '）' : ''));
console.log(`分母抵消的行：${cancelled.map(r => `${r.name}(${r.dnlc.toFixed(3)} vs 余项${r.semi.toFixed(3)})`).join('、') || '无'}`);
console.log(`可报占比（现算）：${quotable.map(q => q.toFixed(1) + '%').join(' ')}`);
console.log(`占比语境内的百分数命中：${checked} 个，跨 ${DOCS.length} 份材料`);
if (exemptLedger.length) {
  console.log(`具名豁免 ${exemptLedger.length} 条（只允许用于"该数字正是被撤回的对象"）：`);
  for (const e of exemptLedger) console.log('  EXEMPT ' + e);
}
if (fails) {
  console.log(`\nGATE FAILED: ${fails} 处违反包内的占比规则。`
    + ' 改法不是删掉数字，而是改用两个绝对项并列（见 paper/main.md §3.2 与 Table 1 的 "n/a (see note)" 格）。');
  process.exit(1);
}
console.log('PASS（硬规则）：没有一处 ≥200% 的占比式数字。'
  + ` 判据 (2) 不构成担保：${advisory.length} 条仅报告、${unattributed.length} 条连体系名都没认出来。`
  + ' 也就是说"占比都算对了"这句话本闸门**没有**验证过，别把它读成通过。');
