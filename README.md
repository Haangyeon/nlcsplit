# nlcsplit —— 非局域关联能的片段-成对分解

把 ωB97X-V / ωB97M-V / VV10 / rVV10 里的 **非局域关联项（VV10 双重和）** 按片段归属
拆开：给出每个片段的自身项 E_AA、每对片段之间的成对项 E_AB，以及它们的和与
PySCF 原生核的总量对照。纯 Python + NumPy，后端用 PySCF 出密度与网格。
（跨**程序**的锚点已建立：ORCA 6.0.1 对本文报告的八个体系全部核过，见下面"它准不准"。）

**不含任何 GAMESS 代码**（GAMESS 许可证不允许再分发），也不依赖 GAMESS。

## 安装

```bash
pip install .            # 依赖 numpy 与 pyscf>=2.12
python -m pytest -q nlcsplit/tests                    # 65 项：45 秒级 + 20 项 slow
python -m pytest -q -m "not slow" nlcsplit/tests      # 45 项，本机约数秒
```

（上面的计数按 `--collect-only` 实测：源码树收集 **65** = 45（`-m "not slow"`）+ 20（`-m slow`）。发布 wheel 不含 `test_fastpair_ide.py`（其 import 的 `fastpair_ide.py` 是对照件，不随包分发），那 20 项（18 秒级 + 2 slow）在 wheel 里没有，故 wheel 上是 45 = 27 + 18。）

## 快速上手

`examples/quickstart.py`（下面的输出就是它跑出来的，ωB97X-V/6-31G\*，水二聚体，网格 level 1）：

```python
from pyscf import gto
from nlcsplit import partition, nlc, geomlib

mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", unit="Angstrom", verbose=0)
mf, *_ = partition.scf_grid(mol, xc="wb97x_v", level=1, basis="6-31g*")
b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]

coords, weights, owner = partition.atom_partition(mol, level=1, scheme="becke")
ao  = mf._numint.eval_ao(mol, coords, deriv=1)
rho = mf._numint.eval_rho(mol, ao, mf.make_rdm1(), xctype="GGA")
sigma = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2

res = nlc.fragment_decomposition(coords, weights, rho[0], sigma,
                                 geomlib.FRAGS["(H2O)2"], b=b, C=C, owner=owner)
```

```
inter[(0,1)] = -0.5237 kcal/mol      # 片间成对项（完整一份）
intra        = -3.5457 -3.7437       # 两个片段各自的自身项
E_nl         = -7.8130   E_loc = 60.8303   E_total = 53.0172
```

`E_total = E_nl + E_loc` 才等于程序里的非局域项总量；`E_loc = β∫ρ` 是单电子密度的
一次项，在任何"复合物 − Σ 单体"的差里**精确抵消**（∫ρ 恒等于电子数）。

## 约定（读源码前必看）

| 约定 | 内容 |
|---|---|
| 核 | VV10：`w0=√(C·σ²/ρ⁴ + 4πρ/3)`，`κ=b(3π/2)(ρ/9π)^{1/6}`，`Φ=−3/(2gg'(g+g'))` |
| 配对 | `g = w0(r_i)R² + κ(r_i)`、`g' = w0(r_j)R² + κ(r_j)`（**同中心**配对，与 PySCF 原生核一致；跨程序一致性已在八个体系上用 ORCA 6.0.1 的 `NL Energy, E(C,NL)` 核过，见"它准不准"）。旧的交叉配对 `g=w0(r_j)R²+κ(r_i)` 水偏高 +0.138、Ar +0.42、苯 +0.91 kcal/mol，保留只为做定义敏感性对照 |
| 半份 | `pair_energy(A,B)` 返回 **半份** 成对项；`fragment_decomposition` 里 `inter[(A,B)] = 2·blk` 是完整一份，故 `E_nl = Σintra + Σinter` 可加性严格成立（实测残差 ≤6.94e-18 Ha） |
| 远区 | `rho_floor`（默认 1e-12）以下点不参与双重和；片间项对这一裁剪不敏感。水二聚体（构造几何, 6-31g\*, becke, `step_d_floor.py`）扫 floor 1e-8…1e-16 五档：验收区间 floor=1e-10…1e-14 三档跨度 **level 1 = 2.1e-11、level 2 = 4.2e-11 Ha**（日志把这两个数打在括号里，单位是 Ha；同一行的 kcal/mol 读数是 0.000000）；含 1e-8、1e-16 端点的全五档跨度按 `P_frz` 最大单点偏移 ~1e-8 kcal/mol、四舍五入到 0.000000、四舍五入到 0.000000 ⇒ floor 在哪档都可当实现细节。代价是丢 10.7%（lvl1,1e-16）–22.6%（lvl2,1e-8）的点 |
| 测度 | `partition.partition_factors` 返回的 `base_w` **不是**空间测度，别拿它直接做软归属。每个原子的径向网格都铺到整个分子，拼接后 `Σ base_w·h` 把 h 积分约 natm 遍——而且不是恰好 natm：H2O2/6-31g\*（6 原子）上对一个单位高斯（解析值 π^{3/2}）实测 1.0738 / 1.0125 / 0.9969 倍于 `natm·π^{3/2}`（level 1/2/3）。正确写法按 owner 掩膜：`Σ_{i: owner(i)=a} base_w_i·S[i,a]·h`，它对 a 求和复现解析值到 1.5e-5 / 1.8e-7 / 到打印位相同 相对；`base_w/natm` 这种"除以原子数"的补丁按片段仍偏 7–13%，不要用。本包生产路径（`step_h_s22.py`、`step1_validate.py`、`examples/check_soft_partition.py`）走 `atom_partition` 的权重，不受影响；坑与锚都在 `nlcsplit/tests/test_partition_factors.py` |

## 它准不准

* **三层裁判，分开说**：
  1. *同库内*：总量对照走 PySCF 原生 VV10 核（`numint.nr_nlc_vxc` →
     `libdft.VXC_vv10nlc`，**不经 libxc**）。水单体 level 1 上同一张网格、同一份密度，
     我们与原生核差 ≤6e-6 kcal/mol（≈1e-8 Ha）。⚠️ 这两个实现同属 PySCF 一个库，
     所以它只证明"我们的算术没错"，不证明"VV10 我们理解对了"。
  2. *跨程序*：**已经建立**。ORCA 6.0.1 对 `! WB97X-V` 原生打印
     `NL Energy, E(C,NL)`，24 份 run 覆盖本文报告的八个 S22 体系（每体系复合物 +
     两个单体），八个 ΔE_NLC 全部在 1% 以内（0.067%–0.952%，最大绝对差
     0.0416 kcal/mol）。逐对数值不手抄，由
     `evidence/orca_widen/generator_cross_program_table.py` 从
     `evidence/orca_run/`、`evidence/orca_widen/`、`nlcsplit/logs/step_h.json`
     现读现算，输出在 `evidence/orca_widen/cross_program_table.txt`。
     对照组：`evidence/orca_control/h2o_wb97x.out`（ωB97X，不带 `-V`）里
     **没有**那一行 ⇒ 那个标签是 VV10 专属，不是通用 DFT 输出。
     两侧网格不一致（ORCA 用 Lebedev-110 / IntAcc 4.004，PySCF 用 `grids.level=1`），
     所以这个差是"网格 + 实现"的联合残差，不归于任何一方。
  3. *归属裁判（跨程序给不了的那一层）*：`evidence/attribution_referee/`。第二个程序
     能核"这项值多少"，核不了"这项归谁"——它根本不做归属。所以这里换到一个**由构造
     给出无归属精确值**的体系：两个归一化高斯（各 4 电子，z 轴上 ±sep/2），`Phi` 只用
     总密度搭一次，`I_XY = ∫∫ ρ_X Φ ρ_Y` 按密度因子成对取。那个定义里没有 Becke 权重、
     没有网格指派、没有片段所有权，且 `E_NL = ½(I_AA + I_BB) + I_AB` 恒成立。三条独立
     路线（3-D 笛卡尔张量积、绕键轴 5-D 柱约化、以密度因子作重要性函数的蒙特卡洛）。
     结论分两半：**喂精确密度因子时，本包的求和代码复现 `I_AB` 到最差 7.96e-7 Ha**，
     低于参照自己的合成不确定度 U = 1.060e-5 Ha（0.00665 kcal/mol，由三个实测误差条拼
     出来）——算术这一半过了，而且走的是不共用我们库的路。喂生产用的 Becke/owner 指派
     时同一个代码离 `I_AB` 有 1.68e-8 ~ 1.26e-4 Ha（0.00001–0.0788 kcal/mol），且换到
     另一套不相交节点上偏差不变 ⇒ 差在归属规则，不在网格。**分辨率如实报**：12 个构型里
     只有 5 个 |偏差| > U（2/3/3/4/12 倍），其余 7 个比参照自身的误差条还小，那部分这个
     裁判**不能**替归属背书，只能说分辨不出。密度是合成的、同核等指数，正对照
     （§3.5 那个已知错的配对）在这儿只移动 0.0052 kcal/mol，与已分辨的偏差同量级 ⇒
     这是台分辨率有限的仪器，不是高分辨谱仪。两次独立整跑：两份表逐字节相同，两份
     machine-readable 结果逐字段比，差异只在计时字段与 worker 数。
* **这条锚点曾经是个假数，教训记在这儿**：本 README 与论文骨架早期都写过
  "与 ORCA 6.0.1 差 6e-4 kcal/mol"，2026-09-29 回读输出后发现被引的那份文件
  **根本没有单列的非局域项**（只有 `EX` 与合计 `EC`），那个数在仓库里也找不到出处，
  于是撤回。真正失败的不是检验，是**找数的方法**：我们在输出里搜
  "nonlocal" 和 "VV10" 这两个词，而 ORCA 把这个量标成 `NL Energy, E(C,NL)`。
  （顺带：搜到的 `E(VV10-nl)` 那一列是双杂化泛函的 PT2 关联项，另一个物理量。）
* **libxc 当不了裁判，不是没试**：本机两份 libxc（conda-forge 5.2.3 与 PySCF 自带的
  7.0.0）在十三个非局域入口点里只导出 `xc_nlc_coef`，没有 `xc_nlc_vxc`、没有 `xc_run`
  ——与 libxc 自己的说法一致：这类 vdW 项"不能用交给 Libxc 的局域密度信息求值，
  必须由调用程序处理"。所以它只给 (b, C) 参数，不给积分的独立数值。Psi4 本机取不到。
* **跨版本/跨机器复现**：PySCF 2.12.1（本机 WSL）与 2.14.0（远端 CentOS）在同一 level 下
  网格点数不同：官方水二聚体、level 1、分区网格，复合物 **18336 → 20248（+10.4%）**，
  而同一份日志里 `E_NLC=+52.9345`、`E_xc(其余)=-11757.5276`、单体 `+26.7636/+26.7644`
  **逐位一致** ⇒ 能量对网格已收敛，点数差是 PySCF 网格构造本身改了。（曾有两版错配：
  `18368` 是把 18336 抄错；`19936 vs 20248 = 1.6%` 是拿**构造几何**的点数去比**官方几何**，
  把几何差混进了版本差。两条都在 `paper/main.md` §2 记了出处。）
* **网格收敛**：同一基组内 level 0→2 的片间项散布 ≤0.008 kcal/mol。
* **已知最大不确定项**：人为的归属方案。同一体系同一网格，Becke / Becke 半径修正 /
  Becke–Treutler / Stratmann 四种方案的片间项跨度：水（构造几何, lvl1）
  **0.040 kcal/mol（|E_AB| 的 7.6%）**；八个 S22 体系（官方几何, lvl1,
  `nlcsplit/logs/step_h.json`）上是
  **0.004–0.247 kcal/mol，相对 0.8%–18.2%，且与体系类型无规律**
  （最小是甲烷二聚体 0.004，最大是苯-水 0.247）⇒ 误差条必须逐体系给，
  一个统一百分比会把甲烷二聚体说错二十倍。
  论文里它应当作为误差条报告，而不是当作通过/不通过的门槛。

## 不能拿它做什么

* **非局域项 ≠ 物理色散。** 官方几何的水二聚体上 `ΔE_NLC = −0.593`，只占
  `ΔE_xc = −3.708 kcal/mol` 的 16.0%；同一个二聚体的构造几何上 `ΔE_NLC = −0.515`
  ——占比随构型走（同一对分子的两种苯二聚体几何给出 97% 与 52%），所以这里没有
  一个"VV10 占色散多少"的通值。甲烷那一行更直接：两项符号相反
  （非局域 −0.517 对半局域余项 +0.285），比值 |ΔE_NLC/ΔE_xc| = 2.2，**分母是两者相消后
  的小余量，占比在该体系上没有意义** —— 包自己有条规则：该比值 > 2 就
  只报两个绝对项、不报占比（`step_f_dispersion.py`），所以论文那一格写的是
  "n/a (see note)"。其余部分在半局域交换-关联 + 精确交换里，而那部分同时混着
  静电与交换排斥。
  本包不做 SAPT/EDA 意义上的分解（也没把静电与交换排斥分开）；
  表 1 的主张是**冻结密度下的叠加差**，未作 BSSE/CP 校正——
  level-2 全 counterpoise 只在六个 ≤17 原子的体系上另外跑过
  （`evidence/l2cp/`），用来检查片间项对校正的敏感性，不是本文报告的量。
* 不做梯度/优化（`step_c_relaxation.py` 里的有限差分/解析梯度对照只是内部验证手段）。
* 不给 rVV10 的 τ 版本 `w0`（当前只实现 σ 形式的 VV10；换 rVV10 需要动能密度）。

## 目录

```
nlcsplit/            包本体：nlc.py(核+分解) partition.py(网格与归属) geomlib.py(几何)
nlcsplit/tests/      pytest：秒级自检 + 标记 slow 的回归/外部对照
nlcsplit/examples/   可运行示例
nlcsplit/step_*.py   证据生成脚本（论文每张表/图对应一个，输出在 nlcsplit/logs/）
```

## 许可

Apache-2.0，见 `LICENSE`。

## API（四个入口，够用）

| 入口 | 给什么 | 要注意 |
|---|---|---|
| `partition.scf_grid(mol, level, xc, basis)` | `(mf, coords, weights, rho, sigma)`：一次自洽场 + PySCF 常规网格上的密度与 σ | 网格与 SCF 用同一 `level`，别混档 |
| `partition.atom_partition(mol, level, scheme)` | `(coords, weights, owner)`；`weights` **已含**分区因子 | `scheme` 四选一：`becke` / `becke-becke-rad` / `becke-treutler` / `stratmann` |
| `partition.partition_factors(mol, level, scheme)` | `(coords, base_w, S[N,natm])`：逐点**多中心**因子，`Σ_a S[i,a] = 1` | 内置两条断言，不过直接抛错，不返回"看着对"的数组（详见下） |
| `nlc.vv10_fields(rho, sigma, b, C, rho_floor)` | `(w0, kap, keep)`：VV10 场量与远区保留掩码 | `keep` 是掩码不是权重，传给下游时别当乘数用 |
| `nlc.pair_energy(coords, wr, w0, kap, iA, iB, pairing=...)` | 一个 (A,B) **半份**块：½ Σ_{i∈A} Σ_{j∈B} | 默认 `same-centre`；`cross` 只作定义敏感性对照，偏高 0.14–0.91 kcal/mol |
| `nlc.fragment_decomposition(...)` | `{'intra','inter','E_nl','E_loc','E_total','n_dropped'}` | `inter[(A,B)]` 是**整份**（= 2×半份），所以 `E_nl = Σintra + Σinter` |

### `partition_factors` 的两条内置断言

```python
coords, base_w, S = partition.partition_factors(mol, level=1, scheme="becke")
```

1. `Σ_a S[i,a] == 1` 逐点成立——生产代码里的阈是 `assert err < 1e-12`（`partition.py:154`），测试同阈（`test_partition_factors.py:29`）；
2. `base_w[i] · S[i, owner(i)]` 必须逐点等于 **PySCF 自己**的
   `gen_grid.get_partition` 权重——按 `base_w` 归一的相对差 `< 1e-12`、逐点误差按总权累积 `< 1e-13`（`partition.py:163,166`）；测试里 `test_partition_factors.py:33,34` 取绝对差 `< 1e-11`、累积 `< 1e-14`。

> 这两条此前在 README 里写成"实测最大偏差 4.4e-16 / 实测 8e-13 绝对值（四方案 × level 0/1/2）"。全库 grep：`4.4e-16`、`8e-13` 在 `nlcsplit/logs/`、`evidence/`、`PROGRESS-*.md` 里 0 命中，没有任何工件记录这两个实测值——上面给的是断言**实际使用的阈值**，不是读数。快测试覆盖四方案 × level 0，level 1/2 在 `@pytest.mark.slow` 档（`test_partition_factors.py:37-43`）。

第 2 条是**外部锚**：比对对象是 `libdft.VXCgen_grid` 的输出，
不是本仓库另写的一份公式，所以它不算自证。

两条容易踩的口径，这里写死：

* **软归属必须喂分区后的 `weights`（或 `atom_partition` 的 `w`），不要喂 `base_w`。**
  `base_w` 是各原子子网格的**原始体积元**，拼接它**不是**"重叠区把同一点重复计数"——拼接点表里没有重复坐标（`partition_factors` 返回的点表与 `atom_partition` 相同）；真正的机制是每个原子的径向网格都铺到**整个分子**，于是每个子网格都把同一个空间函数积了一遍。而且这个倍率**不是常数**：对水二聚体（构造几何 `geomlib.h2o_dimer()`）的真实密度 ρ，`Σ base_w·ρ` 在 level 0/1/2/3 = **100.19 / 690.26 / 279.08 / 94.75**（ne=20，隐含倍率 5.0 / 34.5 / 14.0 / 4.7，非单调、也不收敛到 natm=6），所以"除以原子数"这类补丁错得更远。钉住它的是 `nlcsplit/tests/test_partition_factors.py` 里两条：`test_soft_attribution_owner_masked_matches_analytic_gaussian`（光滑高斯锚，按 owner 掩膜后复现解析值 ∫h=π^{3/2}，不掩膜连常数倍都不是）与 `test_base_w_on_real_density_is_not_a_measure_at_all`（换成真实密度 ρ，证明倍率根本不是一个常数）。
* **软归属与 owner 硬归属对局域项的差别只到浮点级，但要标清几何与网格档。** 水二聚体、6-31g\*、ωB97X-V、**level 3**（ne=20）实测四方案里软硬布居最大差：**构造几何 = 8.686e-07 个电子（×β = 2.642e-06 kcal/mol）**、**官方 S22 几何 = 1.527e-06 个电子（×β = 4.644e-06 kcal/mol）**（`evidence/population/20260930T201142Z_stepk_soft-vs-hard-constructed.out`、`evidence/population/20260930T200927Z_stepk_soft-vs-hard-official.out`）。旧稿只写"≤8.7e-7 个电子（2.6e-6 kcal/mol）"——那是**构造几何、level 3** 那一档，官方几何其实到 1.5e-6；两者都远小于方案间跨度（β·ΔN_A ≈ 0.30–0.33 kcal/mol，差好几个量级），所以 `fragment_decomposition(soft=)` 里"Becke 因子乘了两次"数值上无关紧要，不必当成竞争口径。
