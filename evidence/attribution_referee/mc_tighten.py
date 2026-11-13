"""Tighten the referee's resolution with a THIRD, independent error bar - without
touching the two archived runs.

`outputs/summary.md` compares each attribution offset `d_headline` against `U`, a
combined uncertainty assembled from three *deterministic* quadrature diagnostics
(order-ladder last change, domain-truncation shift, 3-D vs 5-D disagreement). The
3-D vs 5-D term dominates it at 7.97e-06 Ha, so `U = 1.060e-05` Ha resolves only 5
of 12 configurations.

The Monte-Carlo route already in `referee_lib.mc_integral` carries a different and
much smaller uncertainty - its own standard error, which shrinks as 1/sqrt(m) and
does not inherit the node-set/shape systematics of the deterministic ladders. This
script raises the draw count and writes a SEPARATE sidecar:

    outputs/mc_tight.json

so the two shipped `results.json` files stay byte-identical to what they are now.
`summarize.py` reads the sidecar when present and reports resolution against BOTH
error bars, never the smaller one alone, and never calls an offset resolved unless
it clears both.

Run (repository root, after `run.py` so results.json exists):

    PYTHONPATH=. python3 -u evidence/attribution_referee/mc_tighten.py

A quick plumbing check with the default draw count: prefix `MC_TIGHT=400000`.
"""
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))     # repository root
sys.path.insert(0, HERE)                                       # sibling referee_lib, as run.py does

import referee_lib as rl                                        # noqa: E402
from pyscf import dft                                          # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(OUT, "outputs")
RESULTS = os.path.join(OUT, "results.json")
SIDE = os.path.join(OUT, "mc_tight.json")
KCAL = 627.509474
M = int(os.environ.get("MC_TIGHT", "4000000"))
# Same estimator and importance as run.py's MC block, a different seed offset so
# these draws are not a continuation of the archived 400k block.
SEED0 = 314159


def main():
    if not os.path.exists(RESULTS):
        sys.exit(f"没有 {RESULTS}；先跑 run.py，本脚本不重算归属，只加一条误差条")
    res = json.load(open(RESULTS, encoding="utf-8"))
    # VV10 parameters taken the same way run.py takes them: from PySCF, at run time.
    b, C = dft.numint.NumInt().nlc_coeff("wb97x_v")[0][0]
    rows = res["rows"]
    print(f"== 独立蒙特卡洛误差条：{len(rows)} 个构型 × {M:,} 抽样，b={b} C={C} ==")
    out = {"meta": {"m_per_config": M, "seed_base": SEED0, "pkg_level": res["meta"]["pkg_level"],
                    "vv10_b": b, "vv10_C": C, "KCAL": KCAL},
           "rows": []}
    t0 = time.time()
    for i, r in enumerate(rows):
        alpha, sep = r["alpha"], r["sep"]
        gp = rl.GaussPair(sep=sep, alpha_a=alpha, n_a=r["n_elec"])
        mcp, se = rl.mc_integral(gp, b, C, "AB", m=M, seed=SEED0 + 7 * i)
        mc_ha = float(mcp)
        se_ha = float(se)
        # offset of the package's attributed pair block from THIS route's estimate
        d = r["grid_inter"] - mc_ha
        row = {"alpha": alpha, "sep": sep,
               "I_AB_exact_5d": r["I_AB"], "I_AB_mc": mc_ha, "mc_se_ha": se_ha,
               "cross_check_vs_5d_ha": mc_ha - r["I_AB"],
               "d_headline_ha": r["d_headline"], "d_headline_kcal": r["d_headline"] * KCAL,
               "resolved_vs_2se": abs(d) > 2.0 * se_ha,
               "ratio_d_to_se": abs(d) / se_ha if se_ha > 0 else None}
        out["rows"].append(row)
        print(f"  alpha={alpha:4.1f} sep={sep:5.1f} | MC I_AB {mc_ha:+.10e} +/- {se_ha:.2e}"
              f" | vs 5-D {row['cross_check_vs_5d_ha']:+.2e}"
              f" | |d_headline|/se = {row['ratio_d_to_se']:8.1f}"
              f" | 2se? {'yes' if row['resolved_vs_2se'] else 'no '}", flush=True)
    out["meta"]["runtime_s"] = time.time() - t0
    out["meta"]["n_resolved_vs_2se"] = sum(1 for x in out["rows"] if x["resolved_vs_2se"])
    worst_se = max(x["mc_se_ha"] for x in out["rows"])
    out["meta"]["worst_mc_se_ha"] = worst_se
    print(f"\n  {out['meta']['n_resolved_vs_2se']}/{len(rows)} 构型的归属偏移超过它自己的"
          f" 2 倍蒙特卡洛标准误；最大 mc_se = {worst_se:.2e} Ha"
          f"（对比 U = 1.060e-05 Ha）")
    print(f"  用时 {out['meta']['runtime_s']:.0f} s -> {os.path.relpath(SIDE, os.path.dirname(HERE))}")
    with open(SIDE, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


if __name__ == "__main__":
    main()
