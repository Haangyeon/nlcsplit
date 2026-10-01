// 远端 main 里的 paper.md 到底是我母仓哪一个版本？直接取 blob SHA 与本地两种形态比。
const cp = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const TOKEN = fs.readFileSync(process.env.NLCSPLIT_GH_TOKEN_FILE, 'utf8').trim();
const ROOT = 'E:/Project/GAMESS';
const rel = 'paper/joss/paper.md';

(async () => {
  const repo = await fetch('https://api.github.com/repos/Haangyeon/nlcsplit/git/trees/main?recursive=1',
    { headers: { Authorization: 'Bearer ' + TOKEN, Accept: 'application/vnd.github+json' } });
  const t = await repo.json();
  const ent = (t.tree || []).find(x => x.path === rel);
  if (!ent) { console.log('远端没有', rel); return; }
  console.log('远端 main =', (await (await fetch('https://api.github.com/repos/Haangyeon/nlcsplit',
    { headers: { Authorization: 'Bearer ' + TOKEN } })).json()).default_branch, ent.sha);
  const sha = (p) => cp.execFileSync('git', ['hash-object', '--no-filters', p],
    { encoding: 'utf8' }).trim();
  const cand = {
    '母仓 paper/joss/paper.md': path.join(ROOT, rel),
    '导出树 dist': path.join(ROOT, 'dist/nlcsplit', rel),
    '发布副本 .publish': path.join(ROOT, '.publish/nlcsplit', rel),
  };
  for (const [k, p] of Object.entries(cand)) {
    const s = fs.existsSync(p) ? sha(p) : '(缺失)';
    console.log(`${s === ent.sha ? 'MATCH  ' : 'differs'}  ${k}  ${s}`);
  }
  console.log('远端该文件 blob =', ent.sha);
  // 远端正文里那三行辩护注释还在不在
  const raw = await fetch(`https://raw.githubusercontent.com/Haangyeon/nlcsplit/main/${rel}`,
    { headers: { 'X-GitHub-Api-Version': '2022-11-28' } }).then(r => r.text());
  console.log('远端含"不是编的" =', raw.includes('不是编的'));
  console.log('远端含 TBD-AUTHOR-2 那行 =', (raw.match(/.*TBD-AUTHOR-2.*/) || ['(无)'])[0]);
})();
