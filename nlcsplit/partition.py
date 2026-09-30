"""片段归属（partition）方案。

不自己实现 Becke 权重：直接取 PySCF 的 DFT 网格分区，它已经提供
两种分区核（original_becke / stratmann）与两种原子半径修正
（becke / treutler），组合出四种可辩护的归属方案。
另给一种公共网格上的『最近原子硬指派』作为对照。

每个点自带分区权重，因此 Σ_atoms ∫ = 分子积分 —— 这正是需要校验的性质。
"""
import ctypes

import numpy as np
from pyscf import lib, gto
from pyscf.dft import gen_grid, radi
from pyscf import dft

SCHEMES = {
    "becke":          (gen_grid.original_becke, None),
    "becke-becke-rad": (gen_grid.original_becke, radi.becke_atomic_radii_adjust),
    "becke-treutler": (gen_grid.original_becke, radi.treutler_atomic_radii_adjust),
    "stratmann":      (gen_grid.stratmann,      None),
}


def partition_matrix(mol, coords, scheme="becke"):
    """未归一化的 Becke 乘积因子 p_a(r)：返回 (natm, N)。

    与 gen_grid.get_partition 内部的 gen_grid_partition 走**同一个**入口
    （original_becke 系列 → C 核 libdft.VXCgen_grid；stratmann → 它自己那段
    Python 循环），不是我们另写一遍公式。归一化 s_a = p_a/Σ_b p_b 由调用方做，
    所以 p 本身每点不对 1 归一，别拿它直接当权重用。
    """
    if scheme not in SCHEMES:
        raise KeyError(f"未知 scheme {scheme!r}，可选 {sorted(SCHEMES)}")
    becke_scheme, radii_adjust = SCHEMES[scheme]
    if callable(radii_adjust):
        f_radii_adjust = radii_adjust(mol, radi.BRAGG_RADII)
    else:
        f_radii_adjust = None
    atm_coords = np.asarray(mol.atom_coords(), order="C")
    atm_dist = gto.inter_distance(mol)
    coords = np.asarray(coords, order="F")
    ngrids = coords.shape[0]

    if (becke_scheme is gen_grid.original_becke
            and (radii_adjust is radi.treutler_atomic_radii_adjust
                 or radii_adjust is radi.becke_atomic_radii_adjust
                 or f_radii_adjust is None)):
        # C 快路径，与 PySCF 完全一致（含 radii 表为 NULL 的情形）
        if f_radii_adjust is None:
            p_radii_table = lib.c_null_ptr()
        else:
            f_radii_table = np.asarray([f_radii_adjust(i, j, 0)
                                        for i in range(mol.natm) for j in range(mol.natm)])
            p_radii_table = f_radii_table.ctypes.data_as(ctypes.c_void_p)
        pbecke = np.empty((mol.natm, ngrids))
        libdft = lib.load_library("libdft")
        libdft.VXCgen_grid(pbecke.ctypes.data_as(ctypes.c_void_p),
                           coords.ctypes.data_as(ctypes.c_void_p),
                           atm_coords.ctypes.data_as(ctypes.c_void_p),
                           p_radii_table,
                           ctypes.c_int(mol.natm), ctypes.c_int(ngrids))
        return pbecke

    grid_dist = np.empty((mol.natm, ngrids))
    for ia in range(mol.natm):
        dc = coords - atm_coords[ia]
        grid_dist[ia] = np.sqrt(np.einsum("ij,ij->i", dc, dc))
    pbecke = np.ones((mol.natm, ngrids))
    for i in range(mol.natm):
        for j in range(i):
            g = 1 / atm_dist[i, j] * (grid_dist[i] - grid_dist[j])
            if f_radii_adjust is not None:
                g = f_radii_adjust(i, j, g)
            g = becke_scheme(g)
            pbecke[i] *= .5 * (1 - g)
            pbecke[j] *= .5 * (1 + g)
    return pbecke


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


def partition_factors(mol, level=3, scheme="becke"):
    """逐点多中心归属因子：返回 (coords (N,3), base_w (N,), S (N,natm))。

    base_w 是各原子子网格的原始体积元（未乘任何分区因子），S[:,a] 是归一化后的
    s_a(r_i)，满足 Σ_a S[i,a] = 1。于是任一空间函数 h 的归属量为 ∫h·s_a，
    离散成 Σ_i base_w_i · S[i,a] · h(r_i) —— 这才是"软归属"，
    跟 atom_partition 的 owner 硬指派不是一回事（那个只是取了 S 的一列）。

    两条一致性断言在函数内跑，不过就抛 AssertionError，不返回"看着对"的数组：
      1) Σ_a S[i,a] == 1
      2) base_w · S[owner] == PySCF 自己的 atom_partition weights（逐点）
    第 2 条是外部锚——比对对象是 gen_grid.get_partition 的输出，不是本文件的实现。
    """
    tab = gen_grid.gen_atomic_grids(mol, {}, level=level)
    atm_coords = np.asarray(mol.atom_coords())
    coord_list, raw_list = [], []
    for ia in range(mol.natm):
        coords_a, vol = tab[mol.atom_symbol(ia)]
        coord_list.append(coords_a + atm_coords[ia])
        raw_list.append(vol)
    coords = np.vstack(coord_list)
    base_w = np.concatenate(raw_list)
    owner = np.concatenate([np.full(len(c), i) for i, c in enumerate(coord_list)])

    p = partition_matrix(mol, coords, scheme).T           # (N, natm)
    S = p / p.sum(axis=1, keepdims=True)

    err = np.abs(S.sum(axis=1) - 1.0).max()
    assert err < 1e-12, f"Σ_a s_a 未归一，最大偏差 {err:.3e}（scheme={scheme}）"

    w_ref = np.concatenate(gen_grid.get_partition(
        mol, tab, radii_adjust=SCHEMES[scheme][1], becke_scheme=SCHEMES[scheme][0],
        concat=False)[1])
    soft = base_w * S[np.arange(len(owner)), owner]
    # 分母用 base_w 不用 w_ref：stratmann 的因子在 |g|>0.64 处饱和成精确 0/1，
    # 会留下 w_ref~1e-16 的点，拿它当分母得到的"相对差"毫无意义。
    rel = np.abs(soft - w_ref) / base_w
    assert rel.max() < 1e-12, (f"owner 列复现不出 PySCF 的 partition 权重，"
                               f"最大相对差 {rel.max():.3e}（scheme={scheme}）")
    gl = np.abs(soft - w_ref).sum() / base_w.sum()
    assert gl < 1e-13, f"逐点误差按总权累积到 {gl:.3e}（scheme={scheme}）"
    return coords, base_w, S


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
