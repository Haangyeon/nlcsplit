# GAMESS-BLW 修复执行方案 v2（2026-09-28，根因已定位）

## Context

主线任务：把 ωB97X-V（CAM range-separated hybrid + VV10 非局域关联）移植进 GAMESS(1) 2014.11.04 + BLW 补丁树（1.31 M 行 F77，无 git，多个 agent 并行盲改）。

此前有三条互斥的诊断，本轮全部用可复现证据裁决：

| 诊断 | 出处 | 结论 |
|---|---|---|
| "int2a.f 缺失 ⇒ 激活器删了 sp 积分代码 ⇒ 重跑 actvte 修 int2a" | 国际版 Qoder 计划 | **否证**：`diff -rq` 对 pristine tar，积分模块（`int2a/2b/2c/2d/2r/2s/2t/2u/2v/2w`、`shells`、`genl`、`infmt`、`basn31`、`bassto`）逐字节一致，未被改动 |
| "半局域 ωB97X-V 系数/装配错 ⇒ 差 19.35 Ha" | 本 agent 上一轮 | **降级**：代码问题真实存在，但所有能量都是在坏的 RHF 路径上量的，数值不作数 |
| "混版编译（273 个 6-04 的 .o + 4 个今天的）导致基线崩" | 本 agent 本轮假设 | **否证**：服务器 16:17 那次是全量重编（277 个 .o 全在今天，`compall.log` 276 次 gfortran + "done with all compilations"），照样给出同样的错值 |
| "已验证/与 LibXC 一致" | `IMPLEMENT-WB97XV-VALIDATION.md` | **否证**：验证对象是同手写的 `vv10_ref.py`，自我循环 |

## 根因（已定位到文件级）

水/STO-3G RHF 的 SCF 迭代表（`/root/gmsout/h2osto/run.log`）：

```
 iter 1   -74.7971647475     ← 初猜能量已在真值(-74.96)附近 ⇒ 一电子积分正常
 iter 2   -51.4713256869     ← 第一次 density→Fock 重建后 +23.33 Ha
 iter 6   -51.4737302299  "DENSITY CONVERGED"   ← 稳定收敛到错误的解
```

轨道本征值 `-27.95, -6.00, -5.42, -5.26, -5.25`——只剩一个深能级，其余挤成团，不是水的谱。

**规律**：单/双中心纯 s 体系全对（He/STO-3G -2.807784 ✓、H₂/STO-3G -1.116999 ✓、H₂/6-31G -1.126809 ✓），凡多中心且含 p 壳即崩（H₂O/STO-3G -51.47、H₂O/6-31G* RHF -52.119、B3LYP -57.899、ωB97X-V -57.035、exam07 HPO -169.5 对期望 -414.1）。

**坏在 density→Fock 重建，即 `source/rhfuhf.src`** —— 它是全树相对 pristine tar 仅有的 4 个改动文件之一（另三个：`dft.src`、`dftgrd.src`、`dftxca.src`，加新增 `dftvv10.src`）。

第二个独立 bug：`ref/agentA/h2o_ch2.inp` 是 H₂O + `CHARGE=2`，但 neutral/CHARGE=2/CHARGE=4 三份日志结果逐字节相同（都是 10 电子、-52.1194371976）⇒ `CHARGE=` 被吞或三份跑的是同一输入，需判定。

**纪律**：下面 Phase 1 通过之前，仓库里任何能量数字（含 `E_VV10_NL = +0.0444425 Ha`）一律不得进文档或结论。

## 执行环境

计算全部在服务器 `10.8.51.23:24522`（8 核 / 23 GB / 50 G 盘剩 17 G，gfortran 有、无 mpif90、无 PySCF）；本地只做读代码与版本管理。凭据只用于会话，不写入任何文件、不入库、不进记忆。

约定：不在 `/root/GAMESS_BLW` 里改动或重编（另一 agent 正在这棵树上工作，16:45 仍有活动）。所有对照构建放 `/root/gamess_work/`，scratch 放 `/root/gamess_work/scr|usr`，日志放 `/root/gamess_work/out`。

## Phase 1 — 归因：是我们改坏的，还是 BLW 补丁本身就坏（约 40 分钟，决定性）

服务器上新建一棵**纯 pristine** 树并全量编译，跑同一条最小梯子：

```bash
mkdir -p /root/gamess_work/pristine && tar -xf GAMESS_BLW.tar -C /root/gamess_work/pristine
cd /root/gamess_work/pristine/GAMESS_BLW && ./config? -> machines/unix/compall (记录所用平台名与全部编译标志)
# 梯子：He、H2/STO-3G、H2/6-31G、H2O/STO-3G、H2O/6-31G*、exam01(TIMLIM 放大)
```

判据与分支：

| pristine 的 H₂O/STO-3G | 结论 | 后续 |
|---|---|---|
| ≈ -74.96（收敛值就是 iter 1 附近并继续下降） | 破坏来自**我们对 `rhfuhf.src` 的改动**（VV10 挂接） | Phase 2A：把 VV10 挂接重做成不侵入 Fock/density 的形式 |
| 仍 ≈ -51.4 | **BLW 补丁本身**与常规 RHF 冲突（或其激活/构建配方不对） | Phase 2B：产品级决策，见"需你拍板" |
| 编译失败或行为不同 | 构建配方不可复现（actvte 平台名/标志缺失） | 先把 `.f` 与标志全部留档，再重跑 |

同时保留 `.f` 激活产物（现在两棵树的 `source/*.f` 都是 0 个，这是本轮无法审计的直接原因）。

## Phase 2A — 修复 RHF 基线（若 Phase 1 归因到我们的改动）

1. `diff -u <(tar -xOf GAMESS_BLW.tar GAMESS_BLW/source/rhfuhf.src) source/rhfuhf.src` 取出全部改动行，逐处判定必要性。当前已知改动：`COMMON /VV10FL//VV10EN//VV10PR/` 声明（1728-1755）、post-SCF 加 `EVV10`（4041-4045）、`CALL PRTVV10`（4086-4088）、遗留调试格式 `9391 'VV10-DBG'`（4490）。
2. 关键检查项：改动是否动了原有 `COMMON` 声明顺序/宽度、是否插入语句打断了 `GO TO` 标签流程（F77 定长标签控制流极易被插入破坏）、是否在 4041 之前改变了 `ETOT` 的赋值路径。
3. 挂接方式改为"最小侵入"：只在 SCF 收敛后、打印前调用一次，不进入迭代内部。
4. 闸门：He / H₂ / H₂O(STO-3G,6-31G,6-31G*) / exam01 / exam07 全部对到位（H₂O/6-31G* RHF 期望 -76.06，容差 < 1e-5 Ha）。

## Phase 2B — 若归因到 BLW 补丁本身：需你拍板

不做自选路线。三个选项的代价差别很大，届时把证据摆给你再定：
(a) 在标准 GAMESS（无 BLW）分支上做 ωB97X-V，放弃 BLW；
(b) 向 BLW 上游取修好的 `rhfuhf.src`；
(c) 绕开：不改 `rhfuhf.src`，把 VV10 做成纯后处理（读收敛密度自行积分），完全不碰 SCF。

## Phase 3 — 基线绿了才做：ωB97X-V 参数与装配（2–4 小时）

权威源只用 libxc 的 `wb97x_v` 定义（服务器无 PySCF/libxc，需取官方源码）；禁止再与本地三份自写 Python 对拍。已知待修点（行号有效）：

1. `dftxca.src:2861-2877` 分支未设 `C2S`/`C2T`/`DHFUNC`（邻居 104 分支 2854-2856 都设）。
2. `dftxca.src:5948-5958` 关联系数只有 3 位有效数字（0.556/-0.257/1.219/-1.850），本文件其余泛函皆 6–7 位；且 libxc 的 ωB97X-V 关联是 PBE 基（c_c^PBE≈0.710）+ |∇ρ|⁴/ρ³ 项，与 GAMESS 的 B97SS/B97AB **不是同一函数形式**——先判定现有形式能否表达，不能则需新增代码。
3. `VV10_B=6.0/VV10_C=0.01`（2875-2876）应为本项目另一文件 `tools/vv10nlc/vv10nlc.py` 已写明的 5.9/0.0093。
4. `ALPHAC=0.167` 需照 PCCP 2014, 16, 9904 核对，并确认 GAMESS 的 CAM 约定里远程分数是 `ALPHAC+BETAC` 还是 `BETAC`。
5. `MU=0.3` 在 `dft.src:902-903`、`ALPHAC/BETAC` 在 `dftxca.src` —— 同一泛函定义散在两文件，收拢。
6. 参数扫面走 `DFTTYP(1..20)`（已由 `$DFT` 读入的数值通道），不要靠改 BLOCK DATA 重编译。

验收：H₂O/6-31G* ωB97X-V 对 `ref/h2o_wb97x.out`（Psi4 -76.3865924435790618）< 1 mHa，**且先核对两侧几何一致**（尚未核，若不同则不可比）。

## Phase 4 — VV10 非局域项（4–8 小时）

1. 核函数以 Vydrov & Voorhis (JCP 133, 244103) / libxc 为准，废掉本地三份互相矛盾的公式（`dftvv10.src`、`vv10_ref.py`、`vv10nlc.py`：后者 `Φ=-3/(2g)`、`κ=C|∇ρ|⁴/ρ²` 却标注"VV10 Eq. 8"）。已确证疑点：`dftvv10.src:231` 把 bohr⁻⁴ 与 bohr⁻³ 相加，量纲不通。
2. 局部项 `+β∫ρdr` 的符号/形式重定（现状水单分子给出 +27.89 kcal/mol，非局域关联不可能为正）。
3. 20 万点静态 COMMON（`dftvv10.src:131`，溢出静默 `RETURN`）改为 DA 动态数组；水默认网格已 62546 点。
4. O(N²) 双循环加分块/距离截断（62546² ≈ 3.9e9 对，单核）。
5. `DO_VV10CAP` 从改源码改为输入开关；删除全树 0 调用的 `VV10CHK`、`INIT_VV10_PARAMS`。
6. 明确记录：后 SCF 近似 ⇒ 无解析梯度 ⇒ 不能做几何优化/频率。是否自洽（VV10 势进 XC）单列为独立决策。

## Phase 5 — 可审计性与收尾

1. 本地 `git init` + `.gitignore`（排除 `object/`、`*.o`、`gamess.00.x`、`ddi`、scratch、`GAMESS_BLW.tar`、`*.gbw`/`*.densities`），首次提交原样入库。
2. 构建配方入库：actvte 平台名、编译标志、`.f` 保留策略、重编步骤（本轮踩的坑就是"只有 4 个 .o 是新的，且 .f 全被删"，导致无法判断链接进去的是哪版代码）。
3. 重跑测试套件当回归闸门时**必须放大 `$SYSTEM TIMLIM`**——`exam01.inp` 里 `TIMLIM=1`，被 1 分钟砍断后我（和国际版）都把优化中间步 -30.706 当成了失败结论。
4. 重写 `IMPLEMENT-WB97XV-VALIDATION.md`：删掉"系数与 LibXC 一致""两侧应逐位一致""毫级差异"等未经独立验证的断言；每个数字标明裁判来源，且该来源与被测代码无共同作者。
5. 清理候选（**需你逐项确认，不自行删除**）：本地 55 MB tar 与解包副本并存、`rhfuhf.f`/`rhfuhf.src` 双份、3 份过期 `compall_*.log`、`rungms1/2/_modified`、`_backup_20260928/*.o`；服务器 `/root/.cache` 4.1 G、`/root/gamess_work` 126 M（我建的）。`/root/mace` 9.1 G 与 `/root/miniconda3` 8.9 G 含 checkpoints/conda env，像是活跃项目，未列入清理。

## 风险与停止条件

- 最大风险是"在坏基线上调参"：Phase 3/4 的任何改进都必须能表示为相对 Phase 2 闸门的增量。
- 时间盒：Phase 1 若 pristine 也错，立即停止源码级猜测，转 Phase 2B 找你拍板。
- 不做的事：不动另一 agent 正在用的 `/root/GAMESS_BLW`；不删任何非我生成的目录；不把凭据写入仓库、脚本文件或记忆。
