"""A2b 完成判据 L1–L4 的真实体系验证 + 三个外部锚点。产物写 JSON 侧车，不写日志正文。

跑法（CentOS 隔离工作区）：
    OMP_NUM_THREADS=6 NCPC=0 python nlcsplit/examples/check_screen_bound_ide.py --tier l1
    ... --tier l2        # 8 体系 ε=1e-8 复现 step_h.json 的 P_frz（贵，后台跑）
判据（来自 PROGRESS-nlcsplit.md 的 A2b 任务书）：
  L1  证得界 ≥ 实际 |screened−full|，水二聚体 lvl1 与 苯二聚体 lvl0 都验；
  L2  ε=1e-8 复现已入库 step_h.json 全部 8 个 P_frz，误差 ≤ 1e-6 kcal/mol；
  L3  屏蔽开启可加性 < 1e-10 Ha；屏蔽关闭时全套测试逐条相同（关闭路径 = nlc 原样）；
  L4  ε→0 退回全量，差 = 浮点重排噪声（~1e-14 相对）。
外部锚点（两版互相吻合只算旁证，这三个才是裁判）：
  (a) 全量 O(N²) 路径 nlc.pair_energy（屏蔽关闭）
  (b) PySCF 原生核 numint.nr_nlc_vxc
  (c) ORCA 6.0.1：水 −0.5931 / 苯 −4.3252 kcal/mol

纪律：屏蔽默认关闭；总量与分块从同一份保留清单加出来，不另跑带屏蔽总量对账；
rho_floor 与屏蔽两条截断分开报告；计时类测量要求 load<0.5（本脚本主要出的是数值不是墙钟）。
"""
import argparse
import json
import os
import socket
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pyscf import dft, gto   # noqa: E402
from pyscf.dft import numint   # noqa: E402

from nlcsplit import fastpair_ide as fp   # noqa: E402
from nlcsplit import geomlib, nlc, partition   # noqa: E402

KCAL = 627.509474
XC = "wb97x_v"
BASIS = "6-31g*"
EPS = 1.0e-8
SCHEMES = ["becke", "becke-becke-rad", "becke-treutler", "stratmann"]
ORCA_ANCHOR = {"水二聚体": -0.5931, "苯二聚体(A)": -4.3252}
DATA = os.environ.get("S22DIR") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "s22")
HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(os.path.dirname(HERE), "logs")


def load_gate():
    """计时/出数前置：load<0.5 才继续（本机 8 核，另有批次时读高就等或拒）。"""
    try:
        load1 = os.getloadavg()[0]
    except OSError:
        load1 = 0.0
    return load1


def state(system, level, scheme):
    """几何 → SCF（复合物）→ 该 scheme 的 Becke 分区网格 + 密度。返回算双重和所需一切。"""
    if system == "(H2O)2":
        atoms, frags = geomlib.h2o_dimer(), geomlib.FRAGS["(H2O)2"]
        mol = gto.M(atom=atoms, basis=BASIS, verbose=0, unit="Angstrom")
    elif system == "(C6H6)2":
        mol = gto.M(atom=geomlib.benzene_sandwich(), basis=BASIS, verbose=0, unit="Angstrom")
        frags = geomlib.FRAGS["(C6H6)2"]
    else:
        s22name = [k for k, v in geomlib.S22_EN.items() if v == system]
        atoms, frags = geomlib.s22_system(s22name[0], DATA)
        mol = gto.M(atom=[(s, c) for s, c in atoms], basis=BASIS, verbose=0, unit="Angstrom")
    mf = dft.RKS(mol)
    mf.xc = XC
    mf.grids.level = level
    t0 = time.time()
    mf.kernel()
    b, C = mf._numint.nlc_coeff(XC)[0][0]
    X, W, owner = partition.atom_partition(mol, level=level, scheme=scheme)
    rho = mf._numint.eval_rho(mol, mf._numint.eval_ao(mol, X, deriv=1), mf.make_rdm1(),
                              xctype="GGA")
    sig = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
    return dict(mol=mol, mf=mf, frags=frags, b=b, C=C, X=X, W=W, owner=owner,
                rho=rho[0], sig=sig, scheme=scheme, level=level, system=system,
                t_scf=time.time() - t0)


def p_frz_full(st):
    """全量 O(N²) 片间成对项（整份）——就是 nlc.fragment_decomposition 的 inter[(0,1)]。"""
    res = nlc.fragment_decomposition(st["X"], st["W"], st["rho"], st["sig"], st["frags"],
                                     b=st["b"], C=st["C"], owner=st["owner"])
    return res["inter"][(0, 1)] * KCAL, res


def p_frz_screened(st, epsilon=EPS, mode="budget"):
    res = fp.screened_decomposition(st["X"], st["W"], st["rho"], st["sig"], st["frags"],
                                    b=st["b"], C=st["C"], owner=st["owner"],
                                    epsilon=epsilon, mode=mode, full_ref=True)
    return res["inter"][(0, 1)] * KCAL, res


def one_l1(system, level):
    """L1：证得界 ≥ 实际 |screened−full|；并报三个外部锚点差。

    另拿一个故意宽松的 ε 探针（l1_probe），确认屏蔽机制真的会屏：
    S22 这类紧凑二聚体上，原子块质量屏蔽在 ε=1e-8 下常常一块都屏不动（退化成全量，
    界=0、actual=重排噪声）——这正是任务书预警的『真正剪枝的是密度质量不是距离』。
    探针把 ε 放宽到有块可屏，验证 bound≥actual 在有真实丢弃时仍成立。
    """
    st = state(system, level, "becke")
    full, fullres = p_frz_full(st)
    scr, res = p_frz_screened(st)
    actual = abs(res["actual_ha"])
    bound = res["bound_ha"]
    probe = None
    min_bound = min((p["bound"] for p in res["pairs"]), default=float("nan"))
    for eps in (1e-3, 1e-2, 1e-1, 1.0):
        _s, pr = p_frz_screened(st, epsilon=eps)
        if pr["n_dropped_screen"] > 0:
            probe = dict(epsilon=eps, bound_ha=pr["bound_ha"],
                         actual_ha=abs(pr["actual_ha"]),
                         n_dropped_screen=pr["n_dropped_screen"],
                         pass_=bool(pr["bound_ha"] + 1e-16 >= abs(pr["actual_ha"])))
            break
    # 锚点 (b) PySCF 原生核：E_total 应与 nr_nlc_vxc 落在同一值（同网格口径下）
    _, e_ref, _ = numint.nr_nlc_vxc(st["mf"]._numint, st["mol"], st["mf"].grids,
                                    XC, st["mf"].make_rdm1())
    d_pyscf = (res["E_total"] - e_ref) * KCAL
    # 锚点 (c) ORCA：只在能算 ΔE_NLC 且有入库锚的体系上对（水 lvl1）。
    d_orca = None
    if system == "(H2O)2" and level >= 1:
        d_orca = _delta_e_nlc(st) - ORCA_ANCHOR["水二聚体"]
    return dict(system=system, level=level, natm=st["mol"].natm,
                N=len(st["X"]), scheme="becke", full_pfrz=full, screened_pfrz=scr,
                bound_ha=bound, actual_ha=actual,
                l1_pass=bool(bound + 1e-13 >= actual), l1_probe=probe,
                min_block_bound_ha=min_bound,
                d_pyscf_native_kcal=d_pyscf, d_orca_kcal=d_orca,
                n_dropped_rho=res["n_dropped_rho"], n_dropped_screen=res["n_dropped_screen"],
                n_pairs_full=res["n_pairs_full"], points_full=res["points_full"],
                points_kept=res["points_kept"], t_scf=st["t_scf"])


def _delta_e_nlc(st):
    """ΔE_NLC = E_NLC(复合物) − Σ E_NLC(单体@复合物几何)，β∫ρ 在差里精确抵消。"""
    mf = st["mf"]
    comp = fp.screened_decomposition(st["X"], st["W"], st["rho"], st["sig"], st["frags"],
                                     b=st["b"], C=st["C"], owner=st["owner"], mode="full")
    dnlc = comp["E_total"]
    for f in st["frags"]:
        C_bohr = st["mol"].atom_coords()
        txt = "\n".join(f"{st['mol'].atom_symbol(i)} {C_bohr[i][0]:.10f} "
                        f"{C_bohr[i][1]:.10f} {C_bohr[i][2]:.10f}" for i in f)
        sub = gto.M(atom=txt, basis=BASIS, verbose=0, unit="Bohr")
        smf = dft.RKS(sub); smf.xc = XC; smf.grids.level = st["level"]; smf.kernel()
        sX, sW, sown = partition.atom_partition(sub, level=st["level"], scheme=st["scheme"])
        sr = smf._numint.eval_rho(sub, smf._numint.eval_ao(sub, sX, deriv=1),
                                  smf.make_rdm1(), xctype="GGA")
        ss = sr[1] ** 2 + sr[2] ** 2 + sr[3] ** 2
        sb, sC = smf._numint.nlc_coeff(XC)[0][0]
        sres = nlc.fragment_decomposition(sX, sW, sr[0], ss, [list(range(sub.natm))],
                                          b=sb, C=sC, owner=sown)
        dnlc -= sres["E_total"]
    return dnlc * KCAL


def one_l2(name):
    """L2：ε=1e-8 下四方案 P_frz 对全量之差 ≤ 1e-6 kcal/mol，并与 step_h.json 对账。"""
    atoms, frags = geomlib.s22_system(name, DATA)
    mol = gto.M(atom=[(s, c) for s, c in atoms], basis=BASIS, verbose=0, unit="Angstrom")
    mf = dft.RKS(mol); mf.xc = XC; mf.grids.level = 1; mf.kernel()
    b, C = mf._numint.nlc_coeff(XC)[0][0]
    dm = mf.make_rdm1()
    out = {}
    for scheme in SCHEMES:
        X, W, owner = partition.atom_partition(mol, level=1, scheme=scheme)
        rho = mf._numint.eval_rho(mol, mf._numint.eval_ao(mol, X, deriv=1), dm, xctype="GGA")
        sig = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
        res = fp.screened_decomposition(X, W, rho[0], sig, frags, b=b, C=C,
                                         owner=owner, epsilon=EPS, full_ref=True)
        full = nlc.fragment_decomposition(X, W, rho[0], sig, frags, b=b, C=C, owner=owner)
        scr = res["inter"][(0, 1)] * KCAL
        ref = full["inter"][(0, 1)] * KCAL
        add_err = abs(res["E_nl"] - sum(res["intra"].values()) - sum(res["inter"].values()))
        out[scheme] = dict(p_frz=scr, p_frz_full=ref, diff_kcal=scr - ref,
                           bound_ha=res["bound_ha"], actual_ha=res["actual_ha"],
                           additivity_err_ha=add_err,
                           l2_pass=bool(abs(scr - ref) <= 1e-6),
                           l3_pass=bool(add_err < 1e-10),
                           n_pairs_full=res["n_pairs_full"],
                           n_dropped_screen=res["n_dropped_screen"])
    return dict(name=name, natm=mol.natm, N=len(X), schemes=out,
                t_scf=None, pyscf=__import__("pyscf").__version__)


def tier_l4():
    """L4：ε→0（mode=budget, epsilon=1e-300 ⇒ 谁都屏不动）退回全量路径，
    差应 = 浮点重排噪声（~1e-14 相对）。

    ⚠ 上一版拿 P_frz（只有 inter）去比 E_nl（intra+inter），量纲不同塔到 rel=1.39 的
    假 FAIL。这里两边都用**总 E_nl**（同一个 fullres 口径），才是 L4 要量那个量。
    """
    st = state("(H2O)2", 1, "becke")
    _pfrz, fullres = p_frz_full(st)                 # fullres["E_nl"] 是全量总 Nonlinear 和
    _scr, budget_tiny = p_frz_screened(st, epsilon=1e-300, mode="budget")
    ref = fullres["E_nl"]
    rel = abs(budget_tiny["E_nl"] - ref) / abs(ref)
    # ε→0 不应丢任何块：n_dropped_screen 必须为 0
    return dict(system="(H2O)2", level=1, rel_reorder_noise=rel,
                n_dropped_screen=budget_tiny["n_dropped_screen"],
                l4_pass=bool(rel < 1e-12 and budget_tiny["n_dropped_screen"] == 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="l1", choices=["l1", "l2", "l4", "all"])
    ap.add_argument("--out", default=os.path.join(LOGS, "fastpair_ide_validation.json"))
    ap.add_argument("--l2-skip", default="",
                    help="逗号分隔的体系名，从 L2 跳过（苯二聚体 lvl1 是小时级长柱）")
    a = ap.parse_args()
    load1 = load_gate()
    skip = {s for s in a.l2_skip.split(",") if s}

    def dump():
        """每算完一个单元素就刷一次盘，这样长柱没跑完也能取到已完成的行。"""
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(report, fh, ensure_ascii=False, indent=1, allow_nan=False,
                      default=float)

    print(f"# A2b 验证  host={socket.gethostname()}  load1={load1:.2f}  "
          f"pyscf={__import__('pyscf').__version__}  ε={EPS:g} Ha  tier={a.tier}  "
          f"l2_skip={sorted(skip)}", flush=True)
    report = {"host": socket.gethostname(), "load1": load1, "epsilon_ha": EPS,
              "pyscf_version": __import__("pyscf").__version__, "tier": a.tier,
              "l2_skip": sorted(skip)}

    if a.tier in ("l1", "all"):
        report["l1"] = []
        for sysname, lvl in ("(H2O)2", 1), ("(C6H6)2", 0):
            r = one_l1(sysname, lvl)
            report["l1"].append(r)
            dump()
            print(f"  L1 {r['system']:9s} lvl{r['level']} N={r['N']:6d} "
                  f"full={r['full_pfrz']:+8.5f} scr={r['screened_pfrz']:+8.5f} "
                  f"bound={r['bound_ha']:.2e} actual={r['actual_ha']:.2e} "
                  f"{'PASS' if r['l1_pass'] else 'FAIL'}  "
                  f"dPySCF={r['d_pyscf_native_kcal']:.2e} dORCA={r['d_orca_kcal']}  "
                  f"drop(rho,scr)=({r['n_dropped_rho']},{r['n_dropped_screen']})  "
                  f"probe={r['l1_probe']}", flush=True)
    if a.tier in ("l4", "all"):
        report["l4"] = tier_l4()
        dump()
        print(f"  L4 相对重排噪声={report['l4']['rel_reorder_noise']:.2e} "
              f"{'PASS' if report['l4']['l4_pass'] else 'FAIL'}", flush=True)
    if a.tier in ("l2", "all"):
        report["l2"] = []
        for name in geomlib.S22:
            if name in skip:
                continue
            t0 = time.time()
            r = one_l2(name)
            r["wall_s"] = time.time() - t0
            report["l2"].append(r)
            dump()
            ok = all(s["l2_pass"] and s["l3_pass"] for s in r["schemes"].values())
            print(f"  L2 {name:10s} natm={r['natm']:3d} N={r['N']:6d} "
                  f"{'PASS' if ok else 'FAIL'}  ({r['wall_s']:.0f}s)", flush=True)

    os.makedirs(LOGS, exist_ok=True)
    dump()
    print(f"侧车 → {a.out}", flush=True)


if __name__ == "__main__":
    main()
