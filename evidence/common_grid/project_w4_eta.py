"""从**已落档格子的实测用时**外推剩余格的墙钟时间，判断要不要触发降级判据。

为什么要算而不是拍脑袋：目标的降级判据是"排期超过 2 天"，这是个时间条件，得有个估计。
手边正好有已落档各格的实测 `# 用时`（各 `.out` 末行）与原子数，够做一次 log-log 拟合。

两条自律：
1. **只给区间不给单点数**（按拟合残差 ±1σ），这是拟合不是测量；
2. 剩余格的原子数**不硬编**——直接读 `scratch/lit/s22/S22_NN.xyz` 的第一行，
   免得我把"猜的体系大小"当成已知量带进 ETA（本仓这类错今天就犯过一次：把格号记错成甲烷）。

用法：python3 evidence/common_grid/project_w4_eta.py
"""
import glob
import math
import os
import re
import sys

# 这个文件在 evidence/common_grid/ 下，离仓根差**三层**：file -> common_grid -> evidence -> 仓根。
# 上一版少算一层，ROOT 落到 evidence/，glob 变成 evidence/evidence/... → 匹配 0 个文件，
# 于是打出"样本不足不外推"——那是我路径写错，不是数据缺失。**"搜不到"要先怀疑搜索本身。**
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
XYZ = os.path.join(ROOT, "scratch", "lit", "s22")
RE_NATM = re.compile(r"原子\s+(\d+)")
RE_TIME = re.compile(r"#\s*用时\s+([\d.]+)\s*s")
RE_CELL = re.compile(r"(S22_[0-9A-Za-z]+?)_l1_small")
# 批的分波配置（并发数）与尚未落档的格：都从磁盘/批日志反查，见 remaining_cells()
WAVE_CONCURRENCY = {"三": 3, "四": 2}


def measured():
    """已落档且 rc=0 的格：(格号, 原子数, 墙钟秒)。"""
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, "evidence", "common_grid",
                                           "*_s22_full_certificate_S22_*_l1_small.out"))):
        rc = p + ".rc"
        if not (os.path.exists(rc) and open(rc).read().strip() == "0"):
            continue
        txt = open(p, encoding="utf-8", errors="ignore").read()
        m1, m2, m3 = RE_NATM.search(txt), RE_TIME.search(txt), RE_CELL.search(os.path.basename(p))
        if m1 and m2 and m3:
            out.append((m3.group(1), int(m1.group(1)), float(m2.group(1))))
    return out


def xyz_atoms(tag):
    p = os.path.join(XYZ, tag + ".xyz")
    if not os.path.exists(p):
        return None
    try:
        return int(open(p, encoding="utf-8").readline().split()[0])
    except (ValueError, IndexError):
        return None


def remaining_cells(done):
    """所有 S22_*.xyz 里还没落档的格 -> [(格号, 原子数)]，按原子数降序。"""
    have = {c for c, _, _ in done}
    todo = []
    for p in sorted(glob.glob(os.path.join(XYZ, "S22_*.xyz"))):
        tag = os.path.basename(p)[:-4]
        if tag in have:
            continue
        a = xyz_atoms(tag)
        if a:
            todo.append((tag, a))
    return sorted(todo, key=lambda t: -t[1]), have


def fit(pairs):
    n = len(pairs)
    xs = [math.log(a) for a, _ in pairs]
    ys = [math.log(s) for _, s in pairs]
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    slope = num / den
    inter = my - slope * mx
    rms = math.sqrt(sum((y - (inter + slope * x)) ** 2 for x, y in zip(xs, ys)) / n)
    return inter, slope, rms


def inflight(todo):
    """待算格里**已经在跑**的那些：有同名 `.out` 但没有 `rc=0`（半份抬头档）。

    为什么要现算而不是写死"三格"：这句话本身是判据的一部分——"整格耗时计入是上界"
    只对真在跑的格成立，把数字写死就会在波四起起来之后继续宣称"三格"，
    变成一个与实现不符的自述（本仓这类错已犯过）。
    """
    cells = set()
    for tag, _a in todo:
        for p in glob.glob(os.path.join(ROOT, "evidence", "common_grid",
                                        "*_%s_l1_small.out" % tag)):
            rc = p + ".rc"
            if not (os.path.exists(rc) and open(rc).read().strip() == "0"):
                cells.add(tag)
    return sorted(cells)


def parse_waves():
    """从批脚本里读真实的波定义：`wave <并发> <线程> cell...`。

    为什么要读而不是照注释写死：`wave` 的语义是**每发满 par 个就 wait**，
    也就是"分组成 blocks、每组耗时取组内最大"，不是贪心线程池。
    我第一版按贪心算，又把剩余格按大小五五分（实际是 6 + 4），两处都与真实排程不符。
    """
    p = os.path.join(ROOT, "evidence", "common_grid", "run_s22_full_batch.sh")
    waves = []
    for line in open(p, encoding="utf-8", errors="ignore"):
        m = re.match(r"\s*wave\s+(\d+)\s+(\d+)\s+(.+?)\s*$", line)
        if m:
            waves.append((int(m.group(1)), int(m.group(2)), m.group(3).split()))
    return waves


def makespan(pred, par):
    """按 `wave` 的真实语义排：每 par 个一批，批间有 barrier，批耗时 = 批内最大。"""
    total = 0.0
    for i in range(0, len(pred), par):
        grp = pred[i:i + par]
        total += max(grp) if grp else 0.0
    return total


def main():
    rows = measured()
    if len(rows) < 5:
        print("!! 实测样本只有 %d 格，不足以拟合，不外推" % len(rows))
        return 2
    print("# 已落档实测（原子数 / 墙钟秒）")
    for cell, natm, secs in sorted(rows, key=lambda r: r[1]):
        print("   %-8s 原子 %2d  墙钟 %8.1f s" % (cell, natm, secs))
    inter, slope, rms = fit([(a, s) for _, a, s in rows])
    band = math.exp(rms)
    print("\n# log-log 拟合：墙钟 ∝ 原子数^%.2f  样本 %d  残差 ±%.0f%%（按 exp(RMS) 计）"
          % (slope, len(rows), (band - 1) * 100))
    todo, have = remaining_cells(rows)
    print("# 已落档 %d 格；待算 %d 格：%s" % (len(have), len(todo), ", ".join(t for t, _ in todo)))
    if not todo:
        print("\nVERDICT ALL_DONE —— 无需外推")
        return 0
    med = {}
    for tag, a in todo:
        pred = math.exp(inter + slope * math.log(a))
        med[tag] = pred
        print("   %-9s 原子 %2d  墙钟中位 %7.0f s  区间 [%7.0f, %7.0f]"
              % (tag, a, pred, pred / band, pred * band))
    # 按批脚本里的真实波次排程：每波内"发满 par 个就 barrier 等齐"，
    # 已完成格整波跳过；只算还没落档的格（含正在跑的，按其整格耗时计，是保守上界）。
    waves = parse_waves()
    print("\n# 波次（读自 run_s22_full_batch.sh）：")
    tot_mid = tot_lo = tot_hi = 0.0
    for par, th, cells in waves:
        todo_here = [c for c in cells if ("S22_" + c) not in have]
        state = "已完成" if not todo_here else "待算 %d 格（%s）" % (len(todo_here), " ".join(todo_here))
        print("   并发 %d × 线程 %2d：%s" % (par, th, state))
        if not todo_here:
            continue
        vals = [med["S22_" + c] for c in todo_here]
        tot_mid += makespan(vals, par)
        tot_lo += makespan([v / band for v in vals], par)
        tot_hi += makespan([v * band for v in vals], par)
    print("\n# 剩余总墙钟（按真实波次 + barrier 语义）：")
    print("#   中位 %.1f h   区间 [%.1f, %.1f] h" % (tot_mid / 3600, tot_lo / 3600, tot_hi / 3600))
    fly = inflight(todo)
    print("# 口径提醒：%s 按整格耗时计入，所以这是**从现在起的上界式估计**；"
          % ("正在跑的 %d 格（%s）" % (len(fly), " ".join(fly)) if fly else "没有格在跑"))
    print("#   拟合本身只有 %d 个样本、残差 ±%.0f%%，别把它当测量。"
          % (len(rows), (band - 1) * 100))
    print("# 降级判据是「集群排期超过 2 天」——这里估的是本机批，不是集群排队，")
    print("#   但同样用来判断「要不要先交 S22 满 + 一类异质、rVV10 退 SI」。")
    if tot_hi <= 2 * 24 * 3600:
        print("\nVERDICT WITHIN_WINDOW —— 上界 < 48 h，暂不触发降级判据")
        return 0
    print("\nVERDICT DOWNGRADE_DUE —— 上界已越过 48 h：按降级方案交货（S22 满 + 一类异质，"
          "rVV10 全量退 SI），别再等批")
    return 1


if __name__ == "__main__":
    sys.exit(main())
