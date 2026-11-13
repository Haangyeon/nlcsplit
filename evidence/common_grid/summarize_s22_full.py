"""W4 满表汇总：把 22 格 S22 归属证书原件解析成一张表 —— **缺任何一格就拒绝出表**。

为什么必须由脚本出：本仓反复出错的环节都是"人眼把数从 .out 搬到表里"（交接件 §八坑 5：
列标签比数值更容易搬错）。所以这张表只从原件解析，且
  - 每格只取**最新一份 rc=0** 的档（失败档不参与）；
  - 主键是官方文件夹号 S22_NN，人类体系名等独立核对结果进来再并（见 NOTE/naming）；
  - 与已归档八格重叠的体系额外做一次**新旧读数交叉认证**（门取旧档打印分辨率），
    这一列才是"满表与既有表同源同口径"的证据，没有它这张表只是又一批新数。
"""
import glob
import os
import re
import sys
from datetime import datetime, timezone
from statistics import median

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS = ["S22_%02d" % i for i in range(1, 23)]
# 旧八格档（按中文体系名归档）：文件名 ↔ 文件夹号的映射从 geomlib.S22 反查，不手写对照表
OLD_NAME_BY_FILE = {}
FAM_SCHEMES = ["becke", "becke-becke-rad", "becke-treutler", "stratmann"]
# 两条认证门不是一回事，别混用一个数：
#   PRINT_TOL = 旧档只印到 4 位小数 ⇒ 确定性方案能验的上限；
#   HIR_TOL   = Hirshfeld 权重列的非唯一性下限（见 NOTE_hirshfeld_weight_nonuniqueness_20261012.md，
#               自由原子 UHF 的轨道转动会传到 E_AB 上；线程数改变 BLAS 归约序也走到同一量级）。
#               第一条实例：水二聚体新格与旧认证档的 Hirshfeld 列末位不同，两档的抬头行可比对。
PRINT_TOL = 1e-4
HIR_TOL = 1e-3
# ===== 外部声明的交叉认证集合（2026-10-18 裁断第 1 步）=====
# 为什么必须写死在这里：上一版预期数是从被检档反推的，于是"部分失交"（8 格掉到 5 格）时
# 预期跟着降到 5，补丁照样绿 —— 那正是本仓 §2.2 自己批评过的"无法失败的守卫"。
# 身份键 = GMTKN55 官方文件夹号（本表主键，见打印的满表抬头第 3 行）。
# 体系名只用作"这一份旧档确实是这一格"的二次确认，不作为键：档名/档内名不一致那件事
# 已经有实例（benzwater 那份），拿名字当键等于把静默失交请回工具里。
EXPECT_OVERLAP = {
    "S22_01": "氨二聚体",
    "S22_02": "水二聚体",
    "S22_08": "甲烷二聚体",
    "S22_10": "苯-甲烷",
    "S22_11": "苯二聚体(A)",
    "S22_17": "苯-水",
    "S22_18": "苯-氨",
    "S22_20": "苯二聚体(B)",
}
# 每格要认证到的列数：包内 `partition.ALL_SCHEMES` 是名单的唯一定义（不在这里重抄名字），
# 但**条数在这里声明**。包哪天少给一个方案，这里失败，而不是"认证列跟着缩、表照出"。
EXPECT_SCHEME_COUNT = 6
RE_EAB = re.compile(r"^\s{3}(\S+)\s+E_AB\s*=\s*(-?\d+\.\d+)", re.M)
RE_SPAN = re.compile(r"跨度 = (\d+\.\d+)|总跨度 = (\d+\.\d+)")
RE_FORM = re.compile(r"片段 (\S+) \+ (\S+)")
RE_NPTS = re.compile(r"# npts=(\d+)")
RE_ATOMS = re.compile(r"原子 (\d+)")
RE_VERDICT = re.compile(r"VERDICT (\w+)")
RE_USABLE = re.compile(r"# usable=([\w.,-]+)")
RE_OLD_FAM = re.compile(r"家族内 (\S+)\s+E_AB\s*=\s*(-?\d+\.\d+)")
# 旧档抬头自报的体系名（形如 `== <体系名>  level=…  原子 …  公共网格 N=…  片间min … Å`，
# 实例见 `20261012T050216Z_hirshfeld_crossfamily_l1_benzwater_after_unitfix.out` 的抬头行）。
# 键要取这一行而不是文件名：W2 那一格的文件名是拉丁 `benzwater`，其余七格是中文，
# 只按文件名映射会把它**静默丢掉**，交叉认证就从 8 格缩成 7 格而无人报错。
RE_OLD_HDR = re.compile(r"^== (\S+)\s+level=(\d+)\s+原子\s+(\d+)\b.*?片间min\s+([\d.]+)", re.M | re.S)
RE_OLD_VOR = re.compile(r"Voronoi\(最近原子硬指派\)\s+E_AB\s*=\s*(-?\d+\.\d+)")
RE_OLD_HIR = re.compile(r"Hirshfeld\(自由原子库存化\)\s+E_AB\s*=\s*(-?\d+\.\d+)")


def _load_folder_map():
    """geomlib.S22 是 {中文名: 文件名}；反查得到 {文件夹号: 中文名}。"""
    sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
    from nlcsplit import geomlib
    out = {}
    for name, fn in geomlib.S22.items():
        out[fn.replace(".xyz", "")] = name
    return out


def partition_all_schemes():
    """六个方案的名字，从包里取，不在本文件再抄一份清单。"""
    sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
    from nlcsplit import partition
    return list(partition.ALL_SCHEMES)


SKIPPED = []          # 被排除的档，必须打印出来，不能静默少算


def rc_is_ok(path):
    """`.rc` 内容的两代写法都要认：`0`（现约定）与 `rc=0`（10-06 那批）。

    只认 `strip() == "0"` 会造成**静默少算**——一档被跳过而汇总里看不出少了谁。
    所以这里取末尾数字，并把任何"格式读不出"的档记进 SKIPPED。
    """
    try:
        raw = open(path, encoding="utf-8", errors="ignore").read().strip()
    except OSError:
        return False
    m = re.search(r"(-?\d+)\s*$", raw)
    if not m:
        SKIPPED.append((os.path.basename(path), "rc 内容读不出：%r" % raw[:24]))
        return False
    return m.group(1) == "0"


def latest_ok(cell):
    """该格最新的 rc=0 档。"""
    pats = [os.path.join(HERE, "*_%s_l1_*.out" % cell),
            os.path.join(HERE, "*_%s_*.out" % cell)]
    seen = []
    for p in pats:
        for f in glob.glob(p):
            base = os.path.basename(f)
            if "s22_full_certificate" not in base:
                continue
            rc = f + ".rc"
            if not os.path.exists(rc):
                SKIPPED.append((base, "没有同名 .rc（多半还在跑或当年没落）"))
                continue
            if rc_is_ok(rc):
                seen.append(f)
    return sorted(seen)[-1] if seen else None


def parse(path):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    eab = dict(RE_EAB.findall(txt))
    fm = RE_FORM.search(txt)
    npts = RE_NPTS.search(txt)
    at = RE_ATOMS.search(txt)
    v = RE_VERDICT.search(txt)
    us = RE_USABLE.search(txt)
    # 跨度只能从 **usable** 列算：`certify` 的界本来就把被标退化的构造剔掉了，
    # 这里若拿全六列算跨度，PARTIAL 那格的"表里的跨度"与"档里的界"就会是两个数，
    # 而且没有任何一处会报错 —— 只在真出现标记时现形，所以现在就对齐。
    usable = [u for u in (us.group(1).split(",") if us else []) if u in eab] or list(eab)
    fam = [eab[s] for s in FAM_SCHEMES if s in usable]
    allv = [eab[s] for s in usable]
    return {
        "eab": eab, "npts": int(npts.group(1)) if npts else None,
        "natoms": int(at.group(1)) if at else None,
        "frags": " + ".join(fm.groups()) if fm else "?",
        "verdict": v.group(1) if v else "?",
        "usable": usable, "dropped": [s for s in eab if s not in usable],
        "fam_span": (max(float(x) for x in fam) - min(float(x) for x in fam)) if len(fam) == 4 else None,
        "all_span": (max(float(x) for x in allv) - min(float(x) for x in allv)) if len(allv) >= 2 else None,
        "file": os.path.basename(path),
    }


def klass(frags):
    """按**片段元素式**分同核/异质，不看体系名：名字一栏还有"（待核）"。

    `parse()` 给的 frags 形如 "H2O + H2O"（生产者从同一个 split_frags 打出来的），
    两片元素式相同就是同核二聚体，不同就是异质对。切不出两片的情况生产者已经拒跑
    （"不是二聚体，拒跑"），所以这里不必再造兜底分支。
    """
    parts = [p.strip() for p in frags.split("+")]
    if len(parts) != 2 or "?" in parts:
        return "未分类"
    return "同核" if parts[0] == parts[1] else "异质"


def old_overlaps():
    """旧八格档（同单位重测那批）里**六个方案**的读数，用于逐列交叉认证。

    返回 `({官方文件夹号: ({方案: E_AB}, 档名)}, [失效记录])`。

    旧档同时印了家族内四方案、`Voronoi(最近原子硬指派)`、`Hirshfeld(自由原子库存化)`，
    还有一行**故意的诱饵** `（对照，不计入判据）等权 1/natm E_AB = …`。
    所以这里用带标签的三条正则，而不是"任何 `X E_AB = 数`"的通用式 ——
    通用式会把那行等权诱饵也读成一个方案，交叉认证就假阳/假阴一片。

    2026-10-18 裁断第 1 步的改动：原来"读不出六列就 continue""抬头读不出名只 print"
    这两条都会**静默缩面**（少一格，而预期数跟着降）。现在一律记进 `fails`，
    由 `main()` 拿去决定 rc=2。解析失败不等于"没有这一格"。
    """
    out, fails = {}, []
    name2cells = {}
    for cell, nm in _load_folder_map().items():
        name2cells.setdefault(nm, []).append(cell)
    files = sorted(glob.glob(os.path.join(HERE, "2026*_hirshfeld_crossfamily_l1_*_after_unitfix.out")))
    if not files:
        fails.append("交叉认证旧档 glob 落空：目录里一份 "
                     "`2026*_hirshfeld_crossfamily_l1_*_after_unitfix.out` 都没有 ⇒ 这八格是没测，不是通过")
        return out, fails
    for f in files:
        base = os.path.basename(f)
        txt = open(f, encoding="utf-8", errors="ignore").read()
        vals = dict(RE_OLD_FAM.findall(txt))
        for pat, name in ((RE_OLD_VOR, "voronoi"), (RE_OLD_HIR, "hirshfeld")):
            m = pat.search(txt)
            if m:
                vals[name] = m.group(1)
        miss = [s for s in partition_all_schemes() if s not in vals]
        if len(vals) < EXPECT_SCHEME_COUNT or miss:
            fails.append("%s 六列不齐（读到 %d 列，缺 %s）⇒ 计为没测，不静默丢格"
                         % (base, len(vals), "、".join(miss) or "无"))
            continue
        hdr = RE_OLD_HDR.search(txt)
        if not hdr:
            fails.append("%s 抬头读不出体系名 ⇒ 不退回用档名（档名与档内名不一致有前例 benzwater），计为没测" % base)
            continue
        nm = hdr.group(1)
        cells = name2cells.get(nm, [])
        if len(cells) != 1:
            fails.append("%s 档内自报名 %r 在文件夹号映射里命中 %d 格（%s）⇒ 身份不唯一，不猜"
                         % (base, nm, len(cells), "、".join(cells) or "无"))
            continue
        cell = cells[0]
        if cell not in EXPECT_OVERLAP:
            fails.append("%s 落到 %s（自报名 %r），但外部声明的认证集合里没有这一格 ⇒ 声明与实物不符，"
                         "要么查档、要么改声明，不许顺手把预期降下来" % (base, cell, nm))
            continue
        if EXPECT_OVERLAP[cell] != nm:
            fails.append("%s 格 %s 自报名 %r ≠ 声明 %r ⇒ 判身份挂错对象，不当认证"
                         % (base, cell, nm, EXPECT_OVERLAP[cell]))
            continue
        if cell in out:
            fails.append("%s 与 %s 都声明是格 %s ⇒ 一格出现两条旧路，认证键失效" % (out[cell][1], base, cell))
            continue
        # 档名 ↔ 档内自报名不一致仍然打印出来（历史上就是 benzwater 那格用拉丁名），
        # 但身份已按**档内自报名 + 外部声明**双重核过，档名不再是键。
        from_file = (base.split("_l1_")[1].replace("_after_unitfix.out", "")
                     .replace("苯二聚体A", "苯二聚体(A)").replace("苯二聚体B", "苯二聚体(B)"))
        if from_file != nm:
            print("# 旧档档名与档内自报体系名不一致：%s → 取档内自报的 %s（该档自报原子数 %s）"
                  % (from_file, nm, hdr.group(3)))
        out[cell] = ({k: float(v) for k, v in vals.items()}, base)
    return out, fails


def selftest_parser_against_producer():
    """拿**生产者自己的格式常量**造一行，喂给本脚本的正则，必须读得出数。

    这一条是上一轮踩出来的：正则写 `E_AB = ` 单空格，实际打印是 `E_AB =   -0.6010`
    （`%+9.4f` 带前导空格），结果一行都读不出来，而这要等 22 格跑完几个小时后才现形。
    格式常量现在只有一份（`s22_full_certificate.FMT_LINE`），所以这里能真正闭环验证；
    任何一侧改格式，这里立刻失败而不是让汇总表变空。
    """
    sys.path.insert(0, HERE)
    from s22_full_certificate import FMT_LINE
    line = FMT_LINE % ("becke-becke-rad", -0.5577, -7.895)
    got = RE_EAB.findall(line)
    if got != [("becke-becke-rad", "-0.5577")]:
        print("!! 解析器与生产者格式脱钩：喂进去 %r 读出来 %r" % (line, got))
        return 1
    print("# 自检：解析器 vs 生产者格式常量 FMT_LINE —— 一致")
    return 0


def main():
    if selftest_parser_against_producer():
        return 2
    fmap = _load_folder_map()
    rows, missing, unparsed = [], [], []
    for cell in CELLS:
        p = latest_ok(cell)
        if not p:
            missing.append(cell)
            continue
        r = parse(p)
        # 档在但读不出行 = 解析器与打印格式脱钩了。这必须当场叫出来，
        # 不能让下一轮在"批跑完了但表出不来"的时刻才发现正则写错。
        if len(r["eab"]) < 2:
            unparsed.append((cell, os.path.basename(p), len(r["eab"])))
            continue
        rows.append((cell, r))
    print("# 满 S22 归属证书表（脚本从各格 .out 原件解析，非手抄）")
    print("# 生成 %s  解析 %d/%d 格"
          % (datetime.now(timezone.utc).isoformat(), len(rows), len(CELLS)))
    print("# 主键 = GMTKN55 官方文件夹号；体系名一栏只有已独立核对过的才填")
    print()
    print("| 文件夹 | 体系名 | 片段 | 原子 | npts | 家族内跨度 | 含家族外总跨度 | 绝对增量 | 判语 | 原件 |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for cell, r in sorted(rows):
        inc = (r["all_span"] - r["fam_span"]) if (r["all_span"] is not None and r["fam_span"] is not None) else None
        print("| %s | %s | %s | %s | %s | %s | %s | %s | %s | `%s` |"
              % (cell, fmap.get(cell, "（待核）"), r["frags"], r["natoms"], r["npts"],
                 "%.4f" % r["fam_span"] if r["fam_span"] is not None else "缺",
                 "%.4f" % r["all_span"] if r["all_span"] is not None else "缺",
                 "%.4f" % inc if inc is not None else "缺",
                 r["verdict"] + ("" if not r["dropped"] else "（剔除退化列：%s）" % ",".join(r["dropped"])),
                 r["file"]))
    if SKIPPED:
        uniq = sorted(set(SKIPPED))
        print("\n# 被排除在外的档（%d 个）——列出来，不让它静默少算：" % len(uniq))
        for base, why in uniq[:12]:
            print("   %-58s %s" % (base, why))
        if len(uniq) > 12:
            print("   …另 %d 个" % (len(uniq) - 12))
    print()
    if rows:
        fams = [r["fam_span"] for _c, r in rows if r["fam_span"] is not None]
        alls = [r["all_span"] for _c, r in rows if r["all_span"] is not None]
        print("家族内带 = %.4f–%.4f（%d 格）" % (min(fams), max(fams), len(fams)))
        print("含家族外总跨度带 = %.4f–%.4f（%d 格）" % (min(alls), max(alls), len(alls)))
        # 分层是这张满表的主要卖点，不是装饰：正文此前能被一句"你只测了同核二聚体"打掉。
        # 类别**从原件里的片段元素式推**（同核 = 两片元素式相同），不从体系名推——
        # 名字那一栏还有"（待核）"，用名字分类等于把没核过的东西当前提。
        print("\n## 按片段是否同核分层（拆「只测了一类」这个定性攻击）")
        for k in ("同核", "异质", "未分类"):
            sel = [(c, r) for c, r in rows if klass(r["frags"]) == k]
            if not sel:
                print("   %s：0 格" % k)
                continue
            f = [r["fam_span"] for _c, r in sel if r["fam_span"] is not None]
            a = [r["all_span"] for _c, r in sel if r["all_span"] is not None]
            # 跨度与增量必须成对从**同一批**格子取。上一版写的是 zip(inc, sel)，而 inc
            # 只收齐了跨度的格子、sel 收全部，一旦某格缺跨度就静默错位相配，比值全错且不报错。
            pair = [(r["fam_span"], r["all_span"] - r["fam_span"]) for _c, r in sel
                    if r["fam_span"] is not None and r["all_span"] is not None]
            txt = "   %s：%d 格（%s）家族内带 %.4f–%.4f，含家族外总跨度带 %.4f–%.4f" % (
                k, len(sel), "、".join(c for c, _r in sel), min(f), max(f), min(a), max(a))
            if pair:
                inc = [i for _v, i in pair]
                rat = [i / v for v, i in pair if v]
                txt += "，绝对增量 中位 %.4f / 最大 %.4f，增量÷家族内跨度 %.2f–%.2f" % (
                    median(inc), max(inc), min(rat), max(rat))
            print(txt)
    old, ofails = old_overlaps()
    schemes = partition_all_schemes()
    print("\n## 与已归档八格的交叉认证（同一格两条路）")
    print("##   确定性方案（家族内四 + Voronoi）门 = 1e-4（旧档打印分辨率，逐位可复现）；")
    print("##   Hirshfeld 门 = 1e-3 —— 它的逐点权重列本来就有非唯一性下限（自由原子开壳层")
    print("##   近简并 UHF 可在轨道间做能量不变转动），实测见 "
          "`evidence/common_grid/NOTE_hirshfeld_weight_nonuniqueness_20261012.md`。"
          "把它按 1e-4 卡会把正常抖动判成失败。")
    print("##   预期集合 = 本文件常量 `EXPECT_OVERLAP`（%d 格，键=官方文件夹号）与 "
          "`EXPECT_SCHEME_COUNT`（%d 列），**不从被检档反推**；"
          "旧档读不齐/身份不唯一/声明外多出一格，全部计为没测（rc=2），不是缩小预期。"
          % (len(EXPECT_OVERLAP), EXPECT_SCHEME_COUNT))
    for why in ofails:
        print("!! 交叉认证失效：%s" % why)
    mismatch, uncert = [], []
    for cell in sorted(EXPECT_OVERLAP):
        name = EXPECT_OVERLAP[cell]
        if cell not in old:
            uncert.append((cell, "旧档没进认证（见上面失效行）"))
            continue
        r = [x for c, x in rows if c == cell]
        if not r:
            uncert.append((cell, "新档未到"))
            print("   %-12s %-8s 新档未到，先不判" % (cell, name))
            continue
        ov, of = old[cell]
        # 列级缺失以前是 `continue` 掉就完事（缺几列都照样算这一格已认证）。
        # 现在缺哪列点哪列，并让整格进 uncert。
        miss_col = [s for s in schemes if s not in ov or r[0]["eab"].get(s) is None]
        if miss_col:
            uncert.append((cell, "缺列 %s" % "、".join(miss_col)))
        line = []
        for s in schemes:
            if s in miss_col:
                continue
            tol = HIR_TOL if s == "hirshfeld" else PRINT_TOL
            d = abs(float(r[0]["eab"][s]) - ov[s])
            line.append("%s %+.4f" % ("OK" if d <= tol else "OVER", d))
            if d > tol:
                mismatch.append((cell, s, d, tol))
        print("   %-12s %-8s 逐列认证（%d/%d 列）：新档 vs `%s` → %s"
              % (cell, name, len(line), EXPECT_SCHEME_COUNT, of, ", ".join(line)))
    n_cert = len(EXPECT_OVERLAP) - len(uncert)
    print("   已认证 %d/%d 格；声明列数 %d（任何一格列不齐都已在上面进未认证，"
          "断言是**列集合==声明**，不是格数==格数）"
          % (n_cert, len(EXPECT_OVERLAP), EXPECT_SCHEME_COUNT))
    # 这段断言故意放在任何 `if old:` 之外：旧档全落空时 old 为空，写在块内的断言会被一起跳过
    # ——那正是上一轮外部裁断 §7.1 第 3 条点名的形状。
    if ofails or uncert or len(old) != len(EXPECT_OVERLAP):
        print("!! 交叉认证没测齐：失效 %d 条、未认证 %d 格 ⇒ 这是**没测**，不是通过（rc=2）"
              % (len(ofails), len(uncert)))
        return 2
    # 顺序是**改过的**（2026-10-18 裁断第 1 步收尾）：原来 `missing/unparsed` 排在 `mismatch` 之后，
    # 而线上现在恒定有一串 `mismatch`（四列 hirshfeld OVER）⇒ 那一串会**先**返回 rc=1，
    # 于是"某一格只剩 605 B 残件/根本没档"这种**没测**被分类成"出了表但数值不符"。
    # 本文件开头承诺"缺任何一格就拒绝出表"，靠这个顺序是兑不了现的。没测优先于数值不符。
    if missing or unparsed:
        print("\n!! 缺格 %s / 有档读不出 %s —— 满表不出。"
              "这是**没测**（rc=2），不是'出了表但数值不符'（rc=1）；"
              "残件与缺 `.rc` 的档都走这里，不许静默少算一格把表出成 %d 格"
              % ("、".join(missing) or "无",
                 unparsed or "无", len(EXPECT_OVERLAP)))
        if unparsed:
            print("   这类失败不能让它在批跑完的那一刻才现形；对着 `s22_full_certificate.py` 的 print 行修正则。")
        return 2
    if mismatch:
        print("!! 有列新旧不符：%s ⇒ 满表与既有表不同源，先查改动再出正文" % mismatch)
        return 1
    print("\nVERDICT OK —— 22 格齐")
    return 0


if __name__ == "__main__":
    sys.exit(main())
