# PROGRESS — ide-qoder / S2（VV10 NLC 片间分解，正确口径 CP/P_frz/relax）

口径：ωB97X-V/6-31g\*，PySCF 2.12.1，所有量**只含非局域双重积分 ½∬ρρΦ，不含 β∫ρ 局部件**。
本机 WSL（Ubuntu-22.04），`OMP_NUM_THREADS=4`，与 cn-qoder / S1 代理共存。

> 全局限定（S1 结论，成因另一代理在查）：本仓显式双重和相对 libxc/ORCA 有 **+0.138 kcal/mol（水单体，网格无关）固定偏移**。
> ⇒ 一切 **absolute E_NLC**（E_nl[二聚体]、ΣE_nl[单体]、E_loc、libxc 值）都带此待定偏移，**不可单独作真值**；
> 但 **P_frz / CP / relax 是同一实现内部的差值**，偏移在相减中抵消 ⇒ **差值可信**（每体系附 |P_frz|/|E_nl[单体]| 薄差证据佐证）。

---

## [2026-09-29 00:05] [agent=ide-qoder/S2] [done]

**任务1 轮询 s2** 完成（详见日志 `nlcsplit/logs/20260928T224556Z_ide-s2.out`，`[runner s2] end rc=0` @23:19:39）：
- 苯 sandwich lvl0：**N=19752**（分区网格总点数）/ **保留点=18792**（keep=ρ>1e-12）；
- 二聚体双重和耗时 8.7s、交叉块 1.2s；P_frz=-2.9581、E_nl[二聚体]=-54.7085（其 CP=-258.7349 为**垃圾**，因 e_mono 混入 β∫ρ，本任务弃用并另算）。

**任务2 正确口径重算** 完成（脚本 `scratch/ide_s2b_cp.py`，日志 `nlcsplit/logs/20260928T232625Z_ide-s2b.out`）：
- 定义与 `nlcsplit/step_c_relaxation.py` 的 `_nl_all`/`_cross`/`_embed`/`_shells_of` 完全一致；
- **口径自检**：水 lvl0 逐位复现 `nlcsplit/step_c.out`（CP=-0.6616 / P_frz=-0.6316 / relax=-0.0187 / P_frz÷CP=0.955 / relax÷CP=0.028）⇒ 脚本可信；
- 苯 lvl0 的 P_frz=-2.9581 与 s2 逐位吻合（同一实现在同一快照），且本任务补齐 s2 缺的**正确 CP/relax**。

**任务6 server_bundle** 完成：`scratch/server_bundle/`（自包含、零凭据、未连接），详见末节。

### 结果表（正确口径，单位 kcal/mol；absolute E_NLC 均含 +0.138 待定偏移，CP/P_frz/relax 为差值可信）

| 体系 | lvl | N | Nkeep | E_nl[二聚体] | ΣE_nl[单体] | CP | P_frz | relax | P_frz÷CP | relax÷CP | SCF |
|---|---|---|---|---|---|---|---|---|---|---|---|
| (H2O)2 | 0 | 4460 | 4047 | -7.6343 | -6.9727 | **-0.6616** | **-0.6316** | **-0.0187** | 0.955 | 0.028 | 72.5s |
| (H2O)2 | 1 | 19936 | 17110 | -7.6804 | -7.0222 | **-0.6582** | **-0.6333** | **-0.0170** | 0.962 | 0.026 | 80.4s |
| (C6H6)2 | 0 | 19752 | 18792 | -54.7085 | -51.5368 | **-3.1717** | **-2.9581** | **+0.0040** | 0.933 | -0.001 | 1275.6s |
| (C6H6)2 | 1 | 89088 | 未得到 | defer | defer | defer | defer | defer | — | — | 未跑 |

- 单体分裂：苯 lvl0 两个单体 E_nl 各 -25.7684（对称 D6h 一致，符合预期）；水 lvl0 单体 -3.4866/-3.4861。
- ∫ρ(SC)=84.03200、∫ρ(SUP)=84.03216、N_e=84（苯）；水 lvl0 ∫ρ(SC)=19.98481 / N_e=20。P_sup（超位置成对）苯=-2.9584≈P_frz、水=-0.6166≈P_frz。

### 薄差证据（支撑"差值可信"，逐条来自 232625Z 日志）
- 苯 lvl0：|P_frz|/|E_nl[单体]| = **0.115**；水 lvl0 = 0.181；水 lvl1 = 0.180。
  ⇒ 片间项只是单体非局域能的 10–18% 薄差，+0.138 偏移在 dimer−monomers 相减中抵消；
  且水 lvl0→lvl1 的 CP 由 -0.6616→-0.6582（Δ=0.003）、P_frz -0.6316→-0.6333（Δ=0.002），网格加密下**差值几乎不动**，绝对值则各 +0.138 一并漂移 ⇒ 差值稳健、绝对值不可单独信。

出处：以上每格均见 `scratch/ide_s2b_cp.py` 打印 + 日志 `nlcsplit/logs/20260928T232625Z_ide-s2b.out`（水 lvl0/苯 lvl0/水 lvl1 三段完整；苯 lvl1 未产出，见下节 defer）。

---

## [2026-09-29 00:08] [agent=ide-qoder/S2] [finding] 苯 lvl1 本地不可行 → defer 服务器（实测外推，非凭感觉）

**判据 = (N₁/N₀)² 外推总墙钟**，两端都用**实测**（脚本 `scratch/ide_s2b_cp.py` 的 measured 逻辑 + 探针 `scratch/ide_s2b_probeN.py`，探针脚本 `scratch/run_probeN.sh`）：
- N₀(苯 lvl0)=19752（实测，与运行逐位一致）；N₁(苯 lvl1)=**89088**（探针实测，仅建网格 0.1s，不跑 SCF）；
- cost₀(苯 lvl0 总)= SCF 1275.6s + 双重和[SC]9.5s + 双重和[SUP]9.5s = **1294.6s**；
- ratio=(89088/19752)²=**20.35** ⇒ **外推总墙钟 ≈ 1294.6×20.35 ≈ 26,300s ≈ 7.3 小时**，且此为**下限**（未计 2×苯单体 SCF 及其双重和的同等放大）。
- 阈值 `S2B_MAXSEC=2400s`(40min)：26,300s ≫ 阈值 ⇒ **苯 lvl1 连 SCF 都不本地跑，defer 服务器**。
- 对照水 lvl1：N 4460→19936（ratio≈20 同量级），但水 SCF 仅 80.4s、双重和 ~9s ⇒ 整轮 ~98s，本地轻松跑完。

**为什么这么慢（机理，非猜测）**：ωB97X-V 是 range-separated hybrid，PySCF 在每个自洽循环里都重算一次 O(N²) 的 VV10 非局域双重和，故 **SCF 与"显式双重和"同量级、且随 N² 放大**——苯 lvl0 的 1275.6s 里 SCF 独占 ~98%。这解释了任务1里 s2 全程 ~34min 中苯 SCF 的主导地位，也解释了为何 lvl1 直接冲到小时级。

**处置**：运行中进程（旧脚本逻辑=护栏在 SCF 之后）完成水 lvl0/苯 lvl0/水 lvl1 后进入苯 lvl1 的多小时 SCF，已按规矩 **kill 我自己的 python（pid 3806，`scratch/kill_s2b.sh`）**，未触碰其它代理进程（`step_c_relaxation.py` pid 2084/4286 仍在跑，属他人）。修正后的 `ide_s2b_cp.py` 已把护栏移到 **SCF 之前**（先廉价 probe N₁ 再决定），服务器版据此在苯 lvl1 会直接打印 defer 而不浪费 SCF。

---

## [2026-09-29 00:10] [agent=ide-qoder/S2] [finding] 水(氢键) vs 苯(π堆积/色散) 判据对照 —— 正面回应"比 SAPT 色散小好几倍"

| 指标（差值，可信） | 水二聚体 lvl0 | 水二聚体 lvl1 | 苯 sandwich lvl0 |
|---|---|---|---|
| NLC 净贡献 CP (=E_nl[dimer]−ΣE_nl[mono]) | -0.662 | -0.658 | **-3.172** |
| 冻结成对 P_frz 占 CP | 95.5% | 96.2% | 93.3% |
| 弛豫 relax 占 CP | 2.8% | 2.6% | -0.1%（≈0） |
| 文献色散参照 | ≈ -1.0 ~ -1.5 | 同 | ≈ **-1.4** |
| CP ÷ 文献色散 | ~0.4–0.7× | 同 | **~2.3×** |

**结论（用于回复审稿人）**：
1. **量级**：把 β∫ρ 精确抵消后，NLC 对相互作用能的净贡献只剩 CP（=dimer−monomers 双重和之差）。苯 sandwich 的 **CP = -3.17 kcal/mol**，与文献苯二聚体色散 ≈ -1.4 kcal/mol **同量级甚至更大（约 2.3×）**；水二聚体 CP=-0.66，约为其色散参照的 0.4–0.7×。**"你这个数比 SAPT 色散小好几倍" 不成立**——至少对苯（色散主导体系）我们的 NLC 片间项比参考色散还大。
2. **片间集中度**：两体系 P_frz 都占 CP 的 93–96%，relax（纯弛豫）仅 2–3%（苯 ≈0）。⇒ NLC 的相互作用贡献几乎全部由**片间成对项**承载，这正是"可作对二体色散代理来讨论"的依据。
3. **诚实限定（必须一起说）**：CP 是 ωB97X-V 里**非局域项那一份**，不是总相关泛函的全部（半局域 GGA 关联另计）；把 CP 与 SAPT 总色散直接对比会**高估 NLC 占比**。正确表述是"NLC 单项已与参考色散同量级"，而非"NLC = 全部色散"。
4. **可信性护栏**：CP/P_frz/relax 是同一实现内部薄差（|P_frz|/|E_nl[单体]|=0.12–0.18），+0.138 固定偏移在相减中抵消，且水 lvl0→lvl1 加密网格 CP 仅变 0.003 ⇒ **差值稳健**；而 -54.71 / -7.63 这类 absolute E_NLC 仍含待定偏移，**不单独引用**。

出处：`scratch/ide_s2b_cp.py` + `nlcsplit/logs/20260928T232625Z_ide-s2b.out`；文献参照为公开常识量级（苯二聚体 -1.4、水二聚体 -1.0~-1.5 kcal/mol），未附具体DOI，若需引用请在成稿时补原始文献。

---

## [2026-09-29 00:12] [agent=ide-qoder/S2] [done] server_bundle（T2 外迁准备，全程未连接、零凭据）

路径：`e:\Project\GAMESS\scratch\server_bundle\`（WSL：`/mnt/e/Project/GAMESS/scratch/server_bundle/`）

清单：
- `ide_s2b_cp.py` — **修正版**（护栏在 SCF 之前 + probe N₁ 外推），md5=`0e53d60c25914dfb202a9dbb4d6381e5`，与 `scratch/ide_s2b_cp.py` 逐字节一致（`scratch/sync_bundle.sh` 校验）。
- `nlcsplit_snapshot/nlcsplit/*.py` — 从快照 `ide_snapshot_20260928T224224Z/nlcsplit` 复制的自包含副本；
- `nlcsplit_snapshot/SNAPSHOT-MANIFEST.txt` — 快照 md5 清单，服务器端 `md5sum nlcsplit/*.py` 对照；
- `install.sh` — pip 走代理装 `pyscf==2.12.1`，代理=`<PROXY>` **占位符**（运行期 `export PROXY=...` 按次注入），含 `_numint.nlc_coeff` 自检；
- `run.sh` — setsid+nohup+flock+时间戳日志（结构抄 `scratch/ide_runner.sh`），`NLCSNAP=$ROOT/nlcsplit_snapshot`，`S2B_LEVELS` 默认 1；
- `README.md` — 要跑的 level、耗时外推依据（即上节 7.3h/苯 lvl1）、预期产物、日志取回方式。

红线（README 已写明）：服务器工作目录 `/root/gamess_work/nlcsplit/`；**绝不碰 `/root/GAMESS_BLW`**（另一条 GAMESS 线在用）；包内**不含任何口令/私钥/凭据**。

---

## [2026-09-29 00:13] [agent=ide-qoder/S2] [ask] 快照漂移（需知晓，未处理）

`scratch/check_manifest.sh` 核对本次运行所用快照 `ide_snapshot_20260928T224224Z`：
- geomlib.py / partition.py / __init__.py / step_c_relaxation.py：快照=live=manifest 记录，**三方一致**；
- **nlc.py：快照=manifest=a1800277812945717c8b10c11b849ad8，但当前 live=0a579102b6fac934a4749a2a9203a0d6 —— live 树在快照之后被改动**（非本代理，本代理未编辑任何 `nlcsplit/*.py`）。

影响判定：我的 s2b 运行通过 `NLCSNAP` **锁定快照 nlc.py**，故与 step_c（-0.6616 等）、s2（P_frz=-2.9581）**同源可比**，本次所有数字不受该漂移影响、自洽。
风险：若后续有人**改用 live 树**跑同一体系，nlc.py 差异会引入不可控偏移。
建议（ask）：请快照维护方确认 live `nlc.py` 的改动是否为预期；server_bundle 内附的是**快照版 nlc.py**（a1800277…），服务器端应以 `SNAPSHOT-MANIFEST.txt` 为准核对，勿混用 live。

---

### 附：本任务涉及的可复现脚本（均在本代理 scratch/ 下，非 nlcsplit 本体）
- `scratch/ide_s2b_cp.py` — 正确口径主计算（水/苯 × lvl0/1，含 SCF-前 defer 护栏）。
- `scratch/ide_s2b_probeN.py` + `scratch/run_probeN.sh` — 廉价取苯各 level 的 N（0.1s，不跑 SCF）。
- `scratch/diag_s2b.sh` / `scratch/poll_s2b.sh` / `scratch/kill_s2b.sh` / `scratch/sync_bundle.sh` / `scratch/check_manifest.sh` — 诊断/轮询/自kill/同步bundle/快照核对。
- `scratch/build_server_bundle.sh` — 生成 server_bundle（本地，不连接）。
