#!/usr/bin/env node
/*
 * 出货前置核对：不跑 make_public_repo.js，只把它那几张名单**读准**，然后跟磁盘对。
 *
 * 为什么需要（2026-10-13 实测踩出来的）：
 *   1. 我今早加了两份测试（test_certificate.py / test_crossfamily_schemes.py）并补了白名单。
 *      "补了"这件事当时只有我自己知道——一旦漏补，出货会**静默少发**两份测试，
 *      而正文要写的"随包发布 N 个测试模块"就跟着错，且不会有任何东西报警。
 *   2. 我第一次用一条 node -e 内联正则去数白名单，`[...]?` 在注释里就截断了，
 *      于是报出"白名单缺 test_nlc_closure.py"——**假警报**。真因是解析方式不对：
 *      源码里有整行中文注释和括号，naive 正则读不准。本文件用带深度计数、跳过字符串的
 *      括号配对来取数组，并把行注释先剥掉。
 *
 * 判据（任一不满足就 rc=1，让作者在按出货之前看到，而不是出货之后）：
 *   A. `nlcsplit/tests/` 里每个 test_*.py 必须**二选一**：在 TESTS 白名单里，或被
 *      INTERNAL_ONLY_MODULES 具名声明为不发。两者都不在 ⇒ 静默漏发，rc=1。
 *   B. PKG / TESTS 里点名的每个文件必须真在磁盘上 ⇒ 否则出货时会缺件。
 *   C. 打印出"随包会发几个测试模块、收几条测试"，供正文那几处现在时计数引用；
 *      这个数字必须由这个脚本来给，不许手抄。
 */
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
// 可选参数：换一份"名单源文件"来跑。这是为了能让这道核对被**证伪**——
// 没见过它失败的检查器与没有检查器是同一回事（本仓 2026-10-13 一天里为这句话付了三次学费）。
const SRC_FILE = process.argv[2]
  ? path.resolve(ROOT, process.argv[2])
  : path.join(ROOT, 'tools', 'make_public_repo.js');
const SRC = fs.readFileSync(SRC_FILE, 'utf8');
// 先剥掉整行 // 注释：数组字面量中间夹着大段中文说明，带着它们做括号配对会看错行。
const CLEAN = SRC.split('\n').filter((l) => !/^\s*\/\//.test(l)).join('\n');

function arrayLiteral(name) {
  const m = CLEAN.match(new RegExp('const\\s+' + name + '\\s*=\\s*\\['));
  if (!m) return null;
  let i = m.index + m[0].length;      // 紧跟在 '[' 之后
  let depth = 1, out = '';
  while (i < CLEAN.length && depth > 0) {
    const c = CLEAN[i];
    if (c === '[') depth++;
    else if (c === ']') { depth--; if (depth === 0) { i++; break; } }
    out += c;
    i++;
  }
  // 用 JS 自己求值，而不是再写一套字符串解析：名单里可能有三元、拼接或引用别的常量。
  let val;
  try { val = Function('"use strict";return [' + out + ']')(); }
  catch (e) { console.error(`!! ${name} 数组无法求值：${e.message}`); process.exit(1); }
  return Array.isArray(val) ? val.map(String) : null;
}

const PKG = arrayLiteral('PKG') || [];
const TESTS = arrayLiteral('TESTS') || [];

// `INTERNAL_ONLY_MODULES` 在源文件里是 `{ 路径: 不发布的理由 }` **对象**，不是数组。
// 上一版只会读数组，于是把它当"没有具名不发"，反过来把 test_fastpair_ide.py 误报成
// "没人管、要静默少发"——检查器响了，但响在错的前提上，这比不响更糟。
function objectLiteral(name) {
  const m = CLEAN.match(new RegExp('const\\s+' + name + '\\s*=\\s*\\{'));
  if (!m) return null;
  let i = m.index + m[0].length, depth = 1, out = '';
  while (i < CLEAN.length && depth > 0) {
    const c = CLEAN[i];
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) { i++; break; } }
    out += c;
    i++;
  }
  try { return Function('"use strict";return {' + out + '}')(); }
  catch (e) { console.error(`!! ${name} 对象无法求值：${e.message}`); process.exit(1); }
}
const INTERNAL_OBJ = objectLiteral('INTERNAL_ONLY_MODULES') || {};
const INTERNAL = Object.keys(INTERNAL_OBJ);

let rc = 0;
console.log('# 出货前置核对（只读，不写任何文件）');
console.log('# git HEAD', require('child_process')
  .execFileSync('git', ['rev-parse', 'HEAD'], { cwd: ROOT, encoding: 'utf8' }).trim());
console.log(`# PKG ${PKG.length} 项 / TESTS ${TESTS.length} 项 / 具名不发 ${INTERNAL.length} 项`);

// B：白名单点名的文件必须真存在
const missing = [];
for (const f of PKG) if (!fs.existsSync(path.join(ROOT, 'nlcsplit', f))) missing.push('nlcsplit/' + f);
for (const f of TESTS) if (!fs.existsSync(path.join(ROOT, 'nlcsplit', 'tests', f))) missing.push('nlcsplit/tests/' + f);
if (missing.length) { console.log('!! 白名单点到的文件在磁盘上不存在：'); missing.forEach((m) => console.log('   ' + m)); rc = 1; }

// A：磁盘上的每个 test_*.py 要么随包，要么具名不发
const disk = fs.readdirSync(path.join(ROOT, 'nlcsplit', 'tests'))
  .filter((f) => /^test_.*\.py$/.test(f)).sort();
const namedInternal = (f) => INTERNAL.includes('nlcsplit/tests/' + f);
const undeclared = disk.filter((f) => !TESTS.includes(f) && !namedInternal(f));
const shippedTests = disk.filter((f) => TESTS.includes(f));
console.log(`\ntests 目录里 test_*.py 共 ${disk.length} 个：`);
for (const f of disk) {
  const tag = TESTS.includes(f) ? '随包' : (namedInternal(f) ? '具名不发' : '**没人管**');
  console.log(`   ${f.padEnd(32)} ${tag}`);
}
if (undeclared.length) {
  console.log(`!! ${undeclared.length} 个测试模块既不在 TESTS 也不在 INTERNAL_ONLY_MODULES ⇒ 出货会静默少发：`);
  undeclared.forEach((f) => console.log('   ' + f));
  console.log('   修法：随包就加进 TESTS；确属对照件/内部件就加进 INTERNAL_ONLY_MODULES 并在那里写清理由。');
  rc = 1;
}

// C：给正文现在时计数用的数，不许手抄
console.log('\n# 正文该填的数（由本脚本给）：');
console.log(`#   随包测试模块 WHEEL_TEST_MODULES = ${shippedTests.length}`);
console.log(`#   随包包内模块 PKG 数            = ${PKG.length}（含 certificate.py：${PKG.includes('certificate.py')}）`);
console.log(`#   具名不发                         = ${INTERNAL.join(', ') || '（无）'}`);
console.log(rc === 0 ? '\nVERDICT OK —— 名单齐、文件都在、每个测试都有着落' : '\nVERDICT NOTCLEAN —— 见上面 !! 行');
process.exit(rc);
