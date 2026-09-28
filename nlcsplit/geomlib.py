"""体系几何构造。所有内坐标都是公开的标准值，出处在注释里；不做任何"凭记忆编分子"的事。

单体：
  H2O   rOH = 0.9572 A, <HOH = 104.52 deg
  NH3   rNH = 1.012  A, <HNH = 106.7 deg（锥形）
  CH4   rCH = 1.087  A, 正四面体
  苯    rCC = 1.397 A, rCH = 1.084 A, D6h 平面
  稀有气体 单原子

二聚体：
  水二聚体  S22 型氢键结构：R(O..O) = 2.983 A，H-O..O = 126.8 deg，
            给体 O-H 沿 O..O 轴指向受体；受体两个 H 对 O..O 轴对称。
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
    """S22 型氢键二聚体初始结构。给体 O 在 (0,0,R)，其成键 H 沿 -z 指向受体 O；
    自由 OH 与成键 O-H 夹 104.52 度，置于 xz 平面内朝上。"""
    R = 2.983                       # O..O 距离
    r = 0.9572                      # O-H 键长
    th = 104.52 * DEG               # 水单体 H-O-H 角
    acc = 126.8 * DEG               # 受体 H-O..O 角
    out = [("O", (0.0, 0.0, 0.0))]
    for s in (1.0, -1.0):
        out.append(("H", (s * r * np.sin(np.pi - acc), 0.0, r * np.cos(np.pi - acc))))
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
