# PROGRESS — agent-orca（追加式日志，只由 agent-orca 本人续写）

## [2026-09-29 13:34] [agent=agent-orca] [orca-anchor] ORCA 6.0.1 **确实会打印** VV10 项：水/苯两条跨程序裁判值落地，差 +0.0004 与 +0.0416 kcal/mol

先说结论，因为这条直接推翻了本次任务开局时的假设。**ORCA 6.0.1 对 `! WB97X-V` 是把
非局域项单独成行打印的**，就在 `DFT components` 块里，标签是 `NL Energy, E(C,NL)`；
不需要 `%%noloc`/`$noloc`，不需要靠 SCF 迭代表的列，也不需要动用"开关 VV10 跑两次相减"
这个退路。所以本报告里所有 E_VV10 都是**程序自己印出来的一个项**，不是两个总能量相减
差出来的——这跟任务书里预设的"最可能的坑"不一样，得按实测改口径。

### 一、我是怎么确认可打印位置的，以及上一次为什么会误判成"只印 EX 和合并 EC"

`ref/h2o_wb97xv.out` 我用 `non.?local|VV10|noloc|NL` 这类词去 grep，只命中 1 处，是 L116
那条版本横幅里的 "NL-DFT gradient (VV10)"。当时很容易就此下结论说"ORCA 不拆这一项"。
但这属于**我的检索词没覆盖到它的用词**，不是"这个量不存在"——ORCA 给它起的名字是
`NL Energy`，里面既没有 "nonlocal" 也没有 "VV10" 这两个子串。这条区分必须写死在流程里：
**"我 grep 到 0 命中"是一句关于我这次检索的话，不是关于 ORCA 输出的话**；要说"不存在"，
得先证明我穷举过它可能的标签。这次我是这么证的：直接把 `DFT components` 整块打出来看，
L655–L658 四行依次是 `E(X)` / `E(C)` / `NL Energy, E(C,NL)` / `E(XC)`，
其中 L657 = `0.042653836648 Eh`；再拿同目录的 `ref/h2o_wb97x.out`（WB97X，**不带** -V）做
对照，那份的同一块里只有 `E(XC)` 一行，没有 NL 行——**这一正一反两个证据合起来才叫
"ORCA 会打印 VV10 项"**，光有正向 grep 不算。`PROGRESS-ide-qoder.md:291` 已经指过这个标签，
我这次是在六个体系上把它实测落实了一遍。

### 二、算了什么，以及每个数的出处（文件:行号）

体系几何一律从 `scratch/lit/s22/S22_02.xyz`（水二聚体）与 `S22_11.xyz`（苯二聚体，几何 A
sandwich）里**原样搬数字**，由 `nlcsplit/ref/orca/make_inputs.py` 生成输入，一个坐标都没有
手抄、没有重写格式、没有改精度。单体取的是**复合物几何上切出来的片段**，不是单体最优几何
——因为被裁判的那份 PySCF 数走的是 `step_h_s22.one()` 里的 superposition 口径（单体经
`geomlib_sub(mol, f)`，坐标与复合物逐原子相同）。片段划分复用 `geomlib` 的 1.65 Å 共价阈值，
切出来的 `dmin` 与 `logs/step_h.json` 里的 `dmin` 对得上（水 1.9516 vs 1.9515856687929185；
苯 3.3748 vs 3.374830010202341），说明我和它切的是同一刀。基组是 **`6-31G*`**：任务书写的是
"6-31G"，但 `step_h_s22.py:28` 的 `BASIS` 默认是 `"6-31g*"`（即 6-31G(d)，重原子带 d 极化），
我按代码而不是按任务书的一句话走，并在 JSON 里留了 `basis_caveat` 记着这个出入。

| 体系 | 本地镜像文件 : 行号 | 印出来的字面值 (Eh) | kcal/mol |
|---|---|---|---|
| 水单体（供体片段） | `nlcsplit/ref/orca/out/h2o_mono0.out` : 654 | `0.042652043659` | +26.76456 |
| 水单体（受体片段） | `nlcsplit/ref/orca/out/h2o_mono1.out` : 652 | `0.042651347418` | +26.76412 |
| 水二聚体 S22 #2 | `nlcsplit/ref/orca/out/h2o_dimer.out` : 674 | `0.084358235133` | +52.93559 |
| 苯单体（环 1） | `nlcsplit/ref/orca/out/benz_mono0.out` : 714 | `0.161347638691` | +101.24717 |
| 苯单体（环 2） | `nlcsplit/ref/orca/out/benz_mono1.out` : 714 | `0.161347638742` | +101.24717 |
| 苯二聚体 S22 #11(A) | `nlcsplit/ref/orca/out/benz_dimer.out` : 799 | `0.315802583977` | +198.16911 |

六个 run 全部 `****ORCA TERMINATED NORMALLY****` 且 `SCF CONVERGED`，`NL Energy, E(C,NL)`
各命中恰好 1 行（这个"恰好 1 行"是脚本硬门，命中 0 或 ≥2 直接抛异常，不许我事后圆场）。
换算系数沿用仓里的 `KCAL = 627.509474`（`step_f_dispersion.py:24`），不另立一套。

**⚠️ 水二聚体必须跑两个单体，不能算 2× 一个。** S22 #2 里供体水的两条 O–H 是
0.9639 / 0.9571 Å、受体是 0.9590 / 0.9590 Å，两者几何不等价，VV10 项差
6.96e-7 Eh（=0.00044 kcal/mol）。这个量级正好和我跟 PySCF 的水差值同阶，也就是说如果我
图省事跑一个单体乘 2，就会凭空造出 ~0.0004 kcal/mol 的系统误差，把本来就 0.07% 的符合
度糊掉。苯那边两个环互为反演，实测差 5.1e-11 Eh，是真正的等价——这条等价的成立与否也是
**测出来的**，不是假设的。

### 三、两条裁判值对比（PySCF 侧照单全收，没有重跑）

| 体系 | ΔE_NLC_ORCA (kcal/mol) | ΔE_NLC_PySCF (kcal/mol) | ORCA − PySCF | 相对 |
|---|---|---|---|---|
| 水二聚体 S22 #2 | **−0.593094** | −0.5934947874882619 | **+0.000400** | 0.067 % |
| 苯二聚体 S22 #11(A) | **−4.325230** | −4.366812838084419 | **+0.041582** | 0.95 % |

PySCF 侧取自 `nlcsplit/logs/step_h.json` 的 `dnlc` 字段（水：level 1、6-31g*、
pyscf 2.12.1、host `Haangyeon`、run_utc 2026-09-29T04:18:21Z；苯(A)：level 1、6-31g*、
pyscf 2.14.0、host `ubuntu`、run_batch `20260928T213839Z_centos-step_h_benz_l1`）。
**论文里"水二聚体 ΔE_NLC = −0.593 kcal/mol"这句话，现在有了第二个程序的独立支持，
误差 4×10⁻⁴ kcal/mol。**

口径能直接相减的依据：ORCA 的 `E(C,NL)` 与 PySCF 的 `numint.nr_nlc_vxc` 报的都是
**双重和 + β∫ρ 的完整 VV10 项**（`step_f_dispersion.py:53,60-61` 自己就写了这个对齐，
`PROGRESS-nlcsplit.md:338` 也记着），而 β∫ρ 那一份在 superposition 差里因为电子数守恒
精确抵消，所以两个程序的 ΔE_NLC 比的是同一件物理量。

### 四、没做到的、以及踩过的坑（这些是负面结果，照实说）

1. **`%pal` 并行在这个容器里是坏的，六个 run 全是串行。** ORCA 起并行时调用
   `mpirun -np N orca_startup_mpi`，而 PATH 上的 `mpirun` 是 `/home/haangyeon/bin/mpirun`，
   它把 ORCA 的参数当非法参数打了 usage 就死在 Startup；我在脚本里试过自动去 ORCA 安装目录
   旁边找自带的 mpirun，**没找到**。np=16/8/4 三次烟测全部 rc=0 但输出里没有 NL 行
   （注意：rc=0 不等于跑成功，这是我脚本的门禁救回来的，纯看 rc 会误判成通过）。
   np=1 正常。串行只影响耗时（最贵的苯二聚体 130 s），不影响 VV10 的数值。
2. **ORCA 输入文件顶层不认 `#` 注释行**，报 `ERROR: expect a '$', '!', '%', '*' or '[' in
   the input / Line 5`。我第一版输入把 provenance 写在注释里，六个体系一起挂掉。现在 .inp
   里一行注释都没有，出处挪到 `nlcsplit/ref/orca/PROVENANCE.txt` 侧车。
3. **`--mem=` 在这套 Slurm 上一律失败**：`scontrol show nodes` 报所有节点
   `RealMemory=1`（集群没记账内存），请求 24G 直接 `Memory specification can not be
   satisfied`；`--share=none` 也是不认的长选项（Slurm 版本偏老），要写 `--exclusive`。
   最后成型的是 `salloc -N1 -n1 -c16 -p cpu -t 00:30:00 --exclusive srun -n1`。
4. **网格两程序没有对齐**，这是 0.95% 那条最可能的来源。ORCA 用默认：主 DFT 网格
   径向 OptM3-with-GC(2021)、角向最大 Lebedev-302、IntAcc 4.388；VV10 另有一套 NL 网格，
   最大 Lebedev-110、IntAcc 4.004（`out/h2o_mono0.out` 里 `NL GRID GENERATION` 段可查）。
   PySCF 侧是 `grids.level=1`。**我没有做 ORCA 网格敏感性扫描**（比如 Grid5/GRID6 重跑一遍
   看苯那条 0.0416 会不会缩），所以这句话只能说"偏差与网格不一致相容"，不能说"已证明是
   网格造成的"。
5. 只覆盖了 S22 的**两个**体系（水、苯 A），不是 step_h 那张表的八行；苯几何 B、苯-水、
   苯-氨、苯-甲烷没有跑。
6. **没有用 Gaussian**，一次都没有。集群上 `/home/XAR/` 下确有 g09/g16，但它的 `-D3`
   经验色散跟 VV10 那个双重积分不是同一件物理量，替代不了，任务书这条红线我照办了。

### 五、诚实纪律：本轮怎么保证不再出现"查无此数"的锚点

`nlcsplit/logs/orca_anchor.json` **不是手写的**，是 `nlcsplit/ref/orca/build_anchor_json.py`
逐个 open 这六个 `.out`、按正则匹配 `NL Energy, E(C,NL)` 与 `Total Energy` 两行，把
**数值 + 行号 + 原始字面行**一起写进去；匹配数不等于 1 就 `raise SystemExit`，宁可不出
文件也不回落到"我记得是"。另外：六份本地镜像与集群原件 **md5 逐一相同**（本轮现场比过），
`mirror_verified` 字段记了这件事；同一次分配里把 `h2o_mono0` 的同一输入重跑了一遍
（`out/smoke_n1.out`），VV10 项复现到 **1.6e-11 Eh**，即 1×10⁻⁸ kcal/mol，这条写进了
`cross_checks.repeatability_h2o_mono0_Ha`。`ref/h2o_wb97xv.out:657` 那个
`0.042653836648 Eh` 我没有拿来当锚点，它是**另一个几何**（独立优化的 r=0.9572 Å、
∠HOH=104.52° 水）下的单体值，跟 S22 复合物片段单体不是一回事——JSON 里以
`prior_ref_water_monomer_standard_geometry_Ha` 的名义单独留着，并写明它为什么不能用。

### 六、现场与产物

集群工作目录 `/home/haangyeon/orca_vv10_anchor/`（没有碰 `/root/GAMESS_BLW`）：
`inp/` 六个输入、`inp_n1/` 串行副本、`run/*.out` 六份输出、`suite.log` 全含带行号的现场
取证、`vv10_anchor.sh`/`launch.sh`。Slurm job 50834，节点 cpu3，
分配窗口 05:24:05Z–05:27:24Z（UTC），套件总耗时 ~3.3 分钟，远低于 20 分钟上限；跑完
`squeue -u haangyeon` 已空，`salloc: Relinquishing job allocation 50834`，没有留占用。
本地产物：`nlcsplit/ref/orca/{inp,out,PROVENANCE.txt,make_inputs.py,vv10_anchor.sh,
launch.sh,build_anchor_json.py,remote_logs/}` 与 `nlcsplit/logs/orca_anchor.json`。
`nlcsplit/` 包代码、`paper/`、`MAIN-skeleton.md` 及其他 agent 的 PROGRESS 文件一行未改，
没有 commit。

**要补下一步的话，优先级最高的是第 4 条**：给 ORCA 做一次网格升档重跑（水那对最便宜，
几分钟就能判掉），看 0.067% 会不会进一步缩到 SCF 噪声底下——那样"跨程序一致"这句话就能
从"0.4 kcal% 级"提到"µkcal 级"。苯的 0.95% 同样值得一试，但 130 s/次串行，升档网格会更久。
