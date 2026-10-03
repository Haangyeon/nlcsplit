#!/usr/bin/env node
/*
 comment_sentinel.js -- PostToolUse 钩子：拦住"往代码注释里写实测数字"这个动作。

 起因是本仓的一次真实事故：我在 nlcsplit/fastpair.py 的注释里写过一个 95,481，
 它随后被正文引用成"实测值"，而它根本不是任何一次跑的输出。注释是模型最爱写的东西，
 也是最少被核对的东西——它长得像证据，其实只是我的叙述。

 判据刻意收窄，只报"像测量值"的那些：小数位 >= 4，或者数字旁边 18 个字符内出现单位
 （kcal/mol、Ha、Å、e-0X 之类）。阈值、常数、字号、坐标轴范围不报——那些写在代码里是对的。
 报的方式是 exit 2：把理由喂回我，让我当场改（删掉数字，或改成指向归档路径），
 而不是攒到论文里再抓。
*/
"use strict";
const path = require("path");
const L = require("./lib.js");

const UNIT = /(kcal|Ha|kcal\/mol|Å|A\b|e[-+]?0?\d|百分比|%)/;
const NUM = /(\d+\.\d{4,})/g;

function addedText(ev) {
  const ti = (ev && ev.tool_input) || {};
  if (typeof ti.content === "string") return ti.content;
  if (typeof ti.new_string === "string") return ti.new_string;
  const edits = ti.edits || [];
  return edits.map((e) => e.new_string || "").join("\n");
}

function commentHits(text) {
  const out = [];
  text.split("\n").forEach((ln, i) => {
    const inComment = /^\s*(#|\/\/|\*|"""|''')/.test(ln) || /#\s/.test(ln) || /\/\/\s/.test(ln);
    if (!inComment) return;
    for (const m of ln.matchAll(NUM)) {
      out.push({ line: i + 1, num: m[1], why: "小数位 >= 4" });
    }
    const mu = ln.match(/(\d+\.\d+)\s*(kcal\/mol|Ha|Å)/);
    if (mu && !out.some((o) => ln.includes(o.num))) {
      out.push({ line: 0, num: mu[1], why: "数字旁边带单位（像在报测量值）" });
    }
  });
  return out;
}

async function main() {
  if (process.argv.includes("--selftest")) {
    const cases = [
      ["# 实测水二聚体 -6.1290 kcal/mol", true],
      ["# 复合物冻 2，单体冻 [1, 1]", false],
      ["tol = 1e-8    # 判据", false],
      ["// level-2 归档只存到 -0.5930 的三位", true],
    ];
    let bad = 0;
    for (const [txt, want] of cases) {
      const got = commentHits(txt).length > 0;
      const ok = got === want;
      if (!ok) bad++;
      console.log(`  ${ok ? "OK  " : "FAIL"} 期望${want ? "报" : "不报"} 实${got ? "报" : "不报"} :: ${txt.slice(0, 44)}`);
    }
    console.log(bad ? "SELFTEST FAILED" : "SELFTEST PASS");
    process.exit(bad ? 1 : 0);
  }
  const ev = await L.readEvent();
  const rel = L.norm((ev.tool_input && ev.tool_input.file_path) || "")
    .replace(L.norm(ev.cwd || process.cwd()) + "/", "");
  if (!L.inProject(ev.cwd) || !/\.(py|js)$/.test(rel) || /\.test\.|tests\//.test(rel)) process.exit(0);
  const hits = commentHits(addedText(ev));
  if (!hits.length) process.exit(0);
  process.stderr.write(
    "comment-sentinel：这次写进注释的数有「测量味」，它们以后会被正文当出处引用（本仓 95,481 那一例）。\n"
    + hits.slice(0, 6).map((h) => `  ${rel}:${h.line || "?"}  ${h.num}  (${h.why})`).join("\n")
    + "\n怎么办：删掉具体数字，改成指向归档（`evidence/.../<file>.out` 第几行）；"
    + "或者它就是阈值/常数？那把它写成代码里的常量而不是注释里的句子。\n");
  process.exit(2);
}
main();
