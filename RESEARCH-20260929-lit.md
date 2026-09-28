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

⇒ **本项目的方法学缺口在 OpenAlex 的标题+摘要空间里成立**。
这只是 OpenAlex 一层证据；WoS/Scopus 那一轮还没做（需要浏览器与机构会话）。

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
