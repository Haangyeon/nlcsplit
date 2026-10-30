"""水单体非局域项的"锚"这一行，改成从跟踪的归档里读对照值、由本脚本算我们自己的值。

为什么要生成它：骨架表里那一行原来手抄了三个 kcal/mol 数（26.765917 / 26.763873 /
26.765687）。其中一个是**算术错的**——0.042650982 Ha × 627.509474 = 26.763895，不是 26.763873。
手抄换算迟早出这种事，所以这一行的每一个数现在都由本脚本打印：我们这边的值现算，
对照值从两份跟踪归档里解析出来，单位换算只做一次、在打印时做。

用法（WSL，源码树）：python3 evidence/orca_control/monomer_anchor_table.py
"""
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

KCAL = 627.509474
AGENTB = os.path.join(ROOT, "evidence", "agentb_sweep",
                      "20260928T071951Z_agentb-sweep_631gstar.txt")
ORCA = os.path.join(ROOT, "evidence", "orca_control", "h2o_wb97xv.out")


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def agentb_selfconsistent_last():
    """取 sweep (1) 的最后一档：返回 (level, npts, E_NLC_total[Ha])。"""
    rows = []
    inside = False
    for ln in open(AGENTB, encoding="utf-8"):
        if ln.startswith("== (1)"):
            inside = True
            continue
        if ln.startswith("== (2)"):
            break
        if not inside:
            continue
        m = re.match(r"\s*(\d+)\s+(\d+)\s+([\d.]+)\s+([+-][\d.]+)\s+([+-][\d.]+)\s+([+-][\d.]+)", ln)
        if m:
            rows.append((int(m.group(1)), int(m.group(2)), float(m.group(6))))
    if not rows:
        raise SystemExit("解析不到 sweep (1) 的任何一行——归档格式变了，不是'没有值'")
    return rows[-1], rows


def orca_nl_energy():
    for ln in open(ORCA, encoding="utf-8"):
        m = re.search(r"NL Energy, E\(C,NL\) *\:\s*(-?[\d.]+)", ln)
        if m:
            return float(m.group(1))
    raise SystemExit("ORCA 归档里没有 'NL Energy, E(C,NL)' 这一行")


def ours(level):
    from pyscf import gto
    from nlcsplit import partition, nlc, geomlib
    mol = gto.M(atom=geomlib.h2o(), basis="6-31g*", unit="Angstrom", verbose=0)
    mf, *_ = partition.scf_grid(mol, xc="wb97x_v", level=level, basis="6-31g*")
    b, C = mf._numint.nlc_coeff("wb97x_v")[0][0]
    coords, weights, owner = partition.atom_partition(mol, level=level, scheme="becke")
    ao = mf._numint.eval_ao(mol, coords, deriv=1)
    rho = mf._numint.eval_rho(mol, ao, mf.make_rdm1(), xctype="GGA")
    sigma = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
    res = nlc.fragment_decomposition(coords, weights, rho[0], sigma,
                                     [list(range(mol.natm))], b=b, C=C, owner=owner)
    return mol, res, len(coords)


if __name__ == "__main__":
    import pyscf
    print("# 水单体 ωB97X-V/6-31G* 非局域项：这一行全部由本脚本生成，正文只引本档")
    print("# python %s  pyscf %s  numpy %s" % (sys.version.split()[0], pyscf.__version__,
                                               __import__("numpy").__version__))
    print("# KCAL = %r" % KCAL)
    for p in (AGENTB, ORCA):
        print("# 归档 %s sha256=%s" % (os.path.relpath(p, ROOT).replace("\\", "/"), sha(p)))
    for mod in ("nlcsplit/nlc.py", "nlcsplit/partition.py", "nlcsplit/geomlib.py",
                "nlcsplit/step_e_kernel.py"):
        print("# 模块 %s sha256=%s" % (mod, sha(os.path.join(ROOT, mod.replace("/", os.sep)))))
    print("# git HEAD %s" % subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"])
          .decode().strip())
    print()

    (alvl, anpts, aha), rows = agentb_selfconsistent_last()
    tail = sorted({"%.9f" % r[2] for r in rows[-4:]})
    oha = orca_nl_energy()
    print("对照（都从跟踪归档解析，不手抄）：")
    print("  独立脚本 sweep(1) level %d, npts %d : %+0.9f Ha = %+0.6f kcal/mol"
          % (alvl, anpts, aha, aha * KCAL))
    print("    它最后四档在最后一位上摆：%s  ⇒ '收敛到某一位'只到 1e-9 Ha" % ", ".join(tail))
    print("  ORCA 6.0.1 E(C,NL)                : %+0.9f Ha = %+0.6f kcal/mol" % (oha, oha * KCAL))
    print()

    print("本包（显式和 + Becke 分区网格，单片段=整个单体）：")
    for level in (1, 2):
        mol, res, npts = ours(level)
        tot = res["E_total"]
        print("  level %d  nao=%d  npts=%d  E_nl=%+0.9f  E_loc=%+0.9f  E_total=%+0.9f Ha"
              "  = %+0.6f kcal/mol   Δ vs ORCA = %+0.6f kcal/mol"
              % (level, mol.nao_nr(), npts, res["E_nl"], res["E_loc"], tot,
                 tot * KCAL, (tot - oha) * KCAL))
