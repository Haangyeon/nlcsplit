"""软分区分支的验证：此前所有脚本都走 owner=（硬分区），soft= 分支从未被执行过。

判据：用 PySCF 自己的 Becke 分区因子构造 soft[a]，则
  (i)  每点 Σ_a soft[a] == 1
  (ii) Σ_a intra[a] + Σ_{a<b} inter[a,b] == 同一张网格上直接的整体双重和
  (iii) 与同网格硬分区的 E_nl 一致（同一批点、同一密度，只差归属）
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pyscf import gto, dft
from nlcsplit import partition, nlc, geomlib

KCAL = 627.509474
LEVEL = 1

mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", verbose=0, unit="Angstrom")
mf, X0, W0, r00, s00 = partition.scf_grid(mol, xc="wb97x_v", level=LEVEL)
b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
X, W, owner = partition.atom_partition(mol, level=LEVEL, scheme="becke")
ni = mf._numint
rho = ni.eval_rho(mol, ni.eval_ao(mol, X, deriv=1), mf.make_rdm1(), xctype="GGA")
sig = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
wr = W * rho[0]

# 每点归属权重：one-hot 到原子，再按片段合并 —— 与硬分区等价，用来验分支本身
soft_atom = np.zeros((mol.natm, len(X)))
soft_atom[owner, np.arange(len(X))] = 1.0
frags = geomlib.FRAGS["(H2O)2"]
# fragment_decomposition 的 soft= 约定是 **(natm, N) 按原子索引**，内部再按 fragments 合并
soft_check = soft_atom.sum(0)
print(f"(i) 每点 Σ_a soft[a] 偏离 1 的最大值 = {np.abs(soft_check - 1).max():.2e}")

res_soft = nlc.fragment_decomposition(X, W, rho[0], sig, frags, b=b, C=C, soft=soft_atom)
res_hard = nlc.fragment_decomposition(X, W, rho[0], sig, frags, b=b, C=C, owner=owner)

w0, kap, keep = nlc.vv10_fields(rho[0], sig, b, C)
idx = np.where(keep)[0]
E_direct = nlc.pair_energy(X, wr, w0, kap, idx, idx)   # 0.5·ΣΣ(全部保留点) = 整份非局域项

print(f"(ii) 软: Σintra+Σinter = {res_soft['E_nl']:.12f}  直接双重和 = {E_direct:.12f}"
      f"  差 = {abs(res_soft['E_nl'] - E_direct):.2e} Ha")
print(f"     软 intra = {[round(v*KCAL,4) for v in res_soft['intra'].values()]}  "
      f"inter = {[round(v*KCAL,4) for v in res_soft['inter'].values()]} kcal/mol")
print(f"(iii) 硬: Σintra+Σinter = {res_hard['E_nl']:.12f}  与软之差 = "
      f"{abs(res_hard['E_nl'] - res_soft['E_nl']):.2e} Ha")
print(f"     E_AB 软={res_soft['inter'][(0,1)]*KCAL:+.4f}  硬={res_hard['inter'][(0,1)]*KCAL:+.4f} kcal/mol")

ok = (np.abs(soft_check - 1).max() < 1e-12
      and abs(res_soft['E_nl'] - E_direct) < 1e-10
      and abs(res_hard['E_nl'] - res_soft['E_nl']) < 1e-10)
print("\n软分区分支验收:", "PASS" if ok else "FAIL")
