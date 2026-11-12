# JCTC 投稿执行清单（2026-10-29 制）

> 本清单只列"到投稿按钮为止"的动作与已经核过的事实。**Submit 必须作者本人点**，
> 我不代按、也不代登录 ACS Paragon Plus。

> ** dated correction 2026-11-12（Qoder 复核）**：本件两处已过时，勿照引用——
> ① SI 现为 **22 页**（11-12 修孤页，原 23）；② **当前 PDF 无 TOC 图**（10-29 提交 5b86961 已有意移除，
> 下表"TOC graphic 排在正文最后"不再成立；如 ACS 表单要求需另备）。
> 当前权威检查单为 `PRE-SUBMISSION-CHECK-20261112.md`。

## §1 已经核过、不需要再查的合规项

| 项 | 实测 | 依据 |
|---|---|---|
| 稿件类型 | **Article**（不是 Letter）| `paper/notes/raw/jctc_author_guidelines_20261024.txt:11-16`：4 页 / 16 页双倍行距 / 75 词摘要三条上限**只属于 Letters** |
| 页数 | 无上限；当前正文 37 页 | 同上，Article 段未设页数限制 |
| 标题 | 11 词（建议 ≤12）| `main.md:1` |
| 摘要 | 4 句（要求 3–4 句）、277 词 | 脚本计数；期刊近 50 篇样本中位 172 词、区间 15–291 |
| 参考文献 | 92 条，正文引用 88 条 | md2tex 审计；期刊样本中位 84 条 |
| TOC graphic | 3.25 × 1.75 in，排在正文最后 | md2tex 自动排出 |

## §2 上传什么

1. **正文**：`paper/VV10-pair-attribution.pdf`（37 页，0 LaTeX 错、0 overfull）
2. **Supporting Information**：`paper/VV10-pair-attribution-SI.pdf`（23 页；Table S1 出处表 / S2 满 22 体系 /
   S3 十五道出货闸门 + 软件附录）
3. （若系统要求可编辑稿）`paper/main.tex` + `paper/references.bib`；正文由 `tools/md2tex.js` 从
   `paper/main.md` 生成，两边同源。

## §3 表单字段（照抄即可）

- **Title**：Pair Attribution of the VV10 Nonlocal-Correlation Term and Its Grid-Partition Dependence
- **Abstract**：`paper/main.md` 的 `## Abstract` 段（4 句）
- **Corresponding author**：Angran Xia，`haangyeon@snnu.edu.cn`，ORCID `0009-0006-3366-6054`
- **Co-author**：Changwei Wang，`snnu.changweiwang@snnu.edu.cn`，ORCID `0000-0001-5685-2403`
- **Suggested reviewers**：作者决定（我不代填）
- **Cover letter**：待起草（可在你回来前由我出终稿，但发送/粘贴由你执行）

## §4 只有作者能做的三步

1. 登录 ACS Paragon Plus（账号密码只有你有）
2. 逐项核对 §2 的上传件与 §3 的字段
3. 点 **Submit**

## §5 当前阻塞项（2026-10-29 实测）

| 阻塞 | 现状 | 解除办法 |
|---|---|---|
| GitHub 发布仓库 | 仓内无 remote、`gh` 未安装、10-01 用的一次性 PAT 已按纪律删除 | 把 fine-grained PAT 写到 `E:\tmp\nlcsplit_pat.tmp`（脚本约定的位置），我跑 `publish_github.js --push` + 转 public |
| 出货 QA 流水线 | WSL 的 setuptools 是 **59.6.0**，导出工具要求 ≥64（否则会把包名读成 UNKNOWN-0.0.0） | 需授权在 WSL 执行 `python3 -m pip install --user -U "setuptools>=64"`；未授权前我不动你的工具链 |
| 投稿本身 | 需要 ACS 账号 | 你本人操作，或明确授权并给出登录方式（不建议） |
