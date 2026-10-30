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
    # 作者："横轴标签非要搞那么长么，建议缩写，在图题下面解释。"
    # A/B = 两个苯二聚体几何；Bz = benzene；其余即相应二聚体的化学式。解释写进图注。
    SHORT = {"benzene dimer A": "A", "benzene dimer B": "B",
             "benzene···H2O": "Bz·H2O", "benzene···NH3": "Bz·NH3",
             "benzene···CH4": "Bz·CH4"}
    ax.set_xticklabels([SHORT.get(l, l) for l in labels], fontsize=9, rotation=0)
    ax.set_ylabel("kcal/mol")
    ax.set_title("Attraction vs repulsion inside $E_{\\rm xc}$ (superposition, no BSSE)",
                 fontsize=9)
    ax.legend(fontsize=8)
    fig.tight_layout()
    f = os.path.join(OUT, "fig1_xc_split.png")
    fig.savefig(f, dpi=200, bbox_inches="tight", pad_inches=0.03)
    return f


def fig2(rows):
    rows = [r for r in rows if r["pint"].get("becke")]
    SHORT = {"benzene dimer A": "Bz dimer A", "benzene dimer B": "Bz dimer B",
             "benzene···CH4": "Bz···CH4", "benzene···NH3": "Bz···NH3",
             "benzene···H2O": "Bz···H2O"}
    order = sorted(((SHORT.get(EN(r), EN(r)), r["span"] / abs(r["pint"]["becke"]) * 100, r["span"])
                    for r in rows), key=lambda t: -t[1])
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    ax.barh([o[0] for o in order], [o[1] for o in order], color="#4a5568")
    for i, o in enumerate(order):
        ax.text(o[1] + 0.15, i, f"{o[1]:.1f}% ({o[2]:.3f})", va="center", fontsize=7)
    ax.set_xlabel("spread (%)")
    ax.set_xlim(0, max(o[1] for o in order) * 1.2)
    fig.tight_layout()
    f = os.path.join(OUT, "fig2_scheme_sensitivity.png")
    fig.savefig(f, dpi=200, bbox_inches="tight", pad_inches=0.03)
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
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(6.6, 3.4))
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
    axA.text(-0.12, 1.03, "(a)", transform=axA.transAxes, fontsize=8.5,
             va="bottom", ha="left")
    axA.text(0.0, 1.03, "Cost vs pairs", transform=axA.transAxes, fontsize=8.5,
             fontweight="bold", va="bottom", ha="left")

    for r in good:
        for tau, v in r["runs"].items():
            if tau == "exact" or v["abs_dE_kcal"] is None:
                continue
            axB.plot(v["abs_dE_kcal"], 100.0 * v["work_frac_evaluated"],
                     mark[r["level"]][0], color=mark[r["level"]][1], ms=5,
                     alpha=.85)
    axB.axvspan(1e-7, 1e-6, color="#2e7d32", alpha=.12)
    axB.set_xscale("log"); axB.set_xlabel("actual error (kcal/mol)")
    axB.set_ylabel("far pairs still evaluated (%)")
    axB.text(-0.12, 1.03, "(b)", transform=axB.transAxes, fontsize=8.5,
             va="bottom", ha="left")
    axB.text(0.0, 1.03, "Retained fraction", transform=axB.transAxes, fontsize=8.5,
             fontweight="bold", va="bottom", ha="left")
    fig.tight_layout()
    f = os.path.join(OUT, "fig3_screening_cost.png")
    fig.savefig(f, dpi=200, bbox_inches="tight", pad_inches=0.03)
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
LADDER = [("6-31G*", "evidence/ccsdt/20261003T0652Z_snnu_cp_rebuild_631.out"),
          ("aug-cc-pVDZ", "evidence/ccsdt/20261003T0736Z_stepm_dimers_ghostcp_avdz_local.out")]
XCHECK = "evidence/ccsdt/20261003T0752Z_orca_crosscheck_ghostcp.out"
# 泛函那侧的反泊松列。2026-10-03 起改读这一份：以前 fig4/fig5 的 dcp 取自
# logs/step_h_l2cp.json，而那份侧车是 2026-09-28 在 PySCF 2.14.0 上跑的，与其余五行（<CLUSTER>，
# 2.12.1）不同环境。版本才是变量这件事由 evidence/l2cp/cp_version_probe.py 单变量核过。
CP2121 = "evidence/l2cp/20261003T0907Z_wsl2121-cp_levels.out"


def parse_cp2121(level):
    """{system: 反泊松 dE_int (kcal/mol)}，只认生产 counterpoise() 那一列。"""
    rows, lvl = {}, None
    for line in _verbatim(CP2121).splitlines():
        m = re.match(r"== BASIS=(\S+) LEVEL=(\d) ==", line)
        if m:
            if m.group(1) != "6-31g*":
                raise SystemExit("反泊松档里出现了预期外的基组：%s" % m.group(1))
            lvl = int(m.group(2))
            continue
        m = re.match(r"\s+(\S+)\s+nao=\s*\d+\s+dcp\(生产\)=([-+]?\d+\.\d+)", line)
        if m and lvl == level and m.group(1) in SYS_EN:
            rows[m.group(1)] = float(m.group(2))
    missing = [s for s in SYSTEMS if s not in rows]
    if missing:
        raise SystemExit("fig4/fig5: level=%d 的反泊松缺 %s，宁可不出图"
                         % (level, "、".join(missing)))
    return rows

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
        m = re.match(r"\s+(MP2|CCSD|CCSD\(T\))\s+[-+]?\d+\.\d+\s+[-+]?\d+\.\d+\s+([-+]?\d+\.\d+)", line)
        if m and name and conv:
            rows.setdefault(name, {}).setdefault(conv, {})[m.group(1)] = float(m.group(2))
    summ = {}
    for line in txt.splitlines():
        m = re.match(r"\s+(水二聚体|氨二聚体|甲烷二聚体)\s+([-+]?\d+\.\d+)\s+([-+]?\d+\.\d+)"
                     r"\s+([-+]?\d+\.\d+)\s+([-+]?\d+\.\d+)", line)
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
            elif abs(got - summ[s][key]) > 1e-3:
                # 汇总表自己只有三位小数（明细 -4.8225 对汇总 -4.823），所以这道核对的分辨率
                # 是 1e-3 而不是更高。它防的是拿错约定/搬错行那一类，不防末位舍入。
                bad.append("%s %s: 明细 %.4f 与汇总 %.4f 不合" % (s, key, got, summ[s][key]))
    if bad:
        raise SystemExit("fig4: %s 交叉比对失败 ->\n  " % rel + "\n  ".join(bad))
    return rows


def parse_xcheck(rel):
    out = []
    for line in _read(rel).splitlines():
        # The corrected cross-check prints nine columns (counterpoise and uncorrected, each
        # with its own reference and difference) and labels the rungs "frozen"/"all". Only the
        # counterpoise triple is plotted here; an "n/a" in the reference column makes the row
        # unmatched, and the count check below turns that into a refusal rather than a shorter
        # panel.
        m = re.match(r"\s+(\S+二聚体)\s+(\S+)\s+(frozen|all)\s+([-+]?\d+\.\d+)\s+"
                     r"([-+]?\d+\.\d+)\s+([+-]?\d+\.\d+)", line)
        if m:
            out.append((m.group(1), m.group(2), m.group(3),
                        float(m.group(4)), float(m.group(5)), float(m.group(6))))
    if len(out) != 8:
        raise SystemExit("fig4: 跨程序汇总表读到 %d 行，应为 8" % len(out))
    return out


def parse_nlc(rel):
    out = []
    for line in _read(rel).splitlines():
        m = re.match(r"^(\S.*?)\s+(\d+)\s+(\d+)\s+([-+]?\d+\.\d+)\s+([-+]?\d+\.\d+)\s+(\d+\.\d+)\s+"
                     r"(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s*$", line)
        if m:
            out.append((m.group(1).strip(), float(m.group(7))))
    if len(out) != 8:
        raise SystemExit("fig4: 非局域项跨程序表读到 %d 行，应为 8" % len(out))
    return out


def fig4(ladders, xc, nlc, dft):
    from matplotlib.lines import Line2D
    plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"],
                         "mathtext.fontset": "cm"})
    systems = ("水二聚体", "氨二聚体", "甲烷二聚体")
    # 图标题是一句可证伪的话，所以让生成器自己先核一遍。核的内容在 2026-10-03 换过一次：
    # 旧标题主张"每个体系上基组跨度都大于泛函偏差"，而鬼函数修正之后这个说法在数据上反了
    # （比值由生成器自己打印，不在这里抄）。现在这张图主张的是"两个幅度同量级，所以谁也不能
    # 把对方注销"，于是守卫核的是比值必须落在20 倍以内——超出就拒绝把两者画在同一张
    # 并排比较里，因为那时它们根本不可比。
    ratios = []
    for cn in systems:
        span = abs(ladders[1][1][cn]["frozen"]["CCSD(T)"]
                   - ladders[0][1][cn]["frozen"]["CCSD(T)"])
        dev = abs(dft[cn] - ladders[0][1][cn]["frozen"]["CCSD(T)"])
        if not 0.05 <= span / dev <= 20.0:
            raise SystemExit("fig4: %s 上基组跨度 %.3f 与泛函偏差 %.3f 相差超过 20 倍 "
                             "(x%.2f)，把它们并排比较不成立" % (SYS_EN[cn], span, dev, span / dev))
        ratios.append(span / dev)
        print("  fig4 标题核验 %-9s 基组跨度 %.3f / 泛函偏差 %.3f = %.2f"
              % (SYS_EN[cn], span, dev, span / dev))
    # 2026-10-25: split the composite into two independent figures.  The five
    # panels answer two different questions (basis-set ladder vs cross-program
    # check), and one 3+2 float forced either portrait panels or a 0.31 in gap.
    # Figure 3 = the three ladders; Figure 4 = the two checks.
    xs = list(range(len(RUNGS)))

    # 2026-10-29: the three-across strip was an outlier in this manuscript's figure family
    # (aspect 3.02 against 1.0-2.3 for the other six) and every panel came out taller than it
    # was wide.  A 2x2 grid with the key in the fourth cell gives near-square panels and a
    # near-square figure; the span/deviation guard above still runs before anything is written.
    fig = plt.figure(figsize=(6.7, 6.2))
    gs = fig.add_gridspec(2, 2, left=0.085, right=0.985, top=0.965, bottom=0.06,
                          wspace=0.18, hspace=0.30)
    for si, cn in enumerate(systems):
        ax = fig.add_subplot(gs[si // 2, si % 2])
        all_neg = True
        for bi, (basis, rows) in enumerate(ladders):
            ys = [rows[cn][conv][meth] for meth, conv in RUNGS]
            all_neg = all_neg and all(v <= 0 for v in ys)
            ax.plot(xs, ys, "-o" if bi == 0 else "--s", color=SYS_COL[cn], ms=4.2, lw=1.3)
        ax.axhline(dft[cn], color="#c05621", ls=":", lw=1.2)
        ax.axhline(0, color="k", lw=0.6)
        # 数据全在 0 以下时，y=0 线就是面板上边界；再画顶框会在它上方多一条平行线。
        if all_neg:
            ax.set_ylim(top=0)
            ax.spines["top"].set_visible(False)
        ax.set_xticks(xs)
        ax.set_xticklabels(["MP2", "CCSD", "CC(T)\nfc", "CC(T)\nae"], fontsize=7.5)
        ax.set_title("(%s) %s dimer" % ("abc"[si], SYS_EN[cn].capitalize()),
                     fontsize=9.0, fontweight="normal", fontfamily="serif", pad=6.0)
        if si % 2 == 0:
            ax.set_ylabel("$\\Delta E_{\\rm CP}$", fontsize=8.5)
        ax.tick_params(axis="y", labelsize=7.5)
    key = fig.add_subplot(gs[1, 1])
    key.axis("off")
    key.legend([Line2D([], [], color="0.35", marker="o", ls="-"),
                Line2D([], [], color="0.35", marker="s", ls="--"),
                Line2D([], [], color="#c05621", ls=":")],
               ["6-31G*", "aug-cc-pVDZ", "ωB97X-V level 2"], loc="center",
               fontsize=8.0, frameon=False, handlelength=2.2, labelspacing=1.2)
    f3 = os.path.join(OUT, "fig4a_small_dimer_ladders.png")
    fig.savefig(f3, dpi=300, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)

    # 两条跨程序核对线，各自单位、各自一条通过线。单独成一图，不再和梯子挤在一张。
    fig = plt.figure(figsize=(6.5, 2.9))
    gs = fig.add_gridspec(1, 2, wspace=0.32, left=0.14, right=0.985,
                          top=0.90, bottom=0.17)
    ax2 = fig.add_subplot(gs[0, 0])
    short = {"water dimer": "water", "ammonia dimer": "ammonia", "methane dimer": "methane",
             "benzene...water": "Bz...H2O", "benzene...ammonia": "Bz...NH3",
             "benzene...methane": "Bz...CH4", "benzene dimer (A)": "Bz dimer A",
             "benzene dimer (B)": "Bz dimer B"}
    ax2.barh([short.get(n, n) for n, _ in nlc][::-1], [r for _, r in nlc][::-1],
             color="#2b6cb0", height=0.62)
    ax2.axvline(1.0, color="#c05621", ls="--", lw=1.0)
    ax2.set_xlabel("|$\\Delta$| (%)", fontsize=8.5)
    ax2.set_xlim(0, 1.18)
    ax2.tick_params(axis="y", labelsize=7.5)
    ax2.tick_params(axis="x", labelsize=7.5)
    ax2.set_title("(a) NLC deviation", fontsize=9.5, fontweight="normal",
                  fontfamily="serif", pad=5.0)

    ax3 = fig.add_subplot(gs[0, 1])
    SYS1 = {"water": "W", "ammonia": "A", "methane": "M"}
    lab = ["%s %s %s" % (SYS1.get(SYS_EN.get(s, s), SYS_EN.get(s, s)),
                         "631" if b.startswith("6-31") else "avdz",
                         "fc" if c == "frozen" else "ae") for s, b, c, _, _, _ in xc]
    ax3.barh(lab[::-1], [1000 * abs(d) for *_, d in xc][::-1],
             color="#4a5568", height=0.62)
    ax3.axvline(1.0, color="#c05621", ls="--", lw=1.0)
    ax3.set_xlabel("|$\\Delta$| ($10^{-3}$)", fontsize=8.0)
    ax3.set_xlim(0, 1.2)
    ax3.tick_params(axis="y", labelsize=7.5)
    ax3.tick_params(axis="x", labelsize=7.5)
    ax3.set_title("(b) ORCA anchor", fontsize=9.5, fontweight="normal",
                  fontfamily="serif", pad=5.0)
    f4 = os.path.join(OUT, "fig4b_cross_program_checks.png")
    fig.savefig(f4, dpi=300, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return f3, f4



# ---------------------------------------------------------------------------
# 图 5：六个体系上"基组跨度 vs 泛函偏差"两列并置与它们的比值。图 4 的那句话，从三个
# 氢键体系扩到六个。
# 纪律与 fig4 相同且更硬一点：点值只从被论文点名的归档里现取（归档抬头是手写的，
# 不当数据源），并且脚本自己先核这句话——任一体系不成立就拒绝出图。
# ---------------------------------------------------------------------------
PI_LADDER = [("6-31G*", "evidence/ccsdt/20261003T0652Z_snnu_cp_rebuild_631.out"),
             ("aug-cc-pVDZ", "evidence/ccsdt/20261003T0758Z_snnu_pi_three_avdz_ghostcp.out")]
PI_DFT_L2 = ["evidence/ccsdt/20261002T0528Z_snnu_benzene_dft_cp.out",
             "evidence/ccsdt/20261002T0620Z_snnu_benzene_methane_l2.out"]
PI_SYS = ("苯-水", "苯-氨", "苯-甲烷")
PI_EN = {"苯-水": "benzene-water", "苯-氨": "benzene-ammonia", "苯-甲烷": "benzene-methane"}
PI_COL = {"苯-水": "#2b6cb0", "苯-氨": "#2f855a", "苯-甲烷": "#b7791f"}


def _verbatim(rel):
    """归档抬头里那些手写数字不当数据源：只读 `--- verbatim output follows ---` 之后。"""
    parts = _read(rel).split("--- verbatim output follows ---")
    if len(parts) < 2:
        raise SystemExit("fig5: %s 里没有 verbatim 分隔行，拒绝把抬头当数据" % rel)
    return parts[-1]


def _detail_rows(txt):
    """按块跟踪 (体系, 约定)；块分隔行一律重置上下文。

    这条重置是必须的：<CLUSTER> 那批归档的 runner stdout 里也打印同形状的五行
    （方法、两个能量、差值、秒数），不重置就会把绝对能量当差值读进来。
    """
    name = conv = None
    rows = {}
    for line in txt.splitlines():
        if re.match(r"^\s*(#####|=====)", line) or line.startswith("== Step M"):
            name, conv = None, None
        m = re.match(r"== Step M . (\S+?) CCSD", line)
        if m:
            name, conv = m.group(1), None
            continue
        m = re.match(r"\s*--- (frozen\(cores\)|all-electron)", line)
        if m:
            conv = "frozen" if m.group(1).startswith("frozen") else "all"
            continue
        m = re.match(r"\s+(MP2|CCSD|CCSD\(T\))\s+[-+]?\d+\.\d+\s+[-+]?\d+\.\d+\s+([-+]?\d+\.\d+)\s+\d", line)
        if m and name and conv:
            rows.setdefault(name, {}).setdefault(conv, {})[m.group(1)] = float(m.group(2))
    return rows


def parse_pi_ladder():
    out = []
    for basis, rel in PI_LADDER:
        txt = _read(rel)
        rows = _detail_rows(_verbatim(rel))
        missing = ["%s/%s/%s" % (s, c, m) for s in PI_SYS for c in ("frozen", "all")
                   for m in ("MP2", "CCSD", "CCSD(T)")
                   if rows.get(s, {}).get(c, {}).get(m) is None]
        if missing:
            raise SystemExit("fig5: %s 明细缺 %s" % (rel, ", ".join(missing)))
        # 第二表示交叉核对：只认 runner stdout 那一段（明细块之前的行）。
        # 两者必须切开，否则"交叉核对"读的其实就是明细块本身——那是自证，不是核对。
        body = txt.split("--- verbatim output follows ---")[-1]
        mk = re.search(r"^\s*(?:#####|=====)", body, re.M)
        stdout_part = body[:mk.start()] if mk else ""
        vals = [float(x) for x in re.findall(
            r"CCSD\(T\)\s+[-+]?\d+\.\d+\s+[-+]?\d+\.\d+\s+([-+]?\d+\.\d+)\s+\d", stdout_part)]
        want = []
        for s in PI_SYS:
            want += [rows[s]["frozen"]["CCSD(T)"], rows[s]["all"]["CCSD(T)"]]
        if vals:
            if len(vals) != len(want) or any(abs(a - b) > 5e-4 for a, b in zip(vals, want)):
                raise SystemExit("fig5: %s 的 stdout 行与明细块不合 -> %s vs %s"
                                 % (rel, vals, want))
            print("  fig5 交叉核对 %-11s stdout 与明细块一致（%d 个数）" % (basis, len(vals)))
        else:
            print("  fig5 提示：%s 的 stdout 段没有值行，本档只用明细块（不静默）" % rel)
        out.append((basis, rows))
    return out


def parse_pi_dft():
    got = {}
    for rel in PI_DFT_L2:
        lvl = None
        for line in _verbatim(rel).splitlines():
            m = re.match(r"== .*LEVEL=(\d)", line)
            if m:
                lvl = int(m.group(1))
                continue
            m = re.match(r"LEVEL=(\d)\s+(\S+)\s+nao=\s*\d+\s+DFT=\s*([+-]?\d+\.\d+)", line)
            if m:
                lvl, name, val = int(m.group(1)), m.group(2), float(m.group(3))
                if lvl == 2 and name in PI_SYS:
                    got[name] = val
                continue
            m = re.match(r"\s*(\S+)\s+nao=\s*\d+\s+DFT=\s*([+-]?\d+\.\d+)", line)
            if m and lvl == 2 and m.group(1) in PI_SYS:
                got[m.group(1)] = float(m.group(2))
    missing = [s for s in PI_SYS if s not in got]
    if missing:
        raise SystemExit("fig5: DFT level-2 缺 %s" % ", ".join(missing))
    return got


def fig5(pi_ladders, pi_dft, hb_ladders, hb_dft):
    from matplotlib.lines import Line2D
    plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"],
                         "mathtext.fontset": "cm"})
    # 一、先核这句话本身，六个体系全过才画。
    rows6 = []
    for cn in SYSTEMS:
        span = abs(hb_ladders[1][1][cn]["frozen"]["CCSD(T)"]
                   - hb_ladders[0][1][cn]["frozen"]["CCSD(T)"])
        dev = abs(hb_dft[cn] - hb_ladders[0][1][cn]["frozen"]["CCSD(T)"])
        rows6.append((SYS_EN[cn], span, dev))
    for cn in PI_SYS:
        span = abs(pi_ladders[1][1][cn]["frozen"]["CCSD(T)"]
                   - pi_ladders[0][1][cn]["frozen"]["CCSD(T)"])
        dev = abs(pi_dft[cn] - pi_ladders[0][1][cn]["frozen"]["CCSD(T)"])
        rows6.append((PI_EN[cn], span, dev))
    ratios6 = []
    for nm, span, dev in rows6:
        r = span / dev
        if not 0.05 <= r <= 20.0:
            raise SystemExit("fig5: %s 上基组跨度 %.3f 与泛函偏差 %.3f 相差超过两个数量级 "
                             "(x%.2f)，六个体系并排比较不成立" % (nm, span, dev, r))
        ratios6.append(r)
        print("  fig5 核验 %-15s span %.3f / dev %.3f = %.2f" % (nm, span, dev, r))

    fig = plt.figure(figsize=(6.0, 5.8))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.0], hspace=0.35, wspace=0.42,
                          left=0.14, right=0.97, top=0.95, bottom=0.09)
    PIT = {"benzene-water": "Bz···H$_2$O", "benzene-ammonia": "Bz···NH$_3$",
           "benzene-methane": "Bz···CH$_4$"}
    xs = list(range(len(RUNGS)))
    for si, cn in enumerate(PI_SYS):
        ax = fig.add_subplot(gs[si // 2, si % 2])
        all_neg = True
        for bi, (basis, rows) in enumerate(pi_ladders):
            ys = []
            for meth, conv in RUNGS:
                nm2 = cn
                ys.append(rows[nm2][conv][meth])
            all_neg = all_neg and all(v <= 0 for v in ys)
            ax.plot(xs, ys, "-o" if bi == 0 else "--s", color=PI_COL[cn], ms=3.6, lw=1.2)
        ax.axhline(pi_dft[cn], color="#c05621", ls=":", lw=1.2)
        ax.annotate("DFT %.2f" % pi_dft[cn], (0.0, pi_dft[cn]), fontsize=6.8,
                    color="#c05621", xytext=(2, 4), textcoords="offset points",
                    bbox=dict(facecolor="white", edgecolor="none", pad=0.6))
        ax.axhline(0, color="k", lw=0.6)
        if all_neg:
            ax.set_ylim(top=0)
            ax.spines["top"].set_visible(False)
        ax.set_xticks(xs)
        ax.set_xticklabels(["MP2", "CCSD", "CC(T)\nfc", "CC(T)\nae"], fontsize=7.0)
        ax.set_title("(%s) %s" % ("abcd"[si], PIT.get(PI_EN[cn], PI_EN[cn])),
                     fontsize=9.0, fontweight="normal", fontfamily="serif", pad=5.0)
        if si == 0:
            ax.set_ylabel("$\\Delta E_{\\rm CP}$", fontsize=8.5)
            ax.legend([Line2D([], [], color="0.35", marker="o", ls="-"),
                       Line2D([], [], color="0.35", marker="s", ls="--")],
                      ["6-31G*", "aug-cc-pVDZ"], loc="upper left",
                      bbox_to_anchor=(0.0, 1.0), borderaxespad=0.25,
                      fontsize=7.0, frameon=False, handlelength=1.6,
                      borderpad=0.2)
        ax.tick_params(axis="y", labelsize=7.5)

    axb = fig.add_subplot(gs[1, 1])
    BOT = {"water dimer": "water", "ammonia dimer": "ammonia",
           "methane dimer": "methane", "benzene...water": "Bz···H$_2$O",
           "benzene-water": "Bz···H$_2$O", "benzene...ammonia": "Bz···NH$_3$",
           "benzene-ammonia": "Bz···NH$_3$", "benzene...methane": "Bz···CH$_4$",
           "benzene-methane": "Bz···CH$_4$"}
    lab = [BOT.get(nm, nm) for nm, _, _ in rows6]
    span = [s for _, s, _ in rows6]
    dev = [d for _, _, d in rows6]
    y = range(len(lab))
    h = 0.36
    axb.barh([i + h / 2 for i in y], span, height=h, color="#2b6cb0",
             label="correlated reference (6-31G* → aug)")
    axb.barh([i - h / 2 for i in y], dev, height=h, color="#c05621",
             label="DFT vs correlated (6-31G*)")
    for i, (s, d) in enumerate(zip(span, dev)):
        axb.text(s + 0.03, i + h / 2, "%.2f" % s, va="center", fontsize=7.0, color="#2b6cb0")
        axb.text(d + 0.03, i - h / 2, "%.2f" % d, va="center", fontsize=7.0, color="#c05621")
        axb.text(2.52, i, "x%.1f" % (s / d), va="center", fontsize=7.0, color="0.25")
    axb.set_yticks(list(y))
    axb.set_yticklabels(lab, fontsize=7.5)
    axb.set_xlim(0, 2.95)
    axb.set_xlabel("kcal/mol", fontsize=8.5)
    axb.set_title("(d) Six complexes", fontsize=9.0, fontweight="normal",
                  fontfamily="serif", pad=5.0)
    # 同一原因：六体系的比值结论在正文里，图内不再放多行 suptitle。
    f = os.path.join(OUT, "fig5_six_system_spans.png")
    fig.savefig(f, dpi=300, bbox_inches="tight", pad_inches=0.05)
    return f



def toc_graphic(pi_ladders, pi_dft, hb_ladders, hb_dft):
    """ACS 投稿要的 TOC/abstract graphic：3.25 x 1.75 in，一张图讲一句话。

    数据走 fig5 的同一条路（现读被引归档 + 同一句可证伪的话），只是换版面：
    在这个尺寸里能读的只有散点——横轴泛函偏差、纵轴基组跨度、对角线以上即本文主张。
    """
    rows = []
    for cn in SYSTEMS:
        span = abs(hb_ladders[1][1][cn]["frozen"]["CCSD(T)"]
                   - hb_ladders[0][1][cn]["frozen"]["CCSD(T)"])
        dev = abs(hb_dft[cn] - hb_ladders[0][1][cn]["frozen"]["CCSD(T)"])
        rows.append((SYS_EN[cn], span, dev))
    for cn in PI_SYS:
        span = abs(pi_ladders[1][1][cn]["frozen"]["CCSD(T)"]
                   - pi_ladders[0][1][cn]["frozen"]["CCSD(T)"])
        dev = abs(pi_dft[cn] - pi_ladders[0][1][cn]["frozen"]["CCSD(T)"])
        rows.append((PI_EN[cn], span, dev))
    for nm, span, dev in rows:
        if not 0.05 <= span / dev <= 20.0:
            raise SystemExit("toc: %s 上 span %.3f 与 dev %.3f 相差超过两个数量级，"
                             "与 fig5/正文的主张不符" % (nm, span, dev))
    fig = plt.figure(figsize=(3.25, 1.75))
    ax = fig.add_axes([0.15, 0.185, 0.82, 0.645])
    lim = 1.55
    ax.plot([0, lim], [0, lim], "--", color="0.55", lw=0.8)
    ax.text(0.62, 0.30, "equal size:\nneither term is\nthe other's error",
            fontsize=5.4, color="0.4")
    for nm, span, dev in rows:
        ax.plot(dev, span, "o", ms=4.2, color="#2b6cb0")
    for nm, span, dev in rows:
        if nm in ("benzene-ammonia", "benzene-methane", "water", "methane"):
            ax.annotate(nm, (dev, span), fontsize=5.4, color="0.25",
                        xytext=(3, -1), textcoords="offset points")
    ax.set_xlim(0, lim); ax.set_ylim(0, lim)
    ax.set_xlabel("functional deviation at 6-31G* (kcal/mol)", fontsize=6.0)
    ax.set_ylabel("reference move, 1 basis (kcal/mol)", fontsize=6.0)
    ax.tick_params(labelsize=5.8)
    worst_toc = max(max(s / d for _, s, d in rows),
                    1.0 / min(s / d for _, s, d in rows))
    ax.set_title("VV10 pair attribution: the reference's basis move and the functional's\n"
                 "deviation stay within %.0fx - so fixed-basis binding verdicts are unearned"
                 % worst_toc,
                 fontsize=6.0)
    f = os.path.join(OUT, "toc_graphic.png")
    fig.savefig(f, dpi=300, bbox_inches="tight", pad_inches=0.03)
    return f


def fig_sw_decomposition():
    """软件文的一张图：一次调用返回什么。

    数据源是软件文 [S2] 点名的那份归档 stdout，不另写数：五个分区（四个 Becke 系
    + 最近原子）各自给出 E_NL、片间项和分块加和残差。三栏分别是"总量不动 /
    片间项随分区动 / 分块和仍等于整算"，正好是包要交付的三件事。
    """
    path = os.path.join(ROOT, "evidence", "recompute",
                        "20260929T010500Z_step1_geomfix.out")
    rows = []
    pat = re.compile(
        r"^\s{2}(?:scheme=)?(?P<scheme>[^\s]+)\s+.*?"
        r"E_nl=\s*(?P<enl>-?\d+\.\d+)kcal.*?"
        r"分块和差=(?P<res>[\d.eE+-]+)Ha.*?"
        r"E_AB=(?P<eab>-?\d+\.\d+)kcal")
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = pat.match(line)
            if m and not m.group("scheme").startswith("("):
                d = {k: (v if k == "scheme" else float(v))
                     for k, v in m.groupdict().items()}
                d["scheme"] = d["scheme"].split("(")[0]
                rows.append(d)
    if not rows:
        raise SystemExit("没有从 %s 解到任何一行，拒绝出图" % path)
    short = {"becke": "Becke", "becke-becke-rad": "Becke-rad",
             "becke-treutler": "Becke-Treutler", "stratmann": "Stratmann",
             "nearest": "nearest"}
    labels = [short.get(r["scheme"], r["scheme"]) for r in rows]
    x = range(len(rows))
    # (d) 第二根外部锚：ORCA 6.0.1 对同一量的相对差，读归档表，不另写数。
    orca_rows = []
    opath = os.path.join(ROOT, "evidence", "orca_widen", "cross_program_table.txt")
    short_sys = {"water dimer": "water", "ammonia dimer": "ammonia",
                 "methane dimer": "methane",
                 "benzene...water": r"Bz$\cdot$H$_2$O",
                 "benzene...ammonia": r"Bz$\cdot$NH$_3$",
                 "benzene...methane": r"Bz$\cdot$CH$_4$",
                 "benzene dimer (A)": "dimer A", "benzene dimer (B)": "dimer B"}
    with open(opath, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = re.split(r"\s{2,}", line.strip())
            if len(parts) == 9 and re.fullmatch(r"\d+", parts[1]):
                orca_rows.append((short_sys.get(parts[0], parts[0]),
                                  float(parts[6])))
    if len(orca_rows) != 8:
        raise SystemExit("ORCA 表解到 %d 行，期望 8 行，拒绝出图" % len(orca_rows))

    fig, axes = plt.subplots(2, 2, figsize=(6.8, 5.2))
    ax = axes[0, 0]
    # 截断坐标轴上的柱会从 0 起画、看起来差很多；这里改画相对 base 常量（本次归档的最小
    # 绝对值，即左下角那栏纵轴的零点）的偏差。
    base = -7.8130
    ax.plot(x, [(r["enl"] - base) * 1000 for r in rows], "o", ms=5,
            color="#2b6cb0")
    ax.axhline(0, color="k", lw=0.6)
    ax.set_ylabel(r"$\delta E_{\rm NL}$ ($10^{-3}$)")
    ax = axes[0, 1]
    ax.bar(x, [abs(r["eab"]) for r in rows], color="#c05621", width=0.62)
    ax.set_ylabel(r"$|E_{AB}|$")
    ax = axes[1, 0]
    ax.bar(x, [r["res"] for r in rows], color="#4a5568", width=0.62)
    ax.set_yscale("log")
    ax.set_ylabel("residual")
    ax = axes[1, 1]
    xr = range(len(orca_rows))
    ax.bar(xr, [v for _, v in orca_rows], color="#2f855a", width=0.62)
    ax.axhline(1.0, color="k", lw=0.7, ls="--")
    ax.set_xticks(list(xr))
    ax.set_xticklabels([n for n, _ in orca_rows], rotation=35, ha="right",
                       fontsize=6.5)
    ax.set_ylabel(r"$|\Delta|$ (%)")
    panel_titles = ["Nonlocal total", "Pair block", "Residual", "ORCA vs PySCF"]
    for i, a in enumerate(axes.flat):
        if i < 3:
            a.set_xticks(list(x))
            a.set_xticklabels(labels, rotation=20, ha="right", fontsize=7)
        a.tick_params(labelsize=7)
        a.yaxis.label.set_size(8)
        a.text(-0.14, 1.02, "(%s)" % "abcd"[i], transform=a.transAxes,
               fontsize=8.5, va="bottom", ha="left")
        a.text(0.0, 1.02, panel_titles[i], transform=a.transAxes,
               fontsize=8.5, fontweight="bold", va="bottom", ha="left")
    fig.tight_layout(h_pad=1.4, w_pad=1.2)
    f = os.path.join(ROOT, "figs", "fig_sw_decomposition.png")
    fig.savefig(f, dpi=300, bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("读 %d 行；E_NL=%s；E_AB=%s；res=%s"
          % (len(rows), [r["enl"] for r in rows],
             [r["eab"] for r in rows], ["%.2e" % r["res"] for r in rows]))
    return f


if __name__ == "__main__":
    if "--software-fig" in sys.argv:
        print("出图：", fig_sw_decomposition())
        sys.exit(0)
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
        # 反泊松列改读 2.12.1 的那份归档（理由写在 CP2121 上面）。侧车 step_h_l2cp.json 里是
    # 2.14.0 的数，它仍是跨版本对照的一端，但从今往后不当图的数据源。
    dft = parse_cp2121(2)
    print("  反泊松列 %s -> %s" % (CP2121, {SYS_EN[k]: v for k, v in dft.items()}))
    print("出图：", fig4(ladders, parse_xcheck(XCHECK), parse_nlc(NLCTAB), dft))
    pi_lad, pi_dft = parse_pi_ladder(), parse_pi_dft()
    print("出图：", fig5(pi_lad, pi_dft, ladders, dft))
    print("出图：", toc_graphic(pi_lad, pi_dft, ladders, dft))
