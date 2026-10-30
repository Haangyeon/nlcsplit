/* 发布前硬检查：README、LICENSE 段与软件文都写着"不含任何 GAMESS 代码"。
 * 这是法律性声明，不能靠"我记得没抄"，所以它必须是一条**别人也能跑**的检查：
 *   - 这个文件本身随包发布（见 make_public_repo.js 的 TOOLS 清单）；
 *   - 它不依赖任何代理、账号或工作机路径，只需要 python3 + pip。
 *
 * 做法：
 *   (1) 真装一遍到独立目录（读源码树没用——build/lib 里的陈旧副本会漏检，真发生过）；
 *   (2) 对装出来的**每一个文件**逐行扫 GAMESS 标识、GAMESS 专有量名与源码文件名；
 *   (3) 顺带扫许可冲突信号（GPL/AGPL/NASA 头、不明来源的大段 C 移植注释）；
 *   (4) 有命中就 exit 1 —— 让 CI 能直接gate 住，而不是"打印一堆数字等人看"。
 *
 * 用法：
 *   node tools/audit_no_gamess.js                       # 装当前目录到 /tmp/nlcsplit_audit 再扫
 *   node tools/audit_no_gamess.js --target DIR --src PATH
 *   node tools/audit_no_gamess.js --selftest            # 只验判据本身有没有分辨力，不安装
 */
const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const argv = process.argv.slice(2);
const opt = (name, dflt) => {
  const i = argv.indexOf('--' + name);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : dflt;
};
const T = opt('target', '/tmp/nlcsplit_audit');
const SRC = path.resolve(opt('src', '.'));
const NO_INSTALL = argv.includes('--no-install');
// ---- 判据定义放在最前：--selftest 不该依赖一次真安装 ----
// NEEDLE 是"GAMESS 才有的东西"：程序名、专有量名、源码文件名。
// 命中不等于有罪（免责声明里就会出现 "GAMESS" 这个词），但也不能靠"我看了一眼觉得没事"。
// 所以：合法的出现必须是**具名的**——一条 (文件名 × 行文) 规则，逐条记账并打印。
// 规则外的命中一律算违规并 exit 1；规则内一笔都没记上则单独报"白名单可能过期"。
const NEEDLE = /gamess|ab initio|libddis\.|inputst|outputst|dfl\.h|gfile|intcos/i;
const LIC = /\bgpl\b|agpl|gnu general public|nasa open/i;

// 唯一的合法形态：我们在声明"本包不含 GAMESS 代码"。这句话出现在包 docstring，
// 以及 README 的长描述被打包进 dist-info/METADATA 之后的那份副本里。
// 注意 file 与 line **两个都要**匹配才豁免：只按文件名豁免，等于给
// nlcsplit/__init__.py 开了一张空白支票——以后它抄进真代码也照样"合法"。
const ALLOW = [
  { name: '免责声明：本包不含 GAMESS 代码',
    file: /^(?:nlcsplit\/__init__\.py$|.*dist-info\/METADATA$)/,
    line: /不含任何 ?GAMESS ?代码|no ?GAMESS code/i },
  // pip 给"从本地路径装"这件事自己写的来源记录。那一行是**调用者的磁盘路径**，
  // 不是包内容——PyPI 用户拿到的是 wheel 里的 RECORD，没有这个文件。
  // 2026-09-30 实测：从母仓源码树装时它带出本机仓库路径，被本检查判为违规。
  // after 谓词是这条规则的边界：把 URL 值本身挖掉以后，那一行**只该剩下 pip 的骨架**。
  // 少了这一句，"url 里恰好写着 GAMESS"就会连带把同一行里别的 GAMESS 内容一起放过。
  { name: 'pip 自记的本地安装来源（direct_url.json）',
    file: /^[^/]*dist-info\/direct_url\.json$/,
    line: /"url"\s*:\s*"file:\/\/[^"]*"/,
    after: l => !NEEDLE.test(l.replace(/"file:\/\/[^"]*"/, '""')) },
];

function classify(rel, line) {
  for (const a of ALLOW) {
    if (a.file.test(rel) && a.line.test(line) && (!a.after || a.after(line))) return a.name;
  }
  return null;
}

if (NO_INSTALL) {
  console.error('--no-install 已废弃：读源码树/已有目录会漏检（build/lib 的陈旧副本真骗过一次）。');
  console.error('本检查只做"真装一遍再扫"。要看判据本身有没有分辨力，用 --selftest。');
  process.exit(2);
}
if (argv.includes('--selftest')) {
  // 反证：豁免规则必须有分辨力。五种输入，五种预期，任何一条不符就非零退出。
  const cases = [
    // 真 GAMESS 工件：必须判违规
    { rel: 'nlcsplit/nlc.py', line: 'c  ported from GAMESS src/lib/libddis.F', want: null },
    { rel: 'nlcsplit/io.py', line: '  read INPUTST from the gfile', want: null },
    // 免责声明：必须被具名豁免
    { rel: 'nlcsplit/__init__.py', line: '不含任何 GAMESS 代码；依赖 PySCF。', want: '免责声明：本包不含 GAMESS 代码' },
    { rel: 'x-0.1.0.dist-info/METADATA', line: '**不含任何 GAMESS 代码**', want: '免责声明：本包不含 GAMESS 代码' },
    // 同文件、非免责的那句话：不得跟着文件名一起放过（这条是白名单的边界）
    { rel: 'nlcsplit/__init__.py', line: 'helper parses GAMESS $VM1 / INTGC blocks', want: null },
    // pip 的来源记录：URL 里带本机路径要放过……
    { rel: 'x-0.1.0.dist-info/direct_url.json',
      line: '{"dir_info": {}, "url": "file:///some/machine/Project/GAMESS"}',
      want: 'pip 自记的本地安装来源（direct_url.json）' },
    // ……但同一个文件里塞进真内容就不算了（after 谓词的边界）
    { rel: 'x-0.1.0.dist-info/direct_url.json',
      line: '{"dir_info": {}, "url": "file:///tmp/x", "note": "reads GAMESS INPUTST"}',
      want: null },
  ];
  let bad = 0;
  for (const c of cases) {
    const got = classify(c.rel, c.line);
    const ok = got === c.want;
    if (!ok) bad++;
    console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${c.rel} | ${c.line.slice(0, 40)} -> ${JSON.stringify(got)} (want ${JSON.stringify(c.want)})`);
  }
  console.log(`selftest: ${cases.length - bad}/${cases.length} 通过`);
  process.exit(bad ? 1 : 0);
}

try { fs.rmSync(T, { recursive: true, force: true }); } catch (e) { /* 首跑没有该目录 */ }
// 这里曾经硬塞过工作机的回环代理端点作为默认值。那是把"我这台机器能连网"
// 写进一条要求别人执行的检查里：别人跑要么连错代理要么连不上。网络配置属于调用者的环境。
execFileSync('python3', ['-m', 'pip', 'install', '-q', '--no-deps', '--target', T, SRC],
  { stdio: ['ignore', 'inherit', 'inherit'] });

const PKG = path.join(T, 'nlcsplit');
if (!fs.existsSync(PKG)) { console.error('装出来的包不存在：' + PKG); process.exit(2); }

const files = [];
(function walk(d) {
  for (const e of fs.readdirSync(d, { withFileTypes: true })) {
    if (e.isDirectory()) { if (e.name !== '__pycache__') walk(path.join(d, e.name)); }
    else files.push(path.join(d, e.name));
  }
})(T);

const hits = [], licHits = [], exempt = [], used = new Set();
for (const f of files) {
  let txt; try { txt = fs.readFileSync(f, 'utf8'); } catch (e) { continue; }
  if (txt.indexOf('\0') >= 0) continue;            // 二进制（.pyc 之类）不做文本扫，但会被计数
  txt.split(/\r?\n/).forEach((ln, i) => {
    const rel = path.relative(T, f) + ':' + (i + 1);
    const name = classify(rel.replace(/:\d+$/, ''), ln);
    if (name) { exempt.push(`${rel}  <- 具名豁免「${name}」 | ${ln.trim().slice(0, 100)}`); used.add(name); return; }
    if (NEEDLE.test(ln)) hits.push(rel + '  ' + ln.trim().slice(0, 100));
    if (LIC.test(ln)) licHits.push(rel + '  ' + ln.trim().slice(0, 100));
  });
}

const unused = ALLOW.filter(a => !used.has(a.name)).map(a => a.name);
console.log(`扫 ${files.length} 个装出来的文件（含 ${files.filter(f => f.endsWith('.pyc')).length} 个 .pyc）`);
for (const h of exempt) console.log('  EXEMPT ' + h);
if (unused.length) console.log(`  WARN 白名单条目一笔未命中（可能已过期，请核对后删除）：${unused.join(' / ')}`);
for (const h of hits) console.log('  GAMESS? ' + h);
for (const h of licHits) console.log('  LIC   ' + h);
console.log(`\n结论：具名豁免 ${exempt.length} 条，GAMESS 相关 ${hits.length} 条，许可冲突信号 ${licHits.length} 条`);
console.log('豁免账之外的命中都是违规：唯一合法的 GAMESS 出现就是上面逐条列出的免责声明。');
process.exit(hits.length + licHits.length > 0 ? 1 : 0);
