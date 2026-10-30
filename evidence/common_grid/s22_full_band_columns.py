#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W4 满表派生列：逐格算"家族外增量由哪个构造造成"，并给出 Voronoi-only 带。

为什么现在要这个：外部裁决 G6(ii) 判"既不消除也不放大"证据不足——它验算出满表同核格里
"增量 ÷ 家族内跨度"最大到 6.07，而八格旧带给出的印象是 ~4%。这句话在逐格层面没算完之前
不得写进正文。本脚本只读 22 份单格证书，不改任何判据、不重算任何能量。

用法：python3 evidence/common_grid/s22_full_band_columns.py
退出码：0 = 22 格齐且全部通过自检；2 = 预期数不符（缺格/多格/解析失败），绝不打印派生结论；
        3 = 某格 E_NL 在六个方案之间不恒定（闭合被破坏，那格的跨度无意义）。

防"认证零格而报 VERDICT OK"：预期格数写死为常量 EXPECT_CELLS，不从被检对象自算
（外部裁决 §3.7.1 第①条正是这条漏：预期数从被检对象算出来，部分失交时补丁照样过）。
"""
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECT_CELLS = 22
FAMILY = ["becke", "becke-becke-rad", "becke-treutler", "stratmann"]
CROSS = ["voronoi", "hirshfeld"]
ROW = re.compile(r"^\s{3}([a-z][a-z0-9-]*)\s+E_AB = \s*(-?\d+\.\d{4})\s+E_NL = \s*(-?\d+\.\d{4})\s*$")
HEADRX = re.compile(r"^# git HEAD ([0-9a-f]{40})\s*$")
USE_RX = re.compile(r"^# npts=(\d+)\s+usable=(.+)$")
CERT_GLOB = "s22_full_certificate_"

print("# W4 满表派生列：逐格家族外增量来源 + Voronoi-only 带")
print("# 只读 %d 份单格证书；不重算能量、不改判据" % EXPECT_CELLS)

names = sorted(n for n in os.listdir(HERE)
               if CERT_GLOB in n and n.endswith(".out"))

# --- 断言一：先把"有效证书"与"异常件"分开点名，再要求有效格数 == 写死的预期数 ---
# 2026-10-15 实测：目录里有 23 份 .out，其中 S22_03 有两份——15:20:10 那份只有 605 字节的头
# （无 npts 行、无 VERDICT、无自报 exit、无配对 .rc），是启动即断的残件，不是第 23 格。
# 若这里只按 os.listdir 计数就会把残件当格、把格数抬到 23；若直接丢弃又不报，就是
# 外部裁决 §3.7.1 说的"认证零格而报 VERDICT OK"同一类漏。两条都不做：残件单列点名并计数。
valid = []
aborted = []
for n in names:
    path = os.path.join(HERE, n)
    with open(path, "r", encoding="utf-8") as fh:
        txt = fh.read()
    has_verdict = "VERDICT DONE" in txt
    has_exit = bool(re.search(r"^# exit=0 at ", txt, re.M))
    has_rc = os.path.exists(path + ".rc")
    rc_val = None
    if has_rc:
        rc_val = open(path + ".rc", "r", encoding="utf-8").read().strip()
    if has_verdict and has_exit and has_rc and rc_val == "0":
        valid.append((n, txt))
    else:
        aborted.append((n, os.path.getsize(path), has_verdict, has_exit, has_rc, rc_val))

if aborted:
    print("# 异常件（不计入格数，逐份点名）：")
    for n, sz, hv, he, hr, rv in aborted:
        print("#   %s  %d B  VERDICT=%s exit自报=%s .rc=%s 内容=%r"
              % (n, sz, hv, he, hr, rv))
    print("#")

if len(valid) != EXPECT_CELLS:
    sys.stdout.write("REFUSED —— 有效证书 %d 份，预期写死 %d 份（不从被检对象自算）\n"
                     % (len(valid), EXPECT_CELLS))
    sys.exit(2)

print("# 有效证书 %d 份 == 预期 %d 份；异常件 %d 份已点名"
      % (len(valid), EXPECT_CELLS, len(aborted)))

FAMRX = re.compile(r"家族内跨度 = (\d+\.\d{4})")
ALLRX = re.compile(r"含两个家族外构造的总跨度 = (\d+\.\d{4})")

cells = []
heads = set()
for n, txt in valid:
    lines = txt.splitlines()
    val = {}
    enl = {}
    folder = None
    natoms = None
    frag = None
    gap = None
    usable = None
    printed_fam = None
    printed_all = None
    for ln in lines:
        m = HEADRX.match(ln)
        if m:
            heads.add(m.group(1))
        mfam = FAMRX.search(ln)
        if mfam:
            printed_fam = float(mfam.group(1))
        mall = ALLRX.search(ln)
        if mall:
            printed_all = float(mall.group(1))
        if ln.startswith("# W4 满 S22 单格证书"):
            folder = ln.split("文件夹", 1)[1].strip()
        if ln.startswith("# level="):
            mm = re.search(r"原子 (\d+)", ln)
            natoms = int(mm.group(1)) if mm else None
            mf = re.search(r"片段 (.+)$", ln)
            frag = mf.group(1).strip() if mf else None
            mg = re.search(r"片间最短 ([\d.]+) A", ln)
            gap = mg.group(1) if mg else None
        mu = USE_RX.match(ln)
        if mu:
            usable = [u.strip() for u in mu.group(2).split(",")]
        mr = ROW.match(ln)
        if mr:
            val[mr.group(1)] = float(mr.group(2))
            enl[mr.group(1)] = float(mr.group(3))
    need = FAMILY + CROSS
    missing = [s for s in need if s not in val]
    if missing:
        sys.stdout.write("REFUSED —— %s 缺方案列：%s（六列不齐就不许进派生表）\n"
                         % (n, ",".join(missing)))
        sys.exit(2)
    if usable is not None and sorted(usable) != sorted(need):
        sys.stdout.write("REFUSED —— %s 自报 usable 与解析到的六列不一致：%s\n"
                         % (n, ",".join(sorted(usable))))
        sys.exit(2)
    if len(set(enl.values())) != 1:
        sys.stdout.write("REFUSED —— %s 的 E_NL 在六方案之间不恒定（%s），闭合被破坏\n"
                         % (n, sorted(set(enl.values()))))
        sys.exit(3)
    cells.append({"file": n, "folder": folder, "natoms": natoms, "frag": frag,
                  "gap": gap, "v": val, "enl": list(set(enl.values()))[0],
                  "pfam": printed_fam, "pall": printed_all})

if len(heads) > 1:
    print("# 注意：证书跨了 %d 个 git HEAD —— %s" % (len(heads), sorted(heads)))
else:
    print("# 全部 %d 份证书同一 git HEAD：%s" % (len(cells), list(heads)[0]))

print("#")
print("# 列定义：fam = 家族四方案跨度；famV = 家族+Voronoi 跨度；all = 六方案跨度；")
print("#           incV = famV - fam（Voronoi 造成的增量）；incH = all - famV（再加 Hirshfeld 的增量）；")
print("#           末列 = 六方案跨带的两端由哪个构造占据")
print()
hdr = ("folder    nA  fam      famV     all      incV     incH     ratio_all  "
       "lo(六)              hi(六)")
print(hdr)
print("-" * len(hdr))

rows = []
for c in sorted(cells, key=lambda x: x["folder"]):
    v = c["v"]
    fam = max(v[s] for s in FAMILY) - min(v[s] for s in FAMILY)
    famv = max(v[s] for s in FAMILY + ["voronoi"]) - min(v[s] for s in FAMILY + ["voronoi"])
    allsp = max(v.values()) - min(v.values())
    incv = famv - fam
    inch = allsp - famv
    lo = min(v, key=lambda s: v[s])
    hi = max(v, key=lambda s: v[s])
    ratio = allsp / fam if fam > 0 else float("inf")
    rows.append({"folder": c["folder"], "natoms": c["natoms"], "fam": fam, "famv": famv,
                 "all": allsp, "incv": incv, "inch": inch, "ratio": ratio,
                 "lo": lo, "hi": hi, "frag": c["frag"], "gap": c["gap"],
                 "pfam": c["pfam"], "pall": c["pall"]})
    print("%-9s %2d  %-8.4f %-8.4f %-8.4f %-8.4f %-8.4f %-10.2f %-18s %s"
          % (c["folder"], c["natoms"], fam, famv, allsp, incv, inch, ratio,
             "%s %+.4f" % (lo, v[lo]), "%s %+.4f" % (hi, v[hi])))

print()
# --- 控制：重算列必须与证书自印的跨度逐格相符（值打印到 4 位小数 ⇒ 两端各 ±5e-5，容差 1.1e-4）---
# 没有这一段，下面的带就是"我把原件里的数字再算一遍"这种未经比对的声明；有了它，派生列才真的钉在原件上。
bad = []
devs = []
for r in rows:
    for lab, mine, printed in (("fam", r["fam"], r["pfam"]), ("all", r["all"], r["pall"])):
        if printed is None:
            bad.append("%s/%s 原件没自印该列" % (r["folder"], lab))
            continue
        d = abs(mine - printed)
        devs.append(d)
        if d > 1.1e-4:
            bad.append("%s/%s 重算 %.6f vs 原件自印 %.6f 差 %.1e" % (r["folder"], lab, mine, printed, d))
print("== 控制：重算列 vs 证书自印列（44 项，容差 1.1e-4）==")
print("   比对 %d 项，最大偏差 %.2e，超容差 %d 项" % (len(devs), max(devs) if devs else -1, len(bad)))
if bad:
    for b in bad:
        print("   REFUSED " + b)
    sys.exit(2)

fams = [r["fam"] for r in rows]
famvs = [r["famv"] for r in rows]
alls = [r["all"] for r in rows]
incvs = [r["incv"] for r in rows]
inches = [r["inch"] for r in rows]
rats = [r["ratio"] for r in rows]
print("== 带（%d 格）==" % len(rows))
print("   家族内 fam      : %.4f – %.4f" % (min(fams), max(fams)))
print("   家族+Voronoi    : %.4f – %.4f   ← G6(ii) 问的 'Voronoi-only 带' 就是这一行"
      % (min(famvs), max(famvs)))
print("   六方案全含       : %.4f – %.4f" % (min(alls), max(alls)))
print("   Voronoi 增量     : %.4f – %.4f（为 Hirshfeld 增量 %.4f – %.4f）"
      % (min(incvs), max(incvs), min(inches), max(inches)))
print("   比值 all/fam     : %.2f – %.2f，其中 >2 的有 %d 格，>10 的有 %d 格"
      % (min(rats), max(rats), sum(1 for x in rats if x > 2), sum(1 for x in rats if x > 10)))
print()
print("   绝对增量（all - fam）最大格：%s = %.4f kcal/mol"
      % (max(rows, key=lambda r: r["all"] - r["fam"])["folder"],
         max(r["all"] - r["fam"] for r in rows)))
print("   比值最大格：%s = %.2f（该格 fam=%.4f，分母小才把比值抬起来）"
      % (max(rows, key=lambda r: r["ratio"])["folder"], max(rats),
         max(rows, key=lambda r: r["ratio"])["fam"]))
print()
print("   逐格判语（G6(ii) 的原话是'既不消除也不放大'，此处只按算术给三态，不做总结）：")
for r in sorted(rows, key=lambda x: -x["ratio"]):
    tag = ("放大 >2×" if r["ratio"] > 2 else
           ("基本不变 ≤2×" if r["ratio"] > 1.0001 else "不放大（=家族带）"))
    print("      %-9s %5.2f×  %s   incV=%.4f incH=%.4f  lo=%s hi=%s"
          % (r["folder"], r["ratio"], tag, r["incv"], r["inch"], r["lo"], r["hi"]))
n_enlarge = sum(1 for r in rows if r["ratio"] > 2)
n_flat = sum(1 for r in rows if r["ratio"] <= 1.0001)
print()
print("   计数：>2× 的 %d 格；=1.00×（加入家族外后带完全没变）的 %d 格；1–2× 之间的 %d 格"
      % (n_enlarge, n_flat, len(rows) - n_enlarge - n_flat))
print("VERDICT DONE —— 派生列已打印；'既不消除也不放大'能否进正文由上面三态计数决定，不由本脚本下判")
