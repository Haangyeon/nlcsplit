#!/usr/bin/env node
/*
 session_brief.js -- SessionStart / PreCompact 钩子：把"当前真实状态"塞进上下文，而不是让我凭印象。

 治的是这一周里最贵的一类错：小模型（也包括我）在长会话里会把"我记得的状态"当成"状态"——
 于是出现"我说过跑完了但其实没跑""引用一个已经不存在的列名""把上一次的数字搬进新表"。
 会话开始与压缩之前各注入一次硬事实，成本是几次 git 调用，收益是每次开场都从同一个真值出发。

 它不提供结论，只提供可核对的清单；任何一条读不出来就明写"读不出来"，不许用空白冒充没有。
*/
"use strict";
const fs = require("fs");
const path = require("path");
const L = require("./lib.js");

function brief(root) {
  const head = L.git("log --oneline -3", root) || "(git log 失败)";
  const dirty = L.git("status --porcelain", root);
  const dirtyN = dirty ? dirty.split("\n").filter(Boolean).length : 0;
  const lines = [];
  lines.push("== 本项目开场简报（由 session_brief 钩子生成，不是我自己写的）==");
  // 这条简报能被注入，只证明 SessionStart 活着。其余四条一起查——本仓记过"写了脚本≠闸门在跑"。
  const inst = path.join(root, "tools", "hooks", "install.js");
  if (fs.existsSync(inst)) {
    try {
      const cp = require("child_process");
      const o = cp.execSync(`node "${inst}" --check`, { cwd: root, encoding: "utf8",
                                                        stdio: ["ignore", "pipe", "pipe"] }).trim();
      lines.push("闸门注册：" + o);
    } catch (e) {
      lines.push("闸门注册：**与入库的 fragment 不一致或 .qoder/settings.json 读不到** —— "
        + "这条会话里可能根本没有闸门在跑。先跑 node tools/hooks/install.js --check 看差在哪，"
        + "别以为改了脚本就有效。");
    }
  }
  lines.push("HEAD 三个提交：\n" + head.split("\n").map((l) => "  " + l).join("\n"));
  lines.push(`未提交改动：${dirtyN} 个文件` + (dirtyN ? "\n" + dirty.split("\n").slice(0, 8)
              .map((l) => "  " + l).join("\n") : ""));
  const mf = L.staleManifests(root);
  lines.push("证据清单（MANIFEST.sha256）：" + (mf.length ? "陈旧 " + mf.length + " 条\n  "
              + mf.slice(0, 6).join("\n  ") : "新鲜"));
  const cg = path.join(root, "tools", "claim_gate.js");
  if (fs.existsSync(cg)) {
    try {
      const cp = require("child_process");
      const o = cp.execSync(`node "${cg}" --stop-count`, { cwd: root, encoding: "utf8" }).trim();
      // 闸门给的是机器可读 JSON，但这里是**注入给我读的上下文**：原始 JSON 里那一大串
      // per-file 计数我每次都要自己在脑子里解析，反而成了新的错源。只留三个数 + 有问题的文件名。
      const j = JSON.parse(o.split("\n").pop());
      const hot = Object.entries(j.files || {}).filter(([, v]) => v > 0)
                    .map(([k, v]) => `${k}=${v}`);
      lines.push(`正文数字出处闸门（只查已发的 5 份稿）：数字 ${j.number} 条 / 路径 ${j.path} 条`
        + (j.number + j.path
            ? " —— " + hot.join(", ") + "。先补原件或改成脚本生成，不要写进 allowlist。"
            : "（干净，head " + String(j.head).slice(0, 7) + "）"));
    } catch (e) { lines.push("正文数字出处闸门：没跑成（" + String(e.message).slice(0, 60) + "）"); }
  }
  const prog = path.join(root, "PROGRESS-nlcsplit.md");
  if (fs.existsSync(prog)) {
    const t = fs.readFileSync(prog, "utf8").split("\n");
    const heads = t.filter((l) => /^## /.test(l)).slice(-3);
    lines.push("PROGRESS-nlcsplit.md 最后三个小节：\n" + heads.map((h) => "  " + h).join("\n"));
  }
  lines.push("三条硬规矩（都源自本仓真实事故，不是通用建议）：");
  lines.push("  1) 认文件不认通知：后台任务说 exit 0 也要读它自己落盘的退出码；");
  lines.push("  2) MANIFEST 在所有证据编辑定稿之后最后重生成，顺序反了 gate C2 会抓到你自己；");
  lines.push("  3) 集群上的原始日志必须 cat 原文 + 比 sha256 才算入库，禁止用终端回显拼档案。");
  return lines.join("\n");
}

function emit(text, ev) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: ev.hook_event_name === "PreCompact" ? "PreCompact" : "SessionStart",
      additionalContext: text,
    },
  }) + "\n");
  process.exit(0);
}

async function main() {
  if (process.argv.includes("--selftest")) {
    const root = process.cwd();
    const b = brief(root);
    const need = ["HEAD 三个提交", "未提交改动", "MANIFEST", "三条硬规矩", "出处闸门", "闸门注册"];
    const miss = need.filter((k) => !b.includes(k));
    // 负向：闸门那一段必须是渲染过的，原始 JSON 漏进上下文就是这次的回归。
    const leak = /\{"number":/.test(b);
    if (leak) miss.push("闸门段落漏了原始 JSON");
    console.log(miss.length ? "SELFTEST FAIL 缺: " + miss.join(",")
                            : "SELFTEST PASS " + b.length + " 字节（无原始 JSON 泄漏）");
    process.exit(miss.length ? 1 : 0);
  }
  const ev = await L.readEvent();
  const root = ev.cwd || process.cwd();
  if (!L.inProject(root)) process.exit(0);
  emit(brief(root), ev);
}
main();
