"""W0 —— rVV10 路线定价：PySCF 的 NLC 核到底有没有实现 rVV10 的阻尼形式。

问题（读源码提出，见 paper/notes/PLAN-20261012-JCTC-route.md §二）：
  WSL PySCF 2.12.1 的 `numint._vv10nlc` 里核形是写死的 VV10 有理阻尼
  （g = R^2*W0 + K，Phi = -1.5/(g*g'*(g+g'))），参数入口只有 nlc_pars=(Bvv,Cvv)；
  而 `dft/xcfun.py` 把 SCAN_RVV10:(15.7,0.0093) 喂进同一个核。
  ⇒ 若 rVV10 的定义式是另一个阻尼形式，这就是"常用程序按 VV10 阻尼实现 rVV10"。

口径（与已入库的 ORCA 裁判记录一致，不新造一条）：
  - 可比量 = **ΔE_NLC**（复合物 − Σ 单体@复合物几何、各自基组、不做 BSSE），
    β∫ρ 那份局域项在超位置差里**精确抵消**；绝对 E_NLC 同时打印但不用于跨程序判定。
  - E_NLC 取自 `pyscf.dft.numint.nr_nlc_vxc`（本仓 `examples/check_fast_pair.py:44`、
    `check_screen_bound_ide.py:121` 用的就是这条，它调 PySCF 自家 C 核 `libdft.VXC_vv10nlc`，**不经 libxc**）。
    PySCF 2.12.1 的 RKS 没有 `energy_nlc()`（实测 AttributeError），别再往那个名字上试。
  - 两档并列：控制档 WB97X_V（已知 8/8 体系 ΔE_NLC 与 ORCA 差 <1%）量化"网格不一致"这个混淆量；
    测试档 SCAN_RVV10 同口径。只有测试档残差 ≫ 控制档残差，才够格谈"实现缺陷"。
  - 不收敛的行走 UNCONVERGED 标记，不进任何对比表。
  - 本脚本只取数与自证，**不下"谁错了"的结论**（那需要第三裁判 Psi4 + rVV10 原始定义式逐式核）。

退出码由外层命令写 `.rc`（不走管道，`| tee` 会吞掉真值——本仓坑 1）。
"""
import datetime as _dt
import inspect
import json
import os
import re
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
# 测试档为什么从 SCAN_RVV10 换成 ωB97M-V（2026-10-12 实测改判，不是改口径迁就结果）：
# 本机这份 ORCA 6.0.1 不认 `SCAN-RVV10` 关键字 —— 6 个 run 全 rc=4，
# ORCA 自己报 `UNRECOGNIZED OR DUPLICATED KEYWORD(S) IN SIMPLE INPUT LINE / SCAN-RVV10`；
# 而 strings ~/orca6/orca 里 rVV10 族只有 `WB97M-V` / `B97M-V` 这类名字。
# ωB97M-V 的非局域项本身就是 rVV10，且比 SCAN-RVV10 用得多 ⇒ 换成它，测试档反而更硬。
RANKS = [("control_WB97X_V", "WB97X_V", "WB97X-V"),
         ("test_WB97M_V", "wb97mv", "WB97M-V")]
S22DIR = os.environ.get("S22DIR") or os.path.join(REPO, "scratch", "lit", "s22")
OUTDIR = os.path.join(REPO, "evidence", "rvv10_referee")

_lines = []


def say(msg):
    print(msg)
    _lines.append(str(msg))


def kernel_form_evidence():
    """把"核形写死"这条断言的**原文与行号**打进档，不留成我的一句话。"""
    src_path = inspect.getfile(numint)
    txt = open(src_path, encoding="utf-8", errors="ignore").read()
    facts = []
    for pat in [r"^\s*Kvv\s*=.*$", r"^\s*Beta\s*=.*$", r"^\s*W0p\s*=\s*\(.*\)\*\*0\.5.*$",
                r"^\s*Kp\s*=.*$", r"^\s*gp\s*=\s*R2\*W0p\s*\+\s*Kp\s*$",
                r"^\s*g\s*=\s*R2\*W0\s*\+\s*K\s*$", r"^\s*gt\s*=\s*g\s*\+\s*gp\s*$",
                r"^\s*T\s*=\s*RpW/\(g\*gp\*gt\)\s*$", r"^\s*F\s*\*=\s*-1\.5\s*$",
                r"^\s*libdft\.VXC_vv10nlc\("]:
        for m in re.finditer(pat, txt, re.M):
            ln = txt[:m.start()].count("\n") + 1
            facts.append((ln, m.group(0).strip()))
    return src_path, facts


def e_nlc_of(atoms, xc_code, tag):
    """同一 basis / 同一 grids.level 下一个体系（复合物或单体@复合物几何）的 E_NLC。"""
    mol = gto.M(atom=[(s, c) for s, c in atoms], basis=BASIS, verbose=0, unit="Angstrom")
    mol.build()
    mf = dft.RKS(mol)
    mf.xc = xc_code
    mf.grids.level = LEVEL
    mf.kernel()
    coefs = mf._numint.nlc_coeff(mf.xc)
    _v, e_arr, _w = numint.nr_nlc_vxc(mf._numint, mol, mf.grids, mf.xc, mf.make_rdm1())
    e_nlc = float(np.sum(e_arr))
    rec = {"tag": tag, "xc_code": xc_code, "converged": bool(mf.converged),
           "e_tot_au": float(mf.e_tot), "e_nlc_au": e_nlc,
           "e_nlc_kcal": e_nlc * KCAL, "nlc_coeff_repr": repr(coefs),
           "nao": int(mol.nao), "nelectron": int(mol.nelectron),
           "npts": int(mf.grids.coords.shape[0]), "natoms": len(atoms)}
    say("     %-10s natoms=%2d converged=%-5s E(C,NL)=%12.8f Eh = %+9.4f kcal/mol  npts=%d  nao=%d"
        % (tag, len(atoms), mf.converged, e_nlc, e_nlc * KCAL, rec["npts"], rec["nao"]))
    if not mf.converged:
        say("     !! UNCONVERGED —— 不进对比表")
    return rec


def write_orca_input(dirpath, base, atoms, comment, xc_orca):
    os.makedirs(dirpath, exist_ok=True)
    xyz = os.path.join(dirpath, "%s.xyz" % base)
    with open(xyz, "w", encoding="utf-8", newline="\n") as f:
        f.write("%d\n%s\n" % (len(atoms), comment))
        for s, c in atoms:
            # 14 位小数：与本仓已入库的 ORCA 输入卡 nlcsplit/ref/orca/inp/h2o_dimer.inp 同精度。
            # 上一版只写 8 位，控制档取回的 NL 项与本仓归档值在末位上不一致 —— 差来自几何小数位，
            # 不是程序差。要拿控制档当"逐位复现归档"的门，坐标就必须同精度写出。
            # 读数本体见本目录 orca_run/*.out 与同代时间戳的 w0_pyscf_side 档，注释里不放数。
            f.write("%s %18.14f %18.14f %18.14f\n" % (s, c[0], c[1], c[2]))
    inp = os.path.join(dirpath, "%s.inp" % base)
    # 关键字卡照抄已入库的成功跑法 nlcsplit/ref/orca/inp/h2o_dimer.inp：`! <xc> 6-31G* TightSCF`。
    # 2026-10-12 实测：本份 ORCA 6.0.1 build 不认带连字符的 `def2-TightSCF`，12 个 run 全部
    # INPUT ERROR / rc=4；小体系沿用 %maxcore 1000（苯二聚体那类 24 原子才需要 4000）。
    card = "! %s 6-31G* TightSCF\n%%pal nprocs 4 end\n%%maxcore 1000\n* xyzfile 0 1 %s.xyz\n" % (xc_orca, base)
    with open(inp, "w", encoding="utf-8", newline="\n") as f:
        f.write("# W0 ORCA 侧。取标签 `NL Energy, E(C,NL)`；grep VV10/nonlocal 在 ORCA 自己输出里命中 0，不要用。\n")
        f.write("# 取数前必须确认 SCF CONVERGED AFTER n + ORCA TERMINATED NORMALLY + 恰好一行 NL Energy。\n")
        f.write("# 几何 = GMTKN55 官方 S22 struc.xyz；单体用复合物几何、各自基组、不做 BSSE（与已入库 ΔE_NLC 口径一致）。\n")
        f.write("# keyword card 原样：\n")
        for l in card.splitlines():
            f.write("# %s\n" % l)
        f.write(card)
    return inp


def main():
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(OUTDIR, exist_ok=True)
    say("# W0 PySCF 侧 —— rVV10 阻尼形式对照  basis=%s  grids.level=%d" % (BASIS, LEVEL))
    say("# 生成 %s   pyscf=%s  numpy=%s  host=%s" % (stamp, pyscf.__version__, np.__version__, os.uname().sysname))
    say("# 几何源：%s" % S22DIR)
    assert os.path.isdir(S22DIR), "缺官方 S22 几何目录：%s" % S22DIR

    say("")
    say("## 事实自证：PySCF 的 NLC 核形（原文行号，非转述）")
    src, facts = kernel_form_evidence()
    say("   文件：%s" % src)
    for ln, line in facts:
        say("   L%-5d %s" % (ln, line))
    say("   ⇒ 若上面出现 `gp=R2*W0p+Kp` / `T=RpW/(g*gp*gt)` / `F*=-1.5`，则核形为 VV10 有理阻尼，")
    say("     且 Phi 的具体形式与 (b,C) 无关 —— 换 rVV10 参数换不掉核形。")

    payload = {}
    for name in SYSTEMS:
        atoms, frags = geomlib.s22_system(name, S22DIR)
        en = geomlib.S22_EN[name]
        say("")
        say("## %s (%s)  natoms=%d  nfrags=%d" % (name, en, len(atoms), len(frags)))
        rec = {"name_en": en, "nfrags": len(frags), "ranks": {}}
        for kind, xc_code, xc_orca in RANKS:
            say("   [%s]  xc=%s" % (kind, xc_code))
            d = os.path.join(OUTDIR, "orca_in", kind)
            comp = e_nlc_of(atoms, xc_code, "complex")
            comp["orca_inp"] = write_orca_input(d, "%s_complex" % en.replace(" ", "_").replace("···", "--"),
                                                atoms, "%s complex (GMTKN55 S22 official)" % en, xc_orca)
            mos = []
            for k, f in enumerate(frags):
                sub = [atoms[i] for i in f]
                mo = e_nlc_of(sub, xc_code, "mono%d" % k)
                mo["orca_inp"] = write_orca_input(d, "%s_mono%d" % (en.replace(" ", "_").replace("···", "--"), k),
                                                  sub, "%s monomer %d at complex geometry" % (en, k), xc_orca)
                mos.append(mo)
            if not (comp["converged"] and all(m["converged"] for m in mos)):
                say("   ⇒ ΔE_NLC 作废（有未收敛行）")
                de = None
            else:
                de = comp["e_nlc_kcal"] - sum(m["e_nlc_kcal"] for m in mos)
                say("   ==> dE_NLC = %+9.4f kcal/mol   (|E_NLC| 复合物 %+9.4f)" % (de, comp["e_nlc_kcal"]))
            rec["ranks"][kind] = {"xc_code": xc_code, "orca_xc": xc_orca,
                                  "complex": comp, "monomers": mos, "dE_NLC_kcal": de}
        payload[en] = rec

    say("")
    say("## 判读口径（写死在这里，不许事后挑档）")
    say("   控制档 (WB97X_V) 的跨程序残差 = 『网格不一致』的量级（先例：8/8 体系 <1%）。")
    say("   测试档 (SCAN_RVV10) 若与 ORCA 的残差 ≫ 控制档，才构成 rVV10 实现形式的疑点。")
    say("   本脚本不宣称任何程序错了。")

    jp = os.path.join(OUTDIR, "%s_w0_pyscf_side.json" % stamp)
    with open(jp, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=2))
    say("")
    say("# 机器可读副本：%s" % jp)
    with open(os.path.join(OUTDIR, "%s_w0_pyscf_side.out" % stamp), "w", encoding="utf-8") as f:
        f.write("\n".join(_lines) + "\n")


if __name__ == "__main__":
    main()
