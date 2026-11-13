"""量出三个苯二聚体几何的环面夹角与平面内滑移，给正文的 (A)/(B) 命名做原件。

为什么要有这份档（2026-10-05 复查）：§3.2 的表把 `苯二聚体(A)` 写成 sandwich、把 (B) 写成
parallel-displaced，而 `paper/main.md` 另一处与 §3.1 的表写的是 "(A, parallel-displaced)" 与
"(B, T-shaped)"。同一个体系在一篇稿子里有两个名字，审稿人量一次坐标就能判定哪个错。
这份档不靠名字、不靠记忆：只从坐标算质心距、环面夹角、垂直层距与平面内滑移。

用法：python3 evidence/recompute/benzene_dimer_label_measure.py
"""
import hashlib
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from nlcsplit import geomlib                                        # noqa: E402


def metrics(atoms, frags):
    ring = []
    out = []
    for f in frags:
        pts = [np.array(atoms[i][1]) for i in f if atoms[i][0] == "C"]
        assert len(pts) == 6, "每片应有 6 个碳，实得 %d" % len(pts)
        cen = sum(pts) / 6.0
        X = np.array([p - cen for p in pts])
        _, sv, vt = np.linalg.svd(X, full_matrices=False)
        assert sv[2] < 5e-3, "苯环面外残差 %.2e Å，不像苯环" % sv[2]
        ring.append((cen, vt[2] / np.linalg.norm(vt[2])))
        out.append(float(sv[2]))
    (c1, n1), (c2, n2) = ring
    cv = c2 - c1
    along = float(cv @ n1)
    return (float(np.linalg.norm(cv)),
            float(np.degrees(np.arccos(min(1.0, abs(float(n1 @ n2)))))),
            abs(along),
            float(np.linalg.norm(cv - along * n1)),
            max(out))


def classify(dist, ang, layer, slip):
    if ang > 60.0:
        return "T 型（环面近垂直）"
    if slip < 1e-6:
        return "夹心 sandwich（面对面、零滑移）"
    return "平行位移（面对面、有滑移）"


if __name__ == "__main__":
    print("# 苯二聚体几何判别：只看坐标，不看文件名里的说法")
    print("# python %s  numpy %s  pyscf %s" % (sys.version.split()[0], np.__version__,
                                               __import__("pyscf").__version__))
    for mod in ("nlcsplit/geomlib.py", "nlcsplit/tests/test_geometry.py"):
        p = os.path.join(ROOT, mod.replace("/", os.sep))
        print("# sha256 %s = %s" % (mod, hashlib.sha256(open(p, "rb").read()).hexdigest()))
    print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                           capture_output=True, text=True).stdout.strip())
    s22 = os.path.join(ROOT, "scratch", "lit", "s22")
    print("# S22 目录 %s : %s" % (s22, os.path.isdir(s22)))
    print()
    rows = []
    # 索引不抄第二遍：直接问 geomlib.S22，这份档才有"文件被换掉也会报"的效力
    for name in ("苯二聚体(A)", "苯二聚体(B)"):
        atoms, frags = geomlib.s22_system(name, s22)
        rows.append(("%s = %s（官方 S22）" % (name, geomlib.S22[name]), atoms, frags))
    sb = geomlib.benzene_sandwich()
    rows.append(("benzene_sandwich(d=3.81) 构造几何 (C6H6)2", sb, geomlib.FRAGS["(C6H6)2"]))
    for label, atoms, frags in rows:
        d, ang, layer, slip, _ = metrics(atoms, frags)
        print("  %-46s 质心距=%7.3f 环面夹角=%5.1f° 垂直层距=%7.3f 平面内滑移=%7.3f  => %s"
              % (label, d, ang, layer, slip, classify(d, ang, layer, slip)))
    print()
    print("# 结论：S22 的两个苯二聚体是「平行位移」与「T 型」；「夹心」是我们自己构造的第三个几何。")
    print("# 反向验证见 test_geometry.py::test_benzene_dimer_geometries_are_the_two_named_kinds")
    print("#   与 evidence/recompute/ 同名归档：把 (A) 当 T 型、把 (B) 当平行位移都会 AssertionError。")
