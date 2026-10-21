// 同一份仓、同一段逻辑，Windows 侧与 WSL 侧跑 claim_gate 得到的索引数不一样
// （实测 20987 vs 13940）。闸门只用 `trackedFiles()` + `readFileSync`，而两侧 `git ls-files evidence`
// 都是 312 条 ⇒ 差异只可能出在**读**这一步（`try { readFileSync } catch { continue }` 会静默跳过）。
// 本探针不复刻闸门的正则，只做一件事：对同一批 git 跟踪的 evidence 文件逐个尝试读，
// 列出"读不出的"与"读出来但一个十进制数都没有的"，两边各跑一次对答案。
const { execSync } = require("child_process");
const fs = require("fs");

const files = execSync("git ls-files evidence", { encoding: "utf8" })
  .split("\n").filter(Boolean).map((f) => f.replace(/\\/g, "/"));
let fail = [], zero = [], nums = 0;
for (const f of files) {
  let txt;
  try { txt = fs.readFileSync(f, "utf8"); }
  catch (e) { fail.push([f, e.code || e.name]); continue; }
  const m = txt.replace(/−/g, "-").match(/[+-]?\d+\.\d+(?:[eE][-+]?\d+)?/g) || [];
  if (!m.length) zero.push(f);
  nums += m.length;
}
console.log(JSON.stringify({
  side: process.platform, cwd: process.cwd(), tracked: files.length,
  read_fail: fail.length, no_decimal: zero.length, raw_decimal_tokens: nums,
  first_fail: fail.slice(0, 5), first_zero: zero.slice(0, 5),
}, null, 1));
