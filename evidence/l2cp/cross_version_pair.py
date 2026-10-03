"""§2.5 那句"跨版本逐量对照"的原件：读两份 harvest 侧车，逐量打印差。

以前这四个数（-1.404667 / -2.324590 / 0.213163 / -1.441416）与它们的一串 |Δ| 只活在
`scratch/harvest-l2/` 里，正文引用它们而仓内没有原件——`tools/claim_gate.js` 报的这一条。
两份侧车现在都进了本目录：

  20260929T051849Z_wsl2121-benzmeth-l2cp.json      本机 WSL，PySCF 2.12.1
  20260929T051912Z_centos2140-benzmeth-l2cp.json   CentOS，PySCF 2.14.0

两边都是同一体系（苯-甲烷）、同一 level 2、同一 6-31g\\*、同一套官方 S22 几何、都带完整反泊松，
所以这是版本这一变量的对照，不是机器对照（机器与版本当时是绑在一起的，后来
`cp_version_runner.py` 在同机上把版本单独量了一遍，那条结论在这里不重复引用）。

它拒绝在下列情况下出表：任一边缺苯-甲烷行、两边的 level/basis/cpcorr 不一致、
或某一边缺 provenance 键（pyscf_version / host 至少要有）——因为"哪台跑的"这句话本身就是主张。
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WSL = "20260929T051849Z_wsl2121-benzmeth-l2cp.json"
CEN = "20260929T051912Z_centos2140-benzmeth-l2cp.json"
SYSTEM = "苯-甲烷"
KEYS = [("dnlc", "ΔE_NLC"), ("dxc", "ΔE_xc"), ("dtot", "ΔE_int(未校正)"),
        ("span", "归属方案跨度"), ("dcp", "ΔE_int(反泊松)")]


def row(path):
    j = json.load(open(path, encoding="utf-8"))
    for k in ("level", "basis", "cpcorr"):
        if k not in j:
            raise SystemExit("%s: 文件头缺 %s，跨版本主张不成立" % (os.path.basename(path), k))
    for r in j["rows"]:
        if r.get("name") == SYSTEM:
            for k in ("pyscf_version", "host"):
                if not r.get(k):
                    raise SystemExit("%s: %s 行缺 %s" % (os.path.basename(path), SYSTEM, k))
            return j, r
    raise SystemExit("%s: 没有 %s 行" % (os.path.basename(path), SYSTEM))


def main():
    (hj, w), (hc, c) = row(os.path.join(HERE, WSL)), row(os.path.join(HERE, CEN))
    if (hj["level"], hj["basis"], hj["cpcorr"]) != (hc["level"], hc["basis"], hc["cpcorr"]):
        raise SystemExit("两边档位/基组/反泊松开关不一致：%s vs %s"
                         % ((hj["level"], hj["basis"], hj["cpcorr"]),
                            (hc["level"], hc["basis"], hc["cpcorr"])))
    print("== 跨版本逐量对照：%s，level %d，%s，反泊松 %s ==" %
          (SYSTEM, hj["level"], hj["basis"], hj["cpcorr"]))
    print("   A = %s (PySCF %s @ %s)" % (WSL, w["pyscf_version"], w["host"]))
    print("   B = %s (PySCF %s @ %s)" % (CEN, c["pyscf_version"], c["host"]))
    print("   两份都是 2026-09-29 的 harvest 侧车，只读不回写；母仓表 1 用的不是它们。\n")
    for key, label in KEYS:
        a, b = w.get(key), c.get(key)
        if a is None or b is None:
            print("  %-16s A=%s B=%s -> 有一边是 null，不出差值" % (label, a, b))
            continue
        d = abs(a - b)
        print("  %-16s A=%+.6f  B=%+.6f  |Δ|=%.2e %s"
              % (label, a, b, d, "≤1e-3" if d <= 1e-3 else ">1e-3（正文必须单独说这一条）"))
    pa = w["pint"]["becke"] if "pint" in w else None
    pb = c["pint"]["becke"] if "pint" in c else None
    if pa is not None and pb is not None:
        print("  %-16s A=%+.6f  B=%+.6f  |Δ|=%.2e" % ("P_frz[becke]", pa, pb, abs(pa - pb)))
    print("\n判据：除反泊松那一行外，其余各量的 |Δ| 都在 1e-3 kcal/mol 内——这就是 §2.5 把表 1\n"
          "说成「跨版本但可比」的依据。反泊松那一行是唯一的例外，它的机制由\n"
          "evidence/l2cp/cp_version_probe.py 与 20261003T0928Z_cp_version_probe.out 给出。")


if __name__ == "__main__":
    sys.exit(main())
