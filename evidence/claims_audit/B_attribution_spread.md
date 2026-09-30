# 审计 B：归属不确定性的跨度与"方案 vs 网格/基组"这一比较结论

审计对象（主代理原句）：

> "归属不确定性是内禀的：换片段加权方案给 0.004–0.247 kcal/mol（绝对）、0.8–18.2%（相对）；
> 同一基组阶梯上换方案动 0.038–0.040，而总量本身动 0.17 ⇒ 方案选择比网格更值得报。"

审计方式：只读。所有数从工件原始行重新读出、重新算，不采信 `paper/*.md`、
`MAIN-skeleton.md`、`paper/notes/number_audit.md`、`paper/software_notes/claims_audit.md`
里的任何现成结论（它们只用来指路）。重算脚本：`scratch/audit_B/recompute_B.py`。

---

## 0. 判定

**需要限定**（不是不成立，但句子后半的推论用错了对照轴，且 0.8% 那个端点在"体系×数值"层面配错了行）。

三处必须改：

1. **0.004 与 0.8% 不同体系。** 绝对跨度最小 0.004 属**甲烷二聚体**；相对跨度最小 0.792%≈0.8% 属**苯二聚体(A)**。
   甲烷二聚体在存档 stdout 里自己打的是 **0.9%**（不是 0.8%）。区间本身没错，但
   `paper/main.md:470` 和 `MAIN-skeleton.md:182` 把 `0.004 (0.8%)` 写进了同一行（甲烷），
   与工件矛盾。用户句子只写两个区间、没写配对，所以句子可保留，但读者必然读成配对。
2. **0.038–0.040 vs 0.17 比的是"方案 vs 基组"，不是"方案 vs 网格"。** 两个数都出自
   水二聚体（构造几何）、level 1、五档基组阶梯；0.1680 是**基组漂移**。用它去推
   "比网格更值得报"是换轴。
3. **这两个数甚至不支持"方案 > 基组"。** 0.1680 是 0.0400 的 4.2 倍：基组效应**更大**。
   工件能支持的只有"换基组消不掉方案跨度"（不可约性），不是"方案比数值项量级大"。

"方案 vs 网格"这个说法**另有依据**，但依据是 0.0081 / 0.0002（[S13]），句子里没引。
详见 §5。

---

## 1. 体系 × 数值对应表（绝对跨度，全部 level 1 / 6-31G\* / 无 CP / S22 官方几何）

`nlcsplit/logs/step_h.json` 是被 git 跟踪的机器可读侧车；
`nlcsplit/logs/20260928T193520Z_centos-step_h_l1.out` 是同一批次的 stdout，**未被跟踪**（见 §6）。

| 体系（S22 文件） | natm | P_frz(Becke) kcal/mol | span kcal/mol | span/\|P_frz(Becke)\| | 存了几种方案 | step_h.json 行号 | stdout 行号 |
|---|---|---|---|---|---|---|---|
| 苯二聚体(A) `S22_11` | 24 | −4.037656678 | **0.03196568** | 0.792% | 4 | :16, :21 | （另批次 `step_h_benz_l1`） |
| 苯二聚体(B) `S22_20` | 24 | −2.370536562 | 0.21888889 | 9.234% | 4 | :38, :43 | 同上 |
| 水二聚体 `S22_02` | 6 | −0.601214849 | 0.04347249 | 7.231% | 4 | :60, :65 | :5, :28 |
| 氨二聚体 `S22_01` | 8 | −0.649 | 0.029 | 4.468% | **1** | :82, :84 | :9, :29 |
| **甲烷二聚体** `S22_08` | 10 | −0.474 | **0.004** | 0.844% | **1** | :101, :103 | :13, **:30** |
| **苯-水** `S22_17` | 15 | −1.360 | **0.247** | 18.162% | **1** | :120, :122 | :17, **:31** |
| 苯-氨 `S22_18` | 16 | −1.393 | 0.224 | 16.080% | **1** | :139, :141 | :21, :32 |
| 苯-甲烷 `S22_10` | 17 | −1.442 | 0.213 | 14.771% | **1** | :157, :159 | :25, :33 |

重算得到的区间端点（`scratch/audit_B/recompute_B.py` 段 [1]）：

- 绝对：min **0.004 = 甲烷二聚体**，max **0.247 = 苯-水**。
  甲烷这一条已由 2026-09-30 的现场复算独立复现（`evidence/claims_audit/E_c1_live_recompute.out:12`，
  PySCF 2.12.1 复现 2.14.0 的行，见 §6）。
  苯-甲烷是 **0.213**，不是 0.004 —— 历史上那个错配（`PROGRESS-ide-qoder.md:538-539`
  记录"我 :438 那条 [claim] 写的'苯-甲烷 0.004'是错的"）本次**没有**复发；
  但 `paper/p2_skeleton.md:213` 仍把 0.004 写成"P1 归属跨度"而未标体系。
- 相对：min **0.792% = 苯二聚体(A)**，max **18.162% = 苯-水**。
- 每行 `level: 1` / `basis: "6-31g*"` / `cpcorr: false` 逐一读过（例：甲烷 `step_h.json:104-106`）。

**0.8% 的出处冲突（本审计最硬的一条）**：

| 文本 | 甲烷二聚体的相对值 |
|---|---|
| `nlcsplit/logs/20260928T193520Z_centos-step_h_l1.out:30` | `0.004 (  0.9%)` |
| `MAIN-skeleton.md:182`、`PROGRESS-nlcsplit.md:615` | `0.004 (0.8%)` |
| `paper/main.md:470` 表行 | `-0.474 \| 0.004 \| 0.8%` |
| 重算 0.004/\|−0.474\| | 0.844% → 0.8% |

`nlcsplit/step_h_s22.py:148` 打印百分比用的是**未舍入**的 span，排版用 `{span:6.3f}` 打绝对值，
所以 stdout 的 0.9% 是真值、正文的 0.8% 是"拿 3 位小数的 span 去除 3 位小数的 becke"重算出来的。
反推真值区间：stdout 印 0.9% ⇒ ratio ∈ [0.0085, 0.0095)，\|becke\| ∈ [0.4735, 0.4745)
⇒ **span_true ∈ [0.00403, 0.00450)**，即真实相对值是 0.85–0.95%，**0.8% 落在其下界之外**。

---

## 2. "换片段加权方案"到底是哪几种

实现：`nlcsplit/partition.py:17-22`，`SCHEMES` 恰好 4 项，全部是 Becke 乘积划分的变体：

| 键 | 划分核 | 半径修正 |
|---|---|---|
| `becke` | `gen_grid.original_becke` | 无 |
| `becke-becke-rad` | `gen_grid.original_becke` | `radi.becke_atomic_radii_adjust` |
| `becke-treutler` | `gen_grid.original_becke` | `radi.treutler_atomic_radii_adjust` |
| `stratmann` | `gen_grid.stratmann` | 无 |

跨度定义：`nlcsplit/step_h_s22.py:116` `span = max(pint.values()) - min(pint.values())`，
循环在 `:54-62`（四方案各跑一遍 `atom_partition(level=LEVEL, scheme=...)`）。
`nlcsplit/step_g_basis.py:21,46-53` 是同一四方案。

- **没有 Hirshfeld**。全仓 `hirshfeld` 只出现在文献检索串和相关工作正文
  （`paper/main.md:201`、`paper/notes/novelty_crosscheck.md`、`MAIN-skeleton.md:47`），
  没有任何实现或计算。
- **nearest-atom 不是第 5 个方案**。`partition.nearest_partition`（`partition.py:142-146`）
  只用于 `step1_validate.py:72-73` 与两个测试（`tests/test_regression.py:43`、
  `tests/test_tolerance_probe.py:38`）做"软=硬"一致性校验；不在 `SCHEMES` 里，进不了 span。
  唯一把 nearest 一起列进表的是敏感性探针 `scratch/ide_s5_sensitivity.py`（快照脚本，非发布件），
  它对水二聚体的 span 没有影响（nearest 值落在四方案之内）。
- `paper/main.md:288-291` 的措辞（"four variants … plus a nearest-atom hard partition on the
  common grid **as a control**"）与代码一致 ✓。

**"同一套几何、同一档网格"核对结论：网格与基组一致 ✓，几何与运行批次不完全一致 △。**

一致的部分：8 行逐行 `level: 1`、`basis: "6-31g*"`、`cpcorr: false`；片段划分统一由
`geomlib.split_frags()` 按共价连通性给出（`step_h_s22.py:39` + `geomlib.py:185-189`，切不出 2 段就报错）。

不一致的部分：

| 维度 | 情况 |
|---|---|
| 几何目录 | 文件头 `geometry_source: /mnt/e/…/scratch/lit/s22`（`step_h.json:5`），但两条苯行 `run_batch: 20260928T213839Z_centos-step_h_benz_l1`（`:27, :49`）来自远端 `/root/gamess_work/nlcsplit/s22`（`step_h_benz_l1_remote.json:5`）——两份 S22 拷贝，无哈希可证逐字节相同 |
| PySCF | 水二聚体 2.12.1 / host Haangyeon（`:70-71`），其余 2.14.0 / host ubuntu（`:88, :107, :126…`） |
| 批次 | 5 行 `20260928T193520Z`、2 行 `20260928T213839Z`、1 行本地重跑 |
| 存档精度 | 只有 3/8 行存了四方案原值；另外 5 行 `pint` 里只有 `becke`，`span` 以 3 位小数存 —— **0.004 和 0.247 这两个端点恰好是证据最薄的那两行** |

---

## 3. 相对值 0.8% / 18.2% 的分母

**分母 = 该体系自己的 \|P_frz(Becke)\|**，即 Becke 方案下的片间成对项，不是 ΔE_int，也不是 ΔE_NLC。

- 代码：`nlcsplit/step_h_s22.py:148`
  `r['span']/abs(r['pint']['becke'])*100`。
- 正文与之一致：`paper/main.md:461-462` "measured against the Becke-scheme interfragment term"、
  图 2 说明 `paper/main.md:481`、`nlcsplit/figures.py:57`（图也用 `span/abs(pint.becke)`）。
- 18.2% = 0.247/\|−1.360\| = 18.16%（苯-水）**✓ 可核**。
- 0.8% = 0.03196568/\|−4.0376567\| = 0.792%（苯二聚体 A）**✓ 可核**；
  若按正文表行读成甲烷，则与 stdout 的 0.9% 冲突（§1）。

**口径隐患（同一仓里有三套"相对"分母）**：

| 工件 | 分母 | 水二聚体 lvl1 相对值 |
|---|---|---|
| `step_h_s22.py:148` / `step_h.json` / 图 2 | \|P_frz(Becke)\| | 7.231%（官方几何） |
| `paper/main.md:132` | 写作 `\|E_AB\|` | — |
| `scratch/ide_s5_sensitivity.py:120` | `abs(np.mean(inter))`，五方案均值 | 7.92%（`logs/20260929T050035Z_ide-s5full.out:25`，构造几何） |

`E_AB` 与 `P_frz` 在本仓是同一个量（`nlcsplit/nlc.py:137` `inter[(A,B)] = 2.0*blk(A,B)`，
`step_g_basis.py:35` 记作 `E_AB`、`step_h_s22.py:62` 记作 `P_frz`，正文定义在 `paper/main.md:274`），
所以 `main.md:132` 的 `\|E_AB\|` 不算错，但和同文 `\|ΔE_int\|`（水 −7.816）、`\|ΔE_NLC\|`（水 −0.593）
只差一个下标，容易被读成后两者——水二聚体若误用 ΔE_NLC 作分母会得到 7.33%。

---

## 4. "同一基组阶梯上换方案动 0.038–0.040，而总量本身动 0.17"

唯一出处：`evidence/recompute/20260929T003144Z_stepg-recompute.out`
（`nlcsplit/logs/` 下有同内容副本；`evidence/recompute/MANIFEST.sha256` 已收录该文件）。
生成脚本 `nlcsplit/step_g_basis.py`。

| 属性 | 值 | 依据 |
|---|---|---|
| 单位 | kcal/mol | `step_g_basis.py:17 KCAL=627.509474` |
| 体系 | **水二聚体**（仅此一个） | `step_g_basis.py:40 "== 水二聚体 …=="` |
| 几何 | **构造几何** `geomlib.h2o_dimer()`，R(O···O)=2.983 Å，非 S22 官方文件 | `step_g_basis.py:26`、`geomlib.py:87-101`、`geomlib.py:11-14` |
| 网格档位 | **level 1**（五档同一 N=19936） | 文件 `:1 NCLV=1`、`:2 level=1`、`:4-8` N 全为 19936 |
| 基组列表 | sto-3g, 6-31g\*, aug-cc-pvdz, def2-svp, def2-tzvp | `step_g_basis.py:19-20` |
| 0.038–0.040 | 除 STO-3G 外四档的方案跨度：0.0400 / 0.0382 / 0.0390 / 0.0398（`:5-8`） | 重算 `min=0.0382 max=0.0400` |
| 0.17 | P_frz(Becke) 沿阶梯 −0.3857(`:4`) → −0.5537(`:6`) = **0.1680** | `:12` 自打 `aug-cc-pvdz 四方案 max\|Δ\| +0.1680` |

**必须补的三点：**

1. **"across five basis sets" 站不住**：五档全跨度是 **0.0249–0.0400**（STO-3G 打破区间）。
   `0.038–0.040` 只能覆盖后四档。
2. **0.17 有歧义**：`evidence/centos/20260928T165857Z_centos-step2.out:17` 另有
   "E_AB 全体跨度 = **0.1747**"（那是网格×基组**合并**跨度，含 level 0）。两个数都四舍五入到 0.17，
   而句子后半引的是 [S12]（0.1680）。同一句里换轴时极易串。
3. **量级方向反了**：0.1680 / 0.0400 = **4.2**。在同一个体系、同一档网格上，
   **基组效应比方案跨度大 4.2 倍**。工件支持的是"换基组消不掉方案跨度"（不可约），
   不是"方案比数值项更值得报"。`MAIN-skeleton.md:135` 的原始判读写的正是
   "**换基组消不掉**"，`paper/main.md:499` 写的也是 "No better **basis set** will remove it"。

---

## 5. "方案 vs 网格"到底有没有依据？有，但不是这两个数

| 对照轴 | 方案跨度 | 数值项跨度 | 比值 | 工件 |
|---|---|---|---|---|
| 方案 vs **基组** | 0.0400（6-31G\*, lvl1） | 0.1680（五档基组漂移） | **基组大 4.2×** | `evidence/recompute/…stepg-recompute.out:5,12` |
| 方案 vs **网格** | 0.0400（6-31G\*, lvl1） | 0.0081（同一构造几何、6-31G\*、level 0→2，Becke 单方案） | **方案大 4.9×** | `evidence/centos/…step2.out:19`；lvl1→2 仅 0.0002（`:8,:9` 之差） |
| 方案 vs **网格**（level 0→1） | 0.0490 → 0.0400 | 0.0081 | 方案跨度自身随网格动 **0.0090** | `nlcsplit/logs/20260929T050035Z_ide-s5full.out:15, :25` |

所以：

- "方案 > 网格"**在工件里有依据**，靠的是 0.0081 / 0.0002（正文 `paper/main.md:499-501` 也确实是这么写的，标 [S13]），
  **句子里的 0.038–0.040 vs 0.17 推不出它**。
- 且它只在 level 1→2 之间干净成立。level 0→1 时**方案跨度本身**从 0.0490 掉到 0.0400（动 0.0090），
  与整条 0.0081 的网格不确定度同量级，因此"不随更细的网格收缩"（`paper/main.md:614`）只对 level ≥1 成立。
- 交叉核对：0.0081 来自 `step2_convergence.py`（Becke 单方案跨 level，`:29` 默认 scheme="becke"），
  与 S12 同为构造几何、6-31G\* level 1 处逐位吻合（两边都 −0.5237）⇒ 比值可比。
  但正文自己承认 S13 的批次早于几何修正
  （`paper/main.md:770-774`："S13's cross-grid spreads are read here as measured on the *initial*
  S22 geometry … re-running the full ladder on the relaxed geometry stays an open task"）。
- **只有水二聚体一个体系**同时具备方案跨度与网格跨度。没有任何工件在 8 体系表上同时量过两根轴。

---

## 6. 证据强度：0.004 / 0.247 的一手见证没有被存档

`nlcsplit/logs/.gitignore:1` 是 `*.out`。经 `git check-ignore -v` 确认，
`nlcsplit/logs/20260928T193520Z_centos-step_h_l1.out`（唯一同时打印
`方案跨度 0.004`、`方案跨度 0.247` 与 `0.004 ( 0.9%)` 的文件）**未被 git 跟踪**，
也不在任何 `evidence/*/MANIFEST.sha256` 里（`evidence/centos/MANIFEST.sha256` 只收 4 个文件）。

后果：

- level 1 的 S22 跨度只以 `step_h.json` 里 **3 位小数**的 `span` 存在，且 5/8 行不存四方案原值。
- **0.9% vs 0.8% 这个矛盾无法仅从跟踪件判定**——0.9% 的唯一见证是未跟踪文件。
- 唯一被跟踪 + 哈希过的同表 stdout 是 **level 2 + 反泊松** 的
  `evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out`
  （`:16` 甲烷 **0.003**、`:21` 苯-水 **0.248**），配套 `nlcsplit/logs/step_h_l2cp.json`（跟踪 ✓）。
  ⇒ 在**已存档**的证据上，绝对跨度是 **0.003–0.248**，不是 0.004–0.247。
  正文 `paper/main.md:677` 的"to within 0.001 kcal/mol between grid levels 1 and 2"说的正是这个差，
  但它没有交代**端点自身会随档位换数字**。
- `paper/main.md:738-741` 附录声称 "those stdout files are tracked, hash-listed under
  `evidence/*/MANIFEST.sha256`"，对 level-1 的 step_h stdout 不成立。

**补充（2026-09-30 现场复算，独立佐证）**：`evidence/claims_audit/E_c1_live_recompute.out:12`
（并行的 C1 复算，PySCF **2.12.1**/host Haangyeon，脚本 `scratch/recheck_c1.py`，
`basis=6-31g* level=1 cpcorr=0`）现场重跑甲烷二聚体，得
`P_frz[becke] -0.474  方案跨度 0.004  ΔE_NLC -0.517  ΔE_int -0.664`，
与存档行（`step_h.json:101,103`，PySCF 2.14.0/host ubuntu）**逐位吻合**；同文件 `:7` 复算水二聚体
得 `0.043 / -0.601`，也与存档一致。⇒ **0.004 属甲烷二聚体这一点现在有第二台机器、第二个 PySCF
版本独立复现**，历史错配（苯-甲烷）确认未复发。
但该复算走的是 `step_h_s22.one()`，未执行打印百分比的 `__main__` 尾部，
所以 **0.8% vs 0.9% 的冲突仍未被终裁**——现场只印出 `{span:6.3f}` 的 0.004。

---

## 7. 限定后的措辞建议

### 7.1 中文（替换原句）

> 归属不确定性是内禀的：在 8 个 S22 复合物的官方几何上（ωB97X-V/6-31G\*，网格 level 1，
> 四种 Becke 族划分方案），同一个片间成对项随方案变化的绝对跨度为 0.004–0.247 kcal/mol，
> **两个端点属于不同体系**（0.004 为甲烷二聚体，0.247 为苯-水）；相对该体系 Becke 值的跨度为
> 0.8–18.2%，**下界 0.8% 属苯二聚体(A)，而非甲烷二聚体——甲烷在存档输出里记作 0.9%**。
> 在构造几何的水二聚体上、同一档网格（level 1）换五档基组，方案跨度保持 0.0249（STO-3G）、
> 0.0382–0.0400（其余四档），而量本身沿基组走 0.168 kcal/mol：**基组效应仍比方案跨度大 4 倍，
> 换基组不能消掉的是方案跨度本身**。与网格的对照要另看：同一几何、同一基组下 level 0→2 的
> 网格不确定度是 0.0081 kcal/mol（level 1→2 仅 0.0002），比 level 1 的方案跨度小 5 倍——
> **方案选择因此比网格更值得报，但这条依据是 0.0081，不是 0.17**。

### 7.2 英文（若要落进 `paper/main.md`）

> Attribution uncertainty is intrinsic. Over eight S22 complexes at official GMTKN55 geometries
> (ωB97X-V/6-31G\*, grid level 1, four Becke-family partition schemes) the same interfragment pair
> term spans 0.004–0.247 kcal/mol depending on the scheme — endpoints from different systems
> (0.004 methane dimer, 0.247 benzene···water) — and 0.8–18.2% relative to each system's own
> Becke value, where the 0.8% lower bound belongs to benzene dimer A (0.03197/4.03766) and the
> methane row is printed as 0.9% in the archived stdout. On the constructed water-dimer geometry
> at level 1 across five basis sets the scheme spread stays 0.025 (STO-3G) and 0.038–0.040
> (the four larger bases) while the quantity itself drifts 0.17 kcal/mol along the same ladder:
> **the basis effect is still four times larger, and what a better basis cannot remove is the
> scheme spread itself.** The comparison against the *grid* is a different pair of numbers —
> 0.0081 kcal/mol over level 0→2 at 6-31G\* (0.0002 over level 1→2) on that same geometry, five
> times below the level-1 scheme spread — and that, not the basis ladder, is why the scheme
> choice rather than grid convergence has to be reported.

### 7.3 若坚持保留原句结构，最小改动清单

1. `0.8%` 后面加 "(0.004 and 0.8% are different systems: methane dimer and benzene dimer A;
   the archived stdout prints 0.9% for methane)"。
2. 把 "而总量本身动 0.17 ⇒ 方案选择比**网格**更值得报" 改为
   "… ⇒ **换基组消不掉方案跨度**"，另起一句用 0.0081/0.0002 谈网格。
3. "同一基组阶梯"补限定：**水二聚体、构造几何、level 1**（与 0.004–0.247 的
   S22 官方几何不同族；官方几何的水二聚体跨度是 0.043/7.2%，构造几何是 0.040/7.6%）。
4. "0.038–0.040" 前加 "for the four bases beyond STO-3G"。

---

## 8. 证据不足的部分（直说）

- **0.004 与 0.247 的四方案原值不在任何被跟踪工件里。** 只能信 3 位小数的 `span`
  与未跟踪 stdout 的行；无法重算、无法证伪。
- **甲烷 0.9% 的唯一见证未入库**，因此 §1 的"0.8% vs 0.9%"冲突在严格审计意义上不可终裁。
- **方案 vs 网格只在 1 个体系、1 个基组上可比**（水，6-31G\*，构造几何），且 S13 的 level 0
  行属于几何修正前的批次（`paper/main.md:770-774` 自认）。
- 两套 S22 几何目录（本地 `scratch/lit/s22` 与远端 `/root/gamess_work/nlcsplit/s22`）
  无哈希对照，"同一套几何"只能到"同一份官方 GMTKN55 来源"这个强度。
- 未做任何重算运行（只读约束，且 PySCF 环境未确认）；所有数来自存档工件的读取与四则运算。

---

## 9. 工件清单（本次读过的）

`nlcsplit/logs/step_h.json`、`step_h_l2cp.json`、`step_h_benz_l1_remote.json`、
`20260928T193520Z_centos-step_h_l1.out`(未跟踪)、`20260928T193520Z_centos-step_h_benz_l0.out`、
`20260929T003144Z_stepg-recompute.out`、`20260929T050035Z_ide-s5full.out`、
`evidence/centos/20260928T165857Z_centos-step2.out`、
`evidence/recompute/20260929T003144Z_stepg-recompute.out`、
`evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out`、
`evidence/{centos,recompute,l2cp}/MANIFEST.sha256`、
`nlcsplit/partition.py`、`nlcsplit/step_h_s22.py`、`nlcsplit/step_g_basis.py`、
`nlcsplit/step2_convergence.py`、`nlcsplit/geomlib.py`、`nlcsplit/nlc.py`、`nlcsplit/figures.py`、
`scratch/ide_s5_sensitivity.py`、`scratch/recheck_c1.py`、
`evidence/claims_audit/E_c1_live_recompute.out`（现场复算佐证，见 §6）、
`MAIN-skeleton.md`、`paper/main.md`、`PROGRESS-nlcsplit.md`、
`PROGRESS-ide-qoder.md`、`paper/p2_skeleton.md`、`paper/software.md`。

重算脚本：`scratch/audit_B/recompute_B.py`（只读工件，输出见 §1/§4/§5）。
