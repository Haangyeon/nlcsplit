"""把一次 WIDEN_ONLY 单体系运行并进总记录 orca_widen.json。

为什么需要：`generator_run_orca_widen.py` 用 WIDEN_ONLY 单独补跑时，写的是
`orca_local/widen/orca_widen.json` 那份**局部**文件；总记录在上一级。以前这一步是手工
搬的，而手工搬正是"体系数与脚本里的清单悄悄分叉"的来源（苯-氨 就是这么漏掉的：
局部跑过、总数没并、正文写着"扩到 6 个体系"，实际清单里根本没它）。

规则：局部文件里的每个 run 必须已收敛、名字不得与总记录撞、且
program/basis/keyword_card 三项口径必须与总记录一致，否则非零退出不写盘。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MASTER = os.path.join(HERE, "orca_widen.json")
PART = os.path.join(HERE, "orca_local", "widen", "orca_widen.json")
KEY_FIELDS = ("program", "basis", "keyword_card", "pal", "quantity", "unit_of_delta")


def main():
    if not os.path.exists(PART):
        sys.exit(f"ABORT 找不到局部结果 {PART}")
    master = json.load(open(MASTER, encoding="utf-8"))
    part = json.load(open(PART, encoding="utf-8"))

    for f in KEY_FIELDS:
        if master.get(f) != part.get(f):
            sys.exit(f"ABORT 口径不一致：{f} 总记录={master.get(f)!r} 局部={part.get(f)!r}")

    have = {r["name"] for r in master["runs"]}
    added = []
    for r in part["runs"]:
        if r["name"] in have:
            sys.exit(f"ABORT {r['name']} 已在总记录里 —— 手工并过一次了，别再来一遍")
        bad = [e["tag"] for e in [r["dimer"]] + r["monomers"] if not e.get("converged")]
        if bad:
            sys.exit(f"ABORT {r['name']} 有未收敛的 run：{bad} —— 数值不进总记录")
        missing = [e["tag"] for e in [r["dimer"]] + r["monomers"] if e.get("nlc_Ha") is None]
        if missing:
            sys.exit(f"ABORT {r['name']} 有取不到 NL 行的 run：{missing}")
        master["runs"].append(r)
        note = os.environ.get("MERGE_CARD_NOTE")
        if note:
            # 关键词卡片与总记录不同时（例如只有 %maxcore 变了），必须把差异写进被并入的
            # 那条 run：`keyword_card` 只存第一行，光比对它是查不出 %maxcore 差四倍的。
            r["card_note"] = note
        added.append(f"{r['name']} ({r['natoms']} 原子)")

    if not added:
        sys.exit("ABORT 局部文件里没有任何可并入的新体系 —— 空并一次等于制造一条假记录")
    master.setdefault("merge_note", []).append(
        "2026-09-30 由 generator_merge_run.py 并入：" + "、".join(added)
        + "。此前总记录缺苯-氨，而脚本清单里也没有它 —— 体系数与清单分叉是靠这份脚本才发现的。")
    with open(MASTER, "w", encoding="utf-8") as fh:
        json.dump(master, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"并入 {len(added)} 个体系：{'、'.join(added)}；总记录现有 {len(master['runs'])} 个体系")


if __name__ == "__main__":
    main()
