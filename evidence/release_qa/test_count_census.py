"""测试条数清点：收集到多少条、其中多少条被标成 slow、wheel 里那七个模块各收了几条。

为什么要单独生成：正文写"those seven collect 49 in today's tree, and the 20 that stay behind"，
那是**当下树**的计数主张。加了回归测试之后它就过期了，而过期的整数不会被数字闸门抓到
（它只拦带小数点的量，计数交给语境判断）。所以这一格由本脚本打印并归档。

用法：python3 evidence/release_qa/test_count_census.py
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def collect(expr=None):
    cmd = [sys.executable, "-m", "pytest", "nlcsplit/tests", "--collect-only", "-q"]
    if expr:
        cmd += ["-m", expr]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True).stdout
    # `pytest -q --collect-only` 在有被筛掉的条目时打的是 "52/73 tests collected (21 deselected)"，
    # 里面同时含 "73 tests collected"。先按带分数线的形去匹配，否则筛过的会读成全量
    # ——本仓第一版就是这么把 52 读成 73 的，靠下面那条相加校验暴露。
    m = re.search(r"(\d+)/\d+ tests? collected", out) or re.search(r"(\d+) tests? collected", out)
    n = int(m.group(1)) if m else -1
    return n, out


print("# test-count census")
print("# python %s  pyscf %s" % (sys.version.split()[0],
                                 __import__("pyscf").__version__))
print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip())
tot, _ = collect()
fast, _ = collect("not slow")
slow, _ = collect("slow")
print("# collected total=%d  non-slow=%d  slow=%d  (non-slow+slow=%d%s)"
      % (tot, fast, slow, fast + slow, "" if fast + slow == tot else "  MISMATCH"))
if tot < 0 or fast < 0 or slow < 0 or fast + slow != tot:
    sys.exit("清点不出来就退出：不要把'没解析到'写成 0")

per = {}
for mod in sorted(os.listdir(os.path.join(ROOT, "nlcsplit", "tests"))):
    if not (mod.startswith("test_") and mod.endswith(".py")):
        continue
    out = subprocess.run([sys.executable, "-m", "pytest", "nlcsplit/tests/" + mod,
                          "--collect-only", "-q"], cwd=ROOT, capture_output=True,
                         text=True).stdout
    m = re.search(r"(\d+)/\d+ tests? collected", out) or re.search(r"(\d+) tests? collected", out)
    per[mod] = int(m.group(1)) if m else -1
    print("#   %-32s %d" % (mod, per[mod]))
print("# 逐模块相加=%d，与总数 %d %s" % (sum(per.values()), tot,
                                        "一致" if sum(per.values()) == tot else "不一致"))
if sum(per.values()) != tot:
    sys.exit("逐模块相加不等于总数：有模块没被数进去")

# 正文真正要说的不是"树里有多少条"，而是"装进 wheel 的那几个模块收多少条、留在仓里的那几个多少条"。
# 所以这里直接读 wheel 的成员清单来分组，而不是靠人记白名单。
import zipfile
DIST = os.path.join(ROOT, "dist")
CANON = "nlcsplit-0.1.0-py3-none-any.whl"
wheels = sorted(f for f in os.listdir(DIST) if f.endswith(".whl"))
# 只认出货口写的那个规范名。这里原来是 sorted(wheels)[0]：2026-10-09 我把上一版 wheel 改名成
# dist/archive-20261005T0506Z-...whl 留着当"能证伪『已重打』"的证据之后，'a' 排在 'n' 前面，
# 这份清点就静悄悄去数三周前那个 wheel 的成员了——一个自称"读 wheel 不靠记忆"的生成器，
# 被我自己新加的归档命名规则毒掉，而且它给的数看起来完全合理（54/7 正是那天的真值）。
if CANON not in wheels:
    sys.exit("dist/ 里没有规范名 %s（现有 %s）：先跑 node tools/make_public_repo.js 再清点"
             % (CANON, wheels))
names = zipfile.ZipFile(os.path.join(DIST, CANON)).namelist()
shipped = {os.path.basename(n) for n in names if re.match(r"^[^/]+/tests/test_.*\.py$", n)}
in_ship = sorted(m for m in per if m in shipped)
out_ship = sorted(m for m in per if m not in shipped)
s_in = sum(per[m] for m in in_ship)
s_out = sum(per[m] for m in out_ship)
print("# 分组（按出货 wheel 的实际成员；只认规范名，见上面 2026-10-09 的教训）: shipped wheel = %s" % CANON)
print("#   随包发布 %d 个模块，共收 %d 条：%s" % (len(in_ship), s_in, ", ".join(in_ship)))
print("#   不随包    %d 个模块，共收 %d 条：%s" % (len(out_ship), s_out, ", ".join(out_ship)))
print("#   两组合计 %d，与总数 %d %s" % (s_in + s_out, tot,
                                        "一致" if s_in + s_out == tot else "不一致"))
if s_in + s_out != tot or len(in_ship) + len(out_ship) != len(per):
    sys.exit("分组不相加等于全量：有模块既不在 shipped 也不在 not-shipped")
