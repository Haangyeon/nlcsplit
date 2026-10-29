"""W0 第三臂 · (b,C) 在 ΔE_NLC 精度上到底可不可分辨（把"没看出差别"变成"看得出有没有差别"）。

背景：前两臂（同功能号两侧对照）结果是 PySCF 与 ORCA 在 ωB97X-V 与 ωB97M-V **两档上都对到
0.0004 kcal/mol**，与控制档（已入库先例 0.0004）同量级 ⇒ 单凭那一对照，"PySCF 把 rVV10 做成
VV10"这条疑点立不起来。但它也可能是**不可分辨**而不是**不成立**：E_NLC = β·∫ρ + E_NL，
β=(1/32)(3/b²)^{3/4} 随 b 变，两项部分互相抵消，ΔE_NLC 对 b 未必敏感。

本臂直接问这个：把 PySCF 的 `nlc_coeff` 强制成 rVV10 一族常用的 (b,C)=(14.05,0.0359)，
SCF 与 NLC 都用它，看 ΔE_NLC 相对 (6.0,0.01) 那一组动多少、以及它离 ORCA 的数是更近还是更远。

三种结局，都算数：
  R1 强制组明显偏离 ORCA（≫0.0007） ⇒ (b,C) 在这个精度上**可分辨**，
     于是"PySCF 与 ORCA 用的是同一组参数"是硬结论，疑点**证伪**。
  R2 强制组与 (6.0,0.01) 组都落在 ORCA 的 0.0007 内 ⇒ ΔE_NLC **不可分辨**，
     疑点既没证成也没证伪；要换个更敏感的判据（绝对 E_NLC / 逐片段项），不许写任何结论。
  R3 强制组反而**更贴近** ORCA ⇒ PySCF 表里那组是可疑的，但断言仍需第三裁判 + 原始定义式。

纪律：只换 nlc_coeff 一个东西（单变量）；其余基组/网格 level/几何与前两臂逐字相同；
不收敛就整行作废；本脚本不宣称任何程序错了。
"""
import datetime as _dt
import os
import sys

import numpy as np
import pyscf
from pyscf import dft, gto
from pyscf.dft import numint

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO)
from nlcsplit import geomlib  # noqa: E402

BASIS = "6-31g*"
LEVEL = 1
KCAL = 627.50947400
SYSTEMS = ["水二聚体", "甲烷二聚体"]
# (标签, 强制的 (b,C) 或 None = 用 PySCF 自己表里那组)
ARMS = [("as_is_wb97mv", None), ("forced_rvv10_14.05_0.0359", (14.05, 0.0359)),
        ("forced_vv10_6.00_0.0100", (6.0, 0.01))]
S22DIR = os.path.join(REPO, "scratch", "lit", "s22")
OUTDIR = os.path.dirname(os.path.abspath(__file__))

lines = []


def say(s):
    print(s, flush=True)
    lines.append(str(s))


def e_nlc(atoms, xc, forced):
    mol = gto.M(atom=[(s, c) for s, c in atoms], basis=BASIS, verbose=0, unit="Angstrom")
    mol.build()
    mf = dft.RKS(mol)
    mf.xc = xc
    mf.grids.level = LEVEL
    if forced is not None:
        b, C = forced
        mf._numint.nlc_coeff = lambda xc_code, _b=b, _C=C: (((_b, _C), 1),)
    mf.kernel()
    used = mf._numint.nlc_coeff(mf.xc)
    _v, e_arr, _w = numint.nr_nlc_vxc(mf._numint, mol, mf.grids, mf.xc, mf.make_rdm1())
    e = float(np.sum(e_arr))
    say("     %-10s converged=%-5s 用 %s  E(C,NL)=%12.8f Eh = %+9.4f kcal  npts=%d"
        % (last_tag[0], mf.converged, used, e, e * KCAL, mf.grids.coords.shape[0]))
    return e * KCAL, bool(mf.converged)


last_tag = [""]
say("# W0 第三臂 · (b,C) 可分辨性  basis=%s grids.level=%d" % (BASIS, LEVEL))
say("# 生成 %s  pyscf=%s numpy=%s" % (_dt.datetime.now(_dt.timezone.utc).isoformat(),
                                      pyscf.__version__, np.__version__))
say("# 前两臂的对照结果（同目录 w0_pyscf_side 与 orca_run/）：两档残差均 ~0.0004 kcal/mol")
say("")

res = {}
for name in SYSTEMS:
    atoms, frags = geomlib.s22_system(name, S22DIR)
    en = geomlib.S22_EN[name]
    say("== %s (%s) nfrags=%d ==" % (name, en, len(frags)))
    for tag, forced in ARMS:
        last_tag[0] = tag[:10]
        ec, okc = e_nlc(atoms, "wb97mv", forced)
        ms, oks = [], []
        for f in frags:
            em, okm = e_nlc([atoms[i] for i in f], "wb97mv", forced)
            ms.append(em)
            oks.append(okm)
        if okc and all(oks):
            de = ec - sum(ms)
            res.setdefault(en, {})[tag] = de
            say("     ==> dE_NLC = %+9.4f kcal/mol" % de)
        else:
            say("     ==> dE_NLC 作废（有未收敛行）")
    say("")

say("## 判读（写死，不许事后挑档）")
for en, d in res.items():
    base = d.get("as_is_wb97mv")
    for tag in ("forced_rvv10_14.05_0.0359", "forced_vv10_6.00_0.0100"):
        if base is not None and tag in d:
            say("   %-14s %-28s 相对 as_is 动 %.4f kcal/mol" % (en, tag, abs(d[tag] - base)))
say("")
say("   ORCA 侧 ωB97M-V 的 dE_NLC（同几何同基组，见 orca_run/test_WB97M_V__*）：")
say("     (H2O)2 = -0.5965   (CH4)2 = -0.5188   [kcal/mol，由 .out 的 NL Energy 行现算]")
say("   ⇒ 拿上面 R1/R2/R3 三种结局对号，本脚本不下其它结论。")

stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
p = os.path.join(OUTDIR, "%s_w0_forced_params.out" % stamp)
with open(p, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n# exit=0 at %s\n" % _dt.datetime.now(_dt.timezone.utc).isoformat())
print("OUT=%s" % p)
