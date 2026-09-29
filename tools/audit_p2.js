// P2 的措辞闸门。计划书 v2 给 P2 定的门禁是：
//   "主张只允许是：界的实测松紧、可跳占比、墙钟代价，以及为什么亚平方在这类弱耦合
//    二聚体上不成立；不得残留'加速 k 倍'。"
// 这句话以前靠人读，而"慢 5.2 倍"那个标题就是人读漏过一次才被抓到的（它是在 12 个
// 代理抢 CPU 的窗口里测的）。本脚本把两件事变成机器判据：
//   1) 每个反引号里的路径必须**被 git 跟踪**（"文件存在"不算——见 md2tex.js 同一条教训）；
//   2) 每个含加速/亚平方词的句子必须自带否定词，否则报警。判据不是"这个词不许出现"，
//      而是"许它出现在被否定的句子里"，因为 P2 通篇就在说"没有加速"。
// 用法：node tools/audit_p2.js [paper/p2.md]      审计
//      node tools/audit_p2.js --selftest           用假输入证明它会响（每次改判据后必跑）
const fs = require('node:fs');
const cp = require('node:child_process');

const SELFTEST = process.argv.includes('--selftest');
const TARGET = process.argv.slice(2).find(a => !a.startsWith('--')) || 'paper/p2.md';

const TRACKED = new Set((cp.spawnSync('git', ['ls-files'], { encoding: 'utf8' }).stdout || '')
  .split('\n').filter(Boolean));

const byBase = new Map();
for (const p of TRACKED) {
  const b = p.split('/').pop();
  if (!byBase.has(b)) byBase.set(b, []);
  byBase.get(b).push(p);
}
const dirsWith = pre => [...TRACKED].some(p => p.startsWith(pre));

// 引用解析：带目录分隔符的按整条路径查；**裸文件名按 basename 查**。
// 软件文里 `figures.py`、`partition.py` 是行文用的模块名（真身在 nlcsplit/ 下），
// 整条路径查会把它们全判成"文件不存在"，然后这个闸门就变成噪音、被无视。
// 而 `RESEARCH-xxx.md` 这种"全仓根本没有"的名字必须仍然会响。
function resolve(t) {
  if (t.endsWith('/')) return dirsWith(t) ? [{ path: t, ok: true, dir: true }] : [];
  if (t.includes('/')) return TRACKED.has(t) ? [{ path: t, ok: true }] : [];
  const hits = byBase.get(t) || [];
  return hits.length ? hits.map(h => ({ path: h, ok: true })) : [];
}

// 与 md2tex.js 保持同一套"看着像路径"的判据，别在这儿另起炉灶：
// `x.md:700-707` 与 `evidence/**` 都不是路径，误报的闸门会被无视，比没有更糟。
// 第一版把三种东西误判成了路径：API 名 `nlc.pair_energy`、式子 `(4π/3)ρ`、
// pytest 节点 id 的后缀 `…::test_x`。所以加一条字符集闸门 + 扩展名白名单：
// 认"有目录分隔符，或带已知扩展名"的 ASCII 令牌，其余一律不看。
const stripLines = x => x.replace(/:\d+(?:[,-]{1,2}\d+)*$/, '');
const stripNodeId = x => x.replace(/::[\w.[\]-]+$/, '');
const globish = x => /[*?\s]/.test(x);
const EXT = /\.(md|json|out|py|txt|bib|js|png|tex|csv|sh|ya?ml)$/;
const asciiPathish = x => /^[A-Za-z0-9_./-]+$/.test(x);
const looksLikePath = x => x.includes('/') || EXT.test(x);
const pathToken = x => !globish(x) && asciiPathish(stripNodeId(stripLines(x)))
  && looksLikePath(stripNodeId(stripLines(x))) && !stripNodeId(stripLines(x)).startsWith('/');

// 节点 id 单独一类：`file.py::test_name` 里文件在、测试名被改过，是"引用落空"的
// 一种隐蔽形态（今天 fastpair 从 697 行删到 394 行，正是最容易发生这件事的时刻）。
function nodeIdToken(x) {
  const m = x.match(/^(.+\.py)::([\w.[\]-]+)$/);
  if (!m || globish(m[1]) || !asciiPathish(m[1])) return null;
  return { file: m[1], name: m[2] };
}

const SPEED = /\b(faster|speed-?up|speeds? up|accelerat\w*|sub-?quadratic|sublinear|linear.scaling|times? cheaper|cheaper by|scales? (?:as|like)\s*O\(|[Oo]\s*\(\s*N\b|real-?time saving|wall-?clock win)\b/i;
const SPEED_X = /(\d+(?:\.\d+)?|k|x)\s*[\u00d7x]\s*(faster|cheaper|speedup)/i;
const NEGATE = /\b(not|never|no\b|none|nothing|no clean|cannot|can't|fail\w*|refus\w*|reject\w*|void\w*|slower|without|did not|doesn'?t|does not|lost|losing|unproven|we make no|not claim\w*|0 of\b|prunes nothing|0\.0%)\b/i;

function audit(text) {
  const lines = text.split(/\r?\n/);
  const fails = [];

  // 引用扫描必须按**整篇**取反引号跨度，不能按行取：正文排版会把一个路径折成两行
  // （`evidence/coretail/\n2026...out`）。按行扫的时候这个令牌谁也不认识，闸门就
  // 安静地放过了一个根本不存在的路径——这正是"闸门不打开产物目录"那一类失效。
  const spans = [];
  const re = /`([^`]+)`/g;
  let m;
  while ((m = re.exec(text))) {
    spans.push({ raw: m[1], line: text.slice(0, m.index).split(/\r?\n/).length });
  }
  for (const { raw, line } of spans) {
    const flat = raw.replace(/\r?\n\s*/g, '');
    const one = stripNodeId(stripLines(flat));
    if (!pathToken(flat)) continue;
    if (!resolve(one).length) {
      fails.push({ kind: 'path', line, token: one,
        detail: (fs.existsSync(one) ? 'exists but NOT tracked by git' : 'no such file')
          + (raw !== flat ? ' (citation is wrapped across lines)' : '') });
    }
    const node = nodeIdToken(stripLines(flat));
    if (node && TRACKED.has(node.file)) {
      const src = fs.readFileSync(node.file, 'utf8');
      const fn = node.name.split('.').pop();
      if (!new RegExp('def\\s+' + fn.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\s*\\(').test(src)) {
        fails.push({ kind: 'test-id', line, token: flat,
          detail: `file is tracked but defines no function ${fn}()` });
      }
    }
  }

  // 加速措辞在**剥掉引号内容**的副本上逐行判：引号里是别人的题名或行话
  // （"Nonlocal … made faster"），不是我们的主张。剥离必须整篇做——上一版按行剥，
  // 遇到跨行书写的题名就剥不掉，真引用被当成主张报警。
  // 代价是奇数个引号时正则一路吞到下一段，判据会**看瞎**，所以显式检查配对：
  // 不配对就报一条 gate-blind，让失明可被发现，而不是静默放过。
  const qcount = (text.match(/"/g) || []).length;
  if (qcount % 2) {
    fails.push({ kind: 'gate-blind', line: 1, token: 'unbalanced quotes (' + qcount + ')',
      detail: 'quoted-title stripping is unreliable; the wording check on this file is VOID' });
  }
  const stripped = text.replace(/"[^"]*"/g, mm => mm.replace(/[^\n]/g, '')).split(/\r?\n/);
  stripped.forEach((ln, i) => {
    const hasSpeed = SPEED.test(ln) || SPEED_X.test(ln);
    if (!hasSpeed) return;
    if (NEGATE.test(ln)) return;
    fails.push({ kind: 'wording', line: i + 1, token: lines[i].trim().slice(0, 120),
      detail: 'acceleration/scaling wording with no negation in the same line' });
  });

  return fails;
}

if (SELFTEST) {
  // 假输入必须让三类判据都响；否则这个闸门是恒真的，和它不在没什么区别。
  // 反向同样要测：三种"看着像路径"的合法令牌不许误报（第一版就在这三处报过假警）。
  const probe = [
    'we are 3.5\u00d7 faster than the dense kernel on every system.',
    'the tool shows sublinear behaviour for large chains.',
    'see `nlcsplit/definitely_not_a_real_file.py` for the bound.',
    'see `paper/main.md:700-707` for the table.',
    'see `nlcsplit/tests/test_fastpair.py::test_no_such_function_here`.',
    'and for benzene 276/276 [`evidence/bound_forms/',
    'not_a_real_file.out`].',
    'the screened path is 1.08-10.28\u00d7 slower; it never won.',
    '`w0` contains `(4π/3)ρ` and the half-block convention of `nlc.pair_energy`.',
    'closest work is Laikov 2025, "Nonlocal van der Waals density functional made faster".',
    'our scheme is 4\u00d7 faster on the far field.',
    'the "Linear Scaling Hierarchical Integration Scheme for the',
    'Exchange-Correlation Term" of Burow & Sierka octrees the grid.',
  ].join('\n');
  const f = audit(probe);
  const kinds = f.map(x => x.kind);
  const want = ['wording', 'path', 'test-id'];
  const wrapped = f.filter(x => x.detail && x.detail.includes('across lines'));
  // 第二个探针：引号不配对时，剥引号会把判据看瞎——必须自己喊出来。
  const blind = audit('the "title stays open to the next paragraph\nour scheme is 10\u00d7 faster.');
  const ok = want.every(w => kinds.includes(w))
    && wrapped.length === 1 && wrapped[0].token === 'evidence/bound_forms/not_a_real_file.out'
    && !f.some(x => x.line === 4)      // 带行号的引用不许误报
    && !f.some(x => x.line === 8)      // 已否定的加速措辞不许误报
    && !f.some(x => x.line === 9)      // 式子与 API 名不是路径
    && !f.some(x => x.line === 10)     // 别人的题名在引号里，不是我们的主张
    && !f.some(x => x.line === 12 || x.line === 13)   // 跨行书写的题名同样豁免
    && f.some(x => x.line === 11 && x.kind === 'wording')   // 剥掉引号后判据仍然有效
    && blind.some(x => x.kind === 'gate-blind');   // 引号不配对必须自报失明（宁可多报也不静默）
  console.log('selftest findings:', JSON.stringify(f.map(x => `L${x.line} ${x.kind}: ${x.token}`), null, 1));
  console.log('blind probe:', JSON.stringify(blind.map(x => `${x.kind} @L${x.line}`)));
  console.log(ok ? 'SELFTEST OK: 三类判据都会响，引号不配对时闸门自报失明，五种合法写法都不响'
                 : 'SELFTEST FAIL: gate is not discriminating');
  process.exit(ok ? 0 : 1);
}

const text = fs.readFileSync(TARGET, 'utf8');
const fails = audit(text);
const words = (text.match(/\b\w+/g) || []).length;
console.log(`== P2 措辞/出处闸门  ${TARGET}  (${words} words, ${text.split(/\r?\n/).length} lines) ==`);
for (const f of fails) {
  console.log(`FAIL  L${f.line}  [${f.kind}]  ${f.token}\n        ${f.detail}`);
}
if (!fails.length) {
  console.log('PASS  0 findings: 每个反引号路径都被 git 跟踪；每条含加速/标度词的行都自带否定。');
  console.log('NOTE  本闸门只保证"没有残留的加速主张"这一条形式判据；主张本身是否');
  console.log('      与实测一致，仍要对着 evidence/ 里的工件读，脚本管不了。');
}
process.exit(fails.length ? 1 : 0);
