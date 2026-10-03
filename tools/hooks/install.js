#!/usr/bin/env node
/*
 install.js -- 钩子注册的装机件与"注册还在不在"的检查件。

 为什么要有这个文件：`.qoder/` 被 .gitignore 忽略，所以**注册本身不在版本库里**——
 换一台机器、换一个 Qoder 客户端（本仓另有国际版那份）、或者谁清掉本地设置，
 那五个闸门就全部静默失效，而仓库里的 tools/hooks/*.js 照样躺着、看着像有防线。
 本仓记过一次同类事故："别把写了脚本当闸门在跑"。

 所以注册以 tools/hooks/settings.fragment.json 的形式入库，这里两条命令：
   node tools/hooks/install.js --check   # 只回答"当前注册 == 入库那份吗"，不写任何东西
   node tools/hooks/install.js           # 装（已存在且不同则拒绝，除非 --force）
 --check 的退出码非零即失败，可以直接被别的钩子或 CI 叫。
*/
"use strict";
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..", "..");
const fragPath = path.join(__dirname, "settings.fragment.json");
const target = path.join(root, ".qoder", "settings.json");

function canon(v) {
  if (Array.isArray(v)) return "[" + v.map(canon).join(",") + "]";
  if (v && typeof v === "object")
    return "{" + Object.keys(v).sort().map((k) => JSON.stringify(k) + ":" + canon(v[k])).join(",") + "}";
  return JSON.stringify(v);
}
const stable = (v) => canon(v);

function read(p) { try { return JSON.parse(fs.readFileSync(p, "utf8")); } catch (e) { return null; } }

function diffKeys(a, b) {
  const ka = Object.keys(a || {}), kb = Object.keys(b || {});
  const missing = ka.filter((k) => !kb.includes(k));
  const extra = kb.filter((k) => !ka.includes(k));
  const changed = ka.filter((k) => kb.includes(k) && stable(a[k]) !== stable(b[k]));
  return { missing, extra, changed };
}

const frag = read(fragPath);
if (!frag || !frag.hooks) { console.log("FAIL 读不出 " + path.basename(fragPath)); process.exit(1); }
const have = read(target);

if (process.argv.includes("--selftest")) {
  // 比较器本身必须双向：一致要能判一致，掉一个事件/改一条命令必须判出来。
  const nb = (d) => d.missing.length + d.extra.length + d.changed.length;
  const A = { Stop: [{ hooks: [{ command: "node x.js", name: "a" }] }] };
  const cases = [
    ["相同 -> 无差", diffKeys(A, JSON.parse(JSON.stringify(A))), 0],
    ["少一个事件 -> 有差", diffKeys(A, {}), 1],
    ["命令被改 -> 有差", diffKeys(A, { Stop: [{ hooks: [{ command: "node other.js", name: "a" }] }] }), 1],
    ["只是键顺序不同 -> 无差", diffKeys(A, { Stop: [{ hooks: [{ name: "a", command: "node x.js" }] }] }), 0],
  ];
  let f = 0;
  for (const [n, d, wantNonZero] of cases) {
    const got = nb(d);
    const ok = wantNonZero ? got > 0 : got === 0;
    if (!ok) f++;
    console.log(`  ${ok ? "OK  " : "FAIL"} ${n} -> 差 ${got} 处 ${JSON.stringify(d)}`);
  }
  // 真注册必须 == 入库 fragment；不一致说明这台机器上的闸门和我以为的不是同一套。
  const live = diffKeys(frag.hooks, (have || {}).hooks);
  const liveOK = !!have && nb(live) === 0;
  console.log(`  ${liveOK ? "OK  " : "FAIL"} 本机注册与 fragment 一致 -> 差 ${nb(live)} 处`);
  if (!liveOK) console.log("      " + JSON.stringify(live));
  process.exit(f || !liveOK ? 1 : 0);
}

if (process.argv.includes("--check")) {
  if (!have) { console.log("FAIL .qoder/settings.json 不存在——五个闸门当前一个都没在跑"); process.exit(1); }
  const d = diffKeys(frag.hooks, have.hooks);
  if (!d.missing.length && !d.extra.length && !d.changed.length) {
    console.log("OK 注册与入库的 fragment 一致（" + Object.keys(frag.hooks).join(", ") + "）");
    process.exit(0);
  }
  console.log("FAIL 注册与 fragment 不一致："
    + (d.missing.length ? " 缺事件[" + d.missing.join(",") + "]" : "")
    + (d.extra.length ? " 多出[" + d.extra.join(",") + "]" : "")
    + (d.changed.length ? " 内容有差[" + d.changed.join(",") + "]" : ""));
  process.exit(1);
}

const force = process.argv.includes("--force");
if (have) {
  const d = diffKeys(frag.hooks, have.hooks);
  const clean = !d.missing.length && !d.extra.length && !d.changed.length;
  if (clean) { console.log("已是最新，未改动 " + path.relative(root, target)); process.exit(0); }
  if (!force) {
    console.log("目标已存在且不同（先跑 --check 看差在哪；确认要覆盖再加 --force）：\n  "
      + JSON.stringify(d));
    process.exit(1);
  }
  const merged = Object.assign({}, have, { hooks: Object.assign({}, have.hooks, frag.hooks) });
  fs.writeFileSync(target, JSON.stringify(merged, null, 2) + "\n");
} else {
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, JSON.stringify({ hooks: frag.hooks }, null, 2) + "\n");
}

// 写完立刻回读比对：装不上或装歪了要当场说，不能报"成功"。
const back = read(target);
const ok = back && !Object.values(diffKeys(frag.hooks, back.hooks)).some((x) => x.length);
console.log((ok ? "OK 已安装并回读一致: " : "FAIL 装完回读不一致: ") + path.relative(root, target));
process.exit(ok ? 0 : 1);
