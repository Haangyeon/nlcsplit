/* 机构专有判据 —— **只在母仓存在，不随包发布**（见 make_public_repo.js 的 EXPLICITLY_EXCLUDED）。
 *
 * 为什么要单独一个文件（2026-09-30 的自指问题）：
 * 让读者能自己复核发布卫生，就得把闸门代码放进包里；而闸门 B 的判据本身就是
 * "集群内网 IP / SSH 端口 / 账号名 / 工作目录"。原样公开 = 把这些信息公开，
 * 也就是把检查要抓的东西当成检查的一部分发出去。豁免账打印出来逐条读，54 条全是这类串。
 *
 * 所以判据分两半：
 *   公开那半（留在 make_public_repo.js）：抓**形状**——凭据赋值、私钥块、`ssh … @`，
 *     以及 GAMESS 源码工件名（那是公开知识，不是机构标识）。
 *   本文件：点名本机/本集群的具体串，外加"拿这些串做反证"的毒样本。
 * 公开副本会打印 `note_private_rules_loaded: 0`，母仓那次运行必须 >0 才允许出货，
 * 所以两边都不静默：读者知道自己少了哪几类检查，我这边知道专有判据真的在生效。
 *
 * 表内容与拆分前**逐字节相同**（只搬位置，不改判据）：改了判据就等于改了历史那 110 个
 * 文件的脱敏结果，而 C2 的"数字不变"论证正是建立在它们之上。
 */

// ---- 脱敏表里点名本机的行（顺序要紧：具体的在前）----
const PATH = [
  [/\/root\/gamess_work\/nlcsplit\/s22/gi, '<S22_GEOMETRY_DIR>'],
  [/\/root\/gamess_work\/nlcsplit\/logs/gi, '<REMOTE_LOG_DIR>'],
  [/\/root\/gamess_work\/logs/gi, '<REMOTE_LOG_DIR>'],
  [/\/root\/gamess_work/gi, '<REMOTE_WORKDIR>'],
  [/\/home\/haangyeon\/agent_l2_work\/nlcsplit\/logs/gi, '<REMOTE_LOG_DIR>'],
  [/\/home\/haangyeon/gi, '<CLUSTER_HOME>'],
  [/\/mnt\/[a-z]\/Project\/GAMESS/gi, '<REPO>'],
  [/[a-z]:[\\/]+Project[\\/]+GAMESS/gi, '<REPO>'],
  // 本机代理端点。get_s22.sh 早就单独在抹它，但归档 stdout 里也会原样出现
  // （`$ https_proxy=http://127.0.0.1:7890 python3 -m pip install …`），
  // 那是工作机的网络拓扑，不是实验结果。
  [/\b(?:127\.0\.0\.1|localhost):7890\b/gi, '<your-proxy>'],
];
const ENDPOINT = [
  // 注意 `\b-P` 匹配不上：`-` 不是词字符，空格到 `-` 之间没有词边界（第一版就在这儿失配，
  // 于是 `scp -P 24522` 一路活着进了发布树）。
  [/-P[ \t]+24522\b/g, '-P <SSH_PORT>'],
  [/-p[ \t]+20019\b/g, '-p <SSH_PORT>'],
  [/:(24522|20019)\b/g, ':<SSH_PORT>'],
];
const IDENT = [
  [/\bSNNU\b/gi, '<CLUSTER>'],
  [/\bHaangyeon\b/g, '<OPERATOR>'],
];

// ---- 闸门 B 里点名本机的判据（从 make_public_repo.js 原样搬来，一个字符没改）----
const SECRET_PATS = [
  ['集群内网 IP', /10\.8\.51\.23/],
  ['本机代理端口/回环端点', /:7890\b/],
  ['远端家目录', /\/home\/haangyeon/i],
  ['账号串', /\bhaangyeon\b/i],
  ['校内标识串', /\bsnnu\b/i],
  ['工作机绝对路径(远端)', /\/root\/gamess_work/i],
  ['工作机绝对路径(WSL挂载)', /\/mnt\/[a-z]\/Project\/GAMESS/i],
  ['工作机绝对路径(Win盘符,正/反斜杠)', /[a-z]:[\\/]+Project[\\/]+GAMESS/i],
  ['集群SSH端口 24522', /(?<![\d.])24522(?![\d.])/],
  ['集群SSH端口 20019', /(?<![\d.])20019(?![\d.])/],
];

// SPAN_SHAPE 的补充分支：被抹掉的 span 必须长成这些样子之一，否则说明正则咬到了数据行。
const SHAPES = ['127\\.0\\.0\\.1:7890', 'localhost:7890', '-[Pp][ \\t]+\\S+', ':\\d+', 'SNNU', 'Haangyeon'];

// ---- 反证用的毒样本：每条专有判据都要有一个能让它响起来的输入 ----
const POISON = {
  'p_rootwork.txt': '几何来源 /root/gamess_work/nlcsplit/s22',
  'p_mntrepo.txt': 'repo at /mnt/e/Project/GAMESS/nlcsplit',
  'p_winfs.txt': 'OUT = "E:/Project/GAMESS/scratch/x.json"',
  'p_winbs.txt': 'cd E:\\Project\\GAMESS && exit 1',
  'p_winlower.txt': 'path e:\\project\\gamess here',
  'p_ip.txt': 'ssh 10.8.51.23',
  'p_port2.txt': 'scp -P 24522 host:/x',
  'p_port1.txt': 'ssh -p 20019 host',
  'p_user.txt': '侧车 → /home/haangyeon/logs/step_h.json',
  'p_inst.txt': 'affiliation: SNNU',
};
// 每条毒样本预期由哪个判据抓到（selftest 用它算覆盖率）。
const COVERED_NAMES = ['工作机绝对路径(远端)', '工作机绝对路径(WSL挂载)', '工作机绝对路径(Win盘符,正/反斜杠)',
  '集群内网 IP', '集群SSH端口 24522', '集群SSH端口 20019', '账号串', '校内标识串'];
// 脱敏表自己的那条反证行：路径行必须被改、数值行必须逐字节不动。
const SAMPLE = 'L1 == 几何来源 /root/gamess_work/nlcsplit/s22 ==\nL2 E_NLC= +125.7984 N=132176\n';

module.exports = { PATH, ENDPOINT, IDENT, SECRET_PATS, SHAPES, POISON, COVERED_NAMES, SAMPLE };
