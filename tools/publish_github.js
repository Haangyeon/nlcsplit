/* 把**导出树**推到 GitHub。默认只做 dry-run，真推需要显式 --push 与环境变量 NLCSPLIT_GH_TOKEN。
 *
 * 为什么要有这个脚本（2026-09-30）：母仓里带着集群内网 IP、SSH 端口、账号串、未发表稿和
 * 两份 agent 的协调流水；"把仓库设成公开"一旦手滑推的是母仓，这些就永久进公共历史。
 * 所以发布对象只有一个：**tools/make_public_repo.js 吐出来的那一棵树**，
 * 而本脚本拒绝接受任何别的东西（靠导出戳 `.exported-by-make_public_repo` 认）。
 *
 * 凭据纪律：token 只从环境变量读，不落盘、不写进 git remote URL（那会留在 .git/config 与
 * reflog 里）。推送用一次性 header 传，仓库建好即失效的 fine-grained PAT 是唯一建议形态。
 *
 * 用法：
 *   node tools/publish_github.js                       # dry-run：只看它会做什么
 *   NLCSPLIT_GH_TOKEN=...            node tools/publish_github.js --push --owner <login>
 *   NLCSPLIT_GH_TOKEN_FILE=.publish/gh_token.tmp  同上（值不进 shell 历史 / 不进对话记录）
 */
const fs = require('fs');
const path = require('path');
const cp = require('child_process');

const argv = process.argv.slice(2);
const flag = n => argv.includes('--' + n);
const opt = (n, d) => { const i = argv.indexOf('--' + n); return i >= 0 && argv[i + 1] ? argv[i + 1] : d; };

const SRC = process.cwd();
const DIST = path.join(SRC, 'dist', 'nlcsplit');
const BUNDLE = path.join(SRC, '.publish', 'nlcsplit');
const STAMP = '.exported-by-make_public_repo';
const OWNER = opt('owner', '');
const REPO = opt('repo', 'nlcsplit');
const VIS = opt('visibility', 'private');
// token 从环境变量读；也接受 NLCSPLIT_GH_TOKEN_FILE（值放文件里，避免抄进长期保存的会话记录）。
// 两条路都不写进 git remote URL：那会在 .git/config 与 reflog 里留下长期可用的凭据。
const TOKEN_FILE = process.env.NLCSPLIT_GH_TOKEN_FILE || '';
const TOKEN = process.env.NLCSPLIT_GH_TOKEN || (TOKEN_FILE && fs.existsSync(TOKEN_FILE)
  ? fs.readFileSync(TOKEN_FILE, 'utf8').trim() : '');
const DO_PUSH = flag('push');

const die = m => { console.error('中止：' + m); process.exit(1); };

// ---- 1. 发布对象只有一个：闸门刚吐出来的那棵树 ----------------------------
// 每次都从 dist/nlcsplit 重新复制，不复用上一次的 .publish —— 避免"审的是 A、发的是 B"。
if (!fs.existsSync(path.join(DIST, STAMP))) {
  die(`${DIST} 不是导出树（缺 ${STAMP}）。先跑 node tools/make_public_repo.js。`
    + ` 注意**不要**把母仓当发布物：里面有集群内网 IP、端口、账号串与未发表稿。`);
}
if (!flag('no-resync')) {
  cp.execFileSync('git', ['-C', SRC, 'rev-parse', '--verify', 'HEAD'], { stdio: 'ignore' });
  fs.rmSync(BUNDLE, { recursive: true, force: true });
  fs.mkdirSync(path.dirname(BUNDLE), { recursive: true });
  fs.cpSync(DIST, BUNDLE, { recursive: true });
}
const walk = (d, base) => fs.readdirSync(d, { withFileTypes: true })
  .flatMap(e => e.isDirectory() ? walk(path.join(d, e.name), base ? base + '/' + e.name : e.name)
    : [base ? base + '/' + e.name : e.name]);
const files = walk(BUNDLE, '');
if (files.includes('PROGRESS-nlcsplit.md') || files.some(f => /^nlcsplit\/centos_run/.test(f))
  || files.includes('tools/intranet_patterns.private.js')) {
  die('这棵树里出现了母仓专有的文件，拒绝发布。');
}

// ---- 2. 发布前自己扫一遍：与闸门 B 同一批判据 ------------------------------
// 判据从母仓的 private 模块读；读不到就退回形状类那几条，并在输出里说明少了哪些。
const PRIV_PATH = path.join(SRC, 'tools', 'intranet_patterns.private.js');
const PRIV = fs.existsSync(PRIV_PATH) ? require(PRIV_PATH) : null;
const EMAIL = /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g;
const ATTR = ['CITATION.cff', 'pyproject.toml', 'README.md', 'CONTRIBUTING.md', 'LICENSE'];
const rules = PRIV ? PRIV.SECRET_PATS : [];
// 豁免语义必须与闸门 B **同一份**：这里是第二套实现，若只复制判据不复制豁免，
// 结果就是两处对"能不能发"给出不同答案，而严的那一处只会把发布挡在墙上。
// 通道 1：检测器自身的判据定义行（文件在名单里 且 该行含该判据的字面量）。
// 通道 2：署名文件里作者本人的机构邮箱（把地址挖掉后该行不再有别的命中）。
const SELF_DETECT = ['tools/make_public_repo.js', 'tools/audit_no_gamess.js'];
const leaks = [];
const exempted = [];
for (const rel of files) {
  if (/\.(pyc|whl|tar|gz|png|pdf)$/i.test(rel)) continue;
  let t; try { t = fs.readFileSync(path.join(BUNDLE, rel), 'utf8'); } catch (e) { continue; }
  t.split(/\r?\n/).forEach((line, i) => {
    const hit = rules.filter(([, re]) => re.test(line));
    if (!hit.length) return;
    if (SELF_DETECT.includes(rel) && hit.every(([, re]) => line.includes(re.source))) {
      exempted.push(`${rel}:${i + 1} 检测器自身的判据定义（具名豁免，与闸门 B 同一条规则）`);
      return;
    }
    const rest = line.replace(EMAIL, ' ');
    const stillDirty = rules.some(([, re]) => re.test(rest));
    if (ATTR.includes(rel) && !stillDirty && EMAIL.test(line)) {
      exempted.push(`${rel}:${i + 1} 作者通讯地址（具名豁免）`);
    } else leaks.push(`${rel}:${i + 1}  <- ${hit.map(([n]) => n).join('、')} | ${line.trim().slice(0, 110)}`);
  });
}

console.log(`发布对象：${BUNDLE}（导出树，${files.length} 个文件）`);
console.log(`判据来源：${PRIV ? 'private 模块，' + rules.length + ' 条点名判据' : '缺 private 模块，只跑形状类——这条要写明'}`);
console.log(`具名豁免 ${exempted.length} 条：`); exempted.forEach(x => console.log('   ' + x));
if (leaks.length) { console.log('泄漏：'); leaks.forEach(x => console.log('   ' + x)); }
console.log(`目标：https://github.com/${OWNER || '<owner>'}/${REPO}  可见性=${VIS}`);
if (leaks.length) die('上面这些串会进公共历史，先处理再发。');

if (!DO_PUSH) {
  console.log('\ndry-run 结束（没有联网、没有写凭据）。真要发：加 --push，并先 '
    + '`git remote -v` 确认本仓当前**没有** remote。');
  process.exit(0);
}

// ---- 3. 真推送 -----------------------------------------------------------
if (!TOKEN) die('--push 需要环境变量 NLCSPLIT_GH_TOKEN（建议：fine-grained PAT，只给这一个仓、会过期）。');
if (!OWNER) die('--push 需要 --owner <你的 login>。');
if (!/^[A-Za-z0-9._-]+$/.test(REPO)) die('仓库名不合法。');
if (!['private', 'public'].includes(VIS)) die('visibility 只能是 private 或 public。');

const gh = (method, url, body) => {
  const args = ['-sS', '-X', method, url, '-H', 'Authorization: Bearer ' + TOKEN,
    '-H', 'Accept: application/vnd.github+json', '-H', 'X-GitHub-Api-Version: 2022-11-28'];
  if (body) args.push('-H', 'Content-Type: application/json', '-d', JSON.stringify(body));
  const out = cp.execFileSync('curl', args, { encoding: 'utf8' });
  return JSON.parse(out || '{}');
};

const created = gh('POST', 'https://api.github.com/user/repos', {
  name: REPO, private: VIS === 'private', description: 'nlcsplit — fragment and pair resolution of the VV10 nonlocal-correlation energy (PySCF)',
  has_issues: true, has_wiki: false, has_discussions: false, auto_init: false,
});
if (!created.full_name) die('建仓失败：' + JSON.stringify(created).slice(0, 300));
console.log('已建仓库：', created.full_name, created.private ? '(private)' : '(PUBLIC)');

const url = `https://github.com/${created.full_name}.git`;
const run = (...a) => cp.execFileSync('git', a, { cwd: BUNDLE, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
try { fs.rmSync(path.join(BUNDLE, '.git'), { recursive: true, force: true }); } catch (e) {}
run('init', '-b', 'main');
run('add', '-A');
run('-c', 'user.name=Angran Xia', '-c', 'user.email=haangyeon@snnu.edu.cn',
  'commit', '-m', 'nlcsplit 0.1.0 — exported release tree, produced by tools/make_public_repo.js');
// token 不进 remote URL：那只会在 .git/config 与 reflog 里留下长期可用的凭据。
run('remote', 'add', 'origin', url);
cp.execFileSync('git', ['-C', BUNDLE, '-c', 'credential.helper=',
  '-c', `http.extraHeader=Authorization: Bearer ${TOKEN}`,
  'push', '-u', 'origin', 'main'], { stdio: ['ignore', 'inherit', 'inherit'] });

// ---- 4. 推完之后按哈希核对：公开的确实就是我审过的那棵树 -------------------
const head = run('rev-parse', 'HEAD').trim();
const local = new Set(run('ls-tree', '-r', '--format=%(objectname) %(path)', head)
  .split(/\r?\n/).filter(Boolean).map(l => l.trim()));
const api = gh('GET', `https://api.github.com/repos/${created.full_name}/git/trees/${head}?recursive=1`);
if (api.truncated) die('远端树被 API 截断，未能完整核对。');
const remote = new Set((api.tree || []).map(t => `${t.sha} ${t.path}`));
const onlyLocal = [...local].filter(x => !remote.has(x));
const onlyRemote = [...remote].filter(x => !local.has(x));
console.log(`核对：本地 ${local.size} 个 blob，远端 ${remote.size} 个；`
  + `仅本地 ${onlyLocal.length}，仅远端 ${onlyRemote.length}`);
[...onlyLocal, ...onlyRemote].slice(0, 10).forEach(x => console.log('   差异', x));
if (onlyLocal.length || onlyRemote.length) die('远端与导出树不一致 —— 别把这个链接发出去。');
console.log('一致。发布完成：' + created.html_url);
