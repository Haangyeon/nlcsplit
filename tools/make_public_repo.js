#!/usr/bin/env node
/*
 * 从工作仓生成"可直接公开"的干净仓库目录：dist/nlcsplit/
 *
 * 为什么不让 git 直接公开这个仓：
 *   - 入库文件里有 14 个内部工作文件（PROGRESS 与 RESEARCH 等 14 个），
 *     里面全是撤回记录和同行讨论，不是给外人看的东西；
 *   - nlcsplit/centos_run*.sh 与 centos_setup.sh 带集群 IP 与远端绝对路径；
 *   - paper/ 是未发表稿，不进公开代码仓。
 *
 * 三道闸门（任一失败即非零退出，不出货）：
 *   A 无 GAMESS 代码/源码串   B 无密钥与内网主机串   C 证据文件哈希与 MANIFEST 一致
 *
 * 护栏：目标目录已存在且不是本脚本建的 -> 拒绝覆写（今天 build_bib.js 把已核验的
 * references.bib 覆盖成 0 条，教训就是"重新生成人工整理过的产物之前，先证明自己有权覆盖它"）。
 */
const fs = require('fs');
const path = require('path');
const cp = require('child_process');

const SRC = process.cwd();
const OUT = path.join(SRC, 'dist', 'nlcsplit');
const STAMP = '.exported-by-make_public_repo';

// ---------------------------------------------------------------- 白名单
const PKG = ['__init__.py', 'nlc.py', 'partition.py', 'geomlib.py', 'figures.py'];
const STEPS = ['step1_validate.py', 'step2_convergence.py', 'step_b_scan.py', 'step_c_relaxation.py',
  'step_d_floor.py', 'step_e_kernel.py', 'step_f_dispersion.py', 'step_g_basis.py',
  'step_h_s22.py', 'step_i_gridrepr.py'];
const TESTS = ['__init__.py', 'conftest.py', 'test_geometry.py', 'test_kernel.py',
  'test_partition_factors.py', 'test_regression.py'];
const EXAMPLES = ['__init__.py', 'quickstart.py', 'check_fast_pair.py', 'check_soft_partition.py'];
const ROOT = ['README.md', 'CONTRIBUTING.md', 'LICENSE', 'pyproject.toml', 'conftest.py'];
// 明确**不**带：centos_run*.sh, centos_setup.sh（集群 IP/绝对路径）, PROGRESS-*, RESEARCH-*,
// HANDOFF-*, MAIN-skeleton.md, STEP0-*, paper/, scratch/, figs/
const EXPLICITLY_EXCLUDED = ['nlcsplit/centos_run.sh', 'nlcsplit/centos_run2.sh', 'nlcsplit/centos_run3.sh',
  'nlcsplit/centos_run4.sh', 'nlcsplit/centos_run5.sh', 'nlcsplit/centos_setup.sh'];

function sha256(p) {
  // Git Bash 下反斜杠路径会让 sha256sum 的输出前面多一个反斜杠，哈希当场对不上。
  // （我第一版就被这个骗过，报"六个文件哈希全不符"，其实字节一模一样。）
  const sh = String(p).replace(/\\/g, '/');
  return cp.execSync(`sha256sum "${sh}"`, { encoding: 'utf8' }).trim().split(/[\s]+/)[0].replace(/^\\+/, '');
}
function read(p) { return fs.readFileSync(p, 'utf8'); }
function write(rel, text) {
  const to = path.join(OUT, rel);
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.writeFileSync(to, text);
  return rel;
}

// ---------------------------------------------------------------- 覆写护栏
if (fs.existsSync(OUT)) {
  if (!fs.existsSync(path.join(OUT, STAMP))) {
    console.error(`REFUSING: ${OUT} 已存在但不是本脚本建的。手动确认后删除，不要让我覆盖。`);
    process.exit(4);
  }
  cp.execSync(`rm -rf "${OUT}"`);
}
fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, STAMP), new Date().toISOString() + '\n');

const copied = [];
for (const f of ROOT) {
  const p = path.join(SRC, f);
  if (!fs.existsSync(p)) { console.error('MISSING root file: ' + f); process.exit(2); }
  copied.push(write(f, read(p)));
}
for (const f of PKG) copied.push(write('nlcsplit/' + f, read(path.join(SRC, 'nlcsplit', f))));
for (const f of STEPS) copied.push(write('nlcsplit/' + f, read(path.join(SRC, 'nlcsplit', f))));
for (const f of TESTS) copied.push(write('nlcsplit/tests/' + f, read(path.join(SRC, 'nlcsplit/tests', f))));
for (const f of EXAMPLES) copied.push(write('nlcsplit/examples/' + f, read(path.join(SRC, 'nlcsplit/examples', f))));
copied.push(write('nlcsplit/run_all.sh', read(path.join(SRC, 'nlcsplit/run_all.sh'))));

// 几何获取脚本：把写死的本机代理改成"仅在环境里已有则沿用"，否则公开后别人照抄会连不上
let get = read(path.join(SRC, 'nlcsplit/tools/get_s22.sh'));
const before = get;
get = get.replace(/\b127\.0\.0\.1:7890\b/g, '<your-proxy>');
get = get.replace(/^\s*(# )?export HTTPS_PROXY=\S+/m,
  'export HTTPS_PROXY="${HTTPS_PROXY:-}"   # 需要时自行 export，不需要则空值即直连');
if (/7890|127\.0\.0\.1/.test(get)) console.error('BUG: 抹敏之后仍残留本机代理串');
if (get === before) console.error('WARN: get_s22.sh 的代理行没被改掉（格式变了？）');
copied.push(write('nlcsplit/tools/get_s22.sh', get));

// ---------------------------------------------------------------- 侧车：抹外部标识 + 重指路径
const anchor = JSON.parse(read(path.join(SRC, 'nlcsplit/logs/orca_anchor.json')));
for (const k of ['remote_workdir', 'allocation', 'host', 'mirror_verified']) delete anchor[k];
const scrub = (s) => typeof s === 'string'
  ? s.replace(/nlcsplit\/ref\/orca\/out\//g, 'evidence/orca_run/')
     .replace(/\/home\/[A-Za-z0-9._-]+/g, '<cluster-home>')
  : s;
(function walk(o) {
  if (Array.isArray(o)) return o.forEach(walk);
  if (o && typeof o === 'object') {
    for (const k of Object.keys(o)) {
      if (typeof o[k] === 'string') o[k] = scrub(o[k]);
      else walk(o[k]);
    }
  }
})(anchor);
anchor._published_variant = '本文件是公开仓变体：抹掉了远端绝对路径/作业串/主机名，'
  + '并把镜像路径重指到仓内 evidence/orca_run/。母仓原始字段未动。数值、行号、sha256 全部保留。';
copied.push(write('nlcsplit/logs/orca_anchor.json', JSON.stringify(anchor, null, 1) + '\n'));

let side = read(path.join(SRC, 'nlcsplit/logs/step_h.json'));
side = side.replace(/"geometry_source":s*"[^"]*"/, '"geometry_source": "fetched by nlcsplit/tools/get_s22.sh from github.com/grimme-lab/GMTKN55 tag v1"');
copied.push(write('nlcsplit/logs/step_h.json', side));   // 不动：host 字段是"哪台机器出的数"的出处，故意保留

// level-2 + 反泊松 那一档单独成车（母仓 step_h.json 按体系名合并会冲掉同名高档行），
// 它的原始 stdout 也已入库，见 evidence/l2cp/ + MANIFEST.sha256。
copied.push(write('nlcsplit/logs/step_h_l2cp.json', read(path.join(SRC, 'nlcsplit/logs/step_h_l2cp.json'))));
fs.mkdirSync(path.join(OUT, 'evidence'), { recursive: true });   // 必须在 cp -r 之前，否则目标父目录不存在
cp.execSync(`cp -r "${path.join(SRC, 'evidence', 'l2cp')}" "${path.join(OUT, 'evidence', 'l2cp')}"`);
for (const f of fs.readdirSync(path.join(OUT, 'evidence', 'l2cp'))) {
  if (f !== 'MANIFEST.sha256') copied.push('evidence/l2cp/' + f);
}

// ---------------------------------------------------------------- 证据原件：字节不动 + 哈希校验
fs.mkdirSync(path.join(OUT, 'evidence'), { recursive: true });
cp.execSync(`cp -r "${path.join(SRC, 'evidence', 'orca_run')}" "${path.join(OUT, 'evidence', 'orca_run')}"`);
for (const f of fs.readdirSync(path.join(OUT, 'evidence', 'orca_run'))) {
  if (f.endsWith('.out')) copied.push('evidence/orca_run/' + f);
}

// ---------------------------------------------------------------- 闸门 A：无 GAMESS **源码**
// 注意：/gamess/i 一律命中是**误报**——README/CONTRIBUTING/__init__ 里出现这个词，
// 正是因为我们在声明"本包不含 GAMESS 代码"。一个永远失败的门禁和一个不会失败的门禁一样没用。
// 所以这里只抓真正的 GAMESS 源码工件；"gamess"这个词的出现另列为 info，人工过一眼即可。
const gamessPats = [/\$gnum/i, /\bintgc\b/, /\bdiana\b/, /rhfuhf/, /\bgameSS\.src\b/i,
  /ps\/src\//, /GAMESS\.src/, /getscr|erscf[0-9]/];
const wordOnly = [];
const ga = [];
for (const rel of copied) {
  let t; try { t = read(path.join(OUT, rel)); } catch (e) { continue; }
  if (!/\.(py|sh|json|md|toml|txt|out|c|f|f90)$/.test(rel)) continue;
  gamessPats.forEach((re, i) => { if (re.test(t)) ga.push(`${rel}  <- GAMESS 源码工件 模式#${i} ${re}`); });
  if (/gamess/i.test(t)) wordOnly.push(rel);
}

// ---------------------------------------------------------------- 闸门 B：无密钥/内网
// 同样只抓"密钥的形状"，不抓"password 这个英文单词"——CONTRIBUTING 里那句
// "不要把密码写进文件"是规矩本身，不是泄露。
const secretPats = [/10\.8\.51\.23/, /:7890/, /BEGIN [A-Z ]*PRIVATE KEY/,
  /(?:password|passwd|token|api[_-]?key)\s*[:=]\s*["']?\S{4,}/i,
  /\bssh\b[^#\n]*@/, /\b\w+@\b\d{1,3}(\.\d{1,3}){3}/, /\/home\/haangyeon/];
const gb = [];
for (const rel of copied) {
  let t; try { t = read(path.join(OUT, rel)); } catch (e) { continue; }
  const hits = secretPats.map((re, i) => re.test(t) ? i : -1).filter(x => x >= 0);
  if (hits.length) gb.push(`${rel}  <- 命中 ${hits.map(i => secretPats[i]).join(', ')}`);
}

// ---------------------------------------------------------------- 闸门 C：证据哈希
const manFile = path.join(OUT, 'evidence', 'orca_run', 'MANIFEST.sha256');
const gc = [];
if (!fs.existsSync(manFile)) gc.push('MANIFEST.sha256 缺失');
else for (const line of read(manFile).split(/\r?\n/).filter(Boolean)) {
  const [h, name] = [line.split(/[\s*]+/)[0], line.split(/[\s*]+/)[1]];
  const p = path.join(OUT, 'evidence', 'orca_run', name);
  if (!fs.existsSync(p)) { gc.push('缺文件 ' + name); continue; }
  if (sha256(p) !== h) gc.push('哈希不符 ' + name);
}

fs.writeFileSync(path.join(OUT, 'EXPORT-MANIFEST.txt'),
  copied.length + ' files\n' + copied.sort().join('\n') + '\n');

console.log(JSON.stringify({
  out: OUT, files: copied.length,
  gateA_gamess: ga, note_word_only: wordOnly, gateB_secrets: gb, gateC_hashes: gc,
  excluded_by_design: EXPLICITLY_EXCLUDED.concat(['PROGRESS-*.md', 'RESEARCH-*.md', 'HANDOFF-*.md',
    'MAIN-skeleton.md', 'STEP0-*.md', 'paper/**', 'scratch/**', 'figs/**']),
}, null, 1));
const bad = ga.length + gb.length + gc.length;
process.exit(bad ? 1 : 0);
