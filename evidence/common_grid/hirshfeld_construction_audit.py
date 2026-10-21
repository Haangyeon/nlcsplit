#!/usr/bin/env python3
# 家族外构造的两处自审：Hirshfeld 的中心单位 + 自由原子 UHF 的可重复性。
#
# 触发原因：第零'波把 Voronoi/Hirshfeld 并进 `nlcsplit/partition.py` 时，对跑脚本
# `evidence/common_grid/crossfamily_inpackage_check.py` 报 Hirshfeld 的权重新旧**不逐位相同**
# （水二聚体 level 0 上 E_AB 差 3.1e-05 kcal/mol）。查下去不是并包的错，而是下面两条，
# 两条都出在归档那条通路上：
#
#  A) 单位口径。包外脚本第 87 行的自由原子中心是
#        rel = X0 - mol.atom_coord(a, unit="Angstrom")
#     而 X0 来自 `partition.scf_grid` → `mf.grids.coords`，PySCF 的网格坐标恒为 Bohr；
#     `Mole.atom_coord` 默认单位是 Bohr，显式写 "Angstrom" 就返回 Å。两个单位相减，
#     两个单位相减，等价于把每个自由原子挪到了"离原点只差一个 Bohr/Å 换算因子"的错位置上
#     ——离坐标原点越远的原子挪得越多（换算因子由本脚本的"单位事实"行现场打印，不写在注释里）。
#     本脚本先证明单位事实（同一批原子的 Bohr 值 / Å 值 / 两者比值），再量化它对权重与读数的影响。
#
#  B) 可重复性。Hirshfeld 要解每个元素的基态开壳层 UHF。同一个 e_tot 重复到小数点后十二位不变，
#     密度矩阵的 sha 却逐次不同（近简并轨道之间允许做能量不变的转动），传下来 E_AB 就有抖动。
#     这条决定"家族外那一列能不能按逐位相符判"：家族内四方案与 Voronoi 不碰这个 SCF，仍然逐位可复。
#
# 两个影响的量级都用同一张公共网格上的跨度来报：家族内跨度、含 Voronoi 的跨度、
# 含"Å 中心 Hirshfeld"（归档口径）的跨度、含"Bohr 中心 Hirshfeld"（同单位）的跨度。
# 只测 level 0（本脚本的目的是定价，不是替换归档读数）；level 1 的八格读数归
# crossfamily_inpackage_check.py 那条路。
#
# 用法：LEVEL=0 NAMES="水二聚体 氨二聚体 甲烷二聚体" python3 -u evidence/common_grid/hirshfeld_construction_audit.py
import os
import subprocess
import sys
import time
import hashlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from pyscf import gto, scf  # noqa: E402
from pyscf.dft import numint  # noqa: E402
import pyscf  # noqa: E402
from nlcsplit import partition, nlc  # noqa: E402
from nlcsplit.step_f_dispersion import KCAL  # noqa: E402
from nlcsplit.step_h_s22 import build  # noqa: E402

B, C = 6.0, 0.01
LEVEL = int(os.environ.get("LEVEL", "0"))
NAMES = os.environ.get("NAMES", "水二聚体 氨二聚体 甲烷二聚体").split()
FAM = list(partition.SCHEMES)
MULT = dict(partition.FREE_ATOM_MULT)


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def dm_sha(a):
    return hashlib.sha256(np.ascontiguousarray(np.asarray(a)).tobytes()).hexdigest()[:16]


def hirshfeld_S(mol, X0, center_unit, basis="6-31g*"):
    """给定中心单位口径的 Hirshfeld 权重。center_unit 只是决定 atom_coord 返回 Bohr 还是 Å。"""
    ni = numint.NumInt()
    dens = []
    for a in range(mol.natm):
        sym = mol.atom_symbol(a)
        atm = gto.M(atom="%s 0 0 0" % sym, basis=basis, unit="Angstrom",
                    spin=MULT[sym] - 1, verbose=0)
        atm.build()
        mf = scf.UHF(atm).run()
        if not mf.converged:
            sys.exit("%s: 自由原子 UHF 未收敛" % sym)
        rel = X0 - mol.atom_coord(a, unit=center_unit)
        ao = ni.eval_ao(atm, rel, deriv=1)
        dm = mf.make_rdm1()
        rho = ni.eval_rho(atm, ao, dm, xctype="GGA")
        dens.append(np.asarray(rho[0], dtype=float))
    W = np.vstack(dens)
    return W / W.sum(axis=0)


def e_ab(X0, W0, rho0, sig0, frags, S):
    res = nlc.fragment_decomposition(X0, W0, rho0, sig0, frags, b=B, C=C, soft=S,
                                     closure_check=True)
    return res["inter"][(0, 1)] * KCAL, res["E_nl"] * KCAL


print("# 家族外构造自审：Hirshfeld 中心单位口径 + 自由原子 UHF 可重复性")
print("# python %s  pyscf %s  numpy %s" % (sys.version.split()[0],
                                           pyscf.__version__, np.__version__))
print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip())
for rel in ("nlcsplit/partition.py", "nlcsplit/nlc.py", "nlcsplit/step_h_s22.py",
            "evidence/common_grid/hirshfeld_crossfamily.py",
            "evidence/common_grid/crossfamily_inpackage_check.py",
            "evidence/common_grid/hirshfeld_construction_audit.py"):
    print("# sha256 %-46s = %s" % (rel, sha(os.path.join(ROOT, rel))))
print("# level = %d  b = %g  C = %g" % (LEVEL, B, C))
print()

# ---------------------------------------------------------------- 自由原子 UHF 的可重复性
print("== 自由原子 UHF：同一进程内重复三次 ==")
for sym in sorted(MULT):   # 表里每个元素都测，谁稳谁不稳一目了然
    es, hs = [], []
    for _ in range(3):
        atm = gto.M(atom="%s 0 0 0" % sym, basis="6-31g*", unit="Angstrom",
                    spin=MULT[sym] - 1, verbose=0)
        atm.build()
        mf = scf.UHF(atm).run()
        es.append(mf.e_tot)
        hs.append(dm_sha(mf.make_rdm1()))
    print("   %-2s spin=%d  e_tot 三次全同=%s (%.12f)  dm_sha 三次全同=%s  %s"
          % (sym, MULT[sym] - 1, len(set(es)) == 1, es[0], len(set(hs)) == 1,
             " ".join(hs)))
print()

# ---------------------------------------------------------------- 逐体系
for name in NAMES:
    t0 = time.time()
    mol, frags, dmin = build(name)
    mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc="wb97x_v", level=LEVEL, basis="6-31g*")
    assert mf.converged, "%s: SCF 未收敛" % name
    print("== %s  level=%d  原子 %d  公共网格 N=%d  片间min %.2f Å"
          % (name, LEVEL, mol.natm, len(X0), dmin))

    bohr = np.abs(np.asarray(mol.atom_coords())).max()
    agr = np.abs(np.array([mol.atom_coord(i, unit="Angstrom") for i in range(mol.natm)])).max()
    print("   单位事实：|grids coords| max = %.4f  |atom_coord() 默认(Bohr)| max = %.4f  "
          "|atom_coord(unit=Angstrom)| max = %.4f  比值 = %.4f"
          % (np.abs(X0).max(), bohr, agr, bohr / agr))

    e_fam = []
    for s in FAM:
        S = partition.scheme_factors(mol, X0, scheme=s)
        e, _ = e_ab(X0, W0, rho0, sig0, frags, S)
        e_fam.append(e)
    S_vor = partition.voronoi_factors(mol, X0)
    e_vor, _ = e_ab(X0, W0, rho0, sig0, frags, S_vor)
    S_ang = hirshfeld_S(mol, X0, "Angstrom")
    S_bohr = hirshfeld_S(mol, X0, "Bohr")
    e_ang, tot = e_ab(X0, W0, rho0, sig0, frags, S_ang)
    e_bohr, _ = e_ab(X0, W0, rho0, sig0, frags, S_bohr)

    span_fam = max(e_fam) - min(e_fam)
    span_vor = max(e_fam + [e_vor]) - min(e_fam + [e_vor])
    span_ang = max(e_fam + [e_vor, e_ang]) - min(e_fam + [e_vor, e_ang])
    span_bohr = max(e_fam + [e_vor, e_bohr]) - min(e_fam + [e_vor, e_bohr])
    print("   权重差 max|S_Angstrom - S_Bohr| = %.6f" % np.abs(S_ang - S_bohr).max())
    print("   E_AB  becke %+8.4f | voronoi %+8.4f | hirshfeld(Å 归档口径) %+8.4f | "
          "hirshfeld(Bohr 同单位) %+8.4f | 差 %+8.4f"
          % (e_fam[0], e_vor, e_ang, e_bohr, e_bohr - e_ang))
    print("   跨度  家族内 %.4f | +Voronoi %.4f | +Hirshfeld(Å) %.4f | +Hirshfeld(Bohr) %.4f"
          % (span_fam, span_vor, span_ang, span_bohr))
    print("   → 换到同单位后，家族外增量按绝对量 = %.4f → %.4f kcal/mol（+Voronoi 那档 %.4f 不变）"
          % (span_ang - span_fam, span_bohr - span_fam, span_vor - span_fam))
    print("   E_NL 全方案同值 = %+.4f（归属只改分块，不改总量）" % tot)
    print("   （用时 %.1f s）" % (time.time() - t0))
    print()

print("AUDIT DONE —— 两条自审的读数都已打印；判读与是否重跑八格由作者定，本脚本不改任何归档。")
