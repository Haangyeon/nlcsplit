#!/usr/bin/env node
/*
 pdf_lock_gate.js -- PreToolUse(Bash)：建 PDF 之前先看目标有没有被阅读器占用。

 为什么要有它：Acrobat 持有 main.pdf 时 pdflatex 会报 "I can't write on file"，
 而构建脚本只在 stderr 里留一句、PDF 仍是旧版——看上去"构建过了"。本仓已经因为
 这一点交付过两次旧图（2026-10-22 两次都是同一形态）。

 关窗的安全边界（别越写越勇）：只对**窗口标题里含目标文件名**的 Acrobat 进程发
 Ctrl+W，且发送前确认它确实在前台；任何一步不满足就停手并让构建失败，绝不猜标签。
 关不掉时退出码 2，构建不会带着旧 PDF 静默跑完。
*/
"use strict";
const fs = require("fs");
const path = require("path");
const cp = require("child_process");

const root = path.resolve(__dirname, "..", "..");
let raw = "";
try { raw = fs.readFileSync(0, "utf8"); } catch (e) { process.exit(0); }
let cmd = "";
try { cmd = (JSON.parse(raw).tool_input || {}).command || ""; } catch (e) { process.exit(0); }
// 只匹配"真正调用构建脚本"的命令（sh/bash build_pdf.sh ...），不要被 `git add tools/build_pdf.sh`
// 这类把脚本名当路径的命令误触发；文档名只认已知的三份。
const KNOWN = new Set(["main", "software", "p2"]);
const docs = [];
for (const mm of cmd.matchAll(/(?:^|[;&|]\s*|\n)\s*(?:sh|bash)\s+(?:\S*\/)?build_pdf\.sh(?:\s+([A-Za-z0-9_]+))?/g)) {
  docs.push(mm[1] && KNOWN.has(mm[1]) ? mm[1] : "main");
}
if (!docs.length) process.exit(0);
const targets = [...new Set(docs)].map(d => path.join(root, "paper", d + ".pdf"));

function writable(p) {
  // 开写句柄不足以判定：Acrobat 允许别人以写方式打开，却拒绝删除/改名。
  // 这里做一次"改名再改回"的原子探测（check_lock.py 用的同一判据），不改内容。
  const tmp = p + ".lockcheck";
  try {
    fs.renameSync(p, tmp);
    fs.renameSync(tmp, p);
    return true;
  } catch (e) {
    try { fs.renameSync(tmp, p); } catch (e2) { /* 已改回或从未改名 */ }
    return false;
  }
}
const ps = path.join(__dirname, "close_locked_pdf.ps1");
// 宿主进程的 PATH 不一定含 System32，按绝对路径找，找不到再退回 PATH。
const psExe = path.join(process.env.SystemRoot || "C:\\Windows", "System32",
                         "WindowsPowerShell", "v1.0", "powershell.exe");
const exe = fs.existsSync(psExe) ? psExe : "powershell";
for (const target of targets) {
  if (writable(target)) continue;
  const r = cp.spawnSync(exe, ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps, "-PdfPath", target],
                         { encoding: "utf8", timeout: 30000 });
  if (r.stdout) process.stdout.write(r.stdout);
  if (r.error) console.error("[pdf-lock-gate] spawn: " + r.error.message);
  if (r.stderr) console.error(String(r.stderr).trim().slice(0, 400));
  // 关窗是异步的：Acrobat 释放句柄可能晚几百毫秒，直接交给 pdflatex 会撞上竞态。
  let ok = false;
  for (let i = 0; i < 30 && !ok; i++) {
    ok = writable(target);
    if (!ok) Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 200);
  }
  if (!ok) {
    console.error("[pdf-lock-gate] " + path.basename(target) + " 仍被占用（" +
                  (r.stdout || "").trim() + "），构建已拦下：先在 Acrobat 里关掉它。");
    process.exit(2);
  }
}
process.exit(0);
