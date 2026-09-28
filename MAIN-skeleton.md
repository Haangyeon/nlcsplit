# 主篇骨架（A 案）— 每个数字都带出处，"待补"即真空洞

工作标题（二选一）：
- **Fragment-Resolved Nonlocal Correlation: Pair Attribution of the VV10 Term and Its
  Different Roles in Hydrogen-Bonded and Dispersion-Bound Complexes**
- Is the Nonlocal Correlation Term the Dispersion? A Pair-Resolved Decomposition of VV10

一句话主张：**VV10 非局域关联项可以无歧义地按片段对归属；拆开看，它在色散主导体系里是
交换-关联中唯一的吸引来源，而在氢键体系里只承载一成多——所以"非局域项 = 色散"这个默认
等式必须分体系对待。**

写作纪律：下文每个数字后面的方括号是它的证据来源（日志/脚本/commit）。
没有来源的数字一律写成"待补"，不进稿。

---

## 1. Introduction — 缺口在哪

- 现有程序把非局域关联项**折叠成点值再插值加速**，成对结构在加速后不可恢复；
  因此拿不到"哪一对片段贡献了多少"。（代码事实：`pyscf.dft.numint.nr_nlc_vxc` 调
  PySCF 原生 C 核 `libdft.VXC_vv10nlc`，不经 libxc —— 我读源码确认 [nlc.py 头注]）
- **先例查重**：OpenAlex `title_and_abstract.search` 十组检索式，其中
  `"nonlocal correlation" AND "energy decomposition"` = **0**、
  `"vdW-DF" AND "energy decomposition"` = **0**、
  `"nonlocal correlation" AND "many-body expansion"` = **0**、
  `VV10 AND "atom pair"` = **1**、`VV10 AND decomposition` = **3**
  [RESEARCH-20260929-lit.md §1，脚本 scratch/lit_pipeline.js]
- **最近的先例是竞品而非重复**：Dasgupta–Paesani 组 JCTC 2023
  [10.1021/acs.jctc.3c00903；全文 ChemRxiv 绿色 OA 10.26434/chemrxiv-2023-nc64t]
  用**二阶 ALMO-EDA**（E_Int = E_Pol + E_Frz + E_CT + E_Disp）把
  **−VV10 整体当作色散能**，没有在这一项内部做片段/原子对归属。
  ⇒ 我们的对象是他们分解里那个"整块"的内部结构。
- ⚠ 仍待补：WoS/Scopus 正式一轮（不能只靠 OpenAlex）。

## 2. Method

1. **核与约定**：`w0=√(C|∇ρ|⁴/ρ⁴+4πρ/3)`，`κ=b(3π/2)(ρ/9π)^{1/6}`，
   `Φ=−3/(2gg'(g+g'))`，`g=w0(r_i)R²+κ(r_i)`（**同中心配对**）。
   交叉配对 `g=w0(r_j)R²+κ(r_i)` 偏高 +0.13(水)/+0.42(Ar)/+0.91(苯) kcal/mol，
   是错的 [step_e_kernel.py；IDE 的 S3 合成箱独立复现：same-centre 与 PySCF 内核差 −2.8e−19 Ha]
2. **半份/整份约定**：`pair_energy(A,B)` 给半份，`inter[(A,B)]=2·blk`，
   故 `E_nl=Σintra+Σinter` 可加性严格成立（实测残差 **0.00e+00 至 3.5e−18 Ha**）
   [logs/20260929T010500Z_step1_geomfix.out；CentOS step_c.out]
3. **恒等式（方法论要点）**：`E_NLC = 双重和 + β∫ρ`，而 β 为常数、∫ρ ≡ 电子数，
   所以 **β∫ρ 在任何 superposition 差中精确抵消**（实测 ΔE_loc = +3.736e−05 kcal/mol，
   level 1）⇒ 只对双重和做片间分解是严格的，不是近似
   [step_f_dispersion.py 输出；step_c 独立复现同一结论]
4. **归属方案**：Becke / Becke 半径修正 / Becke–Treutler / Stratmann + 最近原子硬分区，
   全部走 PySCF `gen_grid.get_partition` + `radi.BRAGG_RADII`。
5. **远区裁剪**：`rho_floor` 默认 1e−12；1e−8…1e−16 五档之间片间项跨度 **4e−11 kcal/mol**，
   代价是丢弃 10.7–22.6% 的网格点（其上电子数 ≤2.3e−6）[step_d_floor.py]

## 3. Results

### 表 1 验证链
| 对照 | 差 (kcal/mol) | 出处 |
|---|---|---|
| 本包 vs PySCF 原生核（7 体系 × level 1） | ≤ **+0.0015**（苯 −0.0038） | CentOS step_b.out |
| 本包 vs ORCA 6.0.1（水单体） | **6e−4** | ref/h2o_wb97xv.out |
| 跨版本 2.12.1 vs 2.14.0 | 网格点数差 10%，能量分项**逐位一致** | step_f 两边输出 |
⇒ 诚实表述：独立程序只有 ORCA 一个；PySCF 原生核与我们同属一库。
要凑第三个独立实现需直接调 libxc `xc_nlc_vxc` 或 Psi4 —— **待补**。

### 表 2 不确定度三分解（这才是"归属可辩护"的对象）
| 来源 | 幅度 | 判读 | 出处 |
|---|---|---|---|
| 网格 level 0→2 | ≤ **0.008** kcal/mol | 收敛，非问题 | CentOS step2.out |
| 基组 sto-3g→aug-cc-pVDZ | **0.175** | 是物理依赖，须看是否趋 CBS | 同上 |
| 归属方案（4 种） | 水 lvl1 **0.040 (7.7%)**；氨 **0.046 (6.9%)**；甲烷 **0.008 (1.6%)** | 主误差条 | step1_geomfix.out；step_h 冒烟 |
**新观察（可当一个小结论）**：方案不确定度**随体系类型变化** ——
氢键体系 ~7%，纯色散体系 1.6%。

### 表 3 两体可分性（P_frz vs CP）
| 体系 | P_frz | CP | P_frz/CP | relax/CP | 出处 |
|---|---|---|---|---|---|
| 水（构造初始, lvl0） | −0.5316 | −0.5226 | **1.017** | 1.4% | CentOS step_c.out |
| 水（**ωB97X-V 优化后**, O···O 2.901 Å） | −0.5975 | −0.5828 | **1.025** | 0.4% | 同上 |
| 苯 sandwich | −3.1025 | −3.3918 | **0.915** | 0.0% | 同上 |
⇒ 冻结密度片间项吃掉全部超位置差；弛豫是**反向小修正**（比值可 >1，不可讲成正交相加）。

### 表 4 核心化学结果：XC 内部谁在吸引谁在排斥
| 体系 | ΔE_xc(半局域+精确交换) | ΔE_NLC | ΔE_xc 总 | 出处 |
|---|---|---|---|---|
| 水二聚体 lvl1 | **−2.443** | −0.515 | −2.958 | step_f（两台机器逐位一致） |
| 苯 sandwich lvl0 | **+2.620（排斥）** | **−3.258** | −0.638 | CentOS step_f_benz.out |
| 甲烷二聚体 lvl0 | **+0.32（排斥）** | −0.524 | −0.203 | step_h 冒烟 |
**外部对照（带 DOI）**：该文 ωB97M-V 在苯二聚体平衡几何给出的色散分量 **−3.69**
（PBE-VV10/revPBE-VV10 −3.75、revPBE-D3 −3.80、PBE0-VV10 −3.34）
[10.1021/acs.jctc.3c00903 正文 612–619 行]；我们 −3.258，差 **0.43 kcal/mol（11%）**，
可由泛函代差 + 基组(6-31G\* vs def2-QZVPPD) + 几何解释。
⇒ **推翻**"文献色散 −1.4、我们大它 2.3 倍"的说法：−1.4 更像净相互作用能
（该文明确写苯二聚体净能典型 2–3 kcal/mol，是色散被 Pauli 排斥抵消后的余量）。

### 待补（按优先级）
1. S22 子集 level 1 全表（CentOS 批4 在排）——目前只有 3 个体系的 level 0
2. 基组阶梯 def2-SVP/TZVP 两档 → "趋 CBS"判据（step_g 在跑）
3. 其余体系的 CCSD(T)/CBS 色散分量参考值（水/甲烷/氨-水/苯-水），带 DOI
4. 图 1–3（数据齐了就能画）

## 4. Limitations（必须自己先说，别等审稿人）
- **不是 EDA**：没有分离静电/交换/极化/电荷转移，没做 BSSE-CP 校正。
  我们只给 ΔE_xc 的两分（非局域 vs 其余）+ 片间/片内成对结构。
- **非局域项 ≠ 色散**：这正是本文的结论之一，不是缺陷，但标题与摘要不能含糊。
- 独立裁判目前只有 ORCA 一个。
- 归属方案带来的 7.7%（氢键体系）系统不确定度是硬上限，不因网格加密而消失。

## 5. 代码与可复现
包 `nlcsplit`（Apache-2.0，无 GAMESS 代码），每个表对应一个 `step_*.py`，
日志带 UTC 时间戳；几何来源 GMTKN55 官方仓库 [scratch/lit/get_s22.sh]；
README 的 quickstart 输出即本文数值之一（−0.5237）已核对。
