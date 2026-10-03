#!/usr/bin/env node
/*
 stop_gate.js -- Stop 钩子：我想"就这样结束会话"时，先看清留下了什么。

 治的是他最怕的那件事：我把状态搞乱然后收工。具体三类：
   1) 载体或证据有未提交改动（"验证过却没落库"是本仓丢工的主要方式）；
   2) 证据清单陈旧（改了档案没重生成 MANIFEST，等于哈希锁是假的）；
   3) 正文里还有找不到原件的数字。
 任何一条成立就 exit 2 —— asyncRewake 会把我叫醒，理由作为新一轮输入，我必须在结束前
 处理或明确写成待办。逃生口同 precommit：`[gate-bypass: 理由]` 出现在我最近的输出里才放行，
 且留痕。

 刻意**不做**的：不跑 pytest（30 秒起，会让每次收尾都变慢，慢的守卫会被绕开），
 不碰网络（集群状态由任务清单管，不由钩子管）。
*/
"use strict";
const fs = require("fs");
const path = require("path");
const cp = require("child_process");
const L = require("./lib.js");

function problems(root) {
  const out = [];
  const dirty = L.git("status --porcelain", root).split("\n").filter(Boolean);
  const risky = dirty.filter((l) => /^.{1,2}\s+(evidence\/|paper\/|MAIN-skeleton|nlcsplit\/|tools\/)/.test(l));
  if (risky.length) {
    out.push(`未提交的实质改动 ${risky.length} 个（列前 8 个）：\n    `
             + risky.slice(0, 8).map((l) => l.trim()).join("\n    "));
  }
  const mf = L.staleManifests(root);
  if (mf.length) out.push(`证据清单陈旧 ${mf.length} 条：\n    ` + mf.slice(0, 6).join("\n    "));
  try {
    const o = cp.execSync(`node "${path.join(root, "tools", "claim_gate.js")}" --stop-count`,
                          { cwd: root, encoding: "utf8", maxBuffer: 1 << 26 });
    const j = JSON.parse(o.trim().split("\n").pop());
    if (j.number || j.path) {
      const hot = Object.entries(j.files || {}).filter(([, v]) => v > 0)
                    .map(([k, v]) => `${k}=${v}`).join(", ");
      out.push(`正文数字出处：${j.number} 个数无原件 / ${j.path} 条路径问题（${hot || "分布未知"}）`);
    }
  } catch (e) { out.push("claim_gate 没跑成：" + String(e.message).slice(0, 80)); }
  return out;
}

async function main() {
  if (process.argv.includes("--selftest")) {
    const p = problems(process.cwd());
    console.log("  当前问题类数：" + p.length);
    p.forEach((x) => console.log("   - " + x.split("\n")[0]));
    console.log("SELFTEST PASS（能读出问题就算通；零问题也是合法结果）");
    process.exit(0);
  }
  const ev = await L.readEvent();
  const root = ev.cwd || process.cwd();
  if (!L.inProject(root)) process.exit(0);
  const p = problems(root);
  if (!p.length) process.exit(0);
  const transcript = ev.transcript_path ? String(ev.transcript_path) : "";
  if (transcript && fs.existsSync(transcript)) {
    try {
      const t = fs.readFileSync(transcript, "utf8");
      if (/\[gate-bypass:/.test(t.slice(-40000))) {
        L.recordOverride(root, "stop-bypass（收工前仍有未了结项）", p.join("\n"));
        process.exit(0);
      }
    } catch (e) { /* 读不到就照常拦 */ }
  }
  process.stderr.write(
    "stop-gate：先别收工，留下了这些（" + p.length + " 类）：\n  "
    + p.join("\n  ").replace(/\n/g, "\n  ")
    + "\n每条要么当场处理（提交 / 重生成 MANIFEST / 补归档或改成脚本生成），"
    + "要么写进任务清单并在结束时明确告诉我它没做完。真的要先收工：在你最后一段话里写 [gate-bypass: 理由]。\n");
  process.exit(2);
}
main();
