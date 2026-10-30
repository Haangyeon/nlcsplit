// 反向核验三条候选引文的 Crossref 元数据；WoS 只算一个来源，不落第二条来源不写 bib。
// 输出 scratch/bib_new3.json，并把不一致之处打到 stdout。
const fs = require('fs');

const WANT = {
  '10.1103/PhysRevLett.103.063004': { key: 'vydrov2009vv10', year: '2009' },
  '10.1063/1.3521275':              { key: 'vydrov2010simple', year: '2010' },
  '10.1103/PhysRevB.90.075148':     { key: 'hyldgaard2014interp', year: '2014' },
};

const get = (doi) => fetch('https://api.crossref.org/works/' + encodeURIComponent(doi), {
  headers: { 'User-Agent': 'nlcsplit-bib-check/1.0 (mailto:unknown@example.invalid)' },
}).then(r => r.status === 404 ? null : r.json().then(j => ({ status: r.status, m: j.message })));

(async () => {
  const out = {};
  for (const [doi, meta] of Object.entries(WANT)) {
    let v = null;
    for (let attempt = 0; attempt < 3; attempt++) {
      try { v = await get(doi); break; }
      catch (e) { await new Promise(r => setTimeout(r, 1500 * (attempt + 1))); }
    }
    if (!v) { out[doi] = { fail: 'fetch failed after 3 attempts' }; continue; }
    const m = v.m || {};
    const authors = (m.author || []).map(a => [a.given, a.family].filter(Boolean).join(' '));
    out[doi] = {
      key: meta.key,
      title: (m.title || [''])[0],
      journal: (m['container-title'] || [''])[0],
      volume: m.volume || null,
      issue: m.issue || null,
      page: m.page || m['article-number'] || null,
      year_published: (m.issued && m.issued['date-parts'] && m.issued['date-parts'][0][0]) || null,
      year_print: (m.published && m.published['date-parts'] && m.published['date-parts'][0][0]) || null,
      authors,
      expected_year: meta.year,
      year_agrees: String((m.issued && m.issued['date-parts'] && m.issued['date-parts'][0][0]) || '') === meta.year,
    };
  }
  fs.writeFileSync('scratch/bib_new3.json', JSON.stringify(out, null, 1));
  // 只有三条都拿到才退 0；任何一条缺失就非零，避免上游拿空结果去覆写 bib
  const ok = Object.values(out).every(o => o.title && o.journal);
  console.log(JSON.stringify(out, null, 1));
  process.exit(ok ? 0 : 2);
})();
