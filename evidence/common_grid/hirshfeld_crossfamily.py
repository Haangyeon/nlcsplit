#!/usr/bin/env python3
# 家族外分区：把"归属不确定度"从"Becke 家族内的参数敏感性"升到"跨构造"的实测。
#
# 为什么需要它（外部领域席第 1、4 条）：正文的四个方案（becke / becke-becke-rad /
# becke-treutler / stratmann）实测是**一个 Becke 家族的两个开关**（公共网格上
# Becke↔Stratmann 之差见 evidence/common_grid/20261009T083325Z_ownership_vs_quadrature_l1_benzene_dimers.out
# 的纯归属列，量级上远小于半径表那一对）。所以"归属不确定度"
# 这个名字在跨方法意义上还没被证明过。本脚本在同一张公共网格、同一套权重上再加两个
# **构造上不属于该家族**的分区：
#   * Voronoi：最近原子硬指派（等价于 one-hot soft 权重）——不依赖任何密度权重；
#   * Hirshfeld（库存化/stockholder）：逐点 w_A = ρ_A^free / Σ_B ρ_B^free，自由原子密度取
#     基态多重度、UHF 密度、**不做球平均**（与 Gaussian 的默认实现不同之处写在这里，
#     不留给读者猜）。
# 三个构造都在同一 X0/W0/ρ0 上评，所以求积不可能混进来（这是本目录一贯的口径）。
#
# 预登记判据（写下时该脚本尚未运行，2026-10-09）：
#   * 若 家族外跨度 / 家族内跨度 ≤ 2  → "归属不确定度"仍只能带"家族内"限定，正文不许升级措辞；
#   * 若 2 < 比值 ≤ 10                → 跨构造比家族内大但不换量级，正文按实测区间写，仍标家族；
#   * 若 比值 > 10                    → 家族限定必须撤下，误差棒按跨构造写。
# 任何一支都要打印两个跨度的原值，不许只报比值（比值有分母，分母是能被读者核的那个）。
#
# 护栏（缺一条就退出，不打印结论）：
#   1) 每点 soft 权重和 = 1（Hyldahl 归一化后逐点判，超差即抛；fragment_decomposition 内部也判）；
#   2) Hirshfeld 的每点分母 Σ_B ρ_B^free 必须 > 0（自由原子密度在网格边缘会下溢）；
#   3) Voronoi 的 one-hot 权重与 partition.nearest_partition 的硬指派**逐点一致**（否则不是 Voronoi）；
#   4) 若该体系在普查表里有归档值，nearest 硬指派在公共网格上必须复现它（同 ownership_vs_quadrature.py）。
#
# 用法：LEVEL=0 NAMES="水二聚体 甲烷二聚体" python3 evidence/common_grid/hirshfeld_crossfamily.py
import os
import subprocess
import sys
import time
import hashlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from pyscf import gto, scf
from pyscf.dft import numint
import pyscf
from nlcsplit import partition, nlc
from nlcsplit.step_f_dispersion import KCAL
from nlcsplit.step_h_s22 import build

B, C = 6.0, 0.01
LEVEL = int(os.environ.get("LEVEL", "1"))
NAMES = os.environ.get("NAMES", "水二聚体 氨二聚体 甲烷二聚体").split()
SCHEMES = list(partition.SCHEMES)

# 普查归档控制值（与 ownership_vs_quadrature.py 同表，来自 step_h 普查；用于护栏 4）
CENSUS = {"水二聚体": -7.8950}
CENSUS_TOL = 0.005

# 基态自由原子的多重度（Hirshfeld 的自由原子密度用这个自旋态）
MULT = {"H": 2, "C": 3, "N": 4, "O": 3, "F": 2}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def free_atom_soft(mol, X0, basis="6-31g*"):
    """Hirshfeld/stockholder 权重：w_A(r) = ρ_A^free(r) / Σ_B ρ_B^free(r)。

    自由原子 = 该元素的基态多重度（MULT），UHF 密度，与二聚体同基组、同一批网格点。
    不做球平均：这一点与 Gaussian 默认实现不同，按本仓规矩写在函数头而不是藏起来。
    """
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
        # 关键：自由原子必须落在**它自己的位置**上——把网格搬到以该原子为原点再取值。
        # 2026-10-09 第一版把六个自由原子都放在原点算密度 ⇒ 六条径向函数几乎重合 ⇒
        # 权重≈均匀(1/natm) ⇒ 片间块恰好等于总量的一半（三条体系全都如此），
        # 那是构造错的指纹，不是物理结果；那条错读数留档在
        # evidence/common_grid/20261009T152500Z_hirshfeld_crossfamily_l1_small.out
        # 2026-10-12 A 件修正：X0 来自 partition.scf_grid → mf.grids.coords，恒为 Bohr；
        # 原先这里减的是 mol.atom_coord(a, unit="Angstrom")，两个单位相减 ⇒ 每个自由原子
        # 按 (1 − 1/BOHR)·R 整体错位，离坐标原点越远挪得越多。现与网格同为 Bohr（默认单位）。
        # 这一改使本脚本与 20261009T155508Z / 20261009T193232Z / 20261010T061455Z 三份归档
        # 不再逐位相符：旧档原样不重写（MANIFEST 按原始字节锁着），更正注记见同目录 sidecar。
        rel = X0 - mol.atom_coord(a)
        ao = ni.eval_ao(atm, rel, deriv=1)
        rho = ni.eval_rho(atm, ao, dm, xctype="GGA")
        dens.append(np.asarray(rho[0], dtype=float))   # 只要密度分量；整块 append 会把梯度也塞进来
    W = np.vstack(dens)
    if W.shape[0] != mol.natm:
        sys.exit("Hirshfeld: 权重矩阵 %s 的行数 ≠ 原子数 %d——只许 append rho[0]，"
                 "整块 append 会把 4 个分量（含梯度）也塞进来" % (W.shape, mol.natm))
    denom = W.sum(axis=0)
    zero = denom <= 0
    nz = int(zero.sum())
    if nz:
        # 兜底规则（先说事实、不猜原因）：这些点自由原子密度全零，无法归一化。
        # 主规则 = 最近原子硬指派（Voronoi）；对照 = 全部原子等权；
        # "规则选哪个无所谓"由下面的敏感性对照当场证，不写成断言。
        owner = partition.nearest_partition(mol, X0)
        print("   注：%d/%d 个网格点自由原子密度全零（下溢），按最近原子兜底；"
              "另跑等权兜底做敏感性对照" % (nz, len(X0)))
        S_alt = W.copy()
        S_alt[:, zero] = 1.0 / mol.natm
        S_alt = S_alt / S_alt.sum(axis=0)
        S = W.copy()
        S[:, ~zero] = W[:, ~zero] / denom[~zero]
        S[:, zero] = 0.0
        S[owner[zero], np.arange(len(X0))[zero]] = 1.0
        dev = np.abs(S.sum(axis=0) - 1.0).max()
        if dev > 1e-12:
            sys.exit("Hirshfeld: 兜底后每点和偏离 1 达 %.3e" % dev)
        return S, S_alt
    S = W / denom
    dev = np.abs(S.sum(axis=0) - 1.0).max()
    if dev > 1e-12:
        sys.exit("Hirshfeld: 归一化后每点和偏离 1 达 %.3e" % dev)
    return S, None


def voronoi_soft(mol, X0):
    """Voronoi = 最近原子硬指派，写成 one-hot soft 权重（逐点恰一个 1）。"""
    owner = partition.nearest_partition(mol, X0)
    S = np.zeros((mol.natm, len(X0)))
    S[owner, np.arange(len(X0))] = 1.0
    # 护栏 3：one-hot 的 argmax 必须与最近邻指派逐点一致
    if not np.array_equal(S.argmax(axis=0), owner):
        sys.exit("Voronoi: one-hot 权重与 nearest_partition 不一致")
    return S


def row_from_soft(mol, X0, W0, rho0, sig0, frags, S):
    res = nlc.fragment_decomposition(X0, W0, rho0, sig0, frags, b=B, C=C,
                                     soft=S, closure_check=True)
    return res["inter"][(0, 1)] * KCAL, res["E_nl"] * KCAL


print("# 家族外分区：同一公共网格上换归属构造（Voronoi / Hirshfeld）")
print("# python %s  pyscf %s  numpy %s" % (sys.version.split()[0],
                                           pyscf.__version__, np.__version__))
print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip())
for rel in ("nlcsplit/partition.py", "nlcsplit/nlc.py", "nlcsplit/step_h_s22.py"):
    print("# sha256 %-26s = %s" % (rel, sha(os.path.join(ROOT, rel))))
print("# level = %d  b = %g  C = %g  Hirshfeld 自由原子：基态多重度/UHF/不球平均"
      % (LEVEL, B, C))
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

    fam = {}
    for s in SCHEMES:
        p = partition.partition_matrix(mol, X0, scheme=s)
        S = p / p.sum(axis=0)
        dev = np.abs(S.sum(axis=0) - 1.0).max()
        if dev > 1e-12:
            sys.exit("%s/%s: 归一化后每点和偏离 1 达 %.3e" % (name, s, dev))
        fam[s] = row_from_soft(mol, X0, W0, rho0, sig0, frags, S)

    e_fam = [fam[s][0] for s in SCHEMES]
    span_fam = max(e_fam) - min(e_fam)

    S_hir, S_hir_alt = free_atom_soft(mol, X0)
    e_hir, tot_hir = row_from_soft(mol, X0, W0, rho0, sig0, frags, S_hir)
    if S_hir_alt is not None:
        e_alt, _ = row_from_soft(mol, X0, W0, rho0, sig0, frags, S_hir_alt)
        d_alt = abs(e_hir - e_alt)
        print("   兜底敏感性：最近原子兜底 E_AB=%+.4f vs 全部原子等权兜底 %+.4f，差 %.6f"
              "（门 1e-4 kcal/mol）%s"
              % (e_hir, e_alt, d_alt, "OK" if d_alt <= 1e-4 else "**不过**"))
        if d_alt > 1e-4:
            bad.append((name, "hirshfeld-fallback", d_alt))

    S_vor = voronoi_soft(mol, X0)
    e_vor, tot_vor = row_from_soft(mol, X0, W0, rho0, sig0, frags, S_vor)

    # 对照（不计入预登记的跨度判据）：全原子等权 1/natm。
    # 它的作用是当"构造"与"权重近乎均匀"分离：若某构造的读数与这一行几乎相同，
    # 那个构造在网格上就没有真正区分原子，读数不能算它的性质。
    S_uni = np.full((mol.natm, len(X0)), 1.0 / mol.natm)
    e_uni, tot_uni = row_from_soft(mol, X0, W0, rho0, sig0, frags, S_uni)

    e_all = e_fam + [e_hir, e_vor]
    span_all = max(e_all) - min(e_all)

    for s in SCHEMES:
        print("   家族内 %-16s E_AB = %+9.4f  E_NL = %+10.4f" % (s, fam[s][0], fam[s][1]))
    print("   Voronoi(最近原子硬指派)  E_AB = %+9.4f  E_NL = %+10.4f" % (e_vor, tot_vor))
    print("   Hirshfeld(自由原子库存化) E_AB = %+9.4f  E_NL = %+10.4f" % (e_hir, tot_hir))
    print("   （对照，不计入判据）等权 1/natm E_AB = %+9.4f  E_NL = %+10.4f"
          % (e_uni, tot_uni))
    print("   → 家族内跨度 = %.4f kcal/mol（四方案，同一网格同一权重）" % span_fam)
    print("   → 含两个家族外构造的总跨度 = %.4f kcal/mol" % span_all)
    ratio = span_all / span_fam if span_fam > 0 else float("inf")
    print("   → 比值（含家族外 / 家族内） = %.2f（预登记：≤2 不许升级措辞；>10 必须按跨构造写）"
          % ratio)

    owner_near = partition.nearest_partition(mol, X0)
    if name in CENSUS and LEVEL == 1:
        res_near = nlc.fragment_decomposition(X0, W0, rho0, sig0, frags, b=B, C=C,
                                              owner=owner_near, closure_check=True)
        dev = abs(res_near["E_nl"] * KCAL - CENSUS[name])
        print("   护栏：nearest(公共网格) E_NL 与普查归档 %+.4f 之差 = %.4f（门 %.3f）%s"
              % (CENSUS[name], dev, CENSUS_TOL, "OK" if dev <= CENSUS_TOL else "**不过**"))
        if dev > CENSUS_TOL:
            bad.append((name, "census", dev))
    elif name in CENSUS:
        print("   （普查控制值是 level 1 的，本行 level=%d 不适用该门——不拿它当护栏）" % LEVEL)
    print("   （用时 %.1f s）" % (time.time() - t0))
    print()

if bad:
    print("VERDICT REFUSED —— 护栏不过：%s" % bad)
    sys.exit(1)
print("VERDICT DONE —— 数值都已打印；判读按预登记的三档，比值与其分母（家族内跨度）同时报出")
