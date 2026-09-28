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
    ax.set_xticklabels(labels, fontsize=8)
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
    ax.set_title("Attribution-scheme uncertainty: H-bonded ~7% vs dispersion ~2%", fontsize=9)
    fig.tight_layout()
    f = os.path.join(OUT, "fig2_scheme_sensitivity.png")
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
