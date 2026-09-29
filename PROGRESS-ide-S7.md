# PROGRESS — agent=ide-qoder/S7（VV10 第三独立实现调查：直接对接 libxc）

## [2026-09-29 07:18] [agent=ide-qoder/S7] [done]

一句话结论：**libxc 7.0.0 根本没有"产出 VV10 非局域关联能总值"的例程**，因此它
不能充当我们要找的"第三个数值裁判"。它对验证链的贡献只在两处——**参数表**与
**公式/约定定义**，而这两处恰恰证明它与 PySCF **同源**。真正独立的数值锚仍然
只有 ORCA 一个。下面逐条给数据。

证据来源（每个数都能回到这里复核）：
- 主脚本：`scratch/ide_s7_libxc.py`（251 行，[A]校准闸门 / [B]参数独立性 / [C]三方表）
- ctypes shim：`scratch/ide_s7_xcapi.py`（不硬编 offsets，物理量全走库函数读）
- 正式日志：`nlcsplit/logs/20260929T071016Z_ide-s7.out`（`bash scratch/ide_runner.sh s7 …`，`OMP_NUM_THREADS=4`，rc=0）
- 符号/头文件/ldd 侦察日志：`scratch/ide_s7_probe8.sh`…`probe12.sh`、`scratch/ide_s7_probe_flags.sh`
- 快照：`scratch/ide_snapshot_20260929T065022Z`
  - `nlcsplit/nlc.py` md5 = `433a9d7a736572ef28695d403cbc00e4`
  - `nlcsplit/geomlib.py` md5 = `8d205746669e0503bbc68aa139a8841f`（修复版 h2o_dimer）

---

## 1. libxc 是否可用？——哪条路线、版本号

**libxc 版本：7.0.0**（运行时经 `xc_version_string()` + `xc_version(int*,int*,int*)` 双读，
返回 `('7.0.0', (7, 0, 0))`；见日志 line 4）。二进制路径：
`~/.local/lib/python3.10/site-packages/pyscf/lib/deps/lib/libxc.so`（PySCF 自带的上游 libxc）。

按任务给的四条路线，逐条给结果：

- **路线 1（本地 libxc 二进制 + ctypes）——能绑，但绑不出 E_NLC。**
  `nm -D` 与 `hasattr` 双查（日志 line 5–11，probe8/probe12）：
  | 例程 | 是否存在 |
  |---|---|
  | `xc_nlc_vxc` | **False** |
  | `xc_nl_vxc` | **False** |
  | `xc_nl_split_vxc` | **False** |
  | `xc_gga_nlc_vxc` | **False** |
  | `xc_mgga_nlc_vxc` | **False** |
  | `xc_lda_nlc_vxc` | **False** |
  | `xc_nlc_grs_init` | **False** |
  | `xc_nlc_coef` | True（**只返回参数 b, C，不是能量**） |
  | `xc_version` / `xc_func_init` / `xc_gga_vxc` / `xc_mgga_vxc` | True |

  权威头文件 `deps/include/xc.h` 里 NLC 相关**只有** `xc_nlc_coef`（第 579 行），没有任何
  NLC 能量例程的声明。=> **绑定本身成功**（能加载、能取参数、能逐点算半局部项），
  但 libxc **不提供**产出实空间双重和 `E_NLC` 的入口。这是**架构缺口，不是数值分歧**
  （下面第 4 节按校准铁律单列）。

- **路线 2（pip 绑定）——失败。** PyPI 上无名为 `libxc` 的发行版；经代理 `pip install libxc`
  返回 `No matching distribution found`（probe9）。代理本身可达，纯粹没有这个包。

- **路线 3（PySCF 未文档入口）——不存在走 libxc 的 NLC 能量分支。** `pyscf.dft.libxc` 无任何
  `nlc` 能量入口（已 grep）；PySCF 的 VV10 核 `VXC_vv10nlc` 编在 **PySCF 自己的 `libdft.so`**，
  且 `libdft.so` 的 `NEEDED` 依赖列表**不含 libxc.so**（probe9）。

- **路线 4（官方源码公式/参数/约定）——成功，且这才是 libxc 能提供的真正价值。** 从 libxc
  官方仓库读 `gga_xc_vv10.c`、`hyb_mgga_xc_wb97mv.c`、`hyb_gga_xc_wb97.c`（只读，未下载进仓），
  把 ω0/κ/Φ/β 写法、`nlc_b/nlc_C`、nlp_type/flags 全部钉死，见第 3、5 节。

**采用路线：1 + 4 并联。** 路线 1 证明"libxc 无 E_NLC 例程"这一硬事实并取到参数；
路线 4 从源码补齐公式与 VV10/rVV10 约定。

---

## 2. 三方对照表（ωB97X-V / 6-31G\*，同一张网格、同一份 `eval_rho` 密度）

来源：日志 line 53–63（[C] 节）。单位 kcal/mol，KCAL=627.509474。
"我们显式和"= `nlcsplit/nlc.py` 同中心配对 `g=w0_i·R²+κ_i, g'=w0_j·R²+κ_j` 的显式双重和；
"PySCF 原生核"= `numint.nr_nlc_vxc` → `libdft.VXC_vv10nlc`；"libxc"= 待求的第三实现。

| 体系 | level | 网格点数 N | 我们显式和 | PySCF 原生核 | 我们−PySCF (kcal) | libxc | 秒 |
|---|---|---|---|---|---|---|---|
| H2O (geomlib, rOH=0.9572) | 0 | 2216 | +26.79174 | +26.79174 | +4.98e-06 | **N/A** | 0.1 |
| H2O | 1 | 9184 | +26.76540 | +26.76540 | +3.70e-06 | **N/A** | 0.9 |
| H2O | 2 | 19520 | +26.76542 | +26.76541 | +4.00e-06 | **N/A** | 7.5 |
| Ar | 1 | 5112 | +48.47486 | +48.47485 | +6.90e-06 | **N/A** | 0.3 |
| benzene | 0 | 9352 | +101.29215 | +101.29212 | +2.87e-05 | **N/A** | 1.0 |
| benzene | 1 | 39136 | +101.22376 | +101.22374 | +1.85e-05 | **N/A** | 28.6 |
| (H2O)₂（geomlib 修复版 dimer） | 1 | 18368 | +53.01568 | +53.01567 | +6.35e-06 | **N/A** | 5.9 |

- **libxc 列恒为 N/A**：不是"没跑"，而是 libxc 7.0.0 无任何产出 `E_NLC` 总值的例程（第 1 节表）。
- 水二聚体几何用的是 live `geomlib.h2o_dimer()`（md5 8d205746，修复版：`acc=π−θ/2`、
  最短 H···H=2.718 Å、单体角严格 104.52°），**未自造坐标**，未用有缺陷的 `nh3()`。
- 前几档"我们 vs PySCF"最大的是苯 L0/L1，也只有 **2.9e-5 / 1.9e-5 kcal**（≈4.6e-8 / 2.9e-8 Ha），
  随电子数/网格增大没有发散趋势——这与既有定案"水 lvl0 差 7.9e-9 Ha"完全同一量级。
- **注意**：任务里提到的 Ar "+0.418 kcal" / 苯 "+0.906 kcal" 是**此前显式和 vs 另一个参照**
  的量级差（多半是网格等级/密度口径不一致）。**在同一份密度、同一张网格上直接对打时，
  显式和与 PySCF 原生核只差 1e-5 kcal 级**（本表实测），不存在那个 0.4–0.9 kcal 的差。
  这一条值得单独向 cn-qoder 确认：那 0.418/0.906 究竟是不是"同网格同密度"口径。

---

## 3. 校准闸门（先证"我们这一路"闭合，再谈 libxc）—— 日志 line 14–37

铁律：任何自写绑定先用 ORCA 水单体 +26.76569 kcal/mol 校准；不闭合判绑定失败，
不许把绑定失败当"libxc 与我们有差异"。这里校准的是**我们显式和 vs ORCA**（ORCA 几何
`rOH=0.956983 / ∠=104.516`）：

| level | 我们显式和 | PySCF 原生核 | ORCA 已知 | 我们−ORCA (kcal) |
|---|---|---|---|---|
| 0 | +26.79185 | +26.79185 | +26.76569 | **+0.0262**（粗网格） |
| 1 | +26.76553 | +26.76552 | +26.76569 | **−0.0002** |
| 2 | +26.76554 | +26.76554 | +26.76569 | **−0.0001** |

- L1/L2 我们显式和收敛到 ORCA **0.1–0.2 mKcal（2e-4 kcal）**——校准**成立**。
- L0 偏 +0.026 kcal、脚本里 `<1e-2` 闸门在 L0 显示 FAIL，这是**网格分辨率不足**
  （L0 只有 2216 点）导致的积分误差，**不是实现分歧**：同档 L0 我们与 PySCF 仍差 4.97e-6 kcal。
  换 L1/L2 闸门自然 PASS。如实记录，不粉饰。
- `rho_floor` 敏感性：1e-12 vs 1e-8 差 **−1e-8 kcal**（对阈值不敏感），与既有定案一致。

**libxc 侧校准结果**：把 libxc 的 VV10 泛函喂进 `xc_gga_vxc` 逐点评估再积分（日志 line 20/29/37），
得 **−6760 / −6755 kcal** 这种量级——与 +26.77 的非局域值**完全不可比**，因为 libxc 的 VV10
能量评估指针是 NULL、`xc_gga_vxc` 只吐出半局部(RPW86+PBE)那部分，**根本不包含非局域双重和**。
=> **判定：libxc 绑定成功但无 E_NLC 产出（架构缺口），不是"libxc 与我们的核数值有差异"。**

---

## 4. ★"libxc 这个裁判到底有多独立"★（转 cn-qoder + 进论文验证节）

要回答的是：libxc 若能用，算不算独立于 PySCF 的第三方？**结论：不能——在关键的两点
（参数表、VV10/rVV10 约定）上 libxc 与 PySCF 同源，且 libxc 根本不产出可比数值。**

1. **参数表逐位相同。** `xc_nlc_coef`（libxc）与 `nlc_coeff`（PySCF）对同一批泛函给出
   一模一样的 (b, C)（日志 line 42–45）：

   | 泛函 | libxc b | libxc C | PySCF `nlc_coeff` |
   |---|---|---|---|
   | VV10 | 5.9 | 0.0093 | `(((5.9, 0.0093), 1),)` |
   | ωB97X-V | 6.0 | 0.01 | `(((6.0, 0.01), 1),)` |
   | ωB97M-V | 6.0 | 0.01 | `(((6.0, 0.01), 1),)` |

   逐位一致 ⇒ 二者读的是**同一张参数表**（都追溯到 VV10/rVV10 原文与 Grimme 组的
   参数约定），不是两条独立推导。**独立性 = 无。**

2. **fast kernel 不同源、但 libxc 无 kernel。** PySCF 的 `VXC_vv10nlc` 编在自己 `libdft.so`，
   该 `.so` 的依赖闭包**不含 `libxc.so`**（probe9）——所以两个"快速核"并非互相调用。
   但这不带来独立裁判价值，因为 **libxc 侧压根没有实空间双重和的核**（评估指针 NULL）：
   没有第二个 kernel 可与之对打。所谓"两个 fast kernel 是否互抄"的疑问在此体系下**无从谈起**
   ——libxc 没有那个 kernel。

3. **版本口径。** 这里是 PySCF 2.12.1 捆绑的 **libxc 7.0.0**。libxc 自 v6 起把 VV10 的
   非局域项从"库内算"改为"打 `XC_FLAGS_VV10` 标志、由宿主程序自己算双重和"的 pointwise
   架构；本环境的 `xc.h` 与官方 `gga_xc_vv10.c` 都证实了这点（`info` 结构末尾 4 个 NULL =
   exit/lda/gga/mgga 能量评估全为空）。=> 用 libxc 拿 E_NLC 数值，在 7.x 上**结构上不可能**。

4. **`xc_gga_vxc(VV10)` 给的是半局部项**（第 3 节 −6760 kcal），进一步说明"能调通 libxc"
   ≠ "能拿到 libxc 的非局域能"。

**综合判断**：libxc **不是**独立于 PySCF 的第三方数值裁判。它的正确用法是当**规范权威**——
用它的源码与 `nlc_params`/flags **钉死公式与约定**（第 5 节），从而回答"我们和 PySCF 是不是都
把 VV10 写对了"。至于"我们 vs 别的实现"的数值独立性，链条仍是：**显式和 ↔ PySCF 原生核
（同库，不独立）↔ ORCA（唯一真独立锚）**。要凑真第三方数值，得另找 GPAW / Quantum ESPRESSO
的 VV10 实现，或直接以 ORCA 为准——libxc 这条路给不了。

---

## 5. ωB97X-V 在 libxc 里是 VV10 还是 rVV10？—— 已钉死

来自本地 `deps/include/xc_funcs.h` 功能号 + flags 侦察（`ide_s7_probe_flags.sh`）与官方源码：

- libxc 里**只有** `XC_FLAGS_VV10`(1<<10=1024) 和 `XC_FLAGS_NEEDS_TAU`(1<<16=65536)，
  **不存在 `XC_FLAGS_RVV10`**。VV10/rVV10 之分靠 `NEEDS_TAU` + family(MGGA) **隐含**。
- **ωB97X-V**（`XC_HYB_GGA_XC_WB97X_V`=466，family=HYB_GGA）flags = `3D|HYB_CAM|VV10`，
  **无 NEEDS_TAU** ⇒ 用的是**原版 VV10**（ω0 由 ρ、σ=|∇ρ|² 构造）。init 里 `nlc_b=6.0; nlc_C=0.01`，
  能量评估挂 `work_gga`。
- **ωB97M-V**（`XC_HYB_MGGA_XC_WB97M_V`=531，family=HYB_MGGA）flags = `3D|HYB_CAM|NEEDS_TAU|VV10`
  ⇒ 用 **rVV10**（需要动能密度 τ 参与正规化）。`nlc_b=6.0; nlc_C=0.01`，评估 `work_mgga`。
- 两者 **(b,C) 相同 (6.0, 0.01)**，差别只在 Φ 核里 ω0 用 `|∇ρ|⁴/ρ⁴ + (4π/3)ρ` 还是掺 τ。

**对本项目的直接含义**：我们全程用 **ωB97X-V**（`XCC="wb97x_v"`）⇒ 对应 **原版 VV10（ρ,σ 基）**，
与 PySCF `numint._vv10nlc` 走的是同一条 ρ/σ 公式路径——**不存在"libxc 用 rVV10 而 PySCF 用 VV10"
的口径错位风险**（那个错位只有在用 ωB97M-V 时才会浮现）。任务书担心的"该对齐哪一个"这里明确：
用 ωB97X-V 就该对齐原版 VV10，我们已经对齐。若日后论文要同时报 ωB97M-V，则核须换成含 τ
正规化的 rVV10，届时需另建校验，不能沿用本表。

公式核对（`gga_xc_vv10.c` 与我们 `nlc.py`/显式和逐项一致）：
`w0=√(C·|∇ρ|⁴/ρ⁴ + (4π/3)ρ)`、`κ=b(3π/2)(ρ/9π)^{1/6}`、`Φ=−3/(2gg'(g+g'))`、
`E_loc=β∫ρ`、`β=(1/32)(3/b²)^{3/4}`——libxc 的 `par_vv10={5.9,0.0093}` 与我们 `b,C` 传入值一致。

---

## 6. 最终回报（对照任务书"最终回报"清单）

- **libxc 是否可用**：部分可用。路线 **1+4**。版本 **7.0.0**（`xc_version_string`/`xc_version` 实测）。
  可绑、可取参数、可逐点算半局部项；**不可**产出 `E_NLC` 总值（无任何 NLC 能量例程）。
  路线 2(pip) 失败（PyPI 无包），路线 3 无走 libxc 的 NLC 能量入口。
- **三方对照表**：见第 2 节；libxc 列全 N/A。我们显式和 ↔ PySCF 原生核在全部 7 档差 ≤ 2.9e-5 kcal。
- **libxc ↔ PySCF 原生核差多少**：**无法直接量化**（libxc 不给 E_NLC 总值）。可量化的是参数表差 =
  **逐位为 0**（b、C 完全相同）。若把"PySCF 有没有独立于 libxc 的核"算进去：PySCF 的核在 `libdft.so`
  且不链 `libxc.so`，但 libxc 无对应核可比。
- **ωB97X-V 是 VV10 还是 rVV10**：**原版 VV10**（HYB_GGA、无 NEEDS_TAU）；ωB97M-V 才是 rVV10。
- **这个裁判有多独立**：**不独立**（第 4 节）——参数表同源、无自有 E_NLC 核；真独立数值锚仍只有 ORCA。

**未得到 + 原因 + 已尝试全部路径**：未得到"由 libxc 自己 NLC 例程算出的 E_NLC 总值"。
原因：libxc 7.x 架构把 VV10 非局域双重和交宿主计算，库内不提供该例程。已尝试：
`nm -D`/`hasattr` 穷举 7 个候选例程（全 False）、权威头文件 grep（只有 `xc_nlc_coef`）、
pip 安装、PySCF 入口穷举、官方源码逐函数确认。**未用推算值顶替**——libxc 列一律记 N/A。
