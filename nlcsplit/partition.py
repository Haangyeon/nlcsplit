"""片段归属（partition）方案。

不自己实现 Becke 权重：直接取 PySCF 的 DFT 网格分区，它已经提供
两种分区核（original_becke / stratmann）与两种原子半径修正
（becke / treutler），组合出四种可辩护的归属方案。
另给一种公共网格上的『最近原子硬指派』作为对照。

每个点自带分区权重，因此 Σ_atoms ∫ = 分子积分 —— 这正是需要校验的性质。
"""
import numpy as np
from pyscf.dft import gen_grid, radi
from pyscf import dft

SCHEMES = {
    "becke":          (gen_grid.original_becke, None),
    "becke-becke-rad": (gen_grid.original_becke, radi.becke_atomic_radii_adjust),
    "becke-treutler": (gen_grid.original_becke, radi.treutler_atomic_radii_adjust),
    "stratmann":      (gen_grid.stratmann,      None),
}


def atom_partition(mol, level=3, scheme="becke"):
    """返回 (coords (N,3), weights (N,), owner (N,)int)。

    owner[i] = 第 i 个网格点归属的原子序号；weights 已含分区因子。
    """
    if scheme not in SCHEMES:
        raise KeyError(f"未知 scheme {scheme!r}，可选 {sorted(SCHEMES)}")
    becke_scheme, radii_adjust = SCHEMES[scheme]
    tab = gen_grid.gen_atomic_grids(mol, {}, level=level)
    coord_list, weight_list = gen_grid.get_partition(
        mol, tab, radii_adjust=radii_adjust, becke_scheme=becke_scheme, concat=False)
    coords = np.vstack(coord_list)
    weights = np.concatenate(weight_list)
    owner = np.concatenate([np.full(len(c), i) for i, c in enumerate(coord_list)])
    return coords, weights, owner


def nearest_partition(mol, coords):
    """在给定公共网格上做最近原子硬指派（one-hot）。返回 owner (N,) int。"""
    nuc = np.asarray(mol.atom_coords())
    d2 = ((coords[:, None, :] - nuc[None, :, :]) ** 2).sum(-1)
    return np.argmin(d2, axis=1)


def scf_grid(mol, xc="wb97x_v", level=3, basis="6-31g*"):
    """跑一个自洽场，返回 (mf, coords, weights, rho, sigma)。网格用 PySCF 常规网格。"""
    mf = dft.RKS(mol)
    mf.xc = xc
    mf.grids.level = level
    mf.kernel()
    ni = mf._numint
    coords, weights = mf.grids.coords, mf.grids.weights
    rho = ni.eval_rho(mol, ni.eval_ao(mol, coords, deriv=1), mf.make_rdm1(), xctype="GGA")
    sigma = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
    return mf, coords, weights, rho[0], sigma
