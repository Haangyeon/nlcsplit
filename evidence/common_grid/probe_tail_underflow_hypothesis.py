"""判别实验：抖动的点到底在不在"远尾"？——决定 §五 的阈值方案值不值一次整批重跑。

背景（一句话）：Hirshfeld 归属权重 `w_A = ρ_A/Σρ` 在 1 线程下逐位确定、≥2 线程会抖到 1e-1，
猜的机制是"尾部 ρ 与 Σρ 同时下溢 ⇒ 末位噪声被除法放大"。
但"猜得通"不等于"是它"。如果抖的点其实离核很近，那加分母阈值也白搭，
整批重跑就是白花几小时。所以先做这个便宜的判别：

  1. 两个子进程分别用 OMP=1 与 OMP=8 算同一份权重矩阵 S（同一几何、同一网格档）；
     ——必须子进程：BLAS 的线程数在 numpy 导入后就钉死了，进程内改环境变量没用。
  2. 取逐点最大差 `d(x) = max_A |S1-A(x) - S8-A(x)|`，看 d 大的点离最近原子有多远；
  3. 若 d 的大值点系统性地落在远处（分位数明显高于全体分布）⇒ 阈值方案对症；
     若 d 大的点散布在各处、近核处也一样 ⇒ 机制不是下溢，别重跑整批。

只用生产函数返回的 S 与几何本身，不重写任何权重配方。
"""
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NAME = "苯-氨"
LEVEL = 1

WORKER = r'''
import os, sys
import numpy as np
sys.path.insert(0, %(root)r)
from nlcsplit import partition
from nlcsplit.step_h_s22 import build
from pyscf import dft
mol, frags, dmin = build(%(name)r)
g = dft.gen_grid.Grids(mol); g.level = %(level)d; g.build()
S = partition.hirshfeld_factors(mol, g.coords)[0]
np.save(sys.argv[1], np.asarray(S, dtype=np.float64))
# np.save 会给不以 .npy 结尾的名字补上 .npy，所以这里必须写全名——
# 上一版写 ".pts" 结果落盘成 "s1.npy.pts.npy"，父进程按 ".pts" 找不到。
np.save(sys.argv[1] + ".pts.npy", np.asarray(g.coords, dtype=np.float64))
import json
json.dump({"natm": mol.natm,
           "xyz": [[mol.atom_symbol(a), mol.atom_coord(a, unit="Bohr").tolist()]
                   for a in range(mol.natm)]},
          open(sys.argv[1] + ".meta.json", "w"))
''' % {"root": ROOT, "name": NAME, "level": LEVEL}


def run_worker(threads, path):
    env = dict(os.environ)
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        env[k] = str(threads)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, "-c", WORKER, path], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    if p.returncode != 0:
        print("!! 子进程（%d 线程）失败：\n%s" % (threads, p.stderr[-1200:]))
        sys.exit(2)
    return path


def main():
    print("# 远尾假设的判别实验  体系 %s  level %d" % (NAME, LEVEL))
    bohr = 0.529177210903
    tmp = tempfile.mkdtemp(prefix="tailtest_")
    a = run_worker(1, os.path.join(tmp, "s1.npy"))
    b = run_worker(8, os.path.join(tmp, "s8.npy"))
    S1, S8 = np.load(a), np.load(b)
    pts = np.load(a + ".pts.npy")
    import json
    meta = json.load(open(a + ".meta.json"))
    cen = np.asarray([x[1] for x in meta["xyz"]], dtype=float)

    d = np.abs(S1 - S8).max(axis=0)                     # 逐点最大差
    dd = np.linalg.norm(pts[:, None, :] - cen[None, :, :], axis=2).min(axis=1)  # 到最近核的距离(Bohr)
    print("# 网格点 %d，逐点最大差 d 的极值 = %.3e" % (d.size, d.max()))
    print("# 若 1 与 8 线程完全一致（d.max()<=1e-14），这个实验无从判断——先看这一行")
    if d.max() <= 1e-14:
        print("\nVERDICT NO_SIGNAL —— 两次跑逐位相同，取不到差值样本，换更大体系或更多线程再来")
        return 2

    q = np.quantile(dd, [0.5, 0.9, 0.99])
    bad = dd[d > 1e-3]
    good = dd[d <= 1e-3]
    print("# 全体点到最近核距离(Å)：中位 %.2f  p90 %.2f  p99 %.2f" % tuple(q / bohr))
    print("# d>1e-3 的点共 %d 个：距离中位 %.2f Å，最小 %.2f Å，最大 %.2f Å"
          % (bad.size, np.median(bad) / bohr if bad.size else float("nan"),
             bad.min() / bohr if bad.size else float("nan"),
             bad.max() / bohr if bad.size else float("nan")))
    print("# d<=1e-3 的点距离中位 %.2f Å" % (np.median(good) / bohr if good.size else float("nan")))
    # 分位数比：抖的点是否系统性更远。用 p10 而不是中位更稳（绝大多数点本来就不抖）
    p10_bad = np.quantile(bad, 0.10) / bohr if bad.size else float("nan")
    p10_all = np.quantile(dd, 0.10) / bohr
    verdict = "TAIL_HYPOTHESIS_SUPPORTED" if (bad.size and p10_bad > p10_all + 0.5) else \
              "TAIL_HYPOTHESIS_NOT_SUPPORTED"
    verdict = "TAIL_HYPOTHESIS_SUPPORTED" if (bad.size and p10_bad > p10_all + 0.5) else \
              "TAIL_HYPOTHESIS_NOT_SUPPORTED"
    # 注意别用 endswith("SUPPORTED") 判分支：NOT_SUPPORTED 也以 SUPPORTED 结尾——
    # 上一版就是这么写的，于是"否"的判语配了一段"是"的解释，读起来自相矛盾。
    print("# 判据：抖点的 p10 距离 %.2f Å 对比全体 p10 %.2f Å（要 > +0.5 Å 才算支持'远尾'）"
          % (p10_bad, p10_all))
    print("# 抖点占比 %.1f%%（若接近 100%%，那根本不是'少数尾部点'的故事）"
          % (100.0 * bad.size / d.size))
    print("\nVERDICT %s" % verdict)
    if verdict == "TAIL_HYPOTHESIS_SUPPORTED":
        print("   ⇒ 抖确实集中在远尾，分母下溢阈值是对症的修法；§五 的整批重跑值得。")
    else:
        print("   ⇒ 抖的点并不都远在尾部，阈值方案未必解决；别先重跑整批，回到权重构造再定位。")
    return 0 if verdict == "TAIL_HYPOTHESIS_SUPPORTED" else 1


if __name__ == "__main__":
    sys.exit(main())
