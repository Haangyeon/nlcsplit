# 下一步计划 + 死会话成果抢救件（2026-10-11）

> **本文档存在的原因**：会话 `6b5e0489-87de-42fb-937e-a5d02c5f48a8`（"GAMESS开发"）在 10-11 13:47 死亡，
> 死因见文末 §六。它在当天 00:07–00:21 做了一整轮期刊与缺口研究并给出了结论，
> **但一个字节都没写进仓库**（HEAD 仍是 `df8ff66`，工作树干净），
> 之后 12:56 起用户连发 6 次"接下来该怎么办？给我制定一个计划"，每次都撞在 60 s 首包超时上，计划始终没产出。
> 本文档 = 从它的 transcript 里捞出结论 → **逐条回仓重核** → 落成可执行计划。
> 未通过核验的数字一律进 §五"待核"，不进正文。

---

## 一、发表对象与期刊判定（已核验）

前提纠正：ωB97X-V 那条 Fortran 线已作废（`rhfuhf.src` 让多中心 RHF 收敛到错误解），
且哈密顿量是别人的 → 属 JCTC 明文拒收的 "straightforward application of well-established methods"。
**能发表的对象只有 `nlcsplit/`**（VV10 非局域关联项的数值网格片段归属）。

| 刊 | 裁定 | 依据 |
|---|---|---|
| JCTC | 无软件专轨，只 Article/Letter；明写拒 "well-established method 的直接应用" | 框架必须是"审计 + 屏蔽证书**就是**新方法"，不是"我们重实现 VV10" |
| **JCP（首选）** | 同类负面结果的正当归宿 | 文体模板：Lehtola & Marques, *Many recent density functionals are numerically ill-behaved*, JCP 157, 174114 (2022) |
| JCC | 分区歧义主题的自然家 | Andrés 等 *Nine questions on energy decomposition analysis*, JCC 2019 |
| SoftwareX / JOSS | 强制砍掉审计部分，发现拿不到引用权重 | `paper/joss/paper.md` 已成型 11 KB，只缺二作 ORCID（`orcid: TBD-AUTHOR-2`，第 15 行） |

---

## 二、缺口清单（按性价比，全部带仓内出处）

| 级别 | 缺什么 | 核验状态 |
|---|---|---|
| **P0-a** | **四句定性先例全部未引**：Chem. Rev. 2016 "atomic contributions **is not well-defined**"、Keller 2025 JCP "**cannot** be decomposed into atom-pair"、Lehtola 2022、Andrés 2019。`grep -i "lehtola" paper/references.bib` 只有 `lehtola2018libxc`；`ill-behaved / jcc.26003 / nine questions / Keller` 在 `paper/` 正文命中 **0**。不接住 = 审稿人一句"早知道了"毙掉；接住 = 把最大风险翻成动机："学界断言了十年，第一次有人给数" | ✅ 本次 grep 复核 |
| **P0-b** | **A/B 口径**（等作者点头，不动正文） | 见 `QODER_INTL_HANDOFF_20261010.md` §五 |
| **P1** | **8 体系 → 满 S22**。`nlcsplit/geomlib.py` 的 `S22` 字典实测 **8** 条；22 个官方几何已在集群（交接件 §六）。"只测 8 个配合物"是头号 desk-reject 触发项。各格独立可并行 | ✅ `S22 entries: 8` |
| **P2** | **headline 别写成"与量同量级"**。按 Table 1（`paper/main.md:420-429`）÷ 家族内跨度（交接件 §五）实算：比值跨 **0.63 %–19.6 %**（31 倍），可守的说法是"最高约 20 %、因体系而异" | ✅ 本次逐行重算，见 §四 |
| **P3** | 扩展 rVV10 / ωB97M-V（§4.5 自陈未测）＝真新能力；但 PySCF 只实现裸 VV10 核（`numint._vv10nlc`），无参照，须自建核 + 对 ORCA 验证 | ⚠️ PySCF 侧为 transcript 结论，动身前需再确认 |

---

## 三、本次新抓到的一个顺序坑（交接件 §四没写）

**发布链已关账，但最新那部分科学是关账之后才落地的。**

- `570dc48` = 2026-10-09 **20:16:53**（release QA / wheel 钉版）
- `0d40520` = 2026-10-09 **23:28:10**（家族外分区测量脚本 Voronoi + Hirshfeld 入库）→ 晚 **3 h 11 m**
  （死会话写 3 h 12 m，此处已改正）
- `dist/nlcsplit-0.1.0-py3-none-any.whl` 实测：**39 个成员**，文件名与 `.py` 内容里
  `hirshfeld|voronoi|crossfam` 命中数 = **0**

今天还不算错：家族外八格尚未写进 `main.md`（grep 为空），所以 `paper/main.md:1232-1233`
那句 "implements the kernel, the four attribution schemes, the fragment decomposition and
**every table in this paper**" 仍然成立（`nlcsplit/partition.py:17-22` 确实只有
becke / becke-becke-rad / becke-treutler / stratmann 四方案；Voronoi 与 Hirshfeld 活在
包外的 `evidence/common_grid/hirshfeld_crossfamily.py`）。

**但一旦按 A 或 B 把八格写进正文，§5 当场变假，评审 `pip install nlcsplit` 复现不出 headline。**

⇒ 硬顺序：**① 家族外分区并进 `partition.py` → ② 重建 wheel → ③ 重跑发布 QA → ④ 才允许动正文那两格**。
交接件 §四 把 P0→P2 列成纯写作任务，漏了这层，照它做会踩进去。

---

## 四、比值重算（本文档 §二 P2 的原始依据）

家族内跨度 ÷ |dE_NLC|，跨度取交接件 §五，dE_NLC 取 `paper/main.md:422-429`：

| 体系 | 家族内跨度 | dE_NLC | 比值 |
|---|---|---|---|
| 苯 (A) | 0.0274 | 4.367 | **0.63 %** ← 下界 |
| 甲烷 | 0.0034 | 0.517 | 0.66 % |
| 氨 | 0.0284 | 0.678 | 4.19 % |
| 水 | 0.0433 | 0.593 | 7.30 % |
| 苯 (B) | 0.2195 | 2.388 | 9.19 % |
| 苯-甲烷 | 0.2143 | 1.404 | 15.26 % |
| 苯-氨 | 0.2219 | 1.327 | 16.72 % |
| 苯-水 | 0.2468 | 1.259 | **19.60 %** ← 上界 |

极差 31 倍 ⇒ "固定分数"式的说法不可写，与交接件 §五"比值列只作参考、分母不稳"一致。

---

## 五、分波执行计划（每波带验收判据）

| 波次 | 内容 | 成本 | 验收判据 | 阻塞 |
|---|---|---|---|---|
| **零** | P0-a 引文补全：4 条先例逐条查 Crossref 建 bib（含 DOI），起草"接住两句定性断言"的段落放 `paper/notes/`，**不进 main.md 正文** | 纯本地 | `node tools/claim_gate.js` rc=0；每条 bib 有 Crossref 原始返回可复查 | 无，可立即开工 |
| **零'** | §三 顺序坑的工程半边：把 Voronoi/Hirshfeld 并进 `partition.py` 的 `SCHEMES`，与包外脚本对跑逐格复现八格 | 本机分钟级～小时级 | 新旧两条路径八格读数逐位相符；`MANIFEST.sha256` 在所有证据编辑定稿后**最后**重生成 | 无 |
| **一** | 重建 wheel → 重跑发布 QA → §5 那句恢复为真 | 本机 | wheel 成员数变化记录在案，`hirshfeld\|voronoi\|crossfam` 命中 > 0 | 依赖 零' |
| **二** | A/B 落笔（唯一卡正文的事，**要作者点头**）+ P2 的 headline 措辞改成"最高约 20 %、因体系而异" | 纯写作 | 14 处实质差错闸门全绿；S34 附录行需先解决"净化 sbatch 副本"（`gateB_intranet`） | 依赖 一（顺序不能反） |
| **三** | P1 满 S22：14 格补测，各格独立可并行 | 集群 | 已测档位实测 799.9 / 846.2 / 978.6 / 1952.7 / 2180.8 / 2279.4 / 5163.6 / 5207.6 s；14 格串排 ≈ 4–9 h，含大体系上界 1 天（**外推，非实测**） | 按规矩 ≥30 min 直接排，不用问 |
| **四** | JOSS / SoftwareX 备选路线成文 + 二作 ORCID 占位符清除 | 纯写作 | `paper/joss/paper.md:15` 的 `TBD-AUTHOR-2` 与 `:169` 的 `PENDING-CONTRIBUTION` 由作者填真值 | 依赖作者提供 |
| **五** | 只有作者能做的发布动作（PAT → `make_public_repo.js` → push → 转 public → Zenodo → ScholarOne **只 Save 不 Submit**） | — | 交接件 §四 末行 | — |

**待核清单（不许进正文，动身前自己验）**
- Lehtola & Marques 2022 "被引 63" —— 来自 transcript 的网页检索，未落盘原始证据。
- tcc "36 LSF slots、同行占 24" —— 交接件只记了 36 核；24 这个数是 transcript 口述。
- exam01 CH₂ `-30.71` vs 文档 `-37.24`（ωB97X-V 作废证据）—— 在 tcc/WSL 侧，本仓无从复核。

---

## 六、死会话为什么死亡（记进档案，别再撞）

`Model stream timed out before response headers after 60s`（HTTP 408，11 次重试全挡回），
`cmodel / ultimate / kmodel_latest` 三个模型同一条会话一起超时 ⇒ 与模型无关。
根因：**该会话 transcript 已达 4.70 MB / 2 505 条记录，单次请求带 171 条消息、history 993**，
首包延迟从 6 s（正常）漂到 > 60 s；12:00 之后该会话 120 次请求只有 89 次成功。
放大器：用户 13:18/13:20/13:25/13:30/13:39 六次重发同一句，每次都把正在跑的重试链掐断
（UI 里 4 条 `interrupted` + 1 条 `failed`），13:38:30 那次已跑 53 s、差 7 s 到线被下一次重发打断。

**纪律（新窗口也照做）**：单会话 transcript 超 ~1 MB 就必须收口落盘并换窗口；
一条消息发出去后**不许重发**，超时期间它在自动重试；跨窗口只传文件路径，不传历史。

---

## 七、给新窗口的开场指令（直接粘这段，别带历史）

```
先读两份文件，再开工：
  E:\Project\GAMESS\paper\notes\PLAN-20261011-next-steps.md   （计划与本次已核验结论）
  E:\Project\GAMESS\paper\notes\QODER_INTL_HANDOFF_20261010.md （交接件，含 A/B 两写法与红线）
按 §五 的波次表执行：先做第零波与零'波（都不依赖我点头），
第二波（A/B 落笔）等我点头才动正文。
开工前确认 git HEAD = df8ff66、工作树干净、node tools/claim_gate.js 返回 rc=0。
```

---

## 八、本文档的核验记录（谁都能重跑）

- `git log --oneline -1` = `df8ff66`；`git status --short` = 空（本文档写入前）
- `node tools/claim_gate.js` → rc=0（写入后需再跑一次确认没退）
- wheel 成员：`python -c "import zipfile,re; z=zipfile.ZipFile('dist/nlcsplit-0.1.0-py3-none-any.whl'); n=z.namelist(); print(len(n), sum(1 for x in n if re.search('hirshfeld|voronoi|crossfam',x,2)))"` → `39 0`
- `nlcsplit/partition.py:17-22` 四方案；`evidence/common_grid/hirshfeld_crossfamily.py` 存在且不在包内
- `nlcsplit/geomlib.py` 的 `S22` 字典条目数 = 8
- `paper/main.md:420-429` Table 1、`:1232-1233` §5 原句、`:431` level 注
- `paper/joss/paper.md:15` `orcid: TBD-AUTHOR-2`
- 用工时：`evidence/common_grid/` 三份 `.out` 里的 `用时 … s` 行（§五 波次三列了 8 个端点值）
