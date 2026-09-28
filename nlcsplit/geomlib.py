"""体系几何构造。所有内坐标都是公开的标准值，出处在注释里；不做任何"凭记忆编分子"的事。

单体：
  H2O   rOH = 0.9572 A, <HOH = 104.52 deg
  NH3   rNH = 1.012  A, <HNH = 106.7 deg（锥形）
  CH4   rCH = 1.087  A, 正四面体
  苯    rCC = 1.397 A, rCH = 1.084 A, D6h 平面
  稀有气体 单原子

二聚体：
  水二聚体  S22 型氢键结构：R(O..O) = 2.983 A，给体 O-H 沿 O..O 轴（氢键角
            180 度），受体 C2 轴反向平行于该轴（<H-O..O = 127.74 度，S22 表列
            126.8 度，差 0.94 度，取舍见 h2o_dimer 文档）。
            这只是初始结构，正式计算里会做梯度优化后再用。
  苯 sandwich  两个平行环，环面间距 3.81 A，完全重叠（D6h）。
            该构型由对称性即为驻点（净力为零），故不需优化。
"""
import numpy as np

DEG = np.pi / 180.0


def _h2o_monosys(offset=(0.0, 0.0, 0.0), axis_z=True):
    r, th = 0.9572, 104.52 * DEG / 2
    h = [(0.0, r * np.sin(th), r * np.cos(th)), (0.0, -r * np.sin(th), r * np.cos(th))]
    return [("O", offset), ("H", tuple(offset[i] + h[0][i] for i in range(3))),
            ("H", tuple(offset[i] + h[1][i] for i in range(3)))]


def h2o():
    return _h2o_monosys()


def nh3():
    r, th = 1.012, 106.7 * DEG / 2
    # 三个 H 对称分布在 C3 轴两侧
    pts = [("N", (0.0, 0.0, 0.0))]
    for k in range(3):
        phi = 2 * np.pi * k / 3
        pts.append(("H", (r * np.sin(th) * np.cos(phi), r * np.sin(th) * np.sin(phi),
                          r * np.cos(th))))
    return pts


def ch4():
    r = 1.087 / np.sqrt(3)
    return [("C", (0.0, 0.0, 0.0))] + [("H", (s1 * r, s2 * r, s3 * r))
                                       for s1, s2, s3 in ((1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1))]


def benzene(offset=(0.0, 0.0, 0.0)):
    rcc, rch = 1.397, 1.084
    pts = []
    for k in range(6):
        phi = 2 * np.pi * k / 6
        pts.append(("C", (rcc * np.cos(phi), rcc * np.sin(phi), 0.0)))
        pts.append(("H", ((rcc + rch) * np.cos(phi), (rcc + rch) * np.sin(phi), 0.0)))
    return [(s, tuple(c + o for c, o in zip(xyz, offset))) for s, xyz in pts]


def h2o_dimer():
    """S22 型氢键二聚体初始结构（刚性标准单体构造）。

    给体 O 在 (0,0,R)，一个 O–H 沿 −z 严格指向受体 O（氢键角 180 度），自由
    O–H 与它夹 104.52 度、置于 xz 平面朝上；受体的 C2 轴与 O···O 轴反向平行，
    两个 O–H **背向**给体让开孤对。两单体均保持 rOH=0.9572 Å、<HOH=104.52 度。

    与 S22 表列参数的唯一差异：<H–O···O 本构造 = 180 − 104.52/2 = 127.74 度，
    S22 给 126.8 度（差 0.94 度）。二者不能同时严格满足——同时固定 <HOH 和
    <H–O···O 会把受体两个 H 的方位角差写成非 180 度，破坏 Cs 对称。这里优先
    保证单体标准 + 无 H···H 非物理接触（最短 H···H = 2.718 Å）。

    历史坑（2026-09-29 修）：旧版把 126.8 度写成 cos(pi−acc)，受体两个 H 朝
    向给体，H···H 塌到 1.64 Å，且受体单体角被夹成 106.4 度。旧坐标下的所有
    水二聚体数值已作废，须重跑。
    """
    R = 2.983                       # O..O 距离
    r = 0.9572                      # O-H 键长
    th = 104.52 * DEG               # 水单体 H-O-H 角
    acc = np.pi - th / 2.0          # 受体 O-H 与 O..O 轴(+z)的夹角 = 127.74 度
    out = [("O", (0.0, 0.0, 0.0))]
    for s in (1.0, -1.0):
        out.append(("H", (s * r * np.sin(acc), 0.0, r * np.cos(acc))))
    out.append(("O", (0.0, 0.0, R)))
    out.append(("H", (0.0, 0.0, R - r)))
    out.append(("H", (r * np.sin(th), 0.0, R - r * np.cos(th))))
    return out


def benzene_sandwich(d=3.81):
    return benzene() + benzene((0.0, 0.0, d))


SYSTEMS = {
    "He":      lambda: [("He", (0.0, 0.0, 0.0))],
    "Ne":      lambda: [("Ne", (0.0, 0.0, 0.0))],
    "Ar":      lambda: [("Ar", (0.0, 0.0, 0.0))],
    "H2O":     h2o,
    "NH3":     nh3,
    "CH4":     ch4,
    "benzene": lambda: benzene(),
    "(H2O)2":  h2o_dimer,
    "(C6H6)2": benzene_sandwich,
}

# 片段划分：原子序号列表
FRAGS = {
    "(H2O)2":  [[0, 1, 2], [3, 4, 5]],
    "(C6H6)2": [list(range(0, 12)), list(range(12, 24))],
}

# ---------------------------------------------------------------- S22 官方几何
# 来源：Grimme 实验室官方仓库 https://github.com/grimme-lab/GMTKN55 (tag v1) 的
# S22/NN/struc.xyz，原始出处 Jureček et al., Phys. Chem. Chem. Phys. 5, 1811 (2003)。
# 用官方坐标而不是自己构造，是为了让"S22 子集"这张表可复现、可引，且免掉
# "你的二聚体几何是哪来的"这类质疑。取回脚本见 tools/get_s22.sh。
_Z2S = {1: "H", 6: "C", 7: "N", 8: "O", 16: "S"}
# 片段划分阈值(Å)：最长共价键(C–C 1.54) < 1.65 < 最短氢键(O···H 1.81)
COV_CUTOFF = 1.65

S22 = {
    "水二聚体":        "S22_02.xyz",
    "氨二聚体":        "S22_01.xyz",
    "甲烷二聚体":      "S22_08.xyz",
    "苯二聚体(A)":     "S22_11.xyz",
    "苯二聚体(B)":     "S22_20.xyz",
    "苯-水":           "S22_17.xyz",
    "苯-氨":           "S22_18.xyz",
    "苯-甲烷":         "S22_10.xyz",
}


def read_xyz(path):
    """读 struc.xyz（首列可能是原子序数或元素符号），返回 [(symbol, (x,y,z Å)), ...]。"""
    lines = open(path, encoding="utf-8").read().splitlines()
    nat = int(lines[0].split()[0])
    out = []
    for l in lines[2:2 + nat]:
        t = l.split()
        if len(t) < 4:
            raise ValueError(f"{path}: 原子行不足 4 列 -> {l!r}")
        sym = _Z2S[int(t[0])] if t[0].isdigit() else t[0].capitalize()
        out.append((sym, tuple(float(x) for x in t[1:4])))
    if len(out) != nat:
        raise ValueError(f"{path}: 声明 {nat} 个原子，实到 {len(out)}")
    return out


def split_frags(atoms, cutoff=COV_CUTOFF):
    """按共价连通性把复合物切成片段。返回 list[list[int]]，按原子序号升序。

    不写死索引：S22 文件里的原子顺序不保证按分子分组，硬写会静默错切。
    切不出恰好 2 段就直接报错，交人工核对。
    """
    n = len(atoms)
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = sum((atoms[i][1][k] - atoms[j][1][k]) ** 2 for k in range(3)) ** 0.5
            if d < cutoff:
                adj[i].append(j)
                adj[j].append(i)
    seen, frags = set(), []
    for s in range(n):
        if s in seen:
            continue
        stack, comp = [s], set()
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp.add(x)
            stack += [y for y in adj[x] if y not in comp]
        seen |= comp
        frags.append(sorted(comp))
    return frags


def s22_system(name, data_dir, cutoff=COV_CUTOFF):
    """返回 (atoms, frags)：S22 官方几何 + 自动片段划分，并做一致性检查。"""
    import os
    atoms = read_xyz(os.path.join(data_dir, S22[name]))
    frags = split_frags(atoms, cutoff)
    assert len(frags) == 2, f"{name}: 切成 {len(frags)} 段，不是二聚体，需人工核对"
    assert sorted(i for f in frags for i in f) == list(range(len(atoms))), \
        f"{name}: 片段划分没覆盖全部原子"
    return atoms, frags

