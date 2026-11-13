"""归属不确定性证书（certificate）：同一个物理量在给定归属方案集合上的上下界，
外加"这个构造是不是退化了"的机器判据。

为什么要有这一件：正文报的是"跨方案的跨度"这一个数，而读者拿到包之后要能做的是
**对自己那个体系算出同一个数**，并且知道什么时候这个数不可信。归属这一侧的失败模式
不是崩掉，是**安静地给出一个归一化完全正确的权重矩阵**——把自由原子全建在原点那一版
就是如此（权重退化成 1/natm，每点和照样是 1）。所以证书必须同时输出"界"和"退化警告"，
只有前者的话，它会把一个坏构造印成一份看起来合法的证书。

判据全部对内不对外：界由方案集合定义，退化由权重矩阵自身的形状定义，
不需要任何外部参照程序。

单位：kcal/mol（系数与包内各 step 模块一致）。
"""
import hashlib

import numpy as np

from . import nlc, partition

KCAL = 627.509474

# 三个退化阈值。前两个只看矩阵形状（与密度无关）；第三个"两个不同名构造给出同一批权重"
# 是分派参数被吃掉的指纹，不是物理巧合。
_UNIFORM_TOL = 1e-12      # 逐点等于 1/natm 的容差
_CAPTURE_TOL = 1e-9       # 某个片段独占全部测度的容差
_NORM_TOL = 1e-8          # 与 fragment_decomposition 内部那条同值


def _fingerprint(S):
    return hashlib.sha256(np.asarray(S, dtype=np.float64).tobytes()).hexdigest()[:16]


def degeneracy_flags(S, name, seen=None):
    """只观察权重矩阵，不改它。返回 (flags, fingerprint)。

    `seen` 是 {方案名: 指纹} 的累积表，用来发现"两个不同名构造逐位相同"；
    单独检查一个矩阵时可以不传。调用方（`certify`）负责把本名字写进 seen。
    """
    S = np.asarray(S, dtype=float)
    if S.ndim != 2:
        raise ValueError("权重矩阵必须是 (natm, N) 二维，收到 %s" % (S.shape,))
    seen = {} if seen is None else seen
    flags = []
    natm, npts = S.shape
    dev = float(np.abs(S.sum(axis=0) - 1.0).max())
    if dev > _NORM_TOL:
        flags.append({"scheme": name, "kind": "not-normalized",
                      "detail": "每点权重和偏离 1 达 %.3e，不能当测度用" % dev})
    # 指纹一：均匀权重。历史上真出过（自由原子全建在原点），每点和仍为 1，界照样算得出。
    if float(np.abs(S - 1.0 / natm).max()) < _UNIFORM_TOL:
        flags.append({"scheme": name, "kind": "uniform-degenerate",
                      "detail": "逐点权重恒等于 1/natm，归属没有发生任何事"})
    # 指纹二：某一个片段独占全部测度（等于没分片）。
    share = S.sum(axis=1) / npts
    if float(share.max()) > 1.0 - _CAPTURE_TOL:
        flags.append({"scheme": name, "kind": "single-fragment-capture",
                      "detail": "片段 %d 独占全部测度" % int(np.argmax(share))})
    fp = _fingerprint(S)
    for other, other_fp in seen.items():
        if other != name and other_fp == fp:
            flags.append({"scheme": name, "kind": "identical-to-other-scheme",
                          "detail": "与 %s 的权重矩阵逐位相同" % other})
    return flags, fp


def certify(mol, fragments, level=1, schemes=None, xc="wb97x_v", basis="6-31g*",
            b=None, C=None, extra_soft=None):
    """把片间项 E_AB 在 `schemes` 上跑一遍，返回逐方案读数、上下界与退化标记。

    参数
      fragments : list[list[int]]  原子序号分组；证书对所有片段对 (k<l) 出界
      schemes   : 方案名序列，默认 `partition.ALL_SCHEMES`（家族内四 + 家族外二）
      extra_soft: {名字: (natm, N) 逐点权重} —— 调用方自定义的构造，与内置方案同一判据。
                  负控走这条路：故意喂一个均匀矩阵，必须看到 uniform-degenerate。

    返回 dict:
      per_scheme[name] = {"E_ab": {(k,l): kcal/mol 或 None}, "E_nl", "E_loc", "npts"}
      bounds[(k,l)]    = {"lo","hi","span","argmin","argmax"}  # 只对未触发退化的方案求界
      flagged          = [{"scheme","kind","detail"}, ...]
      usable           = [方案名]                # 进了界的那几个
      meta             = {"level","basis","xc","b","C","npts","natm"}
      soft             = {方案名: (natm, N)}      # 原样返回权重矩阵，便于外部复核
    """
    schemes = list(partition.ALL_SCHEMES if schemes is None else schemes)
    if len(schemes) < 2:
        raise ValueError("证书至少需要两个归属方案，否则上下界就是那个数本身")
    if len(fragments) < 2:
        raise ValueError("至少两个片段才谈得上片间归属")
    if any(len(f) == 0 for f in fragments):
        raise ValueError("fragments 里有空片段")
    # 方案名在跑自洽场**之前**就核掉：未知方案是最常见的误用，让它等到 SCF 之后才报，
    # 等于让用户付一遍机时换一个拼写错误。
    custom = set() if extra_soft is None else set(extra_soft)
    unknown = [s for s in schemes if s not in partition.ALL_SCHEMES and s not in custom]
    if unknown:
        raise KeyError("未知方案 %s：内置 %s；自定义的要同时出现在 schemes 与 extra_soft"
                       % (unknown, sorted(partition.ALL_SCHEMES)))

    mf, X0, W0, rho0, sig0 = partition.scf_grid(mol, xc=xc, level=level, basis=basis)
    # scf_grid 已经把 eval_rho 的四分量折成 (密度, |grad|²)，这里不能再取一次 [0]。
    rho0 = np.asarray(rho0, dtype=float)
    sig0 = np.asarray(sig0, dtype=float)
    ni = mf._numint
    if b is None or C is None:
        b, C = ni.nlc_coeff(mf.xc)[0][0]

    per_scheme, flagged, seen, soft = {}, [], {}, {}
    for name in schemes:
        if name in partition.ALL_SCHEMES:
            S = np.asarray(partition.scheme_factors(mol, X0, scheme=name, basis=basis))
        elif extra_soft is not None and name in extra_soft:
            S = np.asarray(extra_soft[name], dtype=float)
        else:
            raise KeyError("未知方案 %r：内置 %s；自定义的要同时出现在 schemes 与 extra_soft"
                           % (name, sorted(partition.ALL_SCHEMES)))
        if S.shape != (mol.natm, len(X0)):
            raise ValueError("方案 %s 的权重矩阵形状 %s，应为 (%d, %d)"
                             % (name, S.shape, mol.natm, len(X0)))
        fl, fp = degeneracy_flags(S, name, seen)
        seen[name] = fp
        flagged.extend(fl)
        soft[name] = S
        kinds = {f["kind"] for f in fl}
        if "not-normalized" in kinds:
            # 连测度都不是，后面的分解没有意义；留在 flagged 里，界不取它。
            per_scheme[name] = {
                "E_ab": {(k, l): None for k in range(len(fragments))
                         for l in range(k + 1, len(fragments))},
                "E_nl": None, "E_loc": None, "npts": int(len(X0))}
            continue
        res = nlc.fragment_decomposition(X0, W0, rho0, sig0, fragments, b=b, C=C, soft=S)
        per_scheme[name] = {
            "E_ab": {(k, l): float(res["inter"][(k, l)]) * KCAL
                     for k in range(len(fragments)) for l in range(k + 1, len(fragments))},
            "E_nl": float(res["E_nl"]) * KCAL,
            "E_loc": float(res["E_loc"]) * KCAL,
            "npts": int(len(X0)),
        }

    bad = {f["scheme"] for f in flagged}
    usable = [s for s in schemes if s not in bad]
    pairs = list(per_scheme[schemes[0]]["E_ab"])
    bounds = {}
    for key in pairs:
        vals = {s: per_scheme[s]["E_ab"][key] for s in usable
                if per_scheme[s]["E_ab"][key] is not None}
        if len(vals) < 2:
            # 只剩一个（或零个）可用构造时不给"界"：报 span=0 会被读成"没有歧义"，
            # 而真相是"这套方案集没能构成一次对照"。负控那条就落在这里。
            bounds[key] = {"lo": None, "hi": None, "span": None, "argmin": None,
                           "argmax": None, "usable": sorted(vals),
                           "detail": "可用方案少于两个，界不给（退化标记吃掉了对照）"}
            continue
        lo, hi = min(vals.values()), max(vals.values())
        bounds[key] = {"lo": lo, "hi": hi, "span": hi - lo,
                       "argmin": min(vals, key=vals.get), "argmax": max(vals, key=vals.get)}
    return {"per_scheme": per_scheme, "bounds": bounds, "flagged": flagged,
            "usable": usable,
            "meta": {"level": level, "basis": basis, "xc": xc, "b": float(b), "C": float(C),
                     "npts": int(len(X0)), "natm": int(mol.natm)},
            "soft": soft}
