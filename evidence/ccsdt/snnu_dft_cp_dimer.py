script
"""苯二聚体(A) 在 6-31g* 下的 omegaB97X-V 反泊松结合能，level 1 与 level 2 各一档。

为什么还缺这一栏。CCSD(T) 那一侧刚刚在 <CLUSTER> 算完（`evidence/ccsdt/` 的 50945：
冻核 -1.4999、全电子 -1.5851 kcal/mol），但 §3.2 的比法是"同一基组同一档位下，
泛函对参考值偏了多少"，所以配对的另一侧必须有人算：主表里苯 sandwich 只在 **level 1**
跑过反泊松，而六体系那条并列用的是 level 2。这一跑把 level 2 的那一档补上，
顺便在第七个体系上再量一次"只改网格档位"的移动。

仍不碰生产侧车：`nlcsplit/step_h_s22.py` 的输出路径写死在 nlcsplit/logs/step_h.json，
那是主表 S3 的载体，这里只 import 它的 counterpoise 函数。

阶段 0 先复现苯-甲烷 level 2 的 -1.3406（`20261002T0620Z_snnu_benzene_methane_l2.out`），
红了就说明约定/版本不是那一档，不押机时。
"""
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from pyscf import gto
from nlcsplit import geomlib, step_h_s22 as H

NAME = "苯二聚体(A)"
CC_FROZEN = -1.4999      # evidence/ccsdt/ 50945，6-31g* 冻核反泊松
CC_AE = -1.5851          # 同一次 run 的全电子档

def cp(name, lvl):
    atoms, frags = geomlib.s22_system(name, H.DATA)
    mol = gto.M(atom=[(s, c) for s, c in atoms], basis=H.BASIS, unit="Angstrom", verbose=0)
    return mol.nao, H.counterpoise(mol, frags, lvl)

# 阶段 0：守卫（跑两个档位里便宜的那个，只判 level 2 一行）
nao0, chk = cp("苯-甲烷", 2)
print("guard 苯-甲烷 level2 nao=%d DFT=%+8.4f" % (nao0, chk))
d = abs(chk - (-1.3406))
print("guard: |%.4f - (-1.3406)| = %.4f %s 0.0002 -> %s"
      % (chk, d, "<=" if d <= 0.0002 else ">", "PASS" if d <= 0.0002 else "FAIL"))
if d > 0.0002:
    print("GUARD_FAIL：不跑苯二聚体"); sys.exit(5)

for lvl in (2, 1):
    nao, dft = cp(NAME, lvl)
    print("LEVEL=%d %s nao=%d DFT=%+8.4f CCSD(T)=%+8.4f DFT-CC=%+7.3f  (AE %+7.3f -> DFT-AE %+7.3f)"
          % (lvl, NAME, nao, dft, CC_FROZEN, dft - CC_FROZEN, CC_AE, dft - CC_AE))
