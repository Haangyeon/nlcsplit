"""机器核对 Table 1：正文那张表的每一格能不能从原件里现算出来。

验收第 1 条写的是"表由脚本从原件现算、**零手抄**"，而 `claim_gate.js` 只查"某个数在某个档里出现过"。
两者差得远：一个数可以确实在档案里出现过，却贴在**错的行**上（把氨的跨度抄到甲烷行），
claim_gate 照样绿。这张表是全文的中心证据，本仓反复出事的就是"人眼搬数"，所以单独查。

行怎么对上（这条决定这个检查有没有意义）：
  不用体系名对。正文是英文（water dimer），档里是中文（水二聚体），
  再加第三份人工维护的中英对照表，等于把我要查的那类错误请回工具里。
  钥匙是**纯归属跨度**这一个数：八格里它互不相同，所以要求"恰好命中一个档块"，
  命中 0 个或 >1 个都直接算检查失败（不唯一就说明这把钥匙此刻失效了）。
  行身份定了之后，再核同一个块里的求积跨度与比值必须逐字相符，
  P_frz 则在 3 位小数精度内相符即通过——但**截断与就近会给出不同末位**，
  这种情况单列成一条提示报出来，不算转录错误（那是"这列怎么写"的口径问题，归作者定）。

列的覆盖面说清楚（这条必须与实现一致，否则又是一个空承诺）：
  本脚本**逐字核**第 5、6、7 列（纯归属跨度、求积跨度、归属/求积比）——它们必须
  逐字出自 S33 那三份档里同一个块，八行全过。
  第 2 列 P_frz **不逐字核，只报差值**：实测它与档里那个"公共网格上的 Becke E_AB"
  是**两个量**（正文那列是自带网格上的），苯系两行差到千分位量级。
  所以第 2 列的出处得另指（见下面打印的排查线索），本脚本不假装覆盖它。
  第 3、4 列（自带网格跨度与相对值）出自普查档，仍由 claim_gate 管"有没有出处"。
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAIN = os.path.join(ROOT, "paper", "main.md")
ARCH_GLOB = os.path.join(ROOT, "evidence", "common_grid", "*_ownership_vs_quadrature*.out")

RE_BLOCK = re.compile(r"^== (.+?)\s+level=\d+\s+原子\s+(\d+)")
RE_BECKE = re.compile(r"归属 becke\s+E_AB\s*=\s*(-?\d+\.\d+)")
RE_ATTR = re.compile(r"纯归属跨度（同一网格同一权重） = (\d+\.\d+)")
RE_QUAD = re.compile(r"求积侧总量跨度（各方案自带网格） = (\d+\.\d+)")
RE_RATIO = re.compile(r"归属/求积 = (\d+\.\d+)")
RE_TROW = re.compile(r"^\| ([^|]+?) \| (-?\d+\.\d+) \| (\d+\.\d+) \| (\d+\.\d)% \| "
                     r"(\d+\.\d+) \| (\d+\.\d+) \| (\d+\.\d+) \|\s*$", re.M)


def blocks():
    out = []
    for path in sorted(glob.glob(ARCH_GLOB)):
        cur = None
        for line in open(path, encoding="utf-8", errors="ignore").read().splitlines():
            m = RE_BLOCK.match(line)
            if m:
                cur = {"name": m.group(1), "natoms": int(m.group(2)), "file": os.path.basename(path)}
                out.append(cur)
                continue
            if cur is None:
                continue
            for key, rx in (("becke", RE_BECKE), ("attr", RE_ATTR), ("quad", RE_QUAD), ("ratio", RE_RATIO)):
                if key not in cur:
                    mm = rx.search(line)
                    if mm:
                        cur[key] = mm.group(1)
    return [b for b in out if all(k in b for k in ("becke", "attr", "quad", "ratio"))]


def table_rows():
    txt = open(MAIN, encoding="utf-8", errors="ignore").read()
    return [{"label": r.group(1).strip(), "p_frz": r.group(2), "own": r.group(3),
             "rel": r.group(4), "attr": r.group(5), "quad": r.group(6), "ratio": r.group(7)}
            for r in RE_TROW.finditer(txt)]


def skeleton_table4b():
    """从 `MAIN-skeleton.md` 的表 4b 取 (跨度, 相对%) → P_frz。

    表 4b 用体系中文名、正文表用英文，所以**不靠名字对**：
    4b 的"方案跨度"格写成 `0.032 (0.8%)`，正文把它拆成第 3、4 两列——
    这一对数同时相等的碰撞概率极低，拿它当钥匙即可，不必引入任何人工中英对照。
    （`MAIN-skeleton.md` 出货时被改名成 `docs/tables_and_provenance.md`，故不在 evidence/ 下。）
    """
    p = os.path.join(ROOT, "MAIN-skeleton.md")
    if not os.path.exists(p):
        return None
    txt = open(p, encoding="utf-8").read()
    m = re.search(r"### 表 4b.*?\n((?:\|.*\n)+)", txt, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        if re.match(r"^\|[\s|:-]+\|\s*$", line) or line.startswith("| 体系"):
            continue
        cells = [c.strip().replace("**", "") for c in line.strip().strip("|").split("|")]
        if len(cells) < 9:
            continue
        # 中文排版里的减号是 U+2212、还可能带不换行空格：不规格化就会把"完全相等的数"
        # 判成不符（我第一次跑就栽在这里，报了水/氨两行"不符"）。claim_gate 早就为此做过同样的归一。
        cells = [c.replace("\u2212", "-").replace("\u00a0", "").replace("−", "-") for c in cells]
        mm = re.match(r"(\d+\.\d+)\s*\((\d+\.\d)%\)", cells[7])
        if not mm:
            continue
        out[(mm.group(1), mm.group(2))] = {"name": cells[0], "p_frz": cells[6]}
    return out


def check_p_frz(rows, t4b):
    """正文第 2 列 P_frz 与表 4b 逐字核：两边都是 3 位小数，该完全相等。"""
    if t4b is None:
        print("!! 没找到 `MAIN-skeleton.md` 的表 4b —— 第 2 列无法核，"
              "这不算通过（工具的沉默不是证据）")
        return ["缺表 4b"]
    bad = []
    for r in rows:
        k = (r["own"], r["rel"])
        b = t4b.get(k)
        if b is None:
            print("!! %-20s 跨度 (%s, %s%%) 在表 4b 里没有对应行" % (r["label"], r["own"], r["rel"]))
            bad.append(r["label"])
            continue
        ok = b["p_frz"] == r["p_frz"]
        print("   %-20s P_frz %-8s vs 表4b %-8s (%s)  %s"
              % (r["label"], r["p_frz"], b["p_frz"], b["name"], "一致" if ok else "不符"))
        if not ok:
            bad.append(r["label"])
    return bad


def check_span_cols(rows):
    """第 3 列（自带网格跨度）与第 4 列（相对%）对 `step_h.json` 核。

    先前我把这两列写成"只有 claim_gate 级凭据"，那是不对的保守：
    `nlcsplit/logs/step_h.json` 每行本来就有专门的 `span` 字段与 `pint.becke`，
    第 3 列应逐字等于 `span`，第 4 列应等于 `round(span/|becke|*100, 1)`。
    体系名仍是人写的映射（正文英文 / JSON 中文），所以这里**不猜名字**：
    只有当第 3 列的值在 JSON 里唯一命中一行时才算凭据，多行同值就报"无法唯一定位"。
    """
    p = os.path.join(ROOT, "nlcsplit", "logs", "step_h.json")
    if not os.path.exists(p):
        print("!! 找不到 `nlcsplit/logs/step_h.json` —— 第 3/4 列这次**没核**，不算通过")
        return ["缺 step_h.json"]
    js = json.load(open(p, encoding="utf-8"))
    cands_all = [(r["name"], (r.get("pint") or {}).get("becke"), r.get("span"))
                 for r in js["rows"]]
    cands_all = [(n, b, sp) for n, b, sp in cands_all if b is not None and sp is not None]
    bad = []
    for row in rows:
        # 按**表格自己的小数位**做数值比对（正文给几位就 round 到几位）。
        # 上一版我用固定宽度 "%.4f" 建索引，于是正文的短写法一律对不上长写法 ——
        # 8 行全报"无对应值"，那是我的格式 bug 不是数据缺失（今晚第三次"解析器假阴性"）。
        d = len(row["own"].split(".")[1]) if "." in row["own"] else 0
        hits = [(n, b, sp) for n, b, sp in cands_all
                if abs(round(sp, d) - float(row["own"])) < 1e-12]
        if len(hits) != 1:
            print("   %-20s 第3列 %-7s → JSON 命中 %d 行，%s"
                  % (row["label"], row["own"], len(hits),
                     "多行同值，无法唯一定位（不判）" if len(hits) > 1 else "无对应值"))
            bad.append(row["label"])
            continue
        name, b, sp = hits[0]
        rel_calc = round(sp / abs(b) * 100, 1)
        rel_ok = ("%.1f" % rel_calc) == ("%.1f" % float(row["rel"]))
        print("   %-20s 第3列 %s==span(%s) OK；第4列 %s%% vs 由未舍入值算 %.1f%% → %s  [%s]"
              % (row["label"], row["own"], "%.*f" % (d, sp), row["rel"], rel_calc,
                 "一致" if rel_ok else "不符", name))
        if not rel_ok:
            bad.append(row["label"])
    return bad


def main():
    bs, rows = blocks(), table_rows()
    print("# Table 1 逐格转录核对（行身份用唯一钥匙「纯归属跨度」定，不用体系名）")
    print("# 原件块 %d 个（%d 份档）  正文行 %d 行"
          % (len(bs), len(glob.glob(ARCH_GLOB)), len(rows)))
    if not rows:
        print("!! 一行都没解析到：要么表改了格式，要么这条正则读不动 —— 不要把'没读到'当'核对通过'")
        return 2
    used, bad, p_gap = set(), [], []
    for r in rows:
        # 行身份只用"纯归属跨度"这一把钥匙：八格里它本来就互不相同（下面要求唯一，不唯一就报）。
        # P_frz 不当钥匙用是刻意的——第一版拿它当钥匙，四行全对不上，查出来是正文那一列
        # 按**截断**保留三位小数，而档里打到四位（就近取整会得到另一个末位）。
        # 那是"这列怎么写"的问题，不是"行贴错没贴错"的问题，两件事混在一个判据里
        # 会看不出到底哪件事错了，所以分开报：具体数请指归档，不要抄进注释。
        hit = [i for i, b in enumerate(bs) if b["attr"] == r["attr"]]
        if len(hit) != 1:
            print("!! %-20s 归属跨度 %s 对上 %d 个档块（钥匙必须唯一，否则这检查没意义）"
                  % (r["label"], r["attr"], len(hit)))
            bad.append(r["label"])
            continue
        b = bs[hit[0]]
        used.add(hit[0])
        ok_derived = (b["quad"] == r["quad"]) and (b["ratio"] == r["ratio"])
        d = abs(float(b["becke"]) - float(r["p_frz"]))
        # P_frz 与"同一个块里的归属跨度"不是同一个量：档里那个是**公共网格**上的 Becke，
        # 正文那一列写的是普查 JSON 里的 Becke（自带网格）。两者差多少没有先验答案，
        # 所以这里只报差值，不据此判转录失败——失败判给 5/6/7 列，它们必须逐字来自同一个块。
        same = d < 5e-4
        print("   %-20s -> %-8s 原子 %2d  归属 %s  求积 %s  比 %s  %s   [P_frz %s vs 档内公共网格 %+.4f，差 %.4f]"
              % (r["label"], b["name"], b["natoms"], r["attr"], r["quad"], r["ratio"],
                 "5/6/7 列一致" if ok_derived else "导出列不符",
                 r["p_frz"], float(b["becke"]), d))
        if not ok_derived:
            print("       档里同一个块是 求积 %s / 比 %s" % (b["quad"], b["ratio"]))
            bad.append(r["label"])
        if not same:
            p_gap.append((r["label"], r["p_frz"], b["becke"], d))
    unused = [i for i in range(len(bs)) if i not in used]
    if unused:
        print("!! 有 %d 个档块没被任何行用到：%s"
              % (len(unused), "; ".join("%s(%s)" % (bs[i]["name"], bs[i]["file"][-28:]) for i in unused)))
    if p_gap:
        print("# 第 2 列 P_frz 与档内公共网格 Becke 不同（%d 行）——这**不一定是错**："
              "两者本来就是两个量（自带网格 vs 公共网格）。" % len(p_gap))
        print("# 但它意味着正文那一列的出处不在 S33 那三份档里，得另指。逐行差值：")
        for label, printed, arch, d in p_gap:
            print("     %-20s 正文 %-10s 公共网格档 %-14s 差 %.4f" % (label, printed, arch, d))
        print("#   出处已查明（我第一版说『找不到』是搜索范围太窄，只 grep 了两个目录就下结论）："
              "这一列的正式出处是 `MAIN-skeleton.md` 的表 4b，"
              "出货时它被改名成 `docs/tables_and_provenance.md`（make_public_repo.js 的改名表），"
              "所以不在 evidence/ 下。详见 paper/notes/DECISION-G4。")
    print()
    print("## 第 2 列 P_frz：与 `MAIN-skeleton.md` 表 4b 逐字核（钥匙 = 跨度+相对值的组合，不用名字映射）")
    pbad = check_p_frz(rows, skeleton_table4b())
    print()
    print()
    print("## 第 3/4 列：对 `nlcsplit/logs/step_h.json` 的 `span` 字段核（第 4 列由未舍入值重算）")
    sbad = check_span_cols(rows)
    print()
    if bad or unused or pbad or sbad:
        print("VERDICT NOTCLEAN —— 见上面 !! 行与「不符/无法唯一定位」行")
        return 1
    print("VERDICT OK —— 第 5/6/7 列逐字来自同一个档块（无串行、无改数），"
          "第 2 列 P_frz 与表 4b 逐字相符 ⇒ Table 1 除第 3/4 列（由 claim_gate 管出处）外都有共现级凭据")
    return 0


if __name__ == "__main__":
    sys.exit(main())
