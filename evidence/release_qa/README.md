# release QA — clean installs and out-of-tree runs

归档日期 2026-09-30。对应 `paper/software.md` §5 的 [S19]。

**被测产物**（这些运行的对象；母仓里后来的重建会换哈希）：

| 文件 | SHA-256 |
|---|---|
| `dist/nlcsplit-0.1.0-py3-none-any.whl` | `4e9efb8e4bf14de6e964dac58dff8a1430f4c40e38e7d312d6a587ff0badf197` |
| `dist/nlcsplit-0.1.0.tar.gz` | `6f8dea45d0f52896dab8b5b11ee15575b024e58762d86bf7fa7e1b33026f6ceb` |

wheel 的 4e9efb8e… 同时出现在 `20260929T170302Z_wheelclean_pyargs.out` 头部，所以
`…_FULL.out` 那一行空哈希是**记录命令的引号 bug**，不是换了文件：
`sha256sum -b $W | cut -d" " -f1` 里的引号在嵌套 bash -lc 中被吃掉。数值由本表补上，
旧日志原文不改。

| 日志 | 装法 | 范围 | 结果 |
|---|---|---|---|
| `20260929T111551Z_cleanvenv_pyargs_full.out` | 干净环境里 `pip install .`（源目录） | 全量 63 | 62 passed, 1 skipped, 1739 s |
| `20260929T111450Z/111551Z_cleanvenv_pyargs_fast.out` | 同上 | `-m "not slow"` | 42 passed, 1 skipped, 20 deselected, ~11 s |
| `20260929T170302Z_wheelclean_pyargs.out` | **wheel**，`pip3 install --no-deps --target` + `PYTHONPATH`，cwd=/tmp | `-m "not slow"` | 24 passed, 1 skipped, 18 deselected, 4.6 s |
| `20260929T170345Z_wheelclean_pyargs_FULL.out` | 同上 | 全量 43（wheel 收集数） | 42 passed, 1 skipped, 581 s |
| `20260929T105905Z_cleanvenv_pyargs.out` | 源目录安装，**含并发事故记录** | 见该文件 | `PASS_WITH_DEFECTS` |

为什么最后一条值得留着：那次跑的时候，本机另一个代理在 19:16 删掉 `build/` 并把
`pip install --force-reinstall --no-deps --no-build-isolation` **装进同一个 venv**，
还多带进去一个 `examples/hybrid_nearfield.py`。该文件把这件事连同"我 pytest 进程已在收集期
导入了所有测试模块、因此测量未被污染"的判断一起写明了。共享 venv 是本机常态，
**这条纪律由它确立**：QA 运行要用一次性 target 目录（后两条 wheel 运行就是这么做的），
别再复用 `$HOME` 下的 venv。

`pip install --target` 而不是 `python -m venv`：本机 WSL 没装 `python3.10-venv`，
`python3 -m venv` 直接失败（"apt install python3.10-venv"）。target 目录 + `PYTHONPATH`
达到同样效果，且日志里打印了 `nlcsplit.__file__` 与非源树 cwd 来证明"不在源树里跑"。
