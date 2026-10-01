# release QA — clean installs and out-of-tree runs

归档日期 2026-09-30（同日补了三份：见"闸门代码随包发布之后"一节）。
对应 `paper/software.md` §5 的 [S19]。

**被测产物**（这些运行的对象；母仓里后来的重建会换哈希）：

| 文件 | SHA-256 |
|---|---|
| `dist/nlcsplit-0.1.0-py3-none-any.whl` | `4e9efb8e4bf14de6e964dac58dff8a1430f4c40e38e7d312d6a587ff0badf197` |
| `dist/nlcsplit-0.1.0.tar.gz` | `6f8dea45d0f52896dab8b5b11ee15575b024e58762d86bf7fa7e1b33026f6ceb` |
| 同上，2026-09-30 重建 | `4dc33eaf281b83a842fed09ccf14605119241c5e55901439f1f9d75aad6b7644` |

哈希会变而**打包字节可以完全相同**：zip 存的是 mtime。所以"随包成员未变"要按成员级证据判，
不能只看容器哈希 —— 这也是 `…_reexport.out` 重跑一遍的理由。

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
| `20260929T212357Z_wheelclean_reexport.out` | 同上，但对 **2026-09-30 重建的 wheel**（`4dc33eaf…`） | 全量 43 | 42 passed, 1 skipped, 406.75 s |
| `20260929T212552Z_gate_selftest.out` | `tools/audit_no_gamess.js` 自己 | `--selftest` 判据 + 一次真装真扫 | 5/5（当时）；装出来 45 个文件，具名豁免 2 条，**违规 1 条 → rc=1**。那一条就是下面第 4 行的东西 |
| `20260929T213552Z_no_gamess_scan_after_allow.out` | 同上，加了第 2 条具名规则之后 | 同一次真装真扫 | 7/7；具名豁免 3 条，违规 0 条，冲突信号 0 条，rc=0 |
| `20260929T213318Z_srcdir_install_fileset.out` | `pip install .`（**母仓源码目录**）与 wheel 的成员对照 | 两边各有多少 `.py` | 源码树装出 37，wheel 只有 31 —— 差集就是六个刻意不发布的内部模块 |
| `gate_selftest_20260930.txt` | 十二条闸门 + 各自的反证 | 命中数、豁免账、自测输出 | 全 0 命中；反证全部按预期响 |
| `published_tree_rerun_20260930.txt` | **发布树自己**：整份复制到新目录，跑它带着的那份导出脚本，连跑两次 | 产出是否不动点、少掉哪些检查 | 两次都 exit 0，两次产出只差导出时间戳；少掉的检查逐条打在 stderr |
| `20260930T181000Z_wheel_pyargs_44_firstrun.out` | 44 收集数的 wheel（`d175c7b8…`），`--target` 树外 | 全量 44 | 43 passed, 1 skipped, **655.52 s**。这是"重打之后必须在树外再跑一次"那条规矩落到实处的第一份 |
| `20260930T181923Z_wheel_pyargs_44.out` | 同上家族的第二次独立跑（`d123d1c8…`，36 成员，哈希写在自己日志里） | 全量 44 | 43 passed, 1 skipped, **519.36 s**。两份跑的收集数相同、容器哈希不同——正是"每次导出都重打 wheel，哈希会变而打包字节可以完全不动" |
| `publish_record_20260930.txt` | 公开仓那一侧的建立记录（远端、分支、blob 对账） | 121 ↔ 121 | 远端 `<OPERATOR>/nlcsplit`（private）建立，main 的 121 个 blob 与导出树逐个 SHA 相同；**可见性翻转与 `repository-code` 仍归作者** |
| `20260930T202235Z_suite65_full_and_counts.out` | **母仓工作树**（不是安装物），`PYTHONPATH=. pytest -q` | 全量 65 = not-slow 45 + slow 20，三份收集数都在这份里 | **65 passed，无跳过，710.73 s，EXIT=0**；抬头带 python/pyscf/numpy/scipy 版本与跑时的 `git status` |
| `20260930T233800Z_suite69_full.out` | **母仓工作树**，`PYTHONPATH=. pytest -q` | 全量 **69 = 49 not-slow + 20 slow**，无跳过 | **69 passed, 380.52 s, EXIT=0**。与 65 项那次（710.73 s）同一台机器、同样设置、新增测试合计 0.28 s ⇒ 1.87 倍差是负载不是内容，两个数都不能当"这个套件的用时"。这份是作者追问"能砍吗"之后实跑出来的，取代了下面那份 carry-over |
| `20260930T230121Z_suite69_fast_and_diffsurface.out` | **母仓工作树**（不是安装物） | 69 = 49 not-slow + 20 slow，但只跑了 49 项 | **49 passed, 20 deselected in 26.13 s** ＋新模块 4 项 0.28 s 通过。当时那 20 项按"逐文件 diff 只多出 `step_m_ccsdt.py` 与新测试"记为 carry-over；**文件末尾已附 2026-09-30T23:38Z 补记**：全量已实跑通过，本文件只作"何时 carry-over 才算合法"的样例保留 |
| `20260930T231147Z_wheel_pyargs_49_member38_fast.out` | **再一次重建的 wheel**（`55033716…`，38 成员、7 个测试模块），同上装法 | 收集 49 = 31 not-slow + 18 slow | **30 passed, 1 skipped, 18 deselected in 25.72 s**。18 项 slow **没重跑**，这是明说的 carry-over：那 8 个测试文件与它们 import 的库模块，与 9 分钟前整跑过的 37 成员 wheel 逐字节相同，`git diff --name-only afdefba HEAD -- nlcsplit/` 只列得出 `step_m_ccsdt.py` |
| `20260930T205444Z_wheel_pyargs_45.out` | **重建后的 wheel**（`149e727b…`，36 成员），同样 `--target` + `PYTHONPATH`，cwd 在解包目录里 | 全量 45（= 27 not-slow + 18 slow），这是本目录里收集数最大的一份 | **44 passed, 1 skipped, 322.21 s**；跳过的是 `test_geometry.py` 那条设计内的 S22 取回项。**注意**这一跑没设 `OMP_NUM_THREADS=2`（前两份都设了），所以 322 s 与 406–656 s 不可并池比较，只有计数可比 |
| `20260930T220142Z_wheel_pyargs_45_member37.out` | **再重建一次的 wheel**（`7e7f9d71…`，37 成员——多出来的只有 `step_m_ccsdt.py`，8 个测试文件逐位相同），同上装法 | 仍是全量 45 | **44 passed, 1 skipped, 504.67 s**。与上一份 1.57 倍的墙钟差发生在同一台机器、同样没设线程变量、测试模块逐位相同的两个 wheel 上，两份日志里都没有可指认的原因 ⇒ 这就是"墙钟只按各自日志引、绝不归一"的实证，可比的是计数不是时间 |

`20260929T213318Z` 那份是本目录里唯一一份**判语指向别处**的证据：它不证明任何数值主张，
它证明的是"装源码 ≠ 装发布物"这个前提曾经是假的，而闸门 V 现在看住它。

## 闸门代码随包发布之后发生的事（2026-09-30）

把 `tools/make_public_repo.js` 放进发布包，第一次运行就把它自己的判据当成了泄漏源：
`gateB_exempt_ledger` 打了 54 条，逐条读下来全是内网 IP、集群端口、账号名、工作目录——
"发布卫生检查"公开之后会把它要抓的东西一起公开。那十条点名判据连同反证毒样本一起搬进
`tools/intranet_patterns.private.js`（不随包发布，在导出报告的 excluded_by_design 里具名）。
公开副本的闸门 B 只剩 4 条形状类判据，并且**每次运行都打印这件事**。

拿发布树本身跑发布脚本，还实测出两个洞：`RELOCATED` 的两个改名源在重跑时 ENOENT，
以及 get_s22.sh 的代理脱敏不幂等（注释尾巴叠了两遍）。两者都修了，
并且 selftest 现在跑两遍验不动点（`scrubFixedPoint`）。
`tools/audit_no_gamess.js --selftest` 里有一条专门验"同一个文件里的非免责句不放行"。

另有一份 **`evidence/internal_only/release_qa_incident_20260929T105905Z.out`**：同一件事的
第一次尝试，判语 `PASS_WITH_DEFECTS`。它**不随发布包出**，因为它把一条 grep 命令原样抄在
日志里，而那行命令里带着集群内网 IP 和账号串——发布闸门 B 在脱敏后的副本上仍然命中它，
于是我们把它留在仓内而不是改写一份归档 stdout 的历史。留着的理由写在它自己身上：

那次跑的时候，本机另一个代理在 19:16 删掉 `build/` 并把
`pip install --force-reinstall --no-deps --no-build-isolation` **装进同一个 venv**，
还多带进去一个 `examples/hybrid_nearfield.py`。该文件连同"我的 pytest 进程已在收集期导入了
所有测试模块、因此测量未被污染"的判断一起写明了。共享 venv 是本机常态，
**这条纪律由它确立**：QA 运行要用一次性 target 目录（上表两条 wheel 运行就是这么做的），
别再复用 `$HOME` 下的 venv。

`pip install --target` 而不是 `python -m venv`：本机 WSL 没装 `python3.10-venv`，
`python3 -m venv` 直接失败（"apt install python3.10-venv"）。target 目录 + `PYTHONPATH`
达到同样效果，且日志里打印了 `nlcsplit.__file__` 与非源树 cwd 来证明"不在源树里跑"。
