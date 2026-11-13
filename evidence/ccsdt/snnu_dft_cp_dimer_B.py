"""苯二聚体(B) 在 6-31g* 下的 omegaB97X-V 反泊松结合能，level 2 与 level 1 各一档。

为什么是它。八个体系里唯一还没有反泊松参考的就是这个几何（S22_20，平行位移的苯二聚体）。
主表有它的 dE_NLC 与归属跨度，缺的是与 CCSD(T) 并排的那一栏。

阶段 0 守卫：复现苯-甲烷 level 2 的 -1.3406（与上两次作业同一判据），红了不押机时。
"""
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from pyscf import gto
from nlcsplit import geomlib, step_h_s22 as H

NAME = "苯二聚体(B)"


def cp(name, lvl):
    atoms, frags = geomlib.s22_system(name, H.DATA)
    mol = gto.M(atom=[(s, c) for s, c in atoms], basis=H.BASIS, unit="Angstrom", verbose=0)
    return mol.nao, H.counterpoise(mol, frags, lvl)


nao0, chk = cp("苯-甲烷", 2)
print("guard 苯-甲烷 level2 nao=%d DFT=%+8.4f" % (nao0, chk))
d = abs(chk - (-1.3406))
print("guard: |%.4f - (-1.3406)| = %.4f %s 0.0002 -> %s"
      % (chk, d, "<=" if d <= 0.0002 else ">", "PASS" if d <= 0.0002 else "FAIL"))
if d > 0.0002:
    print("GUARD_FAIL：不跑苯二聚体(B)"); sys.exit(5)

for lvl in (2, 1):
    nao, dft = cp(NAME, lvl)
    print("LEVEL=%d %s nao=%d DFT=%+8.4f" % (lvl, NAME, nao, dft))
