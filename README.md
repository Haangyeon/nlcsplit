# nlcsplit —— 非局域关联能的片段-成对分解

把 ωB97X-V / ωB97M-V / VV10 / rVV10 里的 **非局域关联项（VV10 双重和）** 按片段归属
拆开：给出每个片段的自身项 E_AA、每对片段之间的成对项 E_AB，以及它们的和与
PySCF 原生核的总量对照。纯 Python + NumPy，后端用 PySCF 出密度与网格。
（跨**程序**的锚点目前尚未建立，见下面"它准不准"——别把"与原生核一致"读成"与别的软件一致"。）

**不含任何 GAMESS 代码**（GAMESS 许可证不允许再分发），也不依赖 GAMESS。

## 安装

```bash
pip install .            # 依赖 numpy 与 pyscf>=2.12
python -m pytest -q nlcsplit/tests          # 8 项，约 90 s
python -m pytest -q -m "not slow" nlcsplit/tests   # 只要秒级自检
```

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
| 配对 | `g = w0(r_i)R² + κ(r_i)`、`g' = w0(r_j)R² + κ(r_j)`（**同中心**配对，与 PySCF 原生核一致；跨程序是否同约定尚未验证，见"它准不准"）。旧的交叉配对 `g=w0(r_j)R²+κ(r_i)` 水偏高 +0.138、Ar +0.42、苯 +0.91 kcal/mol，保留只为做定义敏感性对照 |
| 半份 | `pair_energy(A,B)` 返回 **半份** 成对项；`fragment_decomposition` 里 `inter[(A,B)] = 2·blk` 是完整一份，故 `E_nl = Σintra + Σinter` 可加性严格成立（实测残差 ≤2e-18 Ha） |
| 远区 | `rho_floor`（默认 1e-12）以下点不参与双重和；片间项对这一裁剪不敏感（1e-8…1e-16 五档跨度 4e-11 kcal/mol，代价是丢 10–23% 的点） |

## 它准不准

* **裁判是谁要说清**：总量对照走 PySCF 原生 VV10 核（`numint.nr_nlc_vxc` →
  `libdft.VXC_vv10nlc`，**不经 libxc**，libxc 只管半局域那部分）。水单体 level 1 上
  同一张网格、同一份密度，我们与原生核差 ≤6e-6 kcal/mol（≈1e-8 Ha）。
  ⚠️ **这两个实现同属 PySCF 一个库**，所以它只证明"我们的算术没错"，
  不证明"VV10 我们理解对了"。跨程序锚点**尚未建立**：
  本 README 与论文骨架此前都写过"与 ORCA 6.0.1 差 6e-4 kcal/mol"，
  2026-09-29 回读 `ref/h2o_wb97xv.out` 后发现该文件**根本没有单列的非局域项**
  （只有 `EX` 与合计 `EC`），那个数在 `ref/` 里也找不到出处，**已撤回**。
  要补上需要一次会打印 VV10 项的 ORCA 运行、Psi4，或自己构建 libxc 直调 `xc_nlc_vxc`
  （PySCF 里的 libxc 是静态链的，取不到符号）。
* **跨版本/跨机器复现**：PySCF 2.12.1（本机）与 2.14.0（远端）在同一 level 下网格点数差
  10%（18368 vs 20248），但 `step_f` 的每个能量分项**逐位一致** ⇒ 能量对网格已收敛。
* **网格收敛**：同一基组内 level 0→2 的片间项散布 ≤0.008 kcal/mol。
* **已知最大不确定项**：人为的归属方案。同一体系同一网格，Becke / Becke 半径修正 /
  Becke–Treutler / Stratmann 四种方案的片间项跨度：水（构造几何, lvl1）
  **0.040 kcal/mol（|E_AB| 的 7.6%）**；八个 S22 体系上是
  **0.004–0.310 kcal/mol，相对 0.8%–18.2%，且与体系类型无规律**
  （苯 sandwich 1.8% vs 苯-水 18.2%）⇒ 误差条必须逐体系给，
  一个统一百分比会把甲烷二聚体说错二十倍。
  论文里它应当作为误差条报告，而不是当作通过/不通过的门槛。

## 不能拿它做什么

* **非局域项 ≠ 物理色散。** 水二聚体里 `ΔE_NLC = −0.515`，只占 `ΔE_xc = −2.958 kcal/mol`
  的 17.4%；其余在半局域交换-关联 + 精确交换里，而那部分同时混着静电与交换排斥。
  本包不做 SAPT/EDA 意义上的分解（未做 BSSE/CP 校正，也没把静电与交换排斥分开）。
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

1. `Σ_a S[i,a] == 1` 逐点成立（实测最大偏差 4.4e-16）；
2. `base_w[i] · S[i, owner(i)]` 必须逐点等于 **PySCF 自己**的
   `gen_grid.get_partition` 权重（实测 8e-13 绝对值，四方案 × level 0/1/2）。

第 2 条是**外部锚**：比对对象是 `libdft.VXCgen_grid` 的输出，
不是本仓库另写的一份公式，所以它不算自证。

两条容易踩的口径，这里写死：

* **软归属必须喂分区后的 `weights`（或 `atom_partition` 的 `w`），不要喂 `base_w`。**
  `base_w` 是各原子子网格的**原始体积元**，其并集在重叠区重复计数——
  实测拿它配一次因子积分电子数会得到 **94.75 个**（该体系真值 20）。
* 喂 `w_ref` 之后，"软归属"与"owner 硬归属"对**局域项**的差别只有
  **≤8.7e-7 个电子**（×β 后 ≤2.6e-6 kcal/mol）——两者数值上是同一件事，
  不必当成竞争口径。
