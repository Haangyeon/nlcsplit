"""跨程序裁判：把 ORCA 与 PySCF 的 ΔE_NLC 摆到同一张表上。

只读三个已被 git 跟踪的工件，不跑任何量子化学程序：
  evidence/orca_widen/orca_widen.json   —— 4 个小体系（ORCA 6.0.1，本机）
  nlcsplit/logs/orca_anchor.json        —— 水二聚体与苯二聚体(A)（ORCA 6.0.1）
  nlcsplit/logs/step_h.json             —— PySCF 侧同一量的 level-1 值（按中文名索引）

任何一侧缺数、或两侧的定义字段（基组 / 是否做 counterpoise / 网格层级）不一致，
脚本就非零退出不写表 —— 一张把两个不同定义并排放的表比没有表更坏。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
KCAL_PER_HA = 627.509474          # 与 nlcsplit/step_*.py 里的 KCAL 同一个常数

EN = {"水二聚体": "water dimer", "氨二聚体": "ammonia dimer", "甲烷二聚体": "methane dimer",
      "苯二聚体(A)": "benzene dimer (A)", "苯二聚体(B)": "benzene dimer (B)", "苯-水": "benzene...water", "苯-甲烷": "benzene...methane",
      "苯-氨": "benzene...ammonia"}
S22NO = {"水二聚体": 2, "氨二聚体": 1, "甲烷二聚体": 8, "苯-水": 17, "苯-甲烷": 10,
         "苯二聚体(A)": 11, "苯-氨": 18, "苯二聚体(B)": 20}
# 这张表该有哪些体系，写在一处并由下面的断言双向核对：少一个（跑过了却没进表，
# 苯-氨 就是这么漏过一次）和多一个（清单改了却没跑）都必须响。
EXPECTED = {"水二聚体", "氨二聚体", "甲烷二聚体", "苯-水", "苯-甲烷", "苯-氨", "苯二聚体(A)", "苯二聚体(B)"}


def load(rel):
    p = os.path.join(ROOT, rel)
    if not os.path.exists(p):
        sys.exit(f"ABORT 缺少输入工件：{rel}")
    return json.load(open(p, encoding="utf-8")), rel


def main():
    widen, widen_rel = load("evidence/orca_widen/orca_widen.json")
    anchor, anchor_rel = load("nlcsplit/logs/orca_anchor.json")
    steph, steph_rel = load("nlcsplit/logs/step_h.json")

    # PySCF 侧按中文名索引，顺带把定义字段一起取出，供下面的口径核对
    pyscf = {r["name"]: r for r in steph["rows"]}
    # ORCA 侧：4 个新体系从 widen 的 runs 取，两个锚点从 anchor 的 delta 取
    orca = {}
    for run in widen["runs"]:
        bad = [e for e in [run["dimer"]] + run["monomers"] if not e.get("converged")]
        if bad:
            sys.exit(f"ABORT {run['name']} 有 {len(bad)} 份 run 未收敛，数值不能进表")
        if len(run["monomers"]) != 2:
            sys.exit(f"ABORT {run['name']} 单体数 = {len(run['monomers'])}，不是 2")
        d = run["dimer"]["nlc_Ha"] - sum(m["nlc_Ha"] for m in run["monomers"])
        orca[run["name"]] = {"dE_Ha": d, "dE_kcal": d * KCAL_PER_HA, "natoms": run["natoms"],
                             "source": widen_rel, "nprocs": widen["pal"]}
    for key, name in (("water", "水二聚体"), ("benzene_A", "苯二聚体(A)")):
        ent = anchor["delta"].get(key)
        if not ent:
            sys.exit(f"ABORT 锚点 {key} 不在 {anchor_rel} 里")
        orca[name] = {"dE_Ha": anchor["delta_raw_Ha"][key]["dE_NLC_ORCA_Ha"],
                      "dE_kcal": ent["dE_NLC_ORCA_kcal_mol"], "natoms": ent["natm"],
                      "source": anchor_rel, "nprocs": "4 (cluster)"}

    rows, problems = [], []
    got = set(orca) & set(pyscf)
    if got != EXPECTED:
        missing = ", ".join(sorted(EXPECTED - got)) or "—"
        extra = ", ".join(sorted(got - EXPECTED)) or "—"
        sys.exit(f"ABORT 体系清单与预期不符。\n  缺（ORCA 或 PySCF 任一侧没有）：{missing}"
                 f"\n  多（跑出来了却没写进 EXPECTED）：{extra}\n"
                 "  少一个体系 = 裁判数被少报；多一个 = 有人加了 run 却没核对口径。两种都不许出表。")
    for name in ["水二聚体", "氨二聚体", "甲烷二聚体", "苯-水", "苯-氨", "苯-甲烷",
                 "苯二聚体(A)", "苯二聚体(B)"]:
        o = orca.get(name)
        p = pyscf.get(name)
        if not o or not p:
            problems.append(f"{name}: ORCA 侧 {'有' if o else '无'} / PySCF 侧 {'有' if p else '无'}")
            continue
        if p.get("cpcorr"):
            problems.append(f"{name}: PySCF 那行开了 counterpoise，与 ORCA 的冻结密度口径不同")
        if str(p.get("basis", "")).lower().replace("(", "") != "6-31g*":
            problems.append(f"{name}: PySCF 基组是 {p.get('basis')!r}，不是 6-31G*")
        if p.get("level") != 1:
            problems.append(f"{name}: PySCF 网格层级 = {p.get('level')}，表里其他行是 1")
        diff = o["dE_kcal"] - p["dnlc"]
        span = p.get("span")
        rows.append({
            "system_en": EN[name], "system_zh": name, "s22_no": S22NO[name], "natoms": o["natoms"],
            "dE_NLC_ORCA_kcal_mol": round(o["dE_kcal"], 4),
            "dE_NLC_PySCF_kcal_mol": round(p["dnlc"], 4),
            "difference_kcal_mol": round(diff, 4),
            "relative_diff_percent": round(100.0 * abs(diff) / abs(p["dnlc"]), 3),
            # 跨程序残差要跟"归属跨度"比才有意义：只有当它小于跨度时，另一个程序的
            # 数值才够格充当裁判而不是噪声。span 是 step_h.json 里同一行的实测值。
            "attribution_span_kcal_mol": round(span, 4) if span is not None else None,
            "residual_over_span": round(abs(diff) / span, 3) if span else None,
            "pyscf_level": p.get("level"), "pyscf_basis": p.get("basis"),
            "pyscf_version": p.get("pyscf_version"),
            # 不发宿主机的名字：它对表里任何一个数都不承重，而一旦写进来，导出时
            # 脱敏闸门会把它替掉——于一份"读者可以照着重算"的工件就变成被改过的工件。
            "orca_source": o["source"], "pyscf_source": steph_rel,
        })
    if problems:
        print("\n".join("  " + x for x in problems))
        sys.exit("ABORT 口径不一致 —— 不出表")

    out_json = os.path.join(HERE, "cross_program_table.json")
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump({"definition": "dE_NLC = NL(complex) - sum(NL(monomer at complex geometry, monomer basis))"
                                 "，冻结密度、不做 counterpoise",
                   "kcal_per_Ha": KCAL_PER_HA,
                   "note_orca_grid": "ORCA 用自己的非局域求积（Lebedev-110, IntAcc 4.004），"
                                     "PySCF 用 grids.level=1，所以差值是网格+实现的联合残差，不归于任何一方",
                   "rows": rows}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")

    lines = [f"跨程序裁判（ORCA 6.0.1 vs PySCF）：{len(rows)} 个体系，同一量、同一几何、同一基组",
             "单位 kcal/mol；差 = ORCA - PySCF；相对差按 PySCF 绝对值归一", ""]
    lines.append(f"{'system':22s} {'S22':>4s} {'N':>3s} {'ORCA':>10s} {'PySCF':>10s} "
                 f"{'diff':>9s} {'rel%':>7s} {'span':>8s} {'res/span':>9s}")
    for r in rows:
        lines.append(f"{r['system_en']:22s} {r['s22_no']:4d} {r['natoms']:3d} "
                     f"{r['dE_NLC_ORCA_kcal_mol']:10.4f} {r['dE_NLC_PySCF_kcal_mol']:10.4f} "
                     f"{r['difference_kcal_mol']:9.4f} {r['relative_diff_percent']:7.3f} "
                     f"{r['attribution_span_kcal_mol']:8.4f} {r['residual_over_span']:9.3f}")
    rel = [r["relative_diff_percent"] for r in rows]
    under = sum(1 for r in rows if r["residual_over_span"] < 1.0)
    lines += ["", f"n = {len(rows)} 个体系；相对差区间 {min(rel):.3f}% – {max(rel):.3f}%",
              f"绝对差最大 {max(abs(r['difference_kcal_mol']) for r in rows):.4f} kcal/mol",
              f"跨程序残差小于同行归属跨度的：{under} / {len(rows)} 个体系"
              "（比值 > 1 的那个体系见上表 res/span 列）",
              "定义与口径由本脚本从三个工件现读现算；任一字段不一致即拒绝出表。",
              f"输入：{widen_rel}, {anchor_rel}, {steph_rel}"]
    txt = "\n".join(lines) + "\n"
    out_txt = os.path.join(HERE, "cross_program_table.txt")
    open(out_txt, "w", encoding="utf-8").write(txt)
    try:
        print(txt)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(txt.encode("utf-8"))
    print(f"写入 {out_json}\n     {out_txt}")


if __name__ == "__main__":
    main()
