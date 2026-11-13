"""诊断：苯二聚体(A) 在 aug-cc-pvdz 下的 CP 分解是不是坏了。

触发这件事的是一个不该出现的数。50995 给出 sandwich 的 CCSD(T) 冻核反泊松
6-31g* = -1.4999，aug-cc-pvdz = -6.0626，只换基组就深了 4.56 kcal/mol；
而同一批里三个苯系复合物的基组移动是 0.86/1.45/1.95，三个氢键体系是 1.61/1.13/0.77。
sandwich 比它们都大 2-5 倍，且 -6.06 比文献里这个复合物的 CCSD(T)/CBS（约 -2.7）
深一倍，比同一几何上我们自己的 DFT 反泊松（-1.94）深三倍。
色散主导的复合物不该出现这种读数，所以先怀疑自己的反泊松通路。

本脚本只跑 RHF（384 AO 几秒），把四个量分开打印：
  E_dimer            二聚体真实
  E_monoA_ghost      A 在二聚体几何 + B 的鬼函数
  E_monoB_ghost      B 在二聚体几何 + A 的鬼函数
  E_monoA_iso        A 单独成分子
  E_monoB_iso        B 单独成分子
判据：BSSE = (A_ghost + B_ghost) - (A_iso + B_iso) 在 aug-cc-pVDZ 上应当是
零点几 kcal/mol 量级（弥散函数把 BSSE 压得很小）。如果它出来几 kcal/mol，
那就是通路坏了，-6.06 不能用；如果它确实很小，那 -6.06 是真的，
需要解释的是为什么这个体系对弥散函数如此敏感。
"""
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from pyscf import gto
from nlcsplit import geomlib

DATA = os.environ.get("S22DIR", "scratch/lit/s22")
BASIS = sys.argv[1] if len(sys.argv) > 1 else "aug-cc-pvdz"
atoms, frags = geomlib.s22_system("苯二聚体(A)", DATA)
syms = [s for s, _ in atoms]
coords = [list(c) for _, c in atoms]
A, B = list(frags[0]), list(frags[1])


def build(idx, ghosts):
    spec = []
    for k in idx:
        spec.append((syms[k], coords[k]))
    for k in ghosts:
        spec.append(("ghost-" + syms[k], coords[k]))
    return gto.M(atom=spec, basis=BASIS, unit="Angstrom", verbose=0, charge=0, spin=0)


def rhf(mol):
    m = mol.RHF()
    m.max_memory = 60000
    m.kernel()
    return m.e_tot


d = rhf(build(A + B, []))
ag = rhf(build(A, B))
bg = rhf(build(B, A))
ai = rhf(build(A, []))
bi = rhf(build(B, []))
K = 627.509474
print("basis = %s   nao(dimer)=%d" % (BASIS, build(A + B, []).nao))
print("  E_dimer        = %.10f" % d)
print("  E_monoA_ghost  = %.10f  (nao=%d)" % (ag, build(A, B).nao))
print("  E_monoB_ghost  = %.10f" % bg)
print("  E_monoA_iso    = %.10f  (nao=%d)" % (ai, build(A, []).nao))
print("  E_monoB_iso    = %.10f" % bi)
print("  dE_uncorr  = %+.4f kcal/mol" % ((d - ai - bi) * K))
print("  dE_CP      = %+.4f kcal/mol" % ((d - ag - bg) * K))
print("  BSSE       = %+.4f kcal/mol" % ((ag + bg - ai - bi) * K))
