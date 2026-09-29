# 发布导出器加固记录（2026-09-29）

范围：`tools/make_public_repo.js`（唯一被改的源文件，+682/-110）与 `dist/**`（发布树 + 重新出货的
wheel/sdist + 脱敏账本）。`paper/*.md`、`paper/*.tex`、`references.bib`、`MAIN-skeleton.md`、
`nlcsplit/**` 源码与测试、`pyproject.toml`、`.gitignore`、`PROGRESS-*.md` 均未改；
`evidence/**` 与 `nlcsplit/logs/**` 的**原件**未改（下面有哈希级证明）。
`paper/software.md` 在 `git status` 里显示为 M，那是并行代理改的，不是本次。

命令：`node tools/make_public_repo.js` → **exit 0**，10 个闸门数组全空（`$TEMP/final.json`）。

---

## 1. 审计那两条为什么成立，以及根因

`grep -rIli gamess dist/nlcsplit` 命中 **13 个文件**（本次会话实测复现）。旧闸门报"三数组全空"，
根因是**两个**，不止正则表不全：

| 根因 | 证据 |
|---|---|
| (a) 闸门 B 表里没有工作机路径/端口/账号串 | 旧 `secretPats` 只有 `10.8.51.23 / :7890 / PRIVATE KEY / password= / ssh@ / /home/haangyeon` |
| (b) **闸门遍历的是 `copied` 名单，不是磁盘目录树** | 名单外文件 17 个，其中 13 个是 pytest 在发布树里跑出来的 `.pyc` + 4 个 `MANIFEST.sha256`。`.pyc` 编译自 `__init__.py`，把 docstring 里的仓库串一起带进发布树，而闸门从未打开过它们 |

顺带查出的第三个 bug：`step_h.json` 的几何出处改写正则是 `/"geometry_source":s*"[^"]*"/`
—— `:s*` 少一个反斜杠，要匹配的是"冒号后跟若干字母 s"，而实际字节是 `": "`，
**这条替换从来没命中过**。`/mnt/e/Project/GAMESS/scratch/lit/s22` 因此一路进了发布树。
现已改为 `:"geometry_source"\s*:\s*"..."`，并加了"改写必须真的发生，否则闸门失败"的断言，
不再依赖正则静默失配。

`nlcsplit/run_all.sh:6 cd /mnt/e/Project/GAMESS || exit 1` 同样在名单里但没人看过一眼。

## 2. 闸门 B 新规则

`scanIntranet(root, tree)` 现在遍历 `walkTree(OUT)` 的**每一个**磁盘文件，逐行匹配，
输出 `文件:行号 <- 规则名 正则 | 行内容`，命中即 `exit 1`，没有 warn-and-continue。

新增 8 条（保留原 6 条）：

```
工作机绝对路径(远端)              /\/root\/gamess_work/i
工作机绝对路径(WSL挂载)           /\/mnt\/[a-z]\/Project\/GAMESS/i
工作机绝对路径(Win盘符,正反斜杠)   /[a-z]:[\\/]+Project[\\/]+GAMESS/i
集群内网 IP                      /10\.8\.51\.23/
集群SSH端口 24522                /(?<![\d.])24522(?![\d.])/
集群SSH端口 20019                /(?<![\d.])20019(?![\d.])/
账号串                           /\bhaangyeon\b/i
校内标识串                        /\bsnnu\b/i
```

端口用**裸 token**而不是只匹配 `:24522`，因为 `evidence/centos/MANIFEST.txt:3` 写的是
`scp -P 24522`，冒号形式的规则抓不到它（第一版就在这儿漏了）。

## 3. 发布副本脱敏：能做到自洽，附证明

### 3.1 前置探测（只读）
`nlcsplit/logs/` 与 `evidence/l2cp/` 的 `.out` 首行是脚本自己打的标题行，
例如 `== S22 子集 ωB97X-V/6-31g* level=2，几何来源 /root/gamess_work/nlcsplit/s22 ==`。
绝对路径只出现在**标题行与"侧车 →"行**，数值行里没有路径。所以**原地脱敏可行**，
不需要作废 `[S8]/[S10]` 指向的归档。

### 3.2 三张替换表（只作用于导出副本）
- `PATH_TABLE`：`/root/gamess_work/nlcsplit/s22`→`<S22_GEOMETRY_DIR>`、
  `/root/gamess_work[/nlcsplit]/logs`→`<REMOTE_LOG_DIR>`、`/root/gamess_work`→`<REMOTE_WORKDIR>`、
  `/home/haangyeon[/agent_l2_work/nlcsplit/logs]`→`<CLUSTER_HOME>`/`<REMOTE_LOG_DIR>`、
  `/mnt/<d>/Project/GAMESS` 与 `<盘>:[/]\Project\GAMESS`→`<REPO>`、`127.0.0.1:7890`→`<your-proxy>`
- `ENDPOINT_TABLE`：`-P 24522` / `-p 20019` / `:24522` / `:20019` → `<SSH_PORT>`
- `IDENT_TABLE`：`SNNU`→`<CLUSTER>`、`Haangyeon`→`<OPERATOR>`

**两处超出字面指令的判断，需要你点头**（都可一键回退，回退方式=从表里删那一行）：
1. `ENDPOINT_TABLE` 会删掉数字（端口号）。字面约束是"数字一个字符都不许动"，
   但留着就等于公开集群 SSH 端口。折中：端口只在**声明过的 span 内**消失，逐条列进账本。
2. `IDENT_TABLE` 抹的是机构名/账号名，不是路径。审计要求闸门认得 `snnu`/`haangyeon`，
   认得就必须要么抹要么停；抹成中性标签保留了 provenance 结构（机器名 `cpu3` 仍留着）。

### 3.3 数字/行不变的证明（三层，前两层是硬断言）
```
(1) cut === rebuilt      原文挖掉声明 span  ≡  结果挖掉占位符 —— 逐字符相等
                         ⇒ "除声明过的那几段，一个字符都没动"，数字不变只是推论
(2) 未被命中的行必须整行字节相同，行数必须相等
(3) 每个 span 必须过 SPAN_SHAPE（路径/端点/标识形状，且不含 `=`）——防正则贪吃咬到数据行
```
设计过程中这三层各真的拦下过一次，不是摆设：
- (1) 拦住 `/home/haangyeon/agent_l2_work/...` 里藏的字母 `l2` 的数字 2（旧写法用数字多重集，
  把它报成"越界改了数字"——断言没错，是"路径里没有数字"这个前提错了）；
- (3) 拦住占位符 `<S22_GEOMETRY_DIR>` 自己带进来的 "22"，改为逐点名声明。

### 3.4 独立复核（不依赖导出器自己的断言）
```bash
for pair in <10 个脱敏文件>; do A="$pair"; B="dist/nlcsplit/$pair"
  chg=$(diff --unchanged-line-format='' --old-line-format='%dn ' --new-line-format='' "$A" "$B")
  删掉 $chg 行后 diff "$A" "$B" | wc -l        # 必须 0
  删掉 $chg 行后两侧数值 token 序列 md5 比对    # 必须相同
done
```
实测：10 个文件，行数全部相等，其余行 diff = 0 行，数值 token 序列全等 ⇒ **PASS**。
逐文件改动行：`step_h_l2cp.out:1` / `benzmeth_cp.out:1,11` / `wsl.out:1,11` /
`centos/MANIFEST.txt:2,3` / `oa_stab.js:6` / `xref_calib2.js:10` / `xref_r3.js:12` /
`run_all.sh:6` / `step_h.json:5,71` / `libxc_referee.out:4,8,29,43-46,81,87`。
合计 **11 个文件、28 处 span**（19 path + 8 ident + 1 endpoint，按 `grep -cE '^    line [0-9]+ \['`
分类计数），没有一行是数值行。

### 3.5 哈希怎么处置的
- 每个 evidence 目录的 `MANIFEST.sha256` 在发布树内**重算**，顺序沿用母仓、值换成发布副本字节，
  母仓没登记的发布树新文件补登记（`centos` 从 4 条变 5 条，多的就是 `MANIFEST.txt`）。
- 闸门 C 双向闭合：正向"MANIFEST 里每条哈希必须等于发布副本"，反向"目录里每个文件必须被登记"。
- 自洽性实测：发布树里 6 个目录 `sha256sum -c MANIFEST.sha256` **全部 OK**；
  母仓 3 个目录同样 `sha256sum -c` 通过 ⇒ 母仓哈希对应母仓字节、发布哈希对应发布字节，
  两侧各自自洽，不存在"哈希指原件而文件是副本"。
- **没有悄悄改哈希**：`dist/PATH-SCRUB-LEDGER.txt` 逐文件记 `母仓原件 sha256 → 发布副本 sha256`、
  母仓 MANIFEST 原登记值、改动行号、每条 span 原文与占位符、随 span 消失的数字。
- 发布树里有说明行：`evidence/PUBLISHED-VARIANT-NOTE.txt`（写明哈希对应脱敏后副本、
  原件未动、对照表在哪）。账本刻意放在发布树**之外**（`dist/`，且 `dist/` 已 gitignore），
  因为它必须复述被抹掉的原文。

## 4. 新增两道闸门

**闸门 F（产物成员清单）** —— 对**归档字节**说话，不对源码树说话。
F1 任何 `test_*.py` 不在 `*/tests/` 下 → FAIL；F2 `tests/` 里只允许 `test_*.py`/`conftest.py`/`__init__.py`；
F3 顶层不许带 `.out`；F4 成员清单为空或读不到 METADATA/PKG-INFO → FAIL；F5 必须正好 1 wheel + 1 sdist。
读成员用 python `zipfile`/`tarfile` 而不是 `tar -tzf`（Git Bash 的 tar 把 `E:/` 的冒号当远程主机，实测炸过）。

**闸门 G（LICENSE）** —— 扫三处：发布树 `LICENSE`、wheel 里的 `dist-info/licenses/LICENSE`、
sdist 里的 `LICENSE`（pip 用户看到的是归档里那份）。断言无 `[yyyy] [name of copyright owner]`、
版权行正好 1 处且与 `pyproject` 作者一致。
母仓根 `LICENSE` 保持 Apache 模板原文不动；发布副本按附录自己的指示把空填成 `Copyright 2026 Angran Xia`。

**闸门 R（残留）** —— 发布树里出现 `__pycache__`/`.pyc`/`*.egg-info`/`setup.cfg` 直接 FAIL。
这条就是根因 (b) 的补丁。

**闸门 T** —— 磁盘上有、`EXPORT-MANIFEST.txt` 里没有的文件一律 FAIL（防"名单外没人看"复发）。

出货顺序也改了：产物先建到 `dist/.newartifacts/`，**闸门全绿之后**才搬进 `dist/` 并删旧货，
搬运前后 sha256 当场比对。之前是"先覆盖再检查"，检查失败已经回不去了。

## 5. 新闸门是否真的响过

不是声明，是实测。`NLCSPLIT_SELFTEST=1 node tools/make_public_repo.js` 拿**真 zip / 真文件**去喂
（`dist/.selftest/`，用完即删）：

```
residue  fired=true  clean=true
intranet fired=11 处 / cleanTreeHits=0 / 8 条新规则 covered 全 true
artifacts fired=["夹带脚本式测试模块 nlcsplit/test_fast_pair.py",
                 "tests/ 里出现不允许的文件 nlcsplit/tests/README.md",
                 "顶层带运行产物 nlcsplit/notes.out"]   clean=[]
license   firedFromSourceRepo=3 条（母仓那份模板确实该响）  cleanPublished=[]
scrub     改动行="L1 == 几何来源 <S22_GEOMETRY_DIR> =="；
          未命中行 L2 E_NLC= +125.7984 N=132176 逐字节相同=true
```

正常出货过程中它们也各自响过并被我修掉：闸门 B 9→1→1→0、闸门 C2 2→1→1→0、
闸门 F 1（sdist 无 METADATA——我的规则错，wheel 才用 METADATA）、闸门 G 2（版权行有缩进没匹配上）、
闸门 D 7（`evidence/recompute/`、`evidence/orca_control/`、`orca_run/MANIFEST.sha256`
被 [S8][S9][S12][S18] 引用却没随包发布——引用落空，已把这三个目录纳入发布）。

## 6. 重跑与三处纯净性复扫

| 扫描位置 | 命令 | 命中 | 性质 |
|---|---|---|---|
| 发布树 | `grep -rIli gamess dist/nlcsplit` | **5 文件 / 7 行** | 7 行**全部**是免责声明或闸门说明：`README.md:8`、`__init__.py:3`、`CONTRIBUTING.md:51,53,57`、`docs/tables_and_provenance.md:242`、`.github/workflows/ci.yml:25`。工作机路径 **0** |
| wheel 解包 | `grep -rIli gamess dist/.verify/w` | **2 文件** | `nlcsplit/__init__.py`（docstring 免责声明）、`dist-info/METADATA`（README 免责声明被 setuptools 抄进 long description） |
| sdist 解包 | `grep -rIli gamess dist/.verify/s` | **4 文件** | `nlcsplit/__init__.py`、`README.md`、`PKG-INFO` ×2（同一免责声明的三种副本） |

内网串复扫（`/root/gamess_work`、`/mnt/*/Project/GAMESS`、`<盘>:/Project/GAMESS`、
`10.8.51.23`、`24522`、`20019`、`haangyeon`、`snnu`）在发布树、wheel、sdist 三处均 **0 命中**。

## 7. wheel/sdist 成员核验（解包实测）

出货前那个 01:39 的 wheel：成员里有 `nlcsplit/test_fast_pair.py` 与 `nlcsplit/test_soft_partition.py`，
实锤了"此前'重打 wheel 已验证'只是看了看源码树"。这两个模块在源码树里**早已改名**成
`examples/check_fast_pair.py` / `check_soft_partition.py`，是产物没跟着重打，不是源码没清。

出货后（30 个成员 / 35 个成员）：
```
wheel test_*.py     : nlcsplit/tests/{test_geometry,test_kernel,test_partition_factors,test_regression}.py
sdist  test_*.py     : 同上，路径带 nlcsplit-0.1.0/ 前缀
两处 tests/ 内容      : __init__.py + conftest.py + 上面 4 个 —— 闸门 F2 允许的集合，无多余
nlcsplit/test_fast_pair.py / test_soft_partition.py : 已不存在
顶层 .out / logs/ / __pycache__                    : 0
```
顺带修好的：成员集合 24 → 30（实测 `zipfile` 新旧成员差集：ADDED 8 / REMOVED 2）。
旧 wheel 少 8 个成员，其中 **6 个是真缺的模块**（`figures.py`、`step_h_s22.py`、`step_i_gridrepr.py`、
`tests/conftest.py`、`tests/test_geometry.py`、`tests/test_partition_factors.py`），
另 2 个是 `examples/check_fast_pair.py`/`check_soft_partition.py`——即被移除的那两个脚本式模块的新家。

新产物（最后一次出货，`node tools/make_public_repo.js` exit 0，10 个闸门数组全空）：
`nlcsplit-0.1.0-py3-none-any.whl` 67511 B `sha256 da52df7ce6deda9e14e5803a52a8b0bb22aae183cff17e40ecd9d0f8a7d8d775`；
`nlcsplit-0.1.0.tar.gz` 55992 B `sha256 3601e1f577d67e64c698baded7faeba36ea10f7f9ced1bec61b3f9f12178c89a`。
终局复扫：发布树 gamess **5 文件**、wheel **2**、sdist **4**；内网串三处合计 **0**；
`test_*.py` 出现在 `tests/` 之外 **0**；6 个 evidence 目录 `sha256sum -c` **全 OK**。

**需要交代的处置事故**：我第一版把"删旧货"放在闸门之前，中途一次 exit 1 的运行已经把 01:39 那份
脏 wheel/sdist 覆盖掉了。它们的哈希和成员清单在本次会话里留了档
（wheel `17ea3e7c7804f28e56c83938146abd0e681517078158f2d280d803051a1259e3`、
sdist `c92632655a06085f0935bcdb25ecf92b2fee1459b6866b967eaaaac9a9d24ee7`），但原件字节已不可再取。
顺序后来已改成"全绿才搬"，并用搬运前后 sha256 比对自证。

## 8. 白名单那四个文件：没加，加了会带进什么

按指令**未加**（`nlcsplit/fastpair.py`、`nlcsplit/tests/test_fastpair.py`、
`nlcsplit/examples/probe_bound_forms.py`、`nlcsplit/tests/test_tolerance_probe.py`）。
现状：发布树与两个归档里都没有它们，且没有任何已发布文件引用它们
（`grep -rnE 'fastpair|probe_bound_forms|tolerance_probe' dist/nlcsplit` → 0 行），
所以不加不会造成引用落空。

| 文件 | 体量 | 加进去会带来的东西 |
|---|---|---|
| `nlcsplit/fastpair.py` | 388 行 / 18993 B | 一个新的公开模块与 API 面（`from . import nlc, partition` + numpy，`__init__.py` 不 import 它，属可选入口）。内网串 0 处，闸门 E 不会响。真正的代价是**把还在验收里的成对筛选实现固化成公开 API**，P2 那条主张一改就得跟着改版本号 |
| `nlcsplit/tests/test_fastpair.py` | 386 行 / 22081 B | ①**1 处内网串**：第 16 行 docstring `跑法：cd /mnt/e/Project/GAMESS && python3 -m pytest …`（脱敏表能抹，但这是新增的第 12 个需要抹的文件）②硬依赖 `fastpair`，两者必须同进同出，否则 `pytest nlcsplit/tests` 直接 ImportError ③8 个 `@pytest.mark.slow`（要 SCF），公开后 `pip install .[test] && pytest` 的默认耗时会跳起来 |
| `nlcsplit/examples/probe_bound_forms.py` | 98 行 / 4684 B | 顶层 `from pyscf import dft, gto` + `time`，跑的是墙钟计时对照。把**本机计时数字**放进公开仓，换机器就不成立；同样硬依赖 `fastpair` |
| `nlcsplit/tests/test_tolerance_probe.py` | 57 行 / 2645 B | 摸 PySCF **私有 API**：`mf._numint.nlc_coeff(...)` 与 `numint.nr_nlc_vxc(mf._numint, ...)`。发布进包就等于承诺"这些下划线符号在 `pyscf>=2.12` 上一直存在"，PySCF 一升级 `tests/` 就红。1 个 `@pytest.mark.slow`。内网串 0 处 |

四个都不触发闸门 F（`test_*.py` 在 `tests/` 下是允许的），所以"F 绿"不能当作"可以加"的依据——
决定权在白名单，不在闸门。

## 9. 还留着的问题（要你做决定，我没动）

1. `CONTRIBUTING.md:57` 让读者跑 `node scratch/audit_no_gamess.js`，而 `scratch/` 是 gitignore 的、
   且不进发布树 ⇒ 公开读者手上是一条死指针。这和闸门 D 治的是同一类病，只是它长在散文里而不是附录表里，
   闸门 D 只解析 `paper/main.md` 的附录表，所以看不见它。修法两种：导出时把这一行改写成
   指向 `tools/make_public_repo.js` 的闸门 A/B，或者把 `audit_no_gamess.js` 一起进白名单。我没动，
   因为根 `CONTRIBUTING.md` 不在我的可改范围，而改写发布副本需要你先认这个先例。
2. `dist/PATH-SCRUB-LEDGER.txt` 复述内网原文，**不得随发布树分发**（放在 `dist/`，已 gitignore）。
   如果以后有人把 `dist/` 整目录打包发出去，就白抹了。
3. 并行代理正在往 `evidence/recompute/` 里加文件：本次跑到一半
   `20260929T110830Z_libxc_referee.out` 才出现，它被自动纳管、脱敏了 9 行（`/home/haangyeon`、
   `/mnt/e/Project/GAMESS`、`127.0.0.1:7890`）。但"导出瞬间母仓证据目录仍在被别人写"这个竞态没防——
   闸门 C2 只保证导出那一刻的自洽。出货前最好冻结 evidence 目录。
4. wheel/sdist 的 sha256 每次重建都变（zip 内 mtime 不进 `SOURCE_DATE_EPOCH`）。
   **已实测**：同一份源码树连跑两次得到 `0755e2b0…` 与 `da52df7c…` 两个不同的 wheel 哈希，
   成员清单一致。要可复现得设 `SOURCE_DATE_EPOCH`，我没设，因为那会改变产物字节而不在本次授权范围内。
5. **UNVERIFIED**：新 wheel 没有在干净环境里 `pip install` 后 `import nlcsplit` 实测过——本机 Windows
   Python 无 PySCF，而指令禁止用 WSL 跑计算。成员清单、依赖声明（闸门 E）与 `.pyc` 残留是实测过的，
   "装得上、导得进"这条不是。
6. **UNVERIFIED**：`paper/software.md` 里那句"全仓唯一出现 GAMESS 这个词的地方是包 docstring 里的
   免责声明"我没有改（指令禁止动 `paper/**`）。据本次实测，它现在仍与事实不符——发布树有 5 个文件
   7 行含该词（都是免责声明/闸门说明，但不是"唯一一处"）。这句该由你改写。
