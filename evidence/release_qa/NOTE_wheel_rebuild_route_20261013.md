# wheel 重建路线实测（2026-10-13）· §5 "implements … every table" 现在卡在哪儿

> 一句话：家族外的**代码与随包测试都齐了**，但**出货件必须由导出树建**，
> 而跑导出脚本（`node tools/make_public_repo.js`）是作者列进"只有你做的五件"里的动作。
> 本轮把该实测的都实测了，下面每个数都有同目录原件可复查。

## 一、基线（为什么这句话现在不成立）

原件 `20261013T142600Z_env.out`：

| 项 | 值 |
|---|---|
| 现役 `dist/nlcsplit-0.1.0-py3-none-any.whl` | sha256 `72e61ab5363f7ef9…`，39 成员 |
| 其中 `nlcsplit/partition.py` | 7717 字节，`CROSS_FAMILY_SCHEMES` **不在** |
| 工作树 `nlcsplit/partition.py` | sha256 `ec6c0c569241fc7d…`，12062 字节 |

⇒ 评审 `pip install nlcsplit` 拿到的是旧构造表，跑不出正文跨构造那一列。
（数值正确性本身早已认证：`evidence/common_grid/20261013T_certify_inpackage_vs_external.out`，VERDICT OK。）

## 二、本轮补上的缺口：家族外代码原先**零测试覆盖**

并进 `partition.py` 之后，`grep` 全 `nlcsplit/tests/` 对 `CROSS_FAMILY_SCHEMES` /
`voronoi_factors` / `hirshfeld_factors` 的命中是 **0**，`__init__.py` 也没导出。
也就是说 wheel 里会装一个没人跑过的新分支。已补 `nlcsplit/tests/test_crossfamily_schemes.py`
（5 条，in-tree 2.97 s，都不标 slow —— 走的是 level 0 网格 + 两个自由原子 UHF，够便宜）：

- 方案表拆分本身（家族内四 + 家族外二，`ALL_SCHEMES` 顺序与不相交）；
- Voronoi 是硬指派：逐点 one-hot，且 argmax **逐点等于 `nearest_partition`**（外部锚）；
- Hirshfeld 归一 + **不退化成 1/natm**：判据直接对着代码注释里那个历史缺陷指纹
  （有一版把全部自由原子建在原点，权重退化成均匀）。owner 那一列的均值必须高出退化值一档；
- **dispatcher 真的按 scheme 分派**：三种构造两两之差必须 > 1e-3。
    这条不是凑数——若 `scheme_factors` 把 `scheme` 参数吃掉退回家族内默认，输出照样逐点归一、照样能跑，
    只有拿另一种构造去比才看得出来；
- 未知方案名报 KeyError 且把六个名字全列出来。

## 三、从工作树直建 wheel 的实测结果（**这不是出货件**）

`20261013T142600Z_shipping_wheel_census.out`、`…_wheel_member_diff.out`、
`…_wheel_install_pytest_notslow.out`、`20261013T143000Z_audit_on_staged_wheel.out`：

| 检查 | 结果 |
|---|---|
| 暂存 wheel | sha256 `857188255645f566…`，46 成员，测试模块 8 → **10**（新那份在里面），`partition.py` 与工作树**逐字节相同** |
| 成员级 diff vs 现役 | 只在新的 7 个 = 新测试 + **6 个 `INTERNAL_ONLY_MODULES`**；变了字节的 4 个被测模块 = `partition.py`、`figures.py`、`step_m_ccsdt.py`、`tests/test_regression.py`（都是 10-09 那次出货之后的正当改动）；判语 **REFUSED**——这条闸门本来就是用来否决"只动容器哈希"这种说法的，此处该 REFUSED |
| 树外真装真跑 | `pip install --target` 一次性目录，`nlcsplit.__file__` 指向 target、cwd 不在源树：**61 passed, 2 skipped, 21 deselected in 73.12 s**（`OMP_NUM_THREADS=2` 已在抬头写明）；两条 skip 是 S22 官方几何未取回，设计内 |
| GAMESS/许可泄漏闸门 | **rc=1**，命中 `dist-info/METADATA:43` 的 "No GAMESS source is…" 一句**不在具名豁免账里**（10-09 那次通过的那份豁免的是导出树 README 改写后的另一句） |

## 四、由此定下来的路线（别再走弯路）

1. `tools/make_public_repo.js` 的头两行就写着它的职责：**从工作仓生成干净仓库目录 `dist/nlcsplit/`，
   并从它重新出货 wheel/sdist**；产物先建到 `dist/.newartifacts/`，所有闸门全绿之后才搬进 `dist/`。
   它有闸门 V 专门盯"pip install 会装的模块要么随 wheel 发、要么在这里具名给不发布的理由"，
   `INTERNAL_ONLY_MODULES` 那 6 个就是在它名单上。
2. 所以**从根目录 `python3 -m build` 建出来的 46 成员 wheel 不能当出货件替换进 `dist/`**——
   它装进了 6 个刻意不发布的模块，而且过不了自家泄漏闸门。本轮那三份归档全部标注了
   "对象=工作树直建的对照 wheel"，谁接手都别把它们读成候选发布物。
3. 真正的收口动作 = 作者跑一次 `node tools/make_public_repo.js`（PAT/`push_manual`/转 public 也都在他那五件里）。
   跑完之后再重跑本目录的 census / member-diff / 树外 pytest，把 §5 那句"implements … every table"
   与 `paper/software.md` 里"the published wheel ships eight test modules"那几处**现在时计数**一起改口
   （八 → 十，成员数由新 census 给，不手抄）。

## 五、顺带查出来的一件事：**同一份工作树，两侧 `git status` 数不一样**

`20261013T142600Z_env.out` 抬头里那句 `git status --porcelain | wc -l` = 90 是 **WSL 侧**跑的，
而 Windows 侧同一个时刻是 61。逐条比过（两边各 `git status --porcelain | LC_ALL=C sort` 再 `comm`）：
WSL 多出 **26 条 ` M`**，全是文本文件（`PROGRESS-ide-S1…S8.md`、`PROGRESS-ide-qoder.md`、
`nlcsplit/fastpair_ide.py`、`nlcsplit/examples/check_screen_bound_ide.py`、`nlcsplit/logs/orca_anchor.json` …），
`git diff` 显示"整文件 114 行全变但看不出改了什麼"，`git diff --summary` 里没有模式变更 ⇒ 这是**行尾**不是内容。

根因（实测，不是猜）：Windows 侧全局 `core.autocrlf=true`，仓库里存 LF、工作树检出 CRLF，所以判"干净"；
WSL 侧 `core.autocrlf` 未设（等效 false），拿工作树的 CRLF 字节去比 LF blob ⇒ 每个文本文件都判"整文件已改"。
`.gitattributes` 只给 `evidence/** -text`（不做转换），所以证据目录两侧一致，而 `PROGRESS-*.md`、
`nlcsplit/**.py` 这些没有属性保护。

两条规矩由此定下来：

1. **提交只能在 Windows 侧做**。在 WSL 里 `git add` 这些文件会把一次纯粹的 CRLF→LF 改写
   写进历史，牵动 26 个文件与所有下游哈希；本轮所有"未提交 N 处"的计数一律取 Windows 侧。
2. 任何在 WSL 里跑的脚本**不要把 `git status` 计数写进归档抬头**（会造出一个跨侧不可比、
   且看起来像"丢了改动"的数）。本轮那份 env 抬头保留原文不改，问题记在这里。

（另：`scratch/` 已被 `.gitignore` 收着，本轮的 `scratch/wheel_qa_*` 暂存目录不出现在任何一侧的
status 里，与上面这 26 条无关。）
