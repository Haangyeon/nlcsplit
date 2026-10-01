// 用 token 读 Actions 运行状态。grep 拆 JSON 会在带引号的值上静默取空——
// 这次就是它把 name/status/conclusion 打成空白，害我差点以为 workflow 没名字。
const fs = require('fs');
const TOKEN = fs.readFileSync(process.env.NLCSPLIT_GH_TOKEN_FILE, 'utf8').trim();
const get = async (p) => {
  const r = await fetch('https://api.github.com' + p, {
    headers: { Authorization: 'Bearer ' + TOKEN, Accept: 'application/vnd.github+json' },
  });
  return { status: r.status, body: await r.json() };
};
(async () => {
  const runs = await get('/repos/Haangyeon/nlcsplit/actions/runs?per_page=10');
  console.log('http=' + runs.status + ' total_count=' + (runs.body.total_count ?? 'ERR'));
  for (const r of runs.body.workflow_runs || []) {
    console.log(`run #${r.run_number}  event=${r.event}  status=${r.status}  conclusion=${r.conclusion}`
      + `\n   name="${r.name}"  sha=${(r.head_sha || '').slice(0, 7)}  branch=${r.head_branch}`
      + `\n   url=${r.html_url}`);
  }
  const wf = await get('/repos/Haangyeon/nlcsplit/actions/workflows');
  for (const w of wf.workflows || []) {
    console.log(`workflow "${w.name}"  state=${w.state}  id=${w.id}  path=${w.path}`);
  }
  const repo = await get('/repos/Haangyeon/nlcsplit');
  console.log(`repo: visibility=${repo.body.visibility} private=${repo.body.private}`
    + ` default_branch=${repo.body.default_branch} size=${repo.body.size}KiB`);
})();
