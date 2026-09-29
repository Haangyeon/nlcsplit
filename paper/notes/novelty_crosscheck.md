# 第二轮跨库新颖性核查（OpenAlex / Semantic Scholar / arXiv / Crossref / Scopus）

执行时间：2026-09-29，11:03–12:05 UTC（单次会话，全部走公开 REST API，无登录、无浏览器自动化、无 DOM 抓取）。
执行者：qfmodel 子代理。原始返回全部落盘 `paper/notes/raw/*.json`（文件名带 UTC 时间戳，共 29 个）。
被核查的主张：**把 ωB97X-V 的 VV10 非局域关联项 `E_NLC`（O(N²) 网格双重和）按片段/原子对做空间归属分解，并给出可复现实现。**

---

## 0. 先划性质：这一轮**不是**第二个正式索引

- 本轮全部来自开放网络 API。命中**不可复现**（索引快照随时间漂移、匿名路由受服务端容量支配），
  因此**不计入正文 PRISMA-S 的正式检索计数**，只能作为"补检证据 / 查漏证据"。
- 正式索引仍然只有 **Web of Science Core Collection 一个**（`RESEARCH-20260929-lit.md` §12–§13，
  全量枚举，`RecordsSearched = 58,664,816`）。本轮的价值是**找 WoS 漏掉的近邻**，不是把"一个索引"改成"五个索引"。
- 一条实测到的索引间一致性可以引用：OpenAlex 在 **title+abstract 级**执行
  `"VV10" AND "energy decomposition"` 得到 **1 条**，且就是 WoS 同一轮得到的那唯一一条
  （Kruse, Banáš & Sponer, JCTC 15, 95, DOI 10.1021/acs.jctc.8b00643）。
  这是两个独立索引在同一主张式上给出同一集合，不是两个独立"正式"检索。

---

## 1. 结论先行：威胁等级

### 1.1 有没有"已做同一件事"的先例？——**没有**

在四个可达库、40 条关键词检索式（其中 21 次执行成功拿到服务端自报计数）、
以及 17 次"种子—被引"图遍历（OpenAlex 10 + Semantic Scholar 7，去重后 **6,970 条记录**）下，
**未出现把 VV10/rVV10 非局域关联双重和按片段对（或原子对）做事后归属的在先工作**。

三层筛子，逐层收紧，全部为空：

| 筛子 | 覆盖范围 | 结果 |
|---|---|---|
| 题名级两维同现（非局域词 × 归属词） | WoS 之外最大池：去重 6,656 条被引记录 | **0** |
| 题名+摘要级两维同现 | VV10 直接相关种子的 1,669 条（其中 1,416 条有摘要） | **38** 条，逐条读后**无一同主张**（见 §5） |
| **句级同现**（归属措辞与非局域项出现在同一句） | 同上 1,416 条摘要 | **0**（该正则用三条构造正控验证过会开火，另有一条负控不开火） |

### 1.2 但**发现两条必须划界的近邻**，它们会改写正文的措辞 → 威胁等级：**中**（措辞级，不推翻主张）

**(A) Heßelmann 的非局域修正方案（NLDFT）—— 本轮真正的新增风险点**

- `10.1021/ct300735g`（Heßelmann, *J. Chem. Theory Comput.* **9**(1), 273–283；DOI 与卷页已用 OpenAlex
  `biblio` 回查确认。⚠ OpenAlex 的 `publication_year` 字段是 **2012**，而 2018 那篇正文逐字把它引作
  "[J. Chem. Theory Comput. 9, 273 (2013)]"——卷 9 期 1 的印刷年应是 2013，属 online-first 与 issue 年不一致；
  进 bib 前要用 Crossref `published-print` 再定一年）摘要原文：
  > "A nonlocal correction method to (semi)local density-functional theory (DFT) methods is derived
  > that is based on **a partitioning of the correlation-energy density into atom-atom contributions**."
- `10.1063/1.5032175`（Heßelmann, *J. Chem. Phys.* **149**, 044103 (2018)，被引 3；卷页已 `biblio` 回查）：
  为上面那个方法的能量梯度求解析导数，
  做 76 个三肽与若干非共价二聚体的几何优化；摘要称"the inherent **Hirshfeld weights** are described in terms
  of analytic expressions of the atomic densities"。
- **重叠在哪个维度**：在"**把非局域关联能按原子对摊开**"这个动作上与我们重叠。
- **不重叠在哪**：(1) 摊开的是**他自己构造的**非局域泛函，不是既有 VV10/ωB97X-V 的 `E_NLC`；
  (2) 粒度是 atom–atom，不是 named **fragment** pair；(3) 目的是造方法/做几何优化，不是事后记账；
  (4) 没有讨论"不同划分方案之间同一个片间量能差多少"——那正是我们测出来的 0.004–0.247 kcal/mol 跨度。
- **对正文的硬约束**：**"第一个把非局域关联能按原子对归属"这类句子不能写**。主张必须收窄为
  "**对既有 VV10 项做事后片段对归属**"。
- **为什么 WoS 那一轮会漏**：它的题名用的是 "nonlocal density-functional theory method" 与
  "double Hirshfeld partitioning"，**不含 "nonlocal correlation" 这个词组**；
  §13.4 的 D 式（`"nonlocal correlation" AND (Becke OR Hirshfeld OR …)`）是精确短语匹配，抓不到它。
  这与 §13.5 Hyldgaard 那条是**同一种失效模式**：关键词形状的查询比它要检验的主张窄。

**(B) "显式 N² 求值"与"成本"这条轴上的既有标准做法 —— 引用缺口，不是先例冲突**

- `10.1103/PhysRevLett.103.096102`（Román-Pérez & Soler, PRL 103, 096102 (2009)，被引 **1,594**）
  "Efficient Implementation of a van der Waals Density Functional: Application to Double-Wall Carbon Nanotubes"。
- `10.1103/physrevb.87.041108`（Sabatini, Gorni & de Gironcoli, PRB 87, 041108 (2013)，被引 **738**）
  "Nonlocal van der Waals density functional made simple and efficient"——摘要明写修订 VV10
  使"nonlocal correlation energy **and its derivatives** to be efficiently evaluated in a plane wave framework"，
  并指向上一篇。
- `arXiv:2511.04169`（2025 预印本，Crossref/OpenAlex 未见期刊版）"Nonlocal van der Waals density functional
  made faster"：把六维积分的被积函数近似成少量"密度状分布 × 距离势函数"的乘积，走 fast multipole /
  高斯基解析求值。**不做归属**（属"做了非局域项但不分解"）。
- `references.bib` 现在**这三条都没有**。一篇卖点包含"我们显式求这个双重和"的稿子不引这两篇实现级文献，
  审稿人会直接指出。JuNoLo（§10）已经把"显式求值不是首创"钉过一次；这里是第二次、且是**更主流**的那条线。

### 1.3 判词一句话

**新颖性存活，但主张必须比现在更窄：卖点只能是"对既有 VV10 项的片段对归属 + 划分方案之间的跨度"，
不能是"非局域项的空间归属"本身，也不能是"显式/高效求值"。**

---

## 2. 各库可达性（实测判据，非推测）

| 库 | 端点 | 本轮状态 | 判据（原始返回里可查） | 结论标签 |
|---|---|---|---|---|
| OpenAlex | 非 search 路由：`/works/doi:`、`/works?filter=cites:`、`/works?filter=openalex_id:` | **可达，全程稳定** | 10 次种子遍历共取回 7,654 条被引记录；1,773 条摘要批量取回，0 个失败批次 | `ACCESSIBLE`（引用图 + 已知条目核验） |
| OpenAlex | search 路由：`?search=`、`filter=title_and_abstract.search:` | **间歇可达** | 45 次尝试：21×HTTP 200、14×HTTP 429、10×HTTP 503；503 正文为 "Anonymous search is paused while the search cluster recovers from heavy load"，429 正文 "temporarily rate-limited … retry in 37s" | `PARTIAL / RATE_LIMITED` |
| OpenAlex | `?title_and_abstract.search=`（作**查询参数**） | **已失效** | HTTP 400 + "title_and_abstract.search is not a valid parameter"；现只作 `filter=` 键有效 | `API_CHANGED`（`RESEARCH` §1 那批旧式若重放会全 400） |
| Semantic Scholar | `/graph/v1/paper/DOI:…/citations`、`/references` | **可达** | 7 个种子成功返回，共 314 条去重被引；`/references` 返回 `data:null` | `ACCESSIBLE`（仅引用图，见 §4 的截断声明） |
| Semantic Scholar | `/graph/v1/paper/search` | **不可用** | 两次尝试（会话首、会话中）均 HTTP 429 "Too Many Requests … apply for a key"；未循环重试 | `RATE_LIMITED`（关键词维度＝**未查**） |
| arXiv | `https://export.arxiv.org/api/query` | **可达但未过校准** | 17 条式全部 HTTP 200；但正控失败：`abs:"VV10"` 总命中仅 **5**，而我用 `id_list` 独立确认 arXiv:2208.02841 摘要含 "VV10" 却**不在**返回集内；`ti:"rescaled van der Waals"`＝0 | `INSTRUMENT_FAILED`（其 0 命中一律不作数） |
| Crossref | `/works?query.bibliographic` | **可达但只适合已知条目** | 4 条主题式返回 total 3.3M/10.5M/1.1M/2.7M 且首位是 `.s001` 支持信息文件；与 §9 同病 | `ACCESSIBLE_KNOWN_ITEM_ONLY` |
| Crossref | `/works?filter=references:<doi>` | **该 filter 已下线** | HTTP 400 "filter-not-available: references" | `NOT_AVAILABLE`（Crossref 无法再做被引追踪） |
| Scopus | `api.elsevier.com/content/search/scopus` | **匿名不可达** | HTTP 401 `AUTHENTICATION_ERROR / Invalid API Key` | `NOT_ACCESSIBLE`（无 key 即无入口，与"机构未订阅"是两条独立事实） |
| Scopus | `scopus.com/api/1.0/search/abstract` | **匿名不可达** | HTTP 403 + Cloudflare 挑战页 | `NOT_ACCESSIBLE` |
| WoS / CNKI | — | 本轮**未触碰** | 按硬约束不做登录、不做浏览器自动化 | 沿用 §12–§13 那轮的结论 |

**纪律复述**：429 / 503 / 401 都记成"未查/不可达"，**不记成"未召回"**；
`RecordsFound` 与实取条数不等时不下笔（本轮被引遍历逐种子比对 `count` 与实际累计数，一致才继续）。

---

## 3. 检索式台账（库 | 日期 | 实际执行式 | 命中 | 可复现性评级）

评级定义：
**A** = 请求可原样重放、服务端自报计数、raw 已落盘（仍受索引快照影响）；
**B** = 请求可重放但计数受容量/限流支配，需多次重放才稳；
**C** = 仪器未过自身校准，其数字只作旁证；
**D** = 不可达/无权限，未获得任何计数。

### 3.1 OpenAlex — 关键词矩阵（18 条式；search 路由 18 次 + title_and_abstract 路由 10 次 = 28 次执行）

日期均为 2026-09-29。`search` 路由匹配标题+摘要+（OA 存源的）正文；
`title_and_abstract.search` 路由才是与 WoS `TS=` 可比的口径。

| # | 实际执行式（原文，直接可粘进 URL） | `search` 计数 | `title_and_abstract` 计数 | 评级 |
|---|---|---|---|---|
| S1 | `"VV10" AND "fragment decomposition"` | **3** | 429 | A / B |
| S2 | `"VV10" AND "energy decomposition"` | **139** | **1**（= Kruse 2018） | A |
| S3 | `"rVV10" AND "energy decomposition"` | **26** | 429 | A / B |
| S4 | `"nonlocal correlation" AND "fragment decomposition"` | **3** | 429（重试 1 次仍 429） | B → `RATE_LIMITED` |
| S5 | `"nonlocal correlation" AND "energy decomposition"` | **174** | **0** | A |
| S6 | `"nonlocal correlation" AND "pairwise decomposition"` | **3** | 429 | A / B |
| S7 | `"vdW-DF" AND "energy decomposition"` | 429 | **0** | B / A |
| S8 | `"nonlocal correlation" AND "atomic contributions"` | 429 | **0** | B / A |
| S9 | `"VV10" AND "per-fragment"` | 429 | 429 | `RATE_LIMITED`（未获得计数） |
| S10 | `"nonlocal correlation" AND "resolved into fragments"` | **0** | 503 | A / `RATE_LIMITED` |
| S11 | `"nonlocal correlation" AND "double sum"` | **21** | — | A |
| S12 | `"VV10" AND "grid" AND "decomposition"` | **228** | — | A |
| S13 | `"nonlocal functional" AND "domain decomposition"` | **24** | 503 | A / `RATE_LIMITED` |
| S14 | `"van der Waals density functional" AND "real-space integration"` | **16** | 503 | A / `RATE_LIMITED` |
| S15 | `"nonlocal correlation" AND "Becke partition"` | **8** | 503 | A / `RATE_LIMITED` |
| S16 | `"VV10" AND "many-body expansion"` | 429 | — | `RATE_LIMITED` |
| S17 | `"nonlocal correlation" AND "subsystem" AND "energy decomposition"` | 429 | — | `RATE_LIMITED` |
| S18 | `"VV10" OR "rVV10" AND "attributed to fragments"` | 429 | — | `RATE_LIMITED`（另注：该式 AND/OR 优先级未加括号，本身写法有歧义，重放时应加括号） |

已读到清单的窄集合（计数小、逐条读完）：S1=3、S4=3（首轮成功那次）、S6=3、S10=0、S11=21、S15=8。
**未逐条读完**（诚实登记）：S2=139、S3=26、S5=174、S12=228、S13=24、S14=16 中，只读了各式返回的**前 25 条题名**；
其余因 search 路由随后转 503 未能翻页。这三条大计数（139/174/228）**来自含正文的宽口径**，
命中含义只是"两个词串在文中某处共现"，不能读成"139 篇做了 VV10 的 EDA"。

### 3.2 arXiv — 17 条式 + 12 条正控（评级 **C**，全部只登记不采信）

| # | 式（`search_query=` 原文） | `opensearch:totalResults` |
|---|---|---|
| X1 | `abs:"VV10" AND abs:"energy decomposition"` | 0 |
| X2 | `abs:"VV10" AND abs:"fragment decomposition"` | 0 |
| X3 | `abs:"VV10" AND abs:"fragment"` | 0 |
| X4 | `abs:"rVV10" AND abs:"decomposition"` | 1 |
| X5 | `abs:"nonlocal correlation" AND abs:"energy decomposition"` | 0 |
| X6 | `abs:"nonlocal correlation" AND abs:"pairwise decomposition"` | 0 |
| X7 | `abs:"nonlocal correlation" AND abs:"atomic contributions"` | 0 |
| X8 | `abs:"vdW-DF" AND abs:"energy decomposition"` | 0 |
| X9 | `abs:"nonlocal correlation" AND abs:"resolved into fragments"` | 0 |
| X10 | `abs:"nonlocal correlation" AND abs:"double sum"` | 0 |
| X11 | `abs:"VV10" AND abs:"grid" AND abs:"decomposition"` | 0 |
| X12 | `abs:"nonlocal functional" AND abs:"domain decomposition"` | 0 |
| X13 | `abs:"vdW-DF" AND abs:"real-space" AND abs:"parallel"` | 1 |
| X14 | `abs:"nonlocal correlation" AND (abs:"Becke partition" OR abs:"Hirshfeld partition")` | 0 |
| X15 | `abs:"nonlocal" AND abs:"per-fragment"` | 1 |
| X16 | `abs:"VV10" AND abs:"pair attribution"` | 0 |
| X17 | `Hesselmann AND abs:"double Hirshfeld partitioning"` | 0 |

**为什么这 17 个 0 全部作废**（校准证据，落盘 `arxiv_calibration_*.json` / `arxiv_recall_test_*.json`）：
`abs:"VV10"` 总命中只有 **5**；`abs:"nonlocal correlation"`＝531；`abs:"van der Waals density functional"`＝87。
而我另外用 `id_list` 逐条确认 arXiv:2208.02841 的摘要**确实**写着 "VV10"，它**不在** `abs:"VV10"` 的 5 条里。
⇒ arXiv 的元数据检索对该词不可靠，它的 0 命中只能登记为"查过、未召回"（与 §9/§11 的 Crossref、OpenAlex 同病）。
`abs:"VV10"` 那 5 条（+`all:VV10` 多出的 1 条）已逐条读摘要：见 §5 表。

### 3.3 Crossref — 4 条主题式（评级 **C**，沿用 §9 判词）

| # | 式（`query.bibliographic=` 原文） | `total-results` | 判读 |
|---|---|---|---|
| CR1 | `VV10 nonlocal correlation fragment decomposition energy attribution` | 3,324,774 | 首位 Calbo 综述（真相关），次位 ωB97M-V，第三位是 `.s001` 支持信息文件 |
| CR2 | `nonlocal van der Waals correlation energy partitioned between fragments` | 10,538,231 | 首三位全是 `.s001/.s002` 支持信息记录 |
| CR3 | `VV10 double sum grid pair resolved contribution` | 1,124,334 | 首位是 carbonate/Cu 表面 SI |
| CR4 | `domain decomposition nonlocal density functional grid integration` | 2,657,197 | 首位 Nonlocal Subsystem DFT 的 SI |

⇒ 计数是"库规模"不是"主题命中"，纯相关度引擎，不承载否定主张。
被引追踪路线（`filter=references:`）在本轮已不可用（400 filter-not-available）。
Crossref 唯一可信用途＝**已知条目核验**：本轮所有新建议引用都经 DOI 精确回查（§7）。

### 3.4 Semantic Scholar — 关键词 1 条（评级 **D**）

| 式 | 结果 |
|---|---|
| `query=VV10 fragment decomposition&fields=title,year,externalIds,abstract&limit=10` | HTTP 429，未重试成 |
| `query=nonlocal+correlation+energy+decomposition` 等（会话初探针） | HTTP 429 |

⇒ S2 的**关键词维度本轮＝未查**；它的被引图维度可用（§4）。

---

## 4. 引用链追踪（本轮**主仪器**——它走的是非 search 路由，不受 503/429 支配）

这一步按任务要求优先于关键词，实际也确实比关键词更捞得到东西（Hyldgaard 那条是 §13 靠宽主题式捞到的，
本轮 Heßelmann 那条靠的是被引集合 + 两维筛）。

**种子（10 个 OpenAlex ID，其中 9 个有被引记录）**

| 种子 | OpenAlex ID | 被引数 | 实取记录 | 一致性 |
|---|---|---|---|---|
| Hyldgaard, Berland & Schröder, PRB 90, 075148 (2014) | W2001508813 | 76 | 76 | ✔ |
| Lazić et al., JuNoLo, CPC 181, 371 (2010) | W1994672550 | 47 | 47 | ✔ |
| Vydrov & Van Voorhis, PRL 103, 063004 (2009) | W2104873860 | 391 | 391 | ✔ |
| Vydrov & Van Voorhis, JCP 133, 244103 (2010) | W1970623278 | 1363 | 1364 | ✔（+1 为服务端计数漂移） |
| Dasgupta et al., JCTC 2023 (3c00903) | W4390264022 | 16 | 16 | ✔ |
| Calbo et al., VV10 综述 ARCC 11 (2015) | W2189819143 | 21 | 21 | ✔ |
| Sinha & Pavanello, FDE-vdW, JCP 143 (2015) | W1639678654 | 16 | 16 | ✔ |
| Dion et al., PRL 92, 246401 (2004) | W2003193361 | 5,683 | 5,683 | ✔ |
| Heßelmann, JCP 148 (2018) NLDFT 几何优化 | （见 §5） | 3 | 3 | ✔ |
| （误填的 Dion ID W1964577852） | — | 0 | 0 | 记录在案：我一开始硬编码了一个错的 Dion ID，得 0 条；后经 `doi:` 回查改用 W2003193361 才拿到 5,683。**这个 0 是我的输入错误，不是索引的 0。** |

合计取回 7,654 条被引记录 → 去重 **6,656 条**。

**筛子**

1. 题名两维（非局域词 × 归属词）→ **0 条**。
2. 只含归属词的题名 → 104 条 → 全部补取摘要 → 摘要两维命中 **11 条**（逐条读，见 §5）。
3. 对 VV10 直接相关 7 个种子的 **1,669 条**被引（其中 1,416 条有摘要）做题名+摘要两维 → **38 条**（逐条读，见 §5）。
4. 同 1,416 条做**句级同现**（归属措辞与非局域项同句）→ **0 条**。
   该正则的正控已验：三条构造句全部触发、一条"只算 vdW-DF2 结合能"的负控不触发。

**第二索引（Semantic Scholar 被引图，独立于 OpenAlex）**

7 个种子 → 314 条去重被引 → 两维命中 14 条，**与 OpenAlex 的候选集合成员一致**（同批 FDE-vdW /
Nonlocal Subsystem DFT / Jiao-Schröder-Hyldgaard / Tran-Hutter / Heßelmann / BEEF-vdW 那批），
没有出现 OpenAlex 池之外的新先例。
⚠ **截断声明**：S2 每页 100 条，两个 VV10 种子各**恰好返回 100 条**且响应未给 `total`，
所以这两条遍历是**截断样本**，不是全量；其余 5 个种子取全（67/39/10/2/11）。

---

## 5. 命中判定表

档位定义：**①已做同一件事** / **②部分重叠（标明重叠在哪个维度）** / **③不相关（词表噪声）**。

| 库（发现路径） | 题名 / 年 / DOI | 判定 | 依据（摘要原文或已确认事实） |
|---|---|---|---|
| OA 被引池 + S2 被引池（两索引一致） | Heßelmann, "Assessment of a Nonlocal Correction Scheme to Semilocal DFT Methods", JCTC **9**(1), 273–283（年 2012/2013 待 Crossref 定）, `10.1021/ct300735g` | **②部分重叠**（做了"非局域关联能的原子对摊开"，但摊的是自建泛函、不是既有 VV10；无片段级；无划分方案跨度） | 摘要："…based on a partitioning of the correlation-energy density **into atom-atom contributions**" |
| 同上 | Heßelmann, "Geometry optimisations with a nonlocal DFT method based on a double Hirshfeld partitioning", JCP **149**, 044103 (2018), `10.1063/1.5032175` | **②部分重叠**（上条方法的解析梯度/几何优化续作；它引作 "JCTC 9, 273 (2013)" 的那篇就是上条**同一篇**，故 NLDFT 只有一条原始文献） | 摘要：解析梯度、"inherent Hirshfeld weights … analytic expressions of the atomic densities"、76 个三肽优化 |
| OA 句级/两维 + S2 | Jiao, Schröder & Hyldgaard, "Signatures of van der Waals binding: a coupling-constant scaling analysis", PRB 97, 085115 (2018), `10.1103/physrevb.97.085115` | **②部分重叠**（对同一个 `E_c^nl` 做"更完整空间分辨"的分析，但分辨到 xc hole / 耦合场，不落到命名片段对；且补的是 `T_c^nl`） | 摘要："we thus provide a more complete **spatially resolved analysis** of the electrodynamical-coupling nature of nonlocal-correlation binding" |
| 同上 | Chakraborty, Berland & Thonhauser, "Next-Generation Nonlocal van der Waals Density Functional" (vdW-DF3), JCTC 2020, `10.1021/acs.jctc.0c00471` | **②部分重叠**（动非局域项，方向是**造新的**，不是拆既有的） | 摘要："we present the next-generation nonlocal correlation functional called vdW-DF3" |
| 同上 | Sabatini, Gorni & de Gironcoli, "Nonlocal van der Waals density functional made simple and efficient", PRB 87, 041108 (2013), `10.1103/physrevb.87.041108` | **②部分重叠**（做了非局域项但**不分解**；重叠在"显式/高效求值 + 解析导数"这条轴，直接压我们的实现卖点） | 摘要："allows nonlocal correlation energy and its derivatives to be efficiently evaluated in a plane wave framework" |
| DOI 回查（上条引文溯源） | Román-Pérez & Soler, "Efficient Implementation of a vdW Density Functional…", PRL 103, 096102 (2009), `10.1103/PhysRevLett.103.096102` | **②部分重叠**（同上：可分离高效求值，无归属） | 题名与 DOI 已 OpenAlex 回查；被引 1,594 |
| arXiv（`all:VV10` 唯一多出的一条） | "Nonlocal van der Waals density functional made faster", arXiv:2511.04169 (2025) | **②部分重叠**（做了非局域项但不分解；**预印本＝WoS CC 不覆盖**，成本轴上最新竞品） | 摘要：六维积分被积函数近似为少量乘积、fast multipole / 高斯基解析求值 |
| OA `search` S1/S4/S6 三小集 + 被引池 | Tran & Hutter, "Nonlocal van der Waals functionals: the case of rare-gas dimers and solids", JCP **138**, 204103 (2013), `10.1063/1.4807332`（卷页已 `biblio` 回查） | **②部分重叠（判定停在摘要级）**：摘要确有"An analysis of the results in terms of **energy decomposition** is also provided"，但没写明分解对象；若指非局域项本身则威胁升级 | 需全文确认（待办 §8）；判定标 `UNVERIFIED-at-fulltext` |
| OA `search` S1（3 条之一） | Podeszwa? 否 — `10.1039/c6cp03784d` "Probing non-covalent interactions with a second generation EDA using ALMOs" (PCCP 2016) | **②部分重叠**（做分解，但分解的是总相互作用能，非局域项不在其内） | 已确认属 ALMO-EDA 家族；与 §6 Dasgupta 同一族 |
| OA `search` S1（3 条之一） | `10.1021/acs.jctc.3c00143` "Merging the EDA with the Interacting Quantum Atoms Approach" (JCTC 2023) | **②部分重叠**（QTAIM 空间归属 + 分解，但对象不是非局域双重和） | 题名+摘要级判定 |
| OA S4/S6 命中 | `10.1063/1.3545971`（Zheng–Sanchez–Yang, vdW-DF1/vdW-DF2 对比, JCP 2011）；`10.1038/s41467-024-50030-8`；`10.1021/acs.jpcb.4c01466` | **③不相关**（后两条是 pH/电场涨落与 QM/MM−ΔMLP 软件，命中来自宽口径正文共现） | 逐条读摘要 |
| OA S11（21 条全读题名） | `abs/… "nonlocal correlation" AND "double sum"` 21 条 | **③不相关 20 条**（GHZ 非定域性、μg−2、Bethe ansatz、量子信息、张量网络等，"nonlocal correlation" 是量子信息语汇）＋1 条 Vydrov–VanVoorhis Reply | 21 条题名逐条列出并落盘 |
| OA S15（8 条） | `"nonlocal correlation" AND "Becke partition"` | **②部分重叠 0 / ③不相关 8**：无一条把 Becke 划分用在 VV10 双重和上 | 与 §13.4 D 式（WoS 33 条）互相印证 |
| OA 被引池（归属词在题名） | Bistoni, Altun, Wang & Neese, "Local Energy Decomposition Analysis of London Dispersion Effects", *Acc. Chem. Res.* 2024, `10.1021/acs.accounts.4c00085` | **②部分重叠**（ dispersion 的局域/实空间分解，**摘要不含任何非局域泛函词** ⇒ 不是 VV10 项） | 摘要级：NL 词命中＝NONE |
| 同上 | Giovannini, "Kohn–Sham fragment energy decomposition analysis", JCP 162 (2024), `10.1063/5.0216596` | **②部分重叠**（KS 片段定域 MO + EDA，摘要未出现非局域项） | 同上 |
| 同上 | Mao et al., "From Intermolecular Interaction Energies… ALMO-EDA-II", *Annu. Rev. Phys. Chem.* 72 (2021), `10.1146/annurev-physchem-090419-115149` | **②部分重叠**（EDA 家族综述；非局域项不作内部分解） | 已核 |
| OA + S2 两索引 | FDE-vdW：Sinha & Pavanello `10.1063/1.4928531`；Mi & Pavanello "Nonlocal Subsystem Density Functional Theory" `10.1021/acs.jpclett.9b03281`；Shao, Mi & Pavanello `10.1021/acs.jctc.1c00283`；eQE 2.0：Mi, Shao, Genova & Ceresoli `10.1016/j.cpc.2021.108122` | **②部分重叠**（都是"子系统 × nonlocal"，但 nonlocal 指的是 **NAKE 非加和动能泛函**，不是 `E_c^nl`；四个 DOI 已逐条回查，作者/年份一致） | 摘要已分别确认："the central ingredient setting subsystem DFT apart from Kohn-Sham DFT is the nonadditive kinetic energy functional (NAKE)" |
| OA + S2 | `10.1063/5.0248728` / `10.26434/chemrxiv-2024-2hg7l`（BEEF-vdW 换原子对/多体色散） | **②部分重叠**（动 vdW-DF2 非局域项，但做的是**替换**，不是归属） | 摘要："explores whether atom-pairwise and many-body dispersion treatments represent viable alternatives to using the vdW-DF2 functional" |
| OA + S2 | `10.1063/5.0179149`（ML finite-range nonlocal functional, JCP 2024） | **②部分重叠**（把总密度按原子心局域密度 partition + 多体展开——"原子分辨的非局域性"，但仍是**造新泛函**） | 摘要原文已引 |
| OA + S2 | `10.1103/physrevb.88.045431`（Harris-type vdW-DF scheme, PRB 88, 045431 (2013)） | **②部分重叠**（用片段密度叠加求**总能量**，不给片间归属） | 摘要："use a superposition of fragment densities … to obtain the total energy non-self-consistently" |
| OA `search` S2 首位 | Kruse, Banáš & Sponer, JCTC 15, 95 (2018), `10.1021/acs.jctc.8b00643` | **②部分重叠**（与 WoS §12 #7 同一记录；VV10 只是 29 个受测泛函之一，分解的是 SAPT2+3δ(MP2) 的总相互作用能） | 两索引交叉确认 |
| OA S4/S6/S11/S13/S14/S15 | `10.1002/wcms.1700`（subsystem-DFT update 综述, 2024）、`10.1088/2516-1075/ac25d7`（reduced-gradient analysis）、`10.1039/d5cp01581b`、`10.1021/ct300258z`、`10.1021/ct2005616`、`10.1063/1.4918761` 等 | **③不相关为主**（"fragment" 指模型团簇/片段化表面；"localization" 指轨道；"pairwise" 指 DFT-D） | 已逐条读摘要 |
| arXiv `all:VV10` 6 条 | `arXiv:2208.14639`（VV10 解析二阶导, JCP 2023）、`arXiv:1209.3038`（面向固体的 VV10 变体）、`arXiv:2101.00600`、`arXiv:2202.13208`、`arXiv:2501.12925`、`arXiv:2511.04169` | **②×2 / ③×4**（前两条与 2511.04169 属实现/泛函开发轴；其余为基准与行星物理，噪声） | 六篇摘要已全读并落盘 |
| WoS 那轮已定 | Hyldgaard–Berland–Schröder PRB 90, 075148 (2014) | **②部分重叠**（同一 `E_c^nl` 的物理诠释，不做片段归属）——**本轮再确认：其 76 条被引里也没有做归属的** | 见 §4 筛子 1–2 |
| **①已做同一件事** | — | **0 条** | — |

**关于任务里点名的两篇种子**（"Lee–Ko–Klippenhein–Marques–Vidali 2010"、"Vidali–Klippenhein–Lee 2012"）：
`UNVERIFIED`。Crossref `query.author=Klippenhein` 返回 0 条；OpenAlex `/authors?search=Klippenhein` 返回 0 位作者；
6 位姓 Vidali 的作者（共 1,034 篇作品）里没有一篇题名含 van der Waals / nonlocal / density functional。
另 Crossref `query.bibliographic="Higher-accuracy van der Waals density functional"` 解析到的是
**Lee, Murray, Kong, Lundqvist & Langreth, PRB 82, 081101 (2010)**（LM10，不是这两条名字）。
⇒ 我不否认它们存在，只登记"在可匿名访问的索引里定位不到"。替代覆盖：本轮把 JuNoLo（同组实现线）
+ Dion + 两篇 VV10 + Calbo 综述的**全部被引**都过了两维筛，任何非局域项实现类工作若要拆 VV10 都在这个池子里。

---

## 6. 与 WoS 那一轮的关系：一致、且补上了三个洞

| 维度 | WoS（§12–§13，正式索引） | 本轮（开放索引，补检） |
|---|---|---|
| `VV10 × energy decomposition`（题/摘级） | 1 条（Kruse 2018） | OpenAlex 同口径 1 条，**同一 DOI** ✔ |
| 最贴主张的归属式 | 0 条（§13.4 A 式） | OpenAlex `"…resolved into fragments"` 0 条、`"nonlocal correlation" AND "energy decomposition"` 题/摘级 0 条 ✔ |
| Heßelmann NLDFT | **未出现**（其词表是 nonlocal DFT + double Hirshfeld partitioning，不含 "nonlocal correlation" 短语） | **捞到** ⇒ 需要划界 |
| VV10 高效/可分离求值线（RS09 / SGD13 / arXiv:2511.04169） | 未出现（实现类工作不含归属词） | **捞到** ⇒ 需要引用；预印本尤其落在 WoS 覆盖之外 |
| 两维筛的可检验性 | 靠人逐条读 33/33/7/8 条 | 靠正则 + 正控，覆盖 6,656 条题名 + 1,416 条摘要 |

---

## 7. 申请：给正文的具体替换句（**我没有动任何既有文件**）

### 7.1 `paper/main.md` 局限段（现 624–637 行）／`paper/main.tex` 对应句

**原文（待替换的第一句）**
> Separately, the literature search covers one index - Web of Science Core Collection - because
> Scopus was measured as unsubscribed at our institution and Embase and SciFinder were not searched at all.

**替换为（可直接粘贴，两处事实都有本轮实测依据）**
> Separately, the formal search covers one index — Web of Science Core Collection — because Scopus
> returned `AUTHENTICATION_ERROR` to its public API and no institutional subscription was measured,
> and because Embase and SciFinder were not searched at all. We ran a second pass over open indexes
> (OpenAlex, Semantic Scholar, arXiv, Crossref; 2026-09-29) as a supplementary check rather than as a
> second formal search, since results retrieved over the open network cannot be re-played against a
> stable snapshot and are therefore not counted in the PRISMA flow. That pass confirmed the
> Web of Science result rather than overturning it: at title-and-abstract level, OpenAlex returns the
> same single record for `"VV10" AND "energy decomposition"` as Web of Science does, and `"nonlocal
> correlation" AND "energy decomposition"` returns zero in both. What it added is two neighbours we
> had not bounded, described below.

**并在该段末尾（现 637 行 "…when asked topically (section 4)." 之后）追加一句**
> The same pass also failed to find any prior attribution of the VV10 double sum to fragment pairs —
> across 40 query strings and, more decisively, across 6,656 works citing Hyldgaard et al., JuNoLo,
> both VV10 papers, the Calbo review, FDE-vdW and Dion et al., where a screen requiring both a
> nonlocal-term word and an attribution word matched zero titles and zero sentences; but it did
> surface Heßelmann's nonlocal correction scheme, which we now bound explicitly, and three
> implementation papers we now cite.

（**禁止**写成"已跨库全面核查/多索引确认新颖性"。三处限制必须留着：S2 关键词维度未查、arXiv 未过校准、
OpenAlex search 路由 45 次尝试中 24 次被 429/503 打断。）

### 7.2 `paper/main.md` §1 定位段（现 132–138 行，紧接 Dasgupta 那句之后）**新增两句**

> Heßelmann's nonlocal correction scheme is the closest neighbour on the attribution axis: it derives
> a nonlocal correlation-energy contribution "based on a partitioning of the correlation-energy
> density into atom-atom contributions" [doi 10.1021/ct300735g], with analytic gradients used for
> geometry optimisation afterwards [doi 10.1063/1.5032175]. We do not claim to be the first to
> resolve a nonlocal correlation energy spatially. What is different here is the object and the use:
> we take the VV10 term already present in a published functional and attribute it after the fact to
> named fragments and atom pairs, at fragment — not atom — resolution, and we measure how much the
> same inter-fragment quantity moves across partitioning schemes rather than proposing one scheme.

### 7.3 `paper/main.md` §1 那句"显式求和"的限定（§10 已加过一次，现在需要第二次、更强的那次）

> Evaluating the nonlocal term explicitly, or efficiently, is not our contribution: the separable
> approximation of the six-dimensional integral [Román-Pérez & Soler, PRL 103, 096102 (2009)] and its
> VV10 revision with analytic derivatives [Sabatini, Gorni & de Gironcoli, PRB 87, 041108 (2013)] are
> the standard route, and a 2025 preprint pushes the same direction further [arXiv:2511.04169].
> We keep the double sum explicit precisely to retain the (i, j) index those schemes discard, at a
> cost we quantify in section 4.

### 7.4 `paper/references.bib` 建议新增（前 4 条 DOI 已 OpenAlex/Crossref 精确回查，题名/年份/作者/期刊一致）

```bibtex
@article{hesselmann2012nldft,
  author  = {Andreas Heßelmann},
  title   = {Assessment of a Nonlocal Correction Scheme to Semilocal Density Functional Theory Methods},
  journal = {Journal of Chemical Theory and Computation},
  volume  = {9},
  pages   = {273-283},
  year    = {2013},          % OpenAlex biblio: vol 9, issue 1, pp 273-283; publication_year field says 2012,
                             % and doi 10.1063/1.5032175 cites it as "(2013)". Re-check Crossref published-print before locking.
  doi     = {10.1021/ct300735g},
}
@article{hesselmann2018nldftgrad,
  author  = {Andreas Heßelmann},
  title   = {Geometry optimisations with a nonlocal density-functional theory method based on a double Hirshfeld partitioning},
  journal = {The Journal of Chemical Physics},
  volume  = {149},
  pages   = {044103},
  year    = {2018},
  doi     = {10.1063/1.5032175},
}
@article{romanperez2009efficientvdwd,
  author  = {Guillermo Rom{\'a}n-P{\'e}rez and Jos{\'e} M. Soler},
  title   = {Efficient Implementation of a van der Waals Density Functional: Application to Double-Wall Carbon Nanotubes},
  journal = {Physical Review Letters},
  volume  = {103},
  pages   = {096102},
  year    = {2009},
  doi     = {10.1103/PhysRevLett.103.096102},
}
@article{sabatini2013simpleefficient,
  author  = {Riccardo Sabatini and Tommaso Gorni and Stefano de Gironcoli},
  title   = {Nonlocal van der Waals density functional made simple and efficient},
  journal = {Physical Review B},
  volume  = {87},
  pages   = {041108},
  year    = {2013},
  doi     = {10.1103/physrevb.87.041108},
}
```

**已闭环的一条**：2018 那篇正文逐字引用的 "[J. Chem. Theory Comput. 9, 273 (2013)]" 就是
`10.1021/ct300735g`——本轮收尾用 OpenAlex `biblio` 回查确认其卷 9、期 1、页 273–283。
（此前 Crossref 的 author/title 组合与 OpenAlex `doi:` 试投都没命中它，因为它的题名里不含 "Hirshfeld"。）
⇒ NLDFT 只有**一条**原始文献 + 一条梯度续作，正文划界句按此写，不要写成两条原始工作。
仍需定死的是**年份**：OpenAlex 记 2012、引用作 2013，进 bib 前用 Crossref `published-print` 复核后二选一。
arXiv:2511.04169 若引用，须按项目规矩标"预印本、未见期刊版"。

---

## 8. 残余缺口（不许藏的那部分）

1. **本轮没有任何一条判定是全文级的**。除 §6/§10 已有的两篇全文比对，本轮所有判定停在题名/摘要级，
   最关键的 `10.1063/1.4807332`（Tran & Hutter 2013）那句 "energy decomposition" 到底分解什么，
   **必须读全文才能定死**；读完前，正文不要把话说满。
2. OpenAlex 宽口径大计数只读了前 25 条题名：S2(139)、S5(174)、S12(228)、S3(26)、S13(24)、S14(16) 未翻完，
   因为该路由在会话后段持续 503。
3. S2 的两个 VV10 种子各恰好 100 条 ⇒ **截断样本**，不是全量；S2 关键词检索＝未查（429，未申请 key）。
4. 6,656 条里 Dion-2004 独占的约 4,987 条只做了**题名级**筛查（摘要级只覆盖了 VV10 直接相关种子的 1,669 条）。
5. arXiv 未过已知条目校准 ⇒ 它的 14 个 0 命中只是"查过"。
6. 开放索引快照日期 2026-09-29（本轮），此后入库/改摘要不覆盖。
7. CNKI/中文库本轮未查（按硬约束不登录）。

---

## 9. 复现物清单（`paper/notes/raw/`，文件名含 UTC 戳）

- `oa_cites_W*.json`（10 份）：OpenAlex `filter=cites:<W…>` 全量枚举原始返回。
- `oa_citer_abstracts_vv10seeds_*.json`（2.3 MB）：VV10 相关 7 种子 1,669 条被引的题名+倒排摘要。
- `oa_abstracts_candidates_*.json`：归属词在题名的 104 条摘要。
- `oa_targeted_records_*.json`：§5/§7 每条建议引用的 DOI 逐条回查记录。
- `openalex_search_matrix_*.json`：28 次执行的式子原文、HTTP 状态、`meta.count`、首页清单。
- `openalex_enum_smallsets_*.json`、`openalex_slowpass_*.json`：小集逐条枚举 + 慢速重试（含 429/503 原始报错串）。
- `openalex_search_retry_*.json`：503→恢复期的 5 条探针计数。
- `s2_cites_*.json`（7 份）、`s2_refs_hesselmann2018_*.json`：Semantic Scholar 被引遍历原始分页。
- `arxiv_queries_*.json`、`arxiv_calibration_*.json`、`arxiv_recall_test_*.json`、`arxiv_vv10_items_*.json`：
  17 条式 + 12 条正控 + 校准失败证据 + 6 篇 VV10 相关预印本全文摘要。
- `crossref_topical_*.json`：4 条主题式的 total-results 与首位记录（用于证明其不可承载否定主张）。

一句话给合稿者：**主张不用改方向，要改措辞——把"非局域项的空间归属"降格为"对既有 VV10 项的事后片段对归属"，
并补引 Heßelmann（10.1021/ct300735g、10.1063/1.5032175）与可分离高效求值线（PRL 103, 096102；PRB 87, 041108）。**
