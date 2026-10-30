"""读两份同机同码、只有 PySCF 版本不同的重算日志，出一张反泊松列的版本归属表。

为什么要单独有这么一个脚本。§3.2 偏差表的 DFT 列此前把两个 PySCF 版本的数并排放在一张表里：
水/氨/甲烷三行来自 2026-09-28 的 CentOS 批次（PySCF 2.14.0），其余五行与 CC 侧都来自
PySCF 2.12.1（<CLUSTER>，以及本机 WSL）。要把它改成一个环境，就得先把"版本到底动了哪一个量、
动了多少"钉死——钉死的方式是单变量重跑（同一台机器、同一份脚本、同一几何、同一 OMP
线程数，只有 PYTHONPATH 里的 PySCF 不同），然后由本脚本从两份 stdout 现读。

判据不是"两边差多少"这一句笼统话，而是逐 (体系, 档位) 一行，并带三件事：
  一、复合物与裸单体的网格点数是否逐版本相同（若相同，漂移就不可能来自它们）；
  二、鬼单体的网格点数是否随版本变（这才是被怀疑的那一处）；
  三、生产 counterpoise() 的返回值与脚本自己重搭的鬼单体是否一致（不一致就说明点数
      不是生产那条式子的点数，本脚本拒绝出表）。

任何一格缺失、任何一次解析失败都抛，不静默跳过——少读 N 行还照样画图的后果，
本仓 2026-10-01 的记录里已经有过。
"""
import os
import re
import sys

V2121 = "evidence/l2cp/20261003T0907Z_wsl2121-cp_levels.out"
V2140 = "evidence/l2cp/20261003T0911Z_wsl2140-cp_levels.out"
SYSTEMS = ("水二聚体", "氨二聚体", "甲烷二聚体")
LEVELS = (1, 2)

BLOCK_RE = re.compile(r"^== BASIS=(\S+) LEVEL=(\d) ==")
ROW_RE = re.compile(r"^\s+(\S+)\s+nao=\s*\d+\s+dcp\(生产\)=([-+]?\d+\.\d+)\s+"
                    r"dcp\(诊断\)=([-+]?\d+\.\d+)\s+差=(\S+)")
GRID_RE = re.compile(r"网格点数 复合物=\s*(\d+)\s+裸单体=\[(\d+),\s*(\d+)\]\s+鬼单体=\[(\d+),\s*(\d+)\]")
E_RE = re.compile(r"e_tot\s+复合物([-+]?\d+\.\d+)\s+裸单体和([-+]?\d+\.\d+)\s+"
                  r"鬼单体和([-+]?\d+\.\d+)\s+未校正ΔE_int=([-+]?\d+\.\d+)")
NEED = ("dcp", "ddiag", "n_complex", "n_bare", "n_ghost", "e_dim", "e_bare", "e_ghost", "dtot")


def parse(path):
    """-> {(system, level): record}；每个 (体系, 档位) 必须恰好出现一次且字段齐全。"""
    if not os.path.exists(path):
        raise SystemExit("缺日志：%s（重算没落地就别出这张表）" % path)
    got, level, cur = {}, None, {}
    with open(path, encoding="utf-8") as fh:
        for ln in fh.read().splitlines():
            m = BLOCK_RE.match(ln)
            if m:
                if m.group(1) != "6-31g*":
                    raise SystemExit("%s: 预期外的基组 %s" % (path, m.group(1)))
                level, cur = int(m.group(2)), {}
                continue
            m = ROW_RE.match(ln)
            if m:
                if cur:
                    raise SystemExit("%s: %s level %d 的块没合上就来了下一行"
                                     % (path, cur.get("name"), level))
                cur = {"name": m.group(1), "dcp": float(m.group(2)),
                       "ddiag": float(m.group(3))}
                continue
            m = GRID_RE.match(ln.strip())
            if m and cur:
                cur.update(n_complex=int(m.group(1)), n_bare=(int(m.group(2)), int(m.group(3))),
                           n_ghost=(int(m.group(4)), int(m.group(5))))
                continue
            m = E_RE.match(ln.strip())
            if m and cur:
                cur.update(e_dim=float(m.group(1)), e_bare=float(m.group(2)),
                           e_ghost=float(m.group(3)), dtot=float(m.group(4)))
                key = (cur["name"], level)
                lack = [k for k in NEED if k not in cur]
                if lack:
                    raise SystemExit("%s: %s/level %s 缺字段 %s"
                                     % (path, key[0], key[1], ",".join(lack)))
                if key in got:
                    raise SystemExit("%s: %s/level %s 出现两次"
                                     % (path, key[0], key[1]))
                got[key] = cur
                cur = {}
    missing = [(s, l) for s in SYSTEMS for l in LEVELS if (s, l) not in got]
    if missing:
        raise SystemExit("%s: 缺 %s" % (path, ", ".join("%s/level%d" % m for m in missing)))
    return got


def main():
    a, b = parse(V2121), parse(V2140)
    print("== 反泊松列的 PySCF 版本归属（同机、同脚本、同几何、OMP_NUM_THREADS=8）==")
    print("   A = 2.12.1 (%s)   B = 2.14.0 (%s)" % (V2121, V2140))
    print("   两份都是 6-31g*、官方 S22 初始几何、level 1 与 level 2 各一档\n")
    worst = 0.0
    ghost_same = []
    for name in SYSTEMS:
        for level in LEVELS:
            ra, rb = a[(name, level)], b[(name, level)]
            for tag, r in (("A", ra), ("B", rb)):
                if abs(r["dcp"] - r["ddiag"]) > 1e-6:
                    raise SystemExit("%s: %s level %d 生产/诊断反泊松不一致 %.1e"
                                     % (tag, name, level, abs(r["dcp"] - r["ddiag"])))
            if ra["n_complex"] != rb["n_complex"] or ra["n_bare"] != rb["n_bare"]:
                raise SystemExit("%s level %d: 复合物/裸单体点数随版本变了（%s 对 %s），"
                                 "漂移的归属要重写" % (name, level, ra["n_complex"],
                                                      rb["n_complex"]))
            d = ra["dcp"] - rb["dcp"]
            worst = max(worst, abs(d))
            ghost_same.append(ra["n_ghost"] == rb["n_ghost"])
            print("  %-8s level %d  dcp: A=%+.6f  B=%+.6f  A-B=%+.4f kcal/mol"
                  % (name, level, ra["dcp"], rb["dcp"], d))
            print("             ΔE_int(未校正): A=%+.6f B=%+.6f  差=%+.1e   "
                  "BSSE: A=%.4f B=%.4f"
                  % (ra["dtot"], rb["dtot"], ra["dtot"] - rb["dtot"],
                     ra["dcp"] - ra["dtot"], rb["dcp"] - rb["dtot"]))
            print("             网格点数 复合物 %d/%d  裸单体 %s/%s  鬼单体 %s/%s"
                  % (ra["n_complex"], rb["n_complex"], ra["n_bare"], rb["n_bare"],
                     ra["n_ghost"], rb["n_ghost"]))
    print("\n== 同一版本内，网格档位对反泊松量的影响 ==")
    for name in SYSTEMS:
        for tag, src in (("2.12.1", a), ("2.14.0", b)):
            d1, d2 = src[(name, 1)]["dcp"], src[(name, 2)]["dcp"]
            t1, t2 = src[(name, 1)]["dtot"], src[(name, 2)]["dtot"]
            print("  %-8s %s  dcp level1=%+.4f level2=%+.4f 移动=%+.4f  "
                  "而 ΔE_int(未校正) 移动=%+.4f" % (name, tag, d1, d2, d2 - d1, t2 - t1))
    print("\n判据：跨版本的 |A-B| 最坏 %.4f kcal/mol（六格取最大）。" % worst)
    print("复合物与裸单体的点数已逐格核过：两版本完全相同（否则上面就抛了）。")
    print("鬼单体的点数是否相同：%s。"
          % ("六格全同" if all(ghost_same) else "有 %d/6 格不同——漂移落在零核电荷原子的网格上"
             % sum(1 for x in ghost_same if not x)))


if __name__ == "__main__":
    main()
