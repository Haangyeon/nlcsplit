#!/usr/bin/env node
/*
 route_decisions_to_referee.js -- PreToolUse(AskUserQuestion)

 The user's rule: judgment/review/scope decisions go to the referee MCP, not to
 the user. Only facts or permissions that the referee cannot supply may still be
 asked directly: credentials, money, destructive/irreversible actions, and
 author metadata such as ORCID/e-mail.

 The hook cannot call MCP itself. It blocks the question and tells the agent
 which tool to call instead, so the decision path stays visible in the transcript.
*/
"use strict";

const ALLOW = [
  /credential|password|passcode|token|\bpat\b|2fa|api[_ -]?key|secret/i,
  /payment|price|cost|budget|spend|purchase|subscribe/i,
  /submit|submission|push|publish|delete|overwrite|destroy|reset|force[- ]?push|irreversible|authori[sz]/i,
  /orcid|affiliation|e-?mail|author metadata|funding|grant|acknowledg/i,
];

function classify(text) {
  const s = String(text || "");
  return ALLOW.some((re) => re.test(s)) ? "allow" : "block";
}

function eventText(ev) {
  const ti = (ev && ev.tool_input) || {};
  return [ti.question, ti.header, ti.prompt,
    JSON.stringify(ti.questions || ""), JSON.stringify(ti.options || "")]
    .filter((x) => typeof x === "string").join("\n");
}

function selftest() {
  const cases = [
    ["Which partition is the correct one?", "block"],
    ["Should we keep or drop the four Hirshfeld cells?", "block"],
    ["Which figure layout is better?", "block"],
    ["Please provide the co-author ORCID and e-mail.", "allow"],
    ["Do you authorize submission to the journal?", "allow"],
    ["Enter the API key for the detector.", "allow"],
    ["May I delete the old PDF?", "allow"],
    ["Should I spend money on the paid API?", "allow"],
  ];
  let fails = 0;
  for (const [text, want] of cases) {
    const got = classify(text);
    const ok = got === want;
    console.log(`  ${ok ? "OK  " : "FAIL"} ${want.padEnd(5)} ${text}`);
    if (!ok) fails++;
  }
  console.log(fails ? `SELFTEST FAIL (${fails}/${cases.length})` : `SELFTEST PASS (${cases.length}/${cases.length})`);
  process.exit(fails ? 1 : 0);
}

if (process.argv.includes("--selftest")) selftest();

let raw = "";
process.stdin.on("data", (d) => (raw += d));
process.stdin.on("end", () => {
  let ev = {};
  try { ev = JSON.parse(raw || "{}"); } catch (e) { process.exit(0); }
  const name = ev.tool_name || ev.toolName || ev.name || "";
  if (!/askuserquestion/i.test(name)) process.exit(0);
  const text = eventText(ev);
  if (classify(text) === "allow") process.exit(0);
  process.stderr.write(
    "route-decisions-to-referee: 这是判断/评审/取舍问题，不要问用户。\n"
    + "调用 mcp__referee__referee，把 task / proposal / question / evidence 填全；"
    + "只有凭据、花钱、投稿/删除等不可逆授权，或 ORCID/邮箱等作者元数据，才允许直接问用户。\n");
  process.exit(2);
});
