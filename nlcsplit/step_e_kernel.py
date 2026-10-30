"""核函数写法判别：把 Φ 的候选定义逐个与参照核在同一张网格上对比。

参照 = PySCF 原生 libdft.VXC_vv10nlc（nr_nlc_vxc 不经 libxc）。

背景：IDE 在 ref/h2o_wb97xv.out 里找到 ORCA 6.0.1 的独立 NL Energy，与 PySCF 原生核差 6e-4
kcal/mol，而我们的显式双重和高出 +0.14（水）～+0.91（苯）kcal/mol ⇒ 错在我们这边。
`step_b_scan.py` 的"公共网格"列已排除网格与密度：同一份密度、同一张 PySCF 网格上，
我的核仍然比参照核高 +0.138。所以差异在 Φ 的写法里。

候选（全部只在同一网格、同一密度上比 E_loc + E_nl 的总和）：
  V0 现状    g = w0_j R² + κ_i , g' = w0_i R² + κ_j , κ = b(3π/2)(ρ/9π)^{1/6}
  V1 交换    g = w0_i R² + κ_j , g' = w0_j R² + κ_i
  V2 同点    g = w0_i R² + κ_i , g' = w0_j R² + κ_j
  V3 κ 系数  κ = b(3π²/2)^{1/3} ρ^{1/6}（配 V0 的配对）
  V4 κ 系数2 κ = b(3π²)^{1/3} ρ^{1/6}（配 V0 的配对）
"""
import sys, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto
from pyscf.dft import numint
from nlcsplit import partition, nlc, geomlib

KCAL = 627.509474
PI = np.pi


def kernel_total(X, wr, w0, kap, block=256, pair="V0"):
    n = len(X)
    r2 = np.einsum("ij,ij->i", X, X)
    s = 0.0
    for p0 in range(0, n, block):
        sl = slice(p0, min(p0 + block, n))
        R2 = r2[sl][:, None] + r2[None, :] - 2.0 * (X[sl] @ X.T)
        np.maximum(R2, 0.0, out=R2)
        wi, wj = w0[sl][:, None], w0[None, :]
        ki, kj = kap[sl][:, None], kap[None, :]
        if pair == "V0":
            g, gp = wj * R2 + ki, wi * R2 + kj
        elif pair == "V1":
            g, gp = wi * R2 + kj, wj * R2 + ki
        elif pair == "V2":
            g, gp = wi * R2 + ki, wj * R2 + kj
        phi = -1.5 / (g * gp * (g + gp))
        phi *= wr[None, :]
        s += float(np.dot(phi.sum(axis=1), wr[sl]))
    return 0.5 * s


def run(name, level=1):
    mol = gto.M(atom=geomlib.SYSTEMS[name](), basis="6-31g*", verbose=0, unit="Angstrom")
    mf, X, W, rho, sig = partition.scf_grid(mol, xc="wb97x_v", level=level)
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    beta = (1.0 / 32.0) * (3.0 / (b * b)) ** 0.75
    wr = W * rho
    _, exc_ref, _ = numint.nr_nlc_vxc(mf._numint, mol, mf.grids, "wb97x_v", mf.make_rdm1())
    w0, _, keep = nlc.vv10_fields(rho, sig, b, C)
    loc = beta * wr.sum()
    kapA = b * (1.5 * PI) * (rho / (9.0 * PI)) ** (1.0 / 6.0)          # 现状
    kapB = b * (1.5 * PI * PI) ** (1.0 / 3.0) * rho ** (1.0 / 6.0)     # (3π²/2)^{1/3}
    kapC = b * (3.0 * PI * PI) ** (1.0 / 3.0) * rho ** (1.0 / 6.0)
    print(f"\n{name}  N={len(X)}  参照核总={exc_ref*KCAL:+.4f}  E_loc={loc*KCAL:+.4f} kcal/mol")
    for tag, kap, pair in [("V0 现状", kapA, "V0"), ("V1 交换", kapA, "V1"),
                           ("V2 同点", kapA, "V2"), ("V3 κ=(3π²/2)^1/3", kapB, "V0"),
                           ("V4 κ=(3π²)^1/3", kapC, "V0")]:
        t0 = time.time()
        e = loc + kernel_total(X, wr, w0, kap, pair=pair)
        print(f"   {tag:20s} 总={e*KCAL:+.4f}  与参照核差={(e-exc_ref)*KCAL:+.4f}  "
              f"相对={abs(e-exc_ref)/abs(exc_ref)*100:.3f}%   {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    # 偏差不等网格收敛（step_b 已证），所以大分子用低 level 换可算性
    for nm, lv in [("H2O", 1), ("Ar", 1), ("CH4", 1), ("benzene", 0)]:
        run(nm, lv)
