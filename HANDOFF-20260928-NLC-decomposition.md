# 交接文档：非局域关联（VV10）的片段/成对分解

**接手者须知**：本文自包含，不需要读之前的对话。所有数字都标注了复现方式。凡标 ⚠️ 的是**已知错误或未验证项**，不要当成事实用。

最后更新：2026-09-28，由上一轮 agent 写入。

---

## 0. 一句话现状

原始任务"把 ωB97X-V 移植进 GAMESS-BLW"已被判定为**不该继续的目标**（GAMESS 树 RHF 基线错 10–70 Ha；GAMESS 许可禁止再分发，软件论文无路；ωB97X-V 在 Q-Chem/Psi4/ORCA/MRCC/libxc 里都已有）。
现在的主线是：**在 PySCF 上做一个开源的、代码无关的非局域关联能片段/成对分解层**，目标 JCTC（方法）+ 可能的 SoftwareX/JOSS（软件）。
文献先例核查已完成第一轮，结论是**缺口存在但有条件**。

---

## 1. 已验证的事实（可直接依赖）

### 1.1 宿主能力：PySCF 2.12.1 已经有的东西

环境：WSL `Ubuntu-22.04`，`python3`（用户 `haangyeon`，site-packages 在 `~/.local/lib/python3.10/site-packages/pyscf`）。WSL **没有外网**，但能用代理 `http://127.0.0.1:7890`（Clash，用户本机开启）。

| 能力 | 状态 | 证据 |
|---|---|---|
| ωB97X-V 自洽能量 | ✅ 有 | 水/6-31G\* `RKS(xc='wb97x_v')` 收敛 **-76.3768906496**；ωB97M-V 也可用（-76.37524） |
| NLC 解析梯度 | ✅ 有，且正确 | STO-3G 下解析 vs 中心差分相对偏差 ~1e-4（注意 PySCF 返回 dE/dR，与"力"差一个符号） |
| **逐网格点 NLC 能量密度** | ✅ 有 | `nr_nlc_vxc` 内部 `_vv10nlc(...)` 返回的 `e` 形状 == 网格点数，且 `Σ w·ρ·e ≡ excsum`（精确） |
| **成对 (i∈A, j∈B) 结构** | ❌ 拿不到 | `_vv10nlc` 是 C 扩展，只吐点级 `e` 与势 `v`；加速用的插值分箱把双重和的结构吃掉了 |
| `dftd3` | ❌ 未安装 | 本机 `dft.dftd3` 不存在，D3 参照要另想办法 |
| PySCF 里的 `grids.atom_grid` | ⚠️ 2.12 里是**空 dict** | 不要指望它给原子分区网格；`gen_grid.original_becke` 是 C 存根（`pass`），`get_partition(mol, atom_grids_tab, ...)` 要的是原子网格表不是裸坐标 |

**结论**：点级（实空间）分割几乎免费 ⇒ **不构成贡献**。真正的工作量在"保住成对结构而不退化到 O(N²)"。

### 1.2 libxc 的权威参数（`pyscf.dft.libxc`，透传 libxc，非硬编码）

```
nlc_coeff('wb97x_v')  -> ((6.0, 0.01), 1)      # b, C
nlc_coeff('wb97m_v')  -> ((6.0, 0.01), 1)
nlc_coeff('b97m_v')   -> ((6.0, 0.01), 1)
nlc_coeff('vv10')     -> ((5.9, 0.0093), 1)    # 只有独立 vv10 条目是这组
rsh_coeff('wb97x_v')  -> (0.3, 1.0, -0.833)    # (ω, c_LR, c_SR)
rsh_coeff('wb97m_v')  -> (0.3, 1.0, -0.85)
```

⚠️ **不要**再说"ωB97X-V 应该用 b=5.9/C=0.0093"——那是错的，上一轮 agent 因为信了仓库里一个手写 py 文件而搞错。

### 1.3 VV10 核公式（已数值验证）

```
w0(r)  = sqrt( C·|∇ρ|⁴/ρ⁴ + (4/3)π·ρ )
κ(r)   = b·(3π/2)·(ρ/(9π))^(1/6)
g      = w0_j·R² + κ_i      g' = w0_i·R² + κ_j
Φ      = -3 / (2·g·g'·(g+g'))
E_NL   = 0.5·ΣΣ w_iρ_i·w_jρ_j·Φ
E_loc  = β·∫ρdr ,  β = (1/32)(3/b²)^(3/4)
E_NLC  = E_loc + E_NL
```

- 这套公式（GAMESS `dftvv10.src:231` 用的同一套）**能复现 libxc**：水单体同网格差 **+1.7e-4 Ha (0.108 kcal/mol)**；水二聚体差 **+0.24 ~ +0.32 kcal/mol**。
- ⚠️ 上一轮 agent 曾判这个公式"量纲不通"（bohr⁻⁴ 加 bohr⁻³）——**该质疑已被数值实验否定**，别再拿它当 bug。
- E_NLC 对单体为**正**（水 +26.8 kcal/mol）是正确物理：局部项 β·Nₑ = +0.0484690 Ha 主导，双积分只有 -0.0058161 Ha。

### 1.4 参考数值（用于回归）

| 体系 | 量 | 值 | 来源 |
|---|---|---|---|
| 水/6-31G\* ωB97X-V | E_SCF | -76.3768906496 | PySCF 2.12.1，本机 |
| 水/6-31G\* ωB97X-V | E_tot | -76.3865924435790618 | 仓库内 Psi4 输出 `E:\Project\GAMESS\ref\h2o_wb97x.out`（几何不同，不可直接逐位比） |
| 水/6-31G\* | E_NLC | +0.0426528757 Ha（level 3）/ +0.0426528778（level 4） | libxc；两级网格一致到 2e-9 |
| 水/6-31G\* | E_loc = β·Nₑ | +0.0484690031 Ha | b=6.0 |
| 水/6-31G\* | 双积分 | -0.0058161274 Ha | 差值 |
| 水/STO-3G | E_NLC | +0.0430426670 Ha | libxc level 3 |
| 水二聚体/6-31G\* level1 | E_NLC 总 | +53.1963 kcal/mol | 我的显式双重和；libxc 给 +52.8791 |
| 水二聚体/6-31G\* level1 | **片间 E_AB（最近原子硬分区）** | **-0.2713 kcal/mol** | 有效（可加性校验 6.5e-15） |
| 水二聚体/6-31G\* level1 | 片内 E_AA / E_BB | -3.550 / -3.541 kcal/mol | 同上 |
| 水二聚体/STO-3G level1 | 片间 E_AB（硬分区） | -0.2183 kcal/mol | 可加性校验 1.1e-15 |

水二聚体几何（Å，未优化，O–O = 2.983）见 `scratch/proto_dimer_nlc3.py` 里的 `DIMER`。⚠️ 这个几何**没有做优化**，正式工作前必须用已验证的解析梯度优化。

### 1.5 成本实测

显式双重和，numpy float64，分块 BS=384，单线程：
- N = 18,144 点 → **19.8 s**
- N = 18,272 点 → **13.6 s**
- N = 2,216 点 → 0.8 s

⇒ 细网格（6 万点）单次约 3–4 分钟；S22/S66 全集用显式双重和不可行。**这就是论文要解决的成本问题。**

---

## 2. 已被否证的假设（别重走）

| 曾经的说法 | 结论 |
|---|---|
| "GAMESS 里 `VV10_B=6.0/C=0.01` 是 bug，应为 5.9/0.0093" | ❌ 错，libxc 对 ωB97X-V 就用 6.0/0.01 |
| "非局域关联能不可能为正，E_VV10=+27.9 kcal 说明符号错" | ❌ 错，libxc 同样给正值 |
| "`dftvv10.src:231` 量纲不通" | ❌ 数值上能复现 libxc 到 0.1 kcal/mol，撤回 |
| "GAMESS 基线错是因为混版编译（273 个旧 .o + 4 个新 .o）" | ❌ 服务器 16:17 全量重编（277 个 .o 同日，compall.log 276 次 gfortran）后仍错 |
| "GAMESS 积分模块（int2a 等）被激活器删了 sp 壳代码" | ❌ `diff -rq` 对 pristine tar：积分模块逐字节一致，只有 `dft.src`/`dftgrd.src`/`dftxca.src`/`rhfuhf.src` 改过 + 新增 `dftvv10.src` |
| "exam01 的 -30.706 说明 CH₂ 算错" | ❌ `exam01.inp` 里 `$SYSTEM TIMLIM=1`，那是被 1 分钟时限砍断的**几何优化中间步**，不是收敛值（期望 -37.2380397698） |
| "ref/agentA/h2o_ch2.inp 是 CH₂/STO-2G" | ❌ 它是 **H₂O + CHARGE=2**，而且 neutral/CHARGE=2/CHARGE=4 三份日志逐字节相同 |
| "ωB97X-V 的 ω 没设" | ❌ `dft.src:902-903` 设了 MU=0.3，日志打印 CAMMU = 0.300 |
| "VV10 网格采集有问题" | ❌ `TOTAL ELECTRON NUMBER = 10.0000030382`，采集是对的 |

---

## 3. GAMESS-BLW 那棵树的真实状态（已封存，除非要写应用文）

- 树：`E:\Project\GAMESS\source\GAMESS_BLW`（2014.11.04 + BLW 补丁，278 个 .src / 131 万行 F77，**无 git**）。原始 tar 在 `E:\Project\GAMESS\GAMESS_BLW.tar`（内部路径前缀 `GAMESS_BLW/`）。
- **RHF 基线是坏的**，规律清楚：单/双中心纯 s 体系全对（He/STO-3G -2.807784 ✓、H₂/STO-3G -1.116999 ✓、H₂/6-31G -1.126809 ✓），**凡含 p 壳即崩**：

| 体系 | iter 1（初猜） | "收敛"值 | 应有 |
|---|---|---|---|
| Ne/STO-3G | **-126.6045** | -92.8352 | ≈-126.60 |
| CO/STO-3G | -110.989 | -41.566 | — |
| H₂O/STO-3G | **-74.7972** | -51.4737 | ≈-74.96 |
| H₂O/6-31G\* | — | -52.1194 | ≈-76.06 |
| HPO (exam07) | — | -169.53 | -414.0945 |

  注意 Ne 的 iter 1 = -126.6045 正好是文献值 ⇒ **一电子积分是对的，坏在 density→Fock 重建**。误差随壳层数增长，像数组越界/COMMON 尺寸类问题。
- 我们对 `rhfuhf.src` 的改动只有 16 行，全是**附加式**（`LOGICAL` 声明表尾加 `DOVV10, DO_VV10CAP`、三个**新的** COMMON 块 `/VV10FL/ /VV10EN/ /VV10PR/`、SCF 后一次 `IF(DOVV10) CALL VV10ENG`、一个 `CALL PRTVV10`、一个遗留 `9391 FORMAT('VV10-DBG'...)`）。⇒ **不可能是我们改坏的**，嫌疑在 BLW 补丁本体或构建方式。
- 尚未完成的判别实验（**如果**将来要修）：在隔离副本里带 `-fcheck=bounds -g -fbacktrace` 全量重编，让程序自己在越界处报例程和下标。上一轮卡在 `compall` 报 "Please run 'config' first"——原因是 `install.info` 是 **csh** 脚本、`compall` 要求环境变量已被 source；用 `csh` 跑即可。
- 服务器上 `/root/GAMESS_BLW` 是**另一个 agent 在用的**，不要动。我的隔离副本在 `/root/gamess_work/ctl`（⚠️ 里面 `install.info` 和若干文件的绝对路径被我用 sed 改成了 `/root/gamess_work/ctl`，且 `tools/mbldr.f` 被误改过一行编译标志——那是一次过宽的 sed，副本可弃）。
- 服务器：`10.8.51.23` 端口 `24522`，root，8 核 / 23 GB / 50 GB 盘（剩 17 GB），gfortran 有、mpif90 无、PySCF 无、有外网。凭据由用户按次提供，**不要写进任何文件或记忆**。
- GAMESS 里确认还错的（若将来要修）：`ALPHAC=0.167` 应为 c_SR = **-0.833**（远程仍须 ALPHAC+BETAC=1.0）；`dftxca.src:5948-5958` 的关联系数只有 3 位有效数字（其余泛函都是 6–7 位），且 libxc 的 ωB97X-V 关联是 PBE 基 + |∇ρ|⁴/ρ³ 项，与 GAMESS 的 B97SS/B97AB 多项式**不是同一函数形式**；分支未设 `C2S/C2T/DHFUNC`。
- `E:\Project\GAMESS\source\GAMESS_BLW\IMPLEMENT-WB97XV-VALIDATION.md` **不是证据**：它声称"系数与 LibXC par_wb97x_v 一致"、"与 vv10_ref.py 逐位一致"，而 `vv10_ref.py` 是和 Fortran 同一只手写的。仓库里有**三份互相矛盾**的 VV10 核（`dftvv10.src`、`tools/vv10nlc/vv10_ref.py`、`tools/vv10nlc/vv10nlc.py`，最后一份的核是 `-3/(2g)` 并谎称"VV10 Eq. 8"）。

---

## 4. 文献先例核查结果（Step 0）

检索规模：OpenAlex + Crossref + arXiv，12 组 known-item 查询，**128 条去重记录**。分级：

| 级别 | 含义 | 条数 |
|---|---|---|
| A | 非局域关联 + 能量分解 + EDA 语境 | 1 |
| **A2** | **成对/分片的非局域项**（正是目标） | **0** |
| **B** | 非局域项被实空间分割 | **0** |
| C | EDA 中"色散项"的定义问题 | 5 |

- **SQ-MBD**（Nat. Commun. 2023, doi:10.1038/s41467-023-43785-z，PMC10716193）**已读全文**（118,511 字符）：`nonlocal correlation` 出现 **0** 次、`VV10` **0** 次、`vdW-DF` 1 次且只在参考文献里 ⇒ 它分解的是 MBD（Drude 振子）模型，**不是撞车**。但它明写："such quantification of the fragment contribution to the collective MBD energy is **not unique** since there are multiple ways to partition the pair-fragment contributions."
- **JCTC 2023, doi:10.1021/acs.jctc.3c00903**（唯一的 A 级命中，且正是目标刊）：只拿到 OpenAlex 存的**完整摘要**（ACS 与 ChemRxiv 都 403）。摘要显示它的 EDA 是在 **revPBE-D3 的色散 vs 电荷转移**上做的，`SCAN-rVV10` 只作为**被评测的泛函**出现 ⇒ 判为**邻近、非撞车**，但这是**摘要级证据**。
- ⚠️ **阴性结果要打折**：查询"非局域关联的解析梯度实现"在 OpenAlex 返回 **0 命中**，而 PySCF 实测就有。开放索引的"查不到"≠"不存在"。

### 4.1 仍未完成的两项前置（都需要用户的机构权限）

1. `10.1021/acs.jctc.3c00903` **正文**核实（ACS 付费墙）。
2. **WoS / Scopus** 一轮系统检索：`nonlocal correlation` × `energy decomposition` × `pairwise`，**必须覆盖周期性/vdW-DF 社区**（那边最可能已经做过）。
   可用技能：`academic-db-retrieval`（CNKI/WoS/Scopus + Playwright，SNNU 校内网）。

---

## 5. 论文的立论（已被实验修正过两次，这是最新版）

**不要**用"我们能做到精确可加"当卖点——实验证明那是**平凡的**：把双重和的求和索引按片段分组，分片求和与直接求和差 8.7e-19（机器精度）。SQ-MBD 那句"not unique"因此不能直接反衬你。

真正的贡献只有两块：

1. **归属方案的定义与辩护**。非唯一性的真正来源是"网格点（以及局部项 β∫ρdr）归给哪个片段"，不是求和方式。需要：给出一个有物理依据的方案，证明它对网格、基组、分区半径**稳定**，并与 SAPT/MBD 的色散趋势对得上。
2. **保住成对结构的次二次方算法**。这是唯一的硬算法贡献，也是它不会被说成"trivially available"的理由。现有加速（libxc/PySCF 的插值分箱）与成对分解**互斥**，必须改造。

### 5.1 一个必须正视的量级问题（本轮最重要的发现）

- 水二聚体的**片间 NLC 只有 -0.27 kcal/mol**（硬分区，6-31G\*/level1）。
- 文献里水二聚体的**色散**约 -1.0 ~ -1.5 kcal/mol。
- 而 libxc 的插值核与精确双重和之间就有 **+0.24 ~ +0.32 kcal/mol** 的系统差（level 0→1 不消失）。

⇒ 三件事同时成立：**(a)** 你要测的信号和参照物自身的近似误差**同量级**，所以"对标 libxc 到 0.1 kcal/mol"这种验收标准在这个问题上**不够用**，必须先量化 libxc 插值的误差；**(b)** VV10 的片间项**不等于**物理色散（半局域关联和局部 β 项的跨片段部分也得归属进来），论文必须把"非局域项"和"色散"分清楚，否则会被审稿人一句"你这数比 SAPT 色散小 4 倍"打死；**(c)** 分解方案的价值主张要落在"可解释性/可加性/成本"，不能落在"更准的色散能"。

---

## 6. 立刻要做的事（按顺序，每步有验收标准）

### Step 1 — 修好原型里的 Becke 分区（⚠️ 当前是坏的）

`scratch/proto_dimer_nlc3.py` 里我自写的 `becke_weights()` **是错的**：每点权重和 min=0.171 / max=0.999（应为 1），导致软分区的可加性校验差 **+2.46 kcal/mol**。原因是我临时编的原子半径表（`RAD = {1: 0.529177*0.25*2, 8: ...}`）不对。
正确做法：用 PySCF 自己的表 `pyscf.dft.radi.BRAGG_RADII`（**bohr**，按 Z 索引；`get_partition` 的默认参数里能看到 `array([3.77945036, 0.66140414, 2.64561657, ...])`）。
**验收**：`wb.sum(0)` 逐点 == 1（到 1e-12），且软分区可加性校验 == 0（到 1e-12）。
⚠️ 在修好之前，**只有"最近原子硬分区"的数字可用**（它的可加性校验是 1e-15）。表 1.4 里的片间值全部来自硬分区，有效。

### Step 2 — 归属方案敏感性（论文第一张图）

在同一批网格点上，比较至少 4 种归属：最近原子硬分区 / Becke（半径修正）/ Hirshfeld（自实现或用 `pyscf.tools`）/ 以及"片间区域按密度权重分摊"。
体系：水二聚体（先优化几何）、苯二聚体（π 堆积，色散主导）、S22 里挑 3–5 个。
**验收**：给出 E_AB 随方案的散布（kcal/mol 与 %），并判断哪种方案在网格/基组收敛下最稳定。

### Step 3 — 建立可信参照（解决 §5.1(a)）

不要拿 libxc 当唯一裁判。至少两条独立参照：
- 自己的显式双重和在**加密网格**下外推（level 2/3/4），确认网格收敛；
- 一个外部程序对同一体系的 VV10 值（Psi4 仓库里已有 `ref/h2o_wb97x.out`；Q-Chem/ORCA 若有权限更好）。
**验收**：能把"libxc 插值误差"和"我的离散化误差"分开报数。

### Step 4 — 次二次方算法（论文的技术核心）

目标：在保住 (i∈A, j∈B) 可分离的前提下，把 N² 降下来。可试的方向：
- 把插值方案改成**对 (w0, κ, R²) 三维分箱**并保留箱索引 ⇒ 片间和 = 箱级双线性组合，成本 O(N·nbins)；
- 或对 Φ 做低秩/切比雪夫展开，使 Φ ≈ Σ_k u_k(i)·v_k(j)，天然可分片。
**验收**：与显式双重和在水二聚体上片间项一致到 <0.01 kcal/mol，且 N=6 万点时耗时 < 显式方案的 1/20。

### Step 5 — 才谈投稿

JCTC（方法）为主。SoftwareX/JOSS 只在"独立开源库 + 完整测试 + CI + 文档"齐备时才投；**注意许可**：库里**不得含任何 GAMESS 源码**（GAMESS 不许再分发），PySCF 是 Apache-2.0 可以作为依赖。
先例：libxc 发在 SoftwareX 7 (2018) 1–5, doi:10.1016/j.softx.2017.11.002。

---

## 7. 本轮产出的文件

| 路径 | 内容 |
|---|---|
| `E:\Project\GAMESS\HANDOFF-20260928-NLC-decomposition.md` | 本文 |
| `E:\Project\GAMESS\STEP0-prior-art-verdict.md` | 文献先例核查报告（含分级表、SQ-MBD 全文判定、两项前置） |
| `E:\Project\GAMESS\PLAN-20260928-baseline-first.md` | GAMESS 基线修复方案（**已降级**，仅在决定修那棵树时用） |
| `scratch\pyscf_wb97xv_check.py` | 证明 PySCF 有自洽 ωB97X-V |
| `scratch\pyscf_nlc_grad_check3.py` | 解析梯度 vs 数值差分 |
| `scratch\nlc_reference.py` | 水单体 NLC 参考值 + β 分解 |
| `scratch\test_nlc_decomp.py` | 显式双重和复现 libxc + 可加性平凡性证明 |
| `scratch\proto_dimer_nlc3.py` | 水二聚体原型（⚠️ Becke 部分待修，见 Step 1） |
| `scratch\step0_stageA_oa.py` / `step0_stageC.py` / `step0_triage_known.py` | 检索与分级流水线 |
| `scratch\check_jctc3c00903.py` | 绕付费墙读 JCTC 摘要与引用文献 |
| `scratch\step0_known_items.jsonl` / `step0_openalex.json` | 检索原始记录（143 / 195 条） |

记忆（CN 版 Qoder）：`C:\Users\Administrator\.qoder-cn\projects\E--Project-GAMESS\memory\` 下有 `project-gamess-wb97xv-status.md`、`project-publishability-constraint.md`、`reference-qoder-intl-memory.md`。国际版 Qoder 另有一份**不同步**的记忆在 `C:\Users\Administrator\.qoder\projects\E--Project-GAMESS\memory\`，其中"这套代码从未编译过"已过期。

---

## 8. 与用户协作的规矩（他反复强调过）

- **数字要自己验**，不要把简报里的数字或别人日志里的结论当事实。上一轮 agent 因为信了仓库里自写的"参考实现"和一份"已验证"文档，连续给出三条错误结论。
- **自写的参考实现不算验证**。裁判必须与被测代码无共同作者（libxc、Psi4 输出、论文表格）。
- **默认只报告，不擅自改已交付的产物**；改动前先给对照。
- **不可逆操作（删文件、覆盖二进制、动别人的树）先确认**。服务器磁盘上 `/root/mace`(9.1G) 与 `/root/miniconda3`(8.9G) 看着是活跃项目，不要删。
- **凭据不落盘**：服务器口令、代理设置只用于当次会话。
- 判断/取舍类问题他倾向于送外部模型裁决（`chatgpt-pool-web` 技能），只有凭据、花钱、不可逆三类才找他。
- 本地机器算力弱，重计算放服务器或 WSL；WSL 无外网，走代理 `http://127.0.0.1:7890`。
