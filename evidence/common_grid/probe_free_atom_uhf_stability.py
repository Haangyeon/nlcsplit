"""自由原子 UHF 到底在抖什么：能量抖，还是简并子空间里的占据方式抖？

为什么这条值得单独跑（几秒，不碰复合物 SCF，不抢满表批的核）：
`probe_hirshfeld_recipe_equivalence.py` 已经证明同一份代码同一批网格点跑两遍，
Hirshfeld 归属矩阵能差 1e-1 量级。但"权重不可复现"有两种病因，修法完全不同：
  A. **能量也抖**：UHF 没收敛到同一个极小点 ⇒ 收敛问题，修法是提高收敛档/给确定性初猜；
  B. **能量不抖、密度抖**：同一个能量的近简并轨道之间做了能量不变的转动 ⇒ 简并子空间的
     任意性。这不是"没收敛"，收紧收敛档也不会稳住它——真要修得改**定义**
     （对简并壳层做占据平均 / 球平均 / 用原子自然占据），而那等于换一个方案。
把这两者分开，作者才知道第 2 条出路要付多大代价；否则"加个 level_shift 试试"是瞎猜。

输出：每个元素重复 N 次，报
  - UHF 总能 的 max-min（ Ha 与 kcal/mol）
  - ⟨S²⟩ 的 max-min
  - 1-RDM 相对第一次的 max-rel 差（密度矩阵就是那个解本身，比在网格上采样 ρ 更直接）
  - 与第一次**逐元素完全相同**的重复次数（=N 就说明每次都是同一个解）
"""
import hashlib
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np                                  # noqa: E402
from pyscf import gto, scf                          # noqa: E402

from nlcsplit import partition                      # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPEATS = 5
BASIS = "6-31g*"


def atom_scf(sym, mult):
    atm = gto.M(atom="%s 0 0 0" % sym, basis=BASIS, unit="Angstrom",
                spin=mult - 1, verbose=0)
    atm.build()
    mf = scf.UHF(atm).run()
    return mf


def main():
    out = []
    def p(s=""):
        out.append(s)
        print(s)

    p("# 自由原子 UHF 稳定性探针（只看能量抖不抖 vs 密度抖不抖）")
    p("# 生成 %s  python %s  pyscf %s  numpy %s"
      % (datetime.now(timezone.utc).isoformat(), sys.version.split()[0],
         __import__("pyscf").__version__, np.__version__))
    p("# basis=%s 重复=%d 多重度表=%s（与 partition.hirshfeld_factors 同一份）"
      % (BASIS, REPEATS, partition.FREE_ATOM_MULT))
    p("# sha256 nlcsplit/partition.py = %s"
      % hashlib.sha256(open(os.path.join(ROOT, "nlcsplit", "partition.py"), "rb").read()).hexdigest())
    p()
    p("| 元素 | 重数 | ΔE 极值 (kcal/mol) | Δ⟨S²⟩ 极值 | Δ密度 相对极值 | 完全相同的解 |")
    p("|---|---|---|---|---|---|")

    worst = {"e": 0.0, "d": 0.0}
    for sym in ("H", "C", "N"):
        mult = partition.FREE_ATOM_MULT[sym]
        es, s2s, dens = [], [], []
        for _ in range(REPEATS):
            mf = atom_scf(sym, mult)
            es.append(mf.e_tot)
            s2s.append(mf.spin_square()[0])
            # 直接比 1-RDM，不再去网格上取 ρ：要问的是"每次是不是同一个解"，
            # 密度矩阵就是那个解本身，比任何采样都直接（也少一层 API 坑）。
            dens.append(np.asarray(mf.make_rdm1(), dtype=float))
        es = np.asarray(es); s2s = np.asarray(s2s); D = np.asarray(dens)
        de_ha = es.max() - es.min()
        de_kcal = de_ha * 627.5094740631
        rel = (np.abs(D - D[0]).max(axis=tuple(range(1, D.ndim)))) / max(np.abs(D[0]).max(), 1e-300)
        # 上一版这里对 axis=(1,2) 求 all，对 UHF 的 (nao,nao) 自旋块堆叠是错的轴，
        # 于是打出过 "70/5" 这种不可能的数（结论没受影响——同栏的 Δ 项是精确 0——但那一列作废）。
        identical = np.all(np.isclose(D, D[0], rtol=0, atol=0),
                           axis=tuple(range(1, D.ndim)))
        same = int(identical.sum())
        p("| %s | %d | %.3e | %.3e | %.3e | %d/%d |"
          % (sym, mult, de_kcal, s2s.max() - s2s.min(), rel.max(), same, REPEATS))
        worst["e"] = max(worst["e"], de_kcal)
        worst["d"] = max(worst["d"], float(rel.max()))

    p()
    p("# 最差：ΔE %.3e kcal/mol   Δ密度(相对) %.3e" % (worst["e"], worst["d"]))
    E_TOL, D_TOL = 1e-9, 1e-10
    if worst["e"] > E_TOL:
        p("VERDICT ENERGY_UNSTABLE —— 能量本身在抖（>%.0e kcal/mol）⇒ 是收敛问题，"
          "提高收敛档/给确定性初猜就可能修好，不必换定义。" % E_TOL)
        rc = 3
    elif worst["d"] > D_TOL:
        p("VERDICT DEGENERATE_SUBSPACE —— 能量逐位相同（≤%.0e）而密度在抖 ⇒ "
          "同一个能量的近简并轨道之间做了能量不变的转动。收紧收敛档不会稳住它；"
          "要稳定必须改**定义**（对简并壳层做占据平均/球平均/自然占据），"
          "那等于换一个新的 Hirshfeld 方案，旧读数全部作废。" % E_TOL)
        rc = 4
    else:
        p("VERDICT STABLE —— 能量与密度都复现 ⇒ 自由原子这头不是病因，回头查两份实现的其余差异。")
        rc = 0

    name = "%s_probe_free_atom_uhf_stability.out" % datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(HERE, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n# exit=%d at %s\n"
                  % (rc, datetime.now(timezone.utc).isoformat()))
    with open(path + ".rc", "w", encoding="utf-8") as f:
        f.write("%d\n" % rc)
    print("# 归档 %s rc=%d" % (os.path.relpath(path, ROOT), rc))
    return rc


if __name__ == "__main__":
    sys.exit(main())
