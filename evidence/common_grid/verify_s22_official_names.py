"""把 GMTKN55 官方 S22 参考值表与盘上几何对上，给 22 格定名（投稿表里"体系"那一列的出处）。

为什么现在才做：`20261013T193551Z_verify_s22_folder_identity.out` 只核了 `geomlib.S22`
里已有的 8 个中文名，剩下 14 格的片段式一直挂"待核"——那期间三条外路全断，
官方档取不到，而我给自己定过一条硬规矩：**不凭记忆填名**（我记忆里的 S22 顺序与盘上几何直接冲突）。
2026-10-13 21:5xZ `ssh <CLUSTER>` 回得来 hostname，网络恢复，于是把官方 `.res` 取回来存成
`scratch/lit/gmtkn55_S22.res`，本脚本读的是**那份落盘的副本**，不联网，可离线重跑。

判据不是"我认得这些缩写"，而是两条独立信息必须同时吻合：

1. **元素式**：官方标签对应的化学式（下方 `LABEL_FORMULA`，那是我对缩写的化学读法，
   显式写出来供人反驳）要与该格几何经 `split_frags` 切出的两个片段式一致。
   读法错、或者文件夹号↔标签这层映射错，都会在这里露出来。
2. **物理自洽**：同一标签出现两次（`uracil` 在 05 与 13）时，要靠几何区分谁是谁——
   氢键接触更多、片间最短距离更小的那一格，必须对应参考值更大（结合更强）的那一号。
   这条不许我把两格叫同一个名字还分不清。

3. **分块自洽**：官方 `.res` 用 `##` 把 22 行分成三块（块号是从文件里现读的，不是我背的
   "氢键 7 / 色散 8 / 混合 7"）。块的边界必须同时是几何氢键指纹的边界——块 1 每格都有
   片间氢键、块 2 每格都没有。两边来源独立（官方分隔行 vs 盘上坐标），过这条才算佐证。

另外对"同式不同几何"的四对（05/13、07/15、11/20、14/21）逐一算指纹
（`dmin` / 片间氢键数 / 片间 C···C ≤4.0 A 接触数 / 两片环平面夹角），
要求**指纹可分**——正文表里两行看起来完全一样的体系是缺陷，不是排版问题。

用法：bash evidence/common_grid/run_verify_s22_names.sh
"""
import hashlib
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import numpy as np                                  # noqa: E402
from nlcsplit import geomlib                         # noqa: E402
from s22_full_certificate import formula as hill     # noqa: E402  分子式写法：复用生产者那一份

RES = os.path.join(ROOT, "scratch", "lit", "gmtkn55_S22.res")
XYZDIR = os.path.join(ROOT, "scratch", "lit", "s22")
URL = "https://raw.githubusercontent.com/grimme-lab/GMTKN55/v1/S22/.res"

# 我对官方缩写的化学读法（键 = .res 里那一个字面串，值 = 两个片段的 Hill 式，顺序无关）
LABEL_FORMULA = {
    "nh3":      ("H3N", "H3N"),
    "h2o":      ("H2O", "H2O"),
    "formac":   ("CH2O2", "CH2O2"),          # 甲酸二聚体
    "formam":   ("CH3NO", "CH3NO"),          # 甲酰胺二聚体
    "uracil":   ("C4H4N2O2", "C4H4N2O2"),
    "pyridone": ("C5H5NO", "C5H6N2"),        # 2-吡啶酮 + 2-氨基吡啶
    "AT":       ("C5H5N5", "C5H6N2O2"),      # 腺嘌呤 + 胸腺嘧啶
    "AT S":     ("C5H5N5", "C5H6N2O2"),
    "ch4":      ("CH4", "CH4"),
    "ethene":   ("C2H4", "C2H4"),
    "ethenine": ("C2H4", "C2H2"),            # 乙烯 + 乙炔
    "bzch4":    ("C6H6", "CH4"),
    "bzpd":     ("C6H6", "C6H6"),            # benzene parallel-displaced
    "bzT":      ("C6H6", "C6H6"),            # benzene T-shaped
    "bzh2o":    ("C6H6", "H2O"),
    "bznh3":    ("C6H6", "H3N"),
    "bzhcn":    ("C6H6", "CHN"),
    "pyraz":    ("C4H4N2", "C4H4N2"),        # 吡嗪二聚体
    "indolebz": ("C6H6", "C8H7N"),           # 吲哚–苯
    "indolbz":  ("C6H6", "C8H7N"),
    "phenol":   ("C6H6O", "C6H6O"),
}
HB_ACC = ("N", "O")      # 氢键受体：只认片间 H···N / H···O
HB_MAX = 2.6             # A，算一条氢键的距离门限
STACK_MAX = 4.0          # A，片间 C···C 算"堆积接触"的距离门限


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def parse_res(path):
    """`$tmer 06{,a,b}/$f x -1 1 1 $w 16.934 0 1 pyridone` → ('06', 16.934, 'pyridone', 块号)。

    块号读自文件里的 `##` 分隔行（官方把 22 格分成三块），**不是我背的三类分组**——
    这样"块边界"本身也是一手数据，判据 3 才能拿它去考几何。
    """
    rows, blk = [], 1
    rx = re.compile(r"\$tmer\s+(\d+)\{[^}]*\}/\$f\s+x\s+(?:\S+\s+)+\$w\s+([\d.]+)\s+\d+\s+\d+\s+(.+?)\s*$")
    for line in open(path, encoding="utf-8", errors="ignore"):
        s = line.strip()
        if s == "##":
            blk += 1
            continue
        m = rx.match(s)
        if m:
            rows.append((m.group(1), float(m.group(2)), m.group(3), blk))
    return rows


def geom(nn):
    atoms = geomlib.read_xyz(os.path.join(XYZDIR, "S22_%s.xyz" % nn))
    frags = geomlib.split_frags(atoms, geomlib.COV_CUTOFF)
    if len(frags) != 2:
        return None
    cc = np.array([x for _, x in atoms])
    a, b = frags[0], frags[1]
    inter = [(i, j) for i in a for j in b]
    d = {p: float(np.linalg.norm(cc[p[0]] - cc[p[1]])) for p in inter}
    dmin = min(d.values())
    # 氢键：一侧是 H、另一侧是 N/O。**上一版这里写成 `in "HO"`，那是子串判断——
    # "H" 也在 "HO" 里，于是把 H···H 近接触当成氢键（水二聚体报出 5 条），
    # 同时把真正的 H···N 全漏掉（腺嘌呤–胸腺嘧啶只报 3 条）。判据写错比没判更糟：它会给假绿。
    hb = sum(1 for i, j in inter
             if atoms[i][0] == "H" and atoms[j][0] in HB_ACC and d[(i, j)] <= HB_MAX)
    hb += sum(1 for i, j in inter
              if atoms[j][0] == "H" and atoms[i][0] in HB_ACC and d[(i, j)] <= HB_MAX)
    cc_n = sum(1 for i, j in inter
               if atoms[i][0] == "C" == atoms[j][0] and d[(i, j)] <= STACK_MAX)
    return dict(atoms=atoms, frags=frags, dmin=dmin, hb=hb, cstack=cc_n,
                labels=sorted(hill([atoms[i] for i in f]) for f in frags))


def plane_normal(atoms, frag):
    """该片重原子的最佳拟合平面法向量 + 最大出平面偏差（>0.15 A 视为非平面，不算夹角）。"""
    pts = np.array([atoms[i][1] for i in frag if atoms[i][0] != "H"])
    if len(pts) < 3:
        return None, None
    c = pts - pts.mean(0)
    _, s, vt = np.linalg.svd(c)
    dev = float(np.abs(c @ vt[2]).max())
    return vt[2], dev


def ring_angle(g):
    n1, d1 = plane_normal(g["atoms"], g["frags"][0])
    n2, d2 = plane_normal(g["atoms"], g["frags"][1])
    if n1 is None or n2 is None:
        return None
    if max(d1, d2) > 0.15:
        return None
    cos = abs(float(np.dot(n1, n2)))
    return math.degrees(math.acos(min(1.0, cos)))


def main():
    if not os.path.exists(RES):
        print("!! 取回的官方档不在：%s（先跑 curl 再跑本脚本；缺它=没测，不是通过）" % RES)
        return 2
    rows = parse_res(RES)
    print("# S22 文件夹号 ↔ 官方标签 核对（正文“体系”列的出处）")
    print("# 官方参考值表 URL   %s" % URL)
    print("# 本地副本           %s" % os.path.relpath(RES, ROOT).replace("\\", "/"))
    print("# sha256             %s" % sha(RES))
    print("# 几何目录           %s（与满批同一份，各格 sha 见 2026*_s22_full_certificate_*.out 抬头）"
          % XYZDIR.replace("\\", "/"))
    print("# 分子式写法         复用生产者 `s22_full_certificate.formula`（Hill），不在这儿重新发明")
    if len(rows) != 22:
        print("!! 官方表只解析出 %d 行，预期 22 行 ⇒ 解析器与格式脱钩，先修正则" % len(rows))
        return 1
    print("\n## 官方 .res 原文（逐字节 cat，不靠终端回显拼图）")
    for line in open(RES, encoding="utf-8", errors="ignore").read().splitlines():
        print("   | " + line)

    print("\n## 逐格核对：标签读法的化学式 vs 盘上几何切出的片段式")
    bad, info = [], {}
    print("   %-4s %-9s %-9s %-10s %-14s %s" % ("号", "官方标签", "参考值", "最短 dmin", "片段式（几何）", "指纹"))
    for nn, ref, label, blk in rows:
        g = geom(nn)
        if g is None:
            bad.append((nn, "切不出两段"))
            continue
        want = sorted(LABEL_FORMULA.get(label, ("?", "?")))
        got = g["labels"]
        ang = ring_angle(g)
        info[nn] = dict(ref=ref, label=label, blk=blk,
                        **{k: g[k] for k in ("dmin", "hb", "cstack")},
                        ang=ang, formulas=got)
        tag = "一致" if want == got else "!! 不符（读法 %s vs 几何 %s）" % ("/".join(want), "/".join(got))
        if want != got:
            bad.append((nn, tag))
        fp = "氢键 %d 条，C···C≤4.0 A %d 对" % (g["hb"], g["cstack"])
        if ang is not None:
            fp += "，环面夹角 %.0f°" % ang
        print("   %-4s %-9s %-9.3f %-10.2f %-14s %s  %s"
              % (nn, label, ref, g["dmin"], " + ".join(got), tag, fp))

    print("\n## 判据 2：同式不同几何的四对，指纹必须分得开")
    bypair = {}
    for nn, d in info.items():
        bypair.setdefault(tuple(d["formulas"]), []).append(nn)
    dup = {k: v for k, v in bypair.items() if len(v) > 1}
    fail = 0
    for pair, cells in sorted(dup.items()):
        cells = sorted(cells)
        fps = [info[c] for c in cells]
        same = all(abs(f["dmin"] - fps[0]["dmin"]) < 5e-3 and f["hb"] == fps[0]["hb"]
                   and f["cstack"] == fps[0]["cstack"] for f in fps)
        print("   %s + %s：%s ⇒ %s" % (pair[0], pair[1], " / ".join(
            "S22_%s(dmin %.2f, 氢键 %d, 堆积 %d, 夹角 %s)"
            % (c, info[c]["dmin"], info[c]["hb"], info[c]["cstack"],
               "n/a" if info[c]["ang"] is None else "%.0f°" % info[c]["ang"])
            for c in cells), "分得开" if not same else "!! 分不开"))
        if same:
            fail = 1
        # 同标签复现（uracil 在 05/13）时再加一条物理自洽：更强 ↔ 氢键更多 ↔ dmin 更小
        labs = {info[c]["label"] for c in cells}
        if len(labs) == 1:
            hi, lo = max(cells, key=lambda c: info[c]["ref"]), min(cells, key=lambda c: info[c]["ref"])
            ok = (info[hi]["hb"] >= info[lo]["hb"]) and (info[hi]["dmin"] <= info[lo]["dmin"])
            print("      同标签 %r 两格：参考值大的是 S22_%s(%.3f)、小的是 S22_%s(%.3f)；"
                  "要求前者氢键不少于后者且 dmin 不大于 ⇒ %s"
                  % (list(labs)[0], hi, info[hi]["ref"], lo, info[lo]["ref"],
                     "自洽" if ok else "!! 不自洽，不许硬分"))
            if not ok:
                fail = 1

    print("\n## 判据 3：官方 `##` 分块（块号读自文件）与几何氢键指纹是不是各自独立说同一件事")
    print("   要求：块的边界必须同时是氢键指纹的边界——块 1 每格都有片间氢键、块 2 每格都没有。")
    print("   两边信息独立（一边是官方档里的分隔行，一边是盘上坐标），所以这条过才算真加分；")
    print("   它不是证明，是佐证：某格违例 ⇒ 要么号↔标签错位，要么我的氢键判据错，两者都该停机。")
    blocks = {}
    for nn, d in info.items():
        blocks.setdefault(d["blk"], []).append(nn)
    for blk in sorted(blocks):
        cells = sorted(blocks[blk], key=int)
        hbs = {c: info[c]["hb"] for c in cells}
        print("   块 %d（%d 格 %s–%s）片间氢键：%s"
              % (blk, len(cells), cells[0], cells[-1],
                 " ".join("%s:%d" % (c, hbs[c]) for c in cells)))
        if blk == 1 and any(v == 0 for v in hbs.values()):
            print("      !! 块 1 里有格片间一条氢键都没有 ⇒ 号↔标签错位或判据错")
            fail = 1
        elif blk == 2 and any(v > 0 for v in hbs.values()):
            print("      !! 块 2 里有格有氢键 ⇒ 号↔标签错位或判据错")
            fail = 1
        elif blk >= 3:
            print("      块 %d 不断言（官方这组本来就是氢键/色散混着来的，如 苯–H2O 只有 H···C）" % blk)

    print("\n## 正文可用名（官方标签 + 文件夹号 + 参考值；标签有歧义的按几何描述补）")
    amb = [pair for pair, cells in dup.items()
           if len({info[c]["label"] for c in cells}) == 1]
    for nn in sorted(info, key=lambda s: int(s)):
        d = info[nn]
        print("   S22_%-3s %-9s 参考 %.3f kcal/mol  几何：%s + %s"
              % (nn, d["label"], d["ref"], d["formulas"][0], d["formulas"][1]))
    if amb:
        print("   （注意：%d 组同式且**同标签**，正文引用时必须带文件夹号或几何描述，不能只写标签）"
              % len(amb))

    if bad:
        print("\n!! 有格化学式对不上：%s" % bad)
        print("VERDICT NOTCLEAN —— 标签读法或号↔标签映射有错，名字不许进正文")
        return 1
    if fail:
        print("\nVERDICT NOTCLEAN —— 化学式全对上了，但同式那几对指纹分不开/物理不自洽")
        return 1
    print("\nVERDICT OK —— 22 格官方标签与几何化学式逐格一致；四对同式兄弟指纹可分；"
          "同标签复现的那对物理自洽")
    print("# 这份核对只定“名字↔几何”这一层，不含任何 ωB97X-V 读数；表里的数值仍由各格 .out 原件供。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
