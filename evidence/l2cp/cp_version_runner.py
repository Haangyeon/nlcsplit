"""三个小二聚体的 omegaB97X-V 反泊松结合能在 PySCF 2.12.1 下的单环境重算（level 1 与 2）。

为什么要跑这一份。§3.2 偏差表的八行 DFT 列里，五行的来源是 <CLUSTER> 的 PySCF 2.12.1
（`evidence/ccsdt/20261002T0528Z_snnu_benzene_dft_cp.out:12` 写明 Python 3.10.19 / PySCF 2.12.1），
而水/氨/甲烷那三行来自 2026-09-28 的 CentOS 批次，那一台是 PySCF **2.14.0**
（`paper/notes/gaps_and_figures.md` 第 7 条把这两个版本记为同一件事的两端：苯-甲烷 level-2
反泊松 -1.202 @2.14.0 对 -1.341 @2.12.1）。也就是说这张表此前把两个 PySCF 版本的数并排比。

这一份把三行搬到 2.12.1 上，与其余五行、与表 1 的侧车（`nlcsplit/logs/step_h.json`，
host <OPERATOR> / pyscf 2.12.1）同环境。旧值不删除：跨版本的差要作为实测数字进正文，
它正是本文一直主张的"反泊松量对实现细节敏感"的最新一例。

顺带记录网格点数。同一 level 下 2.14.0 与 2.12.1 给出的复合物网格点数不同（水：43904 对
38944），而 E_xc/E_NLC/E_coul 到打印位一致——所以漂移落在带鬼函数的单体那一侧。这里把
复合物、裸单体、鬼单体三者的点数与 e_tot 都打出来，是为了让这个说法有本文件里的依据，
而不是只有一句推断。

刻意不覆盖生产侧车：step_h_s22.py 的 main() 写死输出到 nlcsplit/logs/step_h.json，这里只
调它的 counterpoise()，不落 JSON。
"""
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from pyscf import gto, dft                                    # noqa: E402
import pyscf                                                   # noqa: E402
from nlcsplit import geomlib                                   # noqa: E402
from nlcsplit import step_h_s22 as H                           # noqa: E402

SMALL = ("水二聚体", "氨二聚体", "甲烷二聚体")


def grid_count(mol, level):
    g = dft.gen_grid.Grids(mol)
    g.level = level
    g.build()
    return len(g.coords)


def scf(mol, level):
    mf = dft.RKS(mol)
    mf.xc = "wb97x_v"
    mf.grids.level = level
    mf.kernel()
    assert mf.converged, "诊断 SCF 未收敛"
    return mf.e_tot


def parts(name, basis, level):
    """复合物 / 裸单体 / 鬼单体的网格点数与 e_tot。

    鬼单体用与 step_h_s22.counterpoise() 完全相同的写法（ghost- 前缀、同样的 Bohr->Angstrom
    十位精度、同样的 unit），并且最后拿 counterpoise() 自己的返回值做交叉比对；对不上就
    说明下面这些点数不是生产那条式子的点数。
    """
    atoms, frags = geomlib.s22_system(name, H.DATA)
    mol = gto.M(atom=[(s, c) for s, c in atoms], basis=basis, unit="Angstrom", verbose=0)
    C = mol.atom_coords() / 1.8897261254
    sym = [mol.atom_symbol(i) for i in range(mol.natm)]

    def build(idx, ghost_idx):
        lines = [f"{sym[i]} {C[i][0]:.10f} {C[i][1]:.10f} {C[i][2]:.10f}" for i in idx]
        lines += [f"ghost-{sym[i]} {C[i][0]:.10f} {C[i][1]:.10f} {C[i][2]:.10f}"
                  for i in ghost_idx]
        return gto.M(atom="\n".join(lines), basis=basis, verbose=0, unit="Angstrom")

    e_dim = scf(mol, level)
    allidx = set(range(mol.natm))
    bare, ghosted = [], []
    for f in frags:
        b = build(f, [])
        bare.append((grid_count(b, level), scf(b, level)))
        g = build(f, sorted(allidx - set(f)))
        assert g.nao_nr() == mol.nao_nr(), "鬼单体基组维数与复合物不一致"
        assert g.nelectron < mol.nelectron, "鬼单体电子数没减少"
        ghosted.append((grid_count(g, level), scf(g, level), g.nao_nr(), g.nelectron))
    diag = (e_dim - sum(x[1] for x in ghosted)) * H.KCAL
    return mol, frags, {"n_complex": grid_count(mol, level), "e_dim": e_dim,
                        "bare": bare, "ghost": ghosted, "dcp_diag": diag}


def main():
    print("== 单环境（本机 PySCF %s / python %s）重算反泊松列，几何 %s =="
          % (pyscf.__version__, sys.version.split()[0], H.DATA))
    print("   module BASIS=%s  OMP_NUM_THREADS=%s" % (H.BASIS, os.environ.get("OMP_NUM_THREADS")))
    for basis in ("6-31g*",):
        for level in (1, 2):
            print("== BASIS=%s LEVEL=%d ==" % (basis, level))
            for name in SMALL:
                mol, frags, o = parts(name, basis, level)
                d = H.counterpoise(mol, frags, level)
                print("  %-8s nao=%3d  dcp(生产)=%+.6f  dcp(诊断)=%+.6f  差=%.1e"
                      % (name, mol.nao, d, o["dcp_diag"], abs(d - o["dcp_diag"])))
                print("      网格点数 复合物=%6d  裸单体=%s  鬼单体=%s"
                      % (o["n_complex"], [b[0] for b in o["bare"]],
                         [g[0] for g in o["ghost"]]))
                print("      e_tot    复合物%+.10f  裸单体和%+.10f  鬼单体和%+.10f  "
                      "未校正ΔE_int=%+.6f"
                      % (o["e_dim"], sum(b[1] for b in o["bare"]),
                         sum(g[1] for g in o["ghost"]),
                         (o["e_dim"] - sum(b[1] for b in o["bare"])) * H.KCAL))
                sys.stdout.flush()


if __name__ == "__main__":
    main()
