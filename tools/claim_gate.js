#!/usr/bin/env node
/*
 claim_gate.js -- 数字与路径的出处闸门（Qoder PostToolUse / Stop hook）。

 它防的是哪一类幻觉：不是"编造一个不存在的函数"那种（那种靠编译器就死了），而是本仓一周内
 反复出现的四种——
   1. 把记忆里上一个版本的数搬进正文（-6.129 搬进新表，而它属于另一个 PySCF）；
   2. 把"计数"当测量值报（"12/12 未收敛"其实是我判据写错）；
   3. 引用一个不存在或没入库的路径；
   4. 把注释里的数当出处。

 所以它只做**机械可判**的事：正文里出现的每个小数，必须能在被 git 跟踪的证据工件里找到同一个
 数（或它按四舍五入到该位数的原形）；每个反引号里的仓内路径，必须存在且已跟踪。
 它**不判**语义——"这个数字是不是在说错的事"它看不见，那仍然是人的活。

 双向自检是硬要求：`--selftest` 会用真数、假数、假路径、截断副本各喂一遍，任一条不符预期就
 非零退出。闸门自己不证明自己能失败，它就等于没守卫（本仓 2026-10-01 的记录）。
*/
"use strict";
const fs = require("fs");
const path = require("path");
const cp = require("child_process");

// 拦只拦**会发出去的**载体。paper/notes/ 与 paper/software_notes/ 是台账：那地方本来就是攒
// "还没找到原件的数"的队列，拿正文的标准拦它，等于逼着把台账塞进 allowlist 或者写 gate-bypass——
// 一个只会大叫的闸门，下次就没人信它的红了（本仓 2026-10-02 的教训）。
// 台账里的数想查，用 `--dump 文件名` 单独点它。
const SHIPPED = new Set(["paper/main.md", "paper/software.md", "paper/p2.md",
                         "MAIN-skeleton.md", "README.md"]);
// RESEARCH-*.md 是文献台账：正文引的外部比较值（-3.34 / 10.26434 那一类）出处在那里，
// 不把它算进证据索引，闸门就会把"文献里的数"误报成"我编的数"。
const EVIDENCE = [/^evidence\//, /^nlcsplit\//, /^dist\/nlcsplit\//, /^figs\//, /^RESEARCH-.*\.md$/];
// 代码里的数只有出现在**语句**里才算出处；注释里的数不算——本仓有一次正文引用的数字
// 就是从我自己写的注释里来的（95,481 那一例）。所以 .py 入索引前先剥 # 注释。
function stripPyComments(txt) {
  return txt.split("\n").map((l) => {
    const i = l.indexOf("#");
    return i >= 0 ? l.slice(0, i) : l;
  }).join("\n");
}
const IDX = path.join(__dirname, "..", ".qoder", "claim-index.json");
const FMT = 6;   // 索引格式版本：改了抽取规则就 +1，否则缓存会让新规则装作没生效

function git(args) {
  try {
    return cp.execSync("git " + args, { encoding: "utf8", maxBuffer: 1 << 28 }).trim();
  } catch (e) {
    return "";
  }
}
function trackedFiles() {
  return git("ls-files").split("\n").filter(Boolean);
}

/* ---------- 证据索引：所有被跟踪工件里的小数 ---------- */
function buildIndex() {
  const files = trackedFiles().filter((f) => EVIDENCE.some((re) => re.test(f)) && !re_skip(f));
  const byInt = {};          // 整数部分 -> [值]
  const exact = new Set();   // 原样字符串
  for (const f of files) {
    let txt;
    try { txt = fs.readFileSync(f, "utf8"); } catch (e) { continue; }
    // 中文排版里的减号是 U+2212，不是 ASCII '-'。不统一的话"归档里有这个数"会被判成没有。
    txt = txt.replace(/−/g, "-");
    if (/\.py$/.test(f)) txt = stripPyComments(txt);
    for (const m of txt.matchAll(/[+-]?\d+\.\d+(?:[eE][-+]?\d+)?/g)) {
      const s = m[0].replace(/^\+/, "");
      exact.add(s);
      exact.add(s.replace(/^-/, ""));   // 正文常取绝对值报幅度，符号不该成为失踪理由
      // 正文常把 -1.242e-04 写成 -1.242×10⁻⁴，取出来的只是尾数 -1.242。
      // 所以带指数的原样串要同时以尾数入索引，否则这一类真数会被当成没出处。
      const em = s.match(/^([+-]?\d+\.\d+)[eE][-+]?\d+$/);
      if (em) {
        exact.add(em[1]);
        exact.add(em[1].replace(/^-/, ""));
        // 尾数也要进"按整数部分分桶"的表，否则正文写 -1.056×10⁻³（取出来是 -1.056）
        // 而归档写 -1.0563e-03 时，四舍五入那条路走不到。
        const mv = parseFloat(em[1]);
        if (isFinite(mv)) (byInt[Math.trunc(mv)] || (byInt[Math.trunc(mv)] = [])).push(mv);
      }
      const v = parseFloat(s);
      if (!isFinite(v)) continue;
      const ip = Math.trunc(v);
      (byInt[ip] || (byInt[ip] = [])).push(v);
    }
  }
  for (const k of Object.keys(byInt)) byInt[k].sort((a, b) => a - b);
  return { fmt: FMT, head: git("rev-parse HEAD"), n: files.length, exact, byInt };
}
function re_skip(f) {
  return /\.(png|jpg|pdf|zip|whl|gz|lock)$/.test(f) || /MANIFEST\.sha256$/.test(f);
}
function loadIndex(force) {
  // 缓存以前按 (格式版本, HEAD) 复用。这个键**看不见 `git add`**：新归档还没提交时，
  // 闸门会拿旧索引判它"无原件"，或者反过来放过一个已被改过内容的档案。省的是 0.6 秒，
  // 买到的是两类静默错判——不值。现在每次重扫（全量 0.7 s）。force 参数保留只是为了调用点不改。
  const idx = buildIndex();
  try {
    fs.mkdirSync(path.dirname(IDX), { recursive: true });
    fs.writeFileSync(IDX, JSON.stringify({ ...idx, exact: [...idx.exact] }));
  } catch (e) { /* 索引只是调试副本，写不下不影响判定 */ }
  idx.exact = new Set(idx.exact);
  return idx;
}

/* 正文里的数 c 是否由某个证据值舍入而来。
   写成数值比较而不是字符串比较，因为两类写法都会撞到同一个数：
     · 正文 1.274（绝对值、三位）对归档 -1.2737（负、四位）——符号和位数同时变；
     · 正文 -8.34e-4 对归档 -0.000834——同一个数两种字面，字符串永远对不上。
   容差取"该数最后那一位的一半"，所以它只放行同值的另一种写法，不放行差一根末位的数。 */
function findSource(idx, c) {
  const s = c.replace(/^\+/, "");
  if (idx.exact.has(s)) return s;
  const m = s.match(/^([+-]?\d+)\.(\d+)(?:[eE]([-+]?\d+))?$/);
  if (!m) return null;
  const d = m[2].length;
  const exp = m[3] ? parseInt(m[3], 10) : 0;
  const val = parseFloat(s);
  const tol = 0.5 * Math.pow(10, exp - d);
  const buckets = new Set([Math.trunc(val), Math.trunc(Math.abs(val)), Math.trunc(-Math.abs(val))]);
  for (const b of buckets) {
    for (const v of (idx.byInt[b] || [])) {
      if (Math.abs(v - val) <= tol) return String(v);
      if (Math.abs(-v - val) <= tol) return String(v);   // 正文取的是绝对值
    }
  }
  return null;
}

/* ---------- 待检文本里的断言 ---------- */
function claimsOf(text) {
  const out = [];
  const lines = text.split("\n");
  lines.forEach((ln0, i) => {
    const ln = ln0.replace(/−/g, "-");
    // 反引号里的路径/命令先抹掉；§3.2 这类节号与 2.12.1 这类版本串也不是化学量。
    const stripped = ln.replace(/`[^`]*`/g, "``")
      .replace(/§\s?\d+(?:\.\d+)*/g, "SEC")
      .replace(/\d+\.\d+\.\d+(?:\.\d+)*/g, "VER");
    for (const m of stripped.matchAll(/(?<![\w.\/])[+-]?\d+\.\d+(?:[eE][-+]?\d+)?/g)) {
      const num = m[0].replace(/^\+/, "");
      // arXiv id（2306.12345）与 DOI 前缀（10.xxxx）不是量。
      if (/^\d{4}\.\d{4,5}$/.test(num) || /^10\.\d{4,5}$/.test(num)) continue;
      out.push({ num, line: i + 1, text: ln.trim().slice(0, 110) });
    }
    for (const m of stripped.matchAll(/(?<![\w.])\d+(?=个|格|行|条|页|对|体系|格全|passed)/g)) {
      out.push({ num: m[0], int: true, line: i + 1, text: ln.trim().slice(0, 110) });
    }
  });
  return out;
}
function citedPaths(text) {
  const out = [];
  // 反引号**可以跨行折行**：一条真路径被排版劈成两半时，只按单行匹配会截出个假路径
  // （`nlcsplit/logs/step_h.json` 就被报成 `logs/step_h.json 不存在`）。反向也一样：
  // 跨行的假引用以前就这么混过去了。所以取整段反引号内容，折掉空白再判它像不像路径。
  const PATHISH = /^[A-Za-z0-9_.\/-]+\/[A-Za-z0-9_.\/-]*\.(?:py|js|out|json|md|txt|sh|csv|png|tex|tsv|log)$/;
  for (const m of text.matchAll(/`([^`]+)`/g)) {
    const raw = m[1];
    if (raw.includes("...") || raw.includes("…")) continue;   // 省略号写法是指代，交给 md2tex 那道全路径闸门
    // 只认"斜杠后面断行"这一种折行。反引号里也可能是**命令**（`node tools/x.js`），
    // 无条件抹空白会把 "node" 和路径粘成一个假路径——那是我自己给闸门添的第一类假报。
    const p = raw.replace(/\/\s+/g, "/").trim();
    if (PATHISH.test(p)) out.push(p);
  }
  return out;
}
function allowlist() {
  const p = path.join(__dirname, "claim-allowlist.tsv");
  if (!fs.existsSync(p)) return [];
  const rows = [];
  fs.readFileSync(p, "utf8").split("\n").forEach((l, i) => {
    if (!l.trim() || l.startsWith("#")) return;
    const parts = l.split("\t");
    // 三列齐全才算一条放行：少一列就是给闸门挖洞（"每行必须有理由"这条纪律由代码执行，不靠自觉）。
    if (parts.length !== 3 || !parts[0] || !parts[1] || !parts[2]) {
      process.stderr.write(`claim-allowlist.tsv 第 ${i + 1} 行不是"文件<TAB>正则<TAB>理由"，本次不放行任何人：${l}\n`);
      process.exitCode = 3;
      return;
    }
    rows.push({ file: parts[0].trim(), re: new RegExp(parts[1]), why: parts[2].trim() });
  });
  return rows;
}

let _declared = null;
/** 包里才有、仓里没有的路径（`docs/tables_and_provenance.md` 这类）算不算幻觉？
 *  只有当**被跟踪的构建脚本自己声明了这个名字**时才算有出处：那是"它会产出的文件"的一手记录。
 *  不这么放行就得把 dist/ 的存在当判据，而 dist/ 在全新克隆上根本不存在——那样闸门会天天假报。 */
function declaredPaths() {
  if (_declared) return _declared;
  const set = new Set();
  const re = /['"]([A-Za-z0-9_.\/-]+\/[A-Za-z0-9_.\/-]*\.(?:md|py|js|yml|yaml|json|txt|sh|csv|tsv|tex|out|png))['"]/g;
  for (const f of trackedFiles()) {
    if (!/^(tools\/|\.github\/|setup\.py$|pyproject\.toml$|MANIFEST\.in$)/.test(f)) continue;
    let t; try { t = fs.readFileSync(f, "utf8"); } catch (e) { continue; }
    for (const m of t.matchAll(re)) set.add(m[1]);
  }
  _declared = set;
  return set;
}

function checkText(idx, label, text) {
  const bad = [];
  const allow = allowlist();
  for (const c of claimsOf(text)) {
    if (c.int) continue;                       // 计数类需要人工判语境，先只拦小数
    // 放行按**文件**绑定：写在 p2.md 名下的例外不能替 main.md 里的同名数字说话。
    if (allow.some((a) => a.file === label && a.re.test(c.num))) continue;
    if (!findSource(idx, c.num)) bad.push({ kind: "number", where: `${label}:${c.line}`, detail: c.num + "  |  " + c.text });
  }
  const tracked = new Set(trackedFiles());
  for (const pth of citedPaths(text)) {
    if (fs.existsSync(pth)) {
      if (!tracked.has(pth)) bad.push({ kind: "path", where: label, detail: pth + " 存在但未 git add" });
    } else if (!declaredPaths().has(pth)) {
      bad.push({ kind: "path", where: label, detail: pth + " 不存在（也不是任何跟踪构建脚本声明的产出名）" });
    }
  }
  return bad;
}

/* ---------- 入口 ---------- */
function isCarrier(f) { return SHIPPED.has(f); }
// 这个闸门是按 GAMESS 这棵树的证据结构写的。全局 hooks 目录会每个项目都叫到一次，
// 所以先认作用域：不在本项目、或本项目没装 settings.json 的，一律放行且不吱声。
function inScope(cwd) {
  const c = (cwd || "").replace(/\\/g, "/");
  return /\/GAMESS$/i.test(c) || fs.existsSync(path.join(cwd, ".qoder", "settings.json"));
}

function runHook() {
  let raw = "";
  process.stdin.on("data", (d) => (raw += d));
  process.stdin.on("end", () => {
    let ev = {};
    try { ev = JSON.parse(raw || "{}"); } catch (e) { process.exit(0); }
    const cwd = ev.cwd || process.cwd();
    process.chdir(cwd);
    if (!inScope(cwd)) process.exit(0);
    const fp = (ev.tool_input && ev.tool_input.file_path) || "";
    const rel = path.relative(cwd, fp).replace(/\\/g, "/");
    if (process.argv.includes("--stop")) return runStop(ev, cwd);
    if (!isCarrier(rel)) process.exit(0);
    const text = (ev.tool_input.new_string || ev.tool_input.content || ev.tool_input.replacement || "");
    if (!text) process.exit(0);
    const idx = loadIndex(false);
    const bad = checkText(idx, rel, text);
    if (!bad.length) process.exit(0);
    report(bad, rel, idx);
  });
}

function runStop(ev, cwd) {
  const idx = loadIndex(true);
  const changed = git("status --porcelain").split("\n").filter(Boolean)
    .map((l) => l.slice(3).trim().replace(/\\/g, "/"))
    .filter((f) => isCarrier(f) && fs.existsSync(f));
  let bad = [];
  for (const f of changed) bad = bad.concat(checkText(idx, f, fs.readFileSync(f, "utf8")));
  if (!bad.length) { process.stderr.write("claim-gate: clean (" + changed.length + " carriers, " + idx.exact.size + " indexed numbers)\n"); process.exit(0); }
  report(bad, "工作树", idx);
}

function report(bad, label, idx) {
  const msg = [
    `claim-gate 拦下 ${bad.length} 条（${label}；证据索引 ${idx.n} 个工件 / ${idx.exact.size} 个数）。`,
    ...bad.slice(0, 15).map((b) => `  [${b.kind}] ${b.where}: ${b.detail}`),
    ...(bad.length > 15 ? [`  ...另 ${bad.length - 15} 条`] : []),
    "",
    "怎么办（按顺序试，别直接放行）：",
    "  1) 这个数是不是上一版/另一环境的？回到产出它的脚本或归档重读一遍，改正文；",
    "  2) 是你新算的？先把产生它的 stdout 入库（evidence/…）并 git add，再重跑；",
    "  3) 是路径没入库？git add；",
    "  4) 确实是结构性数字（阈值、页数、字号、坐标轴范围）而不是化学量？写进 tools/claim-allowlist.tsv，**必须带理由列**，那文件是审得出来的。",
  ].join("\n");
  process.stderr.write(msg + "\n");
  process.exit(2);
}

/* ---------- 自检：闸门必须证明自己能失败 ---------- */
function selftest() {
  const cwd = process.cwd();
  const idx = loadIndex(true);
  const fails = [];
  const probe = (name, text, expectBad) => {
    const got = checkText(idx, "selftest", text).length;
    const ok = expectBad ? got > 0 : got === 0;
    console.log(`  ${ok ? "OK  " : "FAIL"} ${name} -> ${got} 条违规`);
    if (!ok) fails.push(name);
  };
  // 取一个索引里真存在的数当"有出处"的正样本
  const real = [...idx.exact].find((s) => /\d+\.\d{4}/.test(s)) || "-6.152597";
  probe("真数不拦", `the value is ${real} kcal/mol`, false);
  probe("假小数拦", "the deviation is -1.234567 kcal/mol", true);
  probe("假整数语境不拦(语境未建模)", "there are 424242 rows", false);
  probe("不存在的路径拦", "read `evidence/nope/does_not_exist_zz.out`", true);
  probe("未跟踪路径拦", "produced by `scratch/hdr_2121.txt`", true);
  // 包内路径：由跟踪的构建脚本声明的才放行；分母必须打印，否则"0 条违规"和"0 条被解析"长得一样。
  const decl = declaredPaths();
  console.log(`  ---- 跟踪构建脚本声明的产出名：${decl.size} 个`);
  if (!decl.size) { console.log("SELFTEST FAILED: 声明集为空 -> 包内路径这条规则在空转"); process.exit(1); }
  probe("包内路径(已声明)不拦", "ships as `docs/tables_and_provenance.md`", false);
  probe("包内路径(未声明)拦", "ships as `docs/nobody_builds_this_zz.md`", true);
  // 折行的反引号路径：真路径劈成两半必须认得出，假路径劈成两半也必须拦得住。
  probe("折行的真路径不拦", "see `evidence/l2cp/\n20261003T0907Z_wsl2121-cp_levels.out` here", false);
  probe("折行的假路径拦", "see `evidence/l2cp/\nno_such_zz_level.out` here", true);
  probe("反引号里的命令不当路径", "rebuild with `node tools/make_public_repo.js`, which", false);
  // 作用域本身也要测：放宽一处就淹没台账，收紧一处就放过正文。两个方向都得有声音。
  const scope = [
    ["paper/main.md", true], ["paper/software.md", true], ["paper/p2.md", true],
    ["MAIN-skeleton.md", true], ["README.md", true],
    ["paper/notes/number_audit.md", false], ["paper/software_notes/claims_audit.md", false],
    ["paper/references.bib", false],
  ];
  for (const [f, want] of scope) {
    const got = isCarrier(f);
    const ok = got === want;
    console.log(`  ${ok ? "OK  " : "FAIL"} 作用域 ${f} -> ${got}（期望 ${want}）`);
    if (!ok) fails.push("scope:" + f);
  }
  if (fails.length) { console.log("SELFTEST FAILED: " + fails.join(", ")); process.exit(1); }
  console.log("SELFTEST PASS (indexed " + idx.n + " artifacts, " + idx.exact.size + " numbers)");
  process.exit(0);
}

if (process.argv.includes("--selftest")) selftest();
else if (process.argv.includes("--stop-count")) {
  // 给别的钩子用的机器可读计数：不打印细节，只报每类几条 + 按载体的分布。
  const idx = loadIndex(true);   // 强制重建：刚 git add 的档案必须算进出处池
  const files = {};
  let num = 0, pth = 0;
  const list = git("ls-files").split("\n").filter(isCarrier)
    .concat(git("status --porcelain").split("\n").filter(Boolean)
      .map((l) => l.slice(3).trim().replace(/\\/g, "/")).filter((f) => isCarrier(f) && fs.existsSync(f)));
  for (const f of [...new Set(list)]) {
    const bad = checkText(idx, f, fs.readFileSync(f, "utf8"));
    files[f] = bad.length;
    num += bad.filter((b) => b.kind === "number").length;
    pth += bad.filter((b) => b.kind === "path").length;
  }
  console.log(JSON.stringify({ number: num, path: pth, files, head: idx.head }));
  process.exit(0);
}
else if (process.argv.includes("--dump")) {
  // 全量清单模式：不被 15 条截断，用来给一次审计列工作队列
  const f = process.argv[process.argv.indexOf("--dump") + 1];
  const idx = loadIndex(true);
  for (const b of checkText(idx, f, fs.readFileSync(f, "utf8"))) {
    console.log(`${b.kind}\t${b.where}\t${b.detail}`);
  }
  process.exit(0);
}
else if (process.argv.includes("--stop")) { runStop({}, process.cwd()); }
else runHook();
