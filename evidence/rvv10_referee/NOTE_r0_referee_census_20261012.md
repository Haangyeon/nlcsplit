# R0 判定台账 · rVV10 到底有没有能算积分的独立裁判（2026-10-12）

> 问题：要判"`SCAN_RVV10` 拿的是 rVV10 参数、走的却是 VV10 阻尼核形"这件事，
> 必须有一个**能把非局域积分算出来**的独立实现当裁判。本件逐个实测候选，只登记谁给得出什么。
> 方案书：`paper/notes/PLAN-20261012-rvv10-kernel.md`（R0–R5）。

## 一、候选与实测结果

| 候选 | 能不能给 rVV10 积分 | 一手依据（本机实测 / 官方文档） |
|---|---|---|
| ORCA 6.0.1（本机 + 集群） | **不能** | 关键字卡 `! SCAN-RVV10 ...` → `UNRECOGNIZED OR DUPLICATED KEYWORD(S)`，6 跑全 rc=4（`orca_run_FAILED_keywordcard_20261012/`）；`strings ~/orca6/orca` 里无任何 RVV10 功能名 |
| Psi4 1.7（WSL `psi4env`） | **不能** | `B97M-rV`/`SCAN-rVV10`/`PBE-rVV10`/`WB97M-rV` → `Method=... is not available for any derivative level`；**正对照**：`WB97M-V`/`B97M-V` 通过方法解析（只在几何上报错）⇒ 不是我的调用坏了 |
| libxc 5.2.3（`psi4env/lib`）与 PySCF 自带那份 | **不能** | 只导出 `xc_nlc_coef`；本仓 2026-09-29 的 ctypes 符号审计早已定案 |
| **libxc 7.1.2**（新装 `/mnt/e/conda_envs/xcprobe`） | **不能** | `nm -D libxc.so.15`：NLC 相关只有 `xc_nlc_coef`；ctypes 逐个探 `xc_nlc_vxc`/`xc_nld_vxc`/`xc_vdwnl_kernel`/`xc_setup_kernel`/`xc_run` **全"无"** ⇒ 它连 VV10 的积分都给不出 |
| libvdwxc 0.5.0（同上 env） | **不能** | `strings libvdwxc.so.0.0.0` 里 `vv10` **零命中**；它的核清单是 vdW-DF/vdW-DF2/vdW-DF-cx 那一族 λ 核 |
| **CP2K（conda-forge 2026.2，可装 E:）** | **能（文档层面确认）** | 官方手册 `NON_LOCAL` 段原文："Allows for common forms such as vdW-DF, vdW-DF2, optB88-vdW, **rVV10**" ⇒ 基组型代码，最适合对分子体系 |
| **VASP（SNNU 集群有，需授权确认）** | **能** | wiki `Nonlocal vdW-DF functionals`：rVV10 用 **`IVDW_NL=2`**，`BPARAM` 默认 **6.3**、`CPARAM` 默认 **0.0093**，核 **on the fly**（不需预计算核文件），引 **Sabatini et al. (2013)** |
| Q-Chem | 能（手册有显式开关） | `manual.q-chem.com` NLC 段：`NL_CORRELATION` FALSE=VV10（默认）/ TRUE=rVV10。**是否有单位授权待作者答** |

## 二、R0 结论

**裁判存在，而且不止一个**（CP2K 本机可得、VASP 集群可得、Q-Chem 视授权）
⇒ 方案书里"R4 不通就整条判死"的条件**不触发**，这条值得投 R1–R4 的 2–3 天。

首选 **CP2K**，因为它自己就能提供**同一套代码内的 VV10 控制档**：
先用 CP2K 跑 VV10（PySCF+ORCA 已共同确认过的那条），量出 CP2K 与我们口径的系统偏移；
再跑 rVV10，残差若 ≫ 该偏移，才谈得上"形式不一致"。这与 W0 判定用的结构完全同构，
而 W0 正是靠这个结构把我的第一条疑点**证伪**的——所以这套设计的第一用途是防我自己。

VASP 作备选：PAW + 平面波 ⇒ 密度本身与全电子 AO 不同，必须同样带控制档，且要处理周期性箱子的截断。

## 三、一条附带拿到的、可引用的语义证据

libxc 7.1.2 的 `xc_funcs.h`（本机文件，逐行抄进 `20261012T053850Z_r0_libxc_coef_table.out`）把

```
XC_MGGA_C_SCAN_RVV10   292   /* SCAN + rVV10 correlation */
XC_MGGA_C_SCAN_VV10    584   /* SCAN + VV10 correlation */
XC_MGGA_C_SCANL_RVV10  703
XC_MGGA_C_SCANL_VV10   704
```

列为**不同功能号** ⇒ 在事实权威（libxc 的注册表）里，rVV10 不是"换参数的 VV10"。
这使 PySCF 那条"rVV10 参数 + VV10 核形"的路径**语义上可疑**，但**够不上"实现缺陷"的断言**——
断言仍需 CP2K/VASP 的实算对照 + 原始定义式逐式核（方案书 R1 双源门、R4 控制档）。

## 四、本轮我自己的两个错（记下来防再犯）

1. 把 psi4env 的 `libxc.so.9` 当成 libxc 6.x —— 实际是 **5.2.3**（`strings` 直接给版本号）。soname 数字 ≠ 版本号。
2. `xc_nlc_coef` 的 ctypes 原型猜错 ⇒ 8 个 id **全段错误**（`rc=-11`，见那份 .out 的逐行记录）。
   同一次探针里 `xc_functional_get_number` 对 `VV10`/`RVV10` 返回 −1 也**不是符号坏了**，
   而是必须用规范名：`MGGA_C_SCAN_RVV10` → 292 成功。**"字符串/名字查不到"不等于"功能不存在"**——
   这条本仓已有专门教训（string-absence-is-not-absence），我今天又踩了一遍才算真懂。
