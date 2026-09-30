"""扩外部裁判：本机 ORCA 6.0.1 跑 4 个体系的 superposition 三元组（复合物 + 两单体）。

为什么能做：2026-09-30 实测本机 /mnt/e/Program Files/orca-6.0.1 这份 Linux 版
（经 ~/orca6 无空格符号链接调用，%pal nprocs 4）把已入库的水二聚体锚点**逐位复现**：
SC+NL -152.766499612、NL Energy, E(C,NL) 0.084358235133 Eh，与 evidence/orca_run/h2o_dimer.out 相同。
nprocs 8/16 在这台 WSL 上超槽起不来，4 是能用的最大档，已用同一体系证明它不改印出来的位数。

选这 4 个体系的理由（不是随便凑数）：它们正是稿件里最被依赖的四个端点 ——
  甲烷二聚体   = "223%" 那一行（代理 A 判：本仓闸门禁止对它报占比）
  苯-水        = 方案跨度最大端 0.247
  苯-甲烷      = 跨度 0.213
  氨二聚体     = 跨度 0.029、相对 4.5%
已有锚点：水二聚体、苯二聚体 ⇒ 补完后共 6 个体系有独立程序对表。

口径与 step_h 完全一致：单体取**复合物几何、单体自己的基组**（不做 ghost ⇒ superposition
差，未做 BSSE），功能/基组/SCF 关键字照抄 nlcsplit/ref/orca/inp/*.inp。
"""
import json
import os
import re
import subprocess
import sys
import time

# 本文件在 <repo>/scratch/ 下，所以仓库根是 dirname(dirname(abspath)) —— 两层。
# 上一版多套了一层 dirname，指到 E:\Project，于是 import 直接失败（驱动秒退、exit 0 假成功）。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from nlcsplit import geomlib                                            # noqa: E402

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "lit", "s22")
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orca_local", "widen")
ORCA = os.path.expanduser("~/orca6/orca")
KCAL = 627.8509
SYSTEMS = ["甲烷二聚体", "氨二聚体", "苯-水", "苯-甲烷"]
# WIDEN_ONLY 用于单独重跑某个体系；写错名字必须**报错退出**，
# 不能像没有自检的驱动那样悄悄把全部体系再跑一遍。
_only = os.environ.get("WIDEN_ONLY")
if _only:
    picked = [s for s in SYSTEMS if s in [x.strip() for x in _only.split(",")]]
    if not picked:
        raise SystemExit(f"WIDEN_ONLY={_only!r} 未匹配任何体系，可选：{SYSTEMS}")
    SYSTEMS = picked
CARD = "! WB97X-V 6-31G* TightSCF\n%pal nprocs 4 end\n%maxcore 1000\n\n* xyz 0 1\n"

NL_RE = re.compile(r"NL Energy, E\(C,NL\) *: *(-?\d+\.\d+) Eh")
SCNL_RE = re.compile(r"SC\+NL Energy: *(-?\d+\.\d+)")
# ORCA 6.0.1 打的是 "SCF CONVERGED AFTER n CYCLES"，不是 "THE SCF HAS CONVERGED"。
# 上一版判据写错导致 12 份全部误报"收敛=否"，而 NL 值其实取到了 —— 假阴性判据比
# 没有判据更坏：它会把有效结果整批丢掉。两个标记都要命中才算数。
CONV_RE = re.compile(r"SCF CONVERGED AFTER\s+(\d+)\s+CYCLES")
NORM_RE = re.compile(r"ORCA TERMINATED NORMALLY")


def write_deck(path, atoms, idxs):
    body = "".join(f"{sym} {x:14.10f} {y:14.10f} {z:14.10f}\n"
                   for k, (sym, (x, y, z)) in enumerate(atoms) if k in idxs)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(CARD + body + "*\n")


def run(tag, inp):
    t0 = time.time()
    with open(inp + ".log", "w") as fh:
        subprocess.run([ORCA, os.path.basename(inp)], cwd=os.path.dirname(inp),
                       stdout=fh, stderr=subprocess.STDOUT, check=False)
    txt = open(inp + ".log", encoding="utf-8", errors="ignore").read()
    nl, scnl = NL_RE.search(txt), SCNL_RE.search(txt)
    # 两个标记都要：SCF 收敛 + ORCA 正常结束。只认能量行会把"没算完但印了半行"当成成功。
    ok = bool(CONV_RE.search(txt)) and bool(NORM_RE.search(txt)) and nl is not None
    print(f"    {tag:26s} NL={nl.group(1) if nl else '—'}  SC+NL={scnl.group(1) if scnl else '—'}"
          f"  收敛={'是' if ok else '否'}  {time.time()-t0:.0f}s", flush=True)
    return {"tag": tag, "nlc_Ha": float(nl.group(1)) if nl else None,
            "scnl_Ha": float(scnl.group(1)) if scnl else None, "converged": ok,
            "wall_s": round(time.time() - t0, 1)}


def main():
    os.makedirs(WORK, exist_ok=True)
    out = {"program": "ORCA 6.0.1 (local Linux build via ~/orca6)", "basis": "6-31G*",
           "keyword_card": CARD.splitlines()[0], "pal": "nprocs 4",
           "quantity": "NL Energy, E(C,NL) (Ha)", "sign": "ΔE_NLC = NL(复合物) − ΣNL(单体@复合物几何, 单体基组)",
           "unit_of_delta": "kcal/mol", "reproduction_gate": {
               "system": "水二聚体", "local_4rank_NL_Ha": "0.084358235133",
               "archived_NL_Ha": "0.084358235133", "identical": True},
           "runs": []}
    for name in SYSTEMS:
        d = os.path.join(WORK, re.sub(r"[^A-Za-z0-9一-鿿-]", "_", name))
        os.makedirs(d, exist_ok=True)
        atoms, frags = geomlib.s22_system(name, DATA)
        print(f"  {name}: {len(atoms)} 原子，片段 {[len(f) for f in frags]}", flush=True)
        write_deck(os.path.join(d, "dimer.inp"), atoms, set(range(len(atoms))))
        r = {"name": name, "natoms": len(atoms), "frags": [list(f) for f in frags]}
        r["dimer"] = run(name + " / 复合物", os.path.join(d, "dimer.inp"))
        subs = []
        for i, f in enumerate(frags):
            write_deck(os.path.join(d, f"mono{i}.inp"), atoms, set(f))
            subs.append(run(f"{name} / 单体{i}", os.path.join(d, f"mono{i}.inp")))
        r["monomers"] = subs
        if r["dimer"]["converged"] and all(s["converged"] for s in subs):
            r["delta_NLC_kcal"] = round((r["dimer"]["nlc_Ha"]
                                        - sum(s["nlc_Ha"] for s in subs)) * KCAL, 4)
        out["runs"].append(r)
        with open(os.path.join(WORK, "orca_widen.json"), "w", encoding="utf-8") as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)     # 每个体系一存，中途断了也不丢
    print("全部完成 →", os.path.join(WORK, "orca_widen.json"), flush=True)


if __name__ == "__main__":
    main()
