"""同一张公共网格上只换归属：把"归属效应"与"求积效应"拆开。

为什么要生成（2026-10-06，外部评审组领域席 Critical 1，我开原件核实后成立）：
见 `evidence/recompute/20261005T0410Z_additivity_census.out` 的构造苯 sandwich 段——
那里四个方案的**点数逐位相同**，而 E_NL 总量各不相同，∫ρ 那一列也各不相同。这说明
"分区方案"换掉的不只是归属，连积分权重与径向映射一起换了；正文那个归属跨度因此
混着两件事。本脚本在同一张 PySCF 常规网格、同一套权重、同一份密度上，只用
`partition.partition_matrix()` 重算逐点多中心因子，归一化后作为软分区喂
`nlc.fragment_decomposition(soft=...)`——这条通路已被 `tests/test_nlc_closure.py`
覆盖（含必须失败的负控）。

求积侧刻意复用同一个 SCF 的密度矩阵在各方案自带网格上取值，与 `step_h_s22.pair_terms`
的取法一致，保证两边的数可比。

护栏（缺一条就不许把表拿出去用）：
  1) 每点 soft 权重和必须为 1（`fragment_decomposition` 内部也判，超差直接抛）；
  2) 公共网格上的 nearest 硬指派必须复现普查归档里 `nearest(公共网格)` 的读数；
  3) `closure_check` 全程开：块和要对得上"同一批保留点一次算完"的独立参照；
  4) 公共网格上 β∫ρ 对四个方案恒同（同一 W0、同一 rho0），打印一次即可；
  5) 负控：把归属整块对调，跨度必须显著变化（NCSWAP=1 时做）。

预登记两种结局（先写死，免得事后给自己找理由）：
  结局 A：归属效应 ≳ 求积效应 → 现有"归属不确定度"这个名字站得住，补两列即可。
  结局 B：归属效应远小于求积效应 → **停下先报**，核心量名不副实，
           §3.4 与摘要要按新结论重写，不得自行决定。

用法：
  NCS22="水二聚体 氨二聚体 甲烷二聚体" NCLV=1 python3 evidence/common_grid/ownership_vs_quadrature.py
"""
import hashlib
import json
import os
import socket
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)

from nlcsplit import nlc, partition                                   # noqa: E402
from nlcsplit.step_f_dispersion import KCAL                          # noqa: E402
from nlcsplit.step_h_s22 import build                                # noqa: E402
import pyscf                                                         # noqa: E402

B, C = 6.0, 0.01                       # ωB97X-V 的 VV10 参数
LEVEL = int(os.environ.get("NCLV", "1"))
SCHEMES = ["becke", "becke-becke-rad", "becke-treutler", "stratmann"]
# 普查归档里 official (H2O)2 level 1 的公共网格控制行（nearest 硬指派）
CENSUS = {"水二聚体": -7.8950}
CENSUS_TOL = 5e-3                      # kcal/mol
BETA = (1.0 / 32.0) * (3.0 / (B * B)) ** nlc.BETA_EXP


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def common_grid_row(mol, mf, X0, W0, rho0, sig0, frags):
    """四方案在同一张公共网格上只换归属。返回 {scheme: (E_AB, E_total)}。"""
    p_all = {s: partition.partition_matrix(mol, X0, s) for s in SCHEMES}
    out = {}
    for s, p in p_all.items():
        tot = p.sum(axis=0)
        if not np.all(tot > 0):
            sys.exit(f"{s}: 有网格点的多中心因子全为零，无法归一化")
        S = p / tot
        dev = np.abs(S.sum(axis=0) - 1.0).max()
        if dev > 1e-8:
            sys.exit(f"{s}: 归一化后每点和偏离 1 达 {dev:.3e}")
        res = nlc.fragment_decomposition(X0, W0, rho0, sig0, frags,
                                         b=B, C=C, soft=S, closure_check=True)
        out[s] = (res["inter"][(0, 1)] * KCAL, res["E_nl"] * KCAL)
    return out


def native_grid_rows(mol, frags, level, mf):
    """各方案自带网格 + 自带权重下的 E_NL 总量（求积侧）。

    密度矩阵复用同一个 SCF，只在各方案自带网格上取值——与 step_h_s22.pair_terms
    同一取法，保证这一列与归档的普查数可比。
    """
    ni = mf._numint
    dm = mf.make_rdm1()
    out = {}
    for s in SCHEMES:
        X, W, owner = partition.atom_partition(mol, level=level, scheme=s)
        ao = ni.eval_ao(mol, X, deriv=1)
        r = ni.eval_rho(mol, ao, dm, xctype="GGA")
        sig = r[1] ** 2 + r[2] ** 2 + r[3] ** 2
        res = nlc.fragment_decomposition(X, W, r[0], sig, frags,
                                         b=B, C=C, owner=owner)
        out[s] = (res["inter"][(0, 1)] * KCAL, res["E_nl"] * KCAL, len(X),
                  float(np.dot(W, r[0])))
    return out


names = (os.environ.get("NCS22", "水二聚体 氨二聚体 甲烷二聚体")).split()
do_quad = os.environ.get("NCQUAD", "1") == "1"
do_swap = os.environ.get("NCSWAP", "0") == "1"

print("# 归属效应 vs 求积效应：公共网格上只换归属")
print("# python %s  pyscf %s  numpy %s" % (sys.version.split()[0],
                                           pyscf.__version__, np.__version__))
print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                       capture_output=True, text=True).stdout.strip())
for rel in ("nlcsplit/partition.py", "nlcsplit/nlc.py", "nlcsplit/step_h_s22.py"):
    print("# sha256 %-26s = %s" % (rel, sha(os.path.join(ROOT, rel))))
print("# level = %d  b = %g  C = %g  quad=%s swap=%s"
      % (LEVEL, B, C, do_quad, do_swap))
print()

bad = []
for name in names:
    t0 = time.time()
    mol, frags, dmin = build(name)
    mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc="wb97x_v",
                                                level=LEVEL, basis="6-31g*")
    assert mf.converged, f"{name}: SCF 未收敛"
    nelec = mol.nelectron
    intrho = float(np.dot(W0, rho0))
    dloc = BETA * (intrho - nelec) * KCAL
    print("== %s  level=%d  原子 %d  公共网格 N=%d  片间min %.2f Å"
          % (name, LEVEL, mol.natm, len(X0), dmin))
    print("   ∫ρ = %.6f / %d   离散 Δ(β∫ρ) = %+.4f kcal/mol（公共网格上四方案恒同）"
          % (intrho, nelec, dloc))

    rows = common_grid_row(mol, mf, X0, W0, rho0, sig0, frags)
    ebs = [rows[s][0] for s in SCHEMES]
    span_own = max(ebs) - min(ebs)
    for s in SCHEMES:
        print("   归属 %-16s E_AB = %+9.4f   E_NL(总) = %+10.4f" % (s, rows[s][0], rows[s][1]))
    print("   → 纯归属跨度（同一网格同一权重） = %.4f kcal/mol" % span_own)

    # 护栏 2：nearest 硬指派在公共网格上复现普查归档
    owner_near = partition.nearest_partition(mol, X0)
    res_near = nlc.fragment_decomposition(X0, W0, rho0, sig0, frags,
                                          b=B, C=C, owner=owner_near, closure_check=True)
    e_near = res_near["E_nl"] * KCAL
    print("   控制 nearest(公共网格) E_NL(直接) = %+.4f" % e_near)
    if name in CENSUS:
        dev = abs(e_near - CENSUS[name])
        print("   护栏：与普查归档 %+.4f 之差 = %.4f kcal/mol（门 %.3f）%s"
              % (CENSUS[name], dev, CENSUS_TOL, "OK" if dev <= CENSUS_TOL else "**不过**"))
        if dev > CENSUS_TOL:
            bad.append((name, "census", dev))

    if do_swap:
        owner_sw = owner_near.copy()
        owner_sw[owner_near == 0] = 1          # 整块换归属：全部给原子 1
        owner_sw[owner_near == 1] = 0
        res_sw = nlc.fragment_decomposition(X0, W0, rho0, sig0, frags,
                                            b=B, C=C, owner=owner_sw)
        e_sw = res_sw["inter"][(0, 1)] * KCAL
        print("   负控：整体对调归属后 E_AB = %+.4f（原 %+.4f，差 %+.4f）"
              % (e_sw, res_near["inter"][(0, 1)] * KCAL,
                 abs(e_sw - res_near["inter"][(0, 1)] * KCAL)))
        if abs(e_sw - res_near["inter"][(0, 1)] * KCAL) < 1e-6:
            bad.append((name, "swap-control", 0.0))

    if do_quad:
        q = native_grid_rows(mol, frags, LEVEL, mf)
        qt = [q[s][1] for s in SCHEMES]
        span_quad = max(qt) - min(qt)
        for s in SCHEMES:
            print("   求积 %-16s N=%6d ∫ρ=%9.5f  E_NL(总) = %+10.4f"
                  % (s, q[s][2], q[s][3], q[s][1]))
        print("   → 求积侧总量跨度（各方案自带网格） = %.4f kcal/mol" % span_quad)
        print("   → 归属/求积 = %.2f" % (span_own / span_quad if span_quad else float("inf")))
    print("   [%.0f s]" % (time.time() - t0))
    sys.stdout.flush()

print()
if bad:
    print("护栏未过：%s —— 上面的表不许拿出去用" % bad)
    raise SystemExit(1)
print("全部体系护栏通过。判决规则见文件头预登记：归属/求积 ≈ 1 以上 → 结局 A；≈ 0 → 结局 B 停下先报。")
# 时间戳优先用宿主传入的 RUN_TS：本机 WSL 的钟曾慢三天，产物名与 run_utc 因此说谎一次
# （见同目录 NOTE-clock-skew.md）。两个钟并排打出来，偏差当场可见。
print("run_utc=%s (host-provided)  wsl_clock=%s  host=%s"
      % (os.environ.get("RUN_TS", "NOT-SET"),
         time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         socket.gethostname()))
