# R4 收口台账 · CP2K 当 rVV10 裁判的可用边界（2026-10-12）

> 结论一句话：**CP2K 2024.2 能算 rVV10，但算不了 VV10 核形** ⇒
> "同码内 A−B 纯核形差"这个最干净的设计在本机不存在；跨码比较又被半局域/赝势污染。
> 所以"PySCF 的 SCAN_RVV10 不是发表意义上的 rVV10"这条**仍只有结构证据，没有实算裁判**。
> 按方案书 R0 的停机判据，本线到此收口，不再投时间；复跑命令留在文末。

## 一、已验证为真的（全部本机实测，原件见文末）

1. **可用二进制**：`/mnt/e/conda_envs/cp2k24/bin/cp2k.ssmp`（cp2k 2024.2 openblas_nompi，libxsmm 1.17）。
   conda-forge 现役 2026.1/2026.2 要 `GLIBC_2.38`，本机 Ubuntu 22.04 是 2.35 ⇒ 起不来（`fix_cp2k_glibc.log`）。
2. **rVV10 真在这个构建里**（`strings libcp2k.so.2024.2`）：
   `RVV10 Functional: R. Sabatini et al, PRB 87: 041108(R) (2013)`；
   `vdW_kernel_table.dat is for DRSLL and LMKLL and rVV10_kernel_table.dat is for rVV10`；
   `Parameters b and C of the rVV10 functional`；符号 `get_q0_on_grid_rvv10` / `get_q0_on_grid_eo_rvv10`。
   数据目录里 `rVV10_kernel_table.dat` 随包带着。GauXC 命中 0 ⇒ 不需要。
3. **TYPE 枚举里没有 VV10**：`TYPE VV10` → `invalid value for enumeration:VV10`
   （`input_enumeration_types.F:215`）。手册那句"允许 vdW-DF / vdW-DF2 / optB88-vdW / rVV10"是**穷尽**的。
4. **输入语法（试出来的，别再考古）**：
   `&KIND` 的关键字必须换行写；`CUTOFF` 在 `&MGRID` 下不在 `&DFT` 直下；
   `&SCF` 用 `MAX_SCF`（不是 MAX_ITER），`&OUTER_SCF` 也是 `MAX_SCF`；
   SCAN 在 2024.2 既不是 `&SCAN` 也不是 `&LIBXC`（用 `&GGA_X_PBE`/`&GGA_C_PBE` 替代做半局域）；
   `&NON_LOCAL` 认 `TYPE` / `KERNEL_FILE_NAME` / `PARAMETERS`，**不认** `RHO_CUT` / `CUTOFF` / `FUNCTIONAL`；
   坐标直接内联（`&READ_COORDS` 在 2024.2 不是 `&COORD` 的子段）。
5. **一个真算出来的数**：水二聚体 PBE + rVV10(b=15.7, C=0.0093)，GTH-PBE 赝势 + DZVP-MOLOPT-SR-GTH，
   16 Å 立方箱、`&MGRID CUTOFF 300`、SCF 收敛，
   `ENERGY| Total FORCE_EVAL ( QS ) energy [a.u.]: -34.447278039841549`（`run1.out`）。
   CP2K **不单独打印 NLC 项** ⇒ 要取 E_nl 必须差值法（同 deck 去掉 `&VDW_POTENTIAL` 再跑一次）。

## 二、为什么到此收口（不是"做不到"，是"不值得"）

- 最干净的设计是**同码内** A(VV10 核+rVV10 参数) vs B(rVV10 核+rVV10 参数)，半局域/基组/赝势全同，
  差即纯核形差。CP2K 给不出 A（枚举无 VV10）⇒ 设计不成立。
- 退而求其次跨码比（PySCF `scan_rvv10` vs CP2K rVV10）：半局域不同（SCAN vs PBE）、
  芯区不同（全电子 vs GTH 赝势）⇒ 残差里混进两个比核形差还大的量，**判不了**。
- 就算判成了，它也只是 JCTC 的 C3 加分项；C1（证书协议）与 C2（满 S22+异质体系）仍必须做，
  而那两件对 JCP 同样必要 ⇒ 把工作日投到它们上不亏。

## 三、本线留下的可发表素材（不浪费）

1. **语义不一致仍然成立且可引**：libxc 7.1.2 的 `xc_funcs.h` 把 `SCAN-VV10`(584) 与 `SCAN-RVV10`(292)、
   `SCANL-VV10`(704) 与 `SCANL-RVV10`(703) 列为不同功能号；Mardirossian 2017 原文写
   "the difference … originates in the nonlocal correlation kernel" 且 "retained the value of C … b = 6.3"。
   而 PySCF 2.12.1 把 rVV10 参数喂进写死的 VV10 核（`xcfun.py` L320 + `numint._vv10nlc` 核形）。
   ⇒ 正文里能写的是**"参数与核形不匹配"这一结构性观察 + 我们的量化**（换参数动 0.42–0.49 kcal/mol），
   **不能写"PySCF 实现错误"**——没有实算裁判，写了就是越界。
2. 参数敏感性的数（0.42–0.49 kcal/mol，归属带的 8–11 倍）照旧进正文当自我设限。

## 四、复跑命令（谁接手都别再考古）

```
cd /mnt/e/Project/GAMESS/scratch/cp2k_probe
LD_LIBRARY_PATH=/mnt/e/conda_envs/cp2k24/lib /mnt/e/conda_envs/cp2k24/bin/cp2k.ssmp -i probe.inp
# probe.inp 已是可跑的最小 rVV10 deck（PBE 半局域、GTH 赝势、16 A 箱、300 Ry）
# 取 E_nl：把 &VDW_POTENTIAL 整段删掉再跑一次，两总能量相减
```

原件：`fix_cp2k_glibc.log`、`20261012T074040Z_r4_cp2k_three_arms.out`（六跑全 rc=-6 那次，
根因是 `READ_COORDS` 与 `FUNCTIONAL` 两个不存在的段/关键字，不是 CP2K 缺 rVV10）、
`scratch/cp2k_probe/{probe.inp,probe_vv10.inp,run1.out,chk_vv10.out}`。
