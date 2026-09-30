"""出图：读 step_*.py 的 JSON 侧车，不解析日志文本。

图 1  吸引/排斥分开：每体系 ΔE_NLC 与 ΔE_xc(其余) 两根柱（色散体系里后者是正的）
图 2  归属方案不确定度：跨度占 |P_frz| 的百分比，按体系类型排
"""
import json
import os
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
            if len(sub) < 2:
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
