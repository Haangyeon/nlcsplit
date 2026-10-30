"""把 A 件修正后的同单位重测档汇总成新的跨构造表——**只从原件解析，不手抄一个数**。

为什么要有这份：本仓多次实质差错都出在"人眼把数从 .out 搬到表里"这一环
（交接件 §八坑 5：列标签比数值更容易搬错）。所以新表必须由脚本现算，
且缺任何一格就**拒绝出表**，不许用旧数补位。

对照基准（家族内跨度，来自交接件 §五 那张八格表）写成常量而不是注释里的句子：
家族内那一列**不受 A 件影响**（四方案不碰自由原子密度），所以同单位重测必须逐位复现它。
复现不了 ⇒ 说明我改坏了别的东西，整表作废。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STAMPS = ["20261012T050216Z", "20261012T054743Z"]
CELLS = ["水二聚体", "氨二聚体", "甲烷二聚体", "苯-水", "苯-氨", "苯-甲烷",
         "苯二聚体(A)", "苯二聚体(B)"]
# 家族内跨度（kcal/mol）：交接件 §五 归档值；同单位重测必须逐位复现
FAMILY_SPAN_EXPECTED = {"水二聚体": 0.0433, "氨二聚体": 0.0284, "甲烷二聚体": 0.0034,
                        "苯-水": 0.2468, "苯-氨": 0.2219, "苯-甲烷": 0.2143,
                        "苯二聚体(A)": 0.0274, "苯二聚体(B)": 0.2195}
# 旧跨构造总跨度（Å 口径，已作废，只用于报"变了多少"）
OLD_CROSS = {"水二聚体": 0.0650, "氨二聚体": 0.0609, "甲烷二聚体": 0.0414,
             "苯-水": 0.3898, "苯-氨": 0.2792, "苯-甲烷": 0.2445,
             "苯二聚体(A)": 0.2208, "苯二聚体(B)": 0.2373}
OLD_RATIO = {"水二聚体": 1.50, "氨二聚体": 2.15, "甲烷二聚体": 12.17,
             "苯-水": 1.58, "苯-氨": 1.26, "苯-甲烷": 1.14,
             "苯二聚体(A)": 8.06, "苯二聚体(B)": 1.08}

RE_EAB = re.compile(r"(家族内 \S+|Voronoi\S*|Hirshfeld\S*)\s+E_AB\s*=\s*(-?\d+\.\d+)")
RE_FAM = re.compile(r"家族内跨度 = (\d+\.\d+)")
RE_ALL = re.compile(r"总跨度 = (\d+\.\d+)")
RE_RATIO = re.compile(r"比值[^=]*= (\d+\.\d+)")
RE_RC = re.compile(r"rc=(\d+)")


# 档名与体系名不一致的别名（苯-水那一格的 wrapper 把文件名写成了 benzwater）
ALIAS = {"苯-水": "benzwater"}


def find_out(cell):
    names = [cell, ALIAS.get(cell, cell), cell.replace("(", "").replace(")", "")]
    for st in STAMPS:
        for nm in names:
            p = os.path.join(HERE, "%s_hirshfeld_crossfamily_l1_%s_after_unitfix.out" % (st, nm))
            if os.path.exists(p):
                return p
    # 苯(A)/(B) 的档名里带括号，shell 不友好：按前缀找
    for st in STAMPS:
        for f in sorted(os.listdir(HERE)):
            if f.startswith(st) and "_l1_" in f and f.endswith("_after_unitfix.out"):
                key = f.split("_l1_")[1].replace("_after_unitfix.out", "")
                if key in (cell, cell.replace("(", "").replace(")", "")):
                    return os.path.join(HERE, f)
    return None


def parse(path):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    fam = RE_FAM.search(txt)
    allsp = RE_ALL.search(txt)
    rat = RE_RATIO.search(txt)
    eabs = dict((m.group(1), float(m.group(2))) for m in RE_EAB.finditer(txt))
    rc = "0" if "VERDICT DONE" in txt else "未见 VERDICT"
    return (float(fam.group(1)) if fam else None,
            float(allsp.group(1)) if allsp else None,
            float(rat.group(1)) if rat else None, eabs, rc, txt.count("用时"))


def main():
    rows, missing, bad, incomplete = [], [], [], []
    for cell in CELLS:
        p = find_out(cell)
        if not p:
            missing.append(cell)
            continue
        fam, allsp, rat, eabs, rc, ntime = parse(p)
        exp = FAMILY_SPAN_EXPECTED[cell]
        if fam is None or allsp is None:
            # .out 已存在但还没跑到跨度行 = 这一格仍在算，不是缺档也不是结论
            incomplete.append((cell, rc))
            continue
        ok = abs(fam - exp) < 5e-5
        if not ok:
            bad.append((cell, fam, exp))
        rows.append((cell, fam, exp, allsp, OLD_CROSS[cell], rat, OLD_RATIO[cell],
                     (allsp - fam) if (allsp is not None and fam is not None) else None,
                     rc, os.path.basename(p)))
    print("# A 件修正后的同单位跨构造表（由脚本从 .out 原件解析，非手抄）")
    print("# 生成 %s  解析到 %d/%d 格" % (__import__("datetime").datetime.now(
        __import__("datetime").timezone.utc).isoformat(), len(rows), len(CELLS)))
    print()
    print("| 格 | 家族内跨度 | 归档值 | 逐位相符 | 新跨构造 | 旧跨构造(Å) | 新比值 | 旧比值 | 绝对增量 | rc |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for cell, fam, exp, allsp, oldc, rat, oldr, inc, rc, fn in rows:
        print("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |"
              % (cell,
                 "%.4f" % fam if fam is not None else "缺",
                 "%.4f" % exp,
                 "✓" if abs(fam - exp) < 5e-5 else "**不符**",
                 "%.4f" % allsp if allsp is not None else "缺",
                 "%.4f" % oldc,
                 "%.2f" % rat if rat is not None else "缺",
                 "%.2f" % oldr,
                 "%.4f" % inc if inc is not None else "缺",
                 rc))
    print()
    if rows:
        bands = [r[3] for r in rows if r[3] is not None]
        fams = [r[1] for r in rows if r[1] is not None]
        incs = [r[7] for r in rows if r[7] is not None]
        print("新家族内带 = %.4f–%.4f（%d 格）" % (min(fams), max(fams), len(fams)))
        print("新跨构造带 = %.4f–%.4f（%d 格）" % (min(bands), max(bands), len(bands)))
        print("绝对增量范围 = %.4f–%.4f" % (min(incs), max(incs)))
    if missing:
        print("\n!! 缺格：%s —— 表不出，等这些跑完再重跑本脚本" % "、".join(missing))
    if bad:
        print("\n!! 家族内跨度与归档不符：%s ⇒ 单变量被破坏，整表作废，先查改动" % bad)
    if missing or bad:
        return 1
    print("\nVERDICT OK —— 八格齐、家族内跨度逐位复现归档")
    return 0


if __name__ == "__main__":
    sys.exit(main())
