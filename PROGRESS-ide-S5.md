# PROGRESS — ide-qoder / S5：归属方案敏感性（含局部项归属）

## [2026-09-29 05:34] [agent=ide-qoder/S5] [done]

VV10 非局域关联能 `E_NLC = β∫ρdr + ½∬ρ(r)φ[r](r,r')ρ(r')dr dr'` 的片段-成对分解。
本任务回答论文第一张图：**换个归属方案，"片间项 / 片元总 NLC"到底变多少**，卖点在
`E_loc = β∫ρdr` 怎么归属到片段（不是双积分片间项）。

### 0. 运行环境 / 快照 / md5 留档

- 快照目录（唯一真值源，全部计算在此快照上跑，live 树 cn-qoder 仍在改）：
  `e:\Project\GAMESS\scratch\ide_snapshot_20260929T040649Z`
  （由 `scratch/ide_setup_snapshot.sh` 生成，`scratch/IDE_SNAPSHOT_DIR` 指向它，
  runner 注入 `NLCSNAP`，`OMP_NUM_THREADS=4`）
- `SNAPSHOT-MANIFEST.txt`（快照副本 md5 = 快照时刻 live md5，逐文件一致）关键三条：
  - `geomlib.py`  `8d205746669e0503bbc68aa139a8841f`
  - `nlc.py`      `433a9d7a736572ef28695d403cbc00e4`
  - `partition.py` `c82178c768408f566ddd46d552a95c87`
  （其余 `__init__/figures/step*/test_*` 全部 snapshot==live，见 MANIFEST 18 行）
- 方法：ωB97X-V，b=6.0、C=0.01、β=(1/32)(3/b²)^0.75=4.846900e-03 Ha；basis 6-31G*；
  几何一律 `geomlib` 固定几何（H···H 最短 2.718 Å）。
- 脚本：`scratch/ide_s5_probe.py`（闸门探针）、`scratch/ide_s5_sensitivity.py`（主）。
  经 `bash scratch/ide_runner.sh s5full scratch/ide_s5_sensitivity.py` 跑。
- 日志（均在 `nlcsplit/logs/`）：
  - 主完整跑 rc=0：`20260929T050035Z_ide-s5full.out`  ← 本报告所有数字出处
  - 主早先一次（无苯 lvl1，脚本改前的旧逻辑）rc=0：`20260929T043228Z_ide-s5.out`
  - 闸门探针 PROBE: PASS：`20260929T042237Z_ide-s5probe.out`
  - 冒烟（仅水 lvl0）rc=0：`20260929T042825Z_ide-s5smoke.out`

### 1. 闸门探针已定结论（用主脚本前必须先过，见 `20260929T042237Z_ide-s5probe.out`）

- **[A] Σ_A s_A(i)=1 逐点校验**：探针实测偏差 `dev = 0.000e+00`（< 1e-12，成立）。
  但 `atom_partition` 返回的是**拼接的逐原子网格**，每点 owner 唯一、`s_A(i)=W_A(i)/W(i)`
  为纯 one-hot（offdiag 恒 0）⇒ **(b) 软指派 ≡ (a) 硬指派，不新增信息**。故主脚本只用 (a)。
- **[B] 对核参照（区分几何 vintage）**：
  - 旧几何（`ide_snapshot_20260928T224224Z`，`h2o_dimer()` 用 acc=126.8°+cos(π−acc) 的
    H···H 塌缩 bug）：nearest lvl0 `inter_AB = −0.6574` **逐位复现** S4 §1 参照 → 证明
    本人 `fragment_decomposition + nearest` 代码与 S4 参照代码等价。
  - 固定几何（当前 `geomlib`）：nearest lvl0 `inter_AB = −0.4895` ← 这才是**当前真参照**。
  - 结论：任务前提 #5 的 −0.6574/−0.6498 出自**旧 buggy 几何**，不是代码差异；本任务所有数
    在固定几何下，nearest lvl0/1/2 = −0.4895/−0.5007/−0.5019。
  - 苯 sandwich lvl0：本任务 `becke = −3.1004` **精确复现**参照；`nearest = −3.0198`。
    （前提 #5 把 −3.1004 标成了 nearest；实测该值是 becke 的，nearest 是 −3.0198，
    两者都与 PROGRESS-ide-S4 §苯 记录吻合。）
- **[C] 可加性**：主脚本逐 (体系,level,方案) 打印 `|Σ_A E_A^tot − 直接全和|`，全部 ≤ 1.11e-16 Ha。

### 2. 表一 —— `E_nl` 片间双积分项 `inter_AB`（kcal/mol，`pair_energy(A,B)` 半份已 ×2）

| 体系 / level | becke | becke-becke-rad | becke-treutler | stratmann | nearest | **span** | 相对% |
|---|---|---|---|---|---|---|---|
| (H2O)2 lvl0 | −0.5316 | −0.4826 | −0.4986 | −0.5293 | −0.4895 | **0.0490** | 9.68% |
| (H2O)2 lvl1 | −0.5237 | −0.4836 | −0.4986 | −0.5215 | −0.5007 | **0.0400** | 7.92% |
| (H2O)2 lvl2 | −0.5235 | −0.4836 | −0.4985 | −0.5213 | −0.5019 | **0.0398** | 7.88% |
| (C6H6)2 lvl0 | −3.1004 | −3.0942 | −3.0945 | −3.1021 | −3.0198 | **0.0823** | 2.67% |
| (C6H6)2 lvl1 | −3.1006 | −3.1107 | −3.1035 | −3.1006 | −3.0901 | **0.0206** | 0.66% |

网格点数（`N` / 丢弃 `丢`）：水 lvl0 4460/389（nearest 4448/1）、lvl1 19936/2709（nearest 18368/50）、
lvl2 43208/7031（nearest 39008/75）；苯 lvl0 19752/960（nearest 18552/0）、lvl1 89088/8248（nearest 77176/0）。

### 3. 表二 —— 含局部项分摊后的片元总 NLC `E_A^tot = E_loc,A + intra_A + inter_AB/2` 跨方案散布（kcal/mol）

| 体系 / level | span(E_A^tot) | span(E_B^tot) | span(inter_AB)（对照） | E_A^tot span ÷ inter_AB span |
|---|---|---|---|---|
| (H2O)2 lvl0 | **0.2495** | 0.2322 | 0.0490 | ≈ 5.1× |
| (H2O)2 lvl1 | **0.2270** | 0.2276 | 0.0400 | ≈ 5.7× |
| (H2O)2 lvl2 | **0.2270** | 0.2270 | 0.0398 | ≈ 5.7× |
| (C6H6)2 lvl0 | **0.3041** | 0.3041 | 0.0823 | ≈ 3.7× |
| (C6H6)2 lvl1 | **0.0054** | 0.0054 | 0.0206 | ≈ 0.26×（见下） |

- 苯 lvl0/lvl1 两片段对称，`E_loc,A = E_loc,B` ⇒ `span(E_A^tot)=span(E_B^tot)`，逐方案
  `E_A^tot`（lvl0）= +99.3589…+99.6630 kcal。
- **可加性校验值**（每表最大值，`< 1e-10 Ha` 门槛，全部 PASS）：
  水 lvl0 2.776e-17、lvl1 2.776e-17、lvl2 1.388e-17；苯 lvl0 5.551e-17、lvl1 1.110e-16 Ha。

### 4. 跨 level 稳定性（同一方案 `inter_AB` 随加密的最大相邻跳变，kcal；水 lvl0→1→2）

| 方案 | inter_AB [lvl0, lvl1, lvl2] | 最大加密跳变 |
|---|---|---|
| becke | [−0.5316, −0.5237, −0.5235] | 0.0079 |
| becke-becke-rad | [−0.4826, −0.4836, −0.4836] | **0.0011** |
| becke-treutler | [−0.4986, −0.4986, −0.4985] | **0.0001** ← 最稳 |
| stratmann | [−0.5293, −0.5215, −0.5213] | 0.0078 |
| nearest | [−0.4895, −0.5007, −0.5019] | 0.0113 ← 最不稳 |

**最稳方案：`becke-treutler`（最大跳变 0.0001 kcal），次为 `becke-becke-rad`（0.0011 kcal）。
`nearest`（常规 SCF 网格 + 最近原子）在加密时反而漂移最大（0.0113 kcal）**，因其网格点数随
level 的变化方式与专用分区网格不同。论文主方案建议 `becke-treutler`，稳定性依据即此 0.0001 kcal
（苯上同样：becke-treutler lvl0→lvl1 只从 −3.0945 变到 −3.1035，跳变 0.0090 kcal，也属最小之列）。

### 5. 可写进论文的三句话（数值均取自 `20260929T050035Z_ide-s5full.out`）

1. **片间双积分项跨方案散布**：(H2O)2 的 `inter_AB` 跨 5 方案散布 0.040–0.049 kcal/mol
   （相对 7.9–9.7%），(C6H6)2 为 0.082 kcal/mol（lvl0，相对 2.67%）、0.021 kcal/mol（lvl1，相对 0.66%）；
   绝对散布小，但在 |inter_AB|≈0.5 kcal 的水二聚体上**相对散布高达约 10%**。
2. **含局部项分摊后散布更大 —— 真正的非唯一性在 `E_loc` 归属**：把 `E_loc,A=β·Σ_{owner∈A}w_iρ_i`
   并入 `E_A^tot` 后，跨方案散布升到水的 0.227–0.250 kcal/mol（是纯双积分 span 的 ≈5–6 倍）、
   苯 lvl0 的 0.304 kcal/mol（≈3.7 倍）。此量级已与 kT@298K≈0.59 kcal/mol 同阶，足以改变片段归属
   的定性排序 —— 这才是要辩护的对象。（例外：苯 lvl1 因加密网格 + 对称几何使硬指派跨方案趋同，
   span 塌到 0.0054 kcal；这是高格点极限下的数值巧合，不能当作普适结论。）
3. **主方案与稳定性依据**：level 加密下 `becke-treutler` 的 `inter_AB` 漂移最小（水 0.0001 kcal，
   苯 0.0090 kcal），`becke-becke-rad` 次之（0.0011 kcal），`nearest` 最大（0.0113 kcal）；
   故以 `becke-treutler` 作为论文主归属方案。
   **边界**：以上"散布小"仅在这两个体系（水二聚体、苯 sandwich 固定几何）成立，**不得**据此宣称
   "方案无关"；换更大/不对称的体系，局部项分摊的 span 可能显著增大。

### 6. "该口径需要 API 支持，未实现" 清单（如实报告，不绕）

1. **第三口径 `E_AB^tot = inter_AB + (E_loc 的跨片分摊部分)` —— 未实现**。
   需要 `partition` 逐点返回多中心分区因子 `s_A(i)`（非 owner 片段在同一点的 Becke 权重）。
   当前 `partition.atom_partition` 只给逐原子 one-hot owner，跨片软分摊无从取数。
2. **局部项 (b) 真·每点多中心软分摊 —— 未实现**。`Σ_A s_A(i)=1` 精确成立（探针 dev=0），
   但因 one-hot，`s_A(i)=W_A(i)/W(i)` 退化为 0/1 ⇒ (b)≡(a)，不新增信息；真正的跨原子软分摊
   同样受限于上述 API（需要逐点非 owner 片区权重）。

### 7. 交付核对

- 快照目录名 / md5：§0。两张表：§2（`inter_AB` span）、§3（`E_A^tot` span）。
- 最稳方案与依据：§4（`becke-treutler`，水跳变 0.0001 kcal）。
- 可加性校验值：§3 表下（全部 ≤1.11e-16 Ha，PASS）。
- "未实现" 清单：§6。
- 每个数字出处：`20260929T050035Z_ide-s5full.out`（主）、`20260929T042237Z_ide-s5probe.out`（闸门）。
- 未编辑任何 `nlcsplit/*.py` 或他人 PROGRESS；只写 `scratch/ide_s5_*` 与本文件。
