# agent-l2 工作日志

## [2026-09-29 13:25] [agent=agent-l2] [launch] 苯-甲烷 level 2 + 全反泊松：两台机器各挂一份，互不依赖

任务是补上 `step_h` 表里唯一缺的那一行。batch5 那次在 CentOS 上是 `timeout 14400` 到点、
rc=124 被截（`logs/MANIFEST.txt` 里 `20260928T213839Z step_h_l2cp rc=124` 那行就是它），
而脚本的机器可读侧车是**跑完才合并**的，所以被截等于什么都没留下。这一轮不以"跑完"为目标，
只以"两条独立、可断线复查的计算确实挂上了"为目标。

### 两台机器的实况（启动即记录，未等结束）

| | WSL Ubuntu-22.04（笔记本 Haangyeon） | CentOS（10.8.51.23:24522，host `ubuntu`） |
|---|---|---|
| PID（python） | **1189**（launcher bash 1146，会话首进程） | **16286**（launcher bash 16264，会话首进程） |
| 起始 UTC | 2026-09-29T05:18:50Z | 2026-09-29T05:19:12Z |
| `nproc` / `OMP_NUM_THREADS` | 20 / **18** | 8 / **8** |
| 解释器 | `/usr/bin/python3`（3.10.12，系统默认，无 venv） | `/root/gamess_work/nlcsplit/venv/bin/python` |
| PySCF | **2.12.1** | **2.14.0**（与已完成五体系同版本 ⇒ **这一份才是直接可比的**） |
| 日志（stdout） | `/mnt/e/Project/GAMESS/nlcsplit/logs/20260929T051849Z_l2_benzmeth-wsl.out` | `/root/gamess_work/logs/20260929T051912Z_centos-l2_benzmeth_cp.out` |
| 启动元信息 | `/home/haangyeon/agent_l2_work/LAUNCH.txt` | `/root/gamess_work/logs/agent-l2-LAUNCH.txt` |
| 侧车落点 | `/home/haangyeon/agent_l2_work/nlcsplit/logs/step_h.json`（隔离副本） | `/root/gamess_work/nlcsplit/logs/step_h.json` |

启动命令（各写成一个小脚本，中文体系名不穿两层 shell 引号，避免编码错位）：

```bash
# WSL —— 源码副本在 ~/agent_l2_work/nlcsplit/，几何仍读仓库原文件（只读）
cd /home/haangyeon/agent_l2_work && setsid nohup \
  bash /mnt/e/Project/GAMESS/scratch/agent-l2-launch-wsl.sh \
  > /home/haangyeon/agent_l2_work/boot.out 2>&1 < /dev/null &
#   脚本内部等价于：
NCLV=2 NCPC=1 OMP_NUM_THREADS=18 PYTHONUTF8=1 LC_ALL=C.UTF-8 \
S22DIR=/mnt/e/Project/GAMESS/scratch/lit/s22 \
python3 -u nlcsplit/step_h_s22.py 苯-甲烷

# CentOS
cd /root/gamess_work && setsid nohup bash agent_l2_launch.sh \
  > /root/gamess_work/logs/agent-l2-boot.out 2>&1 < /dev/null &
#   脚本内部等价于：
NCLV=2 NCPC=1 OMP_NUM_THREADS=8 PYTHONUTF8=1 LC_ALL=C.UTF-8 \
S22DIR=/root/gamess_work/nlcsplit/s22 \
/root/gamess_work/nlcsplit/venv/bin/python -u nlcsplit/step_h_s22.py 苯-甲烷
```

**`S22DIR` 不是可选项。** 默认几何目录取 `<repo>/scratch/lit/s22`，CentOS 上没有这一层
（那里是 `/root/gamess_work/nlcsplit/s22`，batch5 的 `centos_run5.sh` 也是显式设的这个值），
照搬裸命令会直接 FileNotFoundError，而且是在印完表头之后才炸——日志里只剩一行、看着像"在跑"。

### 挂了之前先确认它在算

`setsid` 之后**另开一次连接**复查（这才是"能活过 shell 退出"的证据，不是同一次调用里的自证）：

- 两侧 `ps -o pid,sid,tty,etime,cputime` 均 `TT=?`（无控制终端），且各采样两次间隔 20 s：
  CentOS `cputime 00:27:43 → 00:28:43`、WSL `00:56:28 → 00:58:14`，CPU 时间在长；
  平均占用分别约 7.6 核与 15.5 核，与 `OMP_NUM_THREADS` 一致。
- 两侧日志均已落表头行（CentOS 87 B、WSL 94 B），`S22_10.xyz` 读到了 17 原子、片段 `[12, 5]`
  （苯 12 + 甲烷 5），启动前的 `s22_system()` 探针两台都过。
- 内存：WSL RSS 1.5 GB / 可用 29 GB；CentOS RSS 1.4 GB / 可用 22 GB。不是瓶颈。

### CentOS 上的源码替换（做了，但先看差异再看写入）

远端 `step_h_s22.py`/`partition.py`/`nlc.py`/`geomlib.py` 与本地不一致（7161/2366/6374/7794 B vs
8581/7317/6999/9191 B）。逐文件 diff 的结论是**纯增量**：`partition.atom_partition` 本体一行没动，
只多了 `partition_matrix()`/`partition_factors()`；`nlc.py` 只改注释（libxc→PySCF 原生核那句更正）；
`geomlib.py` 新增的是手工单体构造器的角度护栏（`_assert_angle`、NH3 半角坑修正），
step_h 走的是官方 xyz，`read_xyz`/`split_frags`/`s22_system`/`S22` 映射表两边完全一致；
`step_h_s22.py` 多的是逐行 provenance（level/basis/cpcorr/run_utc/pyscf_version/host）与
NaN→null 的严格 JSON。⇒ 数值口径不变，provenance 变好，所以值得推。

- 覆盖前先备份到 `/root/gamess_work/nlcsplit/_agentl2_backup_20260929T051713Z/`（本 agent 新建，未删任何东西）。
- 推送的是 LF 归一化副本，落地 md5 与本地一致：`9abac51184c0… / 75f470bcac63… / 433a9d7a7365… / 0ae3004aa9d6…`。
- 推后 `py_compile` 五个模块全过才启动。
- 本地 `nlcsplit/logs/step_h.json`、`paper/*`、各 `PROGRESS-ide-*.md` **一律没动**；WSL 那份之所以
  跑在 `~/agent_l2_work` 副本上，正是为了让它的侧车合并落到副本里，而不是覆盖仓库这份
  （现文件头 `level: 1, cpcorr: false` 与那条 `note` 会被重写，那是别人的真相源，不该由我顺手改掉）。

### 时间估计（拿 batch5 同机同档的实测外推）

batch5 在 CentOS、`OMP_NUM_THREADS=6` 下的单体系耗时：水 480 s、氨 764 s、甲烷 1093 s、
苯-水 4163 s（15 原子）、苯-氨 4610 s（16 原子，复合物网格 126592 点）。
苯-甲烷是 17 原子、复合物网格 132176 点，比苯-氨再大 4.4%，而 VV10 显式和是**平方**代价。

- CentOS（8 线程，2.14.0）：**约 70–95 分钟**，落在 06:30–06:55Z（14:30–14:55 本地）。
- WSL（18 线程，2.12.1）：核数是 CentOS 的 2.25 倍但标度不线性（SCF 段实测只吃到约 5 核），
  **约 50–95 分钟**，大概率与 CentOS 前后脚结束。
- 两边都**没有**套 `timeout`：batch5 的教训是预算截断等于零产出。要不要设上限由下一个 agent 决定。

### 采集配方（日志里出现汇总行之后跑这一条）

```bash
# CentOS（主结果，2.14.0，与五体系直接可比）
ssh -o BatchMode=yes -p 24522 root@10.8.51.23 \
  'L=/root/gamess_work/logs/20260929T051912Z_centos-l2_benzmeth_cp.out;
   grep -q "苯-甲烷" $L && grep -E "^  苯-甲烷|侧车" $L || echo "RUNNING $(ps -o etime=,cputime= -p 16286)";
   tail -3 /root/gamess_work/logs/agent-l2-LAUNCH.txt'
# 拿到行之后，把远端侧车取回来单独存档比对（别直接覆盖仓库那份）：
scp -P 24522 root@10.8.51.23:/root/gamess_work/nlcsplit/logs/step_h.json \
    scratch/step_h.centos-l2.json
```

```bash
# WSL（交叉版本核对，2.12.1；日志在仓库里，Windows 侧直接可读）
grep -E "^  苯-甲烷|汇总|侧车" /mnt/e/Project/GAMESS/nlcsplit/logs/20260929T051849Z_l2_benzmeth-wsl.out
tail -3 /home/haangyeon/agent_l2_work/LAUNCH.txt
```

判成功的标志：日志末尾出现 `  苯-甲烷       原子 17 …` 那一行**且**下一段 `LAUNCH.txt` 里
`rc=0`。只有 `rc=0` 没有行、或有行没有 `ΔE_int(反泊松)`（该列是 `-` 而不是数）都算没成。
成对项与 ΔE_NLC 应与 batch5 五体系同量级（苯-氨是 -1.328 / -1.393）；两台 PySCF 版本不同时
这两个量按理一字不差，若差出 1e-2 量级就是版本行为差异，值得单开一条记录。

两个数都到位后，`paper/main.md` 里"level-2 counterpoise for one of the eight systems
(benzene...methane) was cut off by its own wall-clock budget"那句限制就该改成六/六——
**这句留给下一位改，我不动 `paper/`。**
