# 交接文档 —— GAMESS / nlcsplit 投 JCTC（接收方：豆包 Doubao）

> 前一 Agent（Qoder/Zcode）交接。作者已明确说"交给豆包去投稿"。本文件自包含；
> 关键记忆文件已复制到 `handoff_doubao/`，原始路径见下。打包 ZIP 见 `handoff_doubao/DOUBAO_HANDOFF_JCTC.zip`。
> **红线先说：🚫 密码不入库/不复述；🚫 Submit 必须作者当次明确同意；🚫 不擅自 push/commit。**

## 一、当前状态（一句话）
稿件已定稿可投（main 37 页 PDF + 数学化 DOCX + SI **22 页**，闸门全干净）；ACS 密码已于 2026-11-12 重置（新密码作者掌握，不入库），
投稿改由千问桌面端负责；**当前权威检查单为 `paper/notes/PRE-SUBMISSION-CHECK-20261112.md`**（本件与 1029 检查单的 SI 页数/TOC 描述已过时，见下）。

## 二、你必须读的文件（按优先级）
1. 本文件 `E:\Project\GAMESS\DOUBAO_HANDOFF_JCTC.md`
2. `E:\Project\GAMESS\paper\notes\SUBMISSION-CHECKLIST-20261029.md`（上传件/表单字段/只有作者能做的三步）
3. 记忆（原始路径，副本在 handoff_doubao/）：
   - `C:\Users\Administrator\.qoder-cn\projects\E--Project-GAMESS\memory\project-publishability-constraint.md`
   - `C:\Users\Administrator\.qoder-cn\projects\E--Project-GAMESS\memory\project-nlc-decomposition-line.md`
   - `C:\Users\Administrator\.qoder\projects\E--Project-GAMESS\memory\reference-acs-paragon-submission.md`
   - `C:\Users\Administrator\.qoder\projects\E--Project-GAMESS\memory\project-nlcsplit-software-into-si-20261028.md`
4. `E:\Project\GAMESS\paper\main.md`（正文源；标题/摘要/作者/ORCID 都在里面）

## 三、已完成的事
| 环节 | 状态 | 备注 |
|---|---|---|
| 科学审计/外审 | ✅ | Opus 第四轮 ACCEPT；苯二聚体"稳定排序"假主张已撤 |
| 稿件构建 | ✅ | main 37 页 / SI 22 页，0 LaTeX 错 0 overfull；DOCX 已数学化；**当前 PDF 无 TOC 图**（10-29 已移除，如表单要求需另备） |
| 软件文处置 | ✅ | 不单独投 JOSS，并入 JCTC 的 SI（作者 10-28 定） |
| 仓库发布 | ✅ | `Haangyeon/nlcsplit` 已公开强推 |
| 数字/路径闸门 | ✅ | claim_gate 0 条；MANIFEST 新鲜；git 工作区干净 |
| 参考文献核验 | ✅ | 92/92 Crossref 逐条（DOI/标题/年份/卷 + 作者序列/页码，2026-11-11 补核）；修正 takatani2010s22/altun2018dlpno 两条人名，PDF/DOCX 已同步；档案在 `evidence/bib_provenance/` |
| ORCID | ✅ | 一作 0009-0006-3366-6054；二作 0000-0001-5685-2403（均一手核过） |
| ACS 注册 | ✅ 账号已存在 | 邮箱 haangyeon@snnu.edu.cn 已注册（旧会话完成） |
| ACS 登录 | ⛔ 待作者 | 旧密码失效；重置邮件已发 2026-11-08，等作者设新密码 |
| Figure 3 版式 | ⛔ 待作者选 | 对比图 `scratch/fig3_layout_compare.png`（A=2×2+key / B=3×1 / C=3连排） |

## 四、待做的事（按优先级）
| 优先级 | 事项 | 详情 |
|---|---|---|
| 1 | 作者重置密码并登录 | 点重置邮件→设新密码→登录 publish.acs.org；密码只作者掌握 |
| 2 | 定 Figure 3 版式 | 作者选 A/B/C 后重出图并重建 PDF/DOCX，再上传 |
| 3 | 上传稿件 | Manuscript File 用 **DOCX**（ACS 拒 PDF）；SI 用 PDF；Cover Letter 另备 |
| 4 | 填表单 | 标题/摘要/作者/ORCID/单位照抄 checklist §3；建议审稿人由作者定 |
| 5 | Submit | **作者当次明确同意后才点**；豆包可代填但 Submit 需作者授权 |

## 五、账号/连接信息
- 投稿入口：**ACS Publishing Center（ChronosHub）** `https://publish.acs.org/app/home`。
  旧 `acs.manuscriptcentral.com/acs-jctc` 与 `acsparagonplus.acs.org` 已废/302，别试。
- 账号邮箱：`haangyeon@snnu.edu.cn`（已注册）。ACS ID 用户名未知（可试邮箱或 haangyeon）。
- 密码：**不在此文档、不入库**。旧会话密码已失效；重置邮件已发。作者设新密码后自行登录。
- 提醒：交接完成后建议作者改一次密码（旧密码曾在会话明文出现）。
- 集群（如需重算）：`ssh snnu`（key auth）；tcc `XAR@219.244.66.99:10011`。遵守 snnu-hpc-safety。

## 六、关键文件路径（绝对路径）
| 文件 | 用途 |
|---|---|
| `E:\Project\GAMESS\paper\VV10-pair-attribution.docx` | 正文上传件（DOCX，ACS 接受） |
| `E:\Project\GAMESS\paper\VV10-pair-attribution.pdf` | 正文 PDF（37 页，供作者目视/cover 用） |
| `E:\Project\GAMESS\paper\VV10-pair-attribution-SI.pdf` | SI 上传件（22 页） |
| `E:\Project\GAMESS\paper\main.md` / `main.tex` / `references.bib` | 正文源/可编辑稿 |
| `E:\Project\GAMESS\paper\notes\SUBMISSION-CHECKLIST-20261029.md` | 上传/表单/作者三步 |
| `E:\Project\GAMESS\scratch\fig3_layout_compare.png` | Figure 3 版式 A/B/C 对比 |
| `E:\Project\GAMESS\figs\fig4a_small_dimer_ladders.png` | 现行 Figure 3（3 连排） |

## 七、红线（绝对不能做）
- 🚫 密码/2FA/PAT 不写进任何文件、记忆、ZIP、对话；不编造真人邮箱/ORCID。
- 🚫 Submit 必须作者当次明确同意；不代按、不自动提交。
- 🚫 不擅自 git push/commit/转 public（仓库已公开，勿再动）。
- 🚫 不把 Hirshfeld 列请回正文；不报未测量的数；不重加已撤的"稳定排序"主张。
- 🚫 不在登录节点跑重计算；集群先 squeue 预检。

## 八、踩坑记录
- ACS 登录 SPA 在应用内浏览器回 `?code=1000/1001` 空白 ⇒ 用**桌面 Chrome**（作者已登录的窗口）操作。
- Manuscript File 只收 DOC/DOCX/ZIP，**PDF 被拒**；Cover Letter 收 PDF/DOCX/RTF/TXT。
- 旧密码"末尾带点"（Xar041816. 形式）已失效，别反复试（防锁号）；走重置邮件。
- Figure 3 三連排显瘦窄；作者要接近正方形、全文风格统一；A/B/C 见对比图，未定前不要覆盖上传件。
- 写 tex/CSV 禁用 bash heredoc 内嵌 LaTeX 的 Python 串（`\a`→BEL 控制字符）；用 Write 写 .py 再跑。

## 验证清单（接收方逐项打勾）
- [ ] 读完本文件全部内容
- [ ] 读了第二节列出的记忆文件与 checklist
- [ ] 能复述当前状态（稿件就绪/等作者登录/图3待定）
- [ ] 知道下一步（作者重置登录→定图3→上传DOCX+SI→填表→作者授权Submit）
- [ ] 知道红线（密码不入库/Submit需作者/不擅自push）
- [ ] 向用户报告"接手完毕，准备执行 {下一步}"