"""ΔE_NLC 到底受不受基组叠加误差影响——把 §4.1 那句"不需要反泊松校正"拿去实测。

为什么要生成（2026-10-06，评审组魔鬼代言席提出的 C1）：
  `paper/main.md` §4.1 写"dE_NLC itself needs no such correction: it is evaluated at fixed
  (non-self-consistent) superposed density, so basis-set flexisation does not enter it"。
  但 Table 1 的 ΔE_NLC 出自 `nlcsplit/step_h_s22.py:one()`，那里
  `dnlc = d["e_nlc"] - Σ terms(geomlib_sub(mol, f))["e_nlc"]`：复合物与各单体都是
  **各自收敛的自洽密度**，单体用 `geomlib_sub()` 只切自己的原子、不带鬼函数。
  同文件 `counterpoise()` 只累加 `mf.e_tot`，从未取出鬼单体的 E_NLC——
  也就是说这句话描述的构造与产出表格的构造不是同一个，而且它豁免掉的那件事没人测过。
  本脚本把它测出来：同一泛函、同一基组、同一网格档位下，ΔE_NLC 算两遍——
  一遍按表格那样子（无鬼函数），一遍把对方原子写成鬼函数——差值就是该项的 BSSE。

护栏：无鬼那一侧必须复现 `nlcsplit/logs/step_h.json` 里对应行的 dnlc，
  复现不上就非零退出、不出表——否则我可能在比两个不同的东西。

用法：
  NCS22="水二聚体 氨二聚体 甲烷二聚体" python3 evidence/nlc_cp/nlc_bsse_measure.py
"""
import hashlib
import json
import os
import socket
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from nlcsplit import geomlib, partition                                  # noqa: E402
from nlcsplit.step_f_dispersion import terms, KCAL                       # noqa: E402
from nlcsplit.step_h_s22 import build, geomlib_sub                        # noqa: E402
from pyscf import gto                                                    # noqa: E402
import pyscf                                                             # noqa: E402

BOHR2A = 1.8897261254
SIDECAR = os.path.join(ROOT, "nlcsplit", "logs", "step_h.json")
REPRO_TOL = 1e-3          # kcal/mol：无鬼侧与归档表格的一致门，比归属跨度小一个量级才有意义


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def ghost_sub(mol, idxs):
    """片段在**复合物完整基组**下的鬼单体：对方原子写成 ghost-，只带基函数不带核与电子。

    与 step_h_s22.counterpoise() 里那一份同一构造（同样的两条断言），这样测出来的
    ΔE_NLC(CP) 与正文 §3.2 已有的 ΔE_int(CP) 才是同一个反泊松约定。
    """
    C = mol.atom_coords() / BOHR2A
    sym = [mol.atom_symbol(i) for i in range(mol.natm)]
    lines = [f"{sym[i]} {C[i][0]:.10f} {C[i][1]:.10f} {C[i][2]:.10f}" for i in idxs]
    lines += [f"ghost-{sym[i]} {C[i][0]:.10f} {C[i][1]:.10f} {C[i][2]:.10f}"
              for i in range(mol.natm) if i not in set(idxs)]
    sub = gto.M(atom="\n".join(lines), basis=mol.basis, verbose=0, unit="Angstrom")
    assert sub.nao_nr() == mol.nao_nr(), "鬼单体基组维数与复合物不一致"
    assert sub.nelectron < mol.nelectron, "鬼单体电子数没减少，划分可能错了"
    return sub


rows = {r["name"]: r for r in json.load(open(SIDECAR, encoding="utf-8"))["rows"]}
names = (os.environ.get("NCS22", "水二聚体 氨二聚体 甲烷二聚体")).split()

print("# ΔE_NLC 的基组叠加误差：无鬼 vs 反泊松，同一档位同一基组")
print("# python %s  pyscf %s  numpy %s" % (sys.version.split()[0],
                                           pyscf.__version__, np.__version__))
print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip())
for rel in ("nlcsplit/step_f_dispersion.py", "nlcsplit/step_h_s22.py",
            "nlcsplit/partition.py", "nlcsplit/nlc.py", "nlcsplit/geomlib.py"):
    print("# sha256 %-32s = %s" % (rel, sha(os.path.join(ROOT, rel))))
print("# sidecar %s sha256 = %s" % (os.path.relpath(SIDECAR, ROOT).replace("\\", "/"),
                                    sha(SIDECAR)))
print("# 复现门 REPRO_TOL = %g kcal/mol（无鬼侧 vs 归档 dnlc）" % REPRO_TOL)
print()
print("%-12s %5s %-8s %10s %10s %10s %10s %9s" %
      ("system", "lvl", "basis", "dNLC(nocp)", "dNLC(CP)", "BSSE_NLC",
       "|span|", "BSSE/span"))
bad = []
for name in names:
    arch = rows.get(name)
    if arch is None:
        sys.exit("侧车里没有 %r 这一行，无法设复现护栏" % name)
    level, basis = arch["level"], arch["basis"]
    t0 = time.time()
    mol, frags, dmin = build(name)
    assert mol.basis == basis or (isinstance(mol.basis, str)
                                  and mol.basis.replace("-", "").lower() == basis.replace("-", "").lower()), \
        f"{name}: 建出来的基组 {mol.basis!r} 与归档行 {basis!r} 不一致"
    d = terms(mol, level, "复合物")
    nocp = sum(terms(geomlib_sub(mol, f), level, "单体(无鬼)")["e_nlc"] for f in frags)
    cp = sum(terms(ghost_sub(mol, f), level, "单体(鬼)")["e_nlc"] for f in frags)
    d_nocp = (d["e_nlc"] - nocp) * KCAL
    d_cp = (d["e_nlc"] - cp) * KCAL
    bsse = d_nocp - d_cp
    dev = abs(d_nocp - arch["dnlc"])
    span = arch["span"]
    print("%-12s %5d %-8s %+10.4f %+10.4f %+10.4f %10.4f %9.2f   %4.0fs"
          % (name, level, basis, d_nocp, d_cp, bsse, span,
             abs(bsse) / span if span else float("inf"), time.time() - t0))
    print("             归档 dnlc = %+.4f  本机无鬼复现差 = %.3e kcal/mol（门 %g）"
          % (arch["dnlc"], dev, REPRO_TOL))
    if dev > REPRO_TOL:
        bad.append((name, dev))
    sys.stdout.flush()

if bad:
    print("\n护栏未过：%s —— 上面这些行不能拿去改正文" % bad)
    raise SystemExit(1)
print("\n全部体系无鬼侧复现通过；BSSE_NLC 那一列即 §4.1 那句话所豁免的量。")
print("host=%s  run_utc=%s" % (socket.gethostname(),
                               time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
