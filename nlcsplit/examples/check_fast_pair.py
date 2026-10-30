"""快版 pair_energy 与朴素位移张量版的逐位对照 + 对 PySCF 原生核的绝对校验。"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pyscf import gto, dft
from nlcsplit import partition, nlc, geomlib


def naive(coords, wr, w0, kap, iA, iB):
    s = 0.0
    for p0 in range(0, len(iA), 64):
        ii = iA[p0:p0 + 64]
        dX = coords[ii][:, None, :] - coords[iB][None, :, :]
        R2 = np.einsum("ijk,ijk->ij", dX, dX)
        g = w0[iB][None, :] * R2 + kap[ii][:, None]
        gp = w0[ii][:, None] * R2 + kap[iB][None, :]
        phi = -3.0 / (2.0 * g * gp * (g + gp))
        s += (wr[ii][:, None] * wr[iB][None, :] * phi).sum()
    return 0.5 * s


mol = gto.M(atom=geomlib.h2o_dimer(), basis="6-31g*", verbose=0, unit="Angstrom")
mf = dft.RKS(mol); mf.xc = "wb97x_v"; mf.grids.level = 0; mf.kernel()
b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
X, W, owner = partition.atom_partition(mol, level=0, scheme="becke")
ni = mf._numint
rho = ni.eval_rho(mol, ni.eval_ao(mol, X, deriv=1), mf.make_rdm1(), xctype="GGA")
sig = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
w0, kap, keep = nlc.vv10_fields(rho[0], sig, b, C)
wr = W * rho[0]
idx = np.where(keep)[0]
fA = np.where(np.isin(owner, [0, 1, 2]) & keep)[0]
fB = np.where(np.isin(owner, [3, 4, 5]) & keep)[0]

for tag, (iA, iB) in [("full", (idx, idx)), ("cross", (fA, fB))]:
    a = naive(X, wr, w0, kap, iA, iB)                     # 朴素位移张量版，交叉配对
    c = nlc.pair_energy(X, wr, w0, kap, iA, iB, pairing="cross")
    d = nlc.pair_energy(X, wr, w0, kap, iA, iB)           # 默认 same-centre = PySCF 原生核/ORCA 约定
    print(f"{tag:6s} naiveV0={a:.17e} fastV0={c:.17e} 相对差={abs(a-c)/abs(a):.3e}  "
          f"V2(默认)={d:.17e}  V2-V0={(d-c)*627.509474:+.4f} kcal")

# 绝对校验：整份 E_NLC 必须等于 PySCF 原生核 nr_nlc_vxc（不经 libxc）
from pyscf.dft import numint
_, exc_libxc, _ = numint.nr_nlc_vxc(mf._numint, mol, mf.grids, "wb97x_v", mf.make_rdm1())
libxc_tot = float(exc_libxc)
beta = (1.0 / 32.0) * (3.0 / (b * b)) ** 0.75
mine_v2 = beta * wr.sum() + nlc.pair_energy(X, wr, w0, kap, idx, idx)
mine_v0 = beta * wr.sum() + nlc.pair_energy(X, wr, w0, kap, idx, idx, pairing="cross")
print(f"网格点数 N={len(X)}（Becke 分区，非参照网格）")
print(f"  参照核(其自有网格) E_NLC = {libxc_tot:.10f} Ha")
print(f"  我们 V2  E_NLC = {mine_v2:.10f} Ha   与 libxc 差 = {(mine_v2-libxc_tot)*627.509474:+.4f} kcal/mol")
print(f"  我们 V0  E_NLC = {mine_v0:.10f} Ha   与 libxc 差 = {(mine_v0-libxc_tot)*627.509474:+.4f} kcal/mol")
