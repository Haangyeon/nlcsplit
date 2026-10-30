"""判别实验：Hirshfeld 那一列的线程抖动，病因到底是"线程数"还是"参照密度不做球平均"。

背景（一句话）：`partition.py:237-249` 的实现体确认自由原子是**逐元素 UHF + 直接取 1-RDM**，
没有任何球平均；而 `evidence/common_grid/20261013T183207Z_free_atom_cross_thread.out` 实测
T≥2 时 C/N 给出**能量几乎不动、但 1-RDM 哈希变了**的另一个解——那是"对称等价解
（相差一个空间转动）"的指纹。若参照密度非球平均，线程数就只是**替简并 p 子空间挑取向的骰子**，
"固定单线程"买到的是本机库锁定，不是这一列有定义。

判别（只有这一种做法能分开两种解释）：同一批网格点上，把自由原子密度**改成球平均**再跑一次
T=1 vs T=8。

    max|ΔS_球平均| ≤ 1e-12 且 max|ΔS_现状| ≥ 1e-3  ⇒ DEFINITION_IS_CAUSE
        取向假设坐实：抖动来自非球平均参照密度；单线程只是把骰子按住。
    max|ΔS_球平均| ≥ 1e-3                          ⇒ ORIENTATION_HYPOTHESIS_REFUTED
        我的推断被否证，线程叙事原样成立，不必改定义。
    max|ΔS_现状| ≤ 1e-14                           ⇒ NO_SIGNAL（取不到差值样本，rc=2）

规则是**跑之前**写死在这里的，不是看完数再定的。

代价：只算自由原子与权重，**不跑复合物 SCF**（`build()` 只给 mol 与网格）。
不碰任何门、不改生产代码、不重跑测量档。
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NAME = "苯-氨"          # 现状那一列跨线程抖动最大的格，实例见
                        # `evidence/common_grid/20261014T030330Z_summarize_s22_full_table.out` 的 S22_18 认证行
LEVEL = 1
NRAD = 400              # 径向点数（log 间隔）
NDIR = 252              # 每个半径上的方向数（Fibonacci 球）

WORKER = r'''
import hashlib, json, os, sys
import numpy as np
sys.path.insert(0, %(root)r)
from nlcsplit import partition
from nlcsplit.step_h_s22 import build
from pyscf import dft, gto, scf
from pyscf.dft import numint

NAME, LEVEL, NRAD, NDIR = %(name)r, %(level)d, %(nrad)d, %(ndir)d
BASIS = "6-31g*"

mol, frags, dmin = build(NAME)
g = dft.gen_grid.Grids(mol); g.level = LEVEL; g.build()
coords = np.asarray(g.coords, dtype=float)
S_ns, S_alt, n_zero = partition.hirshfeld_factors(mol, coords, basis=BASIS)

# 方向集：Fibonacci 球，确定性构造，两个线程配置共用同一份
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
    mf = scf.UHF(atm).run()
    if not mf.converged:
        raise RuntimeError("%%s: 自由原子 UHF 未收敛" %% sym)
    dm = mf.make_rdm1()
    r_all = []
    for a in range(mol.natm):
        if mol.atom_symbol(a) != sym:
            continue
        r_all.append(np.linalg.norm(coords - mol.atom_coord(a), axis=1))
    r_all = np.concatenate(r_all)
    r_lo, r_hi = max(r_all.min() * 0.5, 1e-4), r_all.max() * 1.02 + 1e-3
    rad = np.exp(np.linspace(np.log(r_lo), np.log(r_hi), NRAD))
    pts = rad[:, None, None] * DIRS[None, :, :]          # (NRAD, NDIR, 3)
    ao = ni.eval_ao(atm, pts.reshape(-1, 3), deriv=1)
    rho = ni.eval_rho(atm, ao, dm, xctype="GGA")[0].reshape(NRAD, NDIR)
    prof = rho.mean(axis=1)                              # 球平均：对方向求均值
    prof = np.clip(prof, 1e-300, None)
    tables[sym] = (rad, np.log(prof), float(mf.e_tot), float(mf.spin_square()[0]),
                   hashlib.sha256(np.asarray(dm).tobytes()).hexdigest()[:16])

W = np.vstack([
    np.exp(np.interp(np.linalg.norm(coords - mol.atom_coord(a), axis=1),
                     tables[mol.atom_symbol(a)][0], tables[mol.atom_symbol(a)][1]))
    for a in range(mol.natm)])
if W.shape[0] != mol.natm:
    raise AssertionError("球平均权重矩阵行数 %%d ≠ 原子数 %%d" %% (W.shape[0], mol.natm))
den = W.sum(axis=0)
n_zero_sa = int((den <= 0).sum())
if n_zero_sa != n_zero:
    raise AssertionError("球平均侧 n_zero=%%d 与生产实现报的 n_zero=%%d 不一致 ⇒ 两边比的不是同一条规则，"
                        "本实验作废，不把不等当巧合" %% (n_zero_sa, n_zero))
if n_zero:
    raise AssertionError("n_zero=%%d：出现分母为零的点，生产实现对它们走最近原子兜底，"
                        "本探针没写那支 ⇒ 拒跑，别悄悄换成另一套规则" %% n_zero)
S_sa = W / den
print("# 球平均权重逐点求和偏离 1 的最大值 = %%.3e" %% float(np.abs(S_sa.sum(axis=0) - 1.0).max()))
own_ns = np.argmax(S_ns, axis=0)
if not np.array_equal(np.argmax(S_sa, axis=0), own_ns):
    print("# 注：球平均后最近原子归属（argmax）与现状不一致的点数 = %%d"
          %% int((np.argmax(S_sa, axis=0) != own_ns).sum()))
np.save(sys.argv[1] + ".ns.npy", np.asarray(S_ns, dtype=np.float64))
np.save(sys.argv[1] + ".sa.npy", np.asarray(S_sa, dtype=np.float64))
json.dump({"natm": mol.natm, "npts": int(coords.shape[0]), "n_zero": int(n_zero),
           "nrad": NRAD, "ndir": NDIR,
           "threads": [os.environ.get(k) for k in
                       ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")],
           "atom_table": {k: {"e_tot": v[2], "s2": v[3], "dm_hash": v[4],
                              "r_lo": float(v[0][0]), "r_hi": float(v[0][-1])}
                          for k, v in tables.items()}},
          open(sys.argv[1] + ".meta.json", "w"))
''' % {"root": ROOT, "name": NAME, "level": LEVEL, "nrad": NRAD, "ndir": NDIR}

TOL_CAUSE = 1e-12
TOL_DRIFT = 1e-3


def worker(threads, path):
    env = dict(os.environ)
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        env[k] = str(threads)
    env["PYTHONIOENCODING"] = "utf-8"
    p = subprocess.run([sys.executable, "-c", WORKER, path], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    if p.returncode != 0:
        print("!! 子进程（%d 线程）失败 rc=%d：\n%s" % (threads, p.returncode, p.stderr[-1500:]))
        sys.exit(2)
    if p.stdout.strip():
        print("# 子进程(%d) stdout：%s" % (threads, p.stdout.strip()[:300]))
    return path


def main():
    print("# 球平均参照密度的线程判别实验  体系 %s  level %d  径向 %d 点 × 方向 %d"
          % (NAME, LEVEL, NRAD, NDIR))
    print("# 生成 %s" % datetime.now(timezone.utc).isoformat())
    print("# 判读规则（跑前写死）：|ΔS_球平均| <= %g 且 |ΔS_现状| >= %g ⇒ DEFINITION_IS_CAUSE；"
          "|ΔS_球平均| >= %g ⇒ ORIENTATION_HYPOTHESIS_REFUTED；|ΔS_现状| <= 1e-14 ⇒ NO_SIGNAL"
          % (TOL_CAUSE, TOL_DRIFT, TOL_DRIFT))
    tmp = tempfile.mkdtemp(prefix="sphprobe_")
    a = worker(1, os.path.join(tmp, "t1"))
    b = worker(8, os.path.join(tmp, "t8"))
    meta = json.load(open(a + ".meta.json"))
    print("# 网格点 %d，原子 %d，n_zero %d" % (meta["npts"], meta["natm"], meta["n_zero"]))
    m8 = json.load(open(b + ".meta.json"))
    print("# 自由原子（T=1 / T=8 各自自报）：线程环境 %s vs %s"
          % (meta["threads"], m8["threads"]))
    for sym in sorted(meta["atom_table"]):
        x, y = meta["atom_table"][sym], m8["atom_table"][sym]
        print("#   %-2s e_tot %.12f vs %.12f (dE=%.1e)  <S^2> %.4f vs %.4f  "
              "1-RDM 哈希 %s vs %s %s"
              % (sym, x["e_tot"], y["e_tot"],
                 abs(x["e_tot"] - y["e_tot"]), x["s2"], y["s2"], x["dm_hash"], y["dm_hash"],
                 "同解" if x["dm_hash"] == y["dm_hash"] else "**异解**"))

    d_ns = np.abs(np.load(a + ".ns.npy") - np.load(b + ".ns.npy")).max()
    d_sa = np.abs(np.load(a + ".sa.npy") - np.load(b + ".sa.npy")).max()
    d_def = np.abs(np.load(a + ".ns.npy") - np.load(a + ".sa.npy")).max()
    print("# max|ΔS| 跨线程（同一份非球平均实现，T=1 vs T=8） = %.3e" % d_ns)
    print("# max|ΔS| 跨线程（球平均 promolecule，T=1 vs T=8）   = %.3e" % d_sa)
    print("# max|ΔS| 同线程（球平均 vs 非球平均，定义之差）      = %.3e" % d_def)

    if d_ns <= 1e-14:
        print("\nVERDICT NO_SIGNAL —— 现状那一列在这套点上取不到跨线程差值样本，本实验无从判别")
        return 2
    if d_sa <= TOL_CAUSE:
        print("\nVERDICT DEFINITION_IS_CAUSE —— 球平均后抖动降到 %.1e（阈值 %g）" % (d_sa, TOL_CAUSE))
        print("   ⇒ 线程数是在替简并的 p 子空间挑取向；这一列在定义上不唯一，"
              "单线程只锁本机 BLAS，不锁取向。")
    elif d_sa >= TOL_DRIFT:
        print("\nVERDICT ORIENTATION_HYPOTHESIS_REFUTED —— 球平均后仍抖到 %.1e" % d_sa)
        print("   ⇒ 我的取向推断被否证，线程叙事原样成立。")
    else:
        print("\nVERDICT INCONCLUSIVE —— |ΔS_球平均| = %.3e 落在两条阈值之间（%g, %g）"
              % (d_sa, TOL_CAUSE, TOL_DRIFT))
        print("   ⇒ 规则没覆盖这个区间，不许当场编判读；把它当未决项报出来。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
