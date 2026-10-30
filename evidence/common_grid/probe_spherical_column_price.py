"""球平均那一列的**代价定价**：换定义是"收紧同一列"还是"换成另一列"。

背景（一句话）：`20261018T114952Z_spherical_promolecule_thread_probe.out` 实测
非球平均列跨线程差 `max|ΔS| = 6.43e-01`，球平均后降到 `2.23e-05`，
但**同线程下两个定义本身差 `3.31e-01`**——量级和抖动一样大。
裁断第 2 步要在 (a) 仅改名并限定 与 (c) 重新定义并整批重取 之间选，
靠权重差选不出来：**要的是这一列的发表量（片间 `E_AB`，kcal/mol）上差多少**。

预登记判据（写这段时脚本尚未运行，2026-10-18）：
  PRICE      = |E_AB(非球平均, T=1) − E_AB(球平均, T=1)|
  NEWCOL_OK  = |E_AB(球平均, T=1) − E_AB(球平均, T=8)|
  OLDCOL     = |E_AB(非球平均, T=1) − E_AB(非球平均, T=8)|   ← 参照量，应复现已归档的抖
  PRICE <= 1e-4              ⇒ REDEFINITION_IS_IMPLEMENTATION_DETAIL
        球平均只是把同一列的实现收紧；旧读数不必作废。
  PRICE >= 1e-3              ⇒ REDEFINITION_IS_A_NEW_COLUMN
        换定义等于换一列：旧的四格与八格 Hirshfeld 读数按新定义**全部重取**，
        不能写成"同一测量的可复现版"。
  NEWCOL_OK >= 1e-3          ⇒ SPHERICAL_DOES_NOT_FIX_REPRODUCIBILITY（线程叙事另有根因）
  NEWCOL_OK <= 1e-4          ⇒ SPHERICAL_COLUMN_IS_PRINTABLE（新列在打印精度下线程无关）
  任一量落在两条阈值之间      ⇒ INCONCLUSIVE，原样报未决，不当场编判读。

只读生产函数、不改生产代码、不动任何门；`E_AB` 走 `nlc.fragment_decomposition(soft=...)`
与 `hirshfeld_crossfamily.py:137-141` 完全同一条路。
artifact_kind=probe_definition_price ⇒ 本档数字是**假想定义的定价**，不是已认证的生产读数，
不得进正文表格。
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NAME = "苯-氨"      # 现状列跨线程抖最大的那一格（S22_18）
LEVEL = 1
NRAD = 400
NDIR = 252
PRINT_TOL = 1e-4    # 旧表打印分辨率
GATE = 1e-3         # Hirshfeld 列的认证门

WORKER = r'''
import hashlib, json, os, sys
import numpy as np
sys.path.insert(0, %(root)r)
from nlcsplit import partition, nlc
from nlcsplit.step_f_dispersion import KCAL
from nlcsplit.step_h_s22 import build
from pyscf import dft, gto, scf
from pyscf.dft import numint

NAME, LEVEL, NRAD, NDIR = %(name)r, %(level)d, %(nrad)d, %(ndir)d
BASIS, B, C = "6-31g*", 6.0, 0.01


def row(S):
    res = nlc.fragment_decomposition(X0, W0, rho0, sig0, frags, b=B, C=C,
                                     soft=S, closure_check=True)
    return float(res["inter"][(0, 1)] * KCAL), float(res["E_nl"] * KCAL)


mol, frags, dmin = build(NAME)
mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc="wb97x_v", level=LEVEL, basis=BASIS)
assert mf.converged, "%%s: 复合物 SCF 未收敛" %% NAME

# 生产列（非球平均）
S_ns, S_alt, n_zero = partition.hirshfeld_factors(mol, X0, basis=BASIS)
A, A_enl = row(S_ns)

# 球平均 promolecule（同一批点、同一份自由原子数据，只多一步方向平均）
i = np.arange(NDIR)
phi = np.arccos(1.0 - 2.0 * (i + 0.5) / NDIR)
th = np.pi * (1.0 + 5.0 ** 0.5) * i
DIRS = np.stack([np.sin(phi) * np.cos(th), np.sin(phi) * np.sin(th), np.cos(phi)], axis=1)
ni = numint.NumInt()
tables = {}
for sym in sorted({mol.atom_symbol(a) for a in range(mol.natm)}):
    atm = gto.M(atom="%%s 0 0 0" %% sym, basis=BASIS, unit="Angstrom",
                spin=partition.FREE_ATOM_MULT[sym] - 1, verbose=0)
    atm.build()
    mu = scf.UHF(atm).run()
    if not mu.converged:
        raise RuntimeError("%%s: 自由原子 UHF 未收敛" %% sym)
    dm = mu.make_rdm1()
    r_all = np.concatenate([np.linalg.norm(X0 - mol.atom_coord(a), axis=1)
                            for a in range(mol.natm) if mol.atom_symbol(a) == sym])
    r_lo, r_hi = max(r_all.min() * 0.5, 1e-4), r_all.max() * 1.02 + 1e-3
    rad = np.exp(np.linspace(np.log(r_lo), np.log(r_hi), NRAD))
    ao = ni.eval_ao(atm, (rad[:, None, None] * DIRS[None, :, :]).reshape(-1, 3), deriv=1)
    rho = ni.eval_rho(atm, ao, dm, xctype="GGA")[0].reshape(NRAD, NDIR)
    tables[sym] = (rad, np.log(np.clip(rho.mean(axis=1), 1e-300, None)),
                   float(mu.e_tot), hashlib.sha256(np.asarray(dm).tobytes()).hexdigest()[:16])

W = np.vstack([np.exp(np.interp(np.linalg.norm(X0 - mol.atom_coord(a), axis=1),
                                tables[mol.atom_symbol(a)][0],
                                tables[mol.atom_symbol(a)][1]))
               for a in range(mol.natm)])
den = W.sum(axis=0)
if int((den <= 0).sum()) != n_zero:
    raise AssertionError("球平均侧分母零点数 %%d ≠ 生产实现报的 %%d ⇒ 两边不是同一条规则"
                         %% (int((den <= 0).sum()), n_zero))
if n_zero:
    raise AssertionError("n_zero=%%d：生产实现对这些点走最近原子兜底，本探针没写那支 ⇒ 拒跑" %% n_zero)
S_sa = W / den
dev = float(np.abs(S_sa.sum(axis=0) - 1.0).max())
if dev > 1e-10:
    raise AssertionError("球平均权重每点和偏离 1 达 %%.3e ⇒ 归一化没做成" %% dev)
Bv, B_enl = row(S_sa)

json.dump({"threads": [os.environ.get(k) for k in
                       ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")],
           "natm": mol.natm, "npts": int(X0.shape[0]), "n_zero": int(n_zero),
           "sa_norm_dev": dev,
           "eab_ns": A, "eab_sa": Bv, "enl_ns": A_enl, "enl_sa": B_enl,
           "atom_table": {k: {"e_tot": v[2], "dm_hash": v[3]} for k, v in tables.items()}},
          open(sys.argv[1] + ".json", "w"))
''' % {"root": ROOT, "name": NAME, "level": LEVEL, "nrad": NRAD, "ndir": NDIR}


def worker(threads, path):
    env = dict(os.environ)
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        env[k] = str(threads)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, "-c", WORKER, path], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    if p.returncode != 0:
        print("!! 子进程（%d 线程）失败 rc=%d：\n%s" % (threads, p.returncode, p.stderr[-2000:]))
        sys.exit(2)
    return json.load(open(path + ".json"))


def band(x):
    """落在哪一档：'LOW'（<=打印分辨率）/ 'MID'（两阈值之间）/ 'HIGH'（>=门）"""
    if x <= PRINT_TOL:
        return "LOW"
    if x >= GATE:
        return "HIGH"
    return "MID"


def main():
    print("# artifact_kind=probe_definition_price —— 假想定义的定价，不是已认证生产读数")
    print("# 球平均 vs 非球平均 Hirshfeld 列在发表量 E_AB 上差多少  体系 %s  level %d" % (NAME, LEVEL))
    print("# 生成 %s" % datetime.now(timezone.utc).isoformat())
    print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                           capture_output=True, text=True).stdout.strip())
    for rel in ("nlcsplit/partition.py", "nlcsplit/nlc.py"):
        print("# sha256 %-24s = %s" % (rel, hashlib.sha256(
            open(os.path.join(ROOT, rel), "rb").read()).hexdigest()[:32]))
    print("# 预登记判据：PRICE/NEWCOL_OK 用 %g（打印分辨率）与 %g（Hirshfeld 认证门）两档卡"
          % (PRINT_TOL, GATE))

    tmp = tempfile.mkdtemp(prefix="priceprobe_")
    t1 = worker(1, os.path.join(tmp, "t1"))
    t8 = worker(8, os.path.join(tmp, "t8"))
    for tag, d in (("T=1", t1), ("T=8", t8)):
        print("# %s 线程环境 %s  原子 %d  网格 %d  n_zero %d  球平均归一偏离 %.2e"
              % (tag, d["threads"], d["natm"], d["npts"], d["n_zero"], d["sa_norm_dev"]))
        print("#   E_AB 非球平均 %.6f  球平均 %.6f  |ΔE_nl| %.2e"
              % (d["eab_ns"], d["eab_sa"], abs(d["enl_ns"] - d["enl_sa"])))
        for sym in sorted(d["atom_table"]):
            print("#   %-2s 1-RDM %s vs %s %s"
                  % (sym, t1["atom_table"][sym]["dm_hash"], t8["atom_table"][sym]["dm_hash"],
                     "同解" if t1["atom_table"][sym]["dm_hash"]
                     == t8["atom_table"][sym]["dm_hash"] else "**异解**"))

    price = abs(t1["eab_ns"] - t1["eab_sa"])
    newcol = abs(t1["eab_sa"] - t8["eab_sa"])
    oldcol = abs(t1["eab_ns"] - t8["eab_ns"])
    print("# PRICE      = |E_AB(非球平均,T1) − E_AB(球平均,T1)| = %.4e  [%s]" % (price, band(price)))
    print("# NEWCOL_OK  = |E_AB(球平均,T1) − E_AB(球平均,T8)|   = %.4e  [%s]" % (newcol, band(newcol)))
    print("# OLDCOL     = |E_AB(非球平均,T1) − E_AB(非球平均,T8)| = %.4e  [%s]"
          % (oldcol, band(oldcol)))
    print("# 参照：已归档的 S22_18 hirshfeld 新旧不符 = 0.0130（`20261018T111923Z_*_closeout.out`）"
          "⇒ OLDCOL 与之同量级才算复现了同一个病因")

    lines = []
    if band(price) == "LOW":
        lines.append("REDEFINITION_IS_IMPLEMENTATION_DETAIL —— 球平均在发表量上只动 %.1e（≤%g）"
                     % (price, PRINT_TOL))
    elif band(price) == "HIGH":
        lines.append("REDEFINITION_IS_A_NEW_COLUMN —— 球平均把 E_AB 动 %.4f（≥%g）"
                     "⇒ 换定义等于换一列，旧读数不能写成'同一测量的可复现版'" % (price, GATE))
    else:
        lines.append("PRICE_INCONCLUSIVE —— PRICE=%.4e 落在 (%g, %g) 之间，规则没覆盖，未决"
                     % (price, PRINT_TOL, GATE))
    if band(newcol) == "LOW":
        lines.append("SPHERICAL_COLUMN_IS_PRINTABLE —— 球平均列跨线程 %.1e ≤ %g" % (newcol, PRINT_TOL))
    elif band(newcol) == "HIGH":
        lines.append("SPHERICAL_DOES_NOT_FIX_REPRODUCIBILITY —— 球平均列仍跨线程抖 %.4e ≥ %g"
                     % (newcol, GATE))
    else:
        lines.append("NEWCOL_INCONCLUSIVE —— NEWCOL_OK=%.4e 落在 (%g, %g) 之间，未决"
                     % (newcol, PRINT_TOL, GATE))
    if band(oldcol) == "LOW":
        lines.append("!! OLDCOL 只有 %.1e，没复现已归档的 0.0130 抖动 ⇒ 本实验的两个线程配置"
                     "可能没真的换线程，两条判读都不作数" % oldcol)
    print("\nVERDICT " + " | ".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
