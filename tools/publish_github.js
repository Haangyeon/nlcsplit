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
const os = require('os');
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
// 事后复核用：只读远端，一个字也不写。推过一次之后再跑，不该再造第二条历史。
const VERIFY_ONLY = flag('verify-only');

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

if (!DO_PUSH && !VERIFY_ONLY) {
  console.log('\ndry-run 结束（没有联网、没有写凭据）。真要发：加 --push，并先 '
    + '`git remote -v` 确认本仓当前**没有** remote。');
  process.exit(0);
}

// ---- 3. 真推送 -----------------------------------------------------------
if (!TOKEN) die('--push 需要环境变量 NLCSPLIT_GH_TOKEN（建议：fine-grained PAT，只给这一个仓、会过期）。');
if (!OWNER) die('--push 需要 --owner <你的 login>。');
if (!/^[A-Za-z0-9._-]+$/.test(REPO)) die('仓库名不合法。');
if (!['private', 'public'].includes(VIS)) die('visibility 只能是 private 或 public。');

// body 必须走文件：Windows 上 execFileSync 把带引号的 JSON 当参数递给 curl.exe 时，
// 双引号会被 argv 解析吃掉，GitHub 回 "Problems parsing JSON"——一个纯粹的传输层假错。
const gh = (method, url, body) => {
  const args = ['-sS', '--max-time', '120', '-X', method, url, '-H', 'Authorization: Bearer ' + TOKEN,
    '-H', 'Accept: application/vnd.github+json', '-H', 'X-GitHub-Api-Version: 2022-11-28'];
  let tmp = null;
  if (body) {
    tmp = path.join(os.tmpdir(), `nlcsplit-gh-body-${process.pid}.json`);
    fs.writeFileSync(tmp, JSON.stringify(body));
    args.push('-H', 'Content-Type: application/json', '-d', '@' + tmp);
  }
  try {
    const out = cp.execFileSync('curl', args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
    return JSON.parse(out || '{}');
  } catch (e) {
    // 不能把 node 的原始异常抛出去：它会连同 stdout 一起回显，一次成功的 dump 就能
    // 把整棵树的正文灌进日志。只留状态与截断后的头部。
    die(`GitHub 调用失败 ${method} ${url}\n   ${(e.message || '').split('\n')[0].slice(0, 160)}`
      + `\n   ${(e.stdout || '').slice(0, 200)}`);
  } finally {
    if (tmp) fs.rmSync(tmp, { force: true });
  }
};

// 建仓前先查：已存在就复用（并把可见性核对清楚），否则一次 POST 建一个。
// "建仓失败：409 already exists" 是最难查的假失败——仓库其实是对的。
let repo = gh('GET', `https://api.github.com/repos/${OWNER}/${REPO}`);
if (repo.full_name) {
  if (repo.visibility !== VIS) {
    die(`已存在的仓库 ${repo.full_name} 可见性是 ${repo.visibility}，与 --visibility ${VIS} 不符。`
      + '不擅自改可见性——这一步由你在 GitHub 上决定。');
  }
  if (repo.size > 0) die(`${repo.full_name} 已有内容（size=${repo.size} KiB）。不往非空仓库里推。`);
  console.log('复用已存在的仓库：', repo.full_name, repo.private ? '(private)' : '(PUBLIC)');
} else {
  repo = gh('POST', 'https://api.github.com/user/repos', {
    name: REPO, private: VIS === 'private', description: 'nlcsplit — fragment and pair resolution of the VV10 nonlocal-correlation energy (PySCF)',
    has_issues: true, has_wiki: false, has_discussions: false, auto_init: false,
  });
  if (!repo.full_name) die('建仓失败：' + JSON.stringify(repo).slice(0, 300));
  console.log('已建仓库：', repo.full_name, repo.private ? '(private)' : '(PUBLIC)');
}
const FULL = repo.full_name;

if (VERIFY_ONLY) {
  console.log('--verify-only：不建仓、不提交、不推送，只做第 4 步的逐 blob 哈希核对。');
} else {
const url = `https://github.com/${FULL}.git`;
const run = (...a) => cp.execFileSync('git', a, { cwd: BUNDLE, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] });
try { fs.rmSync(path.join(BUNDLE, '.git'), { recursive: true, force: true }); } catch (e) {}
run('init', '-b', 'main');
run('add', '-A');
run('-c', 'user.name=Angran Xia', '-c', 'user.email=haangyeon@snnu.edu.cn',
  'commit', '-m', 'nlcsplit 0.1.0 — exported release tree, produced by tools/make_public_repo.js');
// token 不进 remote URL：那只会在 .git/config 与 reflog 里留下长期可用的凭据。
// 也不用 `-c http.extraHeader=Authorization: Bearer …`：2026-09-30 实测吃 401，
// git 随即去 /dev/tty 要用户名（本沙箱没有 tty，直接 fatal）。GitHub 的 git-over-HTTPS
// 端点认的是 Basic——PAT 放密码位；Bearer 只有 REST 收。
// 另外，值走环境变量 + --config-env：因为 node 在子进程非零退出时会把**整条命令行**
// 印进异常里，上一轮就是靠这条路把 token 泄进了会话记录。参数里没有敏感字节，就印不出来。
run('remote', 'add', 'origin', url);
const basic = 'Authorization: Basic ' + Buffer.from('x-access-token:' + TOKEN).toString('base64');
try {
  cp.execFileSync('git', ['-C', BUNDLE, '-c', 'credential.helper=',
    '--config-env=http.extraHeader=NLCSPLIT_GH_AUTH', 'push', '-u', 'origin', 'main'],
  { stdio: ['ignore', 'inherit', 'inherit'], env: Object.assign({}, process.env, { NLCSPLIT_GH_AUTH: basic }) });
} catch (e) {
  // git 失败时 node 会把整条命令回显进错误里——这里必须自己吞掉，否则凭据进日志。
  die('推送失败（git 自己的输出已回显在上面；本脚本刻意不复述命令行，以免凭据进日志）。\n'
    + '  · refusing to allow a Personal Access Token to create or update workflow …\n'
    + '    → 树里有 .github/workflows/*，classic PAT 必须有 workflow 档\n'
    + '      （或 fine-grained token 勾上 Contents + Workflows 读写）。\n'
    + '  · could not read Username → token 不被接受或已失效。\n'
    + '  · [rejected] non-fast-forward → 远端 main 已经有东西了；先看清那是什么，\n'
    + '    本脚本绝不 force 覆盖别人的历史。');
}
}

// ---- 4. 推完之后按哈希核对：公开的确实就是我审过的那棵树 -------------------
// 比对基准是**导出树里的字节**（git hash-object），不是刚建的那个本地 commit：
// 这样 --verify-only 可以在事后、甚至换一个会话里再跑一次，而且重跑不会像
// "重新 init+commit" 那样造出一个与远端无共同祖先的第二条历史。
// 另注：?recursive=1 返回的是 blob + 中间目录 tree 两种条目（2026-09-30 实测：
// 121 个文件对 144 条，差的 23 条正是目录）。只比 blob，并把目录条数印出来——
// 否则这个闸门会因为自己的类型过滤缺失而谎报"远端多了 23 个文件"。
// /commits/main 会把每个文件的整段 patch 都带回来（实测 >1 MB，一次失败就把
// 整棵树灌进日志）；只要 SHA 就用最瘦的 ref 端点。
const ref = gh('GET', `https://api.github.com/repos/${FULL}/git/ref/heads/main`);
const head = (ref.object || {}).sha;
if (!head) die('读不到远端 main：' + JSON.stringify(ref).slice(0, 200));
const shas = cp.execFileSync('git', ['hash-object', '--stdin-paths'],
  { encoding: 'utf8', input: files.map(f => path.join(BUNDLE, f)).join('\n') })
  .split(/\r?\n/).filter(Boolean);
const local = new Set(files.map((f, i) => `${shas[i]} ${f}`));
const api = gh('GET', `https://api.github.com/repos/${FULL}/git/trees/${head}?recursive=1`);
if (api.truncated) die('远端树被 API 截断，未能完整核对。');
const all = api.tree || [];
const remote = new Set(all.filter(t => t.type === 'blob').map(t => `${t.sha} ${t.path}`));
console.log(`远端 main = ${head}`);
console.log(`核对：本地导出树 ${local.size} 个 blob，远端 ${remote.size} 个 blob`
  + `（API 另有 ${all.length - remote.size} 条目录项）`);
const onlyLocal = [...local].filter(x => !remote.has(x));
const onlyRemote = [...remote].filter(x => !local.has(x));
console.log(`仅本地 ${onlyLocal.length}，仅远端 ${onlyRemote.length}`);
[...onlyLocal, ...onlyRemote].slice(0, 10).forEach(x => console.log('   差异', x));
if (onlyLocal.length || onlyRemote.length) die('远端与导出树不一致 —— 别把这个链接发出去。');
console.log('一致。发布完成：' + repo.html_url);
