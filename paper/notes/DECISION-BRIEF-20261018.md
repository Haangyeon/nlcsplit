# 决策简报 · 2026-10-18（一页）

对象：`E:\Project\GAMESS\nlcsplit\` 随包方法与论文（ωB97X-V 的 VV10 非局域关联项在数值网格上
显式算成片段/原子对归属）。
用途：本轮实测把"要不要重算"变成了"改哪几行字"，**下面每一件都给推荐·代价·卡哪条验收·谁有权**。
背景件：裁断全文 `paper/notes/REFEREE-ADJUDICATION-20261018.md`（含 §五逐条对账）、
执行记录 `PROGRESS-nlcsplit.md` 2026-10-18 一节。

## 一、本轮已完成（不需要你决定，只需你抽查）

| 件 | 结果 | 一手证据 |
|---|---|---|
| 裁断第 1 步（认证断言 + 负对照） | **7 例全 PASS、rc=0**，含它点名的"605 B 残件" | `evidence/common_grid/20261018T121752Z_selftest_certification_gate.out` |
| 顺带查出的**第七条静默遮蔽** | `missing/unparsed`（没测）原来排在 `if mismatch: return 1` 之后 ⇒ 残件会被报成"数值不符"；已改**没测优先 rc=2** | 回归件 `20261018T121833Z_w4_closeout.out`（仍 rc=1、仍那四格 OVER、清单没动 ⇒ **线上判决未变**） |
| 裁断第 2 步（球平均判别） | 判语 **`INCONCLUSIVE`**（按跑前写死的三分法，不事后改口）：跨线程 `6.43e-01 → 2.23e-05`，但**同线程两定义本身差 `3.31e-01`** | `20261018T114952Z_spherical_promolecule_thread_probe.out` rc=0 |
| 裁断"仍缺的核验"第 3 条（ORCA 逐条 PySCF 版本） | **闭合且稿子站得住**：8 行 = 1×2.12.1（水）+ 7×2.14.0，`:338-344` 已披露 cross-release；ORCA 侧两来源在 SI S18（`:1388`）已写明 | `evidence/orca_widen/cross_program_table.json` 每行 `pyscf_version` |
| 裁断"仍缺的核验"第 4 条（libxc 版本对账） | **闭合，并查出正文一处事实错**：本机是 **5 份 / 4 个版本**（5.2.3、6.2.2、7.0.0、7.1.2×2），**五份全部只导出 `xc_nlc_coef`** | `evidence/recompute/20261018T120810Z_libxc_version_census.out` rc=0 |
| 裁断第 3 步的 UTF-8 那一半 | 954 份里**真文本缺陷只有 3 份且同族**（另 18 份本该是二进制）；机制到字节级＝**同一份档前半 GBK、后半 UTF-8** | `evidence/release_qa/20261018T122724Z_utf8_census.out` rc=1=`NEEDS_FIX` |
| 一个从来没成功过的收口环节 | `make_evidence_manifest.sh` 对"清单里无子目录条目"的目录必然失败（空数组退化成一个空行喂给 `sha256sum`）；已修，`recompute` 11→15、`release_qa` 110→114，并用 `sha256sum -c` 独立复核 rc=0 | 修在 `tools/make_evidence_manifest.sh`；⚠ 以前第 2 步从没跑到过，**满表真通那天会当场炸**，现在提前炸掉了 |

## 二、等你拍的（按依赖排序；#1 不拍，#6/#7 都不该动）

| # | 件 | 推荐 | 代价 | 卡哪条验收 | 谁 |
|---|---|---|---|---|---|
| **1** | **G5：Hirshfeld 那一列怎么处置**（四格超 `1e-3`，收口第 1 步至今 STOP 在这） | **(a) 保留现状 + 改名并限定**：列名不再叫"Hirshfeld"，写成"非球平均库存化权重（本机构建、单线程下逐位确定）"，并把它从正文误差棒里摘掉。**(c) 已被实测证明"技术上成立、但不是免费的"**：定价探针 `20261018T120123Z_spherical_column_price.out`（rc=0）给出 `NEWCOL_OK=5.68e-06` **[LOW]** ⇒ 球平均列**在打印精度 1e-4 下真的可复现**（它确实治病）；但 `PRICE=1.2984e-02` **[HIGH]**，是认证门 `1e-3` 的 13 倍、与那四格 OVER 同量级 ⇒ **旧读数全部作废，换的是另一列的数**。要不要为一列 SI 构造的逐位可复现付这 30.6 h，是你的取舍，不是我的 | (a)≈改字，零算力；**(c)＝22 格重取，实测 30.6 h**——22 份 rc=0 原件的自报"用时"合计 **110 017 s**（**全是 level=1**，最大单格 S22_05 11 342 s≈3.1 h，24–30 原子那几格 6–11 kh；证书入口一次 SCF 算六列，所以"只重取一列"省不下 SCF）；且这批是**多线程**跑的，固定单线程只会更贵。本轮那张单格定价探针的实测同步印证：苯-氨一个 worker 在 `T=1` 下墙钟 **35 min**、`T=8` 下 **17 min**（SCF 段跑到 799% CPU），而它只算了六列里的两列 | 随包认证面 8 格×6 列；"缺列/残件不得算通过" | 我可写，落笔要你点头 |
| **2** | **G6：带顶那个数怎么落地** | 带顶 `0.3586` 由**确定性 Voronoi** 抬起（S22_19 的 `incH=0.0000`），Hirshfeld 退 SI；即 G6 买到的是**确定性**，不是"更小的带" | 改字 | 头条比值要与发表对象同层级 | 同上 |
| **3** | **头条句改写**（"既不消除也不放大"已被逐格数据否证） | 照裁断给的措辞：影响**具有体系与构造依赖性**，逐格比值 `1.00–7.07×`、绝对增量最大 `0.1079` | 改字 | 核心不变性主张已失败，必须下调 | 同上 |
| **4** | **G2 落笔口径：三处** | ① `main.md:64` "the **two** libxc shared objects on this machine" → 实为 **5 份 / 4 版本**，且"只导出 `xc_nlc_coef`"对五份都成立（**更强**）；② `:1028-1037` 跨程序表加**就近**版本注记或一列（数据现成）；③ `:711-712` 那句 because 从句——**可照抄文本在本简报末「附」里，本轮新拟**（我先在表里写"`DECISION-G2-20261013.md` 里已有可照抄文本"是**错的**，`grep 710/711/2.12.1` 那份文档**零命中**，已撤） | 改字 | 正文每句话要有同档出处 | 同上 |
| **5** | **表号/题注制作缺陷** | 给 `md2tex.js` 补 `\caption`+`\label`，再把正文所有 `Table 1` 引用逐条改挂到稳定编号 | 0.5–1 h | 构建产物里现在**零表编号** | 我可做 |
| **6** | **提交授权** | 等 #1–#5 定稿再提；**提交只能 Windows 侧**。眼校 328 个未提交文件请用 **`git diff --text`**（`.gitattributes` 把 `evidence/**` 设成 binary，普通 `git diff` 只显示 `Bin … 0 insertions`） | — | 硬规矩二：清单在所有证据定稿后最后重生成 | **只有你** |
| **7** | **出货**（`tools/run_ship_qa.sh --yes`） | 单独授权，与 #6 不同时给 | 30–60 min | 随包测试模块预飞 **10** 个（不是 12） | **只有你** |
| **8** | **那 3 份混合编码档要不要重取** | 建议**只修生成器 + 加一道出货校验**，旧档原样保留（本仓惯例：旧档不改写，注记另存）——它们不进正文，只是内部汇总件 | 分钟级 | 出货前逐档 UTF-8 校验（雏形已是 `utf8_census.py`） | 我可做 |
| **9** | **G1 路线**（JCP vs 冲 JCTC） | 仍建议 **JCP**：#3 把"不变性"这条主张撤下后，剩的是受限数值研究结论，JCTC 的新颖度门槛更难 | — | 对口 ≠ 门槛 | **你** |
| **10** | G3 / G4 遗留 | G3 只剩改措辞 + `README:36` 改指新档；G4 已做完待你确认保留 | 改字 | — | 你点头后我做 |

## 三、我未经你点头做了什么（主动认，不等你抓）

只动了**判据代码的语义与工具**，没动正文、没动门限值、没提交、没出货、没碰集群：
`summarize_s22_full.py`（没测优先返回 rc=2）、`selftest_certification_gate.py`（+2 条负控）、
`run_selftest_certification_gate.sh`（用例数改外部声明 `EXPECT=7`）、`tools/run_w4_closeout.sh`（rc 分派文案）、
`tools/make_evidence_manifest.sh`（空数组 bug）。
**回滚点＝这 5 个文件**；`HIR_TOL=1e-3`/`PRINT_TOL=1e-4` **一个字没放宽**，四格 OVER 仍然红着。

## 附：可照抄文本（本轮新拟，**未写进 `paper/main.md`**——落笔权在你）

**(A) 头条句改写（#3；裁断给的口径，英文原句）**
> How the band responds to leaving the Becke family is system- and construction-dependent: across
> the 22 S22 cells the per-cell ratio of the all-scheme span to the in-family span is 1.00-7.07x,
> and the largest absolute increment is 0.1079 kcal/mol (S22_15).
出处：`evidence/common_grid/20261015T113349Z_s22_full_band_columns.out`（rc=0）。
⚠ 同批的 `:112930Z`/`:113106Z` 与这份都是**混合编码**那 3 份（中文表头前半 GBK 后半 UTF-8），
若要让它们进 SI，**先按 #8 重取或补注记**，否则说明文字对任何 UTF-8 工具都是坏的。

**(B) libxc 那句（#4①，替 `main.md:62-66`）**
> the five libxc shared objects on this machine (conda-forge builds 5.2.3 in the PSI4 environment,
> 6.2.2 and 7.1.2 in two probe/CP2K environments, and the 7.0.0 bundled with PySCF) export
> `xc_nlc_coef` and none of `xc_nlc_vxc`, `xc_nld_vxc`, `xc_vdwnl_kernel`, `xc_setup_kernel`, `xc_run`
出处：`evidence/recompute/20261018T120810Z_libxc_version_census.out`（rc=0，五份 `xc_version_string()` 自报）。
⚠ 措辞边界：今天这一跑探的是**六个**入口名；2026-09-29 那份"十三个入口名"的审计只覆盖当时那两份构建，
**别把两个数并成一句**。另外 PySCF 那份非 conda 安装、无 `conda-meta` 可对照 ⇒ "7.0.0" 只有库自报一条腿。

**(C) 跨程序表的就近版本注记（#4②，接在 `main.md:1037` 表后）**
> The PySCF column is not one release: it is 2.12.1 for the water dimer and 2.14.0 for the other
> seven rows (per-row `pyscf_version` in `evidence/orca_widen/cross_program_table.json`), so the
> smallest residual in the table sits on the only 2.12.1 row and this agreement is not a claim of
> cross-release identity.

**(D) `:710-712` because 从句（#4③）**
原文的问题：从句把"ORCA cross-check"列进"every other DFT number ... was produced in 2.12.1"，
而机读源显示那张跨程序表的 PySCF 一侧是 **7×2.14.0 + 1×2.12.1**（`step_h.json` 独立再证一次：`2.14.0` 七行）。
主句（"the table above quotes 2.12.1 throughout"）指 `:554` 那张 CC 表、**不矛盾，别一起改**。
> ... The table above quotes 2.12.1 throughout, because that is the release the sidecar and the
> figures were produced in; the cross-program check in section 4 is not one version but two - its
> PySCF column is 2.12.1 for the water dimer and 2.14.0 for the other seven rows - so choosing
> 2.12.1 here is a decision, and its cost is exactly the three numbers just given.
（同一处还牵出 `Table 1` 一称二指与"构建产物零表编号"，那是 #5，不在这句里解决。）

