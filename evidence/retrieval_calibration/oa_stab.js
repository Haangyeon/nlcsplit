/* OpenAlex 主题检索的**稳定性**测试：同一查询重复 4 次，看能否召回已知先例是否抖动。
 * 动机：上一轮三条校准第一次 1/3、第二次 0/3 —— 若同式不同果，
 * 那它的 0/低命中完全不能承载"未见先例"这种否定主张，本项目最后一个文献支柱要降级。
 * 判据：对每条查询报 4 次里的召回次数与 rank。 */
const fs = require("fs");
const OUT = "<REPO>/scratch/openalex_stability.json";
const UA = { headers: { "User-Agent": "nlcsplit-refcheck/0.1 mailto:unspecified" } };
const NEEDLE = "balance between physical interpretability and energetic predictability";
const QS = [
  "physical interpretability energetic predictability dispersion corrected functionals",
  "energy decomposition analysis dispersion nonlocal correlation density functional",
  "ALMO energy decomposition dispersion corrected noncovalent interactions",
];
const REPS = 4;

async function once(q) {
  // 上一版把 HTTP 429 计成"未召回"，导致 1/3 与 0/3 两次自相矛盾。
  // 这里必须重试到拿到成功响应为止，只有成功响应的 rank 才计入召回。
  for (let k = 0; k < 6; k++) {
    const r = await fetch("https://api.openalex.org/works?search=" + encodeURIComponent(q)
      + "&per-page=25&mailto=research@example.invalid", UA);
    if (r.status === 429) { await new Promise((s) => setTimeout(s, 3000 * (k + 1))); continue; }
    if (!r.ok) throw new Error("HTTP " + r.status);
    const j = await r.json();
    const t = (j.results || []).map((x) => String(x.title || "").toLowerCase().replace(/\s+/g, " ").trim());
    return { n: t.length, rank: t.findIndex((x) => x.includes(NEEDLE)), top1: t[0] ? t[0].slice(0, 70) : "", tries: k + 1 };
  }
  throw new Error("429 exhausted");
}

(async () => {
  const out = { started: new Date().toISOString(), reps: REPS, note: "只计成功响应；429 退避重试", rows: [] };
  for (const q of QS) {
    const runs = [];
    for (let k = 0; k < REPS; k++) {
      try { runs.push(await once(q)); } catch (e) { runs.push({ error: e.message }); }
      await new Promise((s) => setTimeout(s, 2500));
    }
    const recalls = runs.filter((r) => r.rank >= 0).length;
    const ranks = runs.map((r) => (r.rank === undefined ? "err" : r.rank)).join(",");
    const tops = new Set(runs.map((r) => r.top1)).size;
    out.rows.push({ q, recalls, ranks, distinctTop1: tops, runs });
    console.log(`召回 ${recalls}/${REPS}  ranks=[${ranks}]  不同 top1 数=${tops}\n    ${q.slice(0, 74)}`);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2));
  }
  const unstable = out.rows.filter((r) => r.recalls > 0 && r.recalls < REPS).length;
  out.verdict = unstable > 0
    ? `有 ${unstable} 条查询同式不同果 ⇒ OpenAlex 检索层不确定，其低命中不可作否定证据`
    : out.rows.every((r) => r.recalls === 0)
      ? "四条全不召回 ⇒ 主题召回为零，其低命中不可作否定证据"
      : "稳定召回";
  console.log("\n=== " + out.verdict + " ===");
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2));
})();
