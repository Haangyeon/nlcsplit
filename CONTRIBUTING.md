# 参与

- 开发在 WSL/Linux 与 PySCF>=2.12 上进行；CI 会同时跑 2.12.1 与更新的版本。
- 提交前本地跑 `python -m pytest -q`（8 项，约 90 s）。
- 任何新的能量口径必须同时给两条独立取数路径并在不一致时抛错，参照 `nlcsplit/step_f_dispersion.py` 的三条校验。
- 不要往仓库或脚本里写任何口令、私钥、凭据。

## 发布/投稿前的三道检查

都是实测踩出来的，不是礼节性清单。

1. **先清构建残留再装**。`pip install <本仓库>` 走的是**就地构建**，会在仓库根
   留下 `build/` 与 `nlcsplit.egg-info/`；setuptools 的 `build_py` 只往
   `build/lib/` 里加文件、**不清理已删除的模块**。后果：把一个模块
   `git mv` 走之后，它仍然会从 `build/lib/` 被打进 wheel——
   装出来的包里有源树中根本不存在的文件，而且 `pip --no-cache-dir`
   也救不了（问题不在缓存）。

   ```bash
   rm -rf build *.egg-info      # 每次改了包结构都要做
   pip install --no-deps --target /tmp/chk .
   ls /tmp/chk/nlcsplit/*.py    # 逐行核对装出来的东西
   ```

2. **从源码树之外跑测试**，别只在仓库里 `pytest`：

   ```bash
   cd /tmp && PYTHONPATH=/tmp/chk python3 -m pytest --pyargs nlcsplit
   ```

   这条会立刻暴露"只在自己仓库里才成立"的问题——比如 `slow` 标记
   只登记在仓库 `pyproject.toml` 的 `[tool.pytest.ini_options]` 时，
   外面跑就会对每个 `@pytest.mark.slow` 报 `PytestUnknownMarkWarning`。
   现在由 `nlcsplit/tests/conftest.py` 随包注册，放在包里而不是只放仓库配置里。

3. **注意 fast lane 覆盖不到什么**。`-m "not slow"` 是 CI 的第一道，
   它**故意不含** `test_matches_pyscf_native_kernel` 与
   `test_pair_terms_regression`（这两个才是与 PySCF 原生核的对照）。
   所以 CI 第二道 `pytest -q`（含 slow）不能省——只跑第一道等于
   没验过核心算术。

## 数字进正文之前

表里每一格，在写进 `paper/main.md` 或 README 之前，
**当场打开它声称的那个出处文件看一眼**。这条规矩救过我们三次：
一次是把 level 0 的"换网格表示差"当成算法误差，一次是把有效数据误判为陈旧
（看错同名日志的时间戳），一次是 README/骨架里挂着一条
"与 ORCA 6.0.1 差 6e-4 kcal/mol"而那份 ORCA 输出里
**根本没有单列的非局域项**（详见 `MAIN-skeleton.md` 表 1 的撤回行）。

## "不含 GAMESS 代码"这句话怎么守

README、`LICENSE` 段与软件文都写着**不含任何 GAMESS 代码**（GAMESS 许可证不允许再分发）。
这是法律性声明，不能靠印象维护。做法是把它变成一条可复跑的检查：

```bash
node tools/audit_no_gamess.js            # 独立目录 pip install --target 后逐文件扫装出来的东西
node tools/audit_no_gamess.js --selftest # 只验判据本身有没有分辨力，不安装
```

它扫的是**装出来的东西**而不是源码树（否则 `build/lib` 里的陈旧副本会漏检，见上面第 1 条），
命中项一律具名记账：唯一合法的 GAMESS 出现是包 docstring 与 `dist-info/METADATA`
里那句免责声明，规则外的命中直接非零退出。最近一次实测：扫 17 个文件、
具名豁免 2 条、GAMESS 相关 0 条、GPL/AGPL 类冲突信号 0 条（`--selftest` 5/5，
其中一条专门验"同一个文件里的非免责句不放行"）。
`tools/audit_no_gamess.js` 自己随包发布，所以这三条命令对读者也是可跑的。
新增任何从别处移植的数值代码前，先确认其许可，再重跑这条。
