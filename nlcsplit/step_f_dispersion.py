"""(f) 拆开"VV10 非局域项"与"物理色散"：二聚体 XC 相互作用里各项各占多少。

审稿人要问的就是：你说的片间 NLC 就是色散吗？不是 —— 色散线索同时藏在
半局域关联的跨片部分与非局域项里，而静电/交换排斥也混在半局域那一项中。
本脚用同一个 superposition 公式（复合物 − Σ 单体@复合物几何）分别给出
ΔE_xc(半局域) 与 ΔE_NLC，再报非局域项占 XC 相互作用的比例。

不做的事：不宣称这是 SAPT/EDA 意义上的分解（未做 BSSE/CP 校正、也没分开
静电与交换排斥），只给量级对照；论文的相应段落必须带同一限定。

取数与核对：
  E_NLC 两条独立实现 —— A) PySCF 原生核：numint.nr_nlc_vxc -> libdft.VXC_vv10nlc（不经 libxc）  B) 本包显式对分解
        （V2 核，已与 A、ORCA 对齐到 1e-3 kcal/mol）
  E_xc 两条独立入口 —— C) get_veff 返回的 vhf.exc  D) SCF 自己记的 scf_summary['exc']
  闭合式 —— e_tot == e_nuc + e1 + e_coul + e_xc，残差 >1e-8 Ha 当场报错
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import gto
from pyscf.dft import numint
from nlcsplit import geomlib, partition, nlc

KCAL = 627.509474
BASIS = "6-31g*"
# 本机只做到这个量级；苯 sandwich 的 SCF 里 VV10 双重和占 ~98%，level>=1 请上 CentOS
SYSTEMS = {"(H2O)2": 1, "(C6H6)2": 0}


def _sub(mol, atoms, C):
    """从复合物的 Bohr 坐标里切出片段，写成显式 unit=Bohr 的 atom 串，避免单位歧义。"""
    lines = [f"{mol.atom_symbol(i)} {C[i][0]:.10f} {C[i][1]:.10f} {C[i][2]:.10f}"
             for i in atoms]
    sub = gto.M(atom="\n".join(lines), basis=mol.basis, verbose=0, unit="Bohr")
    assert sub.natm == len(atoms) and np.allclose(sub.atom_coords(), C[atoms]), \
        "切片后单体几何与复合物里的对应原子不一致"
    return sub


def terms(mol, level, tag):
    """返回该体系的 (E_xc 总, E_NLC, E1, E_coul, E_nuc, e_tot)，NLC 走两条独立实现核对。

    注意杂化泛函的记账：PySCF 的 numint.nr_rks 只给半局域部分，**精确交换那项
    是在 get_veff 里补进 vhf.exc 的**。所以这里 E_xc(其余) := vhf.exc − E_NLC，
    它含半局域交换/关联 + 带系数的精确交换，不能叫"纯半局域"。
    """
    mf, X, W, rho, sig = partition.scf_grid(mol, xc="wb97x_v", level=level,
                                            basis=mol.basis)
    assert mf.converged, f"{tag} SCF 未收敛"
    dm = mf.make_rdm1()
    ni = mf._numint

    e_nlc_libxc = float(numint.nr_nlc_vxc(ni, mol, mf.grids, mf.xc, dm)[1])
    b, C_ = ni.nlc_coeff(mf.xc)[0][0]
    w0, kap, keep = nlc.vv10_fields(rho, sig, b=b, C=C_)
    wr = W * rho
    idx = np.where(keep)[0]   # 与 fragment_decomposition 同口径：低于 floor 的点不参与
    beta = (1.0 / 32.0) * (3.0 / (b * b)) ** nlc.BETA_EXP
    e_loc = float(nlc.local_term(beta, wr))
    # PySCF 原生核/ORCA 报的"非局域项"= 双重和 + β∫ρ 两块，这里必须补齐再比
    e_nlc_mine = nlc.pair_energy(X, wr, w0, kap, idx, idx) + e_loc  # A==B ⇒ 0.5·ΣΣ

    vhf = mf.get_veff(mol, dm)
    e_xc = float(vhf.exc)
    e1 = float(np.einsum("ij,ji->", mf.get_hcore(), dm))
    e_nuc = mf.energy_nuc()
    ecoul = float(vhf.ecoul)
    e_semi = e_xc - e_nlc_libxc          # 半局域 xc + 精确交换

    dev = abs(e_nlc_libxc - e_nlc_mine)
    closure = abs(mf.e_tot - (e_nuc + e1 + ecoul + e_xc))
    sum_chk = abs(e_xc - float(mf.scf_summary["exc"]))
    # 两条 NLC 实现的容差随网格走：level 0 粗网格上互差 ~0.05 kcal/mol 是已测事实
    tol = 1e-5 if level >= 1 else 3e-4
    if dev > tol or closure > 1e-8 or sum_chk > 1e-8:
        raise AssertionError(f"{tag} 记账不一致：NLC 两实现差={dev:.3e}(容差 {tol:.0e}) "
                             f"e_tot 闭合残差={closure:.3e} scf_summary 差={sum_chk:.3e} Ha"
                             f" —— 别用这个结果")
    print(f"    {tag:12s} N={len(X):6d}  E_xc(其余)={e_semi*KCAL:+11.4f}  "
          f"E_NLC={e_nlc_libxc*KCAL:+10.4f}  其中β∫ρ={e_loc*KCAL:+9.4f}  "
          f"E_coul={ecoul*KCAL:+12.4f}  NLC两实现差={dev*KCAL:.1e} "
          f"闭合={closure*KCAL:.1e} kcal/mol")
    return dict(e_xc=e_xc, e_nlc=e_nlc_libxc, e_loc=e_loc, e1=e1,
                ecoul=ecoul, e_nuc=e_nuc, e_tot=mf.e_tot, mf=mf, mol=mol)


def report(key, level):
    frags = geomlib.FRAGS[key]
    assert sorted(a for f in frags for a in f) == list(range(sum(len(f) for f in frags)))
    mol = gto.M(atom=geomlib.SYSTEMS[key](), basis=BASIS, verbose=0, unit="Angstrom")
    C = mol.atom_coords()          # Bohr
    # 几何自检：键长写错、H..H 塌缩这类错必须当场暴露，不能等事后对文献
    bohr2a = 1.8897261254
    dd = np.linalg.norm(C[:, None, :] - C[None, :, :], axis=2) / bohr2a
    frag_of = {a: k for k, f in enumerate(frags) for a in f}
    sym = [mol.atom_symbol(i) for i in range(mol.natm)]
    bond = [(dd[i, j], sym[i], sym[j]) for i in range(mol.natm) for j in range(i + 1, mol.natm)
            if dd[i, j] < 1.2 and sym[i] != sym[j]]          # 异种元素近距 = 成键
    gem = [dd[i, j] for i in range(mol.natm) for j in range(i + 1, mol.natm)
           if dd[i, j] < 1.9 and sym[i] == sym[j]]           # 同种元素近距 = geminal H..H 等
    inter = [dd[i, j] for i in range(mol.natm) for j in range(i + 1, mol.natm)
             if frag_of[i] != frag_of[j]]
    gem_txt = f"{min(gem):.4f} Å" if gem else "n/a"
    print(f"\n  {key}  level={level}  成键 n={len(bond)} 范围 "
          f"{min(b[0] for b in bond):.4f}-{max(b[0] for b in bond):.4f} Å  "
          f"geminal 近距 {gem_txt}  片间最短非键 {min(inter):.4f} Å")
    assert all(sum(1 for k in range(mol.natm)
                   if k != i and dd[i, k] < 1.2 and sym[k] != "H") == 1
               for i, s in enumerate(sym) if s == "H"), "有 H 的成键数不是 1"
    assert len(bond) == sum(1 for s in sym if s == "H"), "成键数与 H 数不符"
    assert min(inter) > 1.8, f"片间出现 {min(inter):.3f} Å 的非物理接触"

    d = terms(mol, level, "复合物")
    subs = [terms(_sub(mol, f, C), level, f"单体{i+1}") for i, f in enumerate(frags)]
    m = {k: sum(s[k] for s in subs) for k in d}
    dnlc = (d["e_nlc"] - m["e_nlc"]) * KCAL
    dxc = (d["e_xc"] - m["e_xc"]) * KCAL           # 含 NLC
    dsemi = dxc - dnlc                             # 半局域 + 精确交换
    dloc = (d["e_loc"] - m["e_loc"]) * KCAL
    print(f"    ΔE(电子总能)={(d['e_tot']-m['e_tot'])*KCAL:+8.3f}  "
          f"= Δ核排斥 {(d['e_nuc']-m['e_nuc'])*KCAL:+7.3f} + Δ单电子 {(d['e1']-m['e1'])*KCAL:+8.3f} + "
          f"Δ库仑/精确交换 {(d['ecoul']-m['ecoul'])*KCAL:+8.3f} + Δxc {dxc:+8.3f} kcal/mol")
    print(f"    ΔE_xc(其余，半局域+精确交换)={dsemi:+8.3f}   ΔE_NLC={dnlc:+8.3f}   "
          f"ΔE_xc 总={dxc:+8.3f} kcal/mol")
    print(f"    ΔE_loc(β∫ρ)={dloc:+.3e} kcal/mol"
          f"（∫ρ=电子数是网格恒等式，故此项在 superposition 中**精确抵消** ⇒ "
          f"片间分解只谈双重和是严格的）")
    # 占比只在分母远离零时才有意义：苯 sandwich 里 +2.62 与 -3.26 几乎抵消，
    # "非局域占 ΔE_xc 510%" 这种数毫无信息量，必须改报绝对项。
    if dxc == 0 or abs(dnlc / dxc) > 2.0:
        print(f"    ⚠ 分母抵消：|ΔE_NLC|/|ΔE_xc|={abs(dnlc/dxc):.1f} ⇒ 不报占比，"
              f"只报两个绝对项（吸引与排斥分开看）")
    else:
        print(f"    ⇒ 非局域项占 ΔE_xc 的 {dnlc/dxc*100:.1f}%")
    print(f"    （'其余'那项混着静电与交换排斥，所以这条只是量级对照，不是 SAPT 分解）")
    print(f"    ⇒ ΔE_NLC 应与 step_b 的 dE_NLC / step_c 的 CP 同量级同符号，互为独立复核")
    return dsemi, dnlc


if __name__ == "__main__":
    keys = sys.argv[1:] or list(SYSTEMS)
    print(f"== ωB97X-V/{BASIS}  XC 相互作用拆分（superposition，未做 BSSE 校正）==")
    out = {}
    for key in keys:
        out[key] = report(key, SYSTEMS[key])
    print("\n  汇总（superposition，ωB97X-V/6-31G*；吸引与排斥分开设，不做占比排名）")
    for key, (dsemi, dnlc) in out.items():
        dxc = dsemi + dnlc
        flag = "⚠ 分母抵消" if dxc == 0 or abs(dnlc / dxc) > 2.0 else f"{dnlc/dxc*100:5.1f}%"
        print(f"    {key:9s} ΔE_xc其余 {dsemi:+8.3f}  ΔE_NLC {dnlc:+8.3f}  "
              f"ΔE_xc {dxc:+8.3f}  非局域占比 {flag}")
