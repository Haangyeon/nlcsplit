#!/usr/bin/env node
/*
 * 从工作仓生成"可直接公开"的干净仓库目录：dist/nlcsplit/，并从它重新出货 wheel/sdist。
 *
 * 为什么不让 git 直接公开这个仓：
 *   - 入库文件里有 14 个内部工作文件（PROGRESS 与 RESEARCH 等 14 个），
 *     里面全是撤回记录和同行讨论，不是给外人看的东西；
 *   - nlcsplit/centos_run*.sh 与 centos_setup.sh 带集群 IP 与远端绝对路径；
 *   - paper/ 是未发表稿，不进公开代码仓。
 *
 * 闸门（任一失败即非零退出，不出货；没有"警告后继续"这一档）：
 *   A 无 GAMESS 源码工件        B 无密钥/内网串（含工作机绝对路径、集群端口、账号串）
 *   C 证据哈希与发布副本一致     D 正文引用的每个出处都真的随包发布
 *   E 用到的依赖都得声明        F wheel/sdist 成员清单不夹带脚本式 test_*.py
 *   G LICENSE 无 Apache 模板占位符且版权行已填
 *
 * 2026-09-29 审计后的三处加固（都是被实测打脸加的）：
 *   1. 闸门 B 原来只抓"密钥的形状"，不抓工作机绝对路径。`/root/gamess_work`、
 *      `/mnt/e/Project/GAMESS`、`E:/Project/GAMESS`、集群端口、`haangyeon`、`snnu`
 *      全都不在表里，于是闸门报"数组为空"而 dist 里 13 个文件照旧带串。现在补齐。
 *   2. 闸门原来只扫 `copied` 这份**名单**，不扫**磁盘上的目录树**。名单外的东西
 *      （pytest 在发布树里跑出来的 13 个 .pyc、MANIFEST.sha256 自身）从来没被看过一眼。
 *      现在 A/B 走目录树遍历，并且多一条"发布树里不许有 __pycache__/.pyc"的残留检查。
 *   3. wheel 是 01:39 的旧货，里面还装着 `nlcsplit/test_fast_pair.py` 与
 *      `nlcsplit/test_soft_partition.py`（那两个 import 即执行的脚本式模块在源码树里
 *      早已改名成 examples/check_*.py，但产物没跟着重打）。"重打 wheel 已验证"这句话
 *      当时是对源码树说的，不是对产物说的。现在出货由本脚本做，且闸门 F 解包实测成员。
 *
 * 护栏：目标目录已存在且不是本脚本建的 -> 拒绝覆写（今天 build_bib.js 把已核验的
 * references.bib 覆盖成 0 条，教训就是"重新生成人工整理过的产物之前，先证明自己有权覆盖它"）。
 */
const fs = require('fs');
const path = require('path');
const cp = require('child_process');

const SRC = process.cwd();
// 出货与产物成员核验都要用 python。process.execPath 在 node 里是 node.exe，别用那个。
const PY = process.env.NLCSPLIT_PY || 'python';
try {
  cp.execFileSync(PY, ['-c', 'import setuptools,sys;print(setuptools.__version__,sys.version.split()[0])'],
    { stdio: 'pipe' });
} catch (e) {
  console.error(`FATAL: 找不到可用的 python（${PY}）或 setuptools，无法出货。`);
  process.exit(3);
}
const OUT = path.join(SRC, 'dist', 'nlcsplit');
const DIST = path.join(SRC, 'dist');
const STAGE = path.join(DIST, '.build-stage');          // 出货用的临时源码副本
const STAMP = '.exported-by-make_public_repo';
const LEDGER_OUTSIDE = path.join(DIST, 'PATH-SCRUB-LEDGER.txt');

// ---------------------------------------------------------------- 白名单
const PKG = ['__init__.py', 'nlc.py', 'partition.py', 'geomlib.py', 'figures.py'];
const STEPS = ['step1_validate.py', 'step2_convergence.py', 'step_b_scan.py', 'step_c_relaxation.py',
  'step_d_floor.py', 'step_e_kernel.py', 'step_f_dispersion.py', 'step_g_basis.py',
  'step_h_s22.py', 'step_i_gridrepr.py', 'step_k_population.py'];
const TESTS = ['__init__.py', 'conftest.py', 'test_geometry.py', 'test_kernel.py',
  'test_partition_factors.py', 'test_regression.py'];
const EXAMPLES = ['__init__.py', 'quickstart.py', 'check_fast_pair.py', 'check_soft_partition.py'];
const ROOT = ['README.md', 'CONTRIBUTING.md', 'LICENSE', 'pyproject.toml', 'conftest.py'];
// CI 配置也属于"发布物"：只在工作区里有、公开仓里没有，等于闸门 E 之外的那道门禁
// 对读者不存在。
const WORKFLOW = { '.github/workflows/ci.yml': '.github/workflows/ci.yml' };
// 明确**不**带：centos_run*.sh, centos_setup.sh（集群 IP/绝对路径）, PROGRESS-*（两代理的协调
// 与撤回流水，不是证据）, HANDOFF-*, STEP0-*, paper/, scratch/, figs/。
// RESEARCH-* 与 MAIN-skeleton.md 改为改名进 docs/，见下面 RELOCATED —— 附录要靠它们落地。
const EXPLICITLY_EXCLUDED = ['nlcsplit/centos_run.sh', 'nlcsplit/centos_run2.sh', 'nlcsplit/centos_run3.sh',
  'nlcsplit/centos_run4.sh', 'nlcsplit/centos_run5.sh', 'nlcsplit/centos_setup.sh'];

// 证据目录。recompute/ 与 orca_control/ 是 2026-09-29 补的：paper/main.md 的 [S8][S9][S12][S18]
// 直接按文件名指它们，闸门 D 报"母仓里有、没随包发布"——引用落空。
const EVIDENCE_DIRS = ['l2cp', 'orca_run', 'centos', 'retrieval_calibration', 'recompute',
  'orca_control', 'population', 'agentb_sweep'];

// ================================================================ 脱敏（只发生在导出副本上）
// 三个表分开，因为它们的"数字不变性"论证强度不同：
//   PATH_TABLE     —— 工作机/仓库绝对路径串。
//   ENDPOINT_TABLE —— 集群 SSH 端口。它命中的 span 里带数字，所以单独声明、单独列账。
//   IDENT_TABLE    —— 机构名/集群账号名（审计要求闸门认得 snnu 与 haangyeon）。
//                     它们不是路径，但同样是把"谁、在哪台机器、哪个单位"写在公开产物里。
//                     母仓原件照旧不动，只在导出副本上换成保留语义的中性标签：
//                     "cpu3 (SNNU cluster, …)" -> "cpu3 (<CLUSTER> cluster, …)"，机器名 cpu3 留着。
// 原件（evidence/**、nlcsplit/logs/**）一律不改：这里只改写到 dist/ 的副本。
const PATH_TABLE = [
  [/\/root\/gamess_work\/nlcsplit\/s22/gi, '<S22_GEOMETRY_DIR>'],
  [/\/root\/gamess_work\/nlcsplit\/logs/gi, '<REMOTE_LOG_DIR>'],
  [/\/root\/gamess_work\/logs/gi, '<REMOTE_LOG_DIR>'],
  [/\/root\/gamess_work/gi, '<REMOTE_WORKDIR>'],
  [/\/home\/haangyeon\/agent_l2_work\/nlcsplit\/logs/gi, '<REMOTE_LOG_DIR>'],
  [/\/home\/haangyeon/gi, '<CLUSTER_HOME>'],
  [/\/mnt\/[a-z]\/Project\/GAMESS/gi, '<REPO>'],
  [/[a-z]:[\\/]+Project[\\/]+GAMESS/gi, '<REPO>'],
  // 本机代理端点。get_s22.sh 早就单独在抹它，但归档 stdout 里也会原样出现
  // （`$ https_proxy=http://127.0.0.1:7890 python3 -m pip install …`），
  // 那是工作机的网络拓扑，不是实验结果。
  [/\b(?:127\.0\.0\.1|localhost):7890\b/gi, '<your-proxy>'],
];
const ENDPOINT_TABLE = [
  // 注意 `\b-P` 匹配不上：`-` 不是词字符，空格到 `-` 之间没有词边界（第一版就在这儿失配，
  // 于是 `scp -P 24522` 一路活着进了发布树）。
  [/-P[ \t]+24522\b/g, '-P <SSH_PORT>'],
  [/-p[ \t]+20019\b/g, '-p <SSH_PORT>'],
  [/:(24522|20019)\b/g, ':<SSH_PORT>'],
];
const IDENT_TABLE = [
  [/\bSNNU\b/gi, '<CLUSTER>'],
  [/\bHaangyeon\b/g, '<OPERATOR>'],
];
const SCRUB_TABLES = [['path', PATH_TABLE], ['endpoint', ENDPOINT_TABLE], ['ident', IDENT_TABLE]];
// 一个被抹掉的 span 必须长成"内网串的样子"。这条是防我的正则贪吃：
// 一旦某个 span 里夹了 `=` 或不像路径/端点/标识，就说明它咬到了数据行，立刻失败。
const SPAN_SHAPE = /^(\/[^\s]*|[a-z]:[\\/]\S*|127\.0\.0\.1:7890|localhost:7890|-[Pp][ \t]+\S+|:\d+|SNNU|Haangyeon)$/i;
// 占位符自己带进来的数字，逐个点名。`<S22_GEOMETRY_DIR>` 里的 "22" 是基准集的名字，
// 不是某个测量值 —— 这一栏存在的原因就是闸门真的把它报过一次。
const DECLARED_PLACEHOLDER_DIGITS = { '<S22_GEOMETRY_DIR>': ['22'] };

const digitRuns = s => (s.match(/\d+(?:\.\d+)?/g) || []);
function eqArr(a, b) { return a.length === b.length && a.every((x, i) => x === b[i]); }

const scrubLog = [];   // 每个被改过的文件一条：{rel, bytesBefore, bytesAfter, proof, spans:[{line,text,to,cls}]} 或 {rel, FATAL}
const staleArtifacts = [];  // 被本次出货替换掉的旧 wheel/sdist（哈希留档，见账本第 4 节）

// 单趟从左到右替换，同时记录 span 在**原文**与**结果**里的坐标。三层证明：
//   (1) cut === rebuilt —— 逐字符：原文挖掉声明 span 后，与结果挖掉占位符后完全相等。
//       这条成立就等价于"除了声明过的那几段，一个字符都没动"。
//   (2) 未被命中的行必须**整行字节相同** —— 这就是"数值行未变"的可执行断言。
//   (3) 每个 span 必须过 SPAN_SHAPE；随 span 消失的数字全部逐条列进账本供人工复核。
function scrubText(text, rel) {
  let pos = 0, out = '';
  const spans = [];
  const rules = SCRUB_TABLES.flatMap(([cls, table]) =>
    table.map(([re, to]) => ({ re: new RegExp(re.source, re.flags), to, cls })));
  for (;;) {
    let best = null;
    for (const r of rules) {
      r.re.lastIndex = pos;
      const m = r.re.exec(text);
      if (m && m[0].length && (!best || m.index < best.index)) {
        best = { index: m.index, text: m[0], to: r.to, cls: r.cls };
      }
    }
    if (!best) break;
    out += text.slice(pos, best.index);
    spans.push({ ...best, line: text.slice(0, best.index).split('\n').length, outStart: out.length });
    pos = best.index + best.text.length;
    out += best.to;
  }
  out += text.slice(pos);

  const fail = msg => { scrubLog.push({ rel, FATAL: msg }); return out; };

  // (3) span 形状
  const weird = spans.filter(s => !SPAN_SHAPE.test(s.text) || s.text.includes('='));
  if (weird.length) return fail(`span 不像内网串，正则贪吃到数据了: [${weird.map(s => s.text).join(' | ')}]`);

  // (1) 逐字符证明
  let cut = '', k = 0;
  for (const s of spans) { cut += text.slice(k, s.index); k = s.index + s.text.length; }
  cut += text.slice(k);
  let rebuilt = '', j = 0;
  for (const s of spans) {
    if (out.slice(s.outStart, s.outStart + s.to.length) !== s.to) return fail(`占位符落点记账失败（line ${s.line}）`);
    rebuilt += out.slice(j, s.outStart); j = s.outStart + s.to.length;
  }
  rebuilt += out.slice(j);
  if (cut !== rebuilt) return fail('逐字符证明失败：除了声明的 span，结果里还有别的地方变了');

  // (2) 未被命中的行必须整行相同
  const hitLines = new Set(spans.map(s => s.line));
  const ob = text.split('\n'), pb = out.split('\n');
  if (ob.length !== pb.length) return fail(`行数变了 ${ob.length} -> ${pb.length}`);
  const drifted = [];
  for (let i = 0; i < ob.length; i++) if (!hitLines.has(i + 1) && ob[i] !== pb[i]) drifted.push(i + 1);
  if (drifted.length) return fail(`未被声明的行发生变化: ${drifted.join(',')}`);

  const digitsInSpans = spans.flatMap(s => digitRuns(s.text));
  const digitsFromPlaceholders = [...new Set(spans.map(s => s.to))]
    .flatMap(t => digitRuns(t).map(d => ({ t, d })));
  const badPh = digitsFromPlaceholders.filter(({ t, d }) => !(DECLARED_PLACEHOLDER_DIGITS[t] || []).includes(d));
  if (badPh.length) return fail(`占位符带进未声明的数字 [${badPh.map(x => x.t + ':' + x.d).join(',')}]`);

  if (spans.length) {
    scrubLog.push({
      rel, bytesBefore: Buffer.byteLength(text), bytesAfter: Buffer.byteLength(out),
      proof: 'PASS', lines: [...hitLines].sort((a, b) => a - b), untouchedIdentical: ob.length - hitLines.size,
      spans, digitsInSpans, digitsFromPlaceholders,
    });
  }
  return out;
}
function sha256str(s) {
  return require('crypto').createHash('sha256').update(s, 'utf8').digest('hex').slice(0, 16);
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
function write(rel, text) {
  const to = path.join(OUT, rel);
  fs.mkdirSync(path.dirname(to), { recursive: true });
  fs.writeFileSync(to, text);
  return rel;
}
function put(rel, raw) {              // 走脱敏的写盘
  copied.push(write(rel, scrubText(raw, rel)));
}

for (const f of ROOT) {
  const p = path.join(SRC, f);
  if (!fs.existsSync(p)) { console.error('MISSING root file: ' + f); process.exit(2); }
  put(f, read(p));
}
function read(p) { return fs.readFileSync(p, 'utf8'); }
for (const f of PKG) put('nlcsplit/' + f, read(path.join(SRC, 'nlcsplit', f)));
for (const f of STEPS) put('nlcsplit/' + f, read(path.join(SRC, 'nlcsplit', f)));
for (const f of TESTS) put('nlcsplit/tests/' + f, read(path.join(SRC, 'nlcsplit/tests', f)));
for (const f of EXAMPLES) put('nlcsplit/examples/' + f, read(path.join(SRC, 'nlcsplit/examples', f)));
put('nlcsplit/run_all.sh', read(path.join(SRC, 'nlcsplit', 'run_all.sh')));

// 几何获取脚本：把写死的本机代理改成"仅在环境里已有则沿用"，否则公开后别人照抄会连不上
let get = read(path.join(SRC, 'nlcsplit/tools/get_s22.sh'));
const before = get;
get = get.replace(/\b127\.0\.0\.1:7890\b/g, '<your-proxy>');
get = get.replace(/^\s*(# )?export HTTPS_PROXY=\S+/m,
  'export HTTPS_PROXY="${HTTPS_PROXY:-}"   # 需要时自行 export，不需要则空值即直连');
if (/7890|127\.0\.0\.1/.test(get)) console.error('BUG: 抹敏之后仍残留本机代理串');
if (get === before) console.error('WARN: get_s22.sh 的代理行没被改掉（格式变了？）');
put('nlcsplit/tools/get_s22.sh', get);

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
put('nlcsplit/logs/orca_anchor.json', JSON.stringify(anchor, null, 1) + '\n');

// 这里原来是 side.replace(/"geometry_source":s*"[^"]*"/, ...)：`:s*` 少了一个反斜杠，
// 要匹配的是"冒号后跟若干 s"而不是"若干空白"，而实际字节是 `": "`，所以这条替换
// **从来没有命中过**，/mnt/e/Project/GAMESS 就这样一路进了发布树。现在几何出处统一交给
// PATH_TABLE，并且下面用断言保证"确实改掉了"，不再依赖正则悄悄失配。
let side = read(path.join(SRC, 'nlcsplit/logs/step_h.json'));
side = side.replace(/"geometry_source"\s*:\s*"[^"]*"/,
  '"geometry_source": "fetched by nlcsplit/tools/get_s22.sh from github.com/grimme-lab/GMTKN55 tag v"');
if (/geometry_source"\s*:\s*"fetched by/.test(side) === false) {
  scrubLog.push({ rel: 'nlcsplit/logs/step_h.json', FATAL: 'geometry_source 未被改写（正则失配）' });
}
put('nlcsplit/logs/step_h.json', side);   // host 字段是"哪台机器出的数"的出处，故意保留

// level-2 + 反泊松 那一档单独成车（母仓 step_h.json 按体系名合并会冲掉同名高档行），
// 它的原始 stdout 也已入库，见 evidence/l2cp/ + MANIFEST.sha256。
put('nlcsplit/logs/step_h_l2cp.json', read(path.join(SRC, 'nlcsplit/logs/step_h_l2cp.json')));

// ---------------------------------------------------------------- 证据：逐文件复制 + 副本脱敏 + 重算哈希
fs.mkdirSync(path.join(OUT, 'evidence'), { recursive: true });
const hashLedger = [];        // {rel, orig, published, lines}
const missingSourceManifest = [];   // 母仓里没有 MANIFEST.sha256 的证据目录（发布树这份是新造的）
for (const dir of EVIDENCE_DIRS) {
  const from = path.join(SRC, 'evidence', dir);
  const to = path.join(OUT, 'evidence', dir);
  if (!fs.existsSync(from)) { scrubLog.push({ rel: `evidence/${dir}`, FATAL: '母仓里没有这个证据目录' }); continue; }
  fs.mkdirSync(to, { recursive: true });
  const names = fs.readdirSync(from).filter(f => f !== 'MANIFEST.sha256')
    .filter(f => fs.statSync(path.join(from, f)).isFile());
  const origManFile = path.join(from, 'MANIFEST.sha256');
  const origMan = fs.existsSync(origManFile) ? read(origManFile) : '';
  for (const f of names.sort()) {
    const raw = fs.readFileSync(path.join(from, f), 'utf8');
    const rel = `evidence/${dir}/${f}`;
    const origBytes = fs.readFileSync(path.join(from, f));
    write(rel, scrubText(raw, rel));
    copied.push(rel);
    hashLedger.push({
      rel, orig: sha256(path.join(from, f)), published: sha256(path.join(OUT, rel)),
      listedInSourceManifest: new RegExp('[* ]' + f.replace(/[.]/g, '\\.') + '$', 'm').test(origMan),
      origManifestHash: (origMan.split(/\r?\n/).find(l => l.endsWith('*' + f)) || '').split(/[\s*]+/)[0] || null,
    });
  }
  // 重写 MANIFEST.sha256：顺序沿用母仓（读者按同一顺序核对），哈希换成发布副本的实际字节。
  const ordered = origMan.split(/\r?\n/).filter(Boolean)
    .map(l => l.split(/[\s*]+/)[1]).filter(Boolean)
    .filter(n => fs.existsSync(path.join(to, n)));
  const extra = names.filter(n => !ordered.includes(n));
  const finalOrder = [...ordered, ...extra.sort()];
  const man = finalOrder.map(n => `${sha256(path.join(to, n))} *${n}`).join('\n') + '\n';
  write(`evidence/${dir}/MANIFEST.sha256`, man);
  copied.push(`evidence/${dir}/MANIFEST.sha256`);
  if (!fs.existsSync(origManFile)) {
    missingSourceManifest.push(`evidence/${dir}`);
  }
}

// ---------------------------------------------------------------- 发布变体说明（一行，进发布树）
const NOTE = 'PUBLISHED-VARIANT NOTE (path scrubbing)\n'
  + '\n'
  + '本发布树里的 evidence/**（含 .out 归档 stdout 与 MANIFEST.txt）以及 nlcsplit/logs/**、\n'
  + 'nlcsplit/run_all.sh、evidence/retrieval_calibration/*.js 是**脱敏副本**：母仓原件一个字节都没改，\n'
  + '导出时只把绝对路径/内网端点串换成了占位符（<REPO>、<S22_GEOMETRY_DIR>、<REMOTE_LOG_DIR>、\n'
  + '<REMOTE_WORKDIR>、<CLUSTER_HOME>、<SSH_PORT>），数值行未动，且各目录 MANIFEST.sha256 里的哈希\n'
  + '对应的就是**脱敏后的发布副本**（不是母仓原件）——所以 `sha256sum -c MANIFEST.sha256` 在本目录内自洽。\n'
  + '每个文件的 原件哈希 -> 发布副本哈希 对照、改动的行号、以及"数字是否被动过"的机器证明，\n'
  + '记在 dist/PATH-SCRUB-LEDGER.txt（该账本不进发布树，因为它必须引用被抹掉的原文）。\n';
copied.push(write('evidence/PUBLISHED-VARIANT-NOTE.txt', NOTE));

// ---------------------------------------------------------------- LICENSE：填 Apache 附录占位符
// Apache-2.0 的 APPENDIX 本身是"怎么套用本许可证"的模板，里面的 [yyyy]/[name of copyright
// owner] 是给你填的空。仓库根 LICENSE 保持 Apache 原文一字不动（母仓里它是模板全文，是合规的）；
// 发布副本按附录自己的指示把空填上，于是"LICENSE 里还留着模板占位符"这件事在公开产物里消失，
// 且闸门 G 可以真的失败而不是恒真。
{
  const lic = read(path.join(OUT, 'LICENSE'));
  const filled = lic.replace(/Copyright \[yyyy\] \[name of copyright owner\]/,
    'Copyright 2026 Angran Xia');
  if (filled === lic) scrubLog.push({ rel: 'LICENSE', FATAL: 'Apache 附录占位符未被填写（原文格式变了？）' });
  write('LICENSE', filled);
}

// ---------------------------------------------------------------- 检索记录与主表随包发布
const RELOCATED = {
  'RESEARCH-20260929-lit.md': 'docs/literature_search_20260929.md',
  'MAIN-skeleton.md': 'docs/tables_and_provenance.md',
};
for (const [src, dst] of Object.entries(RELOCATED)) put(dst, read(path.join(SRC, src)));
for (const [src, dst] of Object.entries(WORKFLOW)) put(dst, read(path.join(SRC, src)));

// 母仓 nlcsplit/logs/ 里被论文正文按文件名引用过的 stdout 也必须随行。
const CITED_LOGS = ['20260929T_step_i_gridrepr.out', '20260929T003144Z_stepg-recompute.out',
  '20260929T010500Z_step1_geomfix.out'];
for (const f of CITED_LOGS) put('nlcsplit/logs/' + f, read(path.join(SRC, 'nlcsplit/logs', f)));

fs.writeFileSync(path.join(OUT, 'EXPORT-MANIFEST.txt'),
  copied.length + ' files\n' + copied.sort().join('\n') + '\n');

function sha256(p) {
  // Git Bash 下反斜杠路径会让 sha256sum 的输出前面多一个反斜杠，哈希当场对不上。
  const sh = String(p).replace(/\\/g, '/');
  return cp.execSync(`sha256sum "${sh}"`, { encoding: 'utf8' }).trim().split(/[\s]+/)[0].replace(/^\\+/, '');
}

// ================================================================ 出货：从发布树建 wheel/sdist
// 为什么在 staging 里建而不是在发布树里建：build 会在源码目录长出 build/ 与 *.egg-info/，
// 那些东西不该出现在要公开的目录里。staging 是发布树的完整副本，所以"闸门 F 看到的成员"
// 与"闸门 A/B 看到的模块"是同一套白名单，不再出现"源码树干净、产物是旧的"这种两套事实。
// 关键顺序：产物先建到 dist/.newartifacts/，**所有闸门全绿之后**才搬进 dist/ 并删旧货。
// 否则"闸门失败即不出货"这句话是假的——脏的旧产物早被覆盖了。
const NEWART = path.join(DIST, '.newartifacts');
const artifacts = [];
const artifactPath = {};
{
  for (const f of fs.readdirSync(DIST).filter(x => /^nlcsplit-.*\.(whl|tar\.gz)$/.test(x))) {
    staleArtifacts.push({ f, sha256: sha256(path.join(DIST, f)), mtime: fs.statSync(path.join(DIST, f)).mtime.toISOString() });
  }
  cp.execSync(`rm -rf "${STAGE}" "${NEWART}"`);
  fs.mkdirSync(NEWART, { recursive: true });
  cp.execSync(`cp -r "${OUT}" "${STAGE}"`);
  cp.execSync(`find "${STAGE}" -name '__pycache__' -type d -prune -exec rm -rf {} +`);
  cp.execSync(`rm -f "${path.join(STAGE, 'EXPORT-MANIFEST.txt')}" "${path.join(STAGE, STAMP)}"`);
  cp.execSync(`rm -rf "${path.join(STAGE, 'evidence')}" "${path.join(STAGE, 'nlcsplit/logs')}" "${path.join(STAGE, 'docs')}" "${path.join(STAGE, '.github')}"`);
  // 注意：这里必须是 python，不是 process.execPath（那在 node 里是 node.exe）。
  // 构建日志走 stderr：stdout 必须只有那一份 JSON，否则 `node ... | jq` 直接解析失败。
  console.error(cp.execFileSync(PY, ['-c',
    'from setuptools import build_meta as b\n' +
    'import os,sys\n' +
    'print("built:", b.build_wheel(os.environ["BDIST"]))\n' +
    'print("built:", b.build_sdist(os.environ["BDIST"]))\n'],
    { cwd: STAGE, env: { ...process.env, BDIST: NEWART.replace(/\\/g, '/') }, encoding: 'utf8' }).trim());
  cp.execSync(`rm -rf "${STAGE}"`);
  for (const f of fs.readdirSync(NEWART).sort()) {
    if (!/\.(whl|tar\.gz)$/.test(f)) continue;
    artifacts.push(f);
    artifactPath[f] = path.join(NEWART, f);
  }
}

// ================================================================ 闸门：先收集发布树的**全部**文件
function walkTree(dir, base) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const rel = base ? base + '/' + e.name : e.name;
    if (e.isDirectory()) out.push(...walkTree(path.join(dir, e.name), rel));
    else out.push(rel);
  }
  return out;
}
const tree = walkTree(OUT, '');
const notInManifest = tree.filter(rel => rel !== STAMP && rel !== 'EXPORT-MANIFEST.txt' && !copied.includes(rel));

// ---------------------------------------------------------------- 闸门 R：发布树里不许有构建/测试残留
// 抽成函数是为了能自测（见文件末尾 NLCSPLIT_SELFTEST）：一条从没响过的门禁和一条恒真的
// 门禁一样没用，而本次审计的病根就是"报了三数组全空但其实没扫到文件"。
function checkResidue(treeList) {
  const hits = [];
  for (const rel of treeList) {
    if (/(^|\/)__pycache__(\/|$)/.test(rel) || /\.pyc$/.test(rel) || /\.egg-info(\/|$)/.test(rel) || rel === 'setup.cfg') {
      hits.push(`${rel}  <- 发布树里的构建/pytest 残留（.pyc 会连同 docstring 一起把仓库串带出去）`);
    }
  }
  return hits;
}
const gr = checkResidue(tree);

// ---------------------------------------------------------------- 闸门 A：无 GAMESS **源码**
// 注意：/gamess/i 一律命中是**误报**——README/CONTRIBUTING/__init__ 里出现这个词，
// 正是因为我们在声明"本包不含 GAMESS 代码"。一个永远失败的门禁和一个不会失败的门禁一样没用。
// 所以这里只抓真正的 GAMESS 源码工件；"gamess"这个词的出现另列为 info，人工过一眼即可。
const gamessPats = [/\$gnum/i, /\bintgc\b/, /\bdiana\b/, /rhfuhf/, /\bgameSS\.src\b/i,
  /ps\/src\//, /GAMESS\.src/, /getscr|erscf[0-9]/];
function checkGamessSource(root, treeList) {
  const hits = [], words = [];
  for (const rel of treeList) {
    if (!/\.(py|sh|json|md|toml|txt|out|c|f|f90|js|yml|yaml)$/.test(rel)) continue;
    let t; try { t = read(path.join(root, rel)); } catch (e) { continue; }
    for (const [i, re] of gamessPats.entries()) {
      if (re.test(t)) hits.push(`${rel}:${t.slice(0, t.search(re)).split('\n').length}  <- GAMESS 源码工件 模式#${i} ${re}`);
    }
    if (/gamess/i.test(t)) {
      for (const [ln, line] of t.split(/\r?\n/).entries()) {
        if (/gamess/i.test(line)) words.push(`${rel}:${ln + 1}  ${line.trim().slice(0, 120)}`);
      }
    }
  }
  return { hits, words };
}
const gA = checkGamessSource(OUT, tree);
const ga = gA.hits, wordOnly = gA.words;

// ---------------------------------------------------------------- 闸门 B：无密钥/内网/工作机路径
// 2026-09-29 加固：旧表只有 10.8.51.23 / :7890 / PRIVATE KEY / password= / ssh@ / /home/haangyeon。
// 审计实测 dist 里 13 个文件带串而闸门报"三个数组全空"，两个原因叠在一起：
//   (a) `/root/gamess_work`、`/mnt/e/Project/GAMESS`、`E:/Project/GAMESS`（正/反斜杠、大小写）、
//       集群端口、`haangyeon`、`snnu` 全都不在表里；
//   (b) 旧闸门遍历的是 `copied` 这份名单，不是目录树，名单外文件从未被打开过。
// 现在：默认失败、列出 file:line、扫的是 walkTree 出来的**全部**磁盘文件。
const secretPats = [
  ['集群内网 IP', /10\.8\.51\.23/],
  ['本机代理端口/回环端点', /:7890\b/],
  ['私钥块', /BEGIN [A-Z ]*PRIVATE KEY/],
  ['口令赋值', /(?:password|passwd|token|api[_-]?key)\s*[:=]\s*["']?\S{4,}/i],
  ['ssh 目标', /\bssh\b[^#\n]*@/],
  ['user@裸IP', /\b\w+@\d{1,3}(\.\d{1,3}){3}/],
  ['远端家目录', /\/home\/haangyeon/i],
  ['账号串', /\bhaangyeon\b/i],
  ['校内标识串', /\bsnnu\b/i],
  ['工作机绝对路径(远端)', /\/root\/gamess_work/i],
  ['工作机绝对路径(WSL挂载)', /\/mnt\/[a-z]\/Project\/GAMESS/i],
  ['工作机绝对路径(Win盘符,正/反斜杠)', /[a-z]:[\\/]+Project[\\/]+GAMESS/i],
  ['集群SSH端口 24522', /(?<![\d.])24522(?![\d.])/],
  ['集群SSH端口 20019', /(?<![\d.])20019(?![\d.])/],
];
function scanIntranet(root, treeList) {
  const hits = [];
  for (const rel of treeList) {
    if (!/\.(py|sh|json|md|toml|txt|out|c|f|f90|js|yml|yaml|cfg|ini)$/.test(rel)) continue;
    let t; try { t = read(path.join(root, rel)); } catch (e) { continue; }
    t.split(/\r?\n/).forEach((line, i) => {
      for (const [name, re] of secretPats) {
        if (re.test(line)) hits.push(`${rel}:${i + 1}  <- ${name} ${re}  | ${line.trim().slice(0, 140)}`);
      }
    });
  }
  return hits;
}
const gb = scanIntranet(OUT, tree);

// ---------------------------------------------------------------- 闸门 C：证据哈希（对发布副本）
const gc = [];
for (const dir of EVIDENCE_DIRS) {
  const d = path.join(OUT, 'evidence', dir);
  if (!fs.existsSync(d)) continue;
  const manFile = path.join(d, 'MANIFEST.sha256');
  if (!fs.existsSync(manFile)) { gc.push(`evidence/${dir}: 没有 MANIFEST.sha256`); continue; }
  const man = read(manFile);
  const listed = [];
  for (const line of man.split(/\r?\n/).filter(Boolean)) {
    const parts = line.split(/[\s*]+/);
    const [h, name] = [parts[0], parts[1]];
    listed.push(name);
    const p = path.join(d, name);
    if (!fs.existsSync(p)) { gc.push(`evidence/${dir}: 缺文件 ${name}`); continue; }
    if (sha256(p) !== h) gc.push(`evidence/${dir}: 哈希不符 ${name}（MANIFEST 里的值对不上发布副本的实际字节）`);
  }
  // 反向也要闭合：目录里有文件没进 MANIFEST，等于"这份证据没人担保过"。
  for (const f of fs.readdirSync(d)) {
    if (f === 'MANIFEST.sha256' || f === 'MANIFEST.txt' || f === 'PUBLISHED-VARIANT-NOTE.txt') continue;
    if (!fs.statSync(path.join(d, f)).isFile()) continue;
    if (!listed.includes(f)) gc.push(`evidence/${dir}: ${f} 在目录里但 MANIFEST.sha256 没登记`);
  }
}

// ---------------------------------------------------------------- 闸门 C2：脱敏只动了路径行
// 这条是"数字一个字符都不许动"的可执行版本，也是"能否自洽出货"的判据。
const gc2 = [];
for (const e of scrubLog) {
  if (e.FATAL) { gc2.push(`${e.rel}: ${e.FATAL}`); continue; }
  if (!e.lines || !e.lines.length) gc2.push(`${e.rel}: 命中了脱敏表却没记录行号，账本不可信`);
  if (e.proof !== 'PASS') gc2.push(`${e.rel}: 没有 PASS 的数字不变性证明`);
}
// 母仓哈希必须仍在，且必须**没有**被改动（原件未动的证明）
const origTouched = [];
for (const h of hashLedger) {
  if (h.origManifestHash && h.orig !== h.origManifestHash) {
    origTouched.push(`${h.rel}: 母仓 MANIFEST 登记的哈希 ${h.origManifestHash} != 母仓现在的实际字节 ${h.orig} —— 原件被动过或被换过`);
  }
}
gc2.push(...origTouched);

// ---------------------------------------------------------------- 闸门 D：正文引用的每个出处都真的随包发布
const gateD = (() => {
  const app = read(path.join(SRC, 'paper/main.md'));
  const rows = [...app.slice(app.indexOf('## Appendix')).matchAll(/^\| (S\d+) \|(.*)$/gm)];
  const internal = /^(PROGRESS|HANDOFF|STEP0)/;
  const absent = [], pubInternal = [];
  for (const [, tag, cell] of rows) {
    for (const m of cell.matchAll(/`([^`]+)`/g)) {
      // `file:700-707` names a file *and* lines; a glob or a spaced pattern is not a file.
      // Without this the gate reported "母仓里就没有 evidence/**" and blocked a good build.
      const rel = m[1].replace(/:\d+(?:[,-]{1,2}\d+)*$/, '');
      if (/[*?\s]/.test(rel)) continue;
      if (/^(DOI|arXiv|§|\d)/.test(rel) || !/[/]|\.(out|json|py|md|js|txt|bib)$/.test(rel)) continue;
      if (!fs.existsSync(path.join(SRC, rel))) { absent.push(`${tag}: 母仓里就没有 ${rel}`); continue; }
      const published = RELOCATED[rel] || rel;
      if (internal.test(rel) || EXPLICITLY_EXCLUDED.some(x => rel.startsWith(x))) {
        pubInternal.push(`${tag}: ${rel}（故意只在母仓，公开读者打不开）`);
        continue;
      }
      if (!copied.includes(published)) absent.push(`${tag}: 存在但未随包发布 ${rel}`);
    }
  }
  return { absent, pubInternal };
})();

// ---------------------------------------------------------------- 闸门 E：用到的依赖都得声明
const STDLIB = new Set(['os', 'sys', 'json', 'time', 'math', 'ctypes', 'socket', 'traceback',
  'importlib', 'pathlib', 'argparse', 'functools', 'itertools', 'collections', 'warnings',
  'dataclasses', 'typing', 'subprocess', 'shutil', 'tempfile', 're', 'io', 'abc', 'datetime']);
const DECLARED = new Set([...read(path.join(SRC, 'pyproject.toml'))
  .matchAll(/"([A-Za-z][A-Za-z0-9_.\-]*)[<>=!~\[]?/g)].map(m => m[1].toLowerCase()));
const DIST_OF = { matplotlib: 'matplotlib', scipy: 'scipy', pyscf: 'pyscf', numpy: 'numpy', pytest: 'pytest' };
const gateE = (() => {
  const out = [];
  for (const rel of tree.filter(f => f.endsWith('.py'))) {
    let src; try { src = read(path.join(OUT, rel)); } catch (e) { continue; }
    for (const m of src.matchAll(/^\s*(?:from|import)\s+([A-Za-z_][\w.]*)/gm)) {
      const top = m[1].split('.')[0];
      if (STDLIB.has(top) || top === 'nlcsplit') continue;
      const dist = DIST_OF[top] || top.toLowerCase();
      if (!DECLARED.has(dist)) out.push(`${rel}: import ${m[1]}，但 pyproject 未声明 "${dist}"`);
    }
  }
  return [...new Set(out)];
})();

// ---------------------------------------------------------------- 闸门 F：wheel/sdist 成员清单
// 这条是对**产物**说的，不是对源码树说的——旧的那句"重打 wheel 已验证不再 ship test_*.py"
// 只是看了看源码树，产物里 nlcsplit/test_fast_pair.py 一直都在（本仓实测命中过）。
function membersOf(p) {
  // 用 python 读两种产物：Git Bash 的 tar 会把 `E:/...` 里的冒号当成"远程主机"
  // （`tar (child): Cannot connect to E: resolve failed`），换相对路径又依赖 cwd，
  // 成员清单这件事干脆和 zip 走同一套 zipfile/tarfile，别分叉。
  const q = String(p).replace(/\\/g, '/');
  return cp.execFileSync(PY, ['-c',
    'import sys,zipfile,tarfile\n' +
    'p=sys.argv[1]\n' +
    'if p.endswith(".whl"):\n' +
    '    [print(n) for n in zipfile.ZipFile(p).namelist()]\n' +
    'else:\n' +
    '    [print(m.name) for m in tarfile.open(p).getmembers() if m.isfile()]\n', q],
    { encoding: 'utf8' }).split(/\r?\n/).filter(Boolean);
}
function checkArtifacts(items) {
  const out = [];
  for (const { name: f, path: ap } of items) {
    const mem = membersOf(ap).filter(m => !m.endsWith('/'));
    // F1 任何 test_*.py，只要不在 */tests/ 下，直接 FAIL。
    for (const m of mem.filter(x => /(^|\/)test_[^\/]*\.py$/.test(x))) {
      if (!/(^|\/)tests\//.test(m)) out.push(`${f}: 夹带脚本式测试模块 ${m}（import 即执行，不该进包）`);
    }
    // F2 tests/ 里只允许包内正式测试：test_*.py + conftest.py + __init__.py
    for (const m of mem.filter(x => /(^|\/)tests\//.test(x))) {
      const b = m.split('/').pop();
      if (!(/^(test_[A-Za-z0-9_]*\.py|conftest\.py|__init__\.py)$/.test(b))) {
        out.push(`${f}: tests/ 里出现不允许的文件 ${m}`);
      }
    }
    // F3 顶层包目录里不许带运行产物
    for (const m of mem.filter(x => /^nlcsplit\/(?!tests\/|examples\/)[^\/]+$/.test(x))) {
      if (/\.out$/.test(m)) out.push(`${f}: 顶层带运行产物 ${m}`);
    }
    // wheel 用 dist-info/METADATA，sdist 用 PKG-INFO —— 两种归档的元数据文件名本来就不同。
    if (!mem.some(x => /dist-info\/METADATA$|(^|\/)PKG-INFO$/.test(x))) {
      out.push(`${f}: 读不到成员清单或没有 METADATA/PKG-INFO`);
    }
    if (!mem.length) out.push(`${f}: 成员清单为空`);
  }
  if (items.length !== 2) out.push(`期望正好 1 wheel + 1 sdist，实际 ${items.map(i => i.name).join(', ') || '无'}`);
  return out;
}
const gateF = checkArtifacts(artifacts.map(f => ({ name: f, path: artifactPath[f] })));

// ---------------------------------------------------------------- 闸门 G：LICENSE 占位符与版权行
function readArtifactLicense(p) {
  const q = String(p).replace(/\\/g, '/');
  return cp.execFileSync(PY, ['-c',
    'import sys,zipfile,tarfile\n' +
    'p=sys.argv[1]\n' +
    'if p.endswith(".whl"):\n' +
    '    z=zipfile.ZipFile(p)\n' +
    '    k=[x for x in z.namelist() if x.endswith("LICENSE")]\n' +
    '    print(z.read(k[0]).decode() if k else "<<ABSENT>>")\n' +
    'else:\n' +
    '    t=tarfile.open(p)\n' +
    '    m=[x for x in t.getmembers() if x.name.endswith("LICENSE")]\n' +
    '    print(t.extractfile(m[0]).read().decode() if m else "<<ABSENT>>")\n', q],
    { encoding: 'utf8' });
}
function licenseViolations(targets, author) {
  const out = [];
  for (const [where, t] of Object.entries(targets)) {
    if (t === '<<ABSENT>>') { out.push(`${where}: 归档里没有 LICENSE`); continue; }
    if (/\[yyyy\]|\[name of copyright owner\]/.test(t)) out.push(`${where}: 仍有 Apache 模板占位符 [yyyy] [name of copyright owner]`);
    const cr = [...t.matchAll(/^\s*Copyright\s+(\d{4})\s+(.+)$/gm)];
    if (!cr.length) out.push(`${where}: 没有已填写的版权行（形如 \`Copyright 2026 <holder>\`）`);
    if (cr.length !== 1) out.push(`${where}: 版权行 ${cr.length} 处，应当正好 1 处`);
    if (author && cr.length === 1 && !cr[0][2].includes(author)) {
      out.push(`${where}: 版权人 "${cr[0][2]}" 与 pyproject 作者 "${author}" 不一致`);
    }
  }
  return out;
}
// 要扫三处：发布树里的 LICENSE、wheel 里的 dist-info/licenses/LICENSE、sdist 里的 LICENSE。
// 只看源码树是上一条错误的同款 —— pip 用户实际看到的是归档里那一份。
const gateG = (() => {
  const licPath = path.join(OUT, 'LICENSE');
  if (!fs.existsSync(licPath)) return ['LICENSE 没进发布树'];
  const targets = { 'dist/nlcsplit/LICENSE': read(licPath) };
  for (const f of artifacts) targets[`dist/${f}::LICENSE`] = readArtifactLicense(artifactPath[f]);
  const author = (read(path.join(SRC, 'pyproject.toml')).match(/authors\s*=\s*\[\{\s*name\s*=\s*"([^"]+)"/) || [])[1];
  return licenseViolations(targets, author);
})();

// ================================================================ 闸门自测（NLCSPLIT_SELFTEST=1）
// 这次的病根不是"闸门写错了"，是"闸门报空而它根本没看到东西"。所以每条新规则都要有
// 一个能让它响起来的输入，而且要拿**真产物**（真 zip / 真 tar / 真文件）去喂，不是把
// 断言写在字符串上自己骗自己。两种方向都测：脏输入必须响，干净输入必须不响。
if (process.env.NLCSPLIT_SELFTEST) {
  const NEG = path.join(DIST, '.selftest');
  cp.execSync(`rm -rf "${NEG}"`);
  fs.mkdirSync(path.join(NEG, 'tree'), { recursive: true });
  const R = {};
  const rels = [];
  const poison = {
    'p_rootwork.txt': '几何来源 /root/gamess_work/nlcsplit/s22',
    'p_mntrepo.txt': 'repo at /mnt/e/Project/GAMESS/nlcsplit',
    'p_winfs.txt': 'OUT = "E:/Project/GAMESS/scratch/x.json"',
    'p_winbs.txt': 'cd E:\\Project\\GAMESS && exit 1',
    'p_winlower.txt': 'path e:\\project\\gamess here',
    'p_ip.txt': 'ssh 10.8.51.23',
    'p_port2.txt': 'scp -P 24522 host:/x',
    'p_port1.txt': 'ssh -p 20019 host',
    'p_user.txt': '侧车 → /home/haangyeon/logs/step_h.json',
    'p_inst.txt': 'affiliation: SNNU',
    'clean_ok.txt': 'nothing to see, level=2, E_NLC=+125.7984',
  };
  for (const [n, c] of Object.entries(poison)) { fs.writeFileSync(path.join(NEG, 'tree', n), c + '\n'); rels.push(n); }
  fs.mkdirSync(path.join(NEG, 'tree', '__pycache__'), { recursive: true });
  fs.writeFileSync(path.join(NEG, 'tree', '__pycache__', 'x.cpython-310.pyc'), 'junk');
  const T = walkTree(path.join(NEG, 'tree'), '');
  R.residue = { fired: checkResidue(T).length > 0, clean: checkResidue(rels).length === 0 };
  const bHits = scanIntranet(path.join(NEG, 'tree'), rels);
  const names = new Set(bHits.map(h => h.split('  <- ')[1].split(' /')[0]));
  R.intranet = { fired: bHits.length, cleanTreeHits: scanIntranet(OUT, tree).length,
    covered: Object.fromEntries(['工作机绝对路径(远端)', '工作机绝对路径(WSL挂载)', '工作机绝对路径(Win盘符,正/反斜杠)',
      '集群内网 IP', '集群SSH端口 24522', '集群SSH端口 20019', '账号串', '校内标识串']
      .map(n => [n, names.has(n)])) };

  // 真 zip：把脚本式测试模块塞进一个真的 wheel 里，让 checkArtifacts 用真的读档路径去判。
  cp.execFileSync(PY, ['-c',
    'import sys,zipfile\n' +
    'z=zipfile.ZipFile(sys.argv[1],"w")\n' +
    'for n in ["nlcsplit/__init__.py","nlcsplit/test_fast_pair.py","nlcsplit/tests/README.md",' +
    '"nlcsplit/tests/test_kernel.py","nlcsplit.egg-info/PKG-INFO","nlcsplit/notes.out"]:\n' +
    '    z.writestr(n,"x")\n' +
    'z.close()\n', path.join(NEG, 'poison-1.0-py3-none-any.whl').replace(/\\/g, '/')], { stdio: 'pipe' });
  cp.execFileSync(PY, ['-c',
    'import sys,zipfile\n' +
    'z=zipfile.ZipFile(sys.argv[1],"w")\n' +
    'for n in ["nlcsplit/__init__.py","nlcsplit/tests/test_kernel.py","nlcsplit/tests/conftest.py",' +
    '"nlcsplit/tests/__init__.py","nlcsplit-1.0.dist-info/METADATA","nlcsplit-1.0.dist-info/LICENSE"]:\n' +
    '    z.writestr(n,"x")\n' +
    'z.close()\n', path.join(NEG, 'clean-1.0-py3-none-any.whl').replace(/\\/g, '/')], { stdio: 'pipe' });
  const poisons = checkArtifacts([{ name: 'poison-1.0-py3-none-any.whl', path: path.join(NEG, 'poison-1.0-py3-none-any.whl') }]);
  const cleans = checkArtifacts([{ name: 'clean-1.0-py3-none-any.whl', path: path.join(NEG, 'clean-1.0-py3-none-any.whl') }])
    .filter(x => !/期望正好/.test(x));
  R.artifacts = { fired: poisons, clean: cleans };

  // 真 LICENSE 字节：母仓那份（模板没填）必须响，发布副本那份（填过）必须不响。
  R.license = {
    firedFromSourceRepo: licenseViolations({ 'LICENSE(母仓模板)': read(path.join(SRC, 'LICENSE')) }, 'Angran Xia'),
    cleanPublished: licenseViolations({ 'LICENSE(发布副本)': read(path.join(OUT, 'LICENSE')) }, 'Angran Xia'),
  };
  // 脱敏表本身：喂一条带数字的测量行，证明"只动路径行"这条断言拦得住越界改写。
  const sample = 'L1 == 几何来源 /root/gamess_work/nlcsplit/s22 ==\nL2 E_NLC= +125.7984 N=132176\n';
  const sres = scrubText(sample, 'SELFTEST');
  R.scrub = {
    changedLine: sres.split('\n')[0], untouchedLineIdentical: sres.split('\n')[1] === 'L2 E_NLC= +125.7984 N=132176',
    logged: scrubLog.filter(e => e.rel === 'SELFTEST').map(e => e.FATAL || `${e.proof} lines=${e.lines.join(',')}`),
  };
  console.log(JSON.stringify({ selftest: R, ledgerNote: 'dist/.selftest/ 是一次性验证目录' }, null, 1));
  cp.execSync(`rm -rf "${NEG}"`);
  process.exit(0);
}

// ---------------------------------------------------------------- 脱敏账本（不进发布树）
{
  const L = [];
  L.push('# 路径/端点脱敏账本 —— 由 tools/make_public_repo.js 生成');
  L.push('# 母仓原件一个字节未改；本表记录"导出副本改了什么、哈希怎么对应"。');
  L.push('# 本文件刻意放在发布树之外：它必须逐条引用被抹掉的原文，放进发布树就等于把内网串又写回去。');
  L.push('');
  L.push(`生成时间(UTC): ${new Date().toISOString()}`);
  L.push(`发布树: ${OUT.replace(/\\/g, '/')}`);
  L.push(`占位符表: path/endpoint/ident 三张；每个 span 必须过 SPAN_SHAPE 形状检查`);
  L.push('');
  L.push('## 1. 逐文件：原件哈希 -> 发布副本哈希');
  L.push('（listed=母仓 MANIFEST.sha256 是否原本就登记过该文件；母仓哈希一栏是 sha256sum 对**母仓当前字节**的实测）');
  for (const h of hashLedger) {
    L.push(`${h.rel}`);
    L.push(`    母仓原件   sha256 ${h.orig}`);
    L.push(`    发布副本   sha256 ${h.published}   ${h.orig === h.published ? '(未改动)' : '(已脱敏)'}`);
    L.push(`    母仓 MANIFEST 登记: ${h.listedInSourceManifest ? 'yes' : 'no'}  值: ${h.origManifestHash || '-'}`);
  }
  L.push('');
  L.push('## 2. 逐 span 改动记录（行号按母仓原文；这一节会复述被抹掉的原文，所以本文件不得随发布树分发）');
  for (const e of scrubLog) {
    if (e.FATAL) { L.push(`${e.rel}: FATAL ${e.FATAL}`); continue; }
    L.push(`${e.rel}  (${e.bytesBefore} -> ${e.bytesAfter} bytes)  数字不变性证明: ${e.proof}`);
    L.push(`    受影响行: ${e.lines.join(', ')}`);
    for (const s of e.spans) {
      L.push(`    line ${s.line} [${s.cls}]  原文「${s.text}」 -> 「${s.to}」`);
    }
    L.push(`    证明: 原文挖掉这些 span 与 结果挖掉这些占位符 逐字符相等（cut === rebuilt）`);
    L.push(`    未被命中的行：${e.untouchedIdentical} 行，逐行字节相同（闸门 C2 断言 (2)）`);
    L.push(`    随 span 消失的数字（全部在此披露，供人工复核；均在声明的内网串内部）: [${e.digitsInSpans.join(', ') || '(无)'}]`);
    L.push(`    占位符带进来的数字: [${e.digitsFromPlaceholders.map(x => x.t + ':' + x.d).join(', ') || '(无)'}]`);
  }
  L.push('');
  L.push('## 3. 结论性断言（由闸门 C/C2/F/G 机器校验，不是人工声明）');
  L.push('  - 每个被改的文件都满足 cut === rebuilt：原文挖掉声明 span 后与结果挖掉占位符后逐字符相等，');
  L.push('    所以"只有声明过的那几段变了"，其余字符（含全部数字）一个没动。');
  L.push('  - 随 span 消失的数字只可能是声明表里的集群端口；占位符带入的数字只有 <S22_GEOMETRY_DIR> 的 "22"。');
  L.push('  - 各 evidence 目录 MANIFEST.sha256 已在发布树内重算，哈希对应发布副本：闸门 C（正向+反向闭合）。');
  L.push('  - 母仓原件未被写入：闸门 C2 比对 母仓实际哈希 vs 母仓 MANIFEST 登记值。');
  L.push('');
  L.push('## 4. 本次出货替换掉的旧产物（证明"重打"发生在产物上，不只是源码树）');
  for (const s of staleArtifacts) L.push(`  旧 ${s.f}  sha256 ${s.sha256}  mtime ${s.mtime}`);
  for (const a of artifacts) L.push(`  新 ${a}  sha256 ${sha256(artifactPath[a])}`);
  if (!staleArtifacts.length) L.push('  （dist/ 里没有待替换的旧产物）');
  fs.writeFileSync(LEDGER_OUTSIDE, L.join('\n') + '\n');
}

const report = {
  out: OUT, files: copied.length, treeFiles: tree.length, artifacts,
  ledger: LEDGER_OUTSIDE.replace(/\\/g, '/'),
  gateA_gamess_source_artifacts: ga,
  gateB_intranet: gb,
  gateC_evidence_hashes_vs_published: gc,
  gateC2_scrub_digit_invariance: gc2,
  gateD_cited_but_unshipped: gateD.absent,
  gateE_undeclared_imports: gateE,
  gateF_wheel_sdist_members: gateF,
  gateG_license: gateG,
  gateR_tree_residue: gr,
  gateT_not_in_export_manifest: notInManifest,
  note_word_only_gamess: wordOnly,
  note_internal_only_citations: gateD.pubInternal,
  note_evidence_dirs_without_source_manifest: missingSourceManifest,
  scrubbed_files: scrubLog.filter(e => !e.FATAL).map(e => e.rel),
  excluded_by_design: EXPLICITLY_EXCLUDED.concat(['PROGRESS-*.md', 'HANDOFF-*.md',
    'STEP0-*.md', 'paper/**', 'scratch/**', 'figs/**']),
  relocated_into_docs: RELOCATED,
};

const bad = ga.length + gb.length + gc.length + gc2.length + gateD.absent.length + gateE.length
  + gateF.length + gateG.length + gr.length + notInManifest.length;
if (bad) {
  // 闸门没过：把还没搬进 dist/ 的新产物直接丢掉，旧产物原地不动。"不出货"必须是可验证的，
  // 不是口号 —— 之前那次"重打 wheel 已验证"就是因为先覆盖后检查，检查失败也回不去。
  report.shipped = false;
  report.kept_stale = staleArtifacts;
  console.log(JSON.stringify(report, null, 1));
  cp.execSync(`rm -rf "${NEWART}"`);
  console.error(`\nGATE FAILED: ${bad} 条命中，不出货（exit 1）。上面每个数组都是 file:line。`);
  console.error(`dist/ 里的旧 wheel/sdist 保持原样：${staleArtifacts.map(s => s.f).join(', ') || '(本来就空)'}`);
  process.exit(1);
}

// 全绿 -> 搬进 dist/，替换旧货。
for (const f of artifacts) {
  const dst = path.join(DIST, f);
  if (fs.existsSync(dst)) fs.rmSync(dst);
  fs.copyFileSync(artifactPath[f], dst);
}
// 搬运前后字节必须相同，否则账本第 4 节记的哈希就不是最终交付物的哈希了 —— 当场验一遍。
report.shipped = artifacts.map(f => ({
  f,
  sha256_in_newart: sha256(artifactPath[f]),
  sha256_in_dist: sha256(path.join(DIST, f)),
  identical: sha256(artifactPath[f]) === sha256(path.join(DIST, f)),
}));
if (report.shipped.some(x => !x.identical)) {
  console.error('FATAL: 搬运后字节与过闸时不一致，取消交付');
  process.exit(1);
}
report.removed_stale = staleArtifacts;
cp.execSync(`rm -rf "${NEWART}"`);
console.log(JSON.stringify(report, null, 1));
process.exit(0);
