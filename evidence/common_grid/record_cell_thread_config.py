"""把每一格 S22 证书原件的**线程配置**整理成一份可引用的记录。

为什么需要它：G5 已经查明 Hirshfeld 那一列随 BLAS 线程数变（1 线程逐位相同、≥2 线程自差 1e-1）。
但落档的 12 份 `.out` 抬头**只记了 level/xc/basis/原子/npts，没记线程数**——
所以"这一格是在几个线程上算的"目前只能从批日志反推。

这份脚本做的就是把那个反推**变成一份有出处的记录**，而不是留在脑子里：
  - 从 `s22_full_batch_*.log` 里取 `提交 S22_NN (K 线程) -> 文件名` 与 `完成 S22_NN rc=…` 两种行；
  - 对每个档名核：文件在不在、`.rc` 在不在、`.rc` 与日志里的 rc 是否一致、
    档内有没有 `# exit=` 自写行；
  - **明确标成"派生"而不是"自报"**——把反推说成自报，就是本仓最忌的那种糊弄。

它同时会说出还差什么：线程数进 `.out` 抬头需要改生产者，而生产者正在被批使用，
所以那一步只能在批跑完之后做（已挂在任务 #12）。
"""
import glob
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LOGS = os.path.join(ROOT, "evidence", "common_grid", "s22_full_batch_*.log")
RE_SUB = re.compile(r"提交 (S22_\d+) \((\d+) 线程\) -> (\S+)")
RE_DONE = re.compile(r"完成 (S22_\d+) rc=(\d+) bytes=(\d+)")


def main():
    logs = sorted(glob.glob(LOGS))
    print("# S22 满表各格线程配置记录（**派生自批日志，不是原件自报**）")
    print("# 生成 %s  批日志 %d 份" % (datetime.now(timezone.utc).isoformat(), len(logs)))
    if not logs:
        print("!! 找不到批日志，无从派生")
        return 2
    subs, done = {}, {}
    for lg in logs:
        for line in open(lg, encoding="utf-8", errors="ignore"):
            m = RE_SUB.search(line)
            if m:
                cell, th, fn = m.group(1), int(m.group(2)), m.group(3)
                subs.setdefault(cell, []).append((th, fn, os.path.basename(lg)))
            m = RE_DONE.search(line)
            if m:
                done[m.group(1)] = (int(m.group(2)), int(m.group(3)))

    cells = sorted(subs)
    print("\n| 格 | 线程 | 原件 | .rc | 档内 # exit= | 状态 |")
    print("|---|---|---|---|---|---|")
    problems, n_ok = [], 0
    for cell in cells:
        for th, fn, src in subs[cell]:
            p = os.path.join(ROOT, "evidence", "common_grid", fn)
            exists = os.path.exists(p)
            rcp = p + ".rc"
            rc = open(rcp).read().strip() if os.path.exists(rcp) else "缺"
            has_exit = "-"
            if exists:
                txt = open(p, encoding="utf-8", errors="ignore").read()
                mm = re.search(r"^#\s*exit\s*=\s*(-?\d+)", txt, re.M)
                has_exit = mm.group(1) if mm else "无"
            if not exists:
                st = "未落档（该次提交没产出文件）"
                problems.append((cell, st + "（来自 " + src + "）"))
            elif rc == "缺":
                # 三种"没有 .rc"要分清：同格已有 rc=0 的另一次提交 ⇒ 这次是被取代；
                # 否则档里也没自报行 ⇒ 真的还在跑。把"被取代"和"在跑"混成一类，
                # 日后读这份记录的人就会以为批还没结束。
                if any(os.path.exists(os.path.join(ROOT, "evidence", "common_grid", f2))
                       and os.path.exists(os.path.join(ROOT, "evidence", "common_grid", f2 + ".rc"))
                       and open(os.path.join(ROOT, "evidence", "common_grid", f2 + ".rc")).read().strip() == "0"
                       for _t, f2, _s in subs[cell] if f2 != fn):
                    st = "已被同格重跑取代"
                elif has_exit == "无":
                    st = "在跑中"
                else:
                    st = "rc 缺但档内已自报"
                    problems.append((cell, "有 # exit= 自报行但缺同名 .rc"))
            elif rc == "0":
                st = "rc=0 已落档"
                n_ok += 1
            else:
                st = "rc=%s 失败档" % rc
                problems.append((cell, "退出码非 0"))
            if exists and has_exit == "无" and rc == "0":
                problems.append((cell, "档内无 # exit= 自写行"))
            print("| %s | %d | `%s` | %s | %s | %s |" % (cell, th, fn, rc, has_exit, st))
    print("\n# 已提交 %d 格（含重跑），其中 rc=0 %d 份；批日志来源：%s"
          % (len(subs), n_ok, ", ".join(os.path.basename(x) for x in logs)))
    # 22 格全了吗：以"有 rc=0 档"为准
    ok_cells = set()
    for f in glob.glob(os.path.join(ROOT, "evidence", "common_grid", "*_s22_full_certificate_S22_??_l1_*.out.rc")):
        if open(f).read().strip() == "0":
            m = re.search(r"(S22_\d\d)_l1_", os.path.basename(f))
            if m:
                ok_cells.add(m.group(1))
    print("# 有 rc=0 原件的格：%d/22 → %s" % (len(ok_cells), " ".join(sorted(ok_cells))))
    dup = [c for c, v in subs.items() if len(v) > 1]
    if dup:
        print("# 同一格提交过多次（重跑）：%s —— 汇总脚本按「最新 rc=0」取，旧档不删"
              % ", ".join(dup))
    uniq_problems = sorted(set(problems))
    if uniq_problems:
        print("\n# 需要点出来的问题（不是失败，是**尚不满足验收第 1 条那句话**的部分）：")
        for c, msg in uniq_problems:
            print("   %s  %s" % (c, msg))
        print("   ⇒ 线程数进 `.out` 抬头要改生产者，而生产者正在被批用；只能等批跑完再做（任务 #12）。")
        print("   ⇒ 在那之前，这份记录是唯一能把「哪一格在几个线程上算的」说清的东西，")
        print("      且它是**派生**的：引用它时必须这么说。")
    print("\nVERDICT NOTE —— 本脚本不判通过与否：线程缺失是已知事实，不是新发现。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
