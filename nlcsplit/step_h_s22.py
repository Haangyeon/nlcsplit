"""(h) S22 子集：官方几何下的片间 NLC 项 + XC 拆分 + 四方案敏感性。

几何一律取 GMTKN55 官方仓库(grimme-lab/GMTKN55, tag v1)里的 struc.xyz，
片段划分由 geomlib.split_frags() 按共价连通性自动给出（不写死索引）。
这样"体系清单"这一栏可复现、可引，也不再需要我自己构造二聚体坐标。

每个体系报五个量：
  ΔE_int   superposition 相互作用能（复合物 − Σ 单体@复合物几何），未做 BSSE 校正
  ΔE_xc    同一 superposition 下的 E_xc 差
  ΔE_NLC   其中非局域项那一份（= 片间成对项 + 片内项的跨单体差，β∫ρ 精确抵消）
  P_frz    冻结自洽密度下的片间成对项（四种归属方案各给一个，附跨度）
  CP       超位置差；P_frz/CP 即"两体可分性"
"""
import os
import socket
import sys
import time

import numpy as np
import pyscf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pyscf import dft, gto

from nlcsplit import geomlib, partition, nlc
from nlcsplit.step_f_dispersion import terms, KCAL

BASIS = os.environ.get("NCBAS", "6-31g*")
LEVEL = int(os.environ.get("NCLV", "1"))
# 反泊松要额外解每个片段在完整基组下的 SCF，苯二聚体这类贵体系用 NCPC=0 跳过
CPCORR = os.environ.get("NCPC", "1") == "1"
SCHEMES = ["becke", "becke-becke-rad", "becke-treutler", "stratmann"]
DATA = os.environ.get("S22DIR") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "lit", "s22")


def build(name):
    """官方几何 → PySCF Mole + 片段索引，并做几何护栏。"""
    atoms, frags = geomlib.s22_system(name, DATA)
    mol = gto.M(atom=[(s, c) for s, c in atoms], basis=BASIS, verbose=0, unit="Angstrom")
    C = mol.atom_coords() / 1.8897261254                    # Bohr → Å
    inter = [np.linalg.norm(C[i] - C[j]) for a in frags for b in frags if a is not b
             for i in a for j in b]
    assert min(inter) > 1.5, f"{name}: 片间最短 {min(inter):.3f} Å，几何可疑"
    return mol, frags, min(inter)


def pair_terms(mol, frags, mf):
    """四种归属方案下的片间成对项 P_frz（kcal/mol）。"""
    ni = mf._numint
    b, C = ni.nlc_coeff(mf.xc)[0][0]
    dm = mf.make_rdm1()
    out = {}
    for scheme in SCHEMES:
        X, W, owner = partition.atom_partition(mol, level=LEVEL, scheme=scheme)
        rho = ni.eval_rho(mol, ni.eval_ao(mol, X, deriv=1), dm, xctype="GGA")
        sig = rho[1] ** 2 + rho[2] ** 2 + rho[3] ** 2
        res = nlc.fragment_decomposition(X, W, rho[0], sig, frags,
                                                   b=b, C=C, owner=owner)
        assert abs(res["E_nl"] - sum(res["intra"].values())
                   - sum(res["inter"].values())) < 1e-10, f"{scheme}: 可加性破了"
        out[scheme] = res["inter"][(0, 1)] * KCAL
    return out


NUMKEYS = ("e_xc", "e_nlc", "e_loc", "e1", "ecoul", "e_nuc", "e_tot")


def counterpoise(mol, frags, level):
    """Boys–Bernardi 反泊松校正的相互作用能 (kcal/mol)。

    单体在**复合物的完整基组**下算：把对方原子写成 ghost-，只带基函数不带核与电子。
    实测本机 PySCF 2.12.1：ghost 片段的 nao 与复合物一致(34)，nelectron 只算自己(10)。
    不做的近似：不对 DM 做 superposition 猜测，直接重解每个片段的 SCF。
    """
    C = mol.atom_coords() / 1.8897261254
    sym = [mol.atom_symbol(i) for i in range(mol.natm)]

    def frag_mol(idxs, ghost_idx):
        lines = [f"{sym[i]} {C[i][0]:.10f} {C[i][1]:.10f} {C[i][2]:.10f}" for i in idxs]
        lines += [f"ghost-{sym[i]} {C[i][0]:.10f} {C[i][1]:.10f} {C[i][2]:.10f}"
                  for i in ghost_idx]
        return gto.M(atom="\n".join(lines), basis=BASIS, verbose=0, unit="Angstrom")

    e_dim = terms(mol, level, "复合物(反泊松参照)")["e_tot"]
    tot = 0.0
    for f in frags:
        ghost = [i for i in range(mol.natm) if i not in set(f)]
        sub = frag_mol(f, ghost)
        assert sub.nao_nr() == mol.nao_nr(), "ghost 片段基组维数与复合物不一致"
        assert sub.nelectron < mol.nelectron, "ghost 片段电子数没减少，划分可能错了"
        mf = dft.RKS(sub); mf.xc = "wb97x_v"; mf.grids.level = level
        mf.kernel()
        assert mf.converged, "反泊松单体 SCF 未收敛"
        tot += mf.e_tot
    return (e_dim - tot) * KCAL


def one(name):
    t0 = time.time()
    mol, frags, dmin = build(name)
    d = terms(mol, LEVEL, "复合物")
    m = {k: 0.0 for k in NUMKEYS}
    for f in frags:
        s = terms(geomlib_sub(mol, f), LEVEL, "单体")
        for k in NUMKEYS:
            m[k] += s[k]
    pint = pair_terms(mol, frags, d["mf"])
    dxc = (d["e_xc"] - m["e_xc"]) * KCAL
    dnlc = (d["e_nlc"] - m["e_nlc"]) * KCAL
    dtot = (d["e_tot"] - m["e_tot"]) * KCAL
    dcp = counterpoise(mol, frags, LEVEL) if CPCORR else None
    # None 而不是 float("nan")：nan 经 {:+7.3f} 会印成 "+nan"，在日志里读起来像算错，
    # 而它真正的意思是"这一档按 NCPC=0 关掉了"。
    dcp_s = "   —  " if dcp is None else f"{dcp:+7.3f}"
    span = max(pint.values()) - min(pint.values())
    # 注意：这里的比值分母是"超位置差"Δ_sup，不是 counterpoise；命名上刻意避开 CP 缩写
    print(f"  {name:10s} 原子{mol.natm:3d} 片间min {dmin:4.2f}Å  "
          f"ΔE_int {dtot:+7.3f}  ΔE_int(反泊松) {dcp_s}  ΔE_xc {dxc:+7.3f}  "
          f"ΔE_NLC {dnlc:+7.3f}  P_frz[becke] {pint['becke']:+7.3f}  "
          f"方案跨度 {span:6.3f}  P/Δsup {pint['becke']/dnlc:5.2f}   "
          f"{time.time()-t0:4.0f}s", flush=True)
    return dict(name=name, natm=mol.natm, dmin=dmin, dtot=dtot, dcp=dcp, dxc=dxc,
                dnlc=dnlc, pint=pint, span=span,
                # 逐行记档位：侧车是按体系名跨批次合并的，只有文件头的 level 会说谎
                # （苯在 level 0 跑过一次、level 1 又跑一次，合并后头是 1、行是 0 的数）
                # 下面几项一律机器生成——provenance 只要需要人手工填，它就一定会过期。
                level=LEVEL, basis=BASIS, cpcorr=bool(CPCORR),
                run_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                pyscf_version=pyscf.__version__, host=socket.gethostname())


def geomlib_sub(mol, atoms):
    """按原子索引切出单体（坐标显式按 Bohr 写出，避免单位歧义）。"""
    C = mol.atom_coords()
    txt = "\n".join(f"{mol.atom_symbol(i)} {C[i][0]:.10f} {C[i][1]:.10f} {C[i][2]:.10f}"
                    for i in atoms)
    return gto.M(atom=txt, basis=BASIS, verbose=0, unit="Bohr")


if __name__ == "__main__":
    keys = sys.argv[1:] or list(geomlib.S22)
    print(f"== S22 子集 ωB97X-V/{BASIS} level={LEVEL}，几何来源 {DATA} ==")
    rows = [one(k) for k in keys]
    print("\n  汇总")
    for r in rows:
        print(f"    {r['name']:10s} ΔE_NLC {r['dnlc']:+7.3f}   P_frz 跨度 "
              f"{r['span']:6.3f} ({(r['span']/abs(r['pint']['becke'])*100 if r['pint']['becke'] else 0):5.1f}%)")
    # 机器可读侧车：图脚本读它，不去解析日志文本（日志排版一改就崩）
    import json
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"), exist_ok=True)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "step_h.json")
    prev = []
    if os.path.exists(out):
        try:
            prev = json.load(open(out, encoding="utf-8")).get("rows", [])
        except Exception:
            prev = []

    def finite(o):
        """NaN/Inf 一律转 None：json.dump 默认 allow_nan=True 会写出 `NaN` 字面量，
        那不是合法 JSON —— Python 能读回，jq / JSON.parse / 别的语言会直接报错。
        侧车是给图脚本和外人读的，必须严格合法。"""
        if isinstance(o, float) and not np.isfinite(o):
            return None
        if isinstance(o, dict):
            return {k: finite(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [finite(v) for v in o]
        return o

    # 合并键必须含档位与反泊松开关。原先只按体系名，于是任何一次 level-1 重跑会把
    # 同名的 level-2 行整行冲掉 —— 今天实际发生过，侧车里 level-2 行因此清零，
    # 只剩 .out 里的数（而 .out 不入库）。见 PROGRESS-nlcsplit.md 15:4x。
    def key(r):
        return (r["name"], r.get("level"), bool(r.get("cpcorr")))
    merged = {key(r): r for r in prev}
    merged.update({key(r): r for r in rows})
    # 保持首次出现的顺序，别让 JSON 行序随重跑抖动（图的自变量靠它）
    order, seen_keys = [], set()
    for r in prev + rows:
        k = key(r)
        if k not in seen_keys:
            seen_keys.add(k)
            order.append(k)
    payload = {"basis": BASIS, "level": LEVEL, "cpcorr": CPCORR, "geometry_source": DATA,
               "rows": [finite(merged[k]) for k in order]}
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, allow_nan=False)
    n_lvl = {}
    for r in payload["rows"]:
        n_lvl[r.get("level")] = n_lvl.get(r.get("level"), 0) + 1
    print(f"\n  侧车 → {out}（累计 {len(payload['rows'])} 行，按档位分布 "
          + ", ".join(f"level {k}: {v}" for k, v in sorted(n_lvl.items())) + "）")
