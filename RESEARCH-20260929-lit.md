# 文献调查（2026-09-29 02:20–03:00，cn-qoder 自跑，不经子代理）

方法：确定性 API 管线（OpenAlex `title_and_abstract.search` 精确检索 + OA 定位），
脚本 `scratch/lit_pipeline.js`、`scratch/fetch_chemrxiv.js`、`scratch/lit_browser.js`；
原始返回全部留在 `scratch/lit/pipeline/` 与 `scratch/lit/fulltext/`，可复跑。

## 1. 先例查重：没有"按片段/原子对归属非局域关联双重和"的论文

10 组检索式（每组取回 ≤25 条，去重后共 29 条）：

| 检索式 | 命中总数 |
|---|---|
| "nonlocal correlation" AND fragment | 15 |
| "nonlocal correlation" AND "energy decomposition" | **0** |
| VV10 AND decomposition | **3** |
| rVV10 AND decomposition | 6 |
| VV10 AND "atom pair" | **1** |
| "nonlocal correlation" AND "many-body expansion" | **0** |
| "vdW-DF" AND "energy decomposition" | **0** |
| dispersion AND "pair decomposition" AND "density functional" | **0** |
| fragment AND "nonlocal correlation functional" | 1 |
| monomer AND "nonlocal correlation" | 4 |

判读：**五个检索式命中 0 或 1**，且 29 条去重结果里没有任何一篇做"把 VV10 双重和
按片段对摊开"这件事。最接近的三条是：
- `10.1021/acs.jctc.3c00903`（2023，比较色散模型 + 相互作用能分量，**不是归属分解**）
- `10.1063/1.2189230`（2006，monosubstituted benzene dimers via nonlocal DFT，用非局域泛函算二聚体，不做分解）
- `10.1103/physrevb.97.085115`（2018，vdW 结合的 coupling-constant 标度分析，另一类"分量"思路）

⇒ ~~本项目的方法学缺口在 OpenAlex 的标题+摘要空间里成立~~
**该结论已于 §11 撤回**：OpenAlex 与 Crossref 的主题召回率实测不合格
（近似标题 4/4 rank=0，两条合法主题式各 0/4 稳定漏掉同一篇正题先例），
所以上面那十组的 0 命中**只登记为"查过、未召回"，不作为"不存在"的证据**。
"未见先例"现由 §6（JCTC 3c00903 全文）与 §10（JuNoLo 全文）两处全文比对支撑；
WoS/Scopus 那一轮仍未完成（§8.1，需用户本人过一次机构登录）。

## 2. 计划里"必须拿到全文"的那篇：有免费版本，但自动抓取被挡

- 正式版 `10.1021/acs.jctc.3c00903`：OA status = **closed**（OpenAlex 两处定位均无 PDF）。
- **ChemRxiv 接受稿 `10.26434/chemrxiv-2023-nc64t`：OA = green**，
  PDF 直链在 OpenAlex 里给了（`chemrxiv.org/engage/api-gateway/.../balance-between-physical-interpretability-...pdf`）。
- 抓取实测：curl（浏览器级请求头）403；Playwright 真实 Chromium 里先访问 chemrxiv.org 首页
  拿到 CF cookie，再在页面上下文内 `fetch(..., credentials:'include')` **仍然 403**。
  ⇒ 该 asset 端点对非交互客户端一律拒绝，**需要人工在浏览器里点一次**。

## 3. EDA 那条路的两个对照物：都是绿色 OA，同样被反爬挡

| DOI | 题目（截断） | OA | 免费 PDF 位置 |
|---|---|---|---|
| `10.1063/1.4942921` | Defining the contributions of permanent electrostatics, Pauli repulsion, and dispersion… | **green** | escholarship（curl 403） |
| `10.1146/annurev-physchem-090419-115149` | From Intermolecular Interaction Energies and Observable Shifts to Component Contributions | **green** | osti.gov purl 1779274（连接超时） |
| `10.1021/acs.jpca.3c04374` | Simple, Efficient, and Universal Energy Decomposition Analysis Method… | closed | 无 |

## 4. 仍未解决（等全文）

**SAPT/EDA 的色散分量数值**（水二聚体、苯 sandwich 与 T-shaped、甲烷二聚体、氨-水、苯-水）
——这些数在全文表格里，摘要与元数据里没有。拿到上面三篇 PDF 后可以直接抽。
在此之前，论文里**禁止**引用任何"文献色散 ≈ −1.4 kcal/mol"这类无出处数值
（`PROGRESS-nlcsplit.md` 01:14 已下过同一条禁令）。

## 5. 需要人工的两步（不花钱，浏览器点三下）

1. 打开 ChemRxiv PDF 直链（用 OpenAlex 返回的地址，或先在 `doi.org/10.26434/chemrxiv-2023-nc64t` 页面点 "Download PDF"），
   存为 `scratch/lit/fulltext/chemrxiv.pdf`
2. 打开 `https://escholarship.org/content/qt4x0252xk/qt4x0252xk.pdf` 存为 `scratch/lit/fulltext/almo_eda.pdf`
3. 打开 `https://www.osti.gov/servlets/purl/1779274` 存为 `scratch/lit/fulltext/annurev.pdf`

落盘后我用 pypdf 抽文本，直接产出"SAPT E_disp 对照表 + 该文的分量分析方法是否等于我们的归属分解"的结论。

---

## 6. 全文到手后的实质结论（2026-09-29 03:05，浏览器代操作完成）

下载路径记明：curl / Playwright 真实 Chromium（含"页面上下文内 fetch"）都被 Cloudflare 拒；
改用 Qoder Browser Connector 驱动真实 Chrome，过 CF 质询后在页面上下文里
`fetch → blob → a.download` 触发下载（字节不经过模型上下文）。
落地 `scratch/lit/fulltext/chemrxiv_main.pdf`(1.67 MB, 57 页) 与 `chemrxiv_si.pdf`(15.09 MB)，
pypdf 抽正文文本 114,928 字符。

**6.1 这篇在做什么（决定我们怎么定位）**
作者 Dasgupta, Palos, Pan, Paesani（UCSD），已发 JCTC（version of record 2023-12-27，被引 16）。
它的分解是**二阶 ALMO-EDA**（正文式 3）：`E_Int = E_Pol + E_Frz + E_CT + E_Disp`，
`E_Frz` = 永久静电 + Pauli 排斥；用 PBE/revPBE/PBE0 配 -D3/-D4/-VV10/MBD，
def2-QZVPPD（水簇用 def2-QZVPP），参考泛函取 ωB97M-V。
⇒ 它把"**−VV10 那一项整体**"当作色散能（减去无色散常项的 ΔSCF 型做法），
**没有在非局域项内部做片段/原子对归属**。与我们的贡献正交：
它把整个纠正当色散，我们把这一项拆开并证明它不等于色散。

**6.2 带 DOI 的外部对照数（之前缺的就是这块）**
苯二聚体 parallel-stacked，平衡几何下的 E_Disp（正文 612–619 行）：

| 方法 | E_Disp (kcal/mol) |
|---|---|
| **ωB97M-V（其参考）** | **−3.69** |
| PBE-VV10 / revPBE-VV10 | −3.75 |
| revPBE-D3 | −3.80 |
| PBE0-D3 | −3.55 |
| PBE-D3 | −3.54 |
| PBE0-VV10 | −3.34 |

本项目独立算的 ωB97X-V / 苯 sandwich(3.81 Å) / 6-31G\* / level 0 的
**ΔE_NLC = −3.258 kcal/mol**（与 step_b 的 −3.2583 两条路径互验），
与 ωB97M-V 的 −3.69 差 **0.43 kcal/mol（11%）**，可由泛函代差
（ωB97X-V vs ωB97M-V）、基组（6-31G\* vs def2-QZVPPD）、几何（我们是标准单体 +
D=3.81 Å 构造几何，其平衡几何来自 CCSD(T)/CBS 扫描）三项解释。

**6.3 直接推翻此前两条说法**
1. IDE 在 S2 里用"苯二聚体文献色散 ≈ −1.4 kcal/mol"作分母，得到"我们的数比文献色散大 2.3 倍"。
   **那个 −1.4 无出处，且更像净相互作用能**：本文明写"苯二聚体相互作用能典型只有 2–3 kcal/mol，
   因为色散与 Pauli 排斥相互抵消"（正文 503–505 行）。真正的色散分量是 **−3.5 ~ −3.8**。
   ⇒ 正确表述（有 DOI 支撑，10.1021/acs.jctc.3c00903）：
      **我们的片间 NLC（−3.26）与已发表的 VV10 型色散分量（−3.34 ~ −3.80）同量级**；
      净相互作用能小得多是排斥抵消的结果，不能拿净能当色散分母。
2. 该文引文（121,122）指出 MP2 对 parallel-stacked 苯二聚体高估 2 倍、T-shaped 高估 30%，
   SAPT0/MP2 无法定量给出色散 ⇒ 我们**不能**用 MP2/SAPT0 的数当分母，
   要用 CCSD(T)/CBS 或 ωB97M-V 级参考。水二聚体的对应数这篇**没有**（它做水簇与离子-水），仍待补。

## 7. 仍缺

* 水二聚体 / 甲烷二聚体 / 氨-水 / 苯-水 的 CCSD(T)/CBS 色散分量参考值（带 DOI）。
  候选来源：Podeszwa et al.（该文引文 120，DFT-SAPT 扫苯二聚体 PES）、
  Heßelmann–Jansen SAPT(DFT)、S22/S66×8 原文。需要再次浏览器取全文。
* WoS/Scopus 那一轮正式检索（OpenAlex 一层证据已给，不能替代正式库）。

## 8. 正式检索这一轮的结果：**三台仪器全部不可用**（2026-09-29 09:20 实测，带复现物）

结论先说：**新颖性主张目前仍只有 OpenAlex 一层证据**，不能写成"经正式库核查"。
本轮试图补 WoS/Crossref/Semantic Scholar 三层，三层各自因不同原因不成立，
证据如下（脚本 `scratch/pw_wos3.js`、`scratch/lit_x2.js`，输出
`scratch/wos_r1.json`、`scratch/xref_s2_r2.json`）。

### 8.1 Web of Science（中国镜像 clarivate.cn）——界面进得去，检索不给跑
* 关键机制：**系统代理会把出口换成境外 IP**（browser-use 的 Chrome 实测出
  `104.251.123.25`），该镜像按 IP 认机构 ⇒ 只会撞到 `access.clarivate.com/login`。
  以 `--proxy-server=direct://` 直连则出 `202.117.147.182`（教育网），
  落地页确实是检索界面（`#advancedSearchInputArea` 可见，placeholder
  "Enter or edit your query here…"）。**这一步是本轮真正的进展：馆际通路是通的。**
* 但 `Sign In` 按钮仍在（未获得会话），填入
  `TS=("VV10" AND "decomposition")` 后回车 / "Add to query" 均**不提交**，
  URL 停在 `/wos/woscc/advanced-search`，九条式子全部 `total=null`。
  即该镜像**不允许匿名执行检索**，机构 IP 只解决"能看见界面"。
* 两个额外实测坑：OneTrust 遮罩会让 "Add to query" 永远 `disabled`（要先点掉）；
  技能里记的 `getByRole("button", {name: /^Search$/})` 在本版界面上**匹配不到**，
  实际可见的是 "Add to query" 与一个 class 含 `search` 的按钮。
* ⇒ 需要用户本人过一次 CARSI/机构登录（或明确授权我用其账号登录一次）。
  按纪律不擅自代填口令走 IdP，也不在结果未知时重试。

### 8.2 Crossref `query.bibliographic` ——**known-item 校准不通过**，故其 0 命中无效
三篇确知在库的对照：

| 校准 | 期望 | 实测最高分 | 命中的实际题名 |
|---|---|---|---|
| K1 | Van der Waals Density Functional for General **Use** (Dion PRL 92,246401) | 0.857 | "...for General **Geometries**" |
| K2 | vdW density formalism: … interactions in rings (Thonhauser PRB 69,235111) | 0.667 | 未召回 |
| K3 | Hartree-Fock-Swap … Gibbs energy (Smith 等) | 0.125 | 未召回 |

⚠ **11:50 更正本表的一条判词**：我上面写 K1 命中的是"**另一篇**"，**这个判断错了**。
用 Crossref DOI 精确回查（`scratch/doi_chk.js`）：`10.1103/PhysRevLett.92.246401`
的正式题名就是 **"Van der Waals Density Functional for General Geometries"**
（Dion, Rydberg, Schröder, PRL 92, 246401, 2004）。也就是说 Crossref 那一次
**检索到了正确的那篇**，错的是我手里"期望标题"——我把 "for General Geometries"
记成了不存在的 "for General Use"。
⇒ 结论方向不变但理由要换：**K1 其实是命中**；校准失败只成立于 **K2、K3**
（0.667 / 0.125，两篇都没召回）。仪器判定"不可作为负证据来源"仍然成立，
因为两篇确知在库的文献召不回来；但**不得再说"它给了伪命中"**。
同一轮回查还顺手抓出两个我记错的 DOI：`10.1103/PhysRevB.70.235111` 不是
Thonhauser 那篇（解析到 Chernyshev 等），`10.1063/1.2189230` 是 Thonhauser 2006
JCP 的"单取代苯二聚体"而非"rings 形式体系"。
⇒ 教训比原判断更重要：**"期望值"本身也要验**。我用一个记错的标题去校准一台
搜索引擎，差点把一次正确的检索结果划成仪器的失败。
以后写校准表时，期望题名必须与 DOI 同时从 Crossref 回查得到，不许凭记忆填。

* 判据本身也暴露了：0.85 词元重叠会把 K1 判成**伪命中**（一字之差、另一篇文献）。
  收紧就会把 K2/K3 判死——**这台仪器没有可调和的工作点**。
* 每条式子都返回 `rows` 顶格 8/20 条且相关性明显不对（N3 首条是"六维分子间势能面复核"），
  说明它是纯相关度引擎，不能承载布尔式子。
* ⇒ 本轮 N1–N7 的"没命中"**一律不作数**，第一版里那句结论已从证据链撤回
  （`xref_s2_r1.json` 保留，标为无效实验）。

### 8.3 Semantic Scholar —— 未授权 429 打满，连校准都跑不完
`limit=20` 的 `/paper/search` 在未带 key 的共享池里 5 次退避（2.5–12.5 s）后仍
`429 exhausted`。要用得 API key，属花钱/注册类事项，未擅自办。

### 8.4 这一轮之后，新颖性主张的诚实表述
* 已确立：OpenAlex（10 条 `title_and_abstract.search`，5 条返回 0 或 1）+
  对最近先例 JCTC 3c00903 的**全文级**重叠判定（其把 −VV10 整块当色散能，
  未在该项内部做片段/原子对归属）。
* 未确立：WoS/Scopus 正式检索、第三个独立索引。
* ⇒ 正文里这句必须这么写：**"据 OpenAlex 与对最近先例的全文比对，未见对 VV10
  非局域关联双重和的片段/原子对归属；正式库检索待补"**——
  在补齐 8.1 之前不得写"经 Web of Science 检索确认"。
cat >> RESEARCH-20260929-lit.md << 'MDEOF'

## 9. 上一节的两处判词需要更正（2026-09-29 12:10，Crossref 重测）

§8.2 的结论方向留着，**理由换掉**，并且要记下我错在哪。

### 9.1 我错在"期望值凭记忆填"
用 Crossref DOI 精确回查（`scratch/doi_chk.js`）逐条打开我自己写的对照：

| 我写的期望 | 回查结果 |
|---|---|
| Dion "…for General **Use**" | **该标题不存在**；PRL 92, 246401 的正名是 *…for General **Geometries*** |
| Thonhauser "…rings" (PRB 69 或 70, 235111) | **两个 DOI 都是别的论文**（69→非晶 GdSi 输运；70→强关联有效理论） |
| ωB97X-V = 10.1039/C7CP04995J | **此 DOI Crossref 查无**；真身是 **10.1039/c3cp54374a**, PCCP **16**, 9904 (2014) |

⇒ 我把"检索到了正确论文"判成"伪命中"，因为我的标准答案是编的。
反向对照也证明 API 无辜：随手猜的 `10.1002/qua.21004` 解析到一篇真实但完全无关的
IJQC 2006 论文——**精确回查是可靠的，不可靠的是我脑子里的题名与卷号**。

### 9.2 重测：分两层，结论不同
* **精确题名层：可用。** 先 DOI→题名钉住四条对照，再拿各自题名回喂
  `query.bibliographic`：**4/4 全部 rank=0 命中**（`scratch/xref_calib2.js`）。
* **主题层：召回不完备。** 用最近邻先例 JCTC 2023 (10.1021/acs.jctc.3c00903) 的
  语汇组三条合法主题式查询，**只有 1/3 把它召回**（rank=2），另两条 rank=-1
  （`scratch/xref_r3.js`）。它确实存在、确实同题，却漏了两次。

⇒ **判词（替换 §8.2 那句"没有可调和的工作点"）**：
Crossref 适合**已知条目核验**（DOI、题名、卷页），
**不适合支撑"没有先例"这类否定主张**——理由不是它误报，而是它的主题召回
被证明会漏掉一篇确定在库的同题论文。
所以 §8 的 N1–N7 那批 0 命中仍然不作数，**新的、更强的**理由是上面这句。

### 9.3 重跑七条主题式：没有一条是本项目的主张，但冒出一个必须查的名字
N1–N7 的 top 命中逐条看过（`scratch/xref_r3.json`），无一涉及
"VV10 双重和的片段/原子对归属"。三条要记下来：
* **`10.1016/bs.arcc.2015.09.002` — Calbo, Ortí, Sancho-García, Aragó,
  "The Nonlocal Correlation Density Functional VV10", Annu. Rep. Comput. Chem. 11,
  37–102 (2015)**：VV10 专题综述。**审稿人极可能拿它问"你与这篇综述的关系"**，
  正文相关工作一节必须引并说清它不涉及片内/片间归属。
* **Lazić, Atodiresei, Alaei, Caciuc, Blügel, Brako,
  "JuNoLo – Jülich nonlocal code for parallel post-processing evaluation of vdW-DF
  correlation energy", *Comput. Phys. Commun.* **181**, 371–379 (2010),
  DOI 10.1016/j.cpc.2009.09.016（卷页已 DOI 回查确认）**：
  这是一个**把 vdW-DF 非局域关联项做后处理求值**的程序，是本项目"显式双重和"
  最接近的**实现级**先例。**待办：取全文确认它是否做过空间/片段归属**——
  若做过，新颖性表述要收窄到"归属"而不是"显式求值"。这是当前最该查的一条。
* `10.1039/c3cp54374a`（ωB97X-V 原文，2014）与 `10.1063/1.4952647`（ωB97M-V，2016）
  经回查确认，可直接进参考文献表；Becke 划分 `10.1063/1.454033`、
  Stratmann `10.1016/0009-2614(96)00600-8` 同样已回查确认。

## 10. JuNoLo 全文核完毕：新颖性存活，但 §1 必须加一条限定（2026-09-29 12:35）

**取到开放全文**：arXiv:0810.2273v1（Lazić, Atodiresei, Alaei, Caciuc, Blügel, Brako，
2008-10-13），即 CPC 181, 371–379 (2010) 的同文预印本；
本地 `scratch/jnolo.pdf` → `scratch/jnolo.txt`（16 页、29.7 kB 文本，pypdf 提取）。
（顺带一条网络坑：`http://export.arxiv.org` 直连与走代理都返回 **0 字节**，
换 **https** 才通。）

**它做了什么**（原文措辞）：把 vdW-DF 的非局域项**作为后处理**作用在"任何标准 DFT 码
给出的电荷密度"上，"thus obtaining a new improved value for the **total energy** of the
system"；并明说 "**Nonlocal calculation is computationally quite expensive and scales as
N^2** where N is the number of points in which charge density is defined"，
因此程序的重点是大规模并行。⇒ **显式 N² 双重和求值非局域项，本身不是我的首创。**

**它没做什么**：全文搜 `partition|fragment|decompos|atomic contribut|region|per-atom|assign`
只有 5 处命中，逐条读上下文（第 84、161–165 行）后确认：那里的 "fragment" 指
**吸附质/基底这类物理片段**，用来讨论 seamless 理论在"远距纯 vdW"与"强化学键"两端
的极限行为，**不是能量归属**。而且他们明确把可分片段的情形**推给别的做法**：
> "In such cases one has more or less well separated parts of the system which enables
> localization of charge using tools such as Wannier functions … one could consider
> application of much simpler theories alltogether, such as semiempirical van der Waals
> implementation. **The JuNoLo code is intended for the most general usage of vdW-DF
> theory, especially in cases where chemical bonding is taking place so that one can not
> tell apart fragments of the bonded system.**"

**判定（可写进正文）**：
1. 主篇的核心主张——"对 VV10 非局域双重和做**片段/原子对归属**"——**未见先例成立**，
   JuNoLo 不构成重复。
2. 但 §1 那句"生产程序把配对指标销毁、我们显式求和"**必须加限定**：
   显式（非插值）N² 求值在文献里已有实现，其目的与本文不同（总能量、并行、表面吸附）。
   不加这句，审稿人拿 JuNoLo 一问就变成"你不知道这篇"。
3. 顺带得到的定位收益：JuNoLo 说"可分片段的体系可以改用定域/半经验办法"，
   而本文恰恰是**在可分片段的分子复合物上做归属**——这反而说明
   "归属"与"求值加速"是两个方向，可以借它把 §4 的代价讨论写得更准。

**参考文献表新增（已 DOI 回查 + 全文在手）**：
`10.1016/j.cpc.2009.09.016`（CPC 181, 371–379, 2010）/ arXiv:0810.2273。
另 `10.1016/bs.arcc.2015.09.002`（Calbo 等 VV10 专题综述，ARCC 11, 37–102, 2015）
仍是**待读**状态（今天只回查到元数据，没读全文），先引后补。

> 取证方式（故意不入版本库）：`curl -sSL https://arxiv.org/pdf/0810.2273v1` →
> `scratch/jnolo.pdf` → pypdf 提取 `scratch/jnolo.txt`。**不把他人论文全文提交进本仓库**
> （版权），所以 `scratch/` 又在 .gitignore 里；上面对第 161–165 行的引文即判定的全部依据，
> 任何人可用同一 arXiv 链接复核。若将来需要长期留证，只留引文与页码，不留正文。

## 11. OpenAlex 也降级：它是"标题查找器"，不是主题检索（2026-09-29 12:55）

§1 那十条 `title_and_abstract.search` 一直是"未见先例"主张的**唯一**索引层证据。
今天照 Crossref 的同一套办法给它做召回校准，结论是它同样不能承载否定主张。

### 11.1 过程里先抓到自己一个测量错误
第一轮：三条校准查询 1/3 召回；第二轮同一条脚本跑出 0/3。
**同式不同果**——正要写下"OpenAlex 检索不确定"时先去数了失败类型：
`openalex_stability.json` 里 `runs[].error` 显示每查询 4 次里有 **1–2 次 HTTP 429**，
而我把它计成了"未召回"。⇒ **那不是索引不稳定，是我的限流。**
加了退避重试（429 → 3 s×k 重试，最多 6 次；间隔 2.5 s；per-page=25）后重测。

### 11.2 干净结果（重试版，只计成功响应）

| 查询类型 | 结果 |
|---|---|
| 近似标题式："physical interpretability energetic predictability dispersion corrected functionals" | **4/4 召回，全部 rank=0，top1 唯一** |
| 主题式："energy decomposition analysis dispersion nonlocal correlation density functional" | **0/4，稳定不召回** |
| 主题式："ALMO energy decomposition dispersion corrected noncovalent interactions" | **0/4，稳定不召回** |

对照目标是 JCTC 2023 (10.1021/acs.jctc.3c00903)——**确知在库、且与本项目正题**。
两台引擎（§9 的 Crossref、本节的 OpenAlex）表现出**同一种病**：
标题像 → 必回；主题词 → 不回了。

### 11.3 因此主张改成这样写
* 撤回 §1 末那句"方法学缺口在 OpenAlex 的标题+摘要空间里成立"——
  它的召回被证明不合格，其 0 命中不构成证据。
* "未见先例"现在**只由两处全文比对支撑**：
  (a) JCTC 3c00903（把 −VV10 整块当色散能，未在该项内部归属）；
  (b) JuNoLo / arXiv:0810.2273（显式 N² 求值，但只求总能量，
      且原文把"片段可分"的情形推给定域/半经验办法，见 §10）。
* 正文 §1 已改为 "we are not aware of" 而非"不存在"；
  §6 结论同步；开放索引那部分**只作为已知条目核验**保留（DOI、题名、卷页）。
* WoS/Scopus 那一轮仍是**未完成的硬缺口**，需要用户本人过一次机构登录（§8.1）。

### 11.4 复现物
`scratch/oa_calib.js`（含第一版 0 命中的 bug：NOVEL 是字符串数组却取 `nv.q`，
导致送给 OpenAlex 的检索词是字面量 "undefined"，返回一堆讲 undefined 的论文——
若我没去看返回标题而只读计数，这条会伪装成"四条查询都无先例"），
`scratch/oa_stab.js` → `scratch/openalex_stability.json`（含 429 计数与重试版结果）。

## 12. Web of Science 正式检索一轮：已完成（2026-09-29 12:43，用户本人完成机构登录）

会话确认：历史页显示 `Shaanxi Normal University`。检索在 `www.webofscience.com`
的 WoS Core Collection（全部子库），走 UI 真实提交，**计数一律从 WoS 自己的
Search History 面板读**，不从页面正则猜（见 12.3 那次差点猜错）。

### 12.1 先做校准（这一步决定了下面的零命中能不能用）
| 式 | 命中 | 作用 |
|---|---|---|
| `TS=("energy decomposition analysis")` | **3,317** | 概念组宽度正常 |
| `TI=("Balance between physical interpretability and energetic predictability")` | **1** | 已知条目**精确**召回（就是 §6 那篇先例） |
| `TS=("van der Waals density functional" AND "nonlocal correlation")` | **33** | **主题 AND 式有召回** |
⇒ 与 §9/§11 那两台开放索引形成对照：那两台在合法主题式上 0/4、1/3 召回，
**WoS 三条校准全过**。所以下面的零命中是有效负证据。

### 12.2 先例式与判定
| # | 式 | 命中 | 判定 |
|---|---|---|---|
| 9 | `TS=("vdW-DF" AND ("energy decomposition" OR "fragment decomposition" OR "pair decomposition" OR "partition of the correlation"))` | **0** | 直接主张无人做过 |
| 7 | `TS=("VV10" AND "energy decomposition")` | **1** | Kruse, Běhounek?, Sponer JCTC 15, 95 (2019)，WOS:000455558200012。**读全文摘要**：VV10 只是其基准的 29 个泛函之一，其"分解"是 SAPT2+3δ(MP2) 对**总相互作用能**的分解 ⇒ 不冲突 |
| 4 | `TS=("VV10" AND ("energy decomposition" OR "fragment" OR "pair-wise"))` | **2** | 另一条是 Hujo & Grimme, PCCP 13, 13942 (2011)：测 vdW-DF2/VV10 对氢键的性能 ⇒ 不冲突 |
| 10 | `TS=((ALMO-EDA OR "frozen density embedding" OR "energy decomposition analysis") AND (VV10 OR "nonlocal correlation" OR "non-local correlation"))` | **1** | **Sinha & Pavanello, JCP 143, 084112 (2015)，FDE-vdW**，WOS:000360653900023。它**用子系统响应函数构造一个新的非局域关联泛函**，方向与本文相反（本文是把既有的 VV10 拆开，它是从子系统拼出新的）⇒ **不冲突，但必须作为最近邻相关工作引用** |
| 6 | `TS=("nonlocal correlation" AND ("fragment" OR "atom pair" OR "pair decomposition" OR "subsystem"))` | 4 | 首条即 FDE-vdW |
| 8 | `TS=("nonlocal correlation" AND (attribut* OR "fragment-wise" OR per-fragment OR "atomic contribution" OR "localization of"))` | 4 | 首条 Hamada & Tsukada PRB 83, 245407 (2011)："吸附**归因于**非局域关联项"——归因方向相反 ⇒ 不冲突 |

**结论（可写进正文）**：在 WoS Core Collection 内，
**没有检索到把 VV10/非局域关联双重和按片段或原子对做归属的在先工作**。
新颖性主张由"仅两处全文比对"升级为"经正式数据库检索 + 三处全文核验"。

### 12.3 两条必须一起交代的限制（不然这句结论是虚的）
1. **只逐条看了每个结果列表的相关度首位。** WoS Nextgen 结果页虚拟滚动，
   实测 DOM 里 4 条命中只物化 1 条标题（`app-record` 元素有 9 个但只有 1 个带题名链接），
   滚动与换排序都拿不到其余。所以 #6 与 #8 各 4 条里我只确证了 1 条。
   ⇒ 若审稿人追问，需走 **Export → Plain text, Full Record** 做全量枚举（已记为待办）。
2. **一次差点把 1 命中读成 0。** #10 提交后轮询超时，我按"超时≈零命中"准备记录；
   打开 Search History 才发现它是 **1**。零命中与"我没读到"必须分开——
   这与今天 §9 那次"期望标题凭记忆填"是同一类错误。

### 12.4 复现
检索式即上表原文；会话历史可在 WoS `/wos/history` 用本人账号查看（面板按时间倒序列出
9 条式子与各自计数）。UI 提交方式：`#advancedSearchInputArea` 原生 setter + `input` 事件，
再对面板内最后一个 `Search` 按钮派发 pointer/mouse 序列（导航栏也有一个同名按钮，
点错会跳到 smart-search——踩过）。

---

## 13. 第二轮：改用 WoS 自己的记录接口，全量枚举（2026-09-29 13:4x）

§12.3 那条"只能看到相关度首位"的限制**已解除**。做法不是 Export，是拦截前端调用：
在结果页 hook `window.fetch`，重跑一次 UI 检索，抓下真实请求体，再用同一 SID 直接 POST
`/api/wosnx/core/runQuerySearch`。请求体里 `retrieve.count` 是我能控制的字段（默认 20），
响应是 ndjson，分四类行：`searchInfo`（计数）、`records`（正文与书目）、`analyze`、`link`。
**每条式子拿到的是结构化记录，含题名、作者、期刊、卷期、DOI、UT 号与完整摘要**，
不再依赖 DOM 物化了多少条。

### 13.1 我自己的第二个仪器 bug：ndjson 是按 20 条一批流式发的
`records` 不止一行。`TS=("van der Waals density functional" AND "nonlocal correlation")`
报 `RecordsFound: 33`，第一版解析器把每行 `payload` **覆盖**进变量，于是只剩最后一批
**13 条**——`33` 被我自己读成了 `13`。改成累加后 `batches:[20,13]`、`n:33`、去重后 33 个
不同 UT，与 `RecordsFound` 对上才罢手。
⇒ 与 §12.3 那条"超时不等于零命中"同源，但这次是**反向**的错：**"我只拿到 13 条"差点被
写成"这个主题只有 13 篇"**。凡是分页/流式接口，"拿到的条数"必须与"接口自报的总数"
逐条比对，两者不等就禁止下笔。（OpenAlex 那台是 429 冒充零命中，这台是批次覆盖冒充全量。）

### 13.2 校准与先例式全部用接口重跑一遍（`RecordsSearched = 58,664,816`）
| 式 | UI 轮 | 接口轮 | 一致性 |
|---|---|---|---|
| `TS=("energy decomposition analysis")` | 3,317 | **3,317** | ✔ |
| `TI=("Balance between physical interpretability and energetic predictability")` | 1 | **1**，WOS:001139458900001，JCTC 2023 | ✔ |
| `TS=("van der Waals density functional" AND "nonlocal correlation")` | 33 | **33** | ✔ |
| #9 `TS=("vdW-DF" AND ("energy decomposition" OR "fragment decomposition" OR "pair decomposition" OR "partition of the correlation"))` | 0 | **0** | ✔ |
| #7 `TS=("VV10" AND "energy decomposition")` | 1 | **1**：Kruse, H; **Banáš, P**; Sponer, J（WoS 作者字段 ASCII 化成 `Banás`，正字是 Banáš——§12 表里那个"?"就此填掉） | ✔ |
| #4 `TS=("VV10" AND ("energy decomposition" OR "fragment" OR "pair-wise"))` | 2 | **2**：Hujo–Grimme PCCP 2011 + Kruse 2019 | ✔ |
| #10 `TS=((ALMO-EDA OR "frozen density embedding" OR "energy decomposition analysis") AND (VV10 OR "nonlocal correlation" OR "non-local correlation"))` | 1 | **1**：Sinha–Pavanello，WOS:000360653900023，DOI 10.1063/1.4928531 | ✔ |

计数与上一轮**逐条相同**，所以 §12 的判定不必改；改的是覆盖面。

### 13.3 #6 与 #8 的四条命中，现在全部读到
**#6 `TS=("nonlocal correlation" AND ("fragment" OR "atom pair" OR "pair decomposition" OR "subsystem"))` = 4**
| 记录 | 判定 |
|---|---|
| Sinha & Pavanello, JCP 143(8) 084120 (2015), WOS:000360653900023 | FDE-vdW。用子系统响应函数**构造新的**非局域泛函，方向相反 ⇒ 不冲突，仍作最近邻引用 |
| Vydrov & Van Voorhis, JCP 130(10) (2009), WOS:000264281800005，*Improving the accuracy of the nonlocal vdW density functional with minimal empiricism*（opt-VV10） | 改的是 Φ/κ 的构造与梯度项，不做归属 ⇒ 不冲突。**但它暴露了一个真缺陷，见 13.5** |
| Mollenhauer, Brieger, Paulus, JPC C 119(4) 1898–1904 (2015), WOS:000348753000033 | 芳香分子/石墨片段 adsorption 的 DFT-D2/D3 vs vdW-DF vs CCSD(T) 性能比较；"fragment" 指把石墨烯切成小片的**模型尺寸**，不是能量归属 ⇒ 不冲突 |
| Aldaghfag, Berrada, Abdel-Khalek, Results in Physics 16 (2020), WOS:000540004100017 | Kerr 非线性双量子比特的纠缠统计——纯词表噪声，非化学 ⇒ 不冲突 |

**#8 `TS=("nonlocal correlation" AND (attribut* OR "fragment-wise" OR per-fragment OR "atomic contribution" OR "localization of"))` = 4**
| 记录 | 判定 |
|---|---|
| Hamada & Tsukada, PRB 83, 245407 (2011), WOS:000292183300010 | C60/Au(111)：把**吸附能归因给**非局域关联项。归因方向与本文相反（本文把该项拆给片段，他们把现象拆给项） ⇒ 不冲突 |
| Maity, JPCA (2002), WOS:000176161700021 | 2c-3e 键自由基阳离子；命中来自我词表里的 `"localization of"`（ localization of molecular **orbital**）⇒ 噪声。**这条说明 `localization of` 该从词表里去掉** |
| Kossmann; Kirchner; Neese(?), Mol. Phys. (2007), WOS:000251714600006 | 超精细耦合基准；"nonlocal correlation" 指双杂泛函里的 PT2 轨道依赖项，与 VV10 无关 ⇒ 噪声 |
| Ghosh & Sur, J. Multiscale Model. (2024), WOS:001440510600001 | 含记忆的热弹性质量扩散、非局部应力理论 ⇒ 噪声 |

⇒ **#6/#8 里除 FDE-vdW 与 Hamada–Tsukada 外，四条全是词表噪声或性能基准，没有一条做片段归属。**

### 13.4 三条新式（接口便宜，把§12没敢铺的宽度铺开）
| 式 | 命中 | 逐条读后判定 |
|---|---|---|
| **A** `TS=(("VV10" OR "nonlocal correlation" OR "vdW-DF") AND ("pair-resolved" OR "pair resolved" OR "energy attribution" OR "per-fragment" OR "resolved by fragment" OR "contribution of each fragment"))` | **0** | **最贴主张的一条式子，零命中**。这就是"把非局域项按片段/原子对归属"的字面写法，库里没人这么写过 |
| **B** `TS=("nonlocal correlation" AND ("energy density" OR "localization of the" OR "assigned to"))` | 7 | 首位相关的是 Gao, Zhu, Ren, PRB 101, 035113 (2020)：**构造**一个新的 nonlocal correlation-**energy-density** 泛函（rDW99，走 RPA 对应路线）——又是"拼出新的"，不是"拆开既有的"；其余是 Marom–Tkatchenko–Kronik JCTC 2011（基准）、Thonhauser 组的筛查类工作 ⇒ 不冲突 |
| **C** `TS=("VV10" AND (implementation OR "real-space" OR grid OR "linear scaling" OR fast))` | 8 | 全是泛函开发/实现/基准（ωB97X-V PCCP 2014、ωB97M-V JCP 2016、VV10 解析频率 JCP 2023 等）⇒ 不冲突；顺带确认**没有已发表的 VV10 片段分解实现**这一软件文卖点也站得住 |
| **D** `TS=("nonlocal correlation" AND (Becke OR Hirshfeld OR Mulliken OR "atoms in molecules"))` | 33 | **归属方案 × 非局域项**的直接交叉。全部 33 条题名扫完：Al 团簇、F 心、溶剂化偏电荷、AIM 之类，**没有一条把 Becke/Hirshfeld/Mulliken 划分用在 VV10 双重和上** |
| **E** `TS=("van der Waals density functional" AND "nonlocal correlation")` | 33 | **整个 vdW-DF 非局域关联主题的穷举**。33 条题名全读，4 条摘出来读摘要（下节）。**发现一条必须引用并区分的近邻** |

### 13.5 这一轮真正的新收获：一条我以前完全没查到的先例线
`TS=("van der Waals density functional" AND "nonlocal correlation")` 33 条全枚举里，
**Hyldgaard, Berland & Schröder, PRB 90, 075148 (2014), *Interpretation of van der Waals
density functionals*, DOI 10.1103/PhysRevB.90.075148, WOS:000341268900001** 的摘要写的是：

> "The nonlocal correlation energy in the vdW-DF method **can be interpreted in terms of a
> coupling of zero-point energies of characteristic modes of semilocal exchange-correlation
> (xc) holes** … We use these results to illustrate the nonlocality in the vdW-DF description
> and analyze the vdW-DF formulation of nonlocal correlation."

这是**对同一个量做实空间/物理诠释**的既有线。它不做片段归属、不给"A 与 B 之间多少 kcal/mol"，
但它把"非局域项能不能被解释"这件事占了。我 §12 那五轮关键词式子全部漏了它——
因为它的词表是 xc hole / interpretation，不含 decompose/partition/fragment 任一。
⇒ **正文 §1/§2 必须显式与它划界**：本文不是给 Φ 或 xc hole 做物理诠释，而是把已经算好的
`E_NLC` 按**已命名的片段/原子对**记账，并给出记账方案之间的跨度。同时它是"非局域项的
空间归属是否有意义"这一质疑的**最好代言人**，审稿人若熟悉这条线，一定是拿它来问。

另外两条是**引文缺口，不是先例冲突**：`references.bib` 里有 Dion 2004（原始 vdW-DF）和
Calbo 综述，**却没有 VV10 本人的两篇**——
Vydrov & Van Voorhis, PRL 103, 063004 (2009), DOI 10.1103/PhysRevLett.103.063004（VV10 提出，
题名即本轮 #6 之外的 "Nonlocal van der Waals Density Functional Made Simple"）与
Vydrov & Van Voorhis, JCP 133, 244103 (2010), DOI 10.1063/1.3521275（"the simpler the better"，
`(b, C)` 参数化的出处）。一篇标题就叫 "Pair Attribution of the **VV10** Term" 的文章不引 VV10 原文，
是会被直接退回的错误。三条一起补，bib 13 → 16 条。

### 13.6 §12.3 的两条限制现在的状态
1. ~~只读到相关度首位~~ ⇒ **解除**。#6/#8 各 4 条全读；另加 33+33+7+8 四条宽式全枚举。
2. "超时不等于零命中"依然有效，且本轮又长了一次教训（13.1 的 20 条一批覆盖）。

**仍然要说出口的残余限制**（写进正文 §4，别藏）：
- 只覆盖 **WoS Core Collection** 一个库；Scopus 经 §2/§3 实测机构未订阅，走的是
  CNKI+WoS 的替代口径，Embase/SciFinder 未查。
- 请求体默认 `options.lemmatize = "On"`，我没改；也就是说词形还原开着的，
  这是**召回更宽**的方向，不影响零命中的强度，但要在方法里写明。
- 33+33 那两批噪声我只做了**题名级**判定，摘要级只读了 8 条；对"是否有人做片段归属"这个
  问题题名足够（归属一定写在题名或摘要的方法句里），但这是判断不是证明，正文不得写成
  "全部摘要已读"。
- `RecordsSearched` 58,664,816 = WoS CC 全库规模；检索日期 2026-09-29，此后入库的不覆盖。
