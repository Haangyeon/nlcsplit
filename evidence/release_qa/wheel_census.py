"""发布件清点：wheel 里到底有几个成员、其中几个是测试模块、有没有"脚本式测试"混进去。

为什么要单独生成它：正文里"the wheel now has 36 members / ships seven test modules"是**现在时**的
计数主张，而 wheel 成员会随每次重导变化。手抄一次就会长期说谎（本轮实测已经是 38）。
所以这一格由本脚本读 dist/ 里的 wheel 打印，正文只引本档。

用法：python3 evidence/release_qa/wheel_census.py [dist/nlcsplit-0.1.0-py3-none-any.whl]
"""
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WHL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    ROOT, "dist", "nlcsplit-0.1.0-py3-none-any.whl")

z = zipfile.ZipFile(WHL)
names = [n for n in z.namelist() if not n.endswith("/")]
print("# wheel census: %s" % os.path.relpath(WHL, ROOT).replace("\\", "/"))
import hashlib
print("# sha256 = " + hashlib.sha256(open(WHL, "rb").read()).hexdigest())
print("# members (files, not directories): %d" % len(names))

tests = sorted(n for n in names if re.match(r"^[^/]+/tests/[^/]+\.py$", n))
# `__init__.py` 与 `conftest.py` 住在 tests/ 里但不是测试：把它们算进"脚本式测试"会把结论说反
real_tests = [t for t in tests if os.path.basename(t) not in ("__init__.py", "conftest.py")]
print("# files under */tests/: %d  (其中真正的测试模块 %d)" % (len(tests), len(real_tests)))
for t in tests:
    src = z.read(t).decode("utf-8", "replace")
    n_def = len(re.findall(r"^def test_", src, re.M))
    role = "not-a-test" if t not in real_tests else ""
    # "脚本式测试"= 有 test_ 文件却一 import 就跑、没有 test_ 函数的那种；发布件里不该有
    scriptish = "SCRIPT_STYLE" if (t in real_tests and n_def == 0) else ""
    print("#   %-46s test_ defs=%-3d %s%s" % (t, n_def, scriptish, role))

others = sorted(n for n in names if "/tests/" not in n)
print("# non-test members: %d" % len(others))
for o in others:
    print("#   " + o)
bad = [t for t in real_tests
       if len(re.findall(r"^def test_", z.read(t).decode("utf-8", "replace"), re.M)) == 0]
print("# VERDICT script-style tests shipped: %d %s" % (len(bad), ("|" + ",".join(bad)) if bad else ""))
print("# VERDICT 成员总数 %d = 测试模块 %d + tests/ 下非测试 %d + 其余 %d，四项相加=%d"
      % (len(names), len(real_tests), len(tests) - len(real_tests), len(others),
         len(real_tests) + (len(tests) - len(real_tests)) + len(others)))
