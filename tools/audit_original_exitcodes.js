#!/usr/bin/env node
/*
 * 只读审计：每一份 .out 原件是否真的"自报退出码"。
 *
 * 为什么单开：验收第 1 条的括号里写着"（带 `# exit=` 自写行与 `.rc`）"，
 * 而 `claim_gate.js` 查的是"数字有没有出处、引用的路径存不存在"，**不查这条**。
 * 也就是说这一条此前全靠我记得"新档都有"——9 月的老档有没有，没人知道。
 *
 * 三件事分开判，因为它们是三种不同的缺陷：
 *   missing_exit  文件里根本没有 `# exit=` 行         ⇒ 当初就不是脚本落的档
 *   missing_rc    没有同名 `.rc`                      ⇒ 退出码没落成可机器读的独立文件
 *   mismatch      有 `.rc` 也有 `# exit=`，但两个数不同 ⇒ 有一个是假的
 * 本脚本**不写任何东西**，也不"顺手补 .rc"：从 `# exit=` 反推一个 .rc 出来
 * 看起来等价，但那是在事后制造证据。要补也得由作者点头、并且标成回填档。
 */
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const EVID = path.join(ROOT, 'evidence');
// 带时间戳前缀的 .out 原件（本仓的归档命名约定），以及它们旁边可能被引用的文件
const TS = /^\d{8}T\d{6}Z_/;
// 自报退出码在本仓里有**四代写法**（2026-10-13 实测，不是猜的）：
//   hash_comment  `# exit=0 at 2026-…`          —— 现约定（本脚本按它判"完全合规"）
//   bare_exit     `EXIT=0`                       —— 9 月底那批 ccsdt
//   multi_rc      `pip_rc=0 venv_probe_rc=1 …`   —— 10-09 的 release_qa，一次跑里有多个码
//   none          文件里没有码，只有旁边的 .rc   —— 10-06 那批
// 上一版只认第一种，于是把 44 份被引用的档**全**判成"没有自报"——那是我的判据太窄，
// 不是这些档没有自报。判据错了比没判更糟：它会把正常档案刷成一片红，下次就没人看细节。
const FORMS = [
  ['hash_comment', /^#\s*exit\s*=\s*(-?\d+)/m],
  ['bare_exit', /^EXIT=(-?\d+)\s*$/m],
  ['multi_rc', /(?:^|\s)([a-z_]+_rc)=(-?\d+)/],
];
// .rc 的内容写法也有两代：`0` 与 `rc=0`。任何把它当整数读的工具（含 summarize_s22_full.py
// 的 latest_ok：只认 strip() == "0"）碰到后者就当这档没成功。
function readSelfReport(txt) {
  for (const [form, re] of FORMS) {
    const m = txt.match(re);
    if (m) return { form, code: form === 'multi_rc' ? m[2] : m[1] };
  }
  return { form: 'none', code: null };
}

// `--cited` 只看正文/软件文真引用到的那些档：验收第 1 条说的是"正文每张表每一格"，
// 不是"仓里每一份历史档"。不加这一句，报出来的 89/142 会把两个不同的问题混成一个数。
const CITED_ONLY = process.argv.slice(2).includes('--cited');
function citedSet() {
  const docs = ['paper/main.md', 'paper/software.md', 'paper/p2.md', 'paper/SI.md'];
  const set = new Set();
  for (const d of docs) {
    const p = path.join(ROOT, d);
    if (!fs.existsSync(p)) continue;
    // 反引号里跨行折行的真路径也要接上（claim_gate 里同一条坑：劈成两半的引用）
    const txt = fs.readFileSync(p, 'utf8').replace(/-\s*\n\s*`/g, '`');
    for (const m of txt.matchAll(/`((?:evidence|nlcsplit)\/[^\s`]+?\.out(?:\.rc)?)`/g)) set.add(m[1]);
  }
  return set;
}
const CITED = CITED_ONLY ? citedSet() : null;

const rows = [];
(function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { walk(p); continue; }
    if (!TS.test(e.name) || !e.name.endsWith('.out')) continue;
    const rel = path.relative(ROOT, p).replace(/\\/g, '/');
    if (CITED && !CITED.has(rel) && !CITED.has(rel + '.rc')) continue;
    const txt = fs.readFileSync(p, 'utf8');
    const sr = readSelfReport(txt);
    const rcPath = p + '.rc';
    const hasRc = fs.existsSync(rcPath);
    const rcVal = hasRc ? fs.readFileSync(rcPath, 'utf8').trim() : null;
    // .rc 里抽数字：`0`、`rc=0`、`exit=0` 三代写法都要能读出来
    const rcNum = hasRc ? (rcVal.match(/(-?\d+)\s*$/) || [null, null])[1] : null;
    let status;
    if (sr.form === 'none') status = hasRc ? 'rc_only' : 'nothing';
    else if (!hasRc) status = 'no_rc_sibling';
    else if (rcNum !== sr.code) status = 'mismatch';
    else status = sr.form === 'hash_comment' ? 'current' : 'legacy_form_ok';
    rows.push({ rel, status, form: sr.form, code: sr.code ?? '-', rc: rcVal ?? '-', rcNum: rcNum ?? '-' });
  }
})(EVID);

const STATUSES = ['current', 'legacy_form_ok', 'no_rc_sibling', 'rc_only', 'nothing', 'mismatch'];
const LABEL = {
  current: '现约定', legacy_form_ok: '旧写法且与 .rc 相符', no_rc_sibling: '有码但没 .rc',
  rc_only: '只有 .rc 无码', nothing: '两样都没有', mismatch: '码与 .rc 不符',
};
const byDir = {}, tally = {};
for (const r of rows) {
  const d = r.rel.split('/')[1] || '(顶层)';
  byDir[d] = byDir[d] || {};
  byDir[d][r.status] = (byDir[d][r.status] || 0) + 1;
  tally[r.status] = (tally[r.status] || 0) + 1;
}

console.log('# 原件自报退出码审计（只读，不写任何文件）');
console.log(`# 范围：${CITED_ONLY ? '正文/软件文引用到的档' : '仓内全部时间戳档'}  共 ${rows.length} 份\n`);
console.log('目录                    现约定  旧写法OK  有码无rc  只有rc  都没有  不符');
for (const d of Object.keys(byDir).sort()) {
  const b = byDir[d];
  const cell = (k) => String(b[k] || 0).padStart(9);
  console.log(`   ${d.padEnd(22)}${cell('current')}${cell('legacy_form_ok')}${cell('no_rc_sibling')}${cell('rc_only')}${cell('nothing')}${String(b.mismatch || 0).padStart(5)}`);
}
console.log('\n合计：' + STATUSES.filter((s) => tally[s]).map((s) => `${LABEL[s]}=${tally[s]}`).join('  '));

// 只有"码与 .rc 矛盾"和"两样都没有"是真缺陷；其余是**约定世代不同**，应由正文把话说到那一代。
const hard = rows.filter((r) => r.status === 'mismatch' || r.status === 'nothing');
const drift = rows.filter((r) => r.status !== 'current' && r.status !== 'mismatch' && r.status !== 'nothing');
if (drift.length) {
  console.log(`\n# 约定漂移（不是造假，是写法不同）共 ${drift.length} 份，各世代的代表档：`);
  const seen = new Set();
  for (const r of drift) {
    if (seen.has(r.status)) continue;
    seen.add(r.status);
    console.log(`   ${r.status.padEnd(15)} ${r.rel}  (自报=${r.form}:${r.code}, .rc=${r.rc})`);
  }
}
if (hard.length) {
  console.log(`\n!! 真缺陷 ${hard.length} 份（码与 .rc 矛盾，或两样都没有）：`);
  for (const r of hard.slice(0, 30)) console.log(`   ${r.status.padEnd(10)} ${r.rel}`);
  console.log('\nVERDICT NOTCLEAN —— 上面这些既没有自报也没有 .rc，或两个数打架。');
  process.exit(1);
}
console.log(`\nVERDICT OK —— 没有"两个数打架"或"完全没有退出码痕迹"的档。`
  + `\n   但只有 ${tally.current || 0}/${rows.length} 份用的是验收第 1 条写的**那一种**写法（`
  + `# exit= 行 + .rc），其余 ${drift.length} 份是更早的等价写法。`
  + `\n   ⇒ 正文要么把这句话说清到"每份档都自报退出码（现约定或早期等价形式）"，要么只对它成立的那批这么讲。`);
