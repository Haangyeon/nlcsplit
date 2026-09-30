"""把 §2.1 那句"与独立脚本十档扫上一致到 2e-3 kcal/mol"变成有工件的主张。

被比的那一份是**别人独立写的**扫表（`evidence/agentb_sweep/`，cartesian 6-31G*，
nao=19 已在本机复现），它只有自己的数值、**没有比对列**——所以差值必须由这一份脚本
现算并归档，否则"2e-3"就是一句没有工件的话。

跑法（WSL）：PYTHONPATH=. python3 -u nlcsplit/step_l_sweep_compare.py [最高档]
"""
import json
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyscf import gto  # noqa: E402
import pyscf  # noqa: E402

from nlcsplit import geomlib, nlc, partition  # noqa: E402

KCAL = 627.5094740630563
BASIS, XC = "6-31g*", "wb97x_v"
SWEEP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "evidence", "agentb_sweep",
                     "20260928T071951Z_agentb-sweep_631gstar.txt")


def parse_sweep(path):
    """取两张表：(1) 每档重做 SCF；(2) 固定 level-9 密度只换求积。"""
    tables, cur = {}, None
    for line in open(path, encoding="utf-8"):
        head = re.match(r"== \((\d)\) (.+)", line)
        if head:
            cur = head.group(1)
            tables[cur] = {"title": head.group(2).strip(), "rows": {}}
            continue
        m = re.match(r"\s*(\d)\s+(\d+)\s+([\d.]+)\s+([+-][\d.]+)\s+([+-][\d.]+)\s+([+-][\d.]+)",
                     line)
        if m and cur:
            tables[cur]["rows"][int(m.group(1))] = dict(
                npts=int(m.group(2)), int_rho=float(m.group(3)), e_loc=float(m.group(4)),
                e_nonlocal=float(m.group(5)), e_nlc=float(m.group(6)))
    if not tables.get("1", {}).get("rows"):
        raise SystemExit(f"{path}: 没解析出表 (1)，比对无从谈起")
    return tables


def ours(mol, level):
    """同一张网格上的两条独立实现：我们的显式双重和，与 PySCF 原生核。

    必须用**同一张网格**比：atom_partition 的水单体 level 0 是 2230 点，而那份扫表是
    2216 点（它走 mf.grids）。点数不同就先把"实现差"污染成"网格差"——level 0 上
    这会造出 2.5e-2 kcal/mol 的假差。
    """
    from pyscf.dft import numint
    mf, X, W, rho, sig = partition.scf_grid(mol, xc=XC, level=level, basis=BASIS)
    assert mf.converged, f"level {level} SCF 未收敛"
    dm = mf.make_rdm1()
    b, C = mf._numint.nlc_coeff(mf.xc)[0][0]
    w0, kap, keep = nlc.vv10_fields(rho, sig, b=b, C=C)
    wr = W * rho
    idx = np.flatnonzero(keep)
    beta = (1.0 / 32.0) * (3.0 / (b * b)) ** nlc.BETA_EXP
    mine = float(nlc.pair_energy(X, wr, w0, kap, idx, idx)) + float(nlc.local_term(beta, wr))
    native = float(numint.nr_nlc_vxc(mf._numint, mol, mf.grids, XC, dm)[1])
    return dict(mine=mine, native=native, n_grid=int(len(W)), n_kept=int(idx.size),
                scf=mf.e_tot)


def main():
    top = int(sys.argv[1]) if len(sys.argv) > 1 else 9
    tables = parse_sweep(SWEEP)
    mol = gto.M(atom=geomlib.h2o(), basis=BASIS, verbose=0, unit="Angstrom", cart=True)
    assert mol.nao_cart() == 19, f"cartesian nao={mol.nao_cart()}，与被比那份不是同一套基组"
    print("== 水单体 ωB97X-V/6-31G*(cartesian)：我方显式双重和 vs 独立脚本的十档扫表 ==")
    print(f"  PySCF {pyscf.__version__}  host={os.uname().nodename}  nao={mol.nao_cart()}  "
          f"levels 0..{top}")
    print("  注：被比那份是**同库不同实现**（它也走 PySCF 的 gen_grid + 自己的双重和），"
          "不是第二个程序；第二个程序是 ORCA，见 §4。")
    print(f"\n  lvl  npts_他  npts_我   他 E_NLC(Ha)     我 E_NLC(Ha)     差(kcal/mol)"
          f"   我-原生(kcal)   保留点")
    worst = {"t1": 0.0, "t2": 0.0}
    out = {"pyscf_version": pyscf.__version__, "basis": BASIS, "xc": XC, "cartesian": True,
           "levels": {}}
    for lvl in range(top + 1):
        r = ours(mol, lvl)
        row = {}
        for tab in ("1", "2"):
            ref = tables[tab]["rows"].get(lvl)
            if ref is None:
                continue
            d = (r["mine"] - ref["e_nlc"]) * KCAL
            worst[f"t{tab}"] = max(worst[f"t{tab}"], abs(d))
            row[f"theirs_table{tab}_ha"] = ref["e_nlc"]
            row[f"diff_table{tab}_kcal"] = d
        t1 = row.get("diff_table1_kcal")
        print(f"  {lvl:>3}  {tables['1']['rows'].get(lvl, {}).get('npts', '-'):>7}  "
              f"{r['n_grid']:>8}  "
              f"{row.get('theirs_table1_ha', float('nan')):>15.9f}  {r['mine']:>15.9f}  "
              f"{t1:>+12.3e}   {abs(r['mine'] - r['native']) * KCAL:>12.3e}  {r['n_kept']:>7}")
        out["levels"][lvl] = dict(ours_mine_ha=r["mine"], ours_native_ha=r["native"],
                                  n_grid=r["n_grid"], n_kept=r["n_kept"], **row)
    print(f"\n  最坏 |差|：表(1) 自洽扫 {worst['t1']:.3e} kcal/mol，"
          f"表(2) 固定密度扫 {worst['t2']:.3e} kcal/mol")
    print("  ⇒ §2.1 的 2e-3 只有在上面这两个数之一 ≥ 它时才成立；否则正文要按实测改写。")
    side = os.path.join(os.path.dirname(SWEEP), "sweep_compare.json")
    json.dump(out, open(side, "w"), ensure_ascii=False, indent=1)
    print(f"  侧车 → {side}")


if __name__ == "__main__":
    main()
