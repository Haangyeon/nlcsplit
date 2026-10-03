#!/usr/bin/env node
/*
 precommit_gate.js -- PreToolUse 钩子：`git commit` 之前先过三关。

 为什么放在这儿：本仓所有闸门（md2tex 的 15 个、claim_gate、MANIFEST 核对）都是"构建/发布时"跑的，
 而我一天里 commit 的次数远多于构建的次数——最脏的状态恰恰死在两次构建之间。把最低成本的一层
 挪到 commit 前，等于给"提交即验证"这条纪律装了个物理开关。

 三关（都很便宜，全本地，不碰网络）：
   1) 证据清单新鲜：MANIFEST.sha256 与每个证据文件实际字节一致（顺序错了这里必报）；
   2) 正文数字出处：claim_gate 在**已发出去的 5 份稿**上违规数为 0（台账 paper/notes/ 不拦，
      否则闸门会因大叫而失去信用）；
   3) 没有"存在但未跟踪"的引用路径（claim_gate 里 path 那一类）。

 逃生口是**显式且留痕的**：commit message 里写 `[gate-bypass: 理由]` 才放行，且理由会被追记到
 tools/hooks/GATE-OVERRIDES.log（故意不放在 evidence/：那里每个目录都被 MANIFEST 哈希锁着）。
 没有静默开关——闸门能被静默绕过就等于没有闸门。
*/
"use strict";
const fs = require("fs");
const path = require("path");
const cp = require("child_process");
const L = require("./lib.js");

function gateCounts(root) {
  const cg = path.join(root, "tools", "claim_gate.js");
  if (!fs.existsSync(cg)) return { num: 0, path: 0, err: "claim_gate.js 不在" };
  try {
    const o = cp.execSync(`node "${cg}" --stop-count`, { cwd: root, encoding: "utf8",
                                                         maxBuffer: 1 << 26 });
    const j = JSON.parse(o.trim().split("\n").pop());
    return { num: j.number || 0, path: j.path || 0, files: j.files || {}, err: null };
  } catch (e) {
    return { num: 0, path: 0, err: "闸门没跑成：" + String(e.message).slice(0, 90) };
  }
}

function check(root, msg) {
  const bad = [];
  const mf = L.staleManifests(root);
  if (mf.length) bad.push("证据清单陈旧 " + mf.length + " 条：\n    " + mf.slice(0, 5).join("\n    ")
    + "\n    办法：cd 进那个目录，find . -maxdepth 1 -type f ! -name 'MANIFEST*' -printf '%f\\0' | xargs -0 sha256sum > /tmp/mf.new && mv /tmp/mf.new MANIFEST.sha256，再 git add");
  const g = gateCounts(root);
  if (g.err) bad.push(g.err + "（这条不放行——读不到状态就当有问题）");
  const hot = Object.entries(g.files || {}).filter(([, v]) => v > 0)
                .map(([k, v]) => `${k}:${v}`).join(", ");
  if (g.num) bad.push(`正文数字出处：${g.num} 个数在跟踪的证据工件里找不到`
    + (hot ? "（" + hot + "）" : "")
    + "\n    办法：补归档 stdout，或让脚本把它算出来入库；不许塞 allowlist");
  if (g.path) bad.push(`引用路径：${g.path} 条不存在或未 git add` + (hot ? "（分布 " + hot + "）" : ""));
  if (/gate-bypass/i.test(msg || "")) {
    const why = (msg.match(/\[gate-bypass:\s*([^\]]+)\]/i) || [, "(没写理由)"])[1].trim();
    try {
      // 落点必须在 evidence/ 之外：那下面每个目录都有 MANIFEST.sha256 锁着，
      // 一个"每次绕过都要追加一行"的日志放进锁里，等于让逃生口自己制造下一条违规。
      const log = L.recordOverride(root, "precommit-bypass 理由: " + why,
                                   "问题:\n" + bad.join("\n"));
      process.stderr.write(`precommit-gate：本次按 [gate-bypass] 放行，已留痕 ${path.basename(log)}\n`);
      return [];
    } catch (e) { /* 留痕失败则不免除拦截 */ }
  }
  return bad;
}

async function main() {
  if (process.argv.includes("--selftest")) {
    const root = process.cwd();
    const g = gateCounts(root);
    const mf = L.staleManifests(root);
    console.log(`  claim_gate: 数字 ${g.num} 路径 ${g.path} err=${g.err || "无"}`);
    console.log(`  MANIFEST 陈旧: ${mf.length}`);
    // check() 报的是**问题类数**（清单 / 数字 / 路径 / 闸门读不到，最多 4 类），不是条数。
    const wantCats = (mf.length ? 1 : 0) + (g.err ? 1 : 0) + (g.num ? 1 : 0) + (g.path ? 1 : 0);
    const gotCats = check(root, "").length;
    console.log(`  真实仓：${gotCats} 类（期望 ${wantCats}）`);
    let fails = gotCats === wantCats ? 0 : 1;

    // 反向验证：造一个必然有问题的临时仓，闸门必须拦住；再证明逃生口能用且留痕。
    const os = require("os");
    const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "pcgate-"));
    fs.mkdirSync(path.join(tmp, "evidence", "qa"), { recursive: true });
    fs.writeFileSync(path.join(tmp, "evidence", "qa", "a.out"), "content\n");
    fs.writeFileSync(path.join(tmp, "evidence", "qa", "MANIFEST.sha256"),
                     "0".repeat(64) + "  a.out\n");
    const blocked = check(tmp, "");
    const blockOK = blocked.length >= 2;   // 陈旧清单 + claim_gate.js 不在
    console.log(`  ${blockOK ? "OK  " : "FAIL"} 临时坏仓被拦 ${blocked.length} 类（期望 ≥2）`);
    const escaped = check(tmp, "fix things [gate-bypass: 自检，故意放行]");
    const logPath = path.join(tmp, "tools", "hooks", "GATE-OVERRIDES.log");
    const escapeOK = escaped.length === 0 && fs.existsSync(logPath)
                     && /自检，故意放行/.test(fs.readFileSync(logPath, "utf8"));
    console.log(`  ${escapeOK ? "OK  " : "FAIL"} [gate-bypass] 放行并留痕（日志在 tools/hooks/ 而非锁住的 evidence/）`);
    fs.rmSync(tmp, { recursive: true, force: true });
    fails += blockOK ? 0 : 1;
    fails += escapeOK ? 0 : 1;
    console.log(fails ? `SELFTEST FAIL（${fails} 项不符）` : "SELFTEST PASS (3/3)");
    process.exit(fails ? 1 : 0);
  }
  const ev = await L.readEvent();
  const root = ev.cwd || process.cwd();
  if (!L.inProject(root)) process.exit(0);
  const cmd = ((ev.tool_input || {}).command || "");
  if (!/\bgit\s+commit\b/.test(cmd)) process.exit(0);
  const bad = check(root, cmd);
  if (!bad.length) process.exit(0);
  process.stderr.write("precommit-gate 拦下这次提交（" + bad.length + " 类问题）：\n  "
    + bad.join("\n  ").replace(/\n/g, "\n  ")
    + "\n修完再提交。确实要越过这道闸：在 commit message 里写 [gate-bypass: 一句话理由]，"
    + "它会留痕进 tools/hooks/GATE-OVERRIDES.log 供事后审。\n");
  process.exit(2);
}
main();
