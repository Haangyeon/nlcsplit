/*
 hooks/lib.js -- 本项目几个钩子共用的哑办法。

 为什么要有共用库：钩子是"我下次一定会忘"的那类东西，一旦每个钩子各自写一份"什么算载体、
 什么算本项目"，三份规则就会开始各自漂移——本仓已经有过三次同一规则三个副本的事故。
 所以判定规则集中在这里，钩子只写自己那条判据。
*/
"use strict";
const fs = require("fs");
const path = require("path");
const cp = require("child_process");

// 载体清单**不在这里**：它只有一份，在 tools/claim_gate.js 的 SHIPPED。
// 本仓同一规则写过三个副本、各自漂移过三次，所以这里宁可不导出，逼调用方去问闸门。

function git(args, cwd) {
  try {
    return cp.execSync("git " + args, { cwd: cwd || process.cwd(), encoding: "utf8",
                                        maxBuffer: 1 << 28, stdio: ["ignore", "pipe", "ignore"] }).trim();
  } catch (e) { return ""; }
}

function norm(p) { return (p || "").replace(/\\/g, "/"); }

function inProject(cwd) {
  const c = norm(cwd);
  return /\/GAMESS$/i.test(c) || fs.existsSync(path.join(cwd, ".qoder", "settings.json"));
}

/** 从 stdin 读事件 JSON；坏了就当没这回事（exit 0），绝不把会话卡死在自己的解析错误上。 */
function readEvent() {
  return new Promise((resolve) => {
    let raw = "";
    process.stdin.on("data", (d) => (raw += d));
    process.stdin.on("end", () => {
      try { resolve(JSON.parse(raw || "{}")); } catch (e) { resolve({}); }
    });
    process.stdin.on("error", () => resolve({}));
  });
}

function eventText(ev) {
  const ti = (ev && ev.tool_input) || {};
  return [ti.file_path, ti.command, ti.content, ti.new_string, ti.prompt]
    .filter((x) => typeof x === "string").join("\n");
}

/** 证据目录里 MANIFEST.sha256 与实际字节的差。返回 [] 表示新鲜。 */
function staleManifests(root) {
  const out = [];
  const evRoot = path.join(root, "evidence");
  if (!fs.existsSync(evRoot)) return out;
  for (const d of fs.readdirSync(evRoot)) {
    const dir = path.join(evRoot, d);
    if (!fs.statSync(dir).isDirectory()) continue;
    const mf = path.join(dir, "MANIFEST.sha256");
    if (!fs.existsSync(mf)) continue;
    const want = {};
    for (const ln of fs.readFileSync(mf, "utf8").split("\n")) {
      const m = ln.match(/^([0-9a-f]{64})\s+\*?(.+)$/);
      if (m) want[m[2].trim()] = m[1];
    }
    // "一行都没解析出来"必须自己报告：否则下面的循环找不到 want[f]，会把整份清单读成空转。
    if (!Object.keys(want).length) { out.push(`${d}/MANIFEST.sha256 解析出 0 条登记`); continue; }
    for (const f of fs.readdirSync(dir)) {
      if (f.startsWith("MANIFEST") || !fs.statSync(path.join(dir, f)).isFile()) continue;
      // 自己算，不调外部 sha256sum：那条 shell 路在 Windows 侧取决于 cmd 的 PATH，
      // 一旦取不到值，比较的就不是字节了（本仓把"读不到"当"没有差"见过两回）。
      const got = require("crypto").createHash("sha256")
        .update(fs.readFileSync(path.join(dir, f))).digest("hex");
      if (!want[f]) out.push(`${d}/${f} 未登记进 MANIFEST.sha256`);
      else if (want[f] !== got) out.push(`${d}/${f} 与 MANIFEST 登记的哈希不符（改过没重生成）`);
    }
  }
  return out;
}

/** 双向自检：同一个函数必须对新鲜说"没差"、对三种坏法各说一次"有差"。 */
function selftestStaleManifests() {
  const os = require("os");
  const sha = (b) => require("crypto").createHash("sha256").update(b).digest("hex");
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "qgate-"));
  const dir = path.join(root, "evidence", "qa");
  fs.mkdirSync(dir, { recursive: true });
  const body = Buffer.from("one line\n");
  const mk = (mfLines, extra) => {
    fs.writeFileSync(path.join(dir, "a.out"), body);
    fs.writeFileSync(path.join(dir, "MANIFEST.sha256"), mfLines.join("\n") + "\n");
    if (extra) fs.writeFileSync(path.join(dir, "stray.out"), "x\n");
    else if (fs.existsSync(path.join(dir, "stray.out"))) fs.unlinkSync(path.join(dir, "stray.out"));
  };
  const cases = [
    ["新鲜 -> 0 条",             () => mk([sha(body) + "  a.out"]),                    0],
    ["改过一个字节 -> 1 条",      () => mk([sha(Buffer.from("one linf\n")) + "  a.out"]), 1],
    ["多一个没登记的档案 -> 1 条", () => mk([sha(body) + "  a.out"], true),              1],
    ["清单本身读不出条目 -> 1 条", () => mk(["garbage not a manifest"]),                 1],
  ];
  let fails = 0;
  for (const [name, setup, want] of cases) {
    setup();
    const got = staleManifests(root).length;
    const ok = got === want;
    if (!ok) fails++;
    console.log(`  ${ok ? "OK  " : "FAIL"} ${name} -> ${got} 条（期望 ${want}）`);
  }
  fs.rmSync(root, { recursive: true, force: true });
  console.log(fails ? "SELFTEST FAIL" : "SELFTEST PASS (staleManifests 4/4)");
  process.exit(fails ? 1 : 0);
}

if (require.main === module && process.argv.includes("--selftest")) selftestStaleManifests();

/** 逃生口的落点：必须在 evidence/ 之外——那下面每个目录都被 MANIFEST.sha256 锁着，
 *  一个"每次绕过追加一行"的日志放进锁里，等于让逃生口自己制造下一条违规。 */
function recordOverride(root, tag, problemsText) {
  const log = path.join(root, "tools", "hooks", "GATE-OVERRIDES.log");
  fs.mkdirSync(path.dirname(log), { recursive: true });
  fs.appendFileSync(log, `${new Date().toISOString()} ${tag}\n  `
    + String(problemsText).replace(/\n/g, "\n  ") + "\n");
  return log;
}

module.exports = { git, norm, inProject, readEvent, eventText, staleManifests,
                   recordOverride };
