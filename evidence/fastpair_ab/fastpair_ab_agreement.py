"""一个脚本给两句话供原件：

(1) `paper/p2.md` 里"同一个量在两次跑之间相差 2e-17 相对值"这句话。它引的两个字面值，一个
    来自入库的 A/B 归档 JSON，另一个只出现在 `nlcsplit/logs/` 那份 pytest 日志的断言行里，
    而 `nlcsplit/logs/*.out` 被 `.gitignore` 屏蔽，所以版本库里没有它的原件——正文却把它当成
    实测数在引用。本脚本在同一台机器上把那个量以全精度 Ha 重打一遍：它打出来的就是那个字面值
    的可重跑原件，并把三方（本脚本 / 归档 JSON / 未入库日志）的绝对与相对差一次算清。
    顺带把单位钉死：日志那行是 `assert tot_box < tot_ball`，两个操作数没有乘 KCAL，所以它是
    Ha；`paper/p2_skeleton.md` 早先把它标成 kcal/mol 是单位错。

(2) `paper/p2.md` 由密度下限推"R^-6 渐近区从多远远才生效"那两个 bohr/Å 数是手算的。这里改由
    `nlcsplit.nlc.vv10_fields` 在同一个 rho_floor 上现算，看手算的 κ_min 与由此来的半径是否对得上。

用法：python3 evidence/fastpair_ab/fastpair_ab_agreement.py
"""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from nlcsplit import fastpair, geomlib, nlc, partition          # noqa: E402
from pyscf import gto                                           # noqa: E402

KCAL = 627.50947400            # 与 nlcsplit/tests/test_fastpair.py 同一常数
BOHR2A = 0.529177              # 正文换算 Å 用的那个
RHO_FLOOR = nlc.RHO_FLOOR
JSON = os.path.join(HERE, "fastpair_ab_compare.json")
# 未入库那份 pytest 断言行里的读数；本脚本存在的理由就是给它一个入库原件
PYTEST_LOG_READING_HA = 21723.206496881914
ARCH_ROW = "(H2O)2 geomlib lvl1"
ARCH_KEYS = ("ours_full", "ours_tau1em8")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


print("# 盒界总量的跨跑一致性 + 密度下限推导，两件事一份档")
print("# python %s  pyscf %s  numpy %s" % (sys.version.split()[0],
                                           __import__("pyscf").__version__, np.__version__))
print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip())
print("# sha256 nlcsplit/fastpair.py = %s" % sha(os.path.join(ROOT, "nlcsplit", "fastpair.py")))
print("# sha256 nlcsplit/nlc.py      = %s" % sha(os.path.join(ROOT, "nlcsplit", "nlc.py")))
print("# sha256 %s = %s" % (os.path.relpath(JSON, ROOT).replace("\\", "/"), sha(JSON)))
print()

# ---------- (1) 盒界总量：本机现算 vs 两个已有字面值 ----------
arch = json.load(open(JSON, encoding="utf-8"))
row = [s for s in arch["systems"] if s["system"] == ARCH_ROW]
if len(row) != 1:
    sys.exit("归档里没有唯一的 %s 行，读到 %d 行" % (ARCH_ROW, len(row)))
row = row[0]
arch_vals = {k: row[k]["sum_atomblock_root_bound_ha"] for k in ARCH_KEYS}
if len(set(arch_vals.values())) != 1:
    sys.exit("归档里 %s 的 %s 两列不相同：%s" % (ARCH_ROW, ARCH_KEYS, arch_vals))
arch_val = next(iter(arch_vals.values()))

mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", verbose=0, unit="Angstrom")
mf = partition.scf_grid(mol, xc="wb97x_v", level=1, basis="6-31g*")[0]
assert mf.converged, "SCF 未收敛，下面的比较无意义"
exact = fastpair.screened_decomposition(mol, mf, level=1, screen=None)
ref = fastpair.screened_decomposition(mol, mf, level=1, screen=None, bound="tree")
off = [(a, q) for (a, q) in exact["pairs"] if a != q]
tot_box = sum(fastpair.node_bound(ref["blocks"][a].tree, ref["blocks"][q].tree, 2.0) for (a, q) in off)
tot_ball = sum(fastpair.ball_bound(ref["blocks"][a], ref["blocks"][q], 2.0) for (a, q) in off)

print("(1) 水二聚体（geomlib 自建几何）level 1 的 Σ盒界，全精度 Ha")
print("    交叉对数 = %d    rho_floor = %r" % (len(off), RHO_FLOOR))
print("    A  本脚本现算 tot_box   = %r" % tot_box)
print("    B  归档 JSON (%s) = %r" % (ARCH_ROW, arch_val))
print("    C  未入库 pytest 日志     = %r" % PYTEST_LOG_READING_HA)
print("    逐位相同？A==B %s   A==C %s   B==C %s"
      % (tot_box == arch_val, tot_box == PYTEST_LOG_READING_HA, arch_val == PYTEST_LOG_READING_HA))
for (na, va), (nb, vb) in ((("A", tot_box), ("B", arch_val)),
                           (("A", tot_box), ("C", PYTEST_LOG_READING_HA)),
                           (("B", arch_val), ("C", PYTEST_LOG_READING_HA))):
    print("    %s-%s  绝对差 %.4e Ha   相对差 %.4e" % (na, nb, abs(va - vb), abs(va - vb) / abs(vb)))
print("    盒界与球界是否逐位相同（p2 那句 root 退化）：%s" % (tot_box == tot_ball))
print("    换算成 kcal/mol：%.4e" % (tot_box * KCAL))
print()

# ---------- (2) 密度下限那一对 ----------
rho = np.array([RHO_FLOOR])
sig = np.array([0.0])
w0, kap, keep = nlc.vv10_fields(rho, sig, b=6.0, C=0.01, rho_floor=RHO_FLOOR)
print("(2) 由 nlc.vv10_fields 在 rho 取到密度下限时现算（不重抄公式）")
print("    注意 keep=%s：密度下限这点按代码口径是被判掉的，但 vv10_fields 内部"
      % bool(keep[0]) + "用 rho_floor 兜底，所以给出的是从下方趋近的极限值")
print("    rho_floor = %r , sigma = 0  ->  kappa_min = %.6f   w0_min = %.6e"
      % (RHO_FLOOR, kap[0], w0[0]))
r = float(np.sqrt(float(kap[0]) / float(w0[0])))
print("    sqrt(kappa_min / w0_min) = %.2f bohr = %.2f Angstrom" % (r, r * BOHR2A))
