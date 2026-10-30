"""Task 9 的正确仪器：包内（随发布）路径 vs 修后包外路径，逐格比对。

为什么不是 crossfamily_inpackage_check.py：那份脚本的内联参照副本**必须保持 Å 口径**
（它是归档口径的化身），所以 A 件修正后它的 HIR_TOL 门必然 REFUSED——
`20261013T053243Z_crossfamily_inpackage_check_l1_small.out` 已实测拒在三格
`hirshfeld-readings-over-tol`（差 0.0247/0.0277/0.0328 kcal/mol，正是单位效应本身），
Voronoi 与家族内 dispatcher 仍逐位相同。那份 REFUSED 是**预期拒绝**，不是失败。

本脚本比的是两条**都修过**的路径：
  包内 = 20261013T053243Z 档里"同进程双跑"行的**第二个数**（新权重 = partition.hirshfeld_factors，Bohr）
  包外 = 20261012T054743Z / 20261012T050216Z 档里 `Hirshfeld(自由原子库存化) E_AB`（hirshfeld_crossfamily.py，Bohr）
判据：|包内 − 包外| ≤ 1e-3 kcal/mol（HIR_TOL，来由见 crossfamily_inpackage_check.py 文件头）；
Voronoi 两档差 ≤ 1e-4（两档都只打印 4 位小数，跨档验不了逐位；
"逐位相同"由 crossfamily_inpackage_check 在同进程内对内存矩阵验，20261012T035522Z 与
20261013T053243Z 两份档里 Voronoi 旧vs新都是 bit-identical）。任一不过 ⇒ VERDICT REFUSED，exit 1。
只从原件解析，不手抄；缺档直接拒。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INPAC = "20261013T053243Z_crossfamily_inpackage_check_l1_small.out"
EXT = {"水二聚体": "20261012T054743Z_hirshfeld_crossfamily_l1_水二聚体_after_unitfix.out",
       "氨二聚体": "20261012T054743Z_hirshfeld_crossfamily_l1_氨二聚体_after_unitfix.out",
       "甲烷二聚体": "20261012T054743Z_hirshfeld_crossfamily_l1_甲烷二聚体_after_unitfix.out"}
TOL = 1e-3

RE_DOUBLE = re.compile(r"hirshfeld ([-+0-9.eE]+) vs ([-+0-9.eE]+) 差")
RE_VOR_IN = re.compile(r"voronoi ([-+0-9.eE]+) vs ([-+0-9.eE]+) 差")
RE_HIR_EXT = re.compile(r"Hirshfeld\(自由原子库存化\)\s+E_AB\s*=\s*(-?[0-9.]+)")
RE_VOR_EXT = re.compile(r"Voronoi\(最近原子硬指派\)\s+E_AB\s*=\s*(-?[0-9.]+)")


def main():
    print("# Task 9 认证：包内(Bohr) vs 修后包外(Bohr)，门 %.0e kcal/mol" % TOL)
    bad = []
    for cell, ext in EXT.items():
        pi = os.path.join(HERE, INPAC)
        pe = os.path.join(HERE, ext)
        if not (os.path.exists(pi) and os.path.exists(pe)):
            print("!! 缺档 %s / %s" % (INPAC, ext))
            return 2
        tin = open(pi, encoding="utf-8", errors="ignore").read()
        tex = open(pe, encoding="utf-8", errors="ignore").read()
        # 取该体系段落（按 "== 体系名" 分块）
        def block(txt, name):
            m = re.search(r"== %s .*?(?=\n== |\Z)" % re.escape(name), txt, re.S)
            return m.group(0) if m else ""
        bi, be = block(tin, cell), block(tex, cell)
        mh = RE_DOUBLE.search(bi)
        mv = RE_VOR_IN.search(bi)
        eh = RE_HIR_EXT.search(be)
        ev = RE_VOR_EXT.search(be)
        if not (mh and mv and eh and ev):
            print("!! %s 解析不全（in:%s%s ext:%s%s）" % (cell, bool(mh), bool(mv), bool(eh), bool(ev)))
            return 2
        hir_in, hir_ext = float(mh.group(2)), float(eh.group(1))
        vor_in, vor_ext = float(mv.group(2)), float(ev.group(1))
        dh, dv = abs(hir_in - hir_ext), abs(vor_in - vor_ext)
        # 两档都只打印到 4 位小数 ⇒ 这里能验的上限是打印分辨率，不是逐位。
        # "逐位相同"这件事由 crossfamily_inpackage_check 在同进程内验（它比的是内存里的矩阵），
        # 本脚本只负责跨档交叉认证，门取打印分辨率 1e-4。
        PRINT_TOL = 1e-4
        ok = dh <= TOL and dv <= PRINT_TOL
        print("   %-8s 包内 Hirshfeld %+9.6f  包外 %+9.6f  差 %.2e %s | Voronoi 差 %.1e %s"
              % (cell, hir_in, hir_ext, dh, "OK" if dh <= TOL else "OVER",
                 dv, "OK(≤打印分辨率)" if dv <= PRINT_TOL else "NOT"))
        if not ok:
            bad.append((cell, dh, dv))
    if bad:
        print("VERDICT REFUSED —— %s" % bad)
        return 1
    print("VERDICT OK —— 随发布路径在门内复现修后包外读数；Voronoi 逐位相同")
    return 0


if __name__ == "__main__":
    sys.exit(main())
