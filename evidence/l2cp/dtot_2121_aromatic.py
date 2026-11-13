"""五个芳香体系在 PySCF 2.12.1 下的未校正 ΔE_int（level 2），把 BSSE 差到同一个环境里。

为什么还缺这一份。§3.1 那句"六个体系的 BSSE 是 1.663 / 1.438 / 0.285 与 1.074 / 0.706 / 0.439"
里，前三个数现在两个端点都在 2.12.1 的同一份归档里（`evidence/l2cp/20261003T0907Z_...`），
后三个数的反泊松端在 <CLUSTER> 2.12.1，而**未校正那一端**仍取自 2026-09-28 的 CentOS 批次
（PySCF 2.14.0）。正文当时写的挡箭牌是"未校正值对版本不敏感，两版本差 ≤1e-6 kcal/mol"——
那句话是水/氨/甲烷六格实测出来的（`cp_version_probe.py`），拿它去给苯系那一格担保，是借来的
证据，不是量到的。这一份把那三个数（以及两个苯二聚体，顺带）在本环境补量掉，之后
BSSE 的每个端点都有自己环境的原件。

只算 SCF 能量差，不做归属分解（那是 step_h_s22.one() 的贵的那一半）：
ΔE_int = E(复合物) − ΣE(单体)，三者都在同一 level、同一基组、同一几何下，单体不带鬼函数。
"""
import os
import sys
import time

sys.path.insert(0, os.path.abspath("."))
from pyscf import gto, dft                                    # noqa: E402
import pyscf                                                   # noqa: E402
from nlcsplit import geomlib                                   # noqa: E402
from nlcsplit import step_h_s22 as H                           # noqa: E402

AROMATIC = ("苯-水", "苯-氨", "苯-甲烷", "苯二聚体(A)", "苯二聚体(B)")
LEVEL = int(os.environ.get("NCLV", "2"))


def scf(atoms, basis, level):
    mol = gto.M(atom=[(s, c) for s, c in atoms], basis=basis, unit="Angstrom", verbose=0)
    mf = dft.RKS(mol)
    mf.xc = "wb97x_v"
    mf.grids.level = level
    mf.kernel()
    assert mf.converged, "SCF 未收敛"
    return mol, mf.e_tot


def main():
    print("== 未校正 ΔE_int，PySCF %s / python %s / level %d ==" %
          (pyscf.__version__, sys.version.split()[0], LEVEL))
    print("   几何 %s  基组 6-31g*  OMP=%s" % (H.DATA, os.environ.get("OMP_NUM_THREADS")))
    for name in AROMATIC:
        atoms, frags = geomlib.s22_system(name, H.DATA)
        t0 = time.time()
        mol, e_dim = scf(atoms, "6-31g*", LEVEL)
        tot = 0.0
        for f in frags:
            sub_atoms = [atoms[i] for i in f]
            _, e = scf(sub_atoms, "6-31g*", LEVEL)
            tot += e
        dtot = (e_dim - tot) * H.KCAL
        print("  %-10s nao=%3d 原子=%2d  ΔE_int(level %d, 未校正)=%+.6f  %.0fs"
              % (name, mol.nao, mol.natm, LEVEL, dtot, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
