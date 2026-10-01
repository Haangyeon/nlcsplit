// 归档 GitHub Actions 第一次真跑的观测：原始 JSON 落盘，数字不手抄。
// 存在的理由：本仓库一度写着"no CI run has ever been observed"，而它其实是没查对
// （private 时未认证请求给 404，404 被当成"没有 run"）。这条归档把"查对之后看到什么"
// 逐字段留在盘上，包括那次 failure。
const fs = require('node:fs');
const path = require('node:path');
const TOKEN = fs.readFileSync(process.env.NLCSPLIT_GH_TOKEN_FILE, 'utf8').trim();
const ROOT = 'E:/Project/GAMESS';
const get = async (p) => {
  const r = await fetch('https://api.github.com' + p, {
    headers: { Authorization: 'Bearer ' + TOKEN, Accept: 'application/vnd.github+json' },
  });
  if (!r.ok) throw new Error('HTTP ' + r.status + ' ' + p);
  return r.json();
};

(async () => {
  const ts = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z');
  const out = path.join(ROOT, 'evidence', 'release_qa', ts + '_github_actions_first_runs.out');
  const L = [];
  const say = (s) => { console.log(s); L.push(s); };

  say('== ARCHIVE: GitHub Actions 第一次真跑（Haangyeon/nlcsplit, workflow "tests"）==');
  say('');
  say('为什么有这份归档。paper/software.md 曾经写着 "no CI run has ever been observed"，');
  say('并把"这条 workflow 从没被执行过"当成一条限制报出去。2026-10-01 带凭据一问，');
  say('total_count 已经是 5，而 run #1 双臂 conclusion=failure。之所以昨天看不见：那次用的是');
  say('未认证请求，仓库当时还是 private ⇒ 404，我把 404 读成"没有 run"。所以这里归档的不只是');
  say('"绿了"，也归档那次红：根因是把**出货决定**（node tools/make_public_repo.js）放进了已发布');
  say('仓的 CI，而它 exec 的 tools/audit_share_rule.js 当时不随包发布，闸门 W 的双向自检对脏样例');
  say('和干净样例**都**返回非零（Cannot find module），于是保守拒绝出货、每次 push 判红。');
  say('');
  say('取数方式：GET /repos/Haangyeon/nlcsplit/actions/runs?per_page=20，再逐个 run 取 /jobs。');
  say('每行都是 API 字段的现读现打，没有一个人工誊写的数。');
  say('');

  const runs = await get('/repos/Haangyeon/nlcsplit/actions/runs?per_page=20');
  say('total_count=' + runs.total_count + '  artifact_runs=' + runs.artifacts_count
    + '  (取数时刻 ' + new Date().toISOString() + ')');
  say('');
  for (const r of runs.workflow_runs.slice().reverse()) {
    say('--- run #' + r.run_number + '  id=' + r.id);
    say('    event=' + r.event + '  display_title=' + r.display_title);
    say('    head_sha=' + r.head_sha + '  branch=' + r.head_branch);
    say('    status=' + r.status + '  conclusion=' + String(r.conclusion));
    say('    run_started_at=' + r.run_started_at + '  updated_at=' + r.updated_at);
    say('    url=' + r.html_url);
    const jobs = await get('/repos/Haangyeon/nlcsplit/actions/runs/' + r.id + '/jobs');
    for (const j of jobs.jobs || []) {
      say('    job "' + j.name + '"  status=' + j.status + '  conclusion=' + String(j.conclusion)
        + '  runner=' + (j.runner_name || '-'));
      for (const s of j.steps || []) {
        say('      step ' + String(s.number).padStart(2) + '  ' + s.name
          + '  -> ' + String(s.conclusion));
      }
    }
    say('');
  }
  say('--- 判读');
  const byNum = Object.fromEntries(runs.workflow_runs.map(r => [r.run_number, r]));
  for (const n of Object.keys(byNum).sort((a, b) => a - b)) {
    const r = byNum[n];
    say('run #' + n + '  sha=' + r.head_sha.slice(0, 7) + '  ' + r.status + '/' + String(r.conclusion));
  }
  fs.writeFileSync(out, L.join('\n') + '\n');
  console.log('\nwrote ' + out + '  (' + fs.statSync(out).size + ' bytes)');
})().catch(e => { console.error('FAILED: ' + e.message); process.exit(1); });
