"""满表体系列的唯一性核对：三对"同式不同几何"的格必须分得开。

背景：`verify_s22_folder_identity.py` 把 22 格的片段式全用几何推出来后，发现
`S22_05/13`、`S22_07/15`、`S22_14/21` 三对**片段式完全相同**（只是几何不同）。
如果满表只按"体系名/片段式"排，读者会看到两行一模一样的体系，而两行的数还不一样——
那是可以自己防住的：每格 `.out` 抬头本来就有 `片间最短 dmin`，
用 (片段A, 片段B, dmin) 当键即可唯一。

这个脚本就是那道防线的执行体：撞键就非零退出并点名是哪两格。
退出码：0 唯一；1 有撞键；2 一格的原件都没读到（那不算通过，算没测）。
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
# 同目录那些脚本一样：不把仓根塞进 sys.path 就 import 不到 nlcsplit。
# 上一版没加，靠 `except: return 0` 把这件事吞成了"没有空转"——假绿就是这么来的。
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
RE_FRAGS = re.compile(r"片段 (\S+) \+ (\S+)")
RE_DMIN = re.compile(r"片间最短\s+([\d.]+)")
RE_CELL = re.compile(r"(S22_[0-9A-Za-z]+)_l1_small")


def landed():
    """已落档（rc=0，两种 .rc 写法都认）的格：{键: 格号}。在跑的、被弃的都不算。"""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "evidence", "common_grid",
                                           "*_s22_full_certificate_S22_*_l1_small.out"))):
        rc = p + ".rc"
        if not os.path.exists(rc):
            continue
        if open(rc, encoding="utf-8", errors="ignore").read().strip() not in ("0", "rc=0"):
            continue
        txt = open(p, encoding="utf-8", errors="ignore").read()
        f, d, c = RE_FRAGS.search(txt), RE_DMIN.search(txt), RE_CELL.search(os.path.basename(p))
        if f and d and c:
            out.append(((f.group(1), f.group(2), d.group(1)), c.group(1), os.path.basename(p)))
    return out


def main():
    rows = landed()
    if not rows:
        print("!! 一格已落档的原件都没读到 —— 这是没测，不是通过")
        return 2
    seen, dups = {}, []
    for key, cell, fn in rows:
        if key in seen:
            dups.append((key, seen[key][0], seen[key][1], cell, fn))
        else:
            seen[key] = (cell, fn)
    print("# 体系列唯一性核对：%d 格已落档参与核对，键 = (片段A, 片段B, 片间最短 dmin)" % len(rows))
    if dups:
        print("!! %d 组撞键 —— 表里会出现两行看起来完全一样的体系：" % len(dups))
        for key, c1, f1, c2, f2 in dups:
            print("   %s + %s  dmin=%s   %s 与 %s" % (key[0], key[1], key[2], c1, c2))
            print("      两格原件其实是不同的文件，只是这一键分不开：\n      %s\n      %s" % (f1, f2))
        print("   ⇒ 修法：把 dmin（或 npts）一并列进正文表；两者都仍撞则要给 (A)/(B) 标号。")
        return 1
    # 绿色不等于"测到了"：三对同式格里只要还有一格没落档，本判据对那一对就是空转。
    # 照本仓"跳过≠通过"的老规矩，把空转范围算出来说破。
    print("VERDICT OK —— 每格在 (片段式, dmin) 上唯一")
    pending = twin_pairs_not_yet_both_landed(rows)
    if pending > 0:
        print("# 但本判据**尚未真正受测**：%d 对同式兄弟还没同时落档（已落档 %d 格）。"
              % (pending, len(rows)))
        print("#   绿色只代表「已落档的这些格分得开」；等上面这些对都齐了再跑一次才算真测到。")
    elif pending == 0:
        print("# 22 格已全部落档：本判据这次真的受测过（有成对同式格参与）。")
    return 0


def twin_pairs_not_yet_both_landed(rows):
    """22 格里片段式成对出现的组，有多少对还没双方都落档。

    读不到时**必须说原因**：上一版这里 `except: return 0`，于是"没测成"被打印成
    "没有空转"，正好是这条函数要防的那种假绿。
    """
    try:
        from nlcsplit import geomlib
        from s22_full_certificate import formula
    except Exception as e:
        print("# 空转范围**算不出来**（导入失败：%s）⇒ 别把上面的 OK 读成「配对已验证过」" % e)
        return -1
    allf = {}
    for p in sorted(glob.glob(os.path.join(ROOT, "scratch", "lit", "s22", "S22_*.xyz"))):
        tag = os.path.basename(p)[:-4]
        try:
            atoms = geomlib.read_xyz(p)
            frags = geomlib.split_frags(atoms, geomlib.COV_CUTOFF)
            key = tuple(sorted(formula([atoms[i] for i in f]) for f in frags))
        except Exception:
            continue
        allf.setdefault(key, []).append(tag)
    if not allf:
        print("# 空转范围**算不出来**：一个 xyz 都没读到 ⇒ 别把上面的 OK 读成「配对已验证过」")
        return -1
    landed = {c for _k, c, _f in rows}
    incomplete = [tags for tags in allf.values() if len(tags) > 1
                  and not all(t in landed for t in tags)]
    if incomplete:
        print("# 同式兄弟尚未成对落档的组合：%s"
              % "；".join("/".join(tags) for tags in incomplete))
    return len(incomplete)


if __name__ == "__main__":
    sys.exit(main())
