# 外部裁断登记 2026-10-21（referee MCP，一发，medium 档）

- **提问方约束**：作者 2026-10-21 改令"你自己盯着推进，拿不定的时候外部裁决，我比较忙。批准你的操作"。
- **实际应答模型**：`claude-sonnet-5`（返回体自带 `model` 字段）。
  ⚠ 我先前向作者报过"选了 medium 档模型"并据此发问，那是**读了一份配置文件猜的**；
  这里的模型名是返回体印的，不是我再猜的。要换档得看 referee 服务进程的 `REFEREE_CONFIG`，不是 `~/.codex/referee-mcp/referee.json`。
- **usage**：prompt 2353 / completion 1079 / total 3432（cached 69, cache-write 89）。
- **verdict：`REVISE`**。

## 它给的排序（按"每 CPU 小时能换多少判级"）

1. **(D) 稿件口径与编号**——零算力，但"任何期刊都会挡"。
2. **(B) 一次能 Discriminate 的化学应用**——收益最高但**未验证**，且它明说"选错的应用比没有更糟"。
3. **(A) 补齐网格收敛**——它判定"确认而非发现"，**不作为投稿阻塞项**。
4. **(C) 把 Hirshfeld 列做成可复现**——它认定为**重新定义**（30.6 CPU-h、权重改 3.31e-1），
   结论是"**写进 SI 当已知限制，不要重算**"。这条直接回答了我挂了多轮的 G5/#54 之一。

它同时说：**JCTC 在没有 (B) 成功的前提下不可达**，现状按 JCP/PCCP 投。

## 我这一轮据此做了什么（全部零算力）

`tools/md2tex.js` 原来只发 `\begin{table}/\centering/…/\end{table}`，**不发 `\caption` 也不发 `\label`**
⇒ 全五张表在 PDF 里没有编号，而正文有 15 处写 "Table 1"。三处改动：

1. **表题注与编号**：表块后可跟一行 `**Table N.** 题注`，转成 `\caption{...}\label{tab:N}`；
   没有题注时**不阻塞**但在 audit 里打印 `FAIL: 5 float(s) have no number to cite`。
   加这道改动的同一轮，我先证明了它对现状是惰性的：**没有任何题注时 main.tex 与改前逐字节相同**（`cmp`）。
2. **新闸门 `E-TABLE-REF-UNRESOLVED`**：正文里 `Table N` 若没有对应的 `\label{tab:N}` 就拒绝出稿。
3. **新闸门 `E-APPENDIX-ROWS-LOST`**：出处附表"源文件里 33 行"对"排出的 tex 里几行"。
   **这条抓出一个真损失**：`main.md` 里 S22 那一行的备注被写成 12 行独立段落，把 markdown 表格截断，
   ⇒ **S23、S24、S25、S26、S27、S28、S29、S30、S31、S32、S33 共 11 行从未进过 `main.tex`**，
   而既有审计线"appendix rows never cited: none"一直是绿的——因为它比的是 **markdown** 与正文，从没问"有没有进产物"。
   修法：把两处备注折回各自行内；折回后审计第一次去校验那两行里的裸文件名，
   查出 `hetero.py` / `mc_tighten.py` 少写目录 ⇒ 已补成 `evidence/attribution_referee/…`（两个文件确实存在，逐个 stat 过）。

**结果**：`sh tools/build_pdf.sh main` ⇒ 32 页、`latex errors: 0`、`paper/main.aux` 里
`newlabel{tab:1}` 到 `tab:5` 五条齐全（改之前是 0 条），出处附表 33 行全部进产物，
md2tex `failed checks: 0`。

## 我没有采纳它的一句话

它给的"最强可辩护主张"里写着 "**with certified numerical reproducibility**"。
**这句现在不能照抄**：本仓已实测 Hirshfeld 那一列跨 BLAS 线程数不可复现（权重差到 6.43e-1，
同格 `OMP=4` 证书 `REFUSED`、`OMP=1` 才 `DONE`）。要么把这句话的作用域收到"家族内四方案"，
要么等 (C) 有结论。**裁断给的句子也是主张，不是引文。**

## 一处我自己的操作错误（记在这里免得下次再犯）

我先用 `node tools/claim_gate.js` 空参数跑了一次"喂假数看它响不响"的探针，它没报——
我据此几乎要写下"闸门有洞"。实际是**我调错了模式**：无参数走的是 Stop 钩子模式（读 stdin），
真模式是 `--dump <文件>` / `--stop-count`。用对模式后：干净稿 0 条，喂进 0.91371 就**恰好报 1 条并指到行号**。
⇒ "闸门没输出"和"闸门通过"是两件事；先确认自己被调用的那条分支真的在检查。
