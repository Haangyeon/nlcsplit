#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Step M · 水二聚体的 CCSD(T) 反泊松锚点：把 §4 那句"分不清是泛函性质还是我们算错"变成可判定的比较。

为什么要这一跑
--------------
正文报的水二聚体反泊松校正相互作用能是 ωB97X-V/6-31g* 的 -6.129 kcal/mol
（`evidence/l2cp/20260928T213839Z_centos-step_h_l2cp.out:6`，六体系表里的那一行），
未校正值 -7.816，两者之差 1.69 kcal/mol 就是 BSSE。此前 §4 只能写"需要一个带 DOI 的
CCSD(T)/CBS 参考值来判定这是泛函性质还是我们的实现问题"——那是把判断权交给文献。
本脚本不这样做：它在**同一个几何、同一个基组、同一个反泊松约定**下直接用波恩-奥本海默
哈密顿量做耦合簇，得到与我们的 DFT 数字并列的一栏。比较之所以算外部锚，是因为被测的
两条物理路径不同：一条走 ωB97X-V 的非局域关联核加数值网格，一条走显式电子关联、没有网格。

口径（先写死，免得事后换指称）
------------------------------
* 几何：官方 S22 第 2 号水二聚体（`scratch/lit/s22/S22_02.xyz`），与 l2cp 那一行同一段几何。
  这是 S22 的**初始（未弛豫）几何**，不是各自弛豫后的复合物几何；在弛豫几何上 CCSD(T)
  会更深，那是基准定义而不是偏差，正文若换几何必须同时换这一栏。
* 片段：`geomlib.s22_system` 给的 [0,2,3] / [1,4,5]，与 DFT 那条式子完全同一划分。
* 反泊松：ΔE(CP) = E_dimer(二聚体几何) - Σ E_monomer(二聚体几何里的那一半)。
  未校正：ΔE = E_dimer - Σ E_monomer(各自单独成分子时的同一基组)。
* 参考态：RHF。默认冻 O 的 1s（二聚体 2 个、每单体 1 个，成对抵消），并同时报全电子，
  把"冻核"这一选择本身量出来。
* 方法阶梯：MP2、CCSD、CCSD(T)，从同一次 RHF 出发；CBS 不外推——只报逐基组数与相邻
  两档之差，因为两点外推在这份预算下给不出可声称的误差界。

单位：总能量 Hartree，相互作用能换 kcal/mol（KCAL = 627.509474，与全仓一致）。

用法（WSL，仓库根）：
    PYTHONPATH=. python3 -u nlcsplit/step_m_ccsdt.py
基组用逗号挑，默认先跑与正文同基组那一档：
    BASES="6-31g*,cc-pvdz" PYTHONPATH=. python3 -u nlcsplit/step_m_ccsdt.py
"""

import math
import os
import time

from pyscf import gto, cc as pyscf_cc, mp as pyscf_mp  # noqa: E402
from nlcsplit import geomlib                           # noqa: E402

KCAL = 627.509474
OFFDIR = os.environ.get("S22DIR", "scratch/lit/s22")
BASES = [b.strip() for b in os.environ.get("BASES", "6-31g*").split(",") if b.strip()]
NAME = "水二聚体"
METHODS = ("MP2", "CCSD", "CCSD(T)")


def build(symbols, coords, basis):
    block = "\n".join("%s %.10f %.10f %.10f" % (s, x, y, z)
                      for s, (x, y, z) in zip(symbols, coords))
    return gto.M(atom=block, basis=basis, unit="Angstrom",
                 charge=0, spin=0, verbose=0)


def oo_distance(symbols, coords):
    isyO = [i for i, s in enumerate(symbols) if s == "O"]
    if len(isyO) < 2:
        return float("nan")
    a, b = coords[isyO[0]], coords[isyO[1]]
    return math.dist(a, b)


CORE_SHELLS = {"O": 1}          # K shells per element; H and He have none


def freeze_count(symbols):
    return sum(CORE_SHELLS.get(s, 0) for s in symbols)


def freeze_plan(sym_lists, all_electron=False):
    """Per-molecule frozen-orbital counts, from one place, for one convention rung.

    The invariant this enforces - sum over the fragments equals the count for the
    united set - is what the counterpoise difference needs. Returning the dimer's
    number from a separate call is not redundant: it makes the mismatch impossible
    to write down, which is the only defence against the bug recorded in the header.
    """
    if all_electron:
        return [0] * len(sym_lists)
    return [freeze_count(s) for s in sym_lists]


def correlated(mol, frozen):
    """一次 RHF，出 MP2 / CCSD / CCSD(T) 三个**总**能量（Ha），并带回各自用时。

    两个坑都在这函数里：kernel() 返回的是**相关能**而不是总能量，必须自己加 mf.e_tot；
    而且它的返回是三元组 (e_corr, t1, t2)，不是二元组。
    """
    mmem = int(os.environ.get("MAXMEM_MB", "12000"))
    mf = mol.RHF()
    mf.max_memory = mmem
    mf.kernel()
    e_ref = mf.e_tot
    out = {}

    mp2 = pyscf_mp.MP2(mf)
    mp2.max_memory = mmem
    if frozen:
        mp2.frozen = frozen
    t0 = time.time()
    e_mp2 = mp2.kernel()[0]
    out["MP2"] = (e_ref + e_mp2, time.time() - t0)

    ccsd = pyscf_cc.CCSD(mf)
    ccsd.max_memory = mmem
    if frozen:
        ccsd.frozen = frozen
    ccsd.max_cycle = 60
    t0 = time.time()
    e_ccsd = ccsd.kernel()[0]
    out["CCSD"] = (e_ref + e_ccsd, time.time() - t0)

    t0 = time.time()
    et = ccsd.ccsd_t()
    out["CCSD(T)"] = (e_ref + e_ccsd + et, time.time() - t0)
    out["_ref_and_conv"] = (e_ref, bool(mf.converged), bool(ccsd.converged),
                            getattr(mp2, "converged", None))
    return out


def main():
    # 设在 main() 而不是模块顶层：`tests/test_cc_convention.py` 要 import 这个模块，
    # 一个在导入时就改写 BLAS 线程数的脚本会改变整套测试的运行条件。
    os.environ.setdefault("OMP_NUM_THREADS", "8")
    atoms, frags = geomlib.s22_system(NAME, OFFDIR)
    symbols = [a[0] for a in atoms]
    coords = [a[1] for a in atoms]
    print("== Step M · 水二聚体 CCSD(T) 反泊松锚点 ==")
    print("  几何 : 官方 S22 %s/S22_02.xyz（初始几何，未弛豫），原子 %d，O..O=%.4f A"
          % (OFFDIR, len(atoms), oo_distance(symbols, coords)))
    print("  片段 : %s  （与 l2cp 那一行同一划分）" % (frags,))
    print("  基组 : %s" % (", ".join(BASES),))
    print("  方法 : RHF 参考，MP2/CCSD/CCSD(T)；冻 O 1s 与全电子各报一次")
    print("  线程 : OMP_NUM_THREADS=%s   单位: 总能量 Ha，相互作用 kcal/mol (x%.6f)"
          % (os.environ["OMP_NUM_THREADS"], KCAL))
    print("  对照 : 正文 ωB97X-V/6-31g* level-2 未校正 -7.816，反泊松 -6.129 kcal/mol")
    print()

    for basis in BASES:
        print("### basis = %s" % basis)
        dim = build(symbols, coords, basis)
        mono_cp = [build([symbols[i] for i in f], [coords[i] for i in f], basis)
                   for f in frags]
        frag_syms = [[symbols[i] for i in f] for f in frags]
        coreO = freeze_plan(frag_syms)
        print("  复合物 nao=%d nbas=%d nelec=%d；单体 nao=%d/%d；每片段冻核 %s，合计 %d"
              % (dim.nao, dim.nbas, dim.nelectron,
                 mono_cp[0].nao, mono_cp[1].nao,
                 coreO, sum(coreO)))

        for label, ae in (("frozen(O 1s)", False), ("all-electron", True)):
            t0 = time.time()
            # 复合物与单体的冻核数出自同一次 freeze_plan。第一版不是这样：它只在复合物
            # 一侧切约定（fz 随档位换，单体写死成 coreO），于是"全电子"那一档拿全电子的
            # 复合物配冻核的单体，水二聚体算出 -23.2 kcal/mol 这种物理上不可能的数——
            # 差值里 17 kcal 全是只在一侧计入的 O 1s 相关。这类错不会让任何东西报错：
            # 两个数各自都像一个能量，只有它们的差暴露它。
            fz_d = freeze_plan([symbols], all_electron=ae)[0]
            fz_m = freeze_plan(frag_syms, all_electron=ae)
            ed = correlated(dim, fz_d)
            em = [correlated(m, c) for m, c in zip(mono_cp, fz_m)]
            print("  --- %s  (复合物冻 %d，单体冻 %s) ---" % (label, fz_d, fz_m))
            print("    %-9s %18s %18s %18s %12s" % ("method", "E_dimer", "sum E_mono",
                                                    "dE_CP kcal/mol", "s"))
            for k in METHODS:
                dcp = (ed[k][0] - sum(x[k][0] for x in em)) * KCAL
                print("    %-9s %18.10f %18.10f %+18.4f %12.1f"
                      % (k, ed[k][0], sum(x[k][0] for x in em), dcp, ed[k][1]))
            print("    RHF 参考=%18.10f  收敛 RHF=%s CCSD=%s MP2=%s   本档合计 %.0f s"
                  % (ed["_ref_and_conv"][0], ed["_ref_and_conv"][1],
                     ed["_ref_and_conv"][2], ed["_ref_and_conv"][3], time.time() - t0))
        print()


if __name__ == "__main__":
    main()
