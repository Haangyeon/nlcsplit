"""可加性残差的普查：`E_NL = Σ_A E_AA + Σ_{A<B} E_AB` 到底差多少，别拿一句"由构造成立"过关。

为什么要生成（2026-10-05 复查）：正文写的是"across all systems and partitions reported here
it is 0.00–6.94e-18 Ha"，而版本库里带这个字段的归档只有水二聚体那一行（`step1_validate.py`
的产物，那里最大 6.94e-18、最小 1.73e-18）——"all systems"没有原件，下界 0.00 也不是任何
一次跑的读数。苯二聚体那侧更大的残差只躺在 `nlcsplit/logs/` 里，而那个目录被 `.gitignore`
屏蔽。本脚本用跟踪的模块把同一个校验在三个体系、四种归属方案（外加最近原子硬指派对照）上
重跑一遍，区间由脚本印出来，正文只引它印的那一段。

判据与 `nlcsplit/step1_validate.py` 一致：整体直接双重和 vs 分块和，阈值 1e-10 Ha。

用法：python3 evidence/recompute/additivity_census.py
"""
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from nlcsplit import geomlib, nlc, partition                     # noqa: E402
from pyscf import gto                                            # noqa: E402

KCAL = 627.509474
S22DIR = os.path.join(ROOT, "scratch", "lit", "s22")
BASIS = "6-31g*"
ADD_TOL_HA = 1e-10
# (标签, 几何来源, level, 是否再加最近原子对照)
CASES = [
    ("(H2O)2 official S22_02", ("s22", "水二聚体"), 1, True),
    ("(C6H6)2 A, parallel-displaced, S22_11", ("s22", "苯二聚体(A)"), 0, False),
    ("(C6H6)2 constructed sandwich", ("built", None), 0, False),
]


def density_at(mol, mf, coords):
    ni = mf._numint
    ao = ni.eval_ao(mol, coords, deriv=1)
    rho = ni.eval_rho(mol, ao, mf.make_rdm1(), xctype="GGA")
    return rho[0], rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2


print("# 可加性残差普查：整体直接双重和 vs Σ_分块")
print("# python %s  pyscf %s  numpy %s" % (sys.version.split()[0],
                                           __import__("pyscf").__version__, np.__version__))
print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip())
print("# basis %s , xc wb97x_v , 判据阈值 %.1e Ha（与 nlcsplit/step1_validate.py 同）"
      % (BASIS, ADD_TOL_HA))
print()

devs = []
for label, (kind, name), level, also_nearest in CASES:
    if kind == "s22":
        atoms, frags = geomlib.s22_system(name, S22DIR)
    else:
        atoms, frags = geomlib.benzene_sandwich(), geomlib.FRAGS["(C6H6)2"]
    mol = gto.M(atom=atoms, basis=BASIS, verbose=0, unit="Angstrom")
    mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc="wb97x_v", level=level, basis=BASIS)
    if not mf.converged:
        sys.exit("%s：SCF 未收敛" % label)
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    print("== %s  (%d 原子, %d 电子, 公共网格 %d 点, level %d)"
          % (label, mol.natm, mol.nelectron, len(X0), level))

    def row(scheme, X, W, owner):
        t = time.perf_counter()
        rho, sig = density_at(mol, mf, X)
        w0, kap, keep = nlc.vv10_fields(rho, sig, b, C)
        wr = W * rho
        idx = np.where(keep)[0]
        e_direct = nlc.pair_energy(X, wr, w0, kap, idx, idx)
        res = nlc.fragment_decomposition(X, W, rho, sig, frags, b=b, C=C, owner=owner)
        dev = abs(res["E_nl"] - e_direct)
        integ = float(np.dot(rho, W))
        rel_int = abs(integ - mol.nelectron) / mol.nelectron
        print("  %-16s N=%6d ∫ρ=%9.5f/%d (相对 %.1e %s)  E_NL(直接)=%+9.4f kcal  残差=%.3e Ha  %s  [%.1f s]"
              % (scheme, len(X), integ, mol.nelectron, rel_int,
                 "OK" if rel_int < 1e-4 else "粗网格", e_direct * KCAL, dev,
                 "OK" if dev < ADD_TOL_HA else "FAIL", time.perf_counter() - t))
        devs.append((label, scheme, dev))
        return res

    for scheme in partition.SCHEMES:
        X, W, owner = partition.atom_partition(mol, level=level, scheme=scheme)
        row(scheme, X, W, owner)
    if also_nearest:
        row("nearest(公共网格)", X0, W0, partition.nearest_partition(mol, X0))
    print()

vals = [d for (_, _, d) in devs]
print("== 汇总 ==")
print("  行数 = %d   体系数 = %d" % (len(vals), len(set(l for l, _, _ in devs))))
print("  残差最小 = %.3e Ha   残差最大 = %.3e Ha" % (min(vals), max(vals)))
print("  最大残差来自：%s / %s" % max(devs, key=lambda r: r[2])[:2])
print("  全部低于判据 %.1e Ha：%s" % (ADD_TOL_HA, all(v < ADD_TOL_HA for v in vals)))
