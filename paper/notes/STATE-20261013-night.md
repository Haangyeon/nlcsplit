# 夜批状态与接手清单（2026-10-13 23:25，intl-qoder）

> 目的：`PROGRESS-nlcsplit.md` 已 369 KB，长会话又死过一次（4.70 MB 会话超载），
> 所以这一轮的状态单独落这份短文件。活跃目标（goal `1791903698223-dae5bf`）不变：
> **把 nlcsplit 推到"审稿人一条命令能复现正文每一个数"的投稿就绪态**，四条验收见目标原文。

## 一、正在跑的东西

`evidence/common_grid/run_s22_full_batch.sh`，后台 ID `b2kvwh2tt`，本机 20 核。

- 22 格 S22 官方复合物**全部**走新通路 `nlcsplit.certify`（含已测的八格）
  ⇒ 满表单一来源，且八格重叠给出一次新旧交叉认证。
- 四波按原子数分档：6 并发×3 线程（≤12 原子）→ 5×4（15–20）→ 3×6（24–26）→ 2×10（28–30）。
- 每格一档 `2026*_s22_full_certificate_S22_NN_l1_small.out`(+`.rc`)，抬头自带
  `nlcsplit.__file__`（实测 = 工作树那份）与 xyz / `partition.py` / `certificate.py` 三个 sha256。
- **可续跑**：已有 rc=0 档的格自动跳过；失败档保留（判语 + rc 就是证据），重跑只生成新时间戳档。
- 预估墙钟 7–8 h。定价实测：水二聚体 6 原子 = 3.3 min；S22_03（10 原子，6 线程）>10 min 未完。
  双重和 O(N²)，30 原子两格（S22_07/15）是数量级更贵。

## 二、真阻塞（**2026-10-13 21:5xZ 已解除——见下面"解除记录"，本节上面的实测仍然为真，只是过期了**）

**解除记录**：`ssh snnu` 回得来 `hostname=workstation`、`squeue -u haangyeon` 空；Windows 侧
`curl` 经代理 `127.0.0.1:7890` 取到 `https://raw.githubusercontent.com/grimme-lab/GMTKN55/v1/S22/.res`
（sha256 `a43c93f5…c888bd7`，落在 `scratch/lit/gmtkn55_S22.res`）。
凭这条一手出站把 **22 格全部定名**（判据与两处我自己踩到的判据缺陷见
`evidence/common_grid/NOTE_s22_official_names_20261013.md`，读数档 `20261013T220452Z_verify_s22_official_names.out` rc=0）。
**没解除的**：异质体系一格都还没算（阻塞解除的是"取不到几何"，不是"算完了"）；集群提交仍需作者授权。

三条外路同时断，2026-10-13 15:2x 实测：

| 通路 | 现象 |
|---|---|
| `ssh snnu`（frp 隧道 101.132.159.118:51758） | `kex_exchange_identification: Connection closed by remote host` |
| 主机侧 `WebFetch` github | `fetch failed` |
| `api.github.com` 经 Windows 代理 127.0.0.1:7890 | **403** |
| 命名核对子代理 | 跑 15 min 后 "Unable to connect to the service" |

后果：**"至少一类异质体系"这一半需要联网取官方几何，本地一份都没有**
（`find` 核过：除 `scratch/lit/s22/` 的 22 个官方 xyz 外，盘上没有任何一手 `.xyz/.pdb/.cif`）。

## 三、体系名的处置（这条是本轮学到的，别退回旧做法）

- 官方 `struc.xyz` 第二行注释是**空的**，没有题名；`scratch/lit/identify_s22.py` 只做分子式不做命名。
- 满表**主键 = 官方文件夹号 + 从字节反推的片段分子式**（两者都是一手数据）。
  人类名原先一律打"（待核）"，**2026-10-13 22:0xZ 独立核对已完成**：22/22 与官方 `.res` 标签的化学式逐格一致，
  文件里 `##` 三块（7/8/7）的边界与几何氢键指纹的边界一格不差 ⇒ 名字可以进正文了。
  两条引用纪律：标签 `uracil` 在 05/13 **重复出现**，`indolebz`/`indolbz` 只差字母顺序
  ⇒ 正文必须带文件夹号或几何描述（05 平面、片间氢键 2 条、dmin 1.77；13 堆积、氢键 0、dmin 2.71；14 环面夹角 5°、21 90°），不能只写标签。
- 实际走的取回路径比上面设想的短：没有先列整棵 tree，而是 `contents/S22?ref=v1` 列目录 + 直接 raw 取 `S22/.res`
  （该文件在目录列表里是隐藏名 `.res`，与 `.bib`/`.average`/`.numen` 并列）。
- **不凭记忆填名**：我记忆里的 S22 顺序与盘上几何直接冲突 —— 我以为 03 是 HF–H2O，
  它的字节是两个 CH2O2、片间最短 1.67 Å（强氢键，甲酸二聚体的形状）。
- 网络恢复后的第一步不是猜 raw 路径，而是
  `GET /repos/grimme-lab/GMTKN55/git/trees/v1?recursive=1` 列出真实文件名，
  找带题名与参考能的那份文件，再用参考值反查"文件夹号 ↔ 名称"。

## 四、本轮已完成的（都有原件）

- W3 证书入口 `nlcsplit.certify` + `degeneracy_flags` 四个退化指纹 + 随包负控
  （`nlcsplit/tests/test_certificate.py` 10 条、`test_crossfamily_schemes.py` 5 条）。
  验收：水二聚体 level 1 逐方案在旧档打印分辨率内复现（最大残差 3.6e-05）、
  `argmin/argmax` 同向、`E_NLC` 跨方案极差 2.7e-15 且与旧档 `E_NL` 在 0.005 门内相等
  （`20261013T145505Z_certificate_reproduction_l1_waterdimer.out`，rc=0；
  第一次 REFUSED 那份保留 + sidecar 记因 = 几何不同源）。
- 发布清单 `tools/make_public_repo.js` 的 `PKG`/`TESTS` 补上 `certificate.py` 与两份新测试
  （**不补他就出货失败**：闸门 V 会报 stray）。只读交叉核对：白名单 37 条、
  具名不发的内部件 6 条、白名单里盘上缺的 0 条。
- 第二轮 wheel QA（工作树直建的对照件）：48 成员、**随包测试模块 11 个**、
  `partition.py` 与工作树逐字节相同、树外一次性 target 装跑 69 passed / 2 skipped / 23 deselected。
  同时实测：对照件把 6 个 `INTERNAL_ONLY_MODULES` 装进包里且过不了自家泄漏闸门（rc=1）
  ⇒ **出货件只能由 `make_public_repo.js` 从导出树建**（那是作者的五件之一）。
- 清单脚本化 `tools/make_evidence_manifest.sh`（第一层 + `LC_ALL=C` 排序 + 原子替换 +
  **发现丢登记就拒绝替换**的闸），抓到 `attribution_referee/outputs/` 16 条子目录登记
  会被静默删（`lib.js` 只看第一层，看不见这种损失），并补上 `l2cp/`、`retrieval_calibration/`
  在 HEAD 里漏登的 `MANIFEST.txt` 原件。
- 查实 **git 只能在 Windows 侧操作**：Windows 全局 `core.autocrlf=true`、WSL 未设
  ⇒ WSL 的 git 把 26 个文本文件判成"整文件已改"，在 WSL 里 `git add` 会把一次纯 CRLF→LF 改写写进历史。

## 五b、四件事的**顺序**（实测校正过一次，别再传错）

`grep` 过 `tools/make_public_repo.js` 全文：**没有**"工作树必须干净"这类前置（无 `git status --porcelain`、
无 uncommitted 检查），出货路径也**不触网、不用 token**（token 只出现在脱敏判据与 `push_manual` 那步）。
⇒ **提交授权与出货动作互相独立，谁先都行。** 我 earlier 把"先提交再出货"写成硬顺序，那是我自己加的假依赖。
真正有先后约束的只有两条：
1. **清单必须新鲜才能过 `precommit_gate`** ⇒ "证据定稿 → 重生成清单 → 提交"这个顺序是硬的；
2. **`test_count_census.py` 与 `wheel_census.py` 读的是 `dist/` 里规范名的 wheel**
   ⇒ 正文那两处现在时计数只能在**出货之后**改口，出货之前只能留占位符（见 `DECISION-G2-20261013.md` §四）。

## 六、下一轮接手顺序

1. 看 `evidence/common_grid/s22_full_batch_2026*.log` 与各格 `.rc`；失败格先读它自己的判语再重跑。
2. 22 格齐了再跑 `python3 evidence/common_grid/summarize_s22_full.py`（缺格即拒，不出表）。
3. 然后**才**重生成 `evidence/common_grid` 清单（现在故意等批跑完 —— 中途重生成会把半份 `.out`
   锁进清单，这是本仓"证据定稿 → 重生成清单 → 提交"的顺序纪律）。
4. 网络一通：先做命名核对，再取异质体系（X40 或 ion-pair 子集）官方几何并入同一证书通路。
   **22:0xZ 前半已完成**（22/22 定名 + 22 份几何与上游逐字节相同，见
   `evidence/common_grid/NOTE_s22_official_names_20261013.md`）。**后半没做**，且探到三条新约束：
   - 未认证 GitHub API 已被 **403 rate limit**（一小时 60 次，我这轮用掉了）⇒ 下一轮列目录要么带 token，
     要么走 raw 路径 + 已知文件名。`AL2X6/01/struc.xyz` 实测 **404**，说明各数据库的子目录编号不统一，
     **不要照 S22 的两位数字猜别的库的路径**。
   - **带电体系现在不能直接进证书通路**：`s22_full_certificate.py` 建 `gto.M(...)` 时**没有 `charge` 参数**，
     电离对/离子液体那类会被按中性算电子数 —— 静默错。要先给生产者加电荷入口并重新认证，
     而且**批还在跑的时候不要改它**（波四会 import 改过的文件，等于中途换代码，违反变量控制）。
   - 因此推荐先做**中性且元素异质**的小体系（候选：GMTKN55 的 alane/borane 类、 carbohydrate 氢键类），
     它们既满足"异质"又不需要动代码。选哪一类属研究路线判断，与 G1 同级，留给作者。
5. 等作者的仍是四件：G1 路线改判（建议 JCP）、G2 落笔（含 `main.md:1232-1233` 与
   `software.md:330` 两处现在时计数）、提交授权（约百处，**Windows 侧**）、
   出货与发布动作（`make_public_repo.js` → PAT → `push_manual` → 转 public → ORCID/Zenodo/ScholarOne 只 Save）。

闸门基线：`claim_gate` rc=0、`precommit_gate` rc=0、`staleManifests()`=0（批跑期间会再次陈旧，属预期）。

**一份要认得的孤儿档**：`20261013T152010Z_s22_full_certificate_S22_03_l1_small.out`
只有抬头没有判语、**没有 `.rc`** —— 那是我为"先定价再开批"而起的一次跑，我在它出数前主动
停掉了（改成直接开满批，由批自己给 S22_03 生成合格档）。它**不是**证据，也**不该**被读成结果：
`summarize_s22_full.py` 只取带 `rc=0` 的档，所以它自动被排除。留着是因为归档只增不改，
删它反而破坏"这一轮确实中止过一次"的记录。

## 七、2026-10-14 凌晨接续 —— **本节优先于上面 §五/§六**（上面那些数字与件数已过期）

**批进度**（00:5xZ 实测，第二次替换本节数字）：**20/22** 格 `rc=0` —— `S22_01…06, 08…14, 16…22` 全落，
**只剩 `S22_07` 与 `S22_15`**（都 30 原子、10 线程，`00:41Z` 提交，10 min 时 CPU 各 1:40 且在前进）。
ETA 重算：剩余 2 格 ≈ **3.2 h 中位，区间 [2.3, 4.3] h**，仍 `WITHIN_WINDOW` ⇒ 齐表约在本地上午。
守望者 `20261013T194907Z_watch_batch.out` 到点自己退了，落的是 **`# exit=2`（TIMEOUT，不是失败）**；
它的"满表 N/22"数 `.rc` **个数**，同格重跑会双计 —— 引用前按格去重（本次 20 个 `.rc` = 20 个不同格，已复核）。
`staleManifests()` 现在**不是 0**（156 条），这是**故意**的：批还在写档，中途重生成会把半份 `.out` 锁进清单。

**这一夜新增的工具（接手直接用，别重造）**：
| 要干什么 | 用哪个 |
|---|---|
| 批死活 | `bash evidence/common_grid/check_batch_health.sh`（**只看 CPU 时间前进**；`.out` 不增长是正常的，生产者算完才写盘；`GAP=5` 可加快）|
| 守着批跑完（只读、5 min 一次、默认上限 5 h） | `LIMIT=18000 SLEEP=300 bash evidence/common_grid/watch_batch_until_done.sh`；它自己落 `*_watch_batch.out` + `.rc`，超时退出**不代表失败**，只代表还在算 |
| 还要多久 | `python3 evidence/common_grid/project_w4_eta.py`（中位/区间；剩余格原子数读 `.xyz`，波次读 `run_s22_full_batch.sh`）|
| 每格线程配置 | `bash evidence/common_grid/run_record_cell_thread_config.sh`（**派生自批日志，不是原件自报**）|
| 收口 | `bash tools/run_w4_closeout.sh` —— **8 步**（编号 1…7 加 1b），顺序不可换（满表→线程记录→清单→无丢条目→stale=0→两闸门→全稿零手抄→体系列唯一）|
| 表 1 逐格转录 | `python3 tools/check_table1_transcription.py`（含第 2 列与 `MAIN-skeleton.md` 表 4b 对核）|
| 全稿零手抄 | `node tools/audit_table_row_provenance.js`（只有 `NONE` 才算硬缺陷）|
| 原件自报退出码覆盖面 | `node tools/audit_original_exitcodes.js --cited` |
| 出货前置 | `node tools/preflight_ship_check.js`（随包测试模块 = **10**）|
| 出货 + 装件 + 树外 pytest 一条龙 | `bash tools/run_ship_qa.sh`：**不带参数只打印计划、什么都不执行**；加 `--yes` 才代表授权"出货"这一步（仍不碰 PAT/push/public）|

**这一夜最大的科学发现（原 §六"四件"已不够，现在等作者七件）**：
Hirshfeld 那一列**不可逐位复现**，病因**已闭合 = BLAS 线程数**——
`OMP=1` 时两份实现逐位相同（跨三个新进程也相同），`T=2/4/8` 时同一份实现自差 8.5e-2~7.1e-1，
65% 网格点权重差 >1e-3；能量只差 1e-14 但 **1-RDM 哈希会变**（只看 `e_tot` 会漏判）。
曾被我两次误判成"两份实现分叉""自由原子 UHF 近简并换解"，都被实测否掉；
"加分母下溢阈值"这条出路也被"65% 而非少数尾部点"否掉。
⇒ 见 `evidence/common_grid/NOTE_hirshfeld_two_implementations_20261013.md` §十一~§十三（四条出路带实测价签：
固定单线程是真复现但**苯系数格数小时/格**，`S22_18` 4 线程实测 3714 s）。
**`HIR_TOL=1e-3` 作废**（我按水一格标定的外推），别靠放宽它让它变绿。

**其余七件**（连同 G5 一共 **八件**）：G1 路线（建议 JCP）、G2 落笔（**八处**，含 README 三处 +
新发现的甲烷 `0.9%` vs 表 4b `0.8%`，唯一机读来源支持 `0.8`）、G3（定价后只剩"改措辞"，16/23 是测量档不许重跑）、
G4（已做完，待你确认保留）、G6（带顶数字随线程漂 ⇒ 三选一，推荐改用确定性 Voronoi、Hirshfeld 进 SI）、
提交授权（约 220 处，**必须 Windows 侧**）、出货授权。
一页版：`paper/notes/DECISION-BRIEF-20261014.md`；逐条凭据：`paper/notes/AUDIT-acceptance-20261014.md`。

**假数从未进正文**（`git status --porcelain -- paper/*.md` 空 ⇒ 无需勘误）。

