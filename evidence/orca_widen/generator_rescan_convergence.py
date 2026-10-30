"""就地重扫 orca_widen 的收敛标记 —— 不重跑 ORCA。

为什么需要这个文件：`orca_widen.json` 里的 `converged` 全是 false，而 12 份 .log 每一
份都同时写着 `SCF CONVERGED AFTER n CYCLES` 和 `ORCA TERMINATED NORMALLY`
（`RECHECK_convergence.txt` 是第一次发现这件事的记录）。原因是 JSON 由改判据**之前**
的那版 `generator_run_orca_widen.py` 写出，之后脚本修对了、产物没跟着重生成。
后果不是难看而是危险：一个假阴性判据会把 4 个有效体系整批丢进废纸堆，而 NL 数值本身
一直是对的、也一直被取用。

本脚本只做一件事：用与 `generator_run_orca_widen.py` 完全相同的三个正则重读 .log，
改写 `converged` 字段，并**断言 `nlc_Ha` / `scnl_Ha` 逐位不变**。任何一个数值对不上，
或者重扫后仍有 false，就非零退出不写盘。

跑法（母仓根目录）：
    PYTHONPATH=nlcsplit python3 -u evidence/orca_widen/generator_rescan_convergence.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(HERE, "orca_widen.json")

# 与 generator_run_orca_widen.py 同源，抄在这里是为了让"重扫"不依赖那个脚本的运行环境。
# ORCA 6.0.1 打的是 "SCF CONVERGED AFTER n CYCLES"；"THE SCF HAS CONVERGED" 是别的版本
# 的措辞，拿它当判据会把有效结果全判成失败。
NL_RE = re.compile(r"NL Energy, E\(C,NL\) *: *(-?\d+\.\d+) Eh")
SCNL_RE = re.compile(r"SC\+NL Energy: *(-?\d+\.\d+)")
CONV_RE = re.compile(r"SCF CONVERGED AFTER\s+(\d+)\s+CYCLES")
NORM_RE = re.compile(r"ORCA TERMINATED NORMALLY")


def main():
    data = json.load(open(JSON_PATH, encoding="utf-8"))
    logs = sorted(f for f in os.listdir(HERE) if f.endswith(".log"))
    # 文件名 = 体系名 + _dimer/_mono0/_mono1；tag = 体系名 + " / " + 角色
    ROLE = {"_dimer.log": "复合物", "_mono0.log": "单体0", "_mono1.log": "单体1"}
    by_tag = {}
    for fname in logs:
        for suf, role in ROLE.items():
            if fname.endswith(suf):
                stem = fname[: -len(suf)]
                by_tag[f"{stem} / {role}"] = os.path.join(HERE, fname)
                break
        else:
            sys.exit(f"ABORT 无法给这份日志归类：{fname}")

    changed = 0
    mismatched = []
    still_false = []
    for run in data["runs"]:
        entries = [("dimer", run["dimer"])] + [(f"mono{i}", s) for i, s in enumerate(run["monomers"])]
        for key, ent in entries:
            want = f"{run['name']} / {ent['tag'].split('/')[-1].strip()}"
            path = by_tag.get(want)
            if not path:
                mismatched.append(f"{run['name']}/{key}: 找不到 tag {want!r} 对应的日志")
                continue
            txt = open(path, encoding="utf-8", errors="ignore").read()
            nl, scnl, cv, nm = NL_RE.search(txt), SCNL_RE.search(txt), CONV_RE.search(txt), NORM_RE.search(txt)
            if nl is None:
                mismatched.append(f"{want}: 日志里没有 NL 行")
                continue
            # 数值必须与既有 JSON 逐位相同——本脚本只改判定，不改测量。
            if float(nl.group(1)) != ent["nlc_Ha"]:
                mismatched.append(f"{want}: NL 变了 {ent['nlc_Ha']} -> {nl.group(1)}")
                continue
            if scnl and float(scnl.group(1)) != ent["scnl_Ha"]:
                mismatched.append(f"{want}: SC+NL 变了 {ent['scnl_Ha']} -> {scnl.group(1)}")
                continue
            ok = bool(cv) and bool(nm)
            if not ok:
                still_false.append(f"{want}: conv={bool(cv)} normal={bool(nm)}")
            if ent["converged"] is not ok:
                ent["converged"] = ok
                changed += 1
            ent["convergence_markers"] = {
                "scf_converged_after_cycles": int(cv.group(1)) if cv else None,
                "terminated_normally": bool(nm),
                "log": os.path.basename(path),
            }

    if mismatched:
        print("\n".join("  " + m for m in mismatched))
        sys.exit("ABORT 有日志与 JSON 条目对不上或数值发生变化 —— 未写盘")
    if still_false:
        print("\n".join("  " + s for s in still_false))
        sys.exit("ABORT 重扫后仍有未收敛的 run —— 这些体系的数值不能进正文")

    data["convergence_note"] = (
        "2026-09-30：converged 字段由 generator_rescan_convergence.py 依 .log 重扫更正。"
        "原 JSON 的 false 是判据写错（找 'THE SCF HAS CONVERGED'，ORCA 6.0.1 实际打 "
        "'SCF CONVERGED AFTER n CYCLES'）造成的假阴性；NL/SC+NL 数值逐位未变。"
    )
    with open(JSON_PATH, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"重扫 {sum(len(r['monomers']) + 1 for r in data['runs'])} 份日志，"
          f"改写 converged 字段 {changed} 处，数值零改动")
    for r in data["runs"]:
        print(f"  {r['name']:8s} natoms={r['natoms']:2d}  " + " ".join(
            f"{e['tag'].split('/')[-1].strip()}=conv({e['convergence_markers']['scf_converged_after_cycles']})"
            for e in [r["dimer"]] + r["monomers"]))


if __name__ == "__main__":
    main()
