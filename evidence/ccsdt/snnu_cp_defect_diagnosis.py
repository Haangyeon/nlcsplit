"""决定性检查：step_m 里那栏标成 dE_CP 的数，到底是反泊松还是未校正。

做法：水二聚体 @ 6-31g*，同一套 RHF/CCSD(T) 代码，算三种单体的和：
  (a) 单体在自己的基组里、二聚体几何   —— step_m 现在用的就是这个
  (b) 单体带对方的鬼函数              —— 真正的 Boys-Bernardi
  (c) 单体各自优化几何（水二聚体里单体未形变，所以 (c) 应与 (a) 相同）
然后与归档里那个 -6.856 比。哪个对上，就说明归档那一栏是什么。
"""
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from pyscf import gto, cc as pyscf_cc
from pyscf.cc import ccsd_t as triples_mod

KCAL = 627.509474
DATA = os.environ.get("S22DIR", "scratch/lit/s22")
from nlcsplit import geomlib

atoms, frags = geomlib.s22_system("水二聚体", DATA)
syms = [s for s, _ in atoms]
xyz = [list(c) for _, c in atoms]
A, B = list(frags[0]), list(frags[1])


def mk(spec, frozen):
    m = gto.M(atom=spec, basis="6-31g*", unit="Angstrom", verbose=0)
    mf = m.RHF()
    mf.kernel()
    c = pyscf_cc.CCSD(mf)
    c.frozen = frozen
    e, t1, t2 = c.kernel()
    et = e + triples_mod.kernel(c, c.ao2mo(), t1, t2)
    return m, mf.e_tot + et


def block(idx, ghost=()):
    out = []
    for k in idx:
        out.append("%s %.10f %.10f %.10f" % (syms[k], *xyz[k]))
    for k in ghost:
        out.append("ghost-%s %.10f %.10f %.10f" % (syms[k], *xyz[k]))
    return "\n".join(out)


dim, ed = mk(block(A + B), 2)
a_own, ea_own = mk(block(A), 1)
b_own, eb_own = mk(block(B), 1)
a_g, ea_g = mk(block(A, B), 1)
b_g, eb_g = mk(block(B, A), 1)

print("nao: dimer=%d  单体(自己基组)=%d/%d  单体(带鬼)=%d/%d"
      % (dim.nao, a_own.nao, b_own.nao, a_g.nao, b_g.nao))
print("dE 未校正          = %+.4f kcal/mol" % ((ed - ea_own - eb_own) * KCAL))
print("dE 真反泊松(带鬼)  = %+.4f kcal/mol" % ((ed - ea_g - eb_g) * KCAL))
print("BSSE               = %+.4f kcal/mol" % ((ea_g + eb_g - ea_own - eb_own) * KCAL))
print("归档里 step_m 那一栏 = -6.8560   （对照：正文 DFT 反泊松 -6.129）")
