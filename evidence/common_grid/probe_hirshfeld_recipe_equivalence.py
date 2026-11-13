"""决定性对照：包内 `partition.hirshfeld_factors` 与包外脚本 `free_atom_soft`
对**同一套网格坐标**给出的 Hirshfeld 归属矩阵是不是同一份。

为什么这个对照不用跑复合物 SCF：两条路的差别如果在"自由原子怎么建、权重怎么归一、
零密度点怎么兜底"，那它跟复合物密度无关——只需要同一批网格点坐标。
PySCF 的 `dft.gen_grid.Grids.build()` 不需求解波函数就能给出 coords，
于是这条对照是秒级、且不跟正在跑的满表批抢核。

为什么必须做：苯-氨/苯-甲烷两格里，两条路的 `E_AB` 差 0.0130 / 0.0093，
而**同一格内** `E_NL` 与五列确定性方案逐字相同 ⇒ 差异只在权重构造。
两种病因不能靠"看两份实现差多少"分开，所以这里**先让每份实现跟自己比**：
  (ii) 某一份自己就不可复现（自由原子 UHF 近简并每次收敛到不同解）⇒ rc=3 NOT_REPRODUCIBLE；
  (i) 两份各自都自复现、互比仍有差 ⇒ 那才是实现分叉 ⇒ rc=1 IMPLEMENTATIONS_DIFFER；
  两者都过 ⇒ rc=0 IDENTICAL。
第一版只测互比就下了"实现分叉"的结论，被自己抓回来一次：同一份代码跑两遍，
归属矩阵能差到 1e-1 量级——那种时候"两份实现差多少"根本没有意义。
"""
import importlib.util
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from nlcsplit import partition                   # noqa: E402
from nlcsplit.step_h_s22 import build            # noqa: E402  两条生产路用的就是它


def load_script_impl():
    """只把包外脚本里的 `free_atom_soft` 函数取出来执行，不 import 整个模块。

    这不是洁癖：`hirshfeld_crossfamily.py` 是**从头跑到尾的驱动脚本**，
    没有 `if __name__ == "__main__"` 保护（第 150 行起就在打 sha、第 159 行起就 `build(name)` 开算）。
    直接 import 它会当场启动一次多小时的计算，还会跟正在跑的满表批抢核。
    所以用 ast 抠出目标函数的源码单独编译——顺手把模块的 import 行也执行，保证它引用的名字都在。
    """
    import ast
    import re
    src = open(os.path.join(HERE, "hirshfeld_crossfamily.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    want = {"free_atom_soft"}
    segs = [ast.get_source_segment(src, n) for n in tree.body
            if isinstance(n, (ast.FunctionDef,)) and n.name in want]
    if len(segs) != 1 or segs[0] is None:
        raise RuntimeError("没能在包外脚本里唯一定位 free_atom_soft：找到 %d 段" % len(segs))
    header = "\n".join(l for l in src.splitlines()
                       if re.match(r"^(import |from \S+ import )", l))
    ns = {}
    exec(compile(header, "<imports>", "exec"), ns)
    # 函数体还引用模块级常量（这里叫 `MULT`，包内那份叫 `FREE_ATOM_MULT`）——
    # 名字不同本身就是值得看的线索，所以先把**字面量赋值**按原顺序补进命名空间，
    # 不执行任何非字面量的顶层语句（那才是会触发计算的部分）。
    lits = 0
    for n in tree.body:
        if isinstance(n, ast.Assign) and isinstance(
                n.value, (ast.Constant, ast.Dict, ast.List, ast.Tuple, ast.Set)):
            exec(compile(ast.Module([n], []), "<literal>", "exec"), ns)
            lits += 1
        elif isinstance(n, ast.AnnAssign) and isinstance(
                n.value, (ast.Constant, ast.Dict, ast.List, ast.Tuple, ast.Set)):
            exec(compile(ast.Module([n], []), "<literal>", "exec"), ns)
            lits += 1
    print("# 包外脚本顶层字面量常量补入 %d 条；它的多重度表叫 %s" % (
        lits, "MULT" if "MULT" in ns else "（没有 MULT）"))
    exec(compile(segs[0], "<free_atom_soft>", "exec"), ns)
    return type("Shim", (), {"free_atom_soft": ns["free_atom_soft"]})


def main():
    import pyscf
    from pyscf import dft
    print("# Hirshfeld 两份实现的等价对照（只建网格，不跑复合物 SCF）")
    # 线程数必须打进抬头：这条对照的结论完全取决于它（1 线程时两份实现逐位相同，
    # 2 线程时同一份实现自差可达 1e-1）。不记环境的话，两份档互相矛盾而没人知道为什么——
    # 这正是本仓这两天反复在修的那类"缺元数据的绿"。
    print("# 线程环境 OMP=%s OPENBLAS=%s MKL=%s"
          % (os.environ.get("OMP_NUM_THREADS", "(未设)"),
             os.environ.get("OPENBLAS_NUM_THREADS", "(未设)"),
             os.environ.get("MKL_NUM_THREADS", "(未设)")))
    print("# python %s  pyscf %s  numpy %s"
          % (sys.version.split()[0], pyscf.__version__, np.__version__))
    print("# sha256 nlcsplit/partition.py = %s"
          % __import__("hashlib").sha256(
              open(os.path.join(ROOT, "nlcsplit", "partition.py"), "rb").read()).hexdigest())
    mol, frags, dmin = build("苯-氨")
    g = dft.gen_grid.Grids(mol)
    g.level = 1
    g.build()
    X0 = g.coords
    print("# 体系 苯-氨  原子 %d  片段 %d  片间最短 %.2f A  网格点 %d（level 1，不跑复合物 SCF）"
          % (mol.natm, len(frags), dmin, len(X0)))

    pkg_S, pkg_Salt, pkg_nzero = partition.hirshfeld_factors(mol, X0)
    mod = load_script_impl()
    script_out = mod.free_atom_soft(mol, X0)
    scr_S = script_out[0] if isinstance(script_out, (tuple, list)) else script_out
    pkg = np.asarray(pkg_S, dtype=float)
    scr = np.asarray(scr_S, dtype=float)

    # 关键一步（第一版缺）：同一份实现**再算一遍**，跟自己比。
    # 只比"包内 vs 包外"会把两种完全不同的病因混成一个数字。
    pkg2_S, _, pkg2_nzero = partition.hirshfeld_factors(mol, X0)
    pkg2 = np.asarray(pkg2_S, dtype=float)
    scr2 = np.asarray(mod.free_atom_soft(mol, X0)[0], dtype=float)
    d_self_pkg = np.abs(pkg - pkg2).max()
    d_self_scr = np.abs(scr - scr2).max()
    print("# 返回元数：包内 3（n_zero=%s / 第二次 n_zero=%s）vs 包外 2"
          % (pkg_nzero, pkg2_nzero))
    print("# 自比 max|ΔS|：包内两次 = %.3e   包外两次 = %.3e" % (d_self_pkg, d_self_scr))
    print("# 互比 max|ΔS| = %.3e   均值 = %.3e"
          % (np.abs(pkg - scr).max(), np.abs(pkg - scr).mean()))
    # 零密度兜底这条嫌疑单独判：两次 n_zero 不同，就说明差异来自兜底路径而不是 UHF 解。
    fallback_differs = pkg_nzero != pkg2_nzero
    if fallback_differs:
        print("!! 同一份实现两次调用连 n_zero 都不同（%s vs %s）⇒ 兜底路径本身不确定"
              % (pkg_nzero, pkg2_nzero))
    SELF_TOL = 1e-10
    # 只用返回的 S 做诊断，不再重算任何权重——重算配方就是这个仓这两天反复出事的那件事。
    # 要分辨的是两种很不一样的情形：
    #   尾部少数点上的任意划分（分子分母同时下溢，w_A = ρ_A/Σρ 变成 0/0 量级） ⇒ 修法小：加下溢阈值
    #   还是大面积、每个点都动（那说明整个解不稳定）                        ⇒ 修法大：得换定义
    DD = np.abs(pkg - pkg2)
    big = DD > 1e-3
    n_pts = DD.shape[1]
    n_bad_pts = int(np.count_nonzero(big.any(axis=0)))
    worst_col = int(np.argmax(DD.max(axis=1)))
    row_sum_dev = float(np.abs(pkg.sum(axis=0) - 1.0).max())
    bad_vals = pkg[worst_col][big[worst_col]]
    print("# 抖动定位：>1e-3 的原子-点组合 %d 个，分布在 %d / %d 个网格点上（占 %.4f%%）"
          % (int(big.sum()), n_bad_pts, n_pts, 100.0 * n_bad_pts / n_pts))
    print("# 抖动最大的原子（第 %d 个）在坏点上的权重：n=%d  范围 [%s, %s]  合法权重应在 0~1"
          % (worst_col, bad_vals.size,
             "%.3e" % bad_vals.min() if bad_vals.size else "n/a",
             "%.3e" % bad_vals.max() if bad_vals.size else "n/a"))
    print("# 归一性：包内第一次的逐点权重和偏离 1 的最大值 = %.3e" % row_sum_dev)
    unstable = [nm for nm, d in (("包内 partition.hirshfeld_factors", d_self_pkg),
                                 ("包外 free_atom_soft", d_self_scr))
                if d > SELF_TOL]
    if unstable:
        print("\nVERDICT NOT_REPRODUCIBLE —— %s 同一份实现、同一批坐标两次结果差 %.3e > %g"
              % ("；".join(unstable), max(d_self_pkg, d_self_scr), SELF_TOL))
        print("   病因不是『两份实现不同』：同一份代码、同样输入，出来的归属矩阵就不一样。")
        print("   自由原子 UHF 本身已排除（`probe_free_atom_uhf_stability.py` 实测 ΔE 与 1-RDM")
        print("   在 5 次重复里都是精确 0）⇒ 不确定性在这条权重例程**自己内部**，")
        print("   候选只剩：零密度点的兜底路径、以及依赖集合/字典序的浮点归约顺序。")
        print("   ⇒ 任何走 Hirshfeld 的读数在这个体系上都不可逐位复现；正文引用它之前")
        print("      要么先把这段不确定性定位到一行代码，要么把 Hirshfeld 降级为敏感性对照。")
        return 3
    if pkg.shape != scr.shape:
        print("!! 形状都不同（%s vs %s）：两份实现返回的东西不是一回事，先修对照"
              % (pkg.shape, scr.shape))
        return 2
    d = np.abs(pkg - scr)
    print("# 包内 n_zero=%s  包外返回 shape=%s" % (pkg_nzero, scr.shape))
    print("# max|ΔS| = %.3e   均值|ΔS| = %.3e   逐原子最大差 = %s"
          % (d.max(), d.mean(), np.array2string(d.max(axis=0), precision=3)))
    tol = 1e-12
    if d.max() <= tol:
        print("\nVERDICT IDENTICAL —— 两份实现在同一批点上逐点相同（≤%g）"
              "⇒ 苯系那 0.0130 的差不可能来自实现，只能来自两次运行各自拿到的自由原子解"
              "（即 (ii)：非唯一性随体系增大），修法不是合成一份实现。" % tol)
        return 0
    print("\nVERDICT IMPLEMENTATIONS_DIFFER —— 权重构造本身不同，差 %.3e"
          "⇒ 苯系分歧是实现分叉，单一来源化才是修法；旧读数的来源必须点名。" % d.max())
    return 1


if __name__ == "__main__":
    sys.exit(main())
