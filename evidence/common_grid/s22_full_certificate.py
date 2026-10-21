"""W4 满 S22：对**单个** S22 官方复合物跑归属证书并归档（一格一档）。

档名以官方文件夹号（S22_NN）为主键，不用人类体系名 —— 名称正在独立核对
（我从几何反推的片段分子式与"我记得的 S22 顺序"冲突，见 scratch/s22_inventory.log）。
正文表由 `summarize_s22_full.py` 从这些原件现算，名字那一栏等核对结果再并进去。

与已归档八格的同源性（这是"复现"而不是"另算一套"的前提）：
  - 几何 = `scratch/lit/s22/S22_NN.xyz` 原文字节（sha256 打进本档）；
  - 片段 = `geomlib.split_frags(..., COV_CUTOFF)`，与 `step_h_s22.build()` 同一个函数；
  - 网格 = `partition.scf_grid(mol, xc="wb97x_v", level=1, basis="6-31g*")`，同档位同基组；
  - 构造 = `partition.scheme_factors` 六个方案（家族内四 + Voronoi + Hirshfeld）；
  - 分解 = `nlc.fragment_decomposition(..., soft=S)`，与八格同一条路。
自检：E_NLC 总量必须与归属方案无关（分区穷尽且互不重叠），
      这条同时抓"输入不同源"——几何/基组/网格档/(b,C) 任一不同都会在这里露出来。
"""
import hashlib
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np                       # noqa: E402
from nlcsplit import certificate, geomlib, partition   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "scratch", "lit", "s22")
LEVEL = 1
XC = "wb97x_v"
BASIS = "6-31g*"

# 逐方案读数那一行的**唯一**格式定义。汇总器 `summarize_s22_full.py` 直接 import 这个常量
# 生成一行喂给自己的正则 —— 上一轮就是 "E_AB = " 后面差两个空格把解析器打空了，
# 而那种错只在批跑完（多小时后）才现形。格式放一处，两边就不可能走偏。
FMT_LINE = "   %-16s E_AB = %+9.4f  E_NL = %+10.4f"


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def formula(atoms):
    from collections import Counter
    c = Counter(s for s, _ in atoms)
    order = [e for e in ("C", "H", "N", "O", "F", "S") if e in c] + sorted(set(c) - {"C", "H", "N", "O", "F", "S"})
    return "".join("%s%s" % (e, "" if c[e] == 1 else c[e]) for e in order)


def main(nn):
    t0 = time.time()
    xyz = "S22_%s.xyz" % nn
    p = os.path.join(DATA, xyz)
    if not os.path.exists(p):
        print("!! 缺官方几何 %s" % p)
        return 2
    atoms = geomlib.read_xyz(p)
    frags = geomlib.split_frags(atoms, geomlib.COV_CUTOFF)
    if len(frags) != 2:
        print("!! %s 切成 %d 段，不是二聚体，拒跑（需人工核对，不许硬凑）" % (xyz, len(frags)))
        return 3
    cc = np.array([x for _, x in atoms])
    dmin = min(np.linalg.norm(cc[i] - cc[j]) for a in frags for b in frags if a is not b
               for i in a for j in b)
    print("# W4 满 S22 单格证书  文件夹 %s" % xyz)
    print("# git HEAD %s" % os.popen("cd %s && git rev-parse HEAD" % ROOT).read().strip())
    # 打印实际被 import 的包路径：本仓被"读的是环境里那份旧副本"坑过，
    # 归档必须自己声明用的是哪一份代码，不能靠事后回忆。
    print("# nlcsplit.__file__ %s" % os.path.abspath(partition.__file__))
    print("# sha256 %-40s = %s" % (xyz, sha(p)))
    print("# sha256 nlcsplit/partition.py                     = %s" % sha(os.path.join(ROOT, "nlcsplit", "partition.py")))
    print("# sha256 nlcsplit/certificate.py                   = %s" % sha(os.path.join(ROOT, "nlcsplit", "certificate.py")))
    print("# level=%d xc=%s basis=%s  原子 %d  片间最短 %.2f A  片段 %s + %s"
          % (LEVEL, XC, BASIS, len(atoms), dmin,
             formula([atoms[i] for i in frags[0]]), formula([atoms[i] for i in frags[1]])))

    # 与 step_h_s22.build 同一条护栏（片间最短 > 1.5 A），只是这里先打过 sha 与分子式
    if dmin <= 1.5:
        print("!! 片间最短 %.3f A，几何可疑，拒跑" % dmin)
        return 3

    from pyscf import gto
    mol = gto.M(atom=[(s, c) for s, c in atoms], basis=BASIS, verbose=0, unit="Angstrom")
    r = certificate.certify(mol, frags, level=LEVEL, xc=XC, basis=BASIS)
    print("# npts=%d  usable=%s" % (r["meta"]["npts"], ",".join(r["usable"])))
    if r["flagged"]:
        print("# flagged %s" % r["flagged"])
    for s in partition.ALL_SCHEMES:
        v = r["per_scheme"][s]
        print(FMT_LINE % (s, v["E_ab"][(0, 1)], v["E_nl"]))
    b = r["bounds"][(0, 1)]
    fam = [r["per_scheme"][s]["E_ab"][(0, 1)] for s in partition.SCHEMES]
    allv = [r["per_scheme"][s]["E_ab"][(0, 1)] for s in partition.ALL_SCHEMES]
    print("   -> 家族内跨度 = %.4f kcal/mol（四方案，同一网格同一权重）" % (max(fam) - min(fam)))
    print("   -> 含两个家族外构造的总跨度 = %.4f kcal/mol" % (max(allv) - min(allv)))
    print("   -> 界 lo = %+.4f (%s)  hi = %+.4f (%s)" % (b["lo"], b["argmin"], b["hi"], b["argmax"]))
    enl = [r["per_scheme"][s]["E_nl"] for s in partition.ALL_SCHEMES]
    spread = max(enl) - min(enl)
    print("   护栏：E_NLC 跨方案极差 = %.3e（门 1e-9 相对）%s"
          % (spread, "OK" if spread <= 1e-9 * abs(enl[0]) else "OVER"))
    if spread > 1e-9 * abs(enl[0]):
        print("VERDICT REFUSED —— 闭包不过，界不发")
        return 1
    if r["flagged"]:
        print("VERDICT PARTIAL —— 有构造被标退化，界只由 usable 给（照档入库，汇总脚本按 usable 取）")
        print("# exit=0")
        return 0
    print("VERDICT DONE")
    print("# 用时 %.1f s" % (time.time() - t0))
    return 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    m = re.search(r"(\d+)", arg)
    if not m:
        sys.exit("用法：s22_full_certificate.py <文件夹号，如 3 或 S22_03>")
    sys.exit(main(m.group(1).zfill(2)))
