# tcc (chinahpc, LSF) 作业 93285：取回归档，内容是**一条失败记录**，不是结果

取回日期：2026-10-22（宿主时钟；取回时该机 home 目录 mtime 显示其刚重启过）。
取回物只有两份，均在 `/share/BackUp/XAR/nlcc/out/`，远端修改时间 10-04 19:54：

| 文件 | 字节 | sha256（远端 = 本地，逐字符相同） |
|---|---|---|
| `93285.out` | 3732 | `d1337020cbbe9b57114ca04ca055f525fc1200c0e300b78c3d20f64c7367512f` |
| `93285.err` | 89 | `ce78c56755f7238f8d064bd1d30118e8a2d9e390084cfc56a0f99de74152c3a8` |

取回命令（只读）：

```
scp -P 10011 XAR@219.244.66.99:/share/BackUp/XAR/nlcc/out/93285.out \
                     XAR@219.244.66.99:/share/BackUp/XAR/nlcc/out/93285.err evidence/tcc/
```

## 判定：这个作业**没有产生任何 CCSD(T) 数**

- 标题行自证：`Job 93285: <nlcbenz> ... Exited`，`Started at Results reported on` 两个时间字段都是空的。
- 资源汇总自证：`Exited with exit code 1`、`CPU time : 0.04 sec.`、`Run time : 1 sec.`，
  而 `Turnaround time : 262470 sec.` —— 排队约三天，跑了一秒。
- 死因在 `.err` 里，只有一行：`/home/XAR/.lsbatch/1790852405.93285.shell: line 30: LSB_PROCESSOR_LIST: unbound variable`。
  即脚本在 `set -u` 下引用了 LSF 未导出的变量，**在进入任何计算之前**就退出。
- `.out` 里附了提交时的 `#BSUB` 段（队列 normal、8 核、48 h、`rusage[mem=16000]`），可据此复核当时的资源请求。

## 这对论文意味着什么

没有意味着什么，也不该被写成"已取回结果"：§3.2 的苯二聚体 CCSD(T) 锚来自 SNNU 侧作业
（S28 = 50945、S29 = 50980），与本作业无关；本目录**不提供**任何可引的能量值。
任务 #31 据此关账，性质是"取回并确认该作业无产出"，而不是"补上了一个数据点"。

## 租期相关的一句

该机 `out/` 目录里**只有**这一对文件，没有别的未取回产出；home 下的 `~/project` 是另一条
（ABCluster/Gaussian）工作线，与本项目无关。
