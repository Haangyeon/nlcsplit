"""归档 `paper/main.md` §3.5 那句"β·N_A 恒等式"的实测表：水二聚体官方几何、level 3、
四个划分方案各自的片段布居 N_A，以及它放大成的局域项不确定度。

N_A 是**电子**布居，必须带 ρ(r)；只加体积权重得到的是格体积（这里十万量级），
所以文件里那条"Σ N_A == ne"的断言不是装饰。

跑法（WSL）：PYTHONPATH=. python3 -u nlcsplit/step_k_population.py
"""
import os
import subprocess
import sys

import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyscf import dft, gto  # noqa: E402
import pyscf  # noqa: E402

from nlcsplit import geomlib, partition, step_h_s22  # noqa: E402

BASIS, XC = "6-31g*", "wb97x_v"
LEVEL = int(sys.argv[1]) if len(sys.argv) > 1 else 3
KCAL = 627.5094740630563
SCHEMES = ("becke", "becke-becke-rad", "becke-treutler", "stratmann")


def load():
    """默认走 S22_02 官方几何；GEO=constructed 走 geomlib 自建的那套初始结构。

    第二档不是为了多一个数，是为了判定：工作日志里那张旧表格（ΔN_A = 9.865e-2）
    自称官方几何，却和官方几何的实测（1.081e-1）差 9%，所以要么几何不同要么口径不同。
    """
    if os.environ.get("GEO") == "constructed":
        atoms = geomlib.h2o_dimer()
    else:
        atoms = None
    if atoms is not None:
        mol = gto.M(atom=[(s, c) for s, c in atoms], basis=BASIS, verbose=0, unit="Angstrom")
        frags, dmin = geomlib.split_frags(atoms), None
    else:
        mol, frags, dmin = step_h_s22.build("水二聚体")
    mf = dft.RKS(mol)
    mf.xc = XC
    mf.grids.level = LEVEL
    mf.kernel()
    return mol, frags, mf, dmin


def rho_at(mol, mf, coords):
    ao = mol.eval_gto('GTOval', coords)
    return mf._numint.eval_rho(mol, ao, mf.make_rdm1(), xctype='LDA')


def per_frag(vals, owner, frags):
    """把逐点的 owner 硬指派量按片段加起来。"""
    return [float(sum(vals[owner == a].sum() for a in list(frag))) for frag in frags]


def main():
    mol, frags, mf, dmin = load()
    ne = mol.nelectron
    beta_ha = (1.0 / 32.0) * (3.0 / 6.0 ** 2) ** 0.75
    load1 = subprocess.run(['cat', '/proc/loadavg'],
                           capture_output=True, text=True).stdout.split()[0]
    print("== 水二聚体（geomlib 自建几何）β·N_A 布居表 ==" if dmin is None
          else "== 水二聚体（GMTKN55 官方几何 S22_02）β·N_A 布居表 ==")
    print(f"  PySCF {pyscf.__version__}  host={os.uname().nodename}  basis={BASIS}  xc={XC}"
          f"  level={LEVEL}  片间最短 {dmin if dmin is None else f'{dmin:.3f} A'}"
          f"  E_SCF={mf.e_tot:.10f} Ha  load1={load1}")
    print(f"  β = {beta_ha:.6f} Ha/电子 = {beta_ha * KCAL:.4f} kcal/mol/电子   N_e = {ne}")
    print("\n  scheme            N_A(硬/owner)      β·ΔN_A vs becke")
    rows = {}
    for sch in SCHEMES:
        coords, w, owner = partition.atom_partition(mol, level=LEVEL, scheme=sch)
        hard = per_frag(w * rho_at(mol, mf, coords), owner, frags)
        rows[sch] = hard
        assert abs(sum(hard) - ne) < 1e-3, f"硬指派电子数不守恒：{sum(hard)} vs {ne}"
    ref = rows["becke"][0]
    for sch in SCHEMES:
        hard = rows[sch]
        print(f"  {sch:<16} {hard[0]:9.6f}/{hard[1]:9.6f}"
              f"   {(hard[0] - ref) * beta_ha * KCAL:+9.4f} kcal/mol")
    spread = max(r[0] for r in rows.values()) - min(r[0] for r in rows.values())
    print(f"\n  片段 0 的四方案布居跨度 ΔN_A = {spread:.3e} e"
          f"  ⇒ β·ΔN_A = {spread * beta_ha * KCAL:.4f} kcal/mol")
    print(f"  片段 1 = {ne} − 片段 0，跨度与片段 0 相同（电子数守恒，恒等式而非估算）")

    # 软归属 vs owner 硬归属：同一把测度（PySCF 的分区权重 w，它满足
    # Σ_i w_i f = Σ_a ∫ s_a f = ∫ f），区别只在"整点给 owner"还是"按该点的
    # 各片因子分摊"。这一段是 main.md §2 那句"至多 8.7e-7 个电子"的出处——
    # 以前那个数只在 PROGRESS 日志里，没有工件，现在把它算出来并留档。
    print("\n  软归属 vs owner 硬归属（同网格、同密度、同测度）：")
    worst = 0.0
    for sch in SCHEMES:
        coords, w, owner = partition.atom_partition(mol, level=LEVEL, scheme=sch)
        rho = rho_at(mol, mf, coords)
        p = partition.partition_matrix(mol, coords, sch).T     # (N, natm)，与 partition_factors 同形
        S = p / p.sum(axis=1, keepdims=True)
        wr = w * rho
        hard = per_frag(wr, owner, frags)
        soft = [float((wr * S[:, list(frag)].sum(axis=1)).sum()) for frag in frags]
        # 容差与上面硬指派那条一致（1e-3）：PySCF 自己的分区权重把 ∫ρ 积到
        # 19.999996/20，这是网格的固有误差，不是软指派引入的，别拿 1e-6 卡它。
        assert abs(sum(soft) - ne) < 1e-3, f"软指派不守恒：{sum(soft)} vs {ne}"
        d = max(abs(a - b) for a, b in zip(hard, soft))
        worst = max(worst, d)
        print(f"  {sch:<16} hard N_A={hard[0]:9.6f}/{hard[1]:9.6f}"
              f"  soft N_A={soft[0]:9.6f}/{soft[1]:9.6f}  max|Δ|={d:.3e} e")
    print(f"\n  ⇒ 四方案里最大的软硬差 = {worst:.3e} 个电子"
          f"，乘 β 后 = {worst * beta_ha * KCAL:.3e} kcal/mol")
    print(f"  读法：软/硬两种读法在数值上是同一件事，差 {worst:.1e} e 远小于上一行"
          " 的方案间跨度（差若干个量级），所以它不是另一种不确定度来源。")
    print("  读法：这是**一切用 Becke 布居的分解法共有的**性质，不是本方法的贡献；"
          "差值（ΔE_NLC）里 β∫ρ 精确抵消，只有绝对片段能带上这条不确定度。")


if __name__ == "__main__":
    main()
