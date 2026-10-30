"""A3：把"P2 的亚平方为什么不成立"变成有数字的图，而不是口头结论。

两件事，分开记：
  (1) **功的占比**（与墙钟无关，任何负载下都作数）：exact / screened 各自要评估的
      点对数、可跳占比、cert_err、实际 |dE|。
  (2) **墙钟标度**（只在空载作数）：水链 N = 1,2,3,4 个单体，level 0，
      exact 全量 O(N^2) 对比带屏蔽的树/MAC。每个样本都带 load1、外部可运行任务数与
      OMP 线程数；**外部（不含本进程树）可运行任务 > 1 的样本标 INVALID**，不进图。
      闸门不能数自己的负载——那样每个样本都会自判无效，等于没有闸门。

跑法（WSL，空载）：PYTHONPATH=. python3 -u nlcsplit/step_j_scaling.py
"""
import json
import os
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyscf import dft, gto  # noqa: E402
import pyscf  # noqa: E402

from nlcsplit import fastpair, geomlib, nlc, partition  # noqa: E402

BASIS, XC = "6-31g*", "wb97x_v"
KCAL = 627.5094740630563
TAUS = (None, 1e-8, 1e-10, 1e-12)
LOAD_GATE = 1        # 允许的"非我" R 态用户任务数；自己不算争用
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "nlcsplit", "logs", "step_j.json")


def load1():
    return float(open("/proc/loadavg").read().split()[0])


def _my_ancestors():
    """我自己 + 我的父 shell。用别的方法会把"我自己正在算"当成外部争用，
    于是每个样本都自判 INVALID——那是个永远为真的闸门，等于没有闸门。"""
    mine, pid = {os.getpid()}, os.getpid()
    for _ in range(8):
        try:
            stat = open(f"/proc/{pid}/stat").read()
            ppid = int(stat.rsplit(")", 1)[1].split()[1])
        except (OSError, IndexError, ValueError):
            break
        if ppid in mine or ppid <= 1:
            break
        mine.add(ppid)
        pid = ppid
    return mine


MINE = _my_ancestors()


def external_runnable():
    """非我的、有 cmdline 的 R 态任务数（内核线程没有 cmdline，不算争用）。"""
    n = 0
    for d in os.listdir("/proc"):
        if not d.isdigit() or int(d) in MINE:
            continue
        try:
            with open(f"/proc/{d}/stat") as fh:
                state = fh.read().rsplit(")", 1)[1].split()[0]
            if state != "R":
                continue
            if os.path.getsize(f"/proc/{d}/cmdline") == 0:
                continue
        except (OSError, IndexError, ValueError):
            continue
        n += 1
    return n


def pressure():
    return {"load1": round(load1(), 2), "other_runnable": external_runnable()}


def water_chain(nmon):
    """刚性水单体沿 z 排成一串（3.0 A 间隔）：只为了造一个尺寸阶梯，不是物理体系。"""
    mon = geomlib.h2o_dimer()[:3]                 # 一个单体：O + 2H
    out = []
    for k in range(nmon):
        for sym, (x, y, z) in mon:
            out.append((sym, (x, y, z + 3.0 * k)))
    return out


def one(mol, level, taus=TAUS):
    """同一张网格、同一份密度上跑 exact 与各档 τ，返回逐档记录 + 计时。"""
    rec = {"level": level, "natm": mol.natm, "nelec": mol.nelectron}
    t0 = time.perf_counter()
    mf = dft.RKS(mol)
    mf.xc = XC
    mf.grids.level = level
    mf.kernel()
    rec["t_scf_s"] = time.perf_counter() - t0
    rec["load_after_scf"] = pressure()
    runs = {}
    for tau in taus:
        kw = {} if tau is None else {"screen": tau}
        t0 = time.perf_counter()
        r = fastpair.screened_decomposition(mol, mf, level=level, scheme="becke", **kw)
        dt = time.perf_counter() - t0
        key = "exact" if tau is None else f"tau{tau:.0e}"
        # 不屏蔽的那条路不经过 MAC，所以库里不给它计点对。定义上它评估**全部**
        # far 点对，这里按定义补上；否则表里 exact 印 0.00%，图上一条零线会被读成
        # "全量路径不算点"。同核(self)点对两条路都全算，不进这个比值。
        evaluated = r["pointpairs_far"] if tau is None else r["pointpairs_evaluated"]
        runs[key] = {
            "tau_ha": tau, "wall_s": dt,
            "n_grid": r["n_grid"], "n_kept_points": r["n_kept_points"],
            "pointpairs_far": r["pointpairs_far"],
            "pointpairs_evaluated": evaluated,
            "pointpairs_dropped": r["pointpairs_dropped"],
            "work_frac_evaluated": evaluated / max(r["pointpairs_far"], 1),
            "n_leaves": r["n_leaves"], "n_leafpairs_total": r["n_leafpairs_total"],
            "n_leafpairs_evaluated": r["n_leafpairs_evaluated"],
            "n_accepted": r["n_accepted"], "n_visited": r["n_visited"],
            "cert_err_ha": r["cert_err"],
            "abs_dE_kcal": abs(r["E_nl"] - runs["exact"]["E_nl_ha"]) * KCAL
            if "exact" in runs else None,
            "E_nl_ha": r["E_nl"], "E_pair": r["E_pair"],
            "cert_ge_actual": (True if "exact" not in runs or tau is None
                               else r["cert_err"] + 1e-18 >= abs(r["E_nl"] - runs["exact"]["E_nl_ha"])),
        }
        runs[key]["load_after"] = pressure()
        runs[key]["valid_timing"] = runs[key]["load_after"]["other_runnable"] <= LOAD_GATE
    rec["runs"] = runs
    return rec


def main():
    omp = os.environ.get("OMP_NUM_THREADS", "(unset)")
    up = subprocess.run(['cat', '/proc/uptime'], capture_output=True, text=True).stdout.split()[0]
    print(f"=== step_j_scaling  PySCF {pyscf.__version__}  basis={BASIS}  xc={XC}")
    print(f"    OMP_NUM_THREADS={omp}  uptime_s={float(up):.0f}  load1_now={load1():.2f}")
    print(f"    判据：非本进程树的可运行用户任务 > {LOAD_GATE} 的计时样本标 INVALID，"
          f"只留功占比与正确性。")
    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "pyscf_version": pyscf.__version__, "basis": BASIS, "xc": XC,
           "omp_num_threads": omp, "load_gate": LOAD_GATE, "rows": []}
    for nmon, level in ((1, 0), (2, 0), (3, 0), (4, 0), (2, 1), (3, 1)):
        atoms = water_chain(nmon)
        mol = gto.M(atom=[(s, c) for s, c in atoms], basis=BASIS, verbose=0, unit="Angstrom")
        print(f"\n-- {nmon} 个水单体（{mol.natm} 原子）level={level}  load1={load1():.2f}")
        t0 = time.perf_counter()
        r = one(mol, level)
        r["n_monomers"] = nmon
        r["wall_total_s"] = time.perf_counter() - t0
        out["rows"].append(r)
        for k, v in r["runs"].items():
            print(f"   {k:<12} 评估点对={v['pointpairs_evaluated']:>14,}"
                  f"  占 far {v['work_frac_evaluated'] * 100:6.2f}%"
                  f"  cert={v['cert_err_ha']:.3e} Ha"
                  f"  |dE|={'-' if v['abs_dE_kcal'] is None else format(v['abs_dE_kcal'], '.3e')} kcal"
                  f"  {v['wall_s']:8.2f} s  load1={v['load_after']['load1']:.2f}"
                  f"  外部R={v['load_after']['other_runnable']}"
                  f"{'  INVALID' if not v['valid_timing'] else ''}"
                  f"{'  cert<actual!' if v['cert_err_ha'] and not v['cert_ge_actual'] else ''}")
        json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
        print(f"   侧车 → {OUT}（{len(out['rows'])} 行，增量落盘）")
    ok = [r for r in out["rows"] for v in r["runs"].values() if v["valid_timing"]]
    print(f"\n[计时可用性] {len(ok)} / {sum(len(r['runs']) for r in out['rows'])} 个样本空载可用。"
          f" 只有这些能进标度图。")


if __name__ == "__main__":
    main()
