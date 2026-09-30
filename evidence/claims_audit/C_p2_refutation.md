# 审计：`"P2 那条线是否证：可证界在弱耦合二聚体上剪不动，空载墙钟 1.08–10.28× 更慢。"`

判定：**需要限定**（数值全部可重算、方向无误；但"空载"与"否证"两处口径要收，端点数字不能当稳健量引用）。
重算脚本 `scratch/audit_p2_refutation.py`（输出 `scratch/audit_p2_refutation.out`）；只读，未改动任何已有文件、
未动 `evidence/` 既有工件、未联网、未提交作业。`evidence/scaling/MANIFEST.sha256` 与
`fastpair_ab / bound_forms / coretail` 三份 MANIFEST 全部 `sha256sum -c` 通过（11/11 OK），
`evidence/scaling/step_j.json` 与工作侧车 `nlcsplit/logs/step_j.json` **逐字节相同**。

被审句拆成三个可判定的子命题：

| 子命题 | 判定 | 依据 |
|---|---|---|
| (a) 数值 "1.08–10.28×" | **成立且逐样本可重算**，但它是单次测量的两端点，非稳健量；纳入仓内已被丢弃的那次复现，真实跨度是 **1.03–12.8×** | §1、§4 |
| (b) "空载" | **方向成立、措辞过强**：判据是"每个计时块**结束时**采样一次外部 R 态任务数 ≤1"，24/24 样本外部 R=0、无样本被剔；同工件的 `load1` 记到 0.99–4.24，不是"空载机" | §3 |
| (c) "剪不动 = 否证" | **在测量范围内成立，且不靠墙钟**：0/15 根对上树比大 gemm 便宜、近场占 cross 点对 100.0000%、最小块对界 197.96 Ha 比待判量松 2.37e5×、达标 τ 下仍算 84.4–95.4% far 点对；但**外推到密网格/大体系无数据支撑**，仓内自己的数据显示比值随网格变密而**下降** | §4、§5 |

---

## 1. "1.08–10.28×" 出自哪个工件：逐样本墙钟表

**唯一出处**：`evidence/scaling/step_j.json`（工件自报 `generated_utc 2026-09-29T14:12:54Z`，
PySCF 2.12.1、6-31g\*、wb97x_v、`omp_num_threads "4"`、`load_gate 1`），
对应 stdout `evidence/scaling/20260929T1340Z_step_j_scaling.out`（末尾 `24 / 24 个样本空载可用`、`EXIT=0`）。
稿件表格在 `paper/p2.md:290-298`，**六个系统 × 三档 τ 共 18 个比值逐格与 JSON 重算一致**（下表末列），无一处对不上。

比值一律 = **screened / exact**，`>1` 是**更慢**（见 §2）。

| 体系 | τ (Ha) | exact s | screened s | 比值 | far 点对仍算 % | \|dE\| (kcal/mol) | valid_timing | 外部 R | load1 |
|---|---|---|---|---|---|---|---|---|---|
| 3 原子 L0 | 1e-8 | 0.080247 | 0.425791 | **5.306** | 72.63 | 1.268e-3 | true | 0 | 0.99 |
| 3 原子 L0 | 1e-10 | 0.080247 | 0.552752 | **6.888** | 88.90 | 1.227e-5 | true | 0 | 0.99 |
| 3 原子 L0 | 1e-12 | 0.080247 | 0.640080 | **7.976** | 95.40 | 6.828e-8 | true | 0 | 1.07 |
| 6 原子 L0 | 1e-8 | 0.483199 | 1.417183 | **2.933** | 55.09 | 7.118e-3 | true | 0 | 2.90 |
| 6 原子 L0 | 1e-10 | 0.483199 | 2.391797 | **4.950** | 81.86 | 4.605e-5 | true | 0 | 2.90 |
| 6 原子 L0 | 1e-12 | 0.483199 | 2.619895 | **5.422** | 93.75 | 1.166e-7 | true | 0 | 2.83 |
| 9 原子 L0 | 1e-8 | 0.520865 | 2.947763 | **5.659** | 46.09 | 1.433e-2 | true | 0 | 3.74 |
| 9 原子 L0 | 1e-10 | 0.520865 | 4.629189 | **8.887** | 74.51 | 1.445e-4 | true | 0 | 3.52 |
| 9 原子 L0 | 1e-12 | 0.520865 | 5.341009 | **10.254** | 91.30 | 6.111e-7 | true | 0 | 3.32 |
| 12 原子 L0 | 1e-8 | 0.993717 | 4.619375 | **4.649** | 37.49 | 2.444e-2 | true | 0 | 4.06 |
| 12 原子 L0 | 1e-10 | 0.993717 | 8.362381 | **8.415** | 66.20 | 2.995e-4 | true | 0 | 3.59 |
| 12 原子 L0 | 1e-12 | 0.993717 | 10.217468 | **10.282** | 86.34 | 1.773e-6 | true | 0 | 3.19 |
| 6 原子 L1 | 1e-8 | 4.450458 | 4.857200 | **1.091** | 41.60 | 1.534e-2 | true | 0 | 3.75 |
| 6 原子 L1 | 1e-10 | 4.450458 | 7.318461 | **1.644** | 68.40 | 7.879e-5 | true | 0 | 3.53 |
| 6 原子 L1 | 1e-12 | 4.450458 | 8.675992 | **1.949** | 84.43 | 4.382e-7 | true | 0 | 3.37 |
| 9 原子 L1 | 1e-8 | 9.633560 | 10.406537 | **1.080** | 31.36 | 3.819e-2 | true | 0 | 3.42 |
| 9 原子 L1 | 1e-10 | 9.633560 | 15.681932 | **1.628** | 60.45 | 3.055e-4 | true | 0 | 2.88 |
| 9 原子 L1 | 1e-12 | 9.633560 | 21.059589 | **2.186** | 79.46 | 1.531e-6 | true | 0 | 2.35 |

* 18/18 比值 > 1，**没有一个样本快于全量和**；`min = 1.0802`、`max = 10.2821` ⇒ 稿件的 "1.08–10.28×" 字面正确。
* 6 个 `exact` 样本也各带一次计时与 `valid_timing`，所以稿件说"24 validated samples"（`p2.md:55, 285`）
  与实际相符——但**跨度 1.08–10.28× 只由那 18 个 screened 样本决定**，24 这个分母别拿去撑比值。

### 1.1 仓内还有一次**被丢弃的完整复现**（稿件没提）

`scratch/STEPJ_v1_exact_accounting_missing.out`（48 行，`EXIT=0`、`24 / 24 个样本空载可用`、每行 `外部R=0`）
是同一阶梯的上一次运行，丢弃原因**只是记账**——`exact` 那行的"评估点对"打成 0、"占 far 0.00%"，
**墙钟、load1、外部 R 计数与判据都齐全**（第 3 行印的判据与正式版逐字相同）。它的 18 个比值：

6.286 / 8.143 / 8.571（3 原子 L0）、7.810 / 11.095 / **12.810**（6 原子 L0）、5.281 / 8.386 / 9.456（9 原子 L0）、
5.590 / 8.976 / 11.687（12 原子 L0）、1.213 / 1.749 / 2.094（6 原子 L1）、**1.027** / 1.607 / 2.029（9 原子 L1）。

* 两次运行合并：**36 个计时 screened 样本，0 个快于全量和，跨度 1.027–12.810×**。
  ⇒ 对"剪不动"这是**加强**；对"1.08–10.28×"这个具体区间是**削弱**（真实上端 12.8×，真实下端≈平价）。
* 逐格复现率：screened 时间差 **0.4–13.6%**（多数 <5%），`exact` 基线差 **2.6–56.5%**
  ——最不稳的是 6 原子 L0 的 0.483 s vs 0.21 s。也就是说**比值的不确定度主要来自分母（全量和）**，
  而 L0 的四个基线只有 0.08–0.99 s，本身就在噪声区。
* 顺带：同一份阶梯里 L0 基线内部不自洽——6 原子 6.82M 点对 0.483 s（14.1 Mpp/s），
  9 原子 16.69M 点对 0.521 s（32.1 Mpp/s）。次线性 ⇒ 亚秒级基线被固定开销主导。
  这不翻结论（L0 每个比值仍 ≥2.9），但意味着 **10.28× 这个上端点恰好落在最难复现的那个分母上**。

---

## 2. 比值方向：1.08× 是"慢"，分子是 screened

* 定义写在 `paper/p2.md:287`：**"Ratios are screened/exact wall clock"** ⇒ **分子 = 屏蔽路径，分母 = 全量和**；
  比值 >1 就是**更慢**。工件侧同向：`step_j_scaling.py:106-108` 计时、`:115` 存 `wall_s`，stdout 每行把 exact 排在该体系第一行
  （`20260929T1340Z_step_j_scaling.out:6, 13, 20, 27, 34, 41`），稿件绝对秒数与之逐项一致。
* 区间两端各对应哪个体系/level（不是"一个体系一个数"，而是"两端各锁死一格"）：
  * **1.08× = 3 个水单体（9 原子）level=1，τ=1e-8 Ha**（`step_j.json:614-637`：10.4065 / 9.6336）。
    该格 `abs_dE_kcal = 3.819e-2`，是 P1 要求的 1e-6 kcal/mol 的 **38,193 倍**——即"最不难看的那个比值，
    精度上最不可用"。稿件 `p2.md:319-320` 已明说这一点，方向正确。
  * **10.28× = 4 个水单体（12 原子）level=0，τ=1e-12 Ha**（`step_j.json:436-459`：10.2175 / 0.99372）。
  * 另一组数（摘要 `p2.md:23-25`）**1.95–10.25×** 是"只取达标样本"（|dE|≤1e-6）的跨度：
    重算得达标样本恰 4 个——3 原子 L0 (7.976)、6 原子 L0 (5.422)、9 原子 L0 (10.254)、6 原子 L1 (1.949)，
    端点与摘要一致。⇒ 稿件里 **1.08–10.28（全体）与 1.95–10.25（达标集）是两个不同的口径，都对，但不能混用**。
* 主审句把 1.08× 说成"更慢"，**方向无误**。

---

## 3. "空载"这个前提：判据、字段、逐样本数值、有无剔样

**字段**（`step_j.json`）：每个样本一个 `load_after` = `{"load1": …, "other_runnable": …}`
（例 `step_j.json:38-42`），每个体系另有一个 `load_after_scf`（`:14-17`）；顶层 `load_gate: 1`（`:7`）。

**判据在代码里的样子**（`nlcsplit/step_j_scaling.py`）：
* `:60-76 external_runnable()`——扫 `/proc`，只数**状态为 `R`**、**有 cmdline**（排除内核线程）、
  且 **pid 不在 `MINE` 里**的进程。
* `:40-55 _my_ancestors()`——`MINE` = 自己 + 沿 `/proc/<pid>/stat` 上溯至多 8 层的**父链**；
  注释 `:41-42` 就是主审句提到的那次教训："用别的方法会把'我自己正在算'当成外部争用，
  于是每个样本都自判 INVALID——那是个永远为真的闸门，等于没有闸门"。文件头 `:8-9` 再说一遍。
* `:131-132`——`load_after = pressure()` 在 `perf_counter()` 停表**之后**采一次，
  `valid_timing = other_runnable <= LOAD_GATE`。
* 运行时自述：stdout `:3` "判据：非本进程树的可运行用户任务 > 1 的计时样本标 INVALID"。

**结论：现在用的判据就是"不含本进程树的用户 R 态任务 > 1 才算脏"**，且 `evidence/scaling/step_j.json`
（22:24 落盘）与工件生成时刻同判据——`git log` 里 `step_j_scaling.py` 只有一个提交（`ca0445b`，2026-09-29 22:28），
`scratch/audit/repo{,2}`、`.publish` 里的快照（22:12）与现行版第 1–80 行 **逐字节无差异**，
工件 stdout 也自印了同一条判据 ⇒ **不存在"生成后才改判据"的空间**。

**每个样本当时的外部 R 态任务数：18 个 screened + 6 个 exact 全部 `other_runnable = 0`**（stdout 每行 `外部R=0`，
JSON 全 24 处一致）。**没有任何样本被剔**：`valid_timing: true` 24/24，与稿件 `p2.md:285` 相符。

支撑"当时确实没外部争用"的旁证：
* `uptime_s=62`（stdout `:2`）——WSL 刚重启 62 秒，37 分钟前那份 `coretail` 还写着"本机多代理并发"
  （`evidence/coretail/20260929T130257Z_coretail_bound.out:2`）。
* 每体系的 `load1` 沿样本单调衰减（如 12 原子 L0：4.24→4.06→3.59→3.19），正是一发 4 线程作业收尾的形状。

但 **"空载/idle machine/unloaded machine" 这三处措辞（`p2.md:21, 55, 270`）超出了判据能支撑的东西**：
1. `load1` 记到 **0.99–4.24**（不是 ~0），与 `OMP_NUM_THREADS=4` + 主线程自洽，但字面上不"空"；
2. 判据是**每块结束时的一次瞬时采样**，块长 0.08–21 s，块**中途**的外部突发抓不到（0.08 s 那块几乎无检测力）；
3. 阈值**允许 1 个**外部 R 态任务，即一整颗占用的核也能过关；
4. `step_j.json` **没记 `os.cpu_count`**，"load1 远小于核数"这条无法从本工件自证——20 核只来自另一份工件
   `evidence/bound_forms/20260929T112656Z_hybrid_nearfield.out:4`（`os.cpu_count=20`，2 小时前的同主机）。

**同一仓里还有更强的第二个闸门**（`nlcsplit/examples/hybrid_nearfield.py:78-101, 147-158`）：
对窗口内**非本进程 CPU 时间做积分**，`EXT_GATE` = 外部核数 < 0.5，并逐样本印 `own=/ext=/load=/valid=`
（该工件 15 个样本 `ext≈9–10` 核 ⇒ 全判 INVALID，见 `:59-112` 与 `PROGRESS-nlcsplit.md:1947`）。
**step_j 没用它**。所以稿件 §6 描述的是**较宽松的那一个**——描述得**准确**，但读者容易把它读成"计时被严格核过"。

**关于被丢弃的两次历史尝试**：稿件 `p2.md:281-284` 的两条都能对上——
(a) "5.2× slower" 那句出自苯二夹心被并发占满的窗口（`PROGRESS-nlcsplit.md:1691` `25.9 s（慢 5.2x）`、
`:1954` "计时窗口现在被 12 个代理占满，任何墙钟都是脏数据"，苯侧结论改用冻结 log 的几何计数
`hybrid_nearfield.out:16-24`）✓；
(b) "闸门数自己"那一版**没有留下工件**——`hybrid_nearfield.py` 只有一个提交且已排除自己的 BLAS 线程，
所以那句关于自身历史的陈述只有代码注释 `step_j_scaling.py:41-42` 自证。属**低风险、建议加一句"无存档"**。

---

## 4. "剪不动"有没有独立于墙钟的证据：有，而且是四条

| # | 证据 | 数值 | 出处 `文件:行号` |
|---|---|---|---|
| 1 | **叶对账**（接受/评估/访问计数，与秒数无关） | 9 原子 L1、τ=1e-12：`n_leaves 1061`、`n_leafpairs_total 493,395`、`n_leafpairs_evaluated 348,536`（**70.64%**）、`n_accepted 43,455`、`n_visited 391,955`、`pointpairs 236,127,947 / 297,165,609`（**79.46%**） | `evidence/scaling/step_j.json:673-677`、`:669-672` |
| 2 | **"84–95% far 点对仍被算"这个数的出处** | 4 个达标样本（\|dE\|≤1e-6）的 `work_frac_evaluated`：0.9539670670270839（3 原子 L0）…0.8442802960402652（6 原子 L1）⇒ **84.4–95.4%**。字段定义 = `pointpairs_evaluated/pointpairs_far`（`step_j_scaling.py:120`），即**点对**口径，与稿件"far point pairs"一致 | `step_j.json:102`、`:558`、`:216`、`:330` |
| 3 | **最小原子对界 vs 待判量** | `min_block_bound_ha = 197.95986835849376`，`P_frz_inter_frag = −8.344948837120707e-4 Ha` ⇒ **2.372e5×**；同工件 `n_pairs_bound_below_value = 0`、`dropped_pairs = []`、`n_dropped_screen = 0`（21 个原子块对全数不过） | 界：`evidence/fastpair_ab/fastpair_ide_validation.json:21` 与 `fastpair_ab_compare.json:75`；待判量与两个 0：`fastpair_ab_compare.json:71, 78, 79`；空转：`:25` |
| 4 | **同窗口逐根对 A/B 成本普查**（决定性一条，PROGRESS 早已把它排在墙钟之前） | **`atom pairs where the tree is FASTER than the big gemm: 0/15 (0.0%)`**；oracle"每对走便宜路径"最多省 **0.0%**；单对中位 exact 305.5759 ms vs tree 1606.9475 ms（**5.26×**）；每百万点对 40.28 ms vs 197.4 ms | `evidence/bound_forms/20260929T112656Z_hybrid_nearfield.out:140-146`；判读 `PROGRESS-nlcsplit.md:1941-1944` |
| 5 | **近场占满**：15/15 根盒缝精确 0.0000 Å ⇒ 几何接受/拒绝的**省钱上限是 0.0%**；苯 276/276 缝 0.00 Å、0/276 根界 ≤1e-8 Ha（exact 间项 38.3510 kcal/mol） | `hybrid_nearfield.out:40-43, 46`；苯：`20260929T112656Z_hybrid_nearfield.out:20`（operator 注）与 `evidence/bound_forms/20260929T101447Z_probe_bound_forms.out:310, 312` |
| 6 | **收紧界也换不到可跳性**：核/尾拆分把根界紧 6.116e3×（2.172e+04→3.552 Ha），叶对界只紧 **2.131×**（4.507e-2→2.115e-2 Ha），叶对 ≤1e-12 Ha 者 59,644→64,883（共 197,686），τ=1e-12 可跳点对占比 **12.349%→13.650%**；派工时指定的那个形式在 125,097/197,686 叶对上**反而更松** | `evidence/coretail/20260929T130257Z_coretail_bound.out:113-123, 239-240, 194, 74` |
| 7 | **界本身松到什么程度**：390 个抽样叶对里最坏 bound/\|actual\| = **1.181e+07** | `coretail_bound.out:134, 147` |
| 8 | **几何判据级否证（与成本无关）**：质量加权球在 300,000 次随机细化里 **53,983 次（18.0%）破坏单调性**，轴对齐盒 **0 次** ⇒ 球判据在任何容差、任何硬件上都不能做自顶向下整块跳过 | 计数 `PROGRESS-nlcsplit.md:1650`；钉成测试 `nlcsplit/tests/test_fastpair.py:71`（球）与 `:95`（盒） |
| 9 | **独立工件的交叉印证**：水二聚体 L1、预算 1e-9 Ha 时测试自动选到 **τ=1e-13** 且只省 9.81%（cross+self）⇒ 换算回 **cross 口径仍要算 85.63%**，落在 84.4–95.4% 带内——**这个数不来自 step_j** | `nlcsplit/logs/20260929T105823Z_pytest_fastpair_after_assert_fix.out:24`；换算见 `scratch/audit_p2_refutation.py` §H |

### 4.1 我另算的一条：把比值从"噪声"升成"结构"的盈亏平衡点

`scratch/audit_p2_refutation.py` §D/§F：对每个体系用三档 τ 的 (评估点数, 墙钟) 最小二乘拟合
`wall = A + B·W`（A = 建树+遍历的固定代价，B = 屏蔽路径的**边际**每点对代价），与 exact 的均摊速率比：

| 体系 | A (s) | B (s/1e6 点对) | exact 均摊 | **边际速率比 B/B_exact** | 假设一点不跳的外推 | **打平所需 far 保留比 f\*** | 实测最好保留比 |
|---|---|---|---|---|---|---|---|
| 6 原子 L1 | 1.154 | 0.0745 | 0.0370 | **2.01×** | **2.27×** | **36.86%** | 41.60% |
| 9 原子 L1 | 3.264 | 0.0734 | 0.0324 | **2.26×** | **2.60×** | **29.20%** | 31.36% |
| 12 原子 L0 | 0.406 | — | — | 11.64× | 12.05× | 5.08% | 37.49% |
| 9 原子 L0 | 0.520 | — | — | 10.29× | 11.29× | ≈0% | 46.09% |

（每格只用 3 个点拟合；4 个 L0 格里有 2 个的 A 拟合成负数 ⇒ 亚秒级基线不可信，脚本已逐格标注，
  **结论只引 L1 两格**；L0 两行列出只为说明趋势方向。）

读法（这是本次审计最有用的一条，且不依赖任何一次秒数）：
* 屏蔽路径**连每一点对的边际算术都比全量和贵 2 倍以上**（碎叶 gemm），再叠一个 1.15–3.26 s 的固定树代价；
  于是"**τ→0、一个都不跳**"的极限也要 **2.27–2.60×** 慢。这条直接封掉"是不是我 τ 没调对"。
* 要**只是打平**，必须把 far 点对保留比压到 **29.2% / 36.9%**，而实测最好只到 **31.4% / 41.6%**；
  差的那 2.2 / 4.7 个百分点**只能靠更粗的 τ 去买**，而更粗的 τ 在 τ=1e-8 处已经把 |dE| 放到
  **1.5e-2 / 3.8e-2 kcal/mol = 目标的 15,343× / 38,193×**。
* 所以"剪不动"不是"这台机器今天没加速"，而是：**在这套实现里，省钱的那一半（跳掉的工作）与
  达标的那一半（精度）之间，没有任何 τ 能同时满足**。

---

## 5. 这些数字合起来够不够叫"否证"

**够，但只在它自己的边界内。** 否证的对象、以及它成立的方式：

* **被否证的命题**（=P2 先前的正面假设）："对 VV10 实空间双重和做**带证明界**的层次/MAC 屏蔽，
  在保留片段对归属的前提下，能加速。"
  否证它用的是**三层独立证据**，任何一层单独都够呛、叠起来很硬：
  ① 判定级：0/15 根对上树比大 gemm 便宜，oracle 上限省 0.0%（与硬件无关的分类器上界，§4 表第 4 行）；
  ② 几何级：近场=cross 点对 100.0000%、15/15 根盒缝 0.0000 Å、球判据 18.0% 违单调（§4 表第 5、8 行）；
  ③ 成本结构级：达标 τ 下仍算 84.4–95.4% far 点对，且边际速率还贵 2 倍 ⇒ 无 τ 可打平（§1、§4.1）。
  ①②③ **都不是"一次墙钟比一次墙钟"**，这就是"否证"与"暂时没加速"的分界。
* **否证范围（可以照实说的最大限度）**：*本实现*（PySCF 2.12.1 + 本仓 numpy MAC，`fastpair.screened_decomposition`，
  原子块→最长轴二分叶、min_pts 32）在 ωB97X-V/6-31g\*、刚性水链 1–4 单体（3/6/9/12 原子，
  且这串链在脚本注释里就自陈"**不是物理体系**"`step_j_scaling.py:84`）、网格 level 0–1（保留点 ≤26,073）、
  一台 4 线程的 WSL 主机、**以及 P1 需要的 1e-6 kcal/mol 逐对精度**上，不产生任何加速；
  并且**在这套测量里没有一个样本快于全量和**（含被丢弃的复现：36/36）。
* **外推限制（稿件已承认一部分，还差三条）**：
  1. 稿件 `p2.md:322-335` 已经拒绝做渐近断言并给了理由（τ 是绝对每节点对常数 ⇒ `cert_err` 随 N 增长：
     L0 3→12 原子 2.824e-10→9.187e-9 Ha，9 原子 L1 1.351e-8 Ha；`step_j.json:108, 222, 336, 450, 678`），
     这条**核对无误**，是全文最诚实的一段。
  2. **没测的方向是"网格变密"，而仓内数据显示比值随网格变密而下降**：同一体系 L0→L1，
     6 原子 5.42×→1.95×、9 原子 10.25×→2.19×（12 原子在 level 1 上没跑）；同时保留比也降（55.1%→41.6%、46.1%→31.4%）。
     两条趋势都朝"能翻盘"的方向走。反方向的说法也有依据——固定代价 A 本身随树变大（6 原子 L1 1.15 s →
     9 原子 L1 3.26 s，`n_visited` 只涨 2.1 倍），所以翻盘**不被数据支持**；但同样**不被数据排除**：
     level ≥2 上**没有任何 screened 计时**（仓里只有全量侧的 level-2 规模感，
     `evidence/recompute/20260929T110830Z_libxc_referee.out:216, 219`）。
     ⇒ 否证只在 **≤30,000 网格点（level 0–1）** 内成立，`p2.md:331` 写了这句上界，但没写"趋势朝翻盘走"这件事。
  3. 体系族限制：等密度刚性水链 + 弱耦合二聚体；真正分离的大体系（稿件自己举的 300 原子蛋白-配体）
     未测、且 `p2.md:355-358` 明确不作主张 ✓。
  4. 单实现限制：否证的是"**这种**层次屏蔽（原子块＋Python/numpy 逐节点对判界）"，不是"任何带证明界的方案"。
     稿件 §7 把这写成四条**未满足的条件**（`p2.md:337-358`）✓，这个写法是对的；
     主审句"可证界剪不动"若脱离这四条，就会被读成"可证界这个东西剪不动"。
* **一个不能被漏掉的反面事实（稿件没写）**：同一批工件里唯一一次"比基线快"是
  `tree min_pts=1024` 的 **0.893×**（`hybrid_nearfield.out:134`，contended 窗口、`nval=0`/valid=False）。
  它按 **cross 口径**只丢 **0.0452%** 的点对（保留 99.9548%，`:135`；按 cross+self 全量口径是保留 99.969%，`:105`），
  PROGRESS 判读为"省的是**分块形状**的钱，不是**屏蔽**的钱"（`PROGRESS-nlcsplit.md:1943-1944`）。
  这个处理是对的，但**稿件正文一次都没提这个 0.893×**，而它恰恰是审稿人 `grep` 得出来的东西。

---

## 6. 缺陷清单（按严重程度）

1. **[中] §6 协议陈述与代码不符**：`p2.md:277-279` "each after its own converged SCF"——实际每个体系只跑
   **一次** `mf.kernel()`（`step_j_scaling.py:96-101`，`mf.kernel()` 在 `:100`），四次计时共用同一密度（`fastpair.py:301 mf.make_rdm1()`，
   函数内**不重跑 SCF**）。这使比较更干净（同网格同密度，`n_grid`/`n_kept_points` 四行完全相同，
   如 `step_j.json:22-23, 47-48`），但句子必须改成"共用一次收敛 SCF、每次调用各自重建同一参数的网格"。
2. **[中] "1.08–10.28×" 是单次测量的端点，且被丢弃的复现给出 1.03–12.8×**。引用区间时应写"两次独立空载运行、
   36 个计时样本、比值 1.03–12.8×、无一快于全量和"；只报一次的那对端点会显得区间是稳的。
3. **[中] "idle/unloaded machine"（`p2.md:21, 55, 270`）措辞过强**，见 §3 的 1–4 点。
   建议改成判据的字面陈述（见 §7 措辞）。
4. **[中] §3 的合成夹具数字是孤儿**：`p2.md:176-177` "3.13e-5 against an actual block sum of 3.47e-6,
   a factor of 9 [`nlcsplit/tests/test_kernel.py`; plan §B案]"——`nlcsplit/tests/test_kernel.py`
   **不含任何 bound/界相关代码**（`grep -n "bound\|3\.13\|3\.47"` 零命中），这两个数在全仓
   （含 `evidence/`、`nlcsplit/logs/`、`PROGRESS-*`）**不存在**；`§B案` 这个指引也落不到地上——`MAIN-skeleton.md` 与 `PLAN-20260928-baseline-first.md` 里都查不到
   `B案` 二字（该串只出现在 `PROGRESS-nlcsplit.md:1291`、`PROGRESS-ide-qoder.md`、`scratch/dispatch_1.md` 与稿件自身）。
   界松的真实存档证据是 1.181e+07（390 抽样叶对）与 §4 表第 3、6 行。⇒ **删掉或换成已存档数字**；
   仓的先例（95,481 那个数是注释里造出来的）说明这类数必须清零。
5. **[中] `p2.md:317` "a 1,061-node tree"**——1061 是 `n_leaves`（`step_j.json:673`；语义 `fastpair.py:324-327`），
   节点数不是叶数：同仓 `coretail_bound.out:5` 的口径是 "节点总数 1388（叶 697，内部 691）"，
   与 `p2.md:252` 自己写的 "1,388 nodes and 697 leaves" 一致。`step_j.json` 里没有节点总数这个字段
   （`fastpair.py:381` 只返回 `n_leaves`），所以只能改成"1,061 个叶"，**不要**顺手报一个节点总数。
6. **[中低] §7 第 1 条的上界措辞**：`p2.md:343` "the *smallest* block-pair bound we found in a real dimer is 197.96 Ha"
   只在 geomlib 水二聚体内部成立；同批工件里 S22_02 水二聚体最小界 **133.93 Ha**、苯 S22_11 **188.32 Ha**
   （`fastpair_ab_compare.json:293` 与 `:515`；比值分别 1.398e5×、2.909e4×）。
   摘要 `p2.md:26-27` 还把同一个数叫作 "**loosest** block-pair bound"，而 197.96 是 21 个界里**最紧**的那个
   （与 §1/§7 的 "smallest" 互相矛盾）。⇒ 可主张的普适形式是"**最小的那个界仍比待判量松 2.9e4–2.4e5×**"。
7. **[低] §7 第 2 条一句有歧义**：`p2.md:349-351` "so their admissible τ is finer and **the share smaller**"——
   若"the share"指 evaluated share 则是错的（τ 更细 ⇒ 保留比**升**向 100%）；只有指"droppable share"才对。
   顺带：那两个非达标体系在 finest 实测 τ 下的保留比是 86.34% 与 79.46%（`step_j.json:444, 672`），
   79.46% **低于**摘要的 84.4% 下界——因为它是被精度剔除的；写成"84.4–95.4%（达标集），
   非达标体系只会更高"更稳。
8. **[低] 交叉工件字段名与归属**：`p2.md:344-345` 把 `n_pairs_bound_below_value = 0`、`dropped_pairs = []`
   归给 `fastpair_ide_validation.json`，这两个字段实际只在 `fastpair_ab_compare.json:78-79`；
   sidecar 里的等价物是 `n_dropped_screen: 0`（`:25`）。另外 197.96 在两个文件里末位不同
   （`…49376` vs `…48444`，相对差 2e-16）。苯侧 `ide_validation.json:43` 的 261.04 Ha 与 ab_compare 的 188.32 Ha
   不冲突（`full_pfrz −3.1004` vs `P_frz −4.0618 kcal/mol ⇒ 不同几何`），但别当同一个数引。
9. **[低] 证据只活在临时目录**：唯一那次复现 `scratch/STEPJ_v1_exact_accounting_missing.out`、
   τ=1e-13 那条 `nlcsplit/logs/*.out`、以及 `21723.206496881914` 这个字面值
   （`evidence/` 里的对应值是 `21723.206496881437`）——**全部被 `.gitignore` 屏蔽**
   （`scratch/`、`nlcsplit/logs/*`），克隆仓库的人一条都取不到。要引就得进 `evidence/`。

---

## 7. 限定后的措辞

**中文（给主代理的结论句）**：

> P2 那条线是否证——但范围要写明。在 P1 需要的 1e-6 kcal/mol 逐对精度上，本实现的带证明界层次屏蔽
> **在两次独立、每次计时块结束时外部可运行任务数为 0 的空载运行里，36 个计时样本无一快于全量和，
> 比值 1.03–12.8×**（正式归档那次给的是 1.08–10.28×，端点是单次测量，别当稳健量引）。
> 支撑它的不是墙钟：0/15 根对上判定树比大 gemm 便宜（oracle 上限省 0.0%）、近场占满 cross 点对的
> 100.0000%（15/15 根盒缝精确 0.0000 Å）、最小原子块对界仍比待判量松 2.4e5×（三个二聚体中最保守也 2.9e4×）、
> 达标 τ 下仍要算 84.4–95.4% 的 far 点对；再叠一条我这次新算的：**屏蔽路径的边际每点对代价本身就比全量和贵
> 2.0–2.3 倍**，所以"一个都不跳"的极限也要 2.3–2.6 倍时间，要打平必须把 far 保留比压到 29%/37% 以下，
> 而那需要比 τ=1e-8 更粗的容差——那时误差已经是目标的 1.5e4–3.8e4 倍。
> 外推限制：≤12 原子的刚性水链、网格 level 0–1（≤30,000 点）、这一套实现、这一台机器；
> **网格变密这个方向没测，而且现有数据显示比值随网格变密而下降**（5.42×→1.95×、10.25×→2.19×），
> 所以否证不能写成"任何体系、任何网格都不行"。另：同一批工件里出现过一次 0.893×，
> 它按 cross 口径只丢 0.045% 点对，省的是分块形状的钱不是屏蔽的钱——正文该主动交代。

**英文（若要落进稿件）**：

> P2 is a refutation, scoped: at the 1e-6 kcal/mol per-pair accuracy P1 requires, the certified hierarchical
> screening never beat the dense sum — 0 of 36 timed samples across **two independent runs** in which every
> sample recorded zero runnable tasks outside our own process tree at the end of its timed block
> (ratios 1.03-12.8x; the single archived run gives 1.08-10.28x, and those endpoints are single-sample).
> The verdict does not rest on wall clock: the tree is cheaper than the big gemm on 0/15 atom pairs (oracle
> ceiling 0.0% saving), the near field is 100.0000% of the cross point pairs (all 15 root box gaps exactly
> 0.0000 A), the smallest atom-block bound in a real dimer still exceeds the quantity it must judge by 2.4e5x
> (by 2.9e4x in the least extreme of the three dimers measured), and an accuracy-admissible tau still
> evaluates 84.4-95.4% of the far point pairs. Adding our own fit: the screened path's *marginal* cost per
> point pair is already 2.0-2.3x the dense path's, so even a tau that drops nothing costs 2.3-2.6x as much,
> and merely tying would require retaining under 29%/37% of the far work - a coarser tau than 1e-8, which is
> wrong by 1.5e4-3.8e4 times the target. Not covered: systems beyond 12 atoms, grids denser than level 1
> (<=30,000 points), other implementations - and in our own data the ratio *falls* as the grid densifies, so
> that direction is measured neither way. One contended-window sample in the same artefact family did print
> 0.893x; on the cross point-pair denominator it drops 0.045% of the pairs, i.e. it buys block shape, not screening.

**闸门措辞（替换 `p2.md:21, 55, 270` 的 "idle/unloaded machine"）**：
"on a box where every timed sample recorded zero runnable user tasks outside our own process tree at the
moment the block ended (single instantaneous check per block, threshold <=1; load-average readings 0.99-4.24
are self-induced by `OMP_NUM_THREADS=4`)"。

---

## 8. 我做了什么、没做什么

* 只读。没有修改任何已有文件；没有 `git` 写操作；`evidence/` 既有文件一律未动，且 4 份 MANIFEST 全部校验通过。
* 新建：`evidence/claims_audit/C_p2_refutation.md`（本件）、
  `scratch/audit_p2_refutation.py`（重算，A–H 八节）、`scratch/audit_p2_refutation.out`（其输出）。
* 未联网、未调云端模型、未提交任何作业、未跑 SCF（152–2,467 s 的 SCF 不在只读审计的允许范围里）。
* 所有数字都能从上面点名的工件行重算；`scratch/audit_p2_refutation.py` 一次跑完可复现 §1、§3、§4.1、§5 的全部表格。
