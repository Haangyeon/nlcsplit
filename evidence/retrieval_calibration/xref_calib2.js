/* 用"当场回查过的对照"重做 Crossref 校准。
 *
 * 上一版的失败原因不是判据松紧，而是**期望值本身凭记忆填**：
 *   - "…for General Use" 根本不存在（真名 "…for General Geometries"，我把命中判成伪命中）
 *   - 10.1103/PhysRevB.69.235111 与 .70.235111 回查后是另外两篇（GdSi / 强关联）
 * ⇒ 这次先用 DOI→题名 精确回查钉住三条对照，再用**同一题名**去喂 query.bibliographic，
 *   看真 DOI 能不能回来。判据：三条里每条的期望 DOI 出现在 top-5 即算召回。
 */
const fs = require("fs");
const OUT = "<REPO>/scratch/xref_calib2.json";
const UA = { headers: { "User-Agent": "nlcsplit-refcheck/0.1" } };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const ANCHOR = [
  { id: "A1", doi: "10.1103/PhysRevLett.92.246401" },
  { id: "A2", doi: "10.1063/1.454033" },
  { id: "A3", doi: "10.1039/c3cp54374a" },
  { id: "A4", doi: "10.1016/0009-2614(96)00600-8" },
];

async function meta(doi) {
  const r = await fetch("https://api.crossref.org/works/" + encodeURIComponent(doi), UA);
  if (!r.ok) throw new Error(`DOI 回查失败 ${doi}: HTTP ${r.status}`);
  const j = (await r.json()).message;
  return { doi, title: (j.title || [""])[0].replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim(),
           year: j.issued?.["date-parts"]?.[0]?.[0] };
}
async function search(t) {
  const r = await fetch("https://api.crossref.org/works?rows=5&query.bibliographic="
    + encodeURIComponent(t), UA);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return ((await r.json()).message.items || []).map((it) => String(it.DOI).toLowerCase());
}

(async () => {
  const out = { started: new Date().toISOString(), rows: [] };
  for (const a of ANCHOR) {
    const m = await meta(a.doi);                       // 先钉住"正确答案"
    const got = await search(m.title);                 // 再用它自己的题名去检索
    const rank = got.indexOf(m.doi.toLowerCase());
    const rec = { ...a, ...m, returned: got, rank, recalled: rank >= 0 };
    out.rows.push(rec);
    console.log(`${a.id} ${m.doi}\n    题名: ${m.title.slice(0, 88)}\n` +
                `    用自己的题名检索 → top5 = [${got.map((g) => g.split("/")[0]).join(", ")}]  rank=${rank}  召回=${rec.recalled}`);
    fs.writeFileSync(OUT, JSON.stringify(out, null, 2));
    await sleep(900);
  }
  const n = out.rows.filter((r) => r.recalled).length;
  out.verdict = `${n}/${out.rows.length} 召回`;
  console.log(`\n=== 校准结论：${out.verdict} ===`);
  console.log(n === out.rows.length
    ? "Crossref 精确题名检索可用 → 今早'无效仪器'的判词需重开"
    : "确有漏召 → 其 0 命中不得作为'没有先例'的证据（今早判词成立，但理由要换成这一版）");
  fs.writeFileSync(OUT, JSON.stringify(out, null, 2));
})();
