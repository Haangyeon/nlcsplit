# 进展日志 · ide-qoder（CN 版 Qoder 会话之外的 IDE 侧）

约定与 `PROGRESS-nlcsplit.md` 一致：append-only，抬头 `## [YYYY-MM-DD HH:MM] [agent=ide-qoder] [claim|done|finding|retract|ask]`。
本文件由 IDE 版写；cn-qoder 的 `PROGRESS-nlcsplit.md` 我不改，只读。

**防撞规则（本轮起我自己遵守，也建议 cn-qoder 遵守）**
- cn-qoder 正在改 `nlcsplit/*.py`（G2/G4/G5）。我的任何计算**先快照** `nlcsplit/` 到
  `scratch/ide_snapshot_<ts>/`，用 `PYTHONPATH` 指向快照，绝不 import 正在被编辑的活文件。
  本次快照：`scratch/ide_snapshot_20260928T224224Z`，清单在该目录 `SNAPSHOT-MANIFEST.txt`。
  ⚠️ 该快照之后 live `nlc.py` 已被改动（md5 `a180027…` → `0a5791…`），S2/S3 已知会。
- 我不写 `nlcsplit/*.py`、不 `git init`（那是 G1，归 cn-qoder），免得撞车。
- 我的日志写本文件与 `PROGRESS-ide-S*.md` 分文件，避免多方同时 append 同一个文件。
- 日志文件名一律 `YYYYMMDDTHHMMSSZ_ide-<tag>.out`，由 `scratch/ide_runner.sh` 生成（时间戳 + flock + MANIFEST 追加）。
  cn-qoder 那份 `202609dT141641Z` 的 `%d` 没展开，已在其文件中反映。
- ⚠️ 自我记录一条操作失误：23:35 那次我用整文件写入追加新条目，**把下面的 22:45 批次覆盖掉过**，
  现已按原文重建。以后我只用精确插入追加，不再整写本文件。

---

## [2026-09-28 22:45] [agent=ide-qoder] [claim] T1（外部裁判）+ T2 前置；另开 S1/S2 两个长任务

- **T1** 接手并完成，见下一条。
- **T2** 服务器算力外迁：**卡在凭据**（凭据只在用户手上，我不落盘）。我先不排队等待，
  改成本机并行跑（见 23:35 的 [status] 与下方资源实测）。
- **S1** 显式双重和 vs libxc/ORCA 的 **+0.138 kcal/mol 偏差归因**（本轮新暴露，优先级高于一切）。
- **S2** 苯二聚体 lvl0 的 E_AB / 超位置差（gemm 版已能跑动）。

## [2026-09-28 22:45] [agent=ide-qoder] [done][finding] T1 结论：**裁判方向是反的**

`ref/h2o_wb97x.out` 与 `ref/h2o_wb97xv.out` 我都读了。三条纠错 + 一条推翻性发现。

**(1) 不是 Psi4，是 ORCA 6.0.1。** 两份输出的抬头与 `.bibtex` 都是 Neese 的 ORCA。
HANDOFF §1.4 与记忆里"Psi4 输出"的标注错了。

**(2) HANDOFF 表 1.4 第 2 行引用错了文件：那是 ωB97X，不是 ωB97X-V。**

```
ref/h2o_wb97x.inp :  ! WB97X 6-31G*      → FINAL SINGLE POINT ENERGY -76.386592443579
ref/h2o_wb97xv.inp:  ! WB97X-V 6-31G*    → FINAL SINGLE POINT ENERGY -76.376956199429
```

HANDOFF 写"-76.3865924435790618（ωB97X-V 参照）"——**这个数是纯 ωB97X 的，ωB97X 里没有 VV10 非局域项**。
真正的 ωB97X-V 外部值是 **-76.376956199429**，与我们 PySCF 的 -76.3768906496 差
**6.6e-5 Ha = 0.041 kcal/mol**（不同网格，合理量级）。

**(3) 几何其实是同一套结构，HANDOFF 的"几何不同不可比"这条担心可以取消。**
两份 ref 输入几何相同：O(0,0,0)、H(±0.7569539314, 0.5855232618, 0)
⇒ r(OH) = **0.956983 Å**、∠HOH = **104.516°**。
`geomlib.h2o()` 用 0.9572 Å / 104.52° ⇒ Δr = 2.2e-4 Å，平衡点附近二阶项 ~1e-8 Ha，**完全可比**。

**(4) ⚠️ 最重要：ORCA 直接打印了 NL 项，它站在参照那边，不在我们这边。**

```
ref/h2o_wb97xv.out:622-624   SCF Energy: -76.419630275   NL Energy: 0.042653837
ref/h2o_wb97xv.out:657       NL Energy, E(C,NL) : 0.042653836648 Eh
```

| 来源 | E_NLC(水/6-31G\*) kcal/mol | 与我们显式和之差 |
|---|---|---|
| **ORCA 6.0.1 原生 DFT-NL（独立实现、独立网格）** | **+26.76569** | +0.138 |
| PySCF 原生核（旧文档误标为"libxc"）level 3/4 | +26.76509 | +0.138 |
| PySCF 原生核 level 1（`step_b.out`） | +26.7654 | +0.138 |
| **我们的显式双重和 lvl0/lvl1** | +26.9056 / **+26.9038** | — |

⇒ 当时结论（正确但标签错）：两个互不相关的实现吻合到 6e-4 kcal/mol，**outlier 是我们的显式双重和**。
"libxc 插值核有偏差"这个因果在 23:35 条目里被整体推翻，根因是配对方式。

## [2026-09-28 22:45] [agent=ide-qoder] [retract] 我上轮 P0-1 的量级

我说"两套几何导致 -0.2769 vs -0.3166 的 0.04 分歧"。cn-qoder 的修正成立：
那 0.04 里含 `pair_energy()` 少乘 2 的历史 + level 0 网格问题；两套几何本身在 lvl1 差 1e-4。
**工程问题（几何真值源分裂）仍然真实**，只是它当前的数值后果≈0。我这条撤回。

## [2026-09-28 22:45] [agent=ide-qoder] [ask→cn-qoder]

1. **在 S1 出结果前，请把 `exact`（显式双重和）当被审对象而不是裁判。** 你的 G4（floor 敏感性）与我的 S1
   高度重叠——我把 S1 限定在水单体 lvl0-4 的网格阶梯与项归因上，floor 归你，避免重复。
2. 我的 `nlcsplit` 快照策略如上；`scratch/ide_snapshot_*` 里的副本不是我改的源码。

## [2026-09-28 22:45] [agent=ide-qoder] [status] 资源实测与 T2 判断

- WSL `nproc` = **20**，`free -g` = 31 总 / 27 空闲。cn-qoder 在 `step_d_floor.py` 里按"这台机器只有 8 核"设
  `OMP_NUM_THREADS=2`。⇒ "本地算力弱"到底是 8 物理核 / 20 逻辑核的哪种，需要一条实测才敢写进计划。
- 真正需要服务器的是 **苯二聚体 lvl1** 和 S22 全集 lvl≥1（S2 实测外推见 23:35 条目）。
- 服务器凭据：待用户给。**我不申请、不记录、不写进任何脚本或日志。**
- 小 bug 上报：`logs/202609dT141641Z_step1.out` 文件名 `%d` 没展开，`MANIFEST.txt` 跟着错。

---

## [2026-09-28 23:35] [agent=ide-qoder] [finding] ⚠️ 全仓最高优先级：Φ 的 g/g′ 配对方式写错了，所有在跑的数都作废

两个子代理（S1 网格阶梯、S3 核取证）+ 我自己的独立复核，结论一致且是**定案级**：

**根因**：`nlcsplit/nlc.py` 的 `pair_energy()` 用**交叉配对**
`g = w0_j·R² + κ_i`，`g' = w0_i·R² + κ_j`。
参考实现（PySCF 原生核、ORCA 原生 DFT-NL）用**同中心配对**
`g = w0_i·R² + κ_i`，`g' = w0_j·R² + κ_j`。
两者在对角元 R=0 时相同，非对角且 ω_i≠ω_j 时不同；差值的解析形式
= `Σ_ij (ω_i−ω_j)(κ_i−κ_j)R²` 那一项，因此**随体系增大而增大**，不是常数。

**证据链（三级，都不是自证）**
| 级别 | 实验 | 结果 | 出处 |
|---|---|---|---|
| 合成 6 点箱（ρ、∇ρ 各处不同） | 手算两配对 vs `numint._vv10nlc` | same−PySCF = **−2.8e−19 Ha（逐位相同）**；cross−PySCF = 明显非零 | `scratch/ide_s3_pairing.py` → `logs/20260929T001615Z_ide-s3.out` |
| 均匀气 4 点（σ=0） | 两配对恒等 | 与 PySCF 差 0.000e+00 ⇒ ω/κ/β 系数全对，问题只在配对 | 同上 |
| 真实水网格 L1 | 三方对比 | cross−PySCF **+0.1378**，same−PySCF **−0.0000** | 同上 |

**S1 的先置排除**（`logs/20260928T224554Z_ide-s1.out`、`20260928T230055Z_ide-s1confirm.out`）：
+0.138 不随网格消失（L0→L5：0.1384/0.1379/0.1378/0.1378/0.1378），与 `RHO_FLOOR` 无关，
与"对角自作用主导"无关 ⇒ 只能是核本身的差异。S3 把它定位到了配对。

**我自己独立复核的一条（S3 说"参照不是 libxc"，我验了）**：
```
grep -n _vv10nlc .../pyscf/dft/numint.py  →  471: def _vv10nlc(...)   539: libdft.VXC_vv10nlc(...)
grep -c vv10      .../pyscf/dft/libxc.py   →  0
```
⇒ PySCF 的 NLC 走它**自带的 C 核**（`pyscf/lib/dft/`），`libxc.py` 里根本没有 VV10。
所以本仓（含 HANDOFF、STEP0、PLAN、PROGRESS、我的上一轮评审）里所有写作"libxc 给的参照值"，
**实际是 PySCF 原生核**。第二个裁判是 ORCA 自带的 `DFT-NL`（Hujo & Grimme JCTC 2011, 7, 3866；
b/C 打印在 `ref/h2o_wb97xv.out:462-463`，NL 能量在 `:657`），不经 libxc。
⇒ 裁判确实有两个且互不依赖，但**名字都标错了**，"libxc 插值核有偏差"这个说法整体作废。

**偏移不是常数**（S3 `kernel_variants`）：H₂O +0.1379 / CH₄ +0.1346 / Ar +0.4182 / 苯 +0.9057 kcal/mol。

## [2026-09-28 23:35] [agent=ide-qoder] [retract] 我自己此前两条

1. 上一轮评审把"libxc 偏差随网格不消失"列为**正面结果**、并说它证实了显式实现的必要性 ⇒ 观察对、**因果与标签全反**。
2. 我在 S2 任务书里让代理把 +0.138 当"普适固定偏移、差值里大概率抵消" ⇒ **不成立**（体系相关，苯 0.91）。
   因此 S2 交回的苯二聚体 `P_frz=-2.9581 / CP=-3.1717 / relax/CP=-0.001` 是 **cross 核下的数，全部作废重算**，
   仅"两个二聚体的 relax/CP 都≈0"这一定性趋势值得在修正后复验。

## [2026-09-28 23:35] [agent=ide-qoder] [ask→cn-qoder] 紧急，请在你下一个 job 之前处理

1. **`step2_convergence.py` / `step_c_relaxation.py` / `step_d_floor.py` 现在跑的都是 cross 核。**
   `step_d_floor` 的 floor 判据本身仍然有效（floor 与配对独立），但 `P_frz`/`E_nl` 的**绝对值**要作废；
   `ARCHIVED = {1: (-0.6333, -7.6804), 2: (-0.6335, -7.6817)}` 这个存档参照是错核下的数，别拿它当验收基准。
2. **HANDOFF §1.3 的那条"⚠️ 已被数值实验否定"要再翻回来**：`dftvv10.src:231` 的交叉配对**确实是 bug**
   （当初的"量纲不通"质疑形式错了，但结论方向对了）。GAMESS 树里同一份 cross 公式一并中招。
3. 建议修法（两行）：`pair_energy` 里
   `g = R2*w0A[sl][:,None] + kA[sl][:,None]` / `gp = R2*w0[None,:] + kapB[None,:]`，
   即两侧都用各自的 (ω, κ)。验收：**同一网格上 E_nl 与 `numint._vv10nlc` 隐含值差 < 1e-10 Ha**，
   并在合成 6 点箱上复现我上面的 2.8e-19 逐位一致。
4. 我这边不碰 `nlcsplit/*.py`（所有权归你）。修好的候选模块与回归测试我放在
   `scratch/ide_s4_nlc_v2.py`，直接可当补丁来源。

## [2026-09-28 23:35] [agent=ide-qoder] [status] 本轮派出的子代理与在跑任务

| 任务 | 载体 | 状态 |
|---|---|---|
| T1 外部裁判 | 我自己 | ✅ 完成，且推翻了自己的结论（见上） |
| S1 网格阶梯 + 偏移归因 | 子代理 | ✅ 完成 → 判为核/公式差异 |
| S3 核根因 + 裁判独立性 | 子代理 | ✅ 完成 → 定位为交叉配对错；裁判=PySCF-native+ORCA-native |
| S2 苯二聚体 + server_bundle | 子代理 | ✅ 完成（数值因核错作废，bundle 有效） |
| S4 修正核全体系重算 | 子代理 | 🔄 运行中 |
| T2 服务器实连 | 我 | ⛔ 等用户凭据；包已备齐 `scratch/server_bundle/` |
| Step 0 两前置（JCTC 正文 / WoS-Scopus） | 我 | ⛔ 等用户机构权限 |

苯 lvl1 显式双重和外推 **≈7.3 h**（N₁=89088 实测建网格得到，非估），⇒ 服务器确实需要。
