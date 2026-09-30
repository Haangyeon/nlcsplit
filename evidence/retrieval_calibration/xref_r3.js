/* Crossref 主题级召回校准 + 先例检索重跑。
 *
 * 上一版"无效仪器"的判词源于我用记忆填的期望标题，已在本目录 xref_calib2.json
 * 里以 4/4 rank=0 推翻。但**精确题名能召回 ≠ 主题式查询有足够召回**，
 * 所以这里分两层：
 *   第 1 层 主题召回校准：拿一篇确知存在、且与本项目最近邻的论文（JCTC 2023,
 *          10.1021/acs.jctc.3c00903）的语汇组成主题式查询，看它的 DOI 能否回来。
 *          不通过就不许用下面的 0 命中谈"没有先例"。
 *   第 2 层 先例式：七条主题查询，逐条人工判 top 命中与本项目主张是否真重叠。
 */
const fs = require("fs");
const OUT = "<REPO>/scratch/xref_r3.json";
const UA = { headers: { "User-Agent": "nlcsplit-refcheck/0.1" } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const TARGET = "10.1021/acs.jctc.3c00903";

const CALIB = [
  "energy decomposition analysis dispersion nonlocal correlation density functional",
  "ALMO energy decomposition dispersion corrected density functional noncovalent",
  "balance physical interpretability energetic predictability dispersion corrected",
];
const NOVEL = [
  { id: "N1", q: "VV10 nonlocal correlation energy decomposition into atomic pairs" },
  { id: "N2", q: "fragment decomposition of nonlocal van der Waals correlation energy" },
  { id: "N3", q: "pair-wise attribution grid points nonlocal correlation functional" },
  { id: "N4", q: "vdW-DF nonlocal correlation energy decomposition intermolecular" },
  { id: "N5", q: "omegaB97X-V nonlocal correlation term contribution energy decomposition" },
  { id: "N6", q: "real-space partition atomic contribution VV10 correlation energy" },
  { id: "N7", q: "many-body expansion nonlocal correlation energy VV10 dispersion" },
];

async function q(term, rows = 10) {
  const r = await fetch(`https://api.crossref.org/works?rows=${rows}&select=DOI,title,container-title,issued`
    + "&query.bibliographic=" + encodeURIComponent(term), UA);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return ((await r.json()).message.items || []).map((it) => ({
    doi: String(it.DOI).toLowerCase(),
    title: (it.title || [""])[0].replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim().slice(0, 120),
    j: (it["container-title"] || [""])[0], y: it.issued?.["date-parts"]?.[0]?.[0],
  }));
}

(async () => {
  const out = { started: new Date().toISOString(), calib: [], novel: [] };
  let pass = false;
  for (const c of CALIB) {
    let hits = [];
    try { hits = await q(c); } catch (e) { out.calib.push({ q: c, error: e.message }); continue; }
    const rank = hits.findIndex((h) => h.doi === TARGET);
    if (rank >= 0) pass = true;
    out.calib.push({ q: c, rank, top: hits.slice(0, 3).map((h) => h.title) });
    console.log(`CALIB rank=${rank} ${rank >= 0 ? "召回" : "未召回"} :: ${c.slice(0, 62)}`);
    await sleep(800);
  }
  out.calibPass = pass;
  console.log(`\n>>> 主题级校准 ${pass ? "通过" : "未通过 —— 下面的 0 命中不作负证据"}\n`);
  if (!pass) { fs.writeFileSync(OUT, JSON.stringify(out, null, 2)); return; }

  for (const nv of NOVEL) {
    try {
      const hits = await q(nv.q, 8);
      out.novel.push({ ...nv, n: hits.length, hits });
      console.log(`${nv.id} (${hits.length}) ${nv.q}`);
      hits.slice(0, 4).forEach((h) => console.log("      ", `${h.y} ${h.j.slice(0, 22)} | ${h.title.slice(0, 82)}`));
    } catch (e) { out.novel.push({ ...nv, error: e.message }); console.log(`${nv.id} ERR ${e.message}`); }
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2));
    await sleep(800);
  }
  out.finished = new Date().toISOString();
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2));
})();
