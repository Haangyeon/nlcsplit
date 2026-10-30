"""W3 验收：包内新入口 `nlcsplit.certify(...)` 必须复现已归档的同单位跨构造表。

为什么不写一份"新数字"就算完：八格表已经由 `hirshfeld_crossfamily.py`（包外）与
`crossfamily_inpackage_check.py`（包内 dispatcher）两条路各自跑过并归档，
`certify` 是第三条路。第三条路只有在**与已入库原件逐位对上**时才叫复现，
否则它只是又一个没人核对过的实现。所以本脚本：
  1) 跑 certify（一次 SCF + 六个构造，网格与已归档那份同为 scf_grid(level=1)）；
  2) 从原件解析同名体系的每方案 E_AB 与总跨度（**不手抄一个数**）；
  3) 逐方案比 |新 − 归档|，门取原件的打印分辨率 1e-4（原件只印到 4 位小数）；
  4) 界的方向与取到极值的方案名也必须一致——只比数值不比 argmin/argmax 的话，
     一个把方案名接错的实现照样能过。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import nlcsplit                          # noqa: E402
from nlcsplit import certificate         # noqa: E402
from nlcsplit.step_h_s22 import build    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ARCHIVE = os.environ.get("CERT_ARCHIVE",
                         "20261013T053243Z_crossfamily_inpackage_check_l1_small.out")
# 体系名与线程数都可注入，为的是能不问就答这两个问题：
#   ① 证书入口能不能在**第二格**上也复现（不只水二聚体）；
#   ② 复现结论是否依赖 BLAS 线程数 —— G5 已证 Hirshfeld 权重随线程漂，
#      而本文件的门 TOL=1e-4 比那个抖动小一个量级，所以换个线程跑同一格**可能就该红**。
CELL = os.environ.get("CERT_CELL", "水二聚体")
LEVEL = 1
# 门本身有适用边界，必须写在抬头而不是藏在注释里（今晚两次栽在"绿灯的口径没人知道"）：
#   - 这个 1e-4 是**按水二聚体一格的成功标定的**，与已作废的 HIR_TOL=1e-3 同属"拿一格定门"；
#   - 含 Hirshfeld 的方案**随 BLAS 线程数漂**（实测同格 OMP=4 差 2.3e-4、OMP=1 差 3.9e-05），
#     所以本门只对"线程配置被固定/记录"的比较有意义 —— 跑之前先看 OMP_NUM_THREADS。
TOL = 1e-4        # 原件只印到 4 位小数，能验的上限就是打印分辨率

RE_FAM = re.compile(r"家族内 (\S+)\s+E_AB\s*=\s*(-?\d+\.\d+)")
RE_VOR = re.compile(r"Voronoi\(包内\)\s+E_AB\s*=\s*(-?\d+\.\d+)")
RE_HIR = re.compile(r"Hirshfeld\(包内\)\s+E_AB\s*=\s*(-?\d+\.\d+)")
RE_SPAN = re.compile(r"含两个家族外构造的总跨度 = (\d+\.\d+)")
RE_ENL = re.compile(r"E_NL\s*=\s*(-?\d+\.\d+)")


def parse_archive():
    txt = open(os.path.join(HERE, ARCHIVE), encoding="utf-8", errors="ignore").read()
    block = re.search(r"== %s .*?(?=\n== |\Z)" % CELL, txt, re.S)
    if not block:
        sys.exit("!! 原件里没有 %s 那一段" % CELL)
    b = block.group(0)
    eab = dict(RE_FAM.findall(b))
    eab["voronoi"] = RE_VOR.search(b).group(1)
    eab["hirshfeld"] = RE_HIR.search(b).group(1)
    enl = float(RE_ENL.search(b).group(1))
    return {k: float(v) for k, v in eab.items()}, float(RE_SPAN.search(b).group(1)), enl


def main():
    print("# W3 验收：certify(包内新入口) vs 已归档的包内 dispatcher 读数")
    print("# 原件 %s  体系 %s  level %d  门 %.0e kcal/mol（=原件打印分辨率）"
          % (ARCHIVE, CELL, LEVEL, TOL))
    if not os.path.exists(os.path.join(HERE, ARCHIVE)):
        print("!! 缺原件，拒跑")
        return 2
    ref, ref_span, ref_enl = parse_archive()
    # 几何与片段定义必须与原件同源：原件走 step_h_s22.build（S22 官方几何 + 片段索引表）。
    # 上一轮这里用的是 geomlib.h2o_dimer()——那是**另一个**水二聚体几何，公共网格点数与原件不同，
    # 于是六个方案的 E_AB 整体同向平移，判语 REFUSED（错位来自输入不同源，不是 certify 的实现差异；
    # 两份档的点数各看自己那一份的抬头，别在这里抄数）。
    # 认得出这类坑的形状特征：所有方案残差**同号且近似同幅**，而不是散乱。
    mol, frags, dmin = build(CELL)
    print("# 几何 %s  原子 %d  片间最短 %.2f Å（原件同项见其 == 段抬头）"
          % (CELL, mol.natm, dmin))
    r = certificate.certify(mol, frags, level=LEVEL)
    print("# certify 抬头：%s" % r["meta"])
    print("# usable %s  flagged %s" % (r["usable"], r["flagged"]))
    bad = []
    for s in nlcsplit.partition.ALL_SCHEMES:
        new = r["per_scheme"][s]["E_ab"][(0, 1)]
        old = ref[s]
        d = abs(new - old)
        print("   %-16s certify %+9.4f  归档 %+9.4f  差 %.2e %s"
              % (s, new, old, d, "OK" if d <= TOL else "OVER"))
        if d > TOL:
            bad.append((s, d))
    b = r["bounds"][(0, 1)]
    print("   界 lo %+9.4f (%s)  hi %+9.4f (%s)  span %.4f  归档跨度 %.4f  差 %.2e"
          % (b["lo"], b["argmin"], b["hi"], b["argmax"], b["span"], ref_span,
             abs(b["span"] - ref_span)))
    if abs(b["span"] - ref_span) > TOL:
        bad.append(("span", abs(b["span"] - ref_span)))
    # 界的方向也要一致：只比数值不比方案名的话，接错方案名的实现照样过关。
    # 归档那一格（原件见文件头 ARCHIVE）六个极值彼此分得开，所以按打印值取极值名
    # 不会因四舍五入而换人；真出现并列时这里会报"不符"而不是静默放行。
    ref_argmin = min(ref, key=ref.get)
    ref_argmax = max(ref, key=ref.get)
    for key, who, want in (("argmin", b["argmin"], ref_argmin),
                           ("argmax", b["argmax"], ref_argmax)):
        print("   %s = %s，归档里的同名极值方案 = %s %s"
              % (key, who, want, "OK" if who == want else "不符"))
        if who != want:
            bad.append((key, who, want))
    # 闭包不变量：总 NLC 与归属方案无关（这条不依赖任何外部程序）。
    enl = [v["E_nl"] for v in r["per_scheme"].values() if v["E_nl"] is not None]
    print("   E_nl 跨方案极差 = %.3e（应到机器精度；这条是分区穷尽且互不重叠的闭包判据）"
          % (max(enl) - min(enl)))
    if max(enl) - min(enl) > 1e-9 * abs(enl[0]):
        bad.append(("closure", max(enl) - min(enl)))
    # 总量还要与原件对上：这一条抓的是"输入不同源"（几何、基组、网格档位、(b,C)），
    # 因为归属方案再怎么换也不会动 E_nl 本身。门沿用原件那条护栏的 0.005。
    d_enl = abs(enl[0] - ref_enl)
    print("   E_nl certify %+9.4f  归档 %+9.4f  差 %.4f（门 0.005）%s"
          % (enl[0], ref_enl, d_enl, "OK" if d_enl <= 0.005 else "OVER"))
    if d_enl > 0.005:
        bad.append(("E_nl-vs-archive", d_enl))
    if bad:
        print("VERDICT REFUSED —— %s" % bad)
        return 1
    print("VERDICT DONE —— certify 在原件打印分辨率内逐方案复现已归档的包内读数，界与闭包同向")
    return 0


if __name__ == "__main__":
    sys.exit(main())
