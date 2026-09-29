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
OUT = os.path.join(HERE, "..", "figs")
os.makedirs(OUT, exist_ok=True)


def load(name):
    p = os.path.join(HERE, "logs", name)
    if not os.path.exists(p):
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


def fig3(rows):
    """P2 的主图：可证屏蔽**为什么不划算**。只用 valid_timing 的样本。

    (a) 墙钟 vs 网格点数，exact 与"精度可用的那一档"并列，叠 N^1 与 N^2 参考线；
    (b) 保留的 far 点对比例 vs 实际误差，把正文需要的 1e-6 kcal/mol 画成一条竖线。
    """
    good = [r for r in rows if all(v["valid_timing"] for v in r["runs"].values())]
    if len(good) < 2:
        sys.exit(f"空载可用样本只有 {len(good)} 个，不出图（宁可不出，也别出错图）")
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(9.6, 3.6))
    mark = {0: ("o", "#3b6ea5"), 1: ("s", "#c0504d")}
    for lvl in (0, 1):
        sub = sorted([r for r in good if r["level"] == lvl],
                     key=lambda r: r["runs"]["exact"]["pointpairs_far"])
        if len(sub) < 2:
            continue
        m, c = mark[lvl]
        axA.plot([r["runs"]["exact"]["pointpairs_far"] for r in sub],
                 [r["runs"]["exact"]["wall_s"] for r in sub], m + "-", color=c,
                 label=f"exact, level {lvl}")
        axA.plot([r["runs"]["tau1e-12"]["pointpairs_evaluated"] for r in sub],
                 [r["runs"]["tau1e-12"]["wall_s"] for r in sub], m + "--", color=c,
                 mfc="white", label=f"screened τ=1e-12, level {lvl}")
        for r in sub:                              # 同一体系：功变少、时间变多
            axA.plot([r["runs"]["exact"]["pointpairs_far"],
                      r["runs"]["tau1e-12"]["pointpairs_evaluated"]],
                     [r["runs"]["exact"]["wall_s"], r["runs"]["tau1e-12"]["wall_s"]],
                     "-", color=c, lw=.7, alpha=.45, zorder=0)
    axA.set_xscale("log"); axA.set_yscale("log")
    axA.set_xlabel("far point pairs actually evaluated")
    axA.set_ylabel("wall clock (s)")
    axA.set_title("(a) idle machine, 4 threads, external runnable tasks = 0\n"
                  "each connector = same system: less work, more time", fontsize=8.5)
    axA.legend(fontsize=6.2, loc="upper left")

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
    j = load("step_j.json")
    if j and j["rows"]:
        print("出图：", fig3(j["rows"]))
