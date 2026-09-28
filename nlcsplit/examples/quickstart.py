import os, sys
# 从源码树直接跑时无需 pip install；已 `pip install .` 的话这行是空操作
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pyscf import gto
from nlcsplit import partition, nlc, geomlib

mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", unit="Angstrom", verbose=0)
mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc="wb97x_v", level=1, basis="6-31g*")
b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]

coords, weights, owner = partition.atom_partition(mol, level=1, scheme="becke")
ao = mf._numint.eval_ao(mol, coords, deriv=1)
rho = mf._numint.eval_rho(mol, ao, mf.make_rdm1(), xctype="GGA")
sigma = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2

res = nlc.fragment_decomposition(coords, weights, rho[0], sigma,
                                 geomlib.FRAGS["(H2O)2"], b=b, C=C, owner=owner)
K = 627.509474
print("inter[(0,1)] = %.4f kcal/mol" % (res["inter"][(0, 1)] * K))
print("intra        = %.4f %.4f" % tuple(v * K for v in res["intra"].values()))
print("E_nl         = %.4f   E_loc = %.4f   E_total = %.4f"
      % (res["E_nl"] * K, res["E_loc"] * K, res["E_total"] * K))
