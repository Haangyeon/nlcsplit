"""片段归属（partition）方案。

不自己实现 Becke 权重：直接取 PySCF 的 DFT 网格分区，它已经提供
两种分区核（original_becke / stratmann）与两种原子半径修正
（becke / treutler），组合出四种可辩护的归属方案。
另给一种公共网格上的『最近原子硬指派』作为对照。

每个点自带分区权重，因此 Σ_atoms ∫ = 分子积分 —— 这正是需要校验的性质。

`SCHEMES` 里只有 Becke 家族（两个开关组合出四方案）。Voronoi 与 Hirshfeld 是**构造上
不属于该家族**的归属，入口是"给定这批点上的坐标"，不是 `(becke_scheme, radii_adjust)`
这一对，所以它们进 `CROSS_FAMILY_SCHEMES`，由 `scheme_factors()` 统一分派 —— 六个方案
一个入口，但家族内那四个的既有调用点（按 `for s in SCHEMES` 遍历后喂给
`partition_matrix`）不会被塞进一个它接不住的参数。
"""
import ctypes

import numpy as np
from pyscf import lib, gto, scf
from pyscf.dft import gen_grid, radi, numint
from pyscf import dft

SCHEMES = {
    "becke":          (gen_grid.original_becke, None),
    "becke-becke-rad": (gen_grid.original_becke, radi.becke_atomic_radii_adjust),
    "becke-treutler": (gen_grid.original_becke, radi.treutler_atomic_radii_adjust),
    "stratmann":      (gen_grid.stratmann,      None),
}

# 家族外归属构造（见模块头：为什么它们不并进 SCHEMES）
CROSS_FAMILY_SCHEMES = ("voronoi", "hirshfeld")
ALL_SCHEMES = tuple(SCHEMES) + CROSS_FAMILY_SCHEMES

# 自由原子的基态多重度（Hirshfeld 的自由原子密度按这个自旋态解 UHF）
FREE_ATOM_MULT = {"H": 2, "C": 3, "N": 4, "O": 3, "F": 2}


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
    s_a(r_i)，满足 Σ_a S[i,a] = 1。

    ⚠ base_w **不是**空间测度，`Σ_i base_w_i · S[i,a] · h` 也不是 `∫ s_a h` 的近似——
    它连"差一个常数倍"都不成立，别去猜那个倍数是多少。原因是每个原子的子网格都铺到
    整个分子的 rmax，拼接点表把同一块空间重复覆盖，而重复几次取决于 h 的形态与网格档；
    又因为 Σ_a S[i,a] = 1 逐点成立，这个重复不会被子网格归一性吸收掉。

    两组实测（水二聚体 `geomlib.h2o_dimer()`，6-31g*，natm=6，ne=20，becke）：
      h = ρ（真实密度，带核尖角）：`Σ base_w·ρ` = 100.19 / 690.26 / 279.08 / 94.75
        （level 0/1/2/3），除以 20 得隐含倍率 5.01 / 34.5 / 14.0 / 4.74 —— 非单调、
        不收敛到 natm=6。同一批点上 `Σ w_pyscf·ρ` = 19.992976 / 20.000242 / 19.999990 /
        19.999996，即相对 −3.5e−4 → −2e−7 地收敛到电子数。
      h = 中心 (0,0,0.2) 的单位高斯（光滑，解析值 ∫h = pi^{3/2} = 5.568328）：
        `Σ base_w·h` = 35.874 / 33.827 / 33.308（level 1/2/3），对 natm·∫h = 33.410
        的比是 1.0738 / 1.0125 / 0.9969。只有光滑函数才勉强像"约 natm 倍"。

    软归属的正确写法是**按 owner 掩膜**，也就是只用该原子自己那批子网格点：
        ∫ s_a h  ≈  Σ_{i: owner(i)=a} base_w_i · S[i,a] · h(r_i)
    这才是 PySCF 构造网格的本意（每原子子网格带 s_owner 积分一次全空间），且带一个
    外部锚：对 a 求和必须回到 PySCF 的总权重积分。实测该和 = 5.568243 / 5.568329 /
    5.568328（level 1/2/3），逐片段值 4.536409 / 0.476582 / 0.476780 / … 在 level 2 与
    3 之间六位不变。"除以 natm"这种补丁对光滑函数按片段也偏 7–13%，对真实密度 ρ 偏
    一个量级（隐含倍率 34.5 对 natm=6），都不要用——要软归属就取 `atom_partition`
    的权重，它已带 Becke 因子，是上面那把收敛的测度。

    nlcsplit 的生产路径（step_h_s22.py、step1_validate.py、examples/check_soft_partition.py）
    用的都是 atom_partition 的权重，本包里没有任何已报道的数字建立在 base_w 的软归属上；
    唯一踩在拼接点表上做软归属的是 tests/test_fastpair_ide.py 的 soft 分支，它把同一个
    base_w 同时喂给被测方与参照方，natm 在比值里自己抵消，因此那条测试检不出这个因子。

    两条一致性断言在函数内跑，不过就抛 AssertionError，不返回"看着对"的数组：
      1) Σ_a S[i,a] == 1
      2) base_w · S[owner] == PySCF 自己的 atom_partition weights（逐点）
    第 2 条是外部锚——比对对象是 gen_grid.get_partition 的输出，不是本文件的实现。
    但它只锚 owner 那一列，锚不住上面的覆盖次数：两条边都乘同一个 base_w，比值恒等
    于 1。测度本身要靠 test_soft_attribution_owner_masked_matches_analytic_gaussian。
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


_NORM_TOL = 1e-12   # 每点权重和偏离 1 的容差；与包外家族外测量脚本同值，动它就不是同一条判据


def _check_normalized(S, scheme):
    dev = np.abs(np.asarray(S).sum(axis=0) - 1.0).max()
    if dev > _NORM_TOL:
        raise AssertionError(f"{scheme}: 归一化后每点和偏离 1 达 {dev:.3e}")


def voronoi_factors(mol, coords):
    """Voronoi：最近原子硬指派写成 one-hot 的逐点归属权重，返回 (natm, N)。

    不依赖任何密度，也不依赖 Becke 乘积因子 —— 它是"归属"这一侧最省的构造。
    护栏：one-hot 的 argmax 必须与 nearest_partition 逐点一致，否则给的不是 Voronoi。
    """
    coords = np.asarray(coords)
    owner = nearest_partition(mol, coords)
    S = np.zeros((mol.natm, len(coords)))
    S[owner, np.arange(len(coords))] = 1.0
    if not np.array_equal(S.argmax(axis=0), owner):
        raise AssertionError("voronoi: one-hot 权重与 nearest_partition 不一致")
    _check_normalized(S, "voronoi")
    return S


def hirshfeld_factors(mol, coords, basis="6-31g*", mult=None):
    """Hirshfeld / stockholder：逐点 w_A = ρ_A^free / Σ_B ρ_B^free，返回 (S, S_alt, n_zero)。

    自由原子 = 该元素基态多重度（FREE_ATOM_MULT）、UHF 密度、与复合物同基组、同一批网格点，
    **不做球平均**（与 Gaussian 默认实现的差别，按本仓规矩写在这里，不留给读者猜）。
    S_alt 仅在有点需要兜底时非 None：那是"等权兜底"的敏感性对照，不是另一个方案；
    n_zero 是自由原子密度全零（下溢）的点数，主规则对这些点按最近原子兜底。

    中心坐标与传进来的 `coords` **同为 Bohr**（2026-10-12 A 件修正）。此前这里减的是
    `mol.atom_coord(a, unit="Angstrom")`，而 PySCF 网格坐标恒为 Bohr，两个单位相减会让每个
    自由原子按 (1 − 1/BOHR)·R 整体错位、离原点越远挪得越多；那是包外家族外测量脚本的原样口径，
    本仓已归档的八格 Hirshfeld 读数就是这么来的，并进包内时曾刻意保持逐字不变。
    改成同单位之后，那几份归档**不再能逐位复现**：旧档原样保留（同目录 sidecar 注记说明），
    新读数以新档名入库；`evidence/common_grid/20261011T115335Z_*` 那份构造审计里
    "水二聚体 +Hirshfeld 增量 0.0214 → 0.0000"就是本修正的定价读数。
    """
    coords = np.asarray(coords)
    mult = FREE_ATOM_MULT if mult is None else mult
    dens = []
    ni = numint.NumInt()
    for a in range(mol.natm):
        sym = mol.atom_symbol(a)
        atm = gto.M(atom="%s 0 0 0" % sym, basis=basis, unit="Angstrom",
                    spin=mult[sym] - 1, verbose=0)
        atm.build()
        mf = scf.UHF(atm).run()
        if not mf.converged:
            raise RuntimeError("%s: 自由原子 UHF 未收敛" % sym)
        dm = mf.make_rdm1()
        # 自由原子必须落在它自己的位置上：把网格搬到以该原子为原点再取值。
        # 早先有一版把全部自由原子建在原点，权重退化成 1/natm，片间块恰好等于总量的
        # 一半 —— 那是构造错的指纹而不是物理结果，靠"恰好整齐分数"这条线索才抓到。
        rel = coords - mol.atom_coord(a)          # 与 coords 同为 Bohr（A 件修正，见函数头）
        ao = ni.eval_ao(atm, rel, deriv=1)
        rho = ni.eval_rho(atm, ao, dm, xctype="GGA")
        dens.append(np.asarray(rho[0], dtype=float))   # 只要密度分量；整块 append 会把梯度也塞进来
    W = np.vstack(dens)
    if W.shape[0] != mol.natm:
        raise ValueError("hirshfeld: 权重矩阵 %s 的行数 ≠ 原子数 %d —— 只许 append rho[0]"
                         % (W.shape, mol.natm))
    denom = W.sum(axis=0)
    zero = denom <= 0
    n_zero = int(zero.sum())
    if n_zero == 0:
        S = W / denom
        _check_normalized(S, "hirshfeld")
        return S, None, n_zero
    owner = nearest_partition(mol, coords)
    S_alt = W.copy()
    S_alt[:, zero] = 1.0 / mol.natm
    S_alt = S_alt / S_alt.sum(axis=0)
    S = W.copy()
    S[:, ~zero] = W[:, ~zero] / denom[~zero]
    S[:, zero] = 0.0
    S[owner[zero], np.arange(len(coords))[zero]] = 1.0
    _check_normalized(S, "hirshfeld")
    return S, S_alt, n_zero


def scheme_factors(mol, coords, scheme="becke", basis="6-31g*"):
    """任意归属方案（家族内四方案 + 家族外两种）在同一批点上的逐点权重 S (natm, N)。

    家族内走 `partition_matrix` 再按列归一，与包外脚本一致；家族外走各自构造函数。
    返回的 S 每点求和为 1，可直接喂给 `nlc.fragment_decomposition(soft=S)`。
    """
    if scheme in SCHEMES:
        p = partition_matrix(mol, coords, scheme)
        S = p / p.sum(axis=0)
        _check_normalized(S, scheme)
        return S
    if scheme == "voronoi":
        return voronoi_factors(mol, coords)
    if scheme == "hirshfeld":
        S, _, _ = hirshfeld_factors(mol, coords, basis=basis)
        return S
    raise KeyError(f"未知 scheme {scheme!r}，可选 {sorted(ALL_SCHEMES)}")


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
