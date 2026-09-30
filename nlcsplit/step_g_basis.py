"""Step 2 判据的补测：E_AB 随**基组**的走势（原判据把基组 dependence 与方案敏感性混为一谈）。

Step 2 原文要"同一种方案在 level 0→3、STO-3G→6-31G*→aug-cc-pVDZ 下 E_AB 变化 <0.05"。
这条在物理上是错的要求：片间冻结密度成对项本身就随基组变化（更 diffuse 的基组把密度
铺到片间区），相互作用能也要到 CBS 极限才稳定。所以这里分开判：
  (i)  同基组跨网格的散布 —— 网格是否收敛（已实测 <1e-3 kcal/mol）
  (ii) 同网格跨基组的走势 —— 是否朝 CBS 收敛（本脚补 def2-SVP / def2-TZVP 两档）
  (iii)同基组同网格跨归属方案的散布 —— 才是"方案敏感性"这个真正的立论对象
"""
import sys, os, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto
from pyscf.dft import numint
from nlcsplit import partition, nlc, geomlib

KCAL = 627.509474
LEVEL = int(os.environ.get("NCLV", "1"))
BASIS = (os.environ.get("NCSYS") or
         "sto-3g,6-31g*,aug-cc-pvdz,def2-svp,def2-tzvp").split(",")
SCHEMES = ["becke", "becke-becke-rad", "becke-treutler", "stratmann"]
# 几何可切换：默认走 geomlib.h2o_dimer()（构造几何，历史归档就是它）；给 NCOFF
# 指到 S22 官方几何目录，则在官方水二聚体上跑同一条阶梯——这才是 §6 那条
# "阶梯只在构造几何上"的界唯一能闭合的办法。
OFFDIR = os.environ.get("NCOFF")
if OFFDIR:
    GEOM_ATOMS, GEOM_FRAGS = geomlib.s22_system("水二聚体", OFFDIR)
    GEOM_LABEL = f"官方 S22 几何 {OFFDIR}/S22_02.xyz"
else:
    GEOM_ATOMS, GEOM_FRAGS = geomlib.h2o_dimer(), geomlib.FRAGS["(H2O)2"]
    GEOM_LABEL = "构造几何 geomlib.h2o_dimer()"


def one(basis, scheme):
    mol = gto.M(atom=GEOM_ATOMS, basis=basis, verbose=0, unit="Angstrom")
    mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc="wb97x_v", level=LEVEL, basis=basis)
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    X, W, owner = partition.atom_partition(mol, level=LEVEL, scheme=scheme)
    ao = mf._numint.eval_ao(mol, X, deriv=1)
    rho = mf._numint.eval_rho(mol, ao, mf.make_rdm1(), xctype="GGA")
    sig = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
    res = nlc.fragment_decomposition(X, W, rho[0], sig, GEOM_FRAGS, b=b, C=C, owner=owner)
    _, exc_ref, _ = numint.nr_nlc_vxc(mf._numint, mol, mf.grids, "wb97x_v", mf.make_rdm1())
    return dict(N=len(X), E_AB=res["inter"][(0, 1)], bias=res["E_total"] - exc_ref,
                ne=mol.nelectron)


def main():
    print(f"== 水二聚体 E_AB 基组阶梯（ωB97X-V，网格 level={LEVEL}，几何：{GEOM_LABEL}）==")
    print(f"{'基组':13s} {'ne':>4s} {'N':>7s} " +
          " ".join(f"{s[:14]:>15s}" for s in SCHEMES) + f" {'方案跨度':>10s} {'bias':>9s}")
    tab = {}
    for basis in BASIS:
        try:
            vals = []
            for sc in SCHEMES:
                t0 = time.time()
                r = one(basis, sc)
                vals.append(r["E_AB"] * KCAL)
                bias = r["bias"] * KCAL
                N = r["N"]
            arr = np.array(vals)
            tab[basis] = arr
            print(f"{basis:13s} {r['ne']:4d} {N:7d} " +
                  " ".join(f"{v:+15.4f}" for v in vals) +
                  f" {arr.max()-arr.min():+10.4f} {bias:+9.3f}  {time.time()-t0:4.0f}s",
                  flush=True)
        except Exception as e:
            print(f"{basis:13s} 失败 {type(e).__name__}: {str(e)[:100]}", flush=True)
    if len(tab) > 1:
        keys = list(tab)
        b0 = tab[keys[0]]
        print(f"\n  跨基组漂移（相对 {keys[0]}）：")
        for k in keys[1:]:
            d = tab[k] - b0
            print(f"    {k:13s} becke {d[0]:+.4f}   四方案 max|Δ| {np.abs(d).max():+.4f} kcal/mol")
        last = keys[-2:]
        d = tab[last[1]] - tab[last[0]]
        print(f"\n  最后两档（{last[0]}→{last[1]}）becke 漂移 = {d[0]:+.4f} kcal/mol，"
              f"四方案最大 {np.abs(d).max():+.4f}")
        print("  判据：最后两档漂移 < 0.05 ⇒ 基组已趋 CBS，剩余不确定度由方案跨度决定；"
              "否则需要再加一档（cc-pVQZ 级）才能谈 CBS。")


if __name__ == "__main__":
    main()
