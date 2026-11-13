"""补 6-31g* level 2 下苯-甲烷的 omegaB97X-V 反泊松结合能。

前一次作业（50938）在 30 分钟上限处被切，level 2 只剩苯-水与苯-氨两行；这一份只补第三行，
使 §3.2 那六个体系落在同一档位、同一约定上可比。仍不碰 step_h 的生产侧车。
"""
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from pyscf import gto
from nlcsplit import geomlib, step_h_s22 as H

NAME, REF = "苯-甲烷", -1.0583   # CCSD(T)/6-31g* 冻核反泊松，evidence/ccsdt/20261002T043400Z
atoms, frags = geomlib.s22_system(NAME, H.DATA)
mol = gto.M(atom=[(s, c) for s, c in atoms], basis=H.BASIS, unit="Angstrom", verbose=0)
for lvl in (2, 1):
    d = H.counterpoise(mol, frags, lvl)
    print("LEVEL=%d %s nao=%d DFT=%+8.4f CCSD(T)=%+8.4f DFT-CC=%+7.3f" % (lvl, NAME, mol.nao, d, REF, d - REF))
