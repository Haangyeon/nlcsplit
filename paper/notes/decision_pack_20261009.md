# P4 决策包（2026-10-09）——投稿路线报价，与只有他能做的清单

## 0. 科学面现状（一句话）

外部盲审四席加自查，共抓到 **14 处实质差错**，现已全部落地修正：前九处是 2026-10-05 那轮
"复查全部科学主张"（提交 293bdf9），第十处是领域席抓到的 §4.1 反泊松假豁免（我核原文成立，
随后实测三体系 ΔE_NLC 的 BSSE 改写），第十一、十二处是今天在 P2 落地时开原件才看见的
——附录 S27 把**未反泊松那一列**的冻结核—全电子之差当物理写，§2.5 把**同一版本的两条建网格
路径**之差当版本之差。**第十三处是 §6 那句"跨度不随网格变细而缩小"**：它被 §3.4 新加的 level-0
披露逼出来（苯二聚体两格 level 0 给 0.072 / 0.310，level 1 给 0.032 / 0.219 —— 从最粗网格上来
确实缩约一半），已改成"level-1 数字；1→2 变动小于 0.001；会缩一段然后停止收敛，而不是收敛到零"。
计划的十三处改写**全部完成**：八格公共网格已齐，纯归属跨度 0.0034–0.2468、求积侧总量跨度
0.0001–0.0085、比值 1.29×–1046×（八格全 >1 ⇒ 预登记的结局 A 成立，"归属不确定度"名实相符），
带值在六处载体统一标注 grid level 1。

**第十四处是今晚复查"图与正文口径同源"时撞上的**（不是席位、不是闸门抓的）：撤回过的
"空载机器"仍活在**摘要第 46 行与 §6 第 924 行**，而 `figures.py` 的 (a) 面板标题早就是
"contention gate: external runnable tasks = 0 … not an idle-box claim"。原件也不支持那个词——
两个计时侧车合起来 11 行 / 44 个 run，`other_runnable` 44 个全为 0、`valid_timing` 44/44，
可 `load1` 实测 **0.99–4.24**：成立的是"没有别的外部可运行任务"，不是"机器空着"。
两处正文与 software.md 里对驱动前置条件的转述已改成与原件同话，未新增任何数字
（main 38 页 / software 15 页 / `failed checks: 0` / claim-gate rc=0）。
教训形态：**"同一件事在两个载体里说法不同"没有机器判据**，只有主动按口径去 grep 才会遇见。

另外两条台账清掉了：
- **U1（领域席 Major 7"成本高估"）不成立**：`evidence/scaling/step_j.json` 与其 09-30 重跑档
  共 33 对 screened/exact 计时，**0 对快过精确和**（比值 1.08–10.28 与 1.37–13.29）；
  只看 level 1 的 9 对也是 0 对，比值 1.08–2.63。正文本来就写"none beat the exact sum"，
  席位是把它读成了主张加速。
- **U2 部分清了**：Treutler & Ahlrichs 键已进 `.bib`（Crossref 实测：*Efficient molecular
  numerical integration schemes*, JCP **102**, 346–354, 1995, DOI 10.1063/1.469408）。
  席位列的其余缺引（Horn/Mao/Head-Gordon、IQA/QTAIM、partition-DFT、Hirshfeld-I、
  vdW-DF 线性标度、原子分辨 MBD）**仍未进**，因为每条都要先过 Crossref 再决定引不引。
- **U3（今天新增，已清）**：全部 25 条 `@article` 的**年份口径**清点做完了，判据是 Crossref 的
  `published-print`（纸质卷期年），不是首次上线年。抓到两条内部不自洽并改掉：`kruse2019dna`
  2018→**2019**（JCTC 15, 95–115）、`dasgupta2023` 2023→**2024**（JCTC 20, 49–67）——
  原先 `volume/pages` 是纸质卷期而 `year` 是上线年，读者按"卷 15 (2018)"检索会查不到。
  原件：`evidence/bib_provenance/20261009T124519Z_bib_all25_issue_year_check.out`（改前，
  MATCH 23 / DEVIATION 2，`.rc`=1）与 `...124738Z..._after_fix.out`（改后 25/25，`.rc`=0，
  同一次运行里负控仍抓住被改成 1901 的那条）。键名没改（`dasgupta2023` 现指 2024 那期），
  因为改名要动两处正文引用而不透明标签本身不是主张；正文没有散文年份跟着改（三处载体 grep 过）。

## 1. 三条路线的报价

| 路线 | 做什么 | 机时 | 我的工时 | 席位原话与风险 |
|---|---|---|---|---|
| **A 投 JCC**（期刊适配席判定的 right venue，Major-Revision 级） | 正文已按十二处改完；把 §3.2 的取证叙述搬 SI（纯编辑）；补前置信息 | 0 | ~0.5 天 | "JCC accepts an uncertainty-audit contribution that JCTC sorts as incremental" |
| **B 投 JCTC** | A 的全部 **+ 一个真正的概念增量**：把归属从"数值积分家族"里拿出来——现四方案中三个是同一个 Becke 乘积式换半径表，第四个 Stratmann 虽是另一套式子，但在公共网格上与 Becke 差 ≤0.0021 kcal/mol，而半径表能把数拉开 0.003–0.083；所以缺的是 **Hirshfeld-I / QTAIM  basin / Voronoi 一类的家族外归属**，走已存在并被测试覆盖的 `soft=` 通路即可 | 集群 ~1 天（八体系 × level 1，家族外归属需自建权重） | 机时外 +1 天 | 席位判 "wrong first move; probable rejection without review"，依据的两句自我拆台话（标题 overclaim、"this is not an EDA"）已改；但 M2 还在：全文仍然只说"不是什么"，没说 ALMO-EDA/SAPT 用户该怎么用我们的数 |
| **C 拆两篇** | 把 §3.6 的 screening-certificate 结果 + `p2.md` §4–5 独立成方法篇投 JCTC；主篇按 A 投 JCC | 0 | +1.5 天（两篇骨架都要重写，软件文归属要重划） | 席位原话："The JCTC-shaped asset here is the screening-certificate result — a different paper." |

我的建议只作参考：**先按 A 把稿子做成可投状态**，B 的家族外归属作为一个独立增量排队做——
它不否定 A 的任何数，做了也不阻止投 JCTC；而 C 要动的是稿件边界，得他定。

## 2. 只有他能做的（我不能替，也不该猜）

1. 新 classic PAT → **最后再跑一次 `node tools/make_public_repo.js`** → `push_manual` → 仓库转 public
   → 换掉 release 里过期的 wheel。顺序理由（今天实测到）：导出会把 `evidence/**` 连同各目录的
   `MANIFEST.sha256` 一起复制进发布树——今天 12:04 之后落地的两份比对档案就让导出**拒绝出货**
   （`gateC2_scrub_digit_invariance` 报"母仓有清单但这份文件没登记进去"，`"shipped": false`，
   exit 1，旧产物原样保留）。所以清单必须在导出之前定稿。
2. 第二作者（Changwei Wang）的 ORCID、邮箱、是否通讯；作者顺序与单位行是否照 `main.md:5-11`。
3. 审稿人提名（JCTC/JCC 都要），以及 COI、 funding 两段的实际内容（现在是写给编辑看的指示句）。
4. Zenodo DOI（如果要）；ScholarOne 的登录与 **Save 之后由他点 Submit**——我停在 Save。
5. 路线 A/B/C 的选定；以及"正文 4,569 词的出处附录要不要整段搬 SI"（席位的 desk-reject 触发项第 1 条）。

## 3. 还压着的两件小事

- **测试套件**：全套 **79 passed / 504.41 s**（`evidence/release_qa/20261009T094106Z_full_suite_79passed.log`，
  退出码另存同目录 `.log.rc`；software.md 引的就是这份，10-09 那次限 4 线程）。
  原先这里写的"79 passed / 355 s（2026-10-06 的档）"**用词错过一次**：全仓 grep `355.09` 只命中
  `nlcsplit/logs/full_suite_after_closure.log`（4 行、无环境头、gitignore 的工作日志，宿主时钟
  mtime 2026-10-06T15:13），按 software.md 自己定的规矩它**不是**归档；更正已追加进上面那份
  10-09 档案的末尾（原文第 4 行不动）。没有把它升级成归档：它没有来历可写。
  集群默认 python 里**没有 pytest**（实测 `ModuleNotFoundError`），装它要动他账号环境，我没动；
  这 6–8 分钟只能留在 WSL 跑。
- **图**：§3.6 该拿的 `figs/fig3_screening_cost.png` 席位提到了，属编辑级，做 A 时一并处理。
