"""出图：读 step_*.py 的 JSON 侧车，不解析日志文本。

图 1  吸引/排斥分开：每体系 ΔE_NLC 与 ΔE_xc(其余) 两根柱（色散体系里后者是正的）
图 2  归属方案不确定度：跨度占 |P_frz| 的百分比，按体系类型排
图 3  P2 的主图：可证屏蔽的代价。数据源走 load_cited()，即**论文点名的那两个
      evidence/scaling 工件**，并且两个时间窗一起画 —— 少画一窗等于替正文少报一个
      对本方不利的数。只有单窗可用时退回单窗并打印警告，不静默。
"""
import json
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from nlcsplit import geomlib

EN = lambda r: geomlib.S22_EN.get(r["name"], r["name"])

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # 仓库根：被论文引用的工件都以它为起点
OUT = os.path.join(HERE, "..", "figs")
os.makedirs(OUT, exist_ok=True)


def load(name):
    """读侧车。只读**被 git 跟踪、被论文引用**的那一份。

    09-30 之前 fig3 走的是 `logs/step_j.json`——那是同一天晚些时候的一次运行，
    5 行，而且 logs/ 下的 step_j 没有被跟踪；论文和 §6 表引的却是
    `evidence/scaling/step_j.json`（6 行，09-29）。图和数据源就此分叉：
    读者对着正文核图，会看到图上少一档体系。所以现在按仓库根相对路径取被引工件。
    """
    p = os.path.join(HERE, "logs", name)
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def load_cited(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(p):
        print(f"警告：被引工件不存在，跳过 {rel}")
        return None
    return json.load(open(p, encoding="utf-8"))


def fig1(rows):
    labels = [EN(r) for r in rows]
    nlc = [r["dnlc"] for r in rows]
    rest = [r["dxc"] - r["dnlc"] for r in rows]
    x = range(len(rows))
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    w = 0.38
    ax.bar([i - w / 2 for i in x], nlc, w, label=r"$\Delta E_{\rm NLC}$ (VV10 term)",
           color="#2b6cb0")
    ax.bar([i + w / 2 for i in x], rest, w,
           label=r"$\Delta E_{\rm xc}$ rest (semilocal + exact exch.)", color="#c05621")
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=8, rotation=30, ha="right")
    ax.set_ylabel("kcal/mol")
    ax.set_title("Attraction vs repulsion inside $E_{\\rm xc}$ (superposition, no BSSE)",
                 fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    f = os.path.join(OUT, "fig1_xc_split.png")
    fig.savefig(f, dpi=200)
    return f


def fig2(rows):
    rows = [r for r in rows if r["pint"].get("becke")]
    order = sorted(((EN(r), r["span"] / abs(r["pint"]["becke"]) * 100, r["span"])
                    for r in rows), key=lambda t: -t[1])
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ax.barh([o[0] for o in order], [o[1] for o in order], color="#4a5568")
    for i, o in enumerate(order):
        ax.text(o[1] + 0.15, i, f"{o[1]:.1f}%  (spread {o[2]:.3f})", va="center", fontsize=7)
    ax.set_xlabel("scheme spread / |P_frz|  (%)")
    ax.set_xlim(0, max(o[1] for o in order) * 1.5)
    ax.set_title("Scheme uncertainty is system-dependent (0.8-18%): report per system,\n"
                 "not as one blanket percentage", fontsize=8.5)
    fig.tight_layout()
    f = os.path.join(OUT, "fig2_scheme_sensitivity.png")
    fig.savefig(f, dpi=200)
    return f


def fig3(windows):
    """P2 的主图：可证屏蔽**为什么不划算**。只用通过争用闸门的样本。

    windows = [(窗口标签, rows), ...]。正文报的是两个独立时间窗（33 对，无一更快），
    图只画第一个窗就等于替正文少报一个对本方不利的数——09-30 那版正是如此：
    第二次窗口跑出来后一直没并进来。

    (a) 墙钟 vs 实际评估的 far 点对数，exact 与"精度可用的那一档"用连线成对；
    (b) 保留的 far 点对比例 vs 实际误差，把论文需要的 1e-6 kcal/mol 画成一条带。

    标题与 §6 同步：这是**争用闸门**（采样瞬间外部可运行任务数为 0），不是"机器空载"。
    那句话在正文里已经撤回，图上的字必须一起撤回。
    """
    good = []
    for label, rows in windows:
        ok = [r for r in rows if all(v["valid_timing"] for v in r["runs"].values())]
        print(f"  窗口 {label}: 通过争用闸门 {len(ok)}/{len(rows)}")
        for r in ok:
            r = dict(r); r["_win"] = label
            good.append(r)
    if len(good) < 2:
        sys.exit(f"通过争用闸门的样本只有 {len(good)} 个，不出图（宁可不出，也别出错图）")
    n_win = len({r["_win"] for r in good})
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    mark = {0: ("o", "#3b6ea5"), 1: ("s", "#c0504d")}
    # 同一体系在两个窗口里同色同形，只换线型：多加一种形状会让读者把"第二次测量"
    # 读成第三个体系。空心=归档窗口，实心=重跑窗口。
    order = sorted({r["_win"] for r in good})
    for wi, wlabel in enumerate(order):
        ls = "-" if wi == 0 else "--"
        for lvl in (0, 1):
            sub = sorted([r for r in good if r["level"] == lvl and r["_win"] == wlabel],
                         key=lambda r: r["runs"]["exact"]["pointpairs_far"])
            # 以前这里 `if len(sub) < 2: continue`——单个点的子集不连线，但它也是通过
            # 争用闸门的样本，跳过就等于图上少一个体系、正文的"11 个全画"变成假话。
            # 线型对单点无害（画不出线段而已），所以不再跳过。
            if not sub:
                continue
            m, c = mark[lvl]
            axA.plot([r["runs"]["exact"]["pointpairs_far"] for r in sub],
                     [r["runs"]["exact"]["wall_s"] for r in sub], m + ls, color=c,
                     mfc="none" if wi == 0 else c, label=f"exact, level {lvl}, {wlabel}")
            axA.plot([r["runs"]["tau1e-12"]["pointpairs_evaluated"] for r in sub],
                     [r["runs"]["tau1e-12"]["wall_s"] for r in sub], m + ls, color=c,
                     mew=1.1, label=f"screened 1e-12, level {lvl}, {wlabel}")
            for r in sub:                          # 同一体系：功变少、时间变多
                axA.plot([r["runs"]["exact"]["pointpairs_far"],
                          r["runs"]["tau1e-12"]["pointpairs_evaluated"]],
                         [r["runs"]["exact"]["wall_s"], r["runs"]["tau1e-12"]["wall_s"]],
                         ls, color=c, lw=.8, alpha=.5, zorder=0)
    axA.set_xscale("log"); axA.set_yscale("log")
    axA.set_xlabel("far point pairs actually evaluated")
    axA.set_ylabel("wall clock (s)")
    axA.set_title(f"(a) contention gate: external runnable tasks = 0 at each sampling instant;"
                  f" {n_win} timing windows\n"
                  "each connector = same system: less work, more time — not an idle-box claim",
                  fontsize=7.6)
    axA.legend(fontsize=5.0, loc="upper left")

    for r in good:
        for tau, v in r["runs"].items():
            if tau == "exact" or v["abs_dE_kcal"] is None:
                continue
            axB.plot(v["abs_dE_kcal"], 100.0 * v["work_frac_evaluated"],
                     mark[r["level"]][0], color=mark[r["level"]][1], ms=5,
                     alpha=.85)
    axB.axvspan(1e-7, 1e-6, color="#2e7d32", alpha=.12)
    axB.text(1e-6, axB.get_ylim()[1] * .42, "what the paper needs\n(|dE| ≤ 1e-6 kcal/mol)",
             fontsize=6.8, ha="right", color="#2e7d32")
    axB.set_xscale("log"); axB.set_xlabel("actual error |E_screened − E_exact|  (kcal/mol)")
    axB.set_ylabel("far point pairs still evaluated  (%)")
    axB.set_title("(b) work saved is a function of accuracy you cannot afford to give up",
                  fontsize=8.5)
    fig.tight_layout()
    f = os.path.join(OUT, "fig3_screening_cost.png")
    fig.savefig(f, dpi=200)
    return f


# ---------------------------------------------------------------------------
# 图 4 · 结合能锚点的两条核对线。
#
# 为什么值得多这一张图：§3.2 与 §4.2 现在各有一张数字表（四级阶梯对 DFT、两个程序的
# 残差），读者要自己在两张表之间来回核对"到底是泛函偏了还是参考偏了"。一张图把
# "随基组动的幅度" 与 "跨程序残差的幅度" 放进同一个量级比较里，结论就自明了：
# 基组效应比两程序之差大两个数量级，所以本文不据结合能判泛函。
#
# 数据来源纪律（照 fig3 的做法）：点位置全部从**被论文点名的 stdout** 里现读，
# 并与同一文件自带的汇总表交叉比对；任一体系缺档、或两处读数不合，就拒绝出图。
# 归档抬头里那些手写的引文不当数据源。
# ---------------------------------------------------------------------------
LADDER = [("6-31G*", "evidence/ccsdt/20260930T235900Z_stepm_three_systems_631g.out"),
          ("aug-cc-pVDZ", "evidence/ccsdt/20261001T000400Z_stepm_three_systems_avdz.out")]
XCHECK = "evidence/ccsdt/20261001T052943Z_orca_crosscheck_three_systems.out"
NLCTAB = "evidence/orca_widen/cross_program_table.txt"
SYS_EN = {"水二聚体": "water", "氨二聚体": "ammonia", "甲烷二聚体": "methane"}
SYS_COL = {"水二聚体": "#2b6cb0", "氨二聚体": "#2f855a", "甲烷二聚体": "#b7791f"}
SYSTEMS = ("水二聚体", "氨二聚体", "甲烷二聚体")
RUNGS = (("MP2", "frozen"), ("CCSD", "frozen"), ("CCSD(T)", "frozen"), ("CCSD(T)", "all"))


def _read(rel):
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(p):
        raise SystemExit("fig4: 被引工件缺失 -> %s" % rel)
    return open(p, encoding="utf-8", errors="replace").read()


def parse_ladder(rel):
    """明细块与文件自带的汇总表都读，然后比对；不合就抛，不出图。"""
    txt = _read(rel)
    rows, name, conv = {}, None, None
    for line in txt.splitlines():
        m = re.match(r"== Step M . (\S+?) CCSD", line)
        if m:
            name, conv = m.group(1), None
            continue
        m = re.match(r"\s*--- (frozen\(cores\)|all-electron)\s", line)
        if m:
            conv = "frozen" if m.group(1).startswith("frozen") else "all"
            continue
        m = re.match(r"\s+(MP2|CCSD|CCSD\(T\))\s+-?\d+\.\d+\s+-?\d+\.\d+\s+(-?\d+\.\d+)", line)
        if m and name and conv:
            rows.setdefault(name, {}).setdefault(conv, {})[m.group(1)] = float(m.group(2))
    summ = {}
    for line in txt.splitlines():
        m = re.match(r"\s+(水二聚体|氨二聚体|甲烷二聚体)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)"
                     r"\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", line)
        if m:
            summ[m.group(1)] = dict(zip(("MP2", "CCSD", "CCSD(T)", "all"),
                                        (float(x) for x in m.groups()[1:])))
    bad = []
    for s in SYSTEMS:
        if s not in rows or s not in summ:
            bad.append("%s 在两处之一缺席（明细 %s / 汇总 %s）"
                       % (s, s in rows, s in summ))
            continue
        for key, conv_w, meth in (("MP2", "frozen", "MP2"), ("CCSD", "frozen", "CCSD"),
                                  ("CCSD(T)", "frozen", "CCSD(T)"),
                                  ("all", "all", "CCSD(T)")):
            got = rows[s].get(conv_w, {}).get(meth)
            if got is None:
                bad.append("%s %s/%s 无明细行" % (s, conv_w, meth))
            elif abs(got - summ[s][key]) > 5e-4:
                bad.append("%s %s: 明细 %.4f 与汇总 %.4f 不合" % (s, key, got, summ[s][key]))
    if bad:
        raise SystemExit("fig4: %s 交叉比对失败 ->\n  " % rel + "\n  ".join(bad))
    return rows


def parse_xcheck(rel):
    out = []
    for line in _read(rel).splitlines():
        m = re.match(r"\s+(\S+二聚体)\s+(\S+)\s+(frozen|all-e)\s+(-?\d+\.\d+)\s+"
                     r"(-?\d+\.\d+)\s+([+-]?\d+\.\d+)\s*$", line)
        if m:
            out.append((m.group(1), m.group(2), m.group(3),
                        float(m.group(4)), float(m.group(5)), float(m.group(6))))
    if len(out) != 8:
        raise SystemExit("fig4: 跨程序汇总表读到 %d 行，应为 8" % len(out))
    return out


def parse_nlc(rel):
    out = []
    for line in _read(rel).splitlines():
        m = re.match(r"^(\S.*?)\s+(\d+)\s+(\d+)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(\d+\.\d+)\s+"
                     r"(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s*$", line)
        if m:
            out.append((m.group(1).strip(), float(m.group(7))))
    if len(out) != 8:
        raise SystemExit("fig4: 非局域项跨程序表读到 %d 行，应为 8" % len(out))
    return out


def fig4(ladders, xc, nlc, dft):
    from matplotlib.lines import Line2D
    systems = ("水二聚体", "氨二聚体", "甲烷二聚体")
    # 图标题是一句可证伪的话，所以让生成器自己先核一遍：每个体系"相关参考值随基组的移动"
    # 必须严格大于"本文泛函对该参考值的偏差"。哪一体系不成立就拒绝出图，而不是把标题
    # 改软到无法反驳——这张图的全部意义就在于两个幅度可以被比较。
    for cn in systems:
        span = abs(ladders[1][1][cn]["frozen"]["CCSD(T)"]
                   - ladders[0][1][cn]["frozen"]["CCSD(T)"])
        dev = abs(dft[cn] - ladders[0][1][cn]["frozen"]["CCSD(T)"])
        if not span > dev:
            raise SystemExit("fig4: %s 上基组跨度 %.3f 不大于泛函偏差 %.3f，标题不成立"
                             % (cn, span, dev))
        print("  fig4 标题核验 %-9s 基组跨度 %.3f > 泛函偏差 %.3f kcal/mol"
              % (SYS_EN[cn], span, dev))
    fig = plt.figure(figsize=(6.8, 6.1))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.2, 1.0], hspace=0.52, wspace=0.62,
                          left=0.155, right=0.965, top=0.845, bottom=0.095)
    xs = list(range(len(RUNGS)))

    # (a1..a3) 每个体系一根自己的纵轴：混在一张轴上，水/氨/甲烷的量级差会把后两个压扁。
    for si, cn in enumerate(systems):
        ax = fig.add_subplot(gs[0, si])
        for bi, (basis, rows) in enumerate(ladders):
            ys = [rows[cn][conv][meth] for meth, conv in RUNGS]
            ax.plot(xs, ys, "-o" if bi == 0 else "--s", color=SYS_COL[cn], ms=4.0, lw=1.3)
        ax.axhline(dft[cn], color="#c05621", ls=":", lw=1.2)
        ax.annotate("this work  %.3f" % dft[cn], (0.0, dft[cn]), fontsize=6.2,
                    color="#c05621", xytext=(2, 4), textcoords="offset points")
        ax.axhline(0, color="k", lw=0.6)
        ax.set_xticks(xs)
        ax.set_xticklabels(["MP2", "CCSD", "CCSD(T)\nfc", "CCSD(T)\nae"], fontsize=6.5)
        ax.set_title("%s dimer" % SYS_EN[cn], fontsize=8)
        if si == 0:
            ax.set_ylabel("$\\Delta E_{\\rm CP}$ (kcal/mol)", fontsize=8)
            ax.legend([Line2D([], [], color="0.35", marker="o", ls="-"),
                       Line2D([], [], color="0.35", marker="s", ls="--")],
                      ["6-31G*", "aug-cc-pVDZ"], loc="upper center", fontsize=6.5,
                      frameon=False)
        ax.tick_params(axis="y", labelsize=7)

    # (b)(c) 两条跨程序核对线，各自单位、各自一条通过线
    ax2 = fig.add_subplot(gs[1, 0:2])
    ax2.barh([n for n, _ in nlc][::-1], [r for _, r in nlc][::-1], color="#2b6cb0", height=0.62)
    ax2.axvline(1.0, color="#c05621", ls="--", lw=1.0)
    ax2.text(0.985, 3.4, "1% of the term  ", fontsize=6.5, color="#c05621", ha="right")
    ax2.set_xlabel("$\\Delta E_{\\rm NLC}$: |ORCA - PySCF| as % of the term", fontsize=7.5)
    ax2.set_xlim(0, 1.18)
    ax2.tick_params(axis="y", labelsize=6.5)
    ax2.set_title("(b) the nonlocal term on 8 systems, grids deliberately not matched",
                  fontsize=8)

    ax3 = fig.add_subplot(gs[1, 2])
    lab = ["%s %s %s" % (SYS_EN.get(s, s),
                         "631G*" if b.startswith("6-31") else "avdz",
                         "fc" if c == "frozen" else "ae") for s, b, c, _, _, _ in xc]
    ax3.barh(lab[::-1], [abs(d) for *_, d in xc][::-1], color="#4a5568", height=0.62)
    ax3.axvline(0.001, color="#c05621", ls="--", lw=1.0)
    ax3.text(0.00095, 3.4, "bar 0.001  ", fontsize=6.5, color="#c05621", ha="right")
    ax3.set_xlabel("CCSD(T): |ORCA-PySCF| (kcal/mol)", fontsize=7)
    ax3.set_xlim(0, 0.0012)
    ax3.tick_params(axis="y", labelsize=6.2)
    ax3.set_title("(c) the anchor itself", fontsize=8)

    fig.suptitle("Per system the correlated reference moves more with the basis than the\n"
                 "functional deviates from it - which is why this paper does not judge the\n"
                 "functional on binding energies", fontsize=8.5, y=0.965)
    f = os.path.join(OUT, "fig4_anchor_crosschecks.png")
    fig.savefig(f, dpi=200)
    return f



if __name__ == "__main__":
    h = load("step_h.json")
    if not h or not h["rows"]:
        sys.exit("没有 logs/step_h.json 侧车，先跑 step_h_s22.py")
    print("侧车：basis=%s level=%s 反泊松=%s 体系数=%d"
          % (h["basis"], h["level"], h["cpcorr"], len(h["rows"])))
    print("出图：", fig1(h["rows"]))
    print("出图：", fig2(h["rows"]))
    # 两个时间窗一起喂：正文报的是 33 对（两窗，无一更快），图少画一窗就是少报一个
    # 对本方不利的数。缺第二个窗时退回单窗并明说，不静默。
    w = []
    j = load_cited("evidence/scaling/step_j.json")
    if j and j["rows"]:
        w.append(("archived", j["rows"]))
    j2 = load_cited("evidence/scaling/step_j_rerun_20260930.json")
    if j2 and j2["rows"]:
        w.append(("rerun 2026-09-30", j2["rows"]))
    if not w:
        print("没有 step_j 侧车，跳过 fig3")
    else:
        if len(w) < 2:
            print("警告：只有一个时间窗，fig3 会与正文的 33 对/两窗口径不一致")
        print("出图：", fig3(w))
    # 图 4：结合能锚点的两条核对线。点位置从**被论文点名的 stdout** 现读，并与同一份
    # 文件自带的汇总表交叉比对（parse_ladder 里），任何一处不合就抛，不出图。
    ladders = [(b, parse_ladder(p)) for b, p in LADDER]
    l2 = load("step_h_l2cp.json") or {}
    dft = {}
    for r in l2.get("rows", []):
        if r["name"] in SYS_EN and r.get("level") == 2 and r.get("cpcorr"):
            dft[r["name"]] = r["dcp"]
    if len(dft) != 3:
        raise SystemExit("fig4: level-2 反泊松的 DFT 对照只取到 %d 个体系（应为 3）" % len(dft))
    print("出图：", fig4(ladders, parse_xcheck(XCHECK), parse_nlc(NLCTAB), dft))
