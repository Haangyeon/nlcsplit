"""核对 `geomlib.S22` 的"中文体系名 → 文件夹号"是否与文件**内容**一致。

为什么要单独跑这一条：正文与已归档八格用的是"苯-水""甲烷二聚体"这类**名字**，
而名字到字节之间只有一次人写的字典映射（`geomlib.S22`）。这一步错了不会被任何闸门抓到——
几何读得到、算得出、跨度也归一，只是**整格贴错了标签**。
所以这里只干一件事：用与生产代码同一个 `split_frags(..., COV_CUTOFF)` 把每个文件夹切成片段，
按元素式与"这个名字按化学应当是什么"对照。

期望式来自化学名本身（水=H2O、氨=NH3、甲烷=CH4、苯=C6H6），不是从任何测量或记忆里抄的数。

分子式的**写法**不在这儿重新发明：直接 import 生产者 `s22_full_certificate.formula`。
第一版我自己写了一份 `"%s%d"` 的格式化，把 H2O 打成 `H2O1`，于是八个名字**全部**报"不符"——
一次纯格式差异伪装成六张贴错的标签。现在加 `selftest_label_convention()`：
拿一个已知原子表喂进生产者那份 formatter，输出必须等于 EXPECT 用的写法，
否则一开场就拒跑并说明是约定漂移，而不是让判语去承担格式的改动。

不核对的东西（避免越界）：官方 S22 表里的相互作用能、键距、以及文件夹号在 GMTKN55 里的排序，
本机断网取不到上游名单 ⇒ 那是"待核"，不在本脚本的判定范围。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from nlcsplit import geomlib                      # noqa: E402
from s22_full_certificate import formula as frag_label   # noqa: E402  生产者那份写法，单一来源

# 名字 → 该片应有的元素式（按 frag_label 的写法：计数为 1 时不印 1）
EXPECT = {
    "水二聚体": ("H2O", "H2O"),
    "氨二聚体": ("H3N", "H3N"),
    "甲烷二聚体": ("CH4", "CH4"),
    "苯二聚体(A)": ("C6H6", "C6H6"),
    "苯二聚体(B)": ("C6H6", "C6H6"),
    "苯-水": ("C6H6", "H2O"),
    "苯-氨": ("C6H6", "H3N"),
    "苯-甲烷": ("C6H6", "CH4"),
}


def selftest_label_convention():
    """生产者那份 formatter 与 EXPECT 必须同一写法，否则整表会假阳。"""
    probe = [("O", (0.0, 0.0, 0.0)), ("H", (0.96, 0.0, 0.0)), ("H", (-0.24, 0.93, 0.0))]
    got = frag_label(probe)          # 一个水：写法应是 "H2O"，计数为 1 的 O 不印 1
    if got == "H2O":
        return 0
    print("!! 生产者写法变了（一个水打给出 %r，EXPECT 用的是 'H2O' 这一族写法）："
          "先把 EXPECT 跟着改，再判名字对不对" % got)
    return 1


def main():
    print("# S22 名字↔几何内容一致性核对（片段划分用生产代码同一个 split_frags/COV_CUTOFF）")
    if selftest_label_convention():
        return 2
    print("# 自检：分子式写法与生产者 `s22_full_certificate.formula` 一致")
    data_dir = os.path.join(ROOT, "scratch", "lit", "s22")
    print("# 几何目录 %s" % data_dir)
    print()
    bad = []
    for name, fn in sorted(geomlib.S22.items()):
        p = os.path.join(data_dir, fn)
        if not os.path.exists(p):
            print("!! %-10s %-12s 文件不在：%s" % (name, fn, p))
            bad.append(name)
            continue
        atoms = geomlib.read_xyz(p)
        try:
            frags = geomlib.split_frags(atoms, geomlib.COV_CUTOFF)
        except Exception as e:      # 切不出两段时 geomlib 按设计直接抛：报出来，别让一格炸掉整份核对
            print("   %-10s %-12s 原子 %3d  切分失败：%s  => 不符" % (name, fn, len(atoms), e))
            bad.append(name)
            continue
        got = tuple(sorted(frag_label([atoms[i] for i in f]) for f in frags))
        want = tuple(sorted(EXPECT[name]))
        ok = len(frags) == 2 and got == want
        print("   %-10s %-12s 原子 %3d  片段 %s  期望 %s  => %s"
              % (name, fn, len(atoms), " + ".join(got), " + ".join(want),
                 "一致" if ok else "不符"))
        if not ok:
            bad.append(name)

    print()
    if bad:
        print("VERDICT MISMATCH —— %d 个名字与其几何内容不符：%s"
              % (len(bad), "、".join(bad)))
        print("   这不是格式问题（格式已由上面的自检分开管）：贴错标签的格会把体系名带进正文与图件。")
        return 1
    # 全 22 格的**片段式**清单：名字要等联网核对，但"这一格是哪两片"纯几何就能定，
    # 而且是满表 `体系` 那一列真正需要的东西——所以分开报，别让"名字待核"拖住"片段式已知"。
    print("\n## 全部文件夹的片段式（几何推导，不依赖任何名字映射）")
    print("| 文件夹 | 原子 | 片段式（按元素计数） | 名字状态 |")
    print("|---|---|---|---|")
    inv = {}
    for nm, fn in geomlib.S22.items():
        inv[fn] = nm
    import glob as _glob
    for p in sorted(_glob.glob(os.path.join(data_dir, "S22_*.xyz"))):
        fn = os.path.basename(p)
        try:
            atoms = geomlib.read_xyz(p)
            frags = geomlib.split_frags(atoms, geomlib.COV_CUTOFF)
        except Exception as e:                        # 读不动就明说，不猜
            print("| %s | ? | 读取失败：%s | - |" % (fn, e))
            continue
        labs = " + ".join(frag_label([atoms[i] for i in f]) for f in frags)
        st = inv.get(fn, "待核（未进 geomlib.S22 映射）")
        print("| %-12s | %2d | %s | %s |" % (fn.replace(".xyz", ""), len(atoms), labs, st))
    print("\nVERDICT OK —— geomlib.S22 的 %d 个名字全部与其几何内容一致"
          % len(geomlib.S22))
    return 0


if __name__ == "__main__":
    sys.exit(main())
