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
 *   R 发布树无构建/测试残留      T 发布树每个文件都在导出清单里
 *   U 包内 import 的兄弟模块都得在树里
 *   V pip install . 会装的包目录模块，要么随 wheel 发、要么在这里具名给不发布的理由
 *
 * 2026-09-29 审计后的三处加固（都是被实测打脸加的）：
 *   1. 闸门 B 原来只抓"密钥的形状"，不抓工作机绝对路径。远端工作目录、WSL 挂载路径、
 *      Windows 盘符路径、集群端口、账号名、单位缩写全都不在表里，于是闸门报"数组为空"
 *      而 dist 里 13 个文件照旧带串。现在补齐——具体那十条写进
 *      tools/intranet_patterns.private.js（这些串本身是机构标识，不随包发布，理由见那个文件）。
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
const PKG = ['__init__.py', 'nlc.py', 'partition.py', 'geomlib.py', 'figures.py',
  // fastpair.py 是 P2 的主体，也被 step_j_scaling.py 直接 import。它原先**不在发布清单里**：
  // wheel 里没有这个模块，而随包发的 step 脚本却 import 它——读者从 wheel 里跑不出任何
  // 一个 P2 的数字。闸门 E 只查"外部依赖有没有声明"，查不出这种**包内**依赖，所以没人响。
  'fastpair.py'];
const STEPS = ['step1_validate.py', 'step2_convergence.py', 'step_b_scan.py', 'step_c_relaxation.py',
  'step_d_floor.py', 'step_e_kernel.py', 'step_f_dispersion.py', 'step_g_basis.py',
  'step_h_s22.py', 'step_i_gridrepr.py', 'step_k_population.py',
  // step_m_ccsdt.py：§3.2 那栏 CCSD(T) 阶梯的唯一生产者（S24）。它是包内脚本，
  // 不进清单的话闸门 V 会拦（"包目录里的模块要么白名单要么写理由"）。
  'step_m_ccsdt.py',
  'step_j_scaling.py',
  // step_l_sweep_compare.py 原先不在清单里：它是正文 §2.1 那个"与独立脚本一致到 2e-3"
  // 的**唯一**生产者，而 S21 只挂了被比的那份 raw sweep（里面没有比对列）。
  // 于是这句话在发布物里既没有脚本、也没有产物——正是闸门 D 存在的理由却被漏掉。
  'step_l_sweep_compare.py'];
const TESTS = ['__init__.py', 'conftest.py', 'test_geometry.py', 'test_kernel.py',
  'test_partition_factors.py', 'test_regression.py',
  // 不发 fastpair 的测试，等于"屏蔽机制已验证"这句话在发布物里没有证据。
  // test_fastpair_ide.py 仍然不发：它 import 的 fastpair_ide.py 是对照件，不在包里，
  // 发出去就是一道收集期 ImportError。
  'test_fastpair.py', 'test_tolerance_probe.py',
  // step_m_ccsdt.py 进包了（§3.2 那栏 CCSD(T) 的生产者），它的冻核约定守卫也得进——
  // 否则读者拿到一个没有任何东西钉住"反泊松两侧必须同一约定"这条不变式的脚本，
  // 而这条不变式一旦破了，水二聚体会安静地印出 -23.16 kcal/mol 而不是报错。
  'test_cc_convention.py'];
const EXAMPLES = ['__init__.py', 'quickstart.py', 'check_fast_pair.py', 'check_soft_partition.py'];
// CITATION.cff 也在根清单里：JOSS/SoftwareX 的审稿人按这份文件核署名与授权，
// 它不在包里就等于让读者去 git clone 才能拿到引用信息。
const ROOT = ['README.md', 'CONTRIBUTING.md', 'LICENSE', 'pyproject.toml', 'conftest.py', 'CITATION.cff'];
// 署名类文件**不参与脱敏**（逐字节写出）。脱敏表的目的是把机构标识从证据日志里抹掉，
// 但同一条规则扫到署名、单位或版权行上，改的就是作者身份：2026-09-30 实测到
// CITATION.cff 的一行注释里的机构主机名被换成 chem.<CLUSTER>.edu.cn —— 一份没人能访问的串。
// 这些文件里若真出现了该抹的东西，正确反应是**不出货、由人决定**，不是静默改写。
const NO_SCRUB = ['CITATION.cff', 'LICENSE', 'pyproject.toml'];
// CI 配置也属于"发布物"：只在工作区里有、公开仓里没有，等于闸门 E 之外的那道门禁
// 对读者不存在。
const WORKFLOW = { '.github/workflows/ci.yml': '.github/workflows/ci.yml' };
// 闸门代码本身也是发布物。`CONTRIBUTING.md` 与软件文都写着"跑 node tools/make_public_repo.js
// 复核这十五条闸门"，可 tools/ 整个不在包里 —— 那对读者就是一句空指令（和"引用指向 gitignore
// 里的 logs/"是同一类病：写的人能跑，别人不能）。所以把它和许可证扫描器一起放进去。
// audit_share_rule.js 是 2026-10-01 加进来的：闸门 W 直接 exec 它，而 make_public_repo.js
// 随包发布——一个发布出去的工具硬依赖一个不发布的兄弟文件，正是闸门 U 针对的那类缺陷，
// 只不过 U 只看 Python import，看不见 node 的 spawnSync 路径。公开仓的 CI 第一次变红
// 就是这个洞露出来的地方（详见 .github/workflows/ci.yml 里同日的注释）。
const TOOLS = ['make_public_repo.js', 'audit_no_gamess.js', 'audit_share_rule.js'];
// 放进去就带来一个真问题：这两个文件**本身就是检测模式的定义**，逐行扫必然命中自己。
// 处理是**具名豁免 + 把豁免量报出来**（见报告里的 note_detector_selfscan），
// 而不是悄悄 continue —— 一个把豁免藏起来的扫描器，和没有扫描器等价。
// 名单写死而不是 = TOOLS：第三个文件里没有判据定义，把它算进"检测器"就等于给它开豁免空白支票。
const SELF_DETECT = ['tools/make_public_repo.js', 'tools/audit_no_gamess.js'];
// 明确**不**带：centos_run*.sh, centos_setup.sh（集群 IP/绝对路径）, PROGRESS-*（两代理的协调
// 与撤回流水，不是证据）, HANDOFF-*, STEP0-*, paper/, scratch/, figs/。
// RESEARCH-* 与 MAIN-skeleton.md 改为改名进 docs/，见下面 RELOCATED —— 附录要靠它们落地。
const EXPLICITLY_EXCLUDED = ['nlcsplit/centos_run.sh', 'nlcsplit/centos_run2.sh', 'nlcsplit/centos_run3.sh',
  'nlcsplit/centos_run4.sh', 'nlcsplit/centos_run5.sh', 'nlcsplit/centos_setup.sh',
  // 点名机构标识的那十条判据 + 它们的毒样本。随闸门代码发布就等于随闸门发布这些串。
  'tools/intranet_patterns.private.js'];

// 证据目录。recompute/ 与 orca_control/ 是 2026-09-29 补的：paper/main.md 的 [S8][S9][S12][S18]
// 直接按文件名指它们，闸门 D 报"母仓里有、没随包发布"——引用落空。
const EVIDENCE_DIRS = ['l2cp', 'orca_run', 'centos', 'retrieval_calibration', 'recompute', 'scaling',
  'orca_control', 'population', 'agentb_sweep',
  // P2 引的三份：核/尾界测量、A2b 双实现对账、几何判据与近场探针的原始 stdout。
  // p2.md 一旦被引用闸门扫到，这些目录没进白名单就会"引用落空"。
  'coretail', 'fastpair_ab', 'bound_forms', 'release_qa',
  // 2026-09-30：跨程序裁判扩到 7 个体系（main.md 的 [S18] 现在按文件名指这些）；
  // 以及被引文里的 Crossref 重放记录（main.md §2.4、software.md 都点名它）。
  // 引用闸门 D 的逻辑是"稿件点了名却没随包发布 = 读者拿不到的出处"，所以这两条
  // 必须在正文引用落地的同一次提交里进白名单，不能等下一次导出再补。
  'orca_widen', 'bib_provenance',
  // 2026-10-01：归属裁判（partition-free 精确参照）。main.md §4 现在点名它，
  // 所以这个目录必须随包发布——否则闸门 D 判"读者拿不到的出处"。
  // 它带一层 outputs/，母循环只收顶层文件，嵌套层走下面的 NESTED_EVIDENCE。
  'attribution_referee',
  // 2026-10-01：Step M 的 CCSD(T) 阶梯。§4 那条"分不清是泛函还是我们算错"的开放项
  // 现在靠它变成实测比较，同一个目录里还有它自己的清单。
  'ccsdt'];

// 有些证据目录天然带一层子目录（裁判代码 + 它的机器可读输出）。白名单是逐目录
// 显式的，这里也显式列出要跟着发布的那一层，不做递归全盘扫描。
const NESTED_EVIDENCE = { attribution_referee: ['outputs'] };

// ================================================================ 脱敏（只发生在导出副本上）
// 三个表分开，因为它们的"数字不变性"论证强度不同：
//   PATH_TABLE     —— 工作机/仓库绝对路径串。
//   ENDPOINT_TABLE —— 集群 SSH 端口。它命中的 span 里带数字，所以单独声明、单独列账。
//   IDENT_TABLE    —— 机构名/集群账号名（审计要求闸门认得那家单位与那个账号）。
//                     它们不是路径，但同样是把"谁、在哪台机器、哪个单位"写在公开产物里。
//                     母仓原件照旧不动，只在导出副本上换成保留语义的中性标签：
//                     "cpu3 (<某 cluster>, …)" -> "cpu3 (<CLUSTER> cluster, …)"，机器名 cpu3 留着。
// 原件（evidence/**、nlcsplit/logs/**）一律不改：这里只改写到 dist/ 的副本。
//
// 2026-09-30 的拆分：上面这些串**本身就是机构标识**。闸门代码现在要随包发布，
// 把串写在这份文件里 = 把它们发布，所以点名本机/本集群的那几行搬进
// tools/intranet_patterns.private.js（不随包发）。这里只留"形状"类判据。
// 加载失败不是错误，但必须打印 —— 见 note_private_rules_loaded。
const PRIV_PATH = path.join(__dirname, 'intranet_patterns.private.js');
const PRIV = fs.existsSync(PRIV_PATH) ? require(PRIV_PATH) : null;
const PATH_TABLE = [].concat(PRIV ? PRIV.PATH : []);
const ENDPOINT_TABLE = PRIV ? PRIV.ENDPOINT : [];
const IDENT_TABLE = PRIV ? PRIV.IDENT : [];
const SCRUB_TABLES = [['path', PATH_TABLE], ['endpoint', ENDPOINT_TABLE], ['ident', IDENT_TABLE]];
// 一个被抹掉的 span 必须长成"内网串的样子"。这条是防我的正则贪吃：
// 一旦某个 span 里夹了 `=` 或不像路径/端点/标识，就说明它咬到了数据行，立刻失败。
// 形状分支里点名本机的那几条跟着判据一起住在 private 文件里（同上，为了公开副本不带串）。
const SPAN_SHAPE = new RegExp('^(\\/[^\\s]*|[a-z]:[\\\\/]\\S*'
  + (PRIV ? '|' + PRIV.SHAPES.join('|') : '') + ')$', 'i');
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
  if (NO_SCRUB.includes(f)) { copied.push(write(f, read(p))); continue; }
  put(f, read(p));
}
function read(p) { return fs.readFileSync(p, 'utf8'); }
for (const f of PKG) put('nlcsplit/' + f, read(path.join(SRC, 'nlcsplit', f)));
for (const f of STEPS) put('nlcsplit/' + f, read(path.join(SRC, 'nlcsplit', f)));
for (const f of TESTS) put('nlcsplit/tests/' + f, read(path.join(SRC, 'nlcsplit/tests', f)));
for (const f of EXAMPLES) put('nlcsplit/examples/' + f, read(path.join(SRC, 'nlcsplit/examples', f)));
put('nlcsplit/run_all.sh', read(path.join(SRC, 'nlcsplit', 'run_all.sh')));
// 闸门代码进包：见 TOOLS 上方注释。缺了它，"读者可自行复核这十五条闸门"是空指令。
// **逐字节原样写，不走 scrubText**：这份文件里就带着判据的字面量定义，一被脱敏就等于
// 把读者要跑的那把尺子的刻度磨掉，而且替换串落在正则字面量里会直接语法崩。
// 代价是它必然命中自己的判据 —— 那部分以 hits.exempt / exempt_ledger 具名记账并打印，
// 不是静默放过；点名机构的串则根本不在这份文件里（见 intranet_patterns.private.js）。
for (const f of TOOLS) copied.push(write('tools/' + f, read(path.join(SRC, 'tools', f))));

// ---------------------------------------------------------------- JOSS 稿随仓发布
// `paper/**` 整体不发布是对的（未发表稿），但 **JOSS 的投稿稿必须在仓库里**：JOSS 的
// 流程是从仓库构建 paper.md，编辑器要的是仓内路径。所以这一份是有意例外，别的稿不是。
// 图件是**字节拷贝**，不走 read()/utf8 —— PNG 当文本读会当场损坏；也不走 scrubText，
// 因为它是由随包发布的 nlcsplit/figures.py 从 nlcsplit/logs/*.json 生成的，
// 读者重跑就能得到同一张图（图里的每个数都来自已发布的侧车）。
const JOSS_TEXT = ['paper/joss/paper.md', 'paper/joss/paper.bib'];
const JOSS_BINARY = { 'figs/fig1_xc_split.png': 'paper/joss/fig1_xc_split.png' };
for (const rel of JOSS_TEXT) {
  const p = path.join(SRC, rel);
  if (!fs.existsSync(p)) { console.error('MISSING ' + rel); process.exit(2); }
  put(rel, read(p));
}
for (const [src, dst] of Object.entries(JOSS_BINARY)) {
  const p = path.join(SRC, src);
  if (!fs.existsSync(p)) { console.error(`MISSING 图件 ${src}（先跑 python3 -m nlcsplit.figures）`); process.exit(2); }
  copied.push(write(dst, fs.readFileSync(p)));   // Buffer，不过文本管线
}

// 几何获取脚本：把写死的本机代理改成"仅在环境里已有则沿用"，否则公开后别人照抄会连不上。
// 提成函数是为了让 selftest 能把它**跑两遍**验证不动点——2026-09-29 的读者模拟
// 发现重跑会把注释尾巴叠成两份，这类"对已发布副本再脱敏"的错只有跑两遍才看得见。
const PROXY_NEUTRAL = /export HTTPS_PROXY="\$\{HTTPS_PROXY:-\}"/;
function scrubGetScript(text) {
  let out = text.replace(/\b(?:127\.0\.0\.1|localhost):\d{2,5}\b/g, '<your-proxy>');
  if (!PROXY_NEUTRAL.test(out)) {
    out = out.replace(/^\s*(# )?export HTTPS_PROXY=\S+/m,
      'export HTTPS_PROXY="${HTTPS_PROXY:-}"   # 需要时自行 export，不需要则空值即直连');
  }
  return out;
}
let get = read(path.join(SRC, 'nlcsplit/tools/get_s22.sh'));
const before = get;
get = scrubGetScript(get);
if (/7890|127\.0\.0\.1/.test(get)) console.error('BUG: 抹敏之后仍残留本机代理串');
if (get === before && !PROXY_NEUTRAL.test(before)) console.error('WARN: get_s22.sh 的代理行没被改掉（格式变了？）');
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
// **从来没有命中过**，那条工作机挂载路径就这样一路进了发布树。现在几何出处统一交给
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
  // 嵌套层（裁判的 outputs/）作为带前缀的文件名并进同一份清单，这样下面的
  // MANIFEST 重写、哈希台账与"发布副本哈希对得上"那条判据对它一律成立。
  for (const sub of (NESTED_EVIDENCE[dir] || [])) {
    const subFrom = path.join(from, sub);
    if (!fs.existsSync(subFrom)) { scrubLog.push({ rel: `evidence/${dir}/${sub}`, FATAL: '母仓里没有这一层' }); continue; }
    fs.readdirSync(subFrom).filter(f => f !== 'MANIFEST.sha256')
      .filter(f => fs.statSync(path.join(subFrom, f)).isFile())
      .sort().forEach(f => names.push(`${sub}/${f}`));
  }
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
      dirHasSourceManifest: fs.existsSync(origManFile),
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

// ---------------------------------------------------------------- LICENSE：核验，不代填
// 以前这一步是"发布时把母仓的 [yyyy]/[name] 模板填空"，于是母仓 LICENSE 一直是未署名状态，
// 而 dist 副本却已经写着作者名——两边不一致，且署名不是从源文件来的（2026-09-29 自查发现）。
// 现在源文件署名，这里只做核验：占位符必须不在，署名行必须在。
{
  // LICENSE 由上面的 ROOT 循环原样拷贝，这里只核验母仓那一份已经署好名。
  const lic = read(path.join(SRC, 'LICENSE'));
  if (/Copyright \[yyyy\] \[name of copyright owner\]/.test(lic)) {
    scrubLog.push({ rel: 'LICENSE', FATAL: '母仓 LICENSE 仍是 Apache 模板占位符，先去源文件署名' });
  }
  if (!/^   Copyright 2026 Angran Xia$/m.test(lic)) {
    scrubLog.push({ rel: 'LICENSE', FATAL: '母仓 LICENSE 里没有预期的署名行（著作权人以源文件为准）' });
  }
}

// ---------------------------------------------------------------- 检索记录与主表随包发布
const RELOCATED = {
  'RESEARCH-20260929-lit.md': 'docs/literature_search_20260929.md',
  'MAIN-skeleton.md': 'docs/tables_and_provenance.md',
};
// 这两份在发布时是**改名**进 docs/ 的。于是"拿发布树再跑一遍本脚本"会在 read() 上直接崩：
// 发布树的根目录没有 RESEARCH-*.*，它已经叫 docs/….md 了。2026-09-30 的读者模拟实测到这个。
// 所以认两种形态：母仓形态读原名，发布树形态读已改名的目标（内容同一份，不动它）。
const relocatedPassthrough = [];
for (const [src, dst] of Object.entries(RELOCATED)) {
  if (fs.existsSync(path.join(SRC, src))) { put(dst, read(path.join(SRC, src))); continue; }
  if (fs.existsSync(path.join(SRC, dst))) {
    put(dst, read(path.join(SRC, dst)));
    relocatedPassthrough.push(`${src} -> ${dst}（本树已是发布形态，原样带走）`);
    continue;
  }
  console.error(`MISSING ${src}（也没有改名后的 ${dst}）`); process.exit(2);
}
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

// 哪些文件闸门**该打开**。这里原来是两份扩展名白名单（A 与 B 还不一致，B 多了 cfg|ini），
// 白名单的意思是"新文件格式默认不看"——2026-09-30 加 CITATION.cff 时正好撞上：
// 往里种了一条机构标识串，两条闸门都静悄悄过去了。改成默认全开、只排除已知二进制，
// 于是"没被检查"这件事必须靠显式声明才会发生。
const BINARY_EXT = /\.(pyc|pyo|whl|tar|gz|tgz|zip|bz2|xz|png|jpg|jpeg|gif|pdf|woff2?|ttf|eot|ico|so|dll|dylib|npy|npz|h5|onnx)$/i;
const isText = rel => !BINARY_EXT.test(rel);
// ---------------------------------------------------------------- 闸门 A：无 GAMESS **源码**
// 注意：/gamess/i 一律命中是**误报**——README/CONTRIBUTING/__init__ 里出现这个词，
// 正是因为我们在声明"本包不含 GAMESS 代码"。一个永远失败的门禁和一个不会失败的门禁一样没用。
// 所以这里只抓真正的 GAMESS 源码工件；"gamess"这个词的出现另列为 info，人工过一眼即可。
const gamessPats = [/\$gnum/i, /\bintgc\b/, /\bdiana\b/, /rhfuhf/, /\bgameSS\.src\b/i,
  /ps\/src\//, /GAMESS\.src/, /getscr|erscf[0-9]/];
// 逐行判一条GAMESS 判据命中，并决定它是"检测器自己的判据定义"还是"真工件"。
// 豁免条件写死成两件事同时成立：文件在 SELF_DETECT 名单里，**且这一行确实带着该判据的字面量**
// （行文本里含 re.source）。只按文件名豁免 = 给这两个文件开空白支票。
function classifyGamess(rel, line) {
  for (const [j, re] of gamessPats.entries()) {
    if (!re.test(line)) continue;
    return { pat: j, re, exempt: SELF_DETECT.includes(rel) && line.includes(re.source) };
  }
  return null;
}
function checkGamessSource(root, treeList) {
  const hits = [], words = [], exempt = [];
  for (const rel of treeList) {
    if (!isText(rel)) continue;
    let t; try { t = read(path.join(root, rel)); } catch (e) { continue; }
    // 逐行而非整文件：闸门 B 的教训——只报"这个文件命中过"就没法做具名豁免，
    // 因为豁免必须落在**具体那一行**上。
    t.split(/\r?\n/).forEach((line, i) => {
      const v = classifyGamess(rel, line);
      if (v) {
        const tag = v.exempt ? '<- 具名豁免「检测器自身的判据定义」' : '<- GAMESS 源码工件';
        (v.exempt ? exempt : hits)
          .push(`${rel}:${i + 1}  ${tag} 模式#${v.pat} ${v.re} | ${line.trim().slice(0, 110)}`);
      }
      if (/gamess/i.test(line)) words.push(`${rel}:${i + 1}  ${line.trim().slice(0, 120)}`);
    });
  }
  return { hits, words, exempt };
}
const gA = checkGamessSource(OUT, tree);
const ga = gA.hits, wordOnly = gA.words;

// ---------------------------------------------------------------- 闸门 B：无密钥/内网/工作机路径
// 2026-09-29 加固：旧表只有"密钥的形状"，不抓工作机绝对路径 / 账号 / 校内标识 / 集群端口。
// 审计实测 dist 里 13 个文件带串而闸门报"三个数组全空"，两个原因叠在一起：
//   (a) 判据表不全；
//   (b) 旧闸门遍历的是 `copied` 这份名单，不是目录树，名单外文件从未被打开过。
// 现在：默认失败、列出 file:line、扫的是 walkTree 出来的**全部**磁盘文件。
// 这里只留**不含机构标识的形状类**判据；点名本机/本集群的那十条住在
// tools/intranet_patterns.private.js（不随包发布），加载状态见 note_private_rules_loaded。
const secretPats = [
  ['私钥块', /BEGIN [A-Z ]*PRIVATE KEY/],
  ['口令赋值', /(?:password|passwd|token|api[_-]?key)\s*[:=]\s*["']?\S{4,}/i],
  ['ssh 目标', /\bssh\b[^#\n]*@/],
  ['user@裸IP', /\b\w+@\d{1,3}(\.\d{1,3}){3}/],
].concat(PRIV ? PRIV.SECRET_PATS : []);
// 第二道具名豁免：**作者本人的机构邮箱**。它按构造就同时含账号串与校内域名——
// 而这两条正是闸门 B 的判据。但公开通讯方式是论文与 CITATION.cff 的义务，不是泄漏；
// 该地址由本人 2026-09-30 亲自给出。豁免条件要三件事同时成立：
//   (1) 文件是署名类元数据（ATTRIBUTION_FILES）；
//   (2) 这一行里确实有 email 形态的地址；
//   (3) 把地址整串挖掉以后，那一行不再有别的判据命中。
// 第三条是边界：`/home/<账号>/… 备注 …@…cn` 这种混着机器路径的行不会被"顺带"放过。
const ATTRIBUTION_FILES = ['CITATION.cff', 'pyproject.toml', 'README.md', 'CONTRIBUTING.md', 'LICENSE'];
const EMAIL_PAT = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
function emailExemption(rel, line) {
  if (!ATTRIBUTION_FILES.includes(rel)) return null;
  const found = line.match(EMAIL_PAT);
  if (!found) return null;
  const rest = line.replace(EMAIL_PAT, ' ');
  if (secretPats.some(([, re]) => re.test(rest))) return null;
  return found.join(',');
}
function scanIntranet(root, treeList) {
  const hits = [];
  // hits.exempt：具名豁免的账。检测器自身的正则定义必然命中自己的模式串，
  // 这不是泄漏，但**必须记账并打印**——一个把豁免藏起来的扫描器和没有扫描器等价。
  hits.exempt = [];
  hits.emailExempt = [];
  for (const rel of treeList) {
    if (!isText(rel)) continue;
    let t; try { t = read(path.join(root, rel)); } catch (e) { continue; }
    t.split(/\r?\n/).forEach((line, i) => {
      const matched = secretPats.filter(([, re]) => re.test(line));
      if (!matched.length) return;
      // 一行只记一条账：机构邮箱同时踩中"账号串"与"校内标识串"是常态，
      // 刷两行会把一笔豁免读成两个问题。
      const names = matched.map(([n]) => n).join('、');
      const head = `${rel}:${i + 1}`;
      const tail = ` | ${line.trim().slice(0, 130)}`;
      const em = emailExemption(rel, line);
      // 「检测器自身的判据定义」这条豁免要求**每一条**命中的判据都真的以字面量出现在这一行里
      // （与闸门 A 的 classifyGamess 同一标准）。只按文件名豁免 = 给这两个文件开空白支票，
      // 而它刚刚被用在我的测试样例上：真账号串写在随包代码里，被文件名放过了。
      const isOwnDefinition = SELF_DETECT.includes(rel)
        && matched.every(([, re]) => line.includes(re.source));
      if (isOwnDefinition) hits.exempt.push(`${head}  <- 具名豁免「检测器自身的判据定义」 ${names}${tail}`);
      else if (em) hits.emailExempt.push(`${head}  <- 具名豁免「作者本人的机构邮箱」地址=${em}；放过的是 ${names}${tail}`);
      else hits.push(`${head}  <- ${names}${tail}`);
    });
  }
  return hits;
}
// 邮箱通道自己的反证：四种输入四种预期，每次运行都跑。种错了它就是装饰。
// 反证样本分两份。**公开那份只能测"文件门"这一半**（两条不含任何判据字面量的用例：
// 非署名文件不豁免、署名文件里没有地址也不豁免）。要测"同一行混着别的判据串时不许放过"，
// 那行就得真写着一条判据的样子 —— 把那种字面量放进随包代码，本身就是这条闸门该抓的东西
// （2026-09-30 实测：我先后用 ssh 行、私钥块样子写过用例，两次都被闸门自己抓住）。
// 所以那半边的用例住在 tools/intranet_patterns.private.js，只有母仓这次运行加载；
// 缺了哪一半由报告说：gateB_email_selftest.mixed_line_control=false 就是"这份副本没跑该控制"。
const EMAIL_CASES_PUBLIC = [
  ['nlcsplit/nlc.py', 'reviewer@demo.example', false],   // 非署名文件：不豁免
  ['CITATION.cff', '这行既没有地址也没有判据串', false],  // 无地址：不豁免
];
const emailSelftest = (() => {
  const mixed = PRIV && PRIV.EMAIL_CASES ? PRIV.EMAIL_CASES : [];
  const out = EMAIL_CASES_PUBLIC.concat(mixed).map(([rel, line, want]) => ({
    rel, want, got: !!emailExemption(rel, line),
  }));
  return { all_correct: out.every(c => c.want === c.got), ran: out.length,
    public_cases: EMAIL_CASES_PUBLIC.length,
    mixed_line_control: mixed.length > 0 && mixed.every(([r, l, w]) => !!emailExemption(r, l) === w),
    failures: out.filter(c => c.want !== c.got) };
})();
if (!emailSelftest.mixed_line_control) {
  console.error('注意：邮箱豁免通道的"混合行"反证没跑（判据样例随 private 文件一起不在本副本里）。'
    + '这条通道在本副本上只验过"文件门"两半。');
}
const gb = scanIntranet(OUT, tree);
// 豁免账的自证（老规矩：闸门必须证明自己不是恒真的）。
// 需要 gb.exempt>0 才能说明"这两个文件确实进了扫描、确实命中了、确实按名字放过的"。
// 若哪天 walkTree 或扩展名过滤把它们漏在外面，hits 和 exempt 会同时为 0 —— 那是空转，不是干净。
const selfScan = {
  in_tree: SELF_DETECT.filter(f => tree.includes(f)),
  intranet_exempt: gb.exempt.length,
  email_exempt: gb.emailExempt.length,
  gamess_exempt: gA.exempt.length,
  files_with_exempt: [...new Set(gb.exempt.concat(gA.exempt, gb.emailExempt).map(s => s.split(':')[0]))],
};
const selfScanOk = selfScan.in_tree.length === SELF_DETECT.length
  && selfScan.gamess_exempt > 0 && emailSelftest.all_correct;
// 专有判据的加载状态：母仓这次运行必须加载到，否则"十五条闸门"名不副实（闸门 B 只剩形状类）。
// 缺文件不是读者的错，所以不 block，但必须打印 —— 见下面 console.error 与报告字段。
const privateLoaded = PRIV ? PRIV.SECRET_PATS.length : 0;
// 在母仓里跑（认 PROGRESS-nlcsplit.md：它按设计不进发布树）却没加载到专有判据 = 闸门 B
// 被悄悄削掉一半，这种运行不许出货。读者在发布树里跑则只打印警告 —— 两边都不静默。
const IS_PRIVATE_REPO = fs.existsSync(path.join(SRC, 'PROGRESS-nlcsplit.md'));
if (!PRIV) {
  console.error('注意：tools/intranet_patterns.private.js 不在本副本里（它点名机构标识，不随包发布）。'
    + `闸门 B 此刻只有 ${secretPats.length} 条形状类判据，工作机路径/账号/内网 IP/集群端口这几类**没有被检查**。`);
}

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
  // 发布树那份清单是重算的，所以"目录里有文件"在发布侧总是闭合的；
  // **母仓**侧才是要守的地方：一个没进母仓 MANIFEST 的证据文件，意味着
  // 没有任何人担保过它的字节（实测：step_l 写出的 sweep_compare.json 就是这样混进来的）。
  if (h.origManifestHash === null && h.dirHasSourceManifest
    && !/^MANIFEST\.(sha256|txt)$/.test(h.rel.split('/').pop())) {
    origTouched.push(`${h.rel}: 母仓该目录有 MANIFEST.sha256，但这份文件没登记进去`);
  }
}
gc2.push(...origTouched);

// ---------------------------------------------------------------- 闸门 D：正文引用的每个出处都真的随包发布
const gateD = (() => {
  // paper/** 按设计不进公开仓，所以"拿发布树重跑本脚本"时这里没有正文可读。
  // 这不是读者的错，但也不能让闸门静默变成恒真：显式记一条 skipped 并打印。
  if (!fs.existsSync(path.join(SRC, 'paper/main.md'))) {
    console.error('注意：paper/main.md 不在本树（paper/** 按设计不发布）。'
      + '闸门 D『正文引用的出处都随包发布』这次**没有正文可扫**，不构成对读者的担保。');
    return { absent: [], pubInternal: [], skipped: 'no manuscript in this tree' };
  }
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
      // A token ending in `/` names a directory; `copied` lists files, so comparing them
      // literally can never match and the gate blocked a good build for a reason that was
      // false on its face ("存在但未随包发布 evidence/orca_widen/" — it is shipped).
      // The honest directory rule: at least one file under it must have been copied.
      if (rel.endsWith('/')) {
        if (!copied.some(c => c.startsWith(rel))) {
          absent.push(`${tag}: 该目录下没有任何随包发布的文件 ${rel}`);
        }
        continue;
      }
      if (!copied.includes(published)) absent.push(`${tag}: 存在但未随包发布 ${rel}`);
    }
  }
  return { absent, pubInternal };
})();

// ---------------------------------------------------------------- 闸门 Y：JOSS 稿里的相对链接必须真的随包
// JOSS 是从仓库里的路径构建 paper.md 的，一条断链在编辑那边就是渲染成空白方框——而图件
// 恰恰最容易指向"母仓有、发布树没有"的东西（figs/** 按设计不发布）。闸门 D 只认主篇附录
// 表格里 `反引号包住的路径`，看不见 markdown 的 []() 与 ![]()，所以这条单独立一个。
// 2026-10-01 加，同日把 paper/joss/ 放进发布清单的时候。
function jossBrokenLinks(text, baseDir, isCopied) {
  return [...text.matchAll(/!?\[[^\]]*\]\(\s*([^)\s]+)[^)]*\)/g)]
    .map(m => m[1].replace(/#.*$/, ''))
    .filter(u => !/^(?:https?:|mailto:|#)/i.test(u))
    .map(u => path.posix.normalize(path.posix.join(baseDir, u)))
    .filter(p => !isCopied(p));
}
const gateY = (() => {
  const rel = 'paper/joss/paper.md';
  if (!fs.existsSync(path.join(SRC, rel))) {
    return { broken: [], n: 'no joss paper in this tree', selftest: 'skipped with the manuscript' };
  }
  const set = new Set(copied);
  const text = read(path.join(SRC, rel));
  const broken = jossBrokenLinks(text, 'paper/joss', p => set.has(p))
    .map(p => `${rel}: 链接目标没随包发布 ${p}`);
  // 双向自检走的是**同一个** jossBrokenLinks：脏样例必须正好响在那条假路径上，
  // 干净样例（只有真图）必须静默。只验"会响"拦不住误伤，只验"不响"就是恒真。
  const only = (t) => jossBrokenLinks(t, 'paper/joss', p => p === 'paper/joss/fig1_xc_split.png');
  const dirty = only('![a](fig1_xc_split.png)\n![b](__no_such_figure__.png)\n');
  const clean = only('![a](fig1_xc_split.png)\n');
  const selftest = {
    fired: dirty.length === 1 && dirty[0] === 'paper/joss/__no_such_figure__.png',
    silent_on_valid: clean.length === 0,
  };
  return { broken, n: (text.match(/!?\[[^\]]*\]\(\s*(?:https?:|mailto:)/gi) || []).length, selftest };
})();

// ---------------------------------------------------------------- 闸门 E：用到的依赖都得声明
const STDLIB = new Set(['os', 'sys', 'json', 'time', 'math', 'ctypes', 'socket', 'traceback',
  'importlib', 'pathlib', 'argparse', 'functools', 'itertools', 'collections', 'warnings',
  'dataclasses', 'typing', 'subprocess', 'shutil', 'tempfile', 're', 'io', 'abc', 'datetime',
  // fastpair.py 一进口就被这条闸门拦住：`from __future__ import annotations` 是语言内建，
  // 不是任何发行包。缺它不是代码问题，是这张名单不完整——补上，并让它别再假报警。
  '__future__', 'textwrap', 'hashlib', 'glob', 'random', 'zipfile', 'tarfile',
  // 2026-10-01：证据脚本随包发布后，闸门 E 第一次扫到它们的 import。`multiprocessing`
  // 是发行版标准库，不是第三方发行包——缺它同样是这张名单不完整，不是谁的代码有问题。
  'multiprocessing', 'statistics', 'copy', 'string', 'unittest', 'logging', 'enum']);
const DECLARED = new Set([...read(path.join(SRC, 'pyproject.toml'))
  .matchAll(/"([A-Za-z][A-Za-z0-9_.\-]*)[<>=!~\[]?/g)].map(m => m[1].toLowerCase()));
const DIST_OF = { matplotlib: 'matplotlib', scipy: 'scipy', pyscf: 'pyscf', numpy: 'numpy', pytest: 'pytest' };
function undeclaredImports(pyTree, readAt) {
  const byDir = new Map();
  for (const rel of pyTree) {
    const dir = rel.includes('/') ? rel.slice(0, rel.lastIndexOf('/')) : '';
    if (!byDir.has(dir)) byDir.set(dir, new Set());
    const set = byDir.get(dir);
    if (rel.endsWith('.py')) {
      const base = rel.slice(rel.lastIndexOf('/') + 1).replace(/\.py$/, '');
      if (base !== '__init__') set.add(base);
    } else if (rel.includes('/') && !rel.endsWith('.py')) {
      const seg = rel.slice(rel.lastIndexOf('/') + 1);
      if (/^[A-Za-z_]\w*$/.test(seg)) set.add(seg);   // 同级的包目录
    }
  }
  const out = [];
  for (const rel of pyTree) {
    let src; try { src = readAt(rel); } catch (e) { continue; }
    const dir = rel.includes('/') ? rel.slice(0, rel.lastIndexOf('/')) : '';
    const locals = byDir.get(dir) || new Set();
    for (const m of src.matchAll(/^\s*(?:from|import)\s+([A-Za-z_][\w.]*)/gm)) {
      const top = m[1].split('.')[0];
      if (STDLIB.has(top) || top === 'nlcsplit' || locals.has(top)) continue;
      const dist = DIST_OF[top] || top.toLowerCase();
      if (!DECLARED.has(dist)) out.push(`${rel}: import ${m[1]}，但 pyproject 未声明 "${dist}"`);
    }
  }
  return [...new Set(out)];
}
const gateE = undeclaredImports(tree.filter(f => f.endsWith('.py')),
                                rel => read(path.join(OUT, rel)));
// 双向自检：兄弟模块必须放行（否则闸门把 `import referee_lib` 报成依赖，早晚被人整条
// 关掉），真第三方必须报警。只测单向的闸门等于没测。
const gateESelftest = (() => {
  const t = ['evidence/x/run.py', 'evidence/x/referee_lib.py', 'nlcsplit/nlc.py'];
  const rd = rel => rel.endsWith('run.py')
    ? 'import referee_lib\nimport multiprocessing\nimport nosuchdistribution\n'
    : 'import numpy\n';
  const got = undeclaredImports(t, rd);
  return { fired: got.length === 1 && /nosuchdistribution/.test(got[0]),
    sibling_and_stdlib_silent: !/referee_lib|multiprocessing/.test(got.join('|')),
    reported: got };
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
  // 毒样本本身点名机构标识，所以它跟判据一起住在 private 文件里；缺文件时这一项**显式跳过**，
  // 报告里写 "skipped_no_private_rules"，而不是给一个看起来通过的 green。
  const poison = Object.assign({}, PRIV ? PRIV.POISON : {}, {
    'clean_ok.txt': 'nothing to see, level=2, E_NLC=+125.7984',
  });
  for (const [n, c] of Object.entries(poison)) { fs.writeFileSync(path.join(NEG, 'tree', n), c + '\n'); rels.push(n); }
  fs.mkdirSync(path.join(NEG, 'tree', '__pycache__'), { recursive: true });
  fs.writeFileSync(path.join(NEG, 'tree', '__pycache__', 'x.cpython-310.pyc'), 'junk');
  const T = walkTree(path.join(NEG, 'tree'), '');
  R.residue = { fired: checkResidue(T).length > 0, clean: checkResidue(rels).length === 0 };
  const bHits = scanIntranet(path.join(NEG, 'tree'), rels);
  // 账本一行可能并着多条判据名（账号串、校内标识串…），按顿号展开再判覆盖。
  const names = new Set(bHits.flatMap(h => String(h.split('  <- ')[1] || '').split(' |')[0].split('、')));
  R.intranet = { fired: bHits.length, cleanTreeHits: scanIntranet(OUT, tree).length,
    covered: PRIV
      ? Object.fromEntries(PRIV.COVERED_NAMES.map(n => [n, names.has(n)]))
      : 'skipped_no_private_rules' };

  // 具名豁免通道自己也要有分辨力（它不依赖 private 文件，读者那份副本同样该测）：
  // 同一段文本，落在检测器文件的**判据定义行**上=豁免，落在别的文件里=违规，干净行=什么都不做。
  const probe = 'selftest_probe.txt';
  fs.writeFileSync(path.join(NEG, 'tree', probe), 'nothing\n');
  R.exempt_channel = (() => {
    const line = String(gamessPats[0]);                    // 真实的一条判据定义
    const inDetector = classifyGamess('tools/make_public_repo.js', line);
    const elsewhere = classifyGamess('nlcsplit/nlc.py', line);
    const innocent = classifyGamess('tools/make_public_repo.js', 'x = 1');
    return { detector_definition_exempt: inDetector, elsewhere_is_violation: elsewhere,
      innocent_clean: innocent, ok: !!inDetector && !!elsewhere && !innocent };
  })();

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

  // 真 LICENSE 字节：发布副本那份（填过）必须不响；母仓那份**不再**能当反证——
  // 2026-09-29 署名已经落进源文件，两边都干净。所以反证改成现造一份未填模板喂进去，
  // 否则这条 selftest 悄悄退化成了"两个 0 相等"。
  R.license = {
    cleanPublished: licenseViolations({ 'LICENSE(发布副本)': read(path.join(OUT, 'LICENSE')) }, 'Angran Xia'),
    firedOnUnfilledTemplate: licenseViolations({
      'LICENSE(现造的未填模板)': read(path.join(OUT, 'LICENSE'))
        .replace(/Copyright \d{4}/, 'Copyright [yyyy]')
        .replace(/(Angran Xia)/, '[name of copyright owner]'),
    }, 'Angran Xia'),
  };
  // 脱敏表本身：喂一条带数字的测量行，证明"只动路径行"这条断言拦得住越界改写。
  const sample = PRIV ? PRIV.SAMPLE : 'L1 == plain == \nL2 E_NLC= +125.7984 N=132176\n';
  const sres = scrubText(sample, 'SELFTEST');
  R.scrub = {
    changedLine: sres.split('\n')[0], untouchedLineIdentical: sres.split('\n')[1] === 'L2 E_NLC= +125.7984 N=132176',
    logged: scrubLog.filter(e => e.rel === 'SELFTEST').map(e => e.FATAL || `${e.proof} lines=${e.lines.join(',')}`),
  };
  // 不动点：对"已经脱敏过的输出"再脱敏一次，必须一个字节都不变。
  // 读者拿发布树重跑本脚本是合法操作，而这类二次应用的错只有跑两遍才看得见
  // （实测过一次：get_s22.sh 的替换注释被叠了两份）。
  const getSrc = read(path.join(SRC, 'nlcsplit/tools/get_s22.sh'));
  const g1 = scrubGetScript(getSrc), g2 = scrubGetScript(g1);
  const sideIn = 'path /home/abc/logs/x.json plus nlcsplit/ref/orca/out/h2o.out';
  R.scrubFixedPoint = { get_secondRunIdentical: g1 === g2,
    sidecar_secondRunIdentical: scrub(scrub(sideIn)) === scrub(sideIn) };
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


// ---------------------------------------------------------------- 闸门 W：文稿里的占比必须服从包内那条分母抵消规则
// 规则本体在 `nlcsplit/step_f_dispersion.py`：|dnlc/dxc| > 2 ⇒ 只报两个绝对项，不报占比。
// 2026-10-01 发现这条规则只在代码里执行，文字材料照旧写"甲烷 223%"——主篇结论段、
// software.md §4 与 README 各一处，而主篇 §3.2 自己已经论证过那个数不该报。
// 所以把它做成出货闸门。判据不靠本脚本重新推导，直接调 tools/audit_share_rule.js，
// 避免两处逻辑各自漂移；自检按本文件既有惯例双向做一遍（脏样例必须响、干净样例必须静默）。
const gateW = (() => {
  const { spawnSync: ss } = require('node:child_process');
  const os = require('node:os');
  const run = (file) => ss(process.execPath,
    [path.join(SRC, 'tools', 'audit_share_rule.js'), ...(file ? ['--files=' + file] : [])],
    { encoding: 'utf8', cwd: SRC });
  const probe = (name, body) => {
    const f = path.join(os.tmpdir(), `nlcsplit-gateW-${name}.md`);
    fs.writeFileSync(f, body);
    const r = run(f);
    try { fs.rmSync(f, { force: true }); } catch (e) { /* 临时目录归系统回收，留着无害 */ }
    return r;
  };
  const dirty = probe('dirty', '# t\n\n甲烷二聚体的非局域项占 ΔE_xc 的 240%。\n');
  const clean = probe('clean', '# t\n\n水二聚体的非局域项占 ΔE_xc 的 16%。\n');
  const selftest = { fired: dirty.status !== 0, silent_on_valid: clean.status === 0 };
  if (!selftest.fired || !selftest.silent_on_valid) {
    return { findings: ['闸门 W 的自检没响或误响 ⇒ 这条判据此刻不可信，不许出货'], selftest };
  }
  const real = run(null);
  return { findings: real.status === 0 ? [] : [(real.stdout || '') + (real.stderr || '')]
    .join('\n').split('\n').filter(l => /FAIL\(/.test(l)).map(l => 'audit_share_rule: ' + l.trim()),
    selftest, tail: (real.stdout || '').split('\n').slice(-4).join(' | ') };
})();

// ---------------------------------------------------------------- 闸门 U：包内引用也得真的发出去
// 闸门 E 问的是"这个 import 在 pyproject 里声明了吗"，于是它对**包内**兄弟模块完全沉默：
// `from nlcsplit import fastpair` 没有"声明"这一步可言。实测就是这样漏的——
// `fastpair.py` 不在 PKG 里，而随包的 step_j_scaling.py 第一行就 import 它，
// 读者装完 wheel 跑 P2 的脚本只会拿到 ImportError。
// 判据：随包 .py 里每一条对 nlcsplit 的引用（绝对 `from nlcsplit import X`、
// `import nlcsplit.X`、以及相对的 `from . import X`），其 X 必须真的在导出树里。
function importClosure(treeFiles, readFn) {
  const shipped = new Set(treeFiles
    .map(f => (f.match(/^nlcsplit\/([\w-]+)\.py$/) || [])[1])
    .filter(Boolean));
  const out = [];
  for (const rel of treeFiles.filter(f => f.endsWith('.py') && f.startsWith('nlcsplit/'))) {
    let src; try { src = readFn(rel); } catch (e) { continue; }
    // 只有**直接位于 nlcsplit/ 下**的文件里 `from . import X` 才指 nlcsplit.X；
    // tests/ 或 examples/ 里的相对引用指向它们自己的子包，不能按同一个口径判。
    const depth0 = rel === 'nlcsplit/' + rel.slice('nlcsplit/'.length).split('/')[0];
    const refs = [
      ...[...src.matchAll(/^\s*from\s+nlcsplit(?:\.([\w-]+))?\s+import\s+([^(\n]+?)\s*(?:#.*)?$/gm)]
        .map(m => m[1] ? [m[1]] : m[2].split(',').map(x => x.trim().split(/\s+as\s+/)[0]).filter(Boolean)),
      ...[...src.matchAll(/^\s*import\s+nlcsplit\.(\w+)/gm)].map(m => [m[1]]),
      ...(depth0 ? [...src.matchAll(/^\s*from\s+\.+\s+import\s+([^(\n]+?)\s*(?:#.*)?$/gm)]
        .map(m => m[1].split(',').map(x => x.trim().split(/\s+as\s+/)[0]).filter(x => x && x !== '*')) : []),
    ].flat().filter(r => r && r !== '__future__');
    for (const r of refs) if (!shipped.has(r)) out.push(`${rel}: 引用 nlcsplit.${r}，但它不在导出树里`);
  }
  return [...new Set(out)];
}

// 闸门 X：每一个随包发布的 step_*.py 必须出现在复现驱动 run_all.sh 的 CMD 表里。
// 这个缺陷发生过一次：旧 run_all.sh 只认四个脚本，而母仓有十三个，于是"每个表映射一个
// 脚本"这句话对拿发布物的读者不成立。修好之后**没有留下任何守卫**，所以第 14 个 step
// 脚本（step_m_ccsdt.py）一进来就重演了同一件事——本闸门就是那条当时没写的守卫。
function coverageOf(steps, runnerText) {
  // run_all.sh 的 CMD 表长这样：  [step_h]="nlcsplit/step_h_s22.py"
  const reg = new Set([...runnerText.matchAll(/\]="nlcsplit\/([^"]+\.py)"/g)].map(m => m[1]));
  return steps.filter(s => !reg.has(s.split("/").pop()));
}

const RUNNER_REL = 'nlcsplit/run_all.sh';
const gateXsteps = tree.filter(p => /^nlcsplit\/step[^/]*\.py$/.test(p));
const gateXRaw = fs.existsSync(path.join(OUT, RUNNER_REL))
  ? coverageOf(gateXsteps, read(path.join(OUT, RUNNER_REL)))
  : null;
const gateX = gateXRaw === null
  ? [RUNNER_REL + ' 不在导出树里，覆盖率无从核对']
  : gateXRaw.map(s => s + ' 不在 run_all.sh 的 CMD 表里：读者按发布物的一键入口跑不出它');
const gateXSelftest = (() => {
  if (gateXRaw === null) return { fired: false, clean_input_silent: false };
  const full = read(path.join(OUT, RUNNER_REL));
  // 反证一：把 CMD 表截成"当年那四个"，判据必须响。
  const four = full.replace(/(declare -A CMD=\(\n)([\s\S]*?)(\n\))/g, (m, a, body, c) => a
    + body.split("\n").filter(l => /\[step1\]|\[step2\]|\[step_b\]|\[step_c\]/.test(l)).join("\n") + c);
  const missingOnTruncated = coverageOf(gateXsteps, four);
  // 反证二：喂一份"按构造补全"的表，判据必须闭嘴。补的是合成行，
  // 所以这一半与真实缺陷是否已修无关——否则闸门没修好时自检永远红，
  // 就分不清"守卫坏了"和"还有活没干"。
  const completed = full + '\n' + gateXsteps.map((s, i) => '  [x_' + i + ']="' + s + '"').join('\n');
  const missingOnComplete = coverageOf(gateXsteps, completed);
  return {
    step_scripts: gateXsteps.length,
    fired: missingOnTruncated.length > 0,
    truncated_reports: missingOnTruncated.length,
    clean_input_silent: missingOnComplete.length === 0,
    real_tree_missing: gateXRaw.length,
  };
})();
const gateU = importClosure(tree, rel => read(path.join(OUT, rel)));

// ---------------------------------------------------------------- 闸门 V：源码树里"装了但不该发"的模块
// 2026-09-30 由发布卫生扫描实测出来：`pip install .`（软件文 §5 与 QA 日志都这么写）走的是
// setuptools 对整个包目录的收录，**不看**这里的 PKG/TESTS/EXAMPLES 白名单。于是在母仓里
// `pip install --target` 装出 45 个文件，其中 `nlcsplit/fastpair_ide.py`（同行那份独立实现）、
// 它的测试与四份内部分析脚本都进了 site-packages —— 而 wheel 里没有它们。
// "装源码 = 装发布物"这个前提一直是假的。闸门 F 只看 wheel 成员，看不见这条。
// 现在：包目录里白名单之外的每个 .py 都必须在这里**具名**并给理由，否则不出货。
// 理由不是形式：这些文件的存在本身就是要向读者解释的事实。
const INTERNAL_ONLY_MODULES = {
  'nlcsplit/fastpair_ide.py': '同行(ide-qoder)的独立实现，冻结对照，故意不发布',
  'nlcsplit/tests/test_fastpair_ide.py': '上面那份实现的测试，随它一起不发布',
  'nlcsplit/examples/check_screen_bound_ide.py': '它的验算脚本（import fastpair_ide）',
  'nlcsplit/examples/coretail_bound.py': '核/尾界判死测量，产出归档在 evidence/coretail/',
  'nlcsplit/examples/hybrid_nearfield.py': '近场占比测量，产出归档在 evidence/bound_forms/',
  'nlcsplit/examples/probe_bound_forms.py': '球界/盒界单调性探针，产出归档在 evidence/bound_forms/',
};
const WL_SET = new Set([].concat(PKG, STEPS).map(f => 'nlcsplit/' + f)
  .concat(TESTS.map(f => 'nlcsplit/tests/' + f))
  .concat(EXAMPLES.map(f => 'nlcsplit/examples/' + f)));
// 判据拆成两个纯函数，是为了能拿合成输入自证非恒真（这个仓库的老规矩：闸门要响给自己看）。
const strayModules = found => found.filter(rel => !WL_SET.has(rel) && !INTERNAL_ONLY_MODULES[rel]);
const missingWhitelist = found => [...WL_SET].filter(rel => !found.includes(rel));
function listPackagedPy(root) {
  const out = [];
  for (const dir of ['nlcsplit', 'nlcsplit/tests', 'nlcsplit/examples']) {
    const d = path.join(root, dir);
    if (!fs.existsSync(d)) continue;
    for (const e of fs.readdirSync(d, { withFileTypes: true }))
      if (e.isFile() && e.name.endsWith('.py')) out.push(dir + '/' + e.name);
  }
  return out;
}
const foundSrc = listPackagedPy(SRC);
const gateV = missingWhitelist(foundSrc).map(rel => `白名单里的 ${rel} 在源码树里不存在`)
  .concat(strayModules(foundSrc).map(rel =>
    `${rel}：pip install . 会把它装进 site-packages，wheel 里没有它，`
    + '而且它没在 INTERNAL_ONLY_MODULES 里具名给不发布的理由'));
// 自证非恒真：幽灵模块必须响；已具名的那条不许响；干净输入必须一个都不报。
const gateVSelftest = (() => {
  const ghost = strayModules(['nlcsplit/nlc.py', 'nlcsplit/ghost_module.py']);
  const named = strayModules(['nlcsplit/fastpair_ide.py']);
  const clean = missingWhitelist(foundSrc).length + strayModules(foundSrc).length;
  return { fired: ghost.length === 1 && /ghost_module/.test(ghost[0]),
    silent_on_named: named.length === 0, clean_input_silent: clean === 0, reported: ghost };
})();
// 自证非恒真：喂一份假树与一条假引用，必须**只**报那一条；
// 同时假树里合法的那条（nlc）不许被报——否则这闸门可能只是在乱响。
const gateUSelftest = (() => {
  const fakeTree = ['nlcsplit/__init__.py', 'nlcsplit/nlc.py', 'nlcsplit/step_z.py'];
  const fakeRead = rel => rel.endsWith('step_z.py')
    ? 'from nlcsplit import nlc, notshipped\nfrom . import nlc\n' : 'pass\n';
  const got = importClosure(fakeTree, fakeRead);
  return { fired: got.length === 1 && /notshipped/.test(got[0]),
    silent_on_valid: !got.some(x => /nlc\b/.test(x)), reported: got };
})();

const report = {
  out: OUT, files: copied.length, treeFiles: tree.length, artifacts,
  ledger: LEDGER_OUTSIDE.replace(/\\/g, '/'),
  gateA_gamess_source_artifacts: ga,
  gateB_intranet: gb,
  gateB_exempt_ledger: gb.exempt,
  gateB_email_exempt_ledger: gb.emailExempt,
  gateB_email_selftest: emailSelftest,
  gateA_exempt_ledger: gA.exempt,
  note_detector_selfscan: selfScan,
  note_private_rules_loaded: privateLoaded,
  gateC_evidence_hashes_vs_published: gc,
  gateC2_scrub_digit_invariance: gc2,
  gateD_cited_but_unshipped: gateD.absent,
  gateE_undeclared_imports: gateE,
  gateE_selftest: gateESelftest,
  gateF_wheel_sdist_members: gateF,
  gateG_license: gateG,
  gateR_tree_residue: gr,
  gateT_not_in_export_manifest: notInManifest,
  gateU_import_closure: gateU,
  gateX_runner_coverage: gateX,
  gateX_selftest: gateXSelftest,
  gateU_selftest: gateUSelftest,
  gateV_install_vs_release: gateV,
 gateW_share_rule_in_docs: gateW.findings, note_gateW_selftest: gateW.selftest,
  gateY_joss_links: gateY.broken, gateY_selftest: gateY.selftest,
  gateV_selftest: gateVSelftest,
  note_internal_only_modules: INTERNAL_ONLY_MODULES,
  note_word_only_gamess: wordOnly,
  note_internal_only_citations: gateD.pubInternal,
  note_gateD_skipped: gateD.skipped || null,
  note_evidence_dirs_without_source_manifest: missingSourceManifest,
  scrubbed_files: scrubLog.filter(e => !e.FATAL).map(e => e.rel),
  excluded_by_design: EXPLICITLY_EXCLUDED.concat(['PROGRESS-*.md', 'HANDOFF-*.md',
    'STEP0-*.md', 'scratch/**',
    'paper/**（唯一例外 joss/：JOSS 投稿稿必须在仓库里，JOSS 从仓内路径构建）',
    'figs/**（唯一例外 fig1_xc_split.png：字节拷贝进 paper/joss/，可由随包的 nlcsplit/figures.py 重生成）']),
  relocated_into_docs: RELOCATED,
  note_relocated_passthrough: relocatedPassthrough,
};

const bad = ga.length + gb.length + gc.length + gc2.length + gateD.absent.length + gateE.length
  + gateF.length + gateG.length + gr.length + notInManifest.length + gateU.length + gateV.length
  // 闸门 U 的自检没响 = 这条判据此刻是恒真的，等于没有 —— 不许出货。
  + (gateUSelftest.fired && gateUSelftest.silent_on_valid ? 0 : 1)
  // 闸门 E 的自检双向都要过：真第三方必须报警，兄弟模块与标准库必须放行。
  // 只验"会响"的自检会让误伤回来时没人拦住（本日就是误伤先撞上的）。
  + (gateESelftest.fired && gateESelftest.sibling_and_stdlib_silent ? 0 : 1)
  + gateW.findings.length + (gateW.selftest.fired && gateW.selftest.silent_on_valid ? 0 : 1)
  + gateX.length + (gateXSelftest.fired && gateXSelftest.clean_input_silent ? 0 : 1)
  + gateY.broken.length
  // joss 稿缺失时上面已经 exit(2)，这里的字符串分支只在"发布副本里没有稿"这种
  // 设计上不该出现的状态下走到 —— 那时它算失败，不算通过。
  + (typeof gateY.selftest === 'string' ? 1
     : (gateY.selftest.fired && gateY.selftest.silent_on_valid ? 0 : 1))
  + (gateVSelftest.fired && gateVSelftest.silent_on_named && gateVSelftest.clean_input_silent ? 0 : 1)
  // 同理：具名豁免如果一笔都没记上，说明检测器根本没扫到自己 —— 那"豁免规则"是装饰。
  + (selfScanOk ? 0 : 1)
  // 在母仓跑却没加载到专有判据 = 闸门 B 被削掉一半还宣称跑了十五条。
  + (IS_PRIVATE_REPO && !PRIV ? 1 : 0);
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
