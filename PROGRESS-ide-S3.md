## [2026-09-29 00:25] [agent=ide-qoder/S3] [done] VV10 +0.138 kcal/mol 偏移取证：根因=g/g' 交叉配对错误

### 0. 一句话结论

**核家族没错（是 VV10，不是 rVV10）；ω/κ/β 系数没错（均匀气逐位校验差 0.000e+00）；正则化、网格、σ 幂次、RHO_FLOOR 全部排除。那 +0.1378 kcal/mol 的固定偏移 100% 来自 Φ 里 g/g' 的 ω↔κ 配对方式：本仓快照 `nlcsplit/nlc.py` 用交叉配对 `g=ω_j·R²+κ_i`，而 PySCF 原生 `_vv10nlc` / libxc / ORCA 三者都用同中心配对 `g=ω_i·R²+κ_i`（V2）。** 改成同中心配对后偏移塌到 −0.0000。

判定只基于快照版本 `scratch/ide_snapshot_20260928T224224Z/nlcsplit/nlc.py`（md5 `a1800277812945717c8b10c11b849ad8`）；未编辑任何他人文件，未改 `nlcsplit/nlc.py`（cn-qoder 所有权）。

---

### 1. 调用链真相（子任务 1）

脚本：`scratch/ide_s3_pairing.py` 段 [A]；日志：`nlcsplit/logs/20260929T001615Z_ide-s3.out`。

**关键事实：PySCF 的 `nr_nlc_vxc` 不走 libxc 的 C，而走 PySCF 自己的原生 `_vv10nlc`（`libdft.VXC_vv10nlc`）。** 因此 S1/cn-qoder 文档里把参照值标为"libxc"是**称呼错误**——那个参照数值其实来自 PySCF 原生核。（下面 §4 独立裁判判定依赖这一点。）

`nlc_coeff` 实际返回（日志 [A] 原样）：
```
  wb97x_v   -> (((6.0, 0.01), 1),)
  wb97m_v   -> (((6.0, 0.01), 1),)
  vv10      -> (((5.9, 0.0093), 1),)
  b97m_v    -> (((6.0, 0.01), 1),)
  wb97x     -> ()
```
- 尾数 `1` 的语义：**不是 nlc 类型编号，是组合权重 fac**。依据 `pyscf/dft/libxc.py:416-429`：`_nlc_coeff` 用 `ctypes.c_double*2` 只装 `(b, C)`，再 `nlc_pars.append((tuple(nlc_tmp), fac))`，fac 来自 `nlc_frac`。当泛函无 NLC 时返回空 tuple（`wb97x -> ()`）。
- **ωB97X-V 挂的是原版 VV10 还是 rVV10？** 从参数看 `wb97x_v=(6.0,0.01)`，与 `vv10=(5.9,0.0093)` 不同、与 `wb97m_v=(6.0,0.01)` 相同——这**只**说明 b/C 数值，不能区分 VV10/rVV10（rVV10 差别在 ω0 用 τ，不在 b/C）。真正区分靠 §2 的合成实验：喂进 `_vv10nlc` 的是 `rho`（含 `sigma=|∇ρ|²`）而非 `tau`，且 PySCF 的 `_vv10nlc` 内核（`numint.py:471-555`，注释内核 525-538）用的 ω0 表达式是 `sqrt(C·σ²/ρ⁴+(4π/3)ρ)`——**这就是教科书 VV10，不是 rVV10**。实测 cross/same 两配对都能对上这个 σ-based ω0，说明参照核本身就是 VV10。**"用错核家族（rVV10）"这一嫌疑被否。**

---

### 2. 最小合成实验（子任务 2，决定性）

脚本：`scratch/ide_s3_pairing.py`；日志：`nlcsplit/logs/20260929T001615Z_ide-s3.out`（rc=0，耗时 36s，OMP_NUM_THREADS=2）。

底层入口：`pyscf.dft.numint._vv10nlc(rho, coords, rho, weights, coords, (b,C))`，直接喂 `rho, sigma, weights, b, C`，返回逐点 `exc`；隐含双积分能量 `E_nl = Σ w·ρ·exc − β·Σw·ρ`。手算两配对：
```
cross: g =R2*w0[None,:]+ki[:,None];  gp=R2*w0i[:,None]+kap[None,:]
same : g =R2*w0i[:,None]+ki[:,None];  gp=R2*w0[None,:]+kap[None,:]
phi  = -1.5/(g*gp*(g+gp));   E = 0.5*ΣΣ (w·ρ)_i (w·ρ)_j phi
```

**[B] 6 点紧簇合成箱（ρ、|∇ρ|² 各异，直调 `_vv10nlc`）**：
```
  PySCF _vv10nlc 隐含 E_nl      = -0.000064596844 Ha
  手算 cross(=nlc.py) E_nl      = -0.000064593290 Ha   diff_vs_pyscf=+3.554e-09 Ha
  手算 same(=PySCF内核) E_nl    = -0.000064596844 Ha   diff_vs_pyscf=-2.846e-19 Ha  ← 逐位相同
```
same 与 PySCF 差到 −2.8e−19 Ha（浮点下限内等价），cross 差 +3.6e−9 Ha。合成箱因点少、R² 尺度小，差被稀释到 ~0.0000 kcal；放大效应要到真实密集网格才显形（见 [C]）。

**均匀气校验（4 点，ρ 常数、σ=0）——用来分离"系数错" vs "配对错"**：
```
  [uniform-gas 4pt] E_tot PySCF=+0.006593086498  cross=+0.006593086498  same=+0.006593086498
     cross-PySCF=+0.000e+00  same-PySCF=+0.000e+00
```
解析上，cross 与 same 的 `g·gp` 只在 `R²` 系数上差 `Σ_ij (ω_i−ω_j)(κ_i−κ_j)R²`；`g+gp` 恒等。均匀气里 ω、κ 为常数 ⇒ `(ω_i−ω_j)=0` ⇒ 两配对恒等。**两者都 == PySCF（0.000e+00）证明 ω0 的 σ 幂次/系数、κ 前因子/幂次、β 全对**——若 κ 或 ω0 错，均匀气就不可能对上。故 S1 遗留嫌疑 ②（σ 定义/幂次）与 ③（κ 前因子/幂次）**排除**。偏移纯粹来自非均匀区 ω 与 κ 的**配对方式**。

**[C] 真实水单体 6-31g\* level1 三方对比（决定性放大）**：
```
  nlc_coeff b,C = 6.0, 0.01
  PySCF 隐含 E_nl          = -3.6491 kcal
  cross(手算,同keep)       = -3.5113  diff=+0.1378 kcal   ← 与 S1 观测的 +0.138 吻合
  same(=PySCF内核,同keep)  = -3.6491  diff=-0.0000 kcal   ← 修正后塌零
  快照 nlc.py pair_energy  = -3.5113  diff_vs_pyscf=+0.1378 kcal   ← 被测实现=cross
```
**最小反例即此一行**：同一密度、同一 keep mask、同一 (b,C)，快照 `nlc.py`（cross）=−3.5113，改 same-point=−3.6491，差正好 +0.1378，与 S1 全部网格档观测的 +0.1378~+0.1384 完全一致，且随 level 不收敛掉——因为它是解析定义差，不是离散误差。

---

### 3. 修正公式与出处（子任务 3）

**正确形式（同中心配对）**：
```
g(r,r')  = ω(r)·|r−r'|²  + κ(r)
g'(r,r') = ω(r')·|r−r'|² + κ(r')
Φ(r,r')  = −3 / [ 2 · g(r,r') · g'(r,r') · ( g(r,r') + g'(r,r') ) ]
ω(r) = sqrt( C·|∇ρ(r)|²/ρ(r)⁴ + (4π/3)·ρ(r) )      （VV10，非 rVV10）
κ(r) = b·(3π/2)·( ρ(r)/(9π) )^(1/6)
β    = (1/32)·(3/b²)^(3/4)
E_NL = ½ Σ_i Σ_j (w_iρ_i)(w_jρ_j) Φ_ij ,  E_loc = β Σ w ρ
```
错误形式（本仓快照）把 i/j 交叉：`g=ω_j R²+κ_i`、`g'=ω_i R²+κ_j`。

**出处**：
- Vydrov & Voorhis, *J. Chem. Phys.* **133**, 244103 (2010)，Eq. 4–6：`W(r,r')=−3/(2(g+b)^{1/2}…)`，其中 g、g′ 关于**同一中心**的 ω 与 κ 构造（`g=ω(r)R²+κ(r)`）。
- PySCF `pyscf/dft/numint.py:471–555`（`_vv10nlc`，注释内核 525–538）：`gp=R2*W0p+Kp`（ω_j,κ_j 同点），`g=R2*W0[i]+K[i]`（ω_i,κ_i 同点）——**实测逐位复现（[B] diff −2.8e−19）**。
- libxc `GGA_XC_VV10`（id=255）文档：同上中心配对。
- rVV10 参照（用于排除）：Lee, Vydrov, et al., *J. Chem. Phys.* **137**, 064112 (2012)——ω0 用 τ，本例不适用。

**改完需重测**：所有绝对量（`E_nl`、`E_NLC` 总量、水二聚体 `P_frz`/`CP`）；cn-qoder 已在 V2 下重跑（`PROGRESS-nlcsplit.md` 00:40，level≥1 差塌到 1e−3）。本 S3 与他们的 `step_e_kernel.py`/`kernel_variants.out` 结论一致（V0 cross vs V2 same），但方法独立：我直调 `_vv10nlc` 拿逐点 exc + 均匀气系数校验 + 解析分解，不依赖 libxc C 路径。

---

### 4. 外部裁判独立性（子任务 4）——ORCA 是真独立裁判

证据文件：`ref/h2o_wb97xv.out`、`ref/h2o_wb97xv.bibtex`。

- `ref/h2o_wb97xv.out` L126 `Waldemar Hujo : DFT-NL`；L161 `utilizes the DFT-NL dispersion correction`；L162–164 引用 **Vydrov & Van Voorhis 2010** + **Hujo & Grimme, J. Chem. Theory Comput. 2011, 7, 3866**（ORCA 的 NL 模块即此文的原生实现）。
- L150 虽 `built with libXC 6.2.2`，但**仅链接**，其 post-SCF 的 `E(C,NL)`（L619 `DFT-NL`，L657 `NL Energy, E(C,NL) = 0.042653836648 Eh = +26.76569 kcal/mol`）走自有 DFT-NL，不经 libxc-C 的 NLC。
- VV10 参数打印位置：L462 `NL short-range param. ...: 6.000000`、L463 `NL long-range param. ..: 0.010000`（b=6.0, C=0.01，与 nlc_coeff 一致）。
- 独立网格：L612 网格 3858 点（与 PySCF/本仓网格不同源）。

**判定：ORCA = 独立（native Hujo-Grimme 2011 DFT-NL，非 libxc）。** 且因为 §1 揭示"参照值"其实是 PySCF 原生 `_vv10nlc`（也非 libxc-C），**同意 V2 的两个实现是 PySCF-native 与 ORCA-native，彼此独立、都不依赖 libxc-C、也不依赖我们**。故"两个独立实现同意 V2"这句话**可以写进论文**，且比 S1/cn-qoder 现有的"两个 libxc-backed 实现"表述更强、更准确。

---

### 5. cn-qoder / S1 必须改写的结论与文档点

1. **称呼错误**：S1 `PROGRESS-ide-S1.md` 与 `PROGRESS-nlcsplit.md` 把参照数值标为"libxc"。应改为"**PySCF 原生 `_vv10nlc`（`libdft.VXC_vv10nlc`），非 libxc-C**"。依据 `numint.py:1347 nr_nlc_vxc` 调 `_vv10nlc`，未调 libxc 的 NLC C 入口。
2. **"两个 libxc-backed 实现"表述有误**（`PROGRESS-nlcsplit.md` 00:15 前后）：应为"PySCF-native + ORCA-native 两个原生实现"，二者互不依赖 libxc-C。这反而加强独立裁判论证。
3. **偏移非普适常数**：+0.1378 只是水的值。`nlcsplit/logs/kernel_variants.out` 显示 V0 cross 相对 same 偏差随体系增大：H2O +0.1379 / Ar +0.4182 / CH4 +0.1346 / benzene +0.9057。任何把 "+0.138" 当常数的表述需改为"随体系/电子数增长的 cross-vs-same 配对差"。
4. **尾数 `1` 语义**：S1 记录"那个尾数 `1` 的含义还没查清"。已查清 = 组合权重 fac，非 nlc 类型（§1）。S1 该 TODO 可关闭。
5. **绝对值作废范围确认**：与 cn-qoder 00:15 判断一致——V0 下所有 `E_nl`/`E_NLC`/二聚体 `P_frz`/`CP` 绝对值作废，需 V2 重算（cn-qoder 进行中）。本 S3 提供**独立方法学交叉证实**（非重复其 `step_e_kernel.py`）。

---

### 6. 已排除项清单（避免他人重做）

| 嫌疑 | 判定 | 证据 |
|---|---|---|
| 用错核家族（rVV10 τ-based ω0） | **否** | `_vv10nlc` 用 σ-based ω0；[B]/[C] 两配对都对上同一 σ 核 → 参照核是 VV10 |
| ω0 的 σ 幂次/系数 | **否** | 均匀气 0.000e+00；非均匀 same 逐位 = PySCF |
| κ 前因子/幂次 | **否** | 均匀气 0.000e+00（κ 常数即对）；V3/V4 错κ 在 kernel_variants.out 偏离 ±2~7% |
| β 局部项系数 | **否** | 剥离局部项后差全在双积分（S1 已定 +0.1379）；[C] E_nl same=PySCF |
| 低密度正则化 / ω0 near-zero | **否** | RHO_FLOOR 丢点数 92→502 gap 恒定（S1）；[C] 用同 keep mask 仍复现 +0.1378 |
| 网格不收敛 | **否（非主因）** | level L1..L5 gap 恒 +0.1378（S1）；[C] 是解析定义差不随 level 消失 |
| **g/g' 的 ω↔κ 配对方式** | **是（根因）** | [C] cross=+0.1378, same=−0.0000；[B] same diff −2.8e−19 逐位 = PySCF |

---

### 7. 本任务产物清单

- `scratch/ide_s3_pairing.py`（决定性三段实验脚本，7.1KB）
- `scratch/ide_s3_run_pairing.sh`（2 线程 wrapper）
- `scratch/ide_s3_probe.sh`（环境/源码探测）
- 日志：`nlcsplit/logs/20260929T001450Z_ide-s3.out`（首跑 rc=1，uniform vstack 维度 bug，历史保留）
- 日志：`nlcsplit/logs/20260929T001615Z_ide-s3.out`（**修正后 rc=0，全部证据**）

未编辑任何他人文件；未改 `nlcsplit/nlc.py`；无 git 写操作；未删文件；未连服务器；凭据未落盘。
