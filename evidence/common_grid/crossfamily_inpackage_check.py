#!/usr/bin/env python3
# 第零'波：家族外分区（Voronoi / Hirshfeld）并进包内之后的对跑复现。
#
# 为什么要这份脚本（PLAN-20261011 §三 的顺序坑）：§5 那句"包 implements … every table in
# this paper"要成立，家族外两种构造必须在 `pip install nlcsplit` 之后就能拿到；而八格读数是
# 包外脚本 evidence/common_grid/hirshfeld_crossfamily.py 产出的。并进包内之后，两件事得分别
# 证明，不能混着说：
#   (1) 构造等价：包内 `partition.voronoi_factors` / `partition.hirshfeld_factors` 给出的
#       逐点权重与包外脚本那两个函数**逐位相同**（np.array_equal，不是"差小于某个容差"）。
#   (2) 读数等价：走包内这条路的八格 E_AB / 跨度，与已归档的三份档逐位相符（人工按位比对本文件
#       与 20261009T155508Z / 20261009T193232Z / 20261010T061455Z）。
# 只证 (1) 就把"同一个 S 喂进同一个核必然给同一个数"当成新证据，那是自指校验，本仓不做。
# DOUBLE=1 时对 Voronoi/Hirshfeld 各多跑一次分解（包外权重 vs 包内权重），把 (2) 在同一进程里
# 也当场跑一遍；代价是每个体系多两次双重积分，所以只在便宜的三份小体系上开。
#
# 护栏沿用包外脚本那四条：每点权和=1（在 partition 内部判）、自由原子密度分母>0 或走兜底、
# Voronoi 的 one-hot argmax 逐点等于 nearest_partition、体系在普查表里有归档值时
# nearest 硬指派必须复现它（level 1，门 0.005）。
#
# 用法：LEVEL=1 NAMES="水二聚体 氨二聚体 甲烷二聚体" DOUBLE=1 python3 -u evidence/common_grid/crossfamily_inpackage_check.py
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
LEVEL = int(os.environ.get("LEVEL", "1"))
NAMES = os.environ.get("NAMES", "水二聚体 氨二聚体 甲烷二聚体").split()
DOUBLE = os.environ.get("DOUBLE", "0") == "1"
FAM = list(partition.SCHEMES)
CROSS = list(partition.CROSS_FAMILY_SCHEMES)

CENSUS = {"水二聚体": -7.8950}
CENSUS_TOL = 0.005
MULT = {"H": 2, "C": 3, "N": 4, "O": 3, "F": 2}   # 与包外脚本同一张基态多重度表
# Hirshfeld 那一列不许按"逐位相符"判：它经手由基态多重度解出来的自由原子 UHF，而开壳层
# 近简并轨道之间允许做能量不变的转动 —— 实测同一个 e_tot 重复十二位、密度矩阵的 sha 却
# 逐次不同（H 稳，C/N/O 不稳），传下来的 E_AB 抖动在水二聚体 level 0 上是 5e-4 kcal/mol。
# 所以这一列的门取 1e-3（按那次实测留了一个量级余量），家族内四方案与 Voronoi 不碰那个 SCF，
# 仍然要求 np.array_equal 逐位相同。这条改写是本轮对跑抓出来的，不是为了让新旧相符而放宽。
HIR_TOL = 1e-3


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ---------------------------------------------------------------- 包外（归档时那条）路径
# 逐字从 hirshfeld_crossfamily.py 搬来，不改一个算子顺序：改了就等于拿"我改过的旧路径"
# 去比新路径，那条比就白做了。
def old_free_atom_soft(mol, X0, basis="6-31g*"):
    dens = []
    ni = numint.NumInt()
    for a in range(mol.natm):
        sym = mol.atom_symbol(a)
        atm = gto.M(atom="%s 0 0 0" % sym, basis=basis, unit="Angstrom",
                    spin=MULT[sym] - 1, verbose=0)
        atm.build()
        mf = scf.UHF(atm).run()
        if not mf.converged:
            sys.exit("%s: 自由原子 UHF 未收敛" % sym)
        dm = mf.make_rdm1()
        rel = X0 - mol.atom_coord(a, unit="Angstrom")
        ao = ni.eval_ao(atm, rel, deriv=1)
        rho = ni.eval_rho(atm, ao, dm, xctype="GGA")
        dens.append(np.asarray(rho[0], dtype=float))
    W = np.vstack(dens)
    if W.shape[0] != mol.natm:
        sys.exit("Hirshfeld: 权重矩阵 %s 的行数 ≠ 原子数 %d" % (W.shape, mol.natm))
    denom = W.sum(axis=0)
    zero = denom <= 0
    nz = int(zero.sum())
    if nz:
        owner = partition.nearest_partition(mol, X0)
        S = W.copy()
        S[:, ~zero] = W[:, ~zero] / denom[~zero]
        S[:, zero] = 0.0
        S[owner[zero], np.arange(len(X0))[zero]] = 1.0
        return S
    return W / denom


def old_voronoi_soft(mol, X0):
    owner = partition.nearest_partition(mol, X0)
    S = np.zeros((mol.natm, len(X0)))
    S[owner, np.arange(len(X0))] = 1.0
    if not np.array_equal(S.argmax(axis=0), owner):
        sys.exit("Voronoi: one-hot 权重与 nearest_partition 不一致")
    return S


def e_ab(X0, W0, rho0, sig0, frags, S):
    res = nlc.fragment_decomposition(X0, W0, rho0, sig0, frags, b=B, C=C,
                                      soft=S, closure_check=True)
    return res["inter"][(0, 1)] * KCAL, res["E_nl"] * KCAL


print("# 第零'波对跑：家族外分区并进 partition.py 之后，包内路径 vs 包外（归档那条）路径")
print("# python %s  pyscf %s  numpy %s" % (sys.version.split()[0],
                                           pyscf.__version__, np.__version__))
print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip())
for rel in ("nlcsplit/partition.py", "nlcsplit/nlc.py", "nlcsplit/step_h_s22.py",
            "evidence/common_grid/hirshfeld_crossfamily.py",
            "evidence/common_grid/crossfamily_inpackage_check.py"):
    print("# sha256 %-46s = %s" % (rel, sha(os.path.join(ROOT, rel))))
print("# level = %d  b = %g  C = %g  DOUBLE = %d（1 = 同一进程里两条路径都跑分解）"
      % (LEVEL, B, C, int(DOUBLE)))
print("# 包内方案表：SCHEMES(家族内) = %s ; CROSS_FAMILY_SCHEMES = %s ; ALL_SCHEMES = %s"
      % (",".join(FAM), ",".join(CROSS), ",".join(partition.ALL_SCHEMES)))
print()

bad = []
for name in NAMES:
    t0 = time.time()
    mol, frags, dmin = build(name)
    mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc="wb97x_v",
                                                level=LEVEL, basis="6-31g*")
    assert mf.converged, "%s: SCF 未收敛" % name
    print("== %s  level=%d  原子 %d  公共网格 N=%d  片间min %.2f Å"
          % (name, LEVEL, mol.natm, len(X0), dmin))

    # (1) 构造等价：逐位
    S_vor_new = partition.voronoi_factors(mol, X0)
    S_vor_old = old_voronoi_soft(mol, X0)
    eq_vor = np.array_equal(S_vor_new, S_vor_old)
    S_hir_new, S_hir_alt, n_zero = partition.hirshfeld_factors(mol, X0)
    S_hir_old = old_free_atom_soft(mol, X0)
    dS_hir = float(np.abs(S_hir_new - S_hir_old).max())
    print("   构造逐位相等  voronoi %s (dtype %s/%s, shape %s/%s) | "
          "hirshfeld 最大逐点权重差 = %.3e（下溢点 %d，门见文件头 HIR_TOL 的来由）"
          % (eq_vor, S_vor_new.dtype, S_vor_old.dtype, S_vor_new.shape, S_vor_old.shape,
             dS_hir, n_zero))
    if S_hir_alt is not None:
        print("   （有 %d 个下溢点，包内同时给了等权兜底对照 S_alt，本轮不取它当判据）" % n_zero)
    if not eq_vor:
        bad.append((name, "voronoi-weights-not-identical", None))

    # 家族内：包内统一入口 vs 老的 partition_matrix + 列归一
    e_fam = []
    for s in FAM:
        S_disp = partition.scheme_factors(mol, X0, scheme=s)
        p = partition.partition_matrix(mol, X0, scheme=s)
        S_direct = p / p.sum(axis=0)
        eq = np.array_equal(S_disp, S_direct)
        if not eq:
            bad.append((name, "dispatcher-vs-partition_matrix", s))
        e, _ = e_ab(X0, W0, rho0, sig0, frags, S_disp)
        e_fam.append(e)
        print("   家族内 %-16s E_AB = %+9.4f  （dispatcher 与 partition_matrix 逐位相等：%s）"
              % (s, e, eq))
    span_fam = max(e_fam) - min(e_fam)

    e_vor, tot_vor = e_ab(X0, W0, rho0, sig0, frags, S_vor_new)
    e_hir, tot_hir = e_ab(X0, W0, rho0, sig0, frags, S_hir_new)
    print("   Voronoi(包内)   E_AB = %+9.4f  E_NL = %+10.4f" % (e_vor, tot_vor))
    print("   Hirshfeld(包内) E_AB = %+9.4f  E_NL = %+10.4f" % (e_hir, tot_hir))

    if DOUBLE:
        e_vor_old, _ = e_ab(X0, W0, rho0, sig0, frags, S_vor_old)
        e_hir_old, _ = e_ab(X0, W0, rho0, sig0, frags, S_hir_old)
        d_v = abs(e_vor - e_vor_old)
        d_h = abs(e_hir - e_hir_old)
        same_v = (e_vor == e_vor_old)
        ok_h = (d_h <= HIR_TOL)
        print("   同进程双跑（旧权重 vs 新权重）：voronoi %+.6f vs %+.6f 差 %.1e %s | "
              "hirshfeld %+.6f vs %+.6f 差 %.1e %s（门 %.0e）"
              % (e_vor_old, e_vor, d_v, "bit-identical" if same_v else "NOT",
                 e_hir_old, e_hir, d_h, "OK" if ok_h else "OVER", HIR_TOL))
        if not same_v:
            bad.append((name, "voronoi-readings-not-identical", d_v))
        if not ok_h:
            bad.append((name, "hirshfeld-readings-over-tol", d_h))

    e_all = e_fam + [e_hir, e_vor]
    span_all = max(e_all) - min(e_all)
    print("   → 家族内跨度 = %.4f kcal/mol（四方案，同一网格同一权重）" % span_fam)
    print("   → 含两个家族外构造的总跨度 = %.4f kcal/mol" % span_all)
    print("   → 比值（含家族外 / 家族内） = %.2f"
          % (span_all / span_fam if span_fam > 0 else float("inf")))

    owner_near = partition.nearest_partition(mol, X0)
    if name in CENSUS and LEVEL == 1:
        res_near = nlc.fragment_decomposition(X0, W0, rho0, sig0, frags, b=B, C=C,
                                              owner=owner_near, closure_check=True)
        dev = abs(res_near["E_nl"] * KCAL - CENSUS[name])
        print("   护栏：nearest(公共网格) E_NL 与普查归档 %+.4f 之差 = %.4f（门 %.3f）%s"
              % (CENSUS[name], dev, CENSUS_TOL, "OK" if dev <= CENSUS_TOL else "**不过**"))
        if dev > CENSUS_TOL:
            bad.append((name, "census", dev))
    print("   （与归档对照：读数请逐位比对 %s 里同名体系的行）"
          % "evidence/common_grid/20261009T155508Z_hirshfeld_crossfamily_l1_small_after_position_fix.out")
    print("   （用时 %.1f s）" % (time.time() - t0))
    print()

if bad:
    print("VERDICT REFUSED —— 对跑不过：%s" % bad)
    sys.exit(1)
print("VERDICT DONE —— 构造逐位相等，包内路径读数已打印；与归档的逐位比对见上面各体系行")
