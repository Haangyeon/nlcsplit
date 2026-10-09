# PLAN — 第十轮：外部盲审之后的科学修复与发布链

生成时刻 2026-10-06（本机）。基线 HEAD `ee66702`。
本文件是**操作手册**，不是叙述：每一步都写清"做什么 / 用什么命令 / 护栏是什么 / 失败怎么办"。
长推理与实测读数一律进本文件或 `PROGRESS-nlcsplit.md`，聊天里只留状态表。

---

## 0. 已核实的前置事实（每条都开了原件，不是听席位说的）

| # | 事实 | 原件 |
|---|---|---|
| F1 | 全套测试 **79 passed, rc=0**（原 74 + 新增 5 条闭包测试） | `nlcsplit/logs/full_suite_after_closure.log` |
| F2 | Table 1 的 ΔE_NLC 是**无鬼函数**的超位置差；`counterpoise()` 只累加 `e_tot`，从未取鬼单体的 E_NLC | `nlcsplit/step_h_s22.py:one()`、`counterpoise()` |
| F3 | 实测 ΔE_NLC 的 BSSE：水 −0.0074（0.17×跨度）、氨 −0.0031（0.11×）、**甲烷 +0.0075（1.87×跨度）**；无鬼侧复现归档差 8.7e-15 / 6.4e-5 / 3.9e-4（门 1e-3） | `evidence/nlc_cp/20261006T0657Z_nlc_bsse_three_small_dimers.out` |
| F4 | `E_nl` 在 `nlc.py` 里**按定义**就是块和，故三处旧断言恒真；已改为对独立 monolithic 参照比对，并配必须失败的负控 | `nlcsplit/nlc.py:fragment_decomposition(closure_check=…)`、`nlcsplit/tests/test_nlc_closure.py` |
| F5 | 构造苯 sandwich level 0：四方案**点数同为 19752**，而 E_NL 总量 −56.7887 / −56.6574 / −56.6202 / −56.8369，**总量跨度 0.2167 kcal/mol** | `evidence/recompute/20261005T0410Z_additivity_census.out:19-23` |
| F6 | 同表 ∫ρ = 84.03200 / 84.03203 / 83.95201 / 84.06088（同 N、不同值）⇒ 变的是**积分权重与径向映射**，不只是归属；Δ(β∫ρ) 最大 3.0415×0.10887 = **0.331 kcal/mol** | 同上 |
| F7 | Becke 在**全部 8 个体系**里都是 |P| 的极值成员；Becke↔Stratmann ≤0.006，半径调整那一对被拉开 0.02–0.22 ⇒ "四方案"实为一个家族的两个开关 | `nlcsplit/logs/step_h.json` 的 `pint` 字段 |
| F8 | §6:1183 "2.5–5.2%" 与 §4.3:1018 "2.5–9.7%" 矛盾；用裁判表 + 误差杆 U=1.060e-05 Ha 重推，被分辨的 5 个构型百分比是 2.46–9.67 ⇒ **正确值 2.5–9.7%** | `evidence/attribution_referee/outputs/table.md` |
| F9 | `references.bib` 24 个键里**没有** Treutler/Ahlrichs，而 §2.3 命名了 "Becke–Treutler"；"Becke with the radius adjustment" 亦无引用。（领域席说"names a non-existent paper"是它错了：Treutler & Ahlrichs, JCP 102, 346 (1995) 真实存在，缺的是我这里的键） | `paper/main.md:249-256`、`paper/references.bib` |
| F10 | level 0 苯的归属跨度 0.072(A) / **0.310(B)**，而发表带写 0.004–0.247 ⇒ 0.310 出界，档位依赖未披露 | `evidence/centos/20260928T193520Z_centos-step_h_benz_l0.out:14,18` |
| F11 | 甲烷相对跨度产表打印 **0.9%**，正文两处写 0.8% | `evidence/centos/20260928T193520Z_centos-step_h_l1.out:39` |
| F12 | 附录 S27 行仍带鬼函数修正前的 π 偏差 0.864/1.454/1.951；重出档给 0.7383/0.9913/1.2016 | `paper/main.md:1290`、`evidence/ccsdt/20261005T0414Z_cp_rebuild_compare_labels_fixed.out:107-109` |
| F13 | §2.5 把 19936 说成"构造几何的分区网格"，而普查原件在**官方 S22_02** 下就打印 `公共网格 18336 / becke N=19936` ⇒ 19936 是官方几何的分区网格，且每个 E_AB 都出自它 | `paper/main.md:316-320`、census `:6-7` |
| F14 | 摘要把只审过 PySCF 的事写成 "production implementations"，而 §1:61 明说未审 libxc/ORCA/Psi4/Gaussian | `paper/main.md:26-28,61` |
| F15 | `partition_matrix(mol, coords, scheme)` 接受**外来坐标**、走 PySCF 同一入口、返回未归一化 p_a(r)；`fragment_decomposition(soft=S)` 已存在且已被新测试覆盖 ⇒ P1 无需新架构 | `nlcsplit/partition.py:25-80`、`nlc.py` soft 分支 |

**未核实、不得写进正文的两条**：
- U1 领域席 Major 7"成本高估"（`evidence/scaling/step_j.json` 的 level 1 行我还没读）。
- U2 领域席给的一批 CONFIRMED 缺引（Horn/Mao/Head-Gordon、IQA/QTAIM、partition-DFT、Hirshfeld-I、vdW-DF 线性标度、原子分辨 MBD 等）——**引用键必须逐条经 Crossref 核过元数据才准进 .bib**（本仓已三次栽在"键不存在/张冠李戴"）。

---

## P0 冻结与基线（预算 15 min）

1. 记录基线与哈希，供事后归因：
   ```bash
   git rev-parse HEAD > scratch/round10_baseline_head.txt
   sha256sum paper/main.md paper/notes/review_panel_20261006/*.md >> scratch/round10_baseline_head.txt
   ```
2. 提交**第一笔（只含代码与证据，不含正文）**：
   `nlcsplit/nlc.py`、`nlcsplit/tests/test_nlc_closure.py`、`nlcsplit/tests/test_regression.py`、
   `nlcsplit/step_h_s22.py`、`nlcsplit/step_d_floor.py`、`evidence/nlc_cp/`、
   `paper/notes/review_panel_20261006/`、`PROGRESS-nlcsplit.md`。
   提交信息要写清"闭包守卫从恒真改为对独立参照，含负控；ΔE_NLC 的 BSSE 实测三体系"。
   - 护栏：提交前 `git status --short` 逐行看，**不许 `git add -A`**（本仓规矩：按名添加）。
   - `tools/hooks/GATE-OVERRIDES.log` 是钩子自己写的，一并提交。
3. **本笔不动 `paper/main.md`**——正文改写集中在 P2，避免与 P1 的新数据来回改两遍。

失败应对：若 `git commit` 被钩子拦（exit 2），读它喂回的理由当场改；**禁止 `--no-verify`**。

---

## P1 公共网格重测：把"归属效应"与"求积效应"拆开（预算 2–4 h，含机时）

### 目的
现在正文那个 0.004–0.247 的"归属不确定度"混了两件事（F5/F6）。要分别测：
- **归属效应**：同一张网格、同一套权重、同一份密度，只换 owner/soft ⇒ 纯归属。
- **求积效应**：各方案自带网格下的总量之差（F5 已有 level 0 的数，补 level 1）。
- **局部项离散残差**：Δ(β∫ρ) = β(ΣWρ − N_elec)，逐方案逐档打印。公共网格上它对四方案**恒同**，这正是公共网格测量更干净的理由，要写进正文。

### 预登记两种结局（**先写下来，免得事后合理化**）
- **结局 A（归属效应 ≳ 求积效应）**：现有"归属不确定度"这个名词站得住，只需补一句"其中求积贡献 X、归属贡献 Y"，P2 按原清单改。
- **结局 B（归属效应 ≈ 0，跨度几乎全来自求积）**：**停下，先告诉他**。这意味着论文的核心量名不副实，§3.4 与摘要要改写成"分区方案通过改变求积而移动该量"，且"attribution uncertainty"这个词必须换掉。这是科学结论的改变，不是措辞问题，**不得自行决定**。

### 脚本
新建 `evidence/common_grid/ownership_vs_quadrature.py`，骨架：
```python
# 每体系：一次 SCF（partition.scf_grid）→ 公共网格 X0,W0 与 rho0,sig0
# 四方案：p = partition.partition_matrix(mol, X0, scheme); S = p / p.sum(0)
#         res = nlc.fragment_decomposition(X0, W0, rho0, sig0, frags, b, C, soft=S,
#                                          closure_check=True)
#         E_AB[scheme] = res["inter"][(0,1)];  E_NL_total[scheme] = res["E_nl"]
# 求积侧：对每方案再跑 atom_partition(level, scheme) 的原生网格总量（F5 的 level 0 已有，补 level 1）
# 打印：公共网格 E_AB 跨度 / 原生网格总量跨度 / Δ(β∫ρ) 每格 / 点数 N / ∫ρ
```
必带的护栏（缺一条就不许出表）：
1. **交叉核对**：公共网格 + `nearest_partition` 那一格必须复现普查里 `nearest(公共网格)` 的 −7.8950（水，level 1）；差超门就非零退出。
2. **负控**：把一个原子的归属整块换给另一个原子，跨度必须显著变化；不变说明 soft 通路没生效。
3. `closure_check=True` 全程开着（soft 通路已测），任何 AssertionError 立即停。
4. 每格打印 N、∫ρ、耗时、pyscf 版本、host、git HEAD、脚本与 `nlc.py`/`partition.py` 的 sha256。
5. 归档命名 `YYYYMMDDThhmmZ_ownership_vs_quadrature_<scope>.out` + 同名 `.json`；**先跑一格看读数，再决定批量范围**（本仓教训：第一行落地不许当比例说出口）。

### 范围与机时

**算力选址规矩（2026-10-09 他定的）：短作业本机直接跑、不要问；长作业（>10 分钟或吃满多核）
一律排集群（SNNU `-p cpu`），不许占他的工作机。** 下面"在哪跑"一列按此重排。

| 批次 | 体系 | 档位 | 在哪跑 | 预算 |
|---|---|---|---|---|
| B1 | 水、氨、甲烷 | level 0 + 1 | 本机 WSL（已完成，几十一秒一格） | <10 min |
| B2 | 苯-水、苯-氨、苯-甲烷 | level 0 + 1 | 本机 WSL（已完成，~20 min 一格） | <1 h |
| B3 | 苯二聚体 A、B | level 1 | **集群**（作业 51279，cpu4，-c 32） | 已提交 |
| B4 | 其余任何 >10 min 的新格 | — | **一律集群**：`-c N` 显式给核 + 核对 `sched_getaffinity` | 按需 |

集群侧两个已知坑：`nproc` 会把 `OMP_NUM_THREADS` 取最小值当输出（判并行度看
`Cpus_allowed_list`/`sched_getaffinity`）；`--exclusive` 不等于给了 cpuset，必须显式 `-c`。

B4 走集群时的硬规矩（`snnu-hpc-safety`）：一次 `squeue` 预检 → **一个** `salloc`（不拆多个作业）→ 计算节点上跑 → 原始日志 `cat` 原文 + 比 sha256 才算入库 → **禁止** `pkill -u`、禁止碰他正在跑的作业、禁止在登录节点算。

### 失败应对
| 症状 | 根因 | 处置 |
|---|---|---|
| `soft.sum(axis=0)` 偏离 1 超 1e-8 抛错 | 归一化写错或 p 里有 0 列 | 用 `p / np.maximum(p.sum(0), tiny)` 前先断言 `p.sum(0) > 0` 全点成立；不成立就打印是哪些点、密度多少，**不要**悄悄 clip |
| 公共网格上某方案 E_AB 与原生网格差得离谱 | 公共网格点数不足以描述该方案的权重尖峰 | 记为"该方案在公共网格上不可比"，只报其余方案，并在正文写明；不许挑好看的那格 |
| 苯 level 1 内存爆 | N² 双和 | 降到 level 0 并在正文明写该格缺档；或上集群 |
| WSL 里 PySCF 找不到 | 只有 WSL 有 PySCF | 一律 `wsl -e bash -lc`，长任务用 Bash 后台 + 落盘 rc，**别在 wsl 命令里用 `&`** |
| 后台任务通知说 exit 0 但结果可疑 | 通知不等于事实 | 只认它自己落盘的 rc 文件与 .out 内容 |

---

## P2 正文改写（预算 3–5 h；**每个数字当场从原件取，禁止从被改的那句里抄**）

逐条清单（位置以 HEAD `ee66702` 的行号为准，改一处就可能漂，故按**从后往前**的顺序改，行号不互相影响）：

| 序 | 位置 | 现状 | 改成 | 数字来源 |
|---|---|---|---|---|
| 1 | 附录 S27 行 (1290) | 0.864/1.454/1.951 | 换成 0.7383/0.9913/1.2016 并注明前者被取代 | F12 |
| 2 | §6 (1183) | 2.5–5.2% | 2.5–9.7%，与 §4.3 对齐 | F8 |
| 3 | §6 (1150) | "attribution scheme, not the numerics" | 加限定：甲烷那格 BSSE 是跨度的 1.87× | F3 |
| 4 | §4.1 (883-886) | "needs no such correction … basis-set flexisation does not enter it … which is precisely why" | 删假豁免与假因果；写真话：β∫ρ 是连续统恒等式（离散残差见 P1）、`inter[(A,B)]` 不是两个 SCF 之差故不引入 BSFE、而 Table 1 的 ΔE_NLC 与 ΔE_int 同为无鬼超位置差、BSSE 实测三体系 | F2/F3/F6 + P1 |
| 5 | §3.4 表 (757-782) | 0.8% 两处 | 0.9%（甲烷），且该列**由侧车生成**而非手打 | F11 |
| 6 | §3.4 带 (757,1019,1082) | 0.004–0.247 单列 | 拆成"归属 / 求积"两列 + 披露 level 0 的 0.072/0.310 | F5/F10 + P1 |
| 7 | §3.3 (725,730-734) | level 0 比值当弛豫物理读 | 加 Δ(β∫ρ) 离散残差限定；写明分母是无鬼的 | F3/F6 |
| 8 | §2.5 (316-320) | 19936 = 构造几何 | 19936 是**官方几何**的分区网格；18336/20248 是 SCF 网格；并明说 E_AB 出自哪一个 | F13 |
| 9 | §2.3 (249-256) | Becke–Treutler 无引用 | 补 Treutler & Ahlrichs 键（**先过 Crossref**）；写明"半径调整"在代码里是哪个 `radii_adjust`；披露四者同属 Becke 家族、实为两个开关 | F7/F9 + U2 |
| 10 | §2.2 | "exact by construction … machine precision" | 说明包内检查现在比的是独立 monolithic 参照，并**明写它抓不到什么**（核、密度下限、owner、密度误差是共模） | F4/F5 |
| 11 | §1 (184) | "no system … carries an uncorrected one" | 限定到 ΔE_int；明说 ΔE_NLC 无鬼 | F2 |
| 12 | §1 (127) | "narrower than the title suggests" | **改标题**，让这句不必存在；诚实的范围句保留 | 期刊适配席 C2 |
| 13 | 摘要 (26-28,32-40) | "production implementations"；"cancels identically"；"split loses nothing" | 三处按 F14/F6/F5 收窄 | F5/F6/F14 |

改完全篇再跑：`node tools/claim_gate.js`（必须 0 数 / 0 路径）→ 若有新数字，先补归档或改成脚本生成，**不许**塞进 `claim-allowlist.tsv` 了事。

失败应对：
- 钩子 `comment_sentinel` 拦编辑 ⇒ **它拦下的那次编辑其实已经落盘**，重试会报 "0 occurrences"；先 `sed -n` 看盘上现状再决定。注释/docstring 里别写 `1e-9` 这类 e 记数（会被判实测数字），容差放代码默认值。
- `md2tex` 报"未知文档名" ⇒ 它吃**裸名**：`node tools/md2tex.js main|p2|software`。
- `md2tex` 的路径检查拒绝反引号里的模块路径 ⇒ 写成散文式（"the `fragment_decomposition()` function of `nlcsplit/nlc.py`"）。
- pdflatex 拒绝正文里的中文体系名 ⇒ 一律英文名（本仓旧教训）。
- 引用键 ⇒ 当场从 `.bib` 抄，双向核（键存在 + 元数据对）。

---

## P3 闸门与发布链（预算 1 h；**顺序固定，MANIFEST 永远最后**）

```bash
node tools/claim_gate.js                       # 0 数 / 0 路径
node tools/md2tex.js main && node tools/md2tex.js p2 && node tools/md2tex.js software
bash tools/build_pdf.sh                        # 三份 PDF，latex errors 0，页数记录
wsl -e bash -lc 'cd /mnt/e/Project/GAMESS && PYTHONUTF8=1 python3 -m pytest nlcsplit/tests -q'   # 计数（现 79）
python3 tools/test_count_census.py 之类        # 重出 53+21 → 新拆分，写回 software.md/README
# wheel 重建 + 树外安装自测（读数按各自构建命名，不写"现在的 wheel"）
node tools/make_public_repo.js                 # 15 道闸门 A…Y 必须全空
# 各目录 MANIFEST.sha256 最后重生成（sha256sum -b、LC_ALL=C 排序、排除 MANIFEST 与目录）
```
失败应对：
- gate C2 报"未登记" ⇒ 就是 MANIFEST 顺序反了；重生成后重导，**不要**去改闸门。
- 闸门抓到证据文件缺 sha256 ⇒ 补档，别把文件挪出 evidence。
- 发布树是 `dist/nlcsplit/`；`.publish/nlcsplit` 是 `tools/publish_github.js` 之后才有的副本，别搞混。

---

## P4 交给他的决策包（预算 30 min）

一页，含：
1. P1 的两种结局里**实际发生的是哪一种**，以及它对论文主张的影响。
2. 四席的原话摘录（期刊适配：JCC=大修级、JCTC 现稿会被分走；领域：Major revision，若拒做其 1–4 条则近 reject-and-resubmit，confidence 4/5；魔鬼代言：salvage 一句话 + "Not JCTC as written; JCC major-revise today"）。
3. 路线报价：A 只改错（已含在 P2，零新计算）／B = A + P1（几小时机时）／C = B + 非 Becke 家族分区（Hirshfeld-I 库存化，`soft=` 通路已就绪，估 1 天编码 + 数 core-hour）。
4. 只有他能做的：新 PAT → push → 转 public、第二作者 ORCID/邮箱/通讯、审稿人名单、Zenodo DOI、ScholarOne **只 Save 不 Submit**。

---

## 停止并问他的触发条件（不要自行决定）

- P1 出现**结局 B**（归属效应≈0）⇒ 核心量名不副实，先报再改。
- 任何一格复现护栏不过 ⇒ 停，不猜原因、不用"差不多"的值继续。
- 需要动集群配额或他的作业 ⇒ 先报。
- 需要花钱、凭据、外发（邮件/投稿系统提交）⇒ 先报；投稿系统**永远只 Save**。
- 发现我又要写一个"看起来像证据"的数字而没有刚读到的字节支撑 ⇒ 停下，写"未读到"。

## 关机安全

- 长任务一律 Bash 后台 + 落盘 `rc` 与 `.out`；**认文件不认通知**。
- 每完成一个阶段就提交一次；工作区里唯一副本的东西等于随时会丢。
- 本文件与 `PROGRESS-nlcsplit.md` 是交接面：任何中断，下一位从 P0 第 1 步重读基线哈希开始。
