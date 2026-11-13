"""三个苯系复合物在 6-31g* 下的 omegaB97X-V 反泊松结合能，level 1 与 level 2 各一档。

为什么不直接跑 step_h_s22.py：它把输出写死到 nlcsplit/logs/step_h.json，那是主表 S3 的
生产侧车 —— 为三个数覆盖一份已发表归档不可接受。这里只借用它的 counterpoise()。
"""
import os, sys
sys.path.insert(0, os.path.abspath("."))
from pyscf import gto
from nlcsplit import geomlib
from nlcsplit import step_h_s22 as H

CC = {"苯-水": -3.6536, "苯-氨": -2.2737, "苯-甲烷": -1.0583}   # evidence/ccsdt/20261002T043400Z
for lvl in (1, 2):
    print("== %s  LEVEL=%d  OMP=%s ==" % (H.BASIS, lvl, os.environ.get("OMP_NUM_THREADS")))
    for name, ref in CC.items():
        atoms, frags = geomlib.s22_system(name, H.DATA)
        mol = gto.M(atom=[(s, c) for s, c in atoms], basis=H.BASIS, unit="Angstrom", verbose=0)
        d = H.counterpoise(mol, frags, lvl)
        print("  %-8s nao=%3d  DFT=%+8.4f  CCSD(T)=%+8.4f  DFT-CC=%+7.3f" % (name, mol.nao, d, ref, d - ref))
