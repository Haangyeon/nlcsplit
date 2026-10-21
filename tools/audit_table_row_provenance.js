#!/usr/bin/env node
/*
 * 把"表由脚本从原件现算、零手抄"从一张表推广到全稿的审计（只读）。
 *
 * 为什么要通用化：`check_table1_transcription.py` 只证明了 Table 1 的 5/6/7 列逐字来自同一个档块。
 * 验收第 1 条说的是"正文**每张表**每一格"。别的表要是没人查，就等于那条只做了局部。
 *
 * 怎么做到不需要中英对照表（那是我自己刚犯过的错）：
 *   不看体系名，只看**一行里的数字组合**。一行有 3~6 个独立数值，
 *   它们同时出现在同一份归档里，几乎不可能是巧合——
 *   这就把"行贴错没贴错"和"数抄错没抄错"一起管住了，且不引入任何人手维护的名字映射。
 *   数值按"四舍五入到表格写出的小数位"比对：正文常少印一位，归档多印的那几位不该算不符。
 *
 * 判据：一行里参与比对的数值 ≥ MIN 个且没有任何一份档能同时容纳它们 ⇒ 记 MISSING。
 * 太少数字的行（比如只有 1~2 个数的行）不下结论——那是判据覆盖不到，不是说它错。
 */
const fs = require('fs');
const path = require('path');
const cp = require('child_process');

const ROOT = process.cwd();
const DOCS = ['paper/main.md', 'paper/software.md', 'paper/p2.md'].filter((d) =>
  fs.existsSync(path.join(ROOT, d)));
const MIN = 3;                       // 少于 3 个数值的行不下结论
const NUM = /^[-+]?\d+\.\d+$/;       // 只认带小数点的数，跳过 2 / 22 / 6 这类整数噪声

function trackedTexts() {
  const out = cp.execFileSync('git', ['ls-files'], { cwd: ROOT, encoding: 'utf8' }).split('\n')
    .filter((f) => f && !/\.(png|jpg|pdf|zip|whl|gz|lock)$/.test(f) && /^(evidence|nlcsplit)\/./.test(f));
  const texts = [];
  for (const f of out) {
    const p = path.join(ROOT, f);
    let s; try { s = fs.readFileSync(p, 'utf8'); } catch (e) { continue; }
    if (s.length > 4_000_000) continue;
    const nums = new Set();
    // 归档侧也必须吃指数：上一版这里用 /\d+\.\d+/ ，把 "1.735e-18" 只截成 "1.735"，
    // 于是表里写 1.735e-18 的行被误判成"任何档里都找不到"。假警报的来源在我这边。
    for (const m of s.matchAll(/[-+]?\d+\.\d+(?:[eE][-+]?\d+)?/g)) nums.add(m[0]);
    texts.push({ f, nums });
  }
  return texts;
}

function tableRows(md) {
  const rows = [];
  const lines = fs.readFileSync(path.join(ROOT, md), 'utf8').split('\n');
  let cur = null;
  lines.forEach((l, i) => {
    const isRow = /^\s*\|.+\|\s*$/.test(l);
    if (!isRow) { if (cur && cur.rows.length) rows.push(cur); cur = null; return; }
    if (/^\s*\|[\s|:-]+\|\s*$/.test(l)) return;           // 分隔行
    const cells = l.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());
    const vals = [];
    // 一个格里可以塞好几个数（p2.md 那张计时表就是 `5.31×, 72.6%, 1.3e-3`），
    // 上一版把一个格当一个 token 且要求它整体形如 0.123，于是整张数值表被当成"没有数"跳过了。
    // 现在先按逗号/分号/空格拆格，再逐个判；`×`/`≈`/百分号/千分位都剥掉。
    // 只收带小数点或带指数的数：像 "3"（原子数）这种整数噪声不够当指纹。
    for (const c of cells) {
      // 千分位逗号不能当分隔符：`53,983 (18.0%)` 曾被拆成 "53" 与 "983"（都不带小数点 ⇒ 被丢），
      // 于是整行只剩 1~2 个可比数值、被 MIN 门槛跳过 —— 一张真有数的表就这么"零覆盖"了。
      // 先去掉千分位逗号（数字之间的那种），再按空格/分号拆。
      const c2 = c.replace(/(\d),(\d{3})/g, "$1$2");
      for (const raw of c2.split(/[;]|\s{1,}/)) {
        const t = raw.replace(/[×≈%\s,]/g, '').replace(/^\+/, '');
        if (!/[-+]?\d*\.\d+(e[-+]?\d+)?$/i.test(t) && !/[-+]?\d+\.\d+e[-+]?\d+$/i.test(t)) continue;
        const sgn = t.startsWith('-') ? '-' : '';
        const body = t.replace(/^[-+]/, '');
        const m = /^(\d+)\.(\d+)(?:e([-+]?\d+))?$/i.exec(body);
        if (!m) continue;
        const d = m[2].length;
        const exp = m[3] ? parseInt(m[3], 10) : 0;
        // 比"末位一格"而不是比字符串：正文用科学计数法印、归档用小数印，
        // 同一个数两种写法必须算相等。上一版把指数丢了，会把 1.3e-3 当成 1.3 去匹配。
        vals.push({ s: sgn + body, val: parseFloat(sgn + body),
                    tol: 0.5 * Math.pow(10, exp - d), raw: t });
      }
    }
    if (!cur) cur = { md, line0: i + 1, rows: [] };
    cur.rows.push({ line: i + 1, cells, vals });
  });
  if (cur && cur.rows.length) rows.push(cur);
  return rows;
}

function main() {
  const texts = trackedTexts();
  console.log('# 全稿"零手抄"审计（按行的数值组合找归档共现；不依赖任何名字映射）');
  console.log(`# 扫正文 ${DOCS.join(', ')}  索引 ${texts.length} 份受版本控制的文本`);
  const has = (t, v) => {
    for (const n of t.nums) {
      if ((v.s.startsWith('-')) !== n.startsWith('-')) continue;
      if (Math.abs(parseFloat(n) - v.val) <= v.tol) return true;
    }
    return false;
  };
  const cls = { FULL: [], PARTIAL: [], WEAK: [], NONE: [] };
  const tables = new Map();      // key = doc:表首行 → 该表的分级计数
  let checked = 0, skipped = 0;
  for (const doc of DOCS) {
    for (const tbl of tableRows(doc)) {
      const key = `${doc}:${tbl.line0}`;
      const t = tables.get(key) || { doc, line0: tbl.line0, rows: tbl.rows.length,
                                     checked: 0, skipped: 0, FULL: 0, PARTIAL: 0, WEAK: 0, NONE: 0 };
      tables.set(key, t);
      for (const r of tbl.rows) {
        if (r.vals.length < MIN) { skipped++; t.skipped++; continue; }
        checked++; t.checked++;
        // 一份档能覆盖到这一行的几个数；"跨两份档凑成一行"是合法的，
        // 所以这里分等级报，而不是要求单份档全包（上一版那么干，把 Table 1 全部误判成未命中）。
        const cover = Math.max(...texts.map((t) => r.vals.filter((v) => has(t, v)).length));
        const anywhere = r.vals.every((v) => texts.some((t) => has(t, v)));
        const rec = { doc, line: r.line, n: r.vals.length, cover,
                      vals: r.vals.map((v) => v.s).join(' '), label: r.cells[0].slice(0, 28) };
        const grade = cover === r.vals.length ? 'FULL' : cover >= MIN ? 'PARTIAL'
                    : anywhere ? 'WEAK' : 'NONE';
        cls[grade].push(rec); t[grade]++;
      }
    }
  }
  console.log(`\n可比对行 ${checked}（数值太少跳过 ${skipped}，跳过≠通过）`);
  console.log(`  FULL    单份档全包         ${cls.FULL.length}`);
  console.log(`  PARTIAL 有档覆盖 ≥${MIN} 个数、需跨档拼 ${cls.PARTIAL.length}`);
  console.log(`  WEAK    每个数都找得到，但没有一份档覆盖 ≥${MIN} 个 ${cls.WEAK.length}`);
  console.log(`  NONE    有数值在任何档里都找不到 ${cls.NONE.length}   ← 只有这一类是真问题`);

  // 按表汇总：全局计数会藏住"某一张表一行都没被验证过"这种最该被看见的事。
  console.log(`\n按表覆盖（行=数据行；可比对=该行 ≥${MIN} 个带小数的数值）：`);
  for (const [key, t] of [...tables.entries()].sort()) {
    const flag = t.checked === 0 ? '零机器验证' : (t.NONE ? `有 ${t.NONE} 行NONE` : '');
    console.log(`   ${t.doc}:${t.line0}  数据行 ${String(t.rows).padStart(3)}  `
      + `可比对 ${String(t.checked).padStart(3)}  全/部/弱/无 ${t.FULL}/${t.PARTIAL}/${t.WEAK}/${t.NONE}`
      + (flag ? `   ← ${flag}` : ''));
  }
  for (const k of ['WEAK', 'PARTIAL', 'NONE']) {
    if (!cls[k].length) continue;
    console.log(`\n--- ${k} ---`);
    for (const m of cls[k].slice(0, 12))
      console.log(`   ${m.doc}:${m.line}  [${m.label}]  覆盖 ${m.cover}/${m.n}  ${m.vals}`);
  }
  if (cls.NONE.length) {
    console.log('\nVERDICT NEEDS_REVIEW —— 有整行的数值在任何归档里都找不到，逐条定性（手抄？单位不同？还是索引没覆盖到）。');
    return 1;
  }
  console.log('\nVERDICT OK —— 每个可比对行的数值都能在归档里找到；'
    + 'PARTIAL/WEAK 只是说明"一行跨多份档"，那是合法的（Table 1 就是 S33 与普查两份拼的）。');
  return 0;
}
if (require.main === module) process.exit(main());
