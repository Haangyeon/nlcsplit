const fs = require('fs');
const TOKEN = fs.readFileSync(process.env.NLCSPLIT_GH_TOKEN_FILE, 'utf8').trim();
const get = async (p, raw) => {
  const r = await fetch('https://api.github.com' + p, {
    headers: { Authorization: 'Bearer ' + TOKEN, Accept: 'application/vnd.github+json' },
    redirect: 'follow',
  });
  if (raw) return { status: r.status, text: await r.text() };
  return { status: r.status, body: await r.json() };
};
(async () => {
  const runId = process.argv[2];
  const jobs = await get(`/repos/Haangyeon/nlcsplit/actions/runs/${runId}/jobs`);
  for (const j of (jobs.body.jobs || [])) {
    console.log(`job "${j.name}" status=${j.status} conclusion=${j.conclusion}`);
    for (const s of j.steps || []) {
      if (s.conclusion && s.conclusion !== 'success') {
        console.log(`   FAILED STEP: "${s.name}" -> ${s.conclusion}`);
      }
    }
    for (const m of j.check_run?.output?.annotations || []) {
      console.log(`   anno[${m.annotation_level}] ${m.path}:${m.start_line} — ${(m.message || '').slice(0, 400)}`);
    }
    if (j.check_run?.output?.title) console.log(`   output.title = ${j.check_run.output.title}`);
  }
})();
