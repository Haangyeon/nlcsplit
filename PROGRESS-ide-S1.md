# 进展日志 · ide-qoder / S1：+0.138 kcal/mol 偏差归因判定

**协同约定**（与 PROGRESS-nlcsplit.md 一致）：append-only，只加自己条目；数字必须带来源脚本+日志。
**只读边界**：本任务全程只读 `nlcsplit/`、`ref/`、根目录 `*.md`；未编辑任何 `nlcsplit/*.py`、
`PROGRESS-nlcsplit.md`、`HANDOFF-*`、`STEP0-*`、`PLAN-*`；无 git 写操作、无删除、无远程/凭据、
未动 cn-qoder 的 `step_b_scan.py`/`step2_convergence.py`/`step_d_floor.py`。

**代码版本（快照）**：`NLCSNAP=/mnt/e/Project/GAMESS/scratch/ide_snapshot_20260928T224224Z`
（即 `scratch/IDE_SNAPSHOT_DIR` 指向）。快照内 `nlcsplit/nlc.py` md5 = `a1800277812945717c8b10c11b849ad8`，
与 `SNAPSHOT-MANIFEST.txt` 记录 **MATCH**；当前活树 `nlc.py` md5 相同（本任务仍一律用快照跑）。
（来源：`scratch/ide_s1_arith_check.py`）

**我产生的脚本**（均在 `scratch/`，`ide_s1_` 前缀）：`ide_s1_arith_check.py`、`ide_s1_confirm.py`、`ide_s1_mre.py`；
阶梯脚本 `ide_s1_grid_ladder.py` 为既有、由 runner 调用。

---

## [2026-09-28 23:10] [agent=ide-qoder/S1] [done] 判定：+0.138 是 (B) 核/公式差异，不是 (A) 网格离散化

### 一句话
显式双重和相对 libxc/ORCA 的 +0.138 kcal/mol 偏差**在网格完全收敛后不消失、且全部落在双积分本身**，
判为 **(B) 核/公式/数值处理差异**（置信度高）；`nlc.py` 的显式实现当前**不能当"无插值的真值"**。

### 1) 外部裁判复核（独立重算，未只信上游抄录）
来源：`ref/h2o_wb97xv.inp` L1 `! WB97X-V 6-31G*`；`ref/h2o_wb97xv.out` L54 `Program Version 6.0.1`、
L150 `libXC 6.2.2`、L450-451 泛函 WB97X-V、L657 `NL Energy, E(C,NL) : 0.042653836648 Eh`（L622-624 同值）。
换算（`scratch/ide_s1_arith_check.py`，K=627.509474）：
- ORCA 0.042653836648 Eh → **+26.76569 kcal/mol** ✓ 与上游一致
- libxc 0.0426528757 Eh → **+26.76508 kcal/mol**；ORCA−libxc = **+0.000603 kcal/mol** ✓（"6e-4"成立）
- β(b=6)=0.00484690 Ha/e⁻ = **3.0415 kcal/e⁻**；β·Nₑ(Nₑ=10) = **30.4148 kcal/mol**
两个独立实现（ORCA 走自身 post-SCF 网格 3858 点，与 PySCF 网格不同）互吻合到 6e-4。

### 2) bias(level) 阶梯表 — 同网格同密度，explicit 与 libxc 共享 X/W/ρ
来源：`scratch/ide_s1_grid_ladder.py` → 日志 `nlcsplit/logs/20260928T224554Z_ide-s1.out`（rc=0，`[runner s1] end 22:58:57`）。
单位 kcal/mol；bias=explicit−libxc；nl差=显式双积分 E_nl − libxc 隐含双积分(libxc_total−β·Nₑ)。

**orca-xyz（与 ORCA 严格同结构）**
| lvl | N | ∫ρ−Nₑ | E_loc | E_nl | explicit | libxc | bias | nl差 |
|--|--|--|--|--|--|--|--|--|
| 0 | 2216 | +0.00568 | +30.4320 | −3.5018 | +26.9302 | +26.7918 | **+0.1384** | +0.1211 |
| 1 | 9184 | −0.00004 | +30.4146 | −3.5113 | +26.9034 | +26.7655 | **+0.1379** | +0.1380 |
| 2 | 19520 | −0.00000 | +30.4148 | −3.5114 | +26.9034 | +26.7655 | **+0.1378** | +0.1378 |
| 3 | 29984 | +0.00000 | +30.4148 | −3.5114 | +26.9034 | +26.7655 | **+0.1378** | +0.1378 |
| 4 | 53072 | +0.00000 | +30.4148 | −3.5114 | +26.9034 | +26.7655 | **+0.1378** | +0.1378 |

**geomlib**：bias 序列逐位相同（0.1384/0.1379/0.1378/0.1378/0.1378），explicit 26.9301→26.9032、libxc 26.7654，
⇒ 偏差不依赖几何/坐标来源。

**相邻级差分（orca-xyz bias）**：L0→L1 −0.0005，L1→L2 −0.0001，L2→L3 −0.0000，L3→L4 −0.0000；相邻比 ≈1.0，**无单调向 0 收敛**。

### 3) 决定性补充（step-4）— 更细网格 + 严格电子数剥离局部项
来源：`scratch/ide_s1_confirm.py` → 日志 `nlcsplit/logs/20260928T230055Z_ide-s1confirm.out`（rc=0，`[runner s1confirm] end 23:07:51`）。
bias_strict = (β·Nₑ + E_nl) − libxc（局部项用**严格电子数**，不用数值 ∫ρ）；∫ρ项err = β·(∫ρ−Nₑ)·K。

| lvl | N | 保留 | explicit_strict | libxc | bias_total | bias_strict | nl_bias | ∫ρ项err |
|--|--|--|--|--|--|--|--|--|
| 4 | 53072 | 52980 | +26.9034 | +26.7655 | +0.1378 | **+0.1378** | **+0.1378** | +0.0000 |
| 5 | 80192 | 79690 | +26.9034 | +26.7655 | +0.1378 | **+0.1378** | **+0.1378** | +0.0000 |

**结论**：到 level 5（8 万点）网格已饱和（explicit 恒 26.9034、libxc 恒 26.7655）；用严格 Nₑ 剥掉局部项后
bias_strict=nl_bias=+0.1378、∫ρ项err=0.0000 ⇒ **整个 +0.138 来自双积分项本身，与网格、与 ∫ρ 数值无关**。

### 4) 分项归因
- **局部项 E_loc**：L0 = +30.4320（含 ∫ρ 过冲 β·0.00568 = 3.0415×0.00568 = **+0.0172** kcal），L1 起收敛到 +30.4148 = β·Nₑ；
  即 L0 的 bias 比 L1 高出的 +0.0005 中，局部项过冲贡献 +0.0172、被双积分在 L0 的低值（nl差 +0.1211 vs +0.1378）抵消，净 bias 仍 ≈0.138。**局部项误差随网格归零，非偏差主因。**
- **双积分 E_nl**：收敛到 −3.5114 kcal；libxc 隐含双积分 = 26.7655 − 30.4148 = **−3.6493** kcal；
  差 = −3.5114 − (−3.6493) = **+0.1379** kcal（= nl差/nl_bias）。即我们的双重和比 libxc 的少负 0.138（占 |E_nl| 约 **3.8%**），是系统性、非舍入。

### 5) 判读结论与置信度
**(B) 核/公式/数值处理差异。置信度：高。** 依据：
1. bias 跨 L1→L5 恒定 +0.1378，无向 0 收敛趋势（排除"粗网格不可用"）；
2. ∫ρ−Nₑ → 0、严格 Nₑ 剥离后 nl_bias 仍 +0.1378（排除密度数值/局部项）；
3. 两个独立实现（ORCA 独立网格 + PySCF-libxc）互吻合到 6e-4，把我们这版从零实现孤立在 +0.138；
4. 自包含 MRE（`scratch/ide_s1_mre.py` → 日志 `20260928T230503Z_ide-s1mre.out`，rc=0）在 level 1（N=9184，~2s）
   即复现 **gap=+0.1380 kcal/mol**。
唯一保留项：ORCA 内部亦链 libxc 6.2.2；故严格说"两个 libxc-backed 实现"而非两个完全异构裁判。但它们网格/代码路径独立，
仍不支持"我们的显式和才是真、libxc 恰好同向错 0.138"这一假设。定案需下面第 6 节的微扰实验。

### 6) 已排除 / 主候选 + 区分实验（按要求仅建议，未跑）
- **已排除（本数据即可判）**：
  - *网格离散化*：bias 恒定不降（第 2/3 节）。
  - *RHO_FLOOR 静默丢点*：bias 恒定时丢弃点数从 L4 的 92 增到 L5 的 502 却不改变 gap ⇒ 非丢点驱动；
    与 cn-qoder `step_d_floor.out`（floor 1e-8…1e-16 对片间项影响 1e-11）互证 ⇒ floor 假设关闭。
  - *自作用 i=j 对角项为主因*：对角项 ∝ w_i²，加密网格应使 gap 衰减；gap 平坦 ⇒ 非对角主因。
- **主候选（整体被积函数差异）**：
  1. **ωB97X-V 实为 rVV10**：libxc 对 `wb97x_v` 走 rVV10 的 ω0 低密度正则化，可能与 `nlc.py` 里教科书 VV10 的
     `w0=sqrt(C·σ²/ρ⁴+(4π/3)ρ)` 形式/系数不同。区分实验：直接对照 libxc 源码 rVV10 分支的 ω0、κ、σ 用法逐项核对 nlc.py。
  2. **σ 定义/幂次**：本实现 σ=|∇ρ|²（三分量平方和）、项为 C·σ²/ρ⁴=C|∇ρ|⁴/ρ⁴；若 libxc 用 C·σ/ρ^(4/3) 等变体则整体偏移。
     区分实验：固定密度把该项整体置零（纯 ρ 项）分别算 explicit 与 libxc，看差是否落在该项。
  3. **κ 前因子/幂**：`kap=b(3π/2)(ρ/9π)^{1/6}` 与 rVV10 的 κ 表达式差异。区分实验：按 rVV10 重定义 kap 后跑 L2，看 gap 是否归零。

### 7) 需要因此改写的 cn-qoder 在跑/已写结论
1. **`nlc.py` docstring "这里是 O(N^2) 的显式实现：它是'真值'"（L12）——论文前提**。按本判定：定位并修正第 6 节核差异前，
   explicit 单体 E_NLC 系统性偏高 +0.138，**不能当"无插值真值"**。（我无权改 nlc.py，交 cn-qoder 处理。）
2. **PROGRESS-nlcsplit.md L72-74 "libxc 插值核偏差随网格不消失…缺外部裁判"**：外部裁判已到（ORCA=libxc 到 6e-4）。
   归因需**反转**——离群的是**我们的显式实现**，不是 libxc 插值。cn-qoder "偏差随网格不消失、非离散化驱动"的**观察**与本任务一致，
   但"libxc 偏差"这个**标签**应改为"explicit 相对两实现的偏差"。
3. **PROGRESS-nlcsplit.md L96-98 Step3 "缺外部裁判(=T1)"**：T1 交付（见第 1 节数值），可勾除。
4. **凡以 explicit 单体/绝对 E_NLC 为锚点者**（例如给次二次方方案校准 target、或报告绝对 E_NLC）继承 +0.138 系统偏差；
   建议改锚 libxc/ORCA 或先修 nlc.py 再重测。二聚体片间 E_AB（cn-qoder 报跨 level 0→2 仅差 0.0019，网格钝感）
   受同一固定偏移影响**可能较小**，但绝对片内/单体项仍偏 +0.138，需在核修正后用同一 L2 网格复测确认交叉项是否也带此偏移。

### 8) 下一步建议
1. 让实现核对优先于任何"真值"用途：按第 6 节实验 1（对照 libxc rVV10 源码）先定性 VV10-vs-rVV10/σ/κ 三者谁是因，
   修 nlc.py 后以 ORCA +26.76569 / libxc +26.76508 为目标复现到 <1e-3 kcal。
2. 修正后，把 S1 阶梯（本日志 L0-L5）复跑一遍确认 bias→~0，作为"显式实现可信"的闸门，再谈片断分解绝对量。
3. 在此之前，论文中所有依赖 explicit 绝对值的前提降为"待定"。

### 9) 日志/产物清单（本任务）
- `scratch/ide_s1_arith_check.py`（外部裁判复核 + 快照 md5 校验，直接前台运行）
- 阶梯：`scratch/ide_s1_grid_ladder.py` → `nlcsplit/logs/20260928T224554Z_ide-s1.out`（rc=0）
- 补充：`scratch/ide_s1_confirm.py` → `nlcsplit/logs/20260928T230055Z_ide-s1confirm.out`（rc=0，含 L5）
- 复现：`scratch/ide_s1_mre.py` → `nlcsplit/logs/20260928T230503Z_ide-s1mre.out`（rc=0）
- 冒烟基线（既有）：`nlcsplit/logs/20260928T224427Z_ide-s1smoke.out`
