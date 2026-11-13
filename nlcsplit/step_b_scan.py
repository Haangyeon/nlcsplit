"""(b) VV10 核偏差 + 片段分解，跨体系扫描。

参照实现是 PySCF 原生 C 核 libdft.VXC_vv10nlc（nr_nlc_vxc 不经 libxc，
libxc 只管半局域那部分）；下面列名沿用 "libxc" 是历史称呼，正式表里要改成 "pyscf核"。

每个体系给出四个量（kcal/mol）：
  exact   本包的显式双重和 E_NLC = β∫ρdr + 1/2∬ρρΦ
  libxc   PySCF 原生 _vv10nlc 的加速值（列名为历史称呼，非 libxc 本尊）
  bias    exact - 参照；若随网格不消失即为两套核实现之间的系统差
  E_AB    冻密度片间成对项 2·Σ_{i∈A,j∈B}（仅二聚体；pair_energy 返回半份，此处乘 2）
  dE_NLC  超位置差 E_NLC(复合物) - Σ E_NLC(单体@复合物几何)（仅二聚体）
"""
import sys, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto
from pyscf.dft import numint
from nlcsplit import partition, nlc, geomlib

KCAL = 627.509474
BASIS_PREF = ["6-31g*", "cc-pvdz"]
LEVELS = [0, 1]
BETA = lambda b: (1.0 / 32.0) * (3.0 / (b * b)) ** 0.75


def build(name):
    last = None
    for b in BASIS_PREF:
        try:
            return gto.M(atom=geomlib.SYSTEMS[name](), basis=b, verbose=0, unit="Angstrom"), b
        except Exception as e:
            last = e
    raise RuntimeError(f"{name} 无可用基组 {BASIS_PREF}: {last}")


def exact_nlc(mol, dm, basis, level, b, C):
    """返回 (E_tot, E_loc, E_nl, coords, weights, rho, sig, keep, owner)。"""
    X, W, owner = partition.atom_partition(mol, level=level, scheme="becke")
    ao = numint.NumInt().eval_ao(mol, X, deriv=1)
    rho = numint.NumInt().eval_rho(mol, ao, dm, xctype="GGA")
    r0, sig = rho[0], rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
    w0, kap, keep = nlc.vv10_fields(r0, sig, b, C)
    wr = W * r0
    idx = np.where(keep)[0]
    E_loc = BETA(b) * wr.sum()
    E_nl = nlc.pair_energy(X, wr, w0, kap, idx, idx)
    return E_loc + E_nl, E_loc, E_nl, (X, W, r0, sig, keep, owner, w0, kap, wr)


def run_one(name, level):
    mol, basis = build(name)
    mf, Xc, Wc, r0c, s0c = partition.scf_grid(mol, xc="wb97x_v", level=level, basis=basis)
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    dm = mf.make_rdm1()
    _, exc_libxc, _ = numint.nr_nlc_vxc(mf._numint, mol, mf.grids, "wb97x_v", dm)
    t0 = time.time()
    E_tot, E_loc, E_nl, pack = exact_nlc(mol, dm, basis, level, b, C)
    X, W, r0, sig, keep, owner, w0, kap, wr = pack

    # 同一密度在 PySCF 常规网格上用显式双重和再算一遍：应与之吻合（检验网格表示无关性）
    w0c, kapc, keepc = nlc.vv10_fields(r0c, s0c, b, C)
    wrc = Wc * r0c
    ic = np.where(keepc)[0]
    E_common = BETA(b) * wrc.sum() + nlc.pair_energy(Xc, wrc, w0c, kapc, ic, ic)

    frags = geomlib.FRAGS.get(name)
    E_AB, dE = float("nan"), float("nan")
    if frags:
        idx_of = [np.where(np.isin(owner, f) & keep)[0] for f in frags]
        E_AB = 2.0 * nlc.pair_energy(X, wr, w0, kap, idx_of[0], idx_of[1])
        dE = E_common
        for f in frags:
            sub = gto.M(atom=[(mol.atom_symbol(i), mol.atom_coord(i)) for i in f],
                        basis=basis, verbose=0, unit="Bohr")
            mfs, Xs, Ws, rs, ss = partition.scf_grid(sub, xc="wb97x_v", level=level, basis=basis)
            w0s, kaps, ks = nlc.vv10_fields(rs, ss, b, C)
            wrs = Ws * rs
            isx = np.where(ks)[0]
            dE -= BETA(b) * wrs.sum() + nlc.pair_energy(Xs, wrs, w0s, kaps, isx, isx)

    fmt = lambda v: f"{v*KCAL:+9.4f}" if v == v else "      n/a  "
    print(f"{name:10s} {basis:8s} lvl={level} ne={mol.nelectron:3d} N={len(X):6d} "
          f"exact={fmt(E_tot)} libxc={fmt(exc_libxc)} bias={fmt(E_tot-exc_libxc)} "
          f"公共网格={fmt(E_common)} 表示差={fmt(E_tot-E_common)} "
          f"E_AB={fmt(E_AB)} dE_NLC={fmt(dE)}  {time.time()-t0:5.1f}s", flush=True)
    return dict(name=name, level=level, exact=E_tot, libxc=exc_libxc, E_AB=E_AB, dE=dE,
                common=E_common)


def main():
    names = os.environ.get("NLCSYS", "").split(",") if os.environ.get("NLCSYS") else \
        ["He", "Ne", "Ar", "H2O", "NH3", "CH4", "benzene", "(H2O)2", "(C6H6)2"]
    levels = [int(x) for x in os.environ.get("NCLV", "").split(",")] \
        if os.environ.get("NCLV") else LEVELS
    rows = []
    for name in names:
        for lv in levels:
            if name == "(C6H6)2" and lv > 0:
                continue   # 显式双重和是 O(N²)：level>0 的苯二聚体在本机不可行
            try:
                rows.append(run_one(name, lv))
            except Exception as e:
                import traceback
                print(f"{name} lvl={lv} 失败: {type(e).__name__}: {str(e)[:150]}", flush=True)
                traceback.print_exc()
    print("\n===== 汇总 =====")
    print(f"{'体系':10s} {'lvl':4s} {'bias(exact-参照核)':>18s} {'网格表示差':>14s} {'E_AB':>10s} {'dE_NLC':>10s}")
    for r in rows:
        print(f"{r['name']:10s} {r['level']:<4d} {(r['exact']-r['libxc'])*KCAL:+18.4f} "
              f"{(r['exact']-r['common'])*KCAL:+14.4f} "
              f"{(r['E_AB']*KCAL if r['E_AB']==r['E_AB'] else float('nan')):+10.4f} "
              f"{(r['dE']*KCAL if r['dE']==r['dE'] else float('nan')):+10.4f}")


if __name__ == "__main__":
    main()
