# Step 0 先例核查结论：非局域关联能的片段/成对分解

> **本文档与 `HANDOFF-20260928-NLC-decomposition.md` 冲突时以 HANDOFF 为准。** HANDOFF §5 已撤回本文档 §5.1 原先的"精确可加=第一贡献"主张，§2 列出了本文档部分依据已被否证的假设。本文档只保留文献检索部分的价值，立论以 HANDOFF 为准。

**结论：条件性 GO。** 缺口在三个独立检索源里都没有被占据，但"没人做"有两种解释——疏忽，或在定义上不成立——后者会直接否决整篇论文。分辨它们只需要读两篇文章，见 §5。

---

## 1. 检索规模与结果

| 来源 | 查询 | 去重记录 | 备注 |
|---|---|---|---|
| OpenAlex（含出版商摘要） | 18 + 6 组 | 195 | 429 限流导致 4 组首跑失败，已用礼貌队列补齐大部分 |
| Crossref | 15 组 known-item | ~84（与上合并去重） | 常带 Elsevier/ACS 摘要 |
| arXiv | 11 组 | 少量 | API 走代理可用 |
| 合计 known-item 核查 | 12 组（完成 6/12，后台继续） | 84 | 命中即刻落盘，进程被杀不丢数据 |

按与目标缺口的重叠度分级（`step0_triage_known.py`）：

| 级别 | 含义 | 条数 |
|---|---|---|
| **A** | 非局域关联 + 能量分解 + EDA 语境同时出现 | **1** |
| **A2** | **成对/分片的非局域项**（正是你要做的东西） | **0** |
| **B** | 非局域项被实空间分割/分配 | **0** |
| **C** | EDA 中"色散项"的定义问题 | 4 |
| D | 背景 | 72 |

两条关键阴性结果：查询 `VV10 nonlocal correlation energy per fragment pair decomposition` 与 `vdW-DF nonlocal correlation energy real-space partition` 在 OpenAlex 上**返回 0 命中**（不是返回无关结果——是真的 0）。

## 2. 缺口的精确表述

**不存在的工作**：把 VV10 / vdW-DF 的**非局域关联项本身**，在 EDA 框架内归属到片段或原子对，并保持各项之和精确等于原泛函给出的总非局域关联能。

**已存在的三条邻近路线**（它们是这个方向，但不等于上面那句）：

1. **GKS-EDA / ALMO-EDA2** — 确实输出一个"dispersion"分量，但该分量由微扰论或冻密度差**另行定义**，并不是从泛函内部的 NLC 项拆出来的。JCP 2014 原始 GKS-EDA（doi:10.1021/jp500405s）、PCCP 2016 ALMO-EDA2（doi:10.1039/c6cp03784d）、WIREs 2020 综述（doi:10.1002/wcms.1460）。
2. **MBD（Tkatchenko）及其 SQ-MBD 2023 改版** — 原子 Drude 振子模型本就有成对/多体分解，且 SQ-MBD 明确提到"投影相互作用能等可观测量"。**这是离你最近的一篇**，但它分解的是 MBD 模型，不是 VV10 泛函的双重积分。doi:10.1038/s41467-023-43785-z。
3. **libxc / PySCF** — 已经给出**逐网格点**的非局域关联能量密度（见 §3），所以"点级/实空间分割"这件事本身已经是现成的，不构成贡献。

## 3. 技术底座（本地实测，不是推断）

PySCF 2.12.1（WSL）：

- ωB97X-V 能量自洽 ✓：水/6-31G\* 收敛 -76.37689 Ha；ωB97M-V 同样可用。
- **解析梯度 ✓**：STO-3G 下与中心差分相对偏差 ~1e-4 ⇒ NLC 项确实进了梯度。
- **逐点能量密度 ✓**：`nr_nlc_vxc` 内部 `_vv10nlc(...)` 返回的 `e` 形状等于网格点数（实测 9088 点 → `e.shape == weights.shape`），且 `Σ w·ρ·e` 与 `excsum` 精确相等。**结论：点级（Becke/Hirshfeld 加权）分割几乎免费，不值得写成论文。**
- **成对结构 ✗**：`_vv10nlc` 是 C 扩展，只吐出点级 `e` 和势 `v`；成对 (i∈A, j∈B) 的核结构被它的**插值算法吃掉了**（代码里能看到 `nbins`/插值分箱）。⇒ 想做**成对**分解，要么放弃插值改付 O(N²) 的显式双重和，要么发明一个"保持成对结构"的近似。

这才是论文真正的技术张力，比"φ 依赖总密度所以分解不唯一"更具体、更能立住，也更好证明工作量。

## 4. 顺带更正我方先前的两个错误

1. **"`VV10_B=6.0, VV10_C=0.01` 是 bug，应为 5.9/0.0093" — 错。** libxc 自己的表就是：ωB97X-V / ωB97M-V / B97M-V 用 **(6.0, 0.01)**，(5.9, 0.0093) 只属于独立的 `vv10` 条目。GAMESS 那两行参数与 libxc 一致；反倒是仓库里手写的 `tools/vv10nlc/vv10nlc.py` 标错了归属。我上一轮拿一个自写文件当依据，判断错了来源。
2. **"非局域关联能不可能为正" — 错。** 实测 libxc 对同一水分子给 **+0.0426529 Ha (+26.8 kcal/mol)**（6-31G\*，level 3/4 网格一致到 2e-9），分解为局部项 `β·Nₑ = +0.0484690 Ha` 与双积分 `-0.0058161 Ha`。正值是正确物理。GAMESS 的 +0.0444425 Ha 与之只差 1.1 kcal/mol——但这**不能算验证通过**：双积分只是大正数里的一小条负量，其相对误差可以被总差掩盖。等 RHF 基线修好，必须逐点比对 libxc。

另外 libxc 给出 ωB97X-V 的 `rsh_coeff = (ω, c_LR, c_SR) = (0.3, 1.0, -0.833)`（ωB97M-V 为 -0.85），所以 **`ALPHAC=0.167` 确认是错的**，短程 HF 系数应为 -0.833，远程仍须满足 ALPHAC+BETAC = 1.0。

## 5. 决定性两篇的阅读结果

### 5.1 SQ-MBD — 已读**全文**（PMC10716193，正文 118,511 字符）

关键词计数：`nonlocal correlation` **0**、`VV10` **0**、`rVV10` **0**、`vdW-DF` **1**（且只出现在 Berland 那篇综述的参考文献列表里）、`EDA` 1、`ALMO` 1、`fragment` 61。

⇒ **它分解的是 MBD（原子 Drude 振子）模型的能量，不是 DFT 的非局域关联泛函。不构成撞车。**

但它有一句必须正面回应的话（原文）：

> "We stress that such quantification of the fragment contribution to the collective MBD energy is **not unique** since there are multiple ways to partition the pair-fragment contributions."

这句话是坏消息也是好消息：坏在"分解不唯一"这个反对意见已经被提出过；好在它只针对 MBD 的投影相互作用能，与本工作的对象不同。

⚠️ **本节原先的结论已撤销（2026-09-28，按 HANDOFF §5 收口）。** 上一版在这里写的是："VV10 是一个显式双重积分，天然带 (i,j) 成对结构，可以做成精确可加的归属，这是 Drude 振子模型做不到的；因此论文的第一贡献应当是**一个唯一且精确可加的 NLC 成对/片段分解定义**。" 这个卖点被实测否证了：把双重和的求和索引按片段分组后，分片求和与直接求和之差为 **8.7e-19 Ha**，即浮点机器精度。"精确可加"是这个做法自带的属性，不是贡献；SQ-MBD 那句 "not unique" 因此也**不能**用来反衬本工作。

按 `HANDOFF-20260928-NLC-decomposition.md` §5，真正剩下的贡献只有两条：

1. **归属方案（partition / assignment scheme）的定义与辩护。** 非唯一性的真正来源是"网格点、以及局部项 β∫ρdr 归给哪个片段"，不是求和方式。需要给出一个有物理依据的方案，并证明它对网格、基组、分区半径**稳定**，且与 SAPT/MBD 的色散趋势对得上。
2. **保住成对结构的次二次方算法。** 现有加速手段（libxc/PySCF 的插值分箱）与成对分解**互斥**，必须改造；这是唯一的硬算法贡献，也是本工作不会被视为"trivially available"的理由。

**本文档与 `HANDOFF-20260928-NLC-decomposition.md` 冲突时以 HANDOFF 为准。**

### 5.2 JCTC 2023 3c00903（唯一 A 级命中）— **只拿到摘要，正文被 403 挡住**

Crossref 存的摘要原文："By analyzing the interaction energies and their individual components, we demonstrate that there exists variability across different systems for **empirical dispersion models**, which are calibrated for reproducing the interaction energies of specific systems. Thus, parameter fitting may undermine the underlying physics, as dispersion models rely on error compensation among the different components…"

⇒ 从摘要判断，他们分析的是**经验色散模型（DFT-D 类）的分项**，不是把 VV10 的双重积分按片段归属。**归为邻近、非撞车。**

⚠️ 但这是**摘要级证据**。该文发表在 JCTC（正是目标刊），投稿前必须拿正文核实它有没有顺手做 NLC 的分片归属。ACS 有付费墙，需要机构权限。

### 5.3 其余 known-item 核查（Stage C 12/12 完成，128 条去重）

| 查询 | OpenAlex 命中 |
|---|---|
| VV10 非局域项的分片/成对分解 | **0** |
| vdW-DF 非关联能的实空间分割 | **0** |
| Hirshfeld/Becke 分割非局域关联 | **0** |
| Q-Chem/Psi4 中的 NLC 分解输出 | **0** |
| 非局域关联能的解析梯度实现 | **0** ← 注意这条是**假阴性**：PySCF 实测就有解析梯度 |

最终分级：A=1（已判邻近）、**A2=0**、**B=0**、C=5、D=72。

**上面那行假阴性很重要**：它证明开放索引的"0 命中"只能当弱证据——一个明显存在的事实（PySCF 有 NLC 梯度）在 OpenAlex 里查不出来。所以本报告的阴性结果提高置信度，但**不能单独充当 go 的凭据**。

## 6. 判定：**GO，带两个前置**

缺口成立：**把 VV10/rVV10 的非局域关联项在 EDA 框架内做片段/成对归属、并保持各项精确可加**，未见先例。最近的 SQ-MBD 对象不同（MBD 模型）且自陈分解不唯一，这恰好给出你的差异化主张。

两个前置，任一不过就停下改述：

1. **JCTC 3c00903 正文核实**（需 ACS/机构权限）——确认它没有顺手把 NLC 项按片段归属。
2. **WoS / Scopus 一轮系统检索**（需机构登录）——补上开放索引的覆盖漏洞，重点检索 `nonlocal correlation` × `energy decomposition` × `pairwise`，以及 vdW-DF 在**周期性体系**里的分片处理（那个社区更可能已经做过类似的事）。

过了这两关，第一个工程切口就是 §3 指出的真难点：**在保住成对结构的前提下不退化到 O(N²)**——即改造 libxc/PySCF 用来加速的插值方案，使 (i∈A, j∈B) 的核贡献仍可分离。这一条既是论文的技术核心，也是它不会被视为" trivially available"的理由。

## 7. 对"顺手一篇 SoftwareX"的影响

元宝方案里的 Step 1（在 PySCF 上做自洽 VV10 + 梯度 → SoftwareX）**已不成立**：上游全有了。若 §5 判定 GO，SoftwareX 那份产物应当改写成**"NLC 的点级/成对/片段分解层 + 基准数据"**这个真实缺口，而不是又一个 VV10 实现；工程重心随之落到"如何在不退化到 O(N²) 的前提下保住成对结构"。
