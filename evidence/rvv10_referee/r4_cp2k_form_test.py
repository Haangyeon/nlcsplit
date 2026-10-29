"""R4 · CP2K 三臂形式对照：把"PySCF 的 SCAN_RVV10 是不是真 rVV10"变成一次可复查的测量。

设计（单变量，三臂只差核形与参数两件事）：
  A 臂  CP2K + VV10 核形 + (b,C)=(15.7,0.0093)   ← 这就是 PySCF 的 `scan_rvv10` 的配置
  B 臂  CP2K + rVV10 核形 + (b,C)=(15.7,0.0093)   ← 发表意义上的 SCAN-RVV10
  C 臂  CP2K + VV10 核形 + (b,C)=(6.0,0.01)       ← 已知能与 PySCF/ORCA 对上的 sanity 臂
半局域部分三臂**全部用 SCAN**，基组/截断/收敛阈一致。

判读（写死，不许事后挑档）：
  1) 先要 C 臂与 PySCF `wb97xv` 的 ΔE_NLC 对上（量级同 W0 的 0.0004–0.0007，
     或至少与截断/PAW 差异自洽）——**这条不过，整份对照作废**，因为说明我 CP2K 口径搭错了。
     注意 CP2K 用 GTH 赝势替芯，PySCF 是全电子 ⇒ C 臂本来就不会逐位对上，
     所以这条只能当"量级门"，不能当逐位门；写进正文时这个差异必须交代。
  2) A 与 B 的差 = **纯形式差**。若 |ΔE_NLC(A) − ΔE_NLC(B)| ≫ 数值噪声（三臂同设置，
     噪声由 A 与 A 重跑的差给），则"PySCF 的 SCAN_RVV10 走的是 VV10 核形、不是 rVV10"
     得到实算支持；若两者在噪声内相同 ⇒ 这条疑点再次证伪，如实写证伪。
  3) 任何"某程序实现错了"的句子仍需：原始定义式逐式核（R1 双源门，式 (6)(7) 的第二源）
     + 第二家独立码同向。**本脚本只出数，不出结论。**

已知风险（跑之前就知道，省得事后找理由）：
  - CP2K 的 `&NON_LOCAL FUNCTIONAL` 到底吃哪些 PARAM_ 编号、rVV10 名字怎么拼，
    我按手册与常见写法先试，**报错就照它吐的关键字清单改**，不猜第二遍。
  - 分子体系在 CP2K 里要周期性箱 ⇒ 用大箱 + 单 k 点；箱大小会进截断误差，
    所以三臂必须同箱同截断，只换核形/参数。
"""
import datetime as _dt
import os
import subprocess
import sys

# 2026-10-12 实测：conda-forge 现役 cp2k 2026.2/2026.1 要 GLIBC_2.38，本机 Ubuntu 22.04 是 2.35 ⇒ 起不来。
# 可用的是 **cp2k=2024.2 的 openblas_nompi 构建**（libxsmm 1.17），而且它给的二进制名是
# **cp2k.ssmp**，不是 cp2k.popt —— 我第一版按 .popt 测，把一次成功的安装误判成失败。
ENV = "/mnt/e/conda_envs/cp2k24"
CP2K = os.path.join(ENV, "bin", "cp2k.ssmp")
REPO = "/mnt/e/Project/GAMESS"
OUTDIR = os.path.join(REPO, "evidence", "rvv10_referee", "cp2k_r4")
S22 = os.path.join(REPO, "scratch", "lit", "s22")
SYSTEMS = [("水二聚体", "S22_02.xyz"), ("甲烷二聚体", "S22_08.xyz")]
ARMS = [("A_vv10kernel_rvv10pars", "VV10", 15.7, 0.0093),
        ("B_rvv10kernel_rvv10pars", "rVV10", 15.7, 0.0093),
        ("C_vv10kernel_vv10pars", "VV10", 6.0, 0.01)]
CUTOFF = 300.0          # Ry；分子体系用不到 400 Ry 的平面波等价截断，三臂一致即可
RHO_CUT = 12            # CP2K 的 rho 截断阶数（默认 12）
BOX = 16.0              # Å 立方箱：25 Å 会把网格放大到 9M 点而纯浪费，16 Å 足够隔离镜像
SEMILLOCAL = "SCAN"

lines = []


def say(s):
    print(s, flush=True)
    lines.append(str(s))


def find_data():
    for cand in (os.path.join(ENV, "share", "cp2k", "data"),
                 os.path.join(ENV, "share", "cp2k")):
        if os.path.isdir(cand):
            names = os.listdir(cand)
            basis = next((n for n in names if n.startswith("BASIS_MOLOPT")), None)
            pot = next((n for n in names if n.startswith("GTH_POTENTIALS")), None)
            if basis and pot:
                return cand, basis, pot
    return None, None, None


def xyz_to_cp2k(path):
    txt = open(path, encoding="utf-8", errors="ignore").read().splitlines()
    nat = int(txt[0].split()[0])
    out = []
    z2s = {1: "H", 6: "C", 7: "N", 8: "O"}
    for l in txt[2:2 + nat]:
        t = l.split()
        sym = z2s[int(t[0])] if t[0].isdigit() else t[0].capitalize()
        out.append("%s %s %s %s" % (sym, t[1], t[2], t[3]))
    return out


def make_inp(tag, functional, b, C, atoms, datadir, basis, pot):
    d = os.path.join(OUTDIR, tag)
    os.makedirs(d, exist_ok=True)
    xyz = os.path.join(d, "mol.xyz")
    with open(xyz, "w", encoding="utf-8", newline="\n") as f:
        f.write("%d\n%s (GMTKN55 S22 official, W0/R4)\n" % (len(atoms), tag))
        for a in atoms:
            f.write(a + "\n")
    inp = os.path.join(d, "job.inp")
    with open(inp, "w", encoding="utf-8", newline="\n") as f:
        f.write("&GLOBAL\n  PROJECT %s\n  RUN_TYPE ENERGY\n  PRINT_LEVEL MEDIUM\n&END GLOBAL\n\n" % tag)
        f.write("&FORCE_EVAL\n  METHOD QUICKSTEP\n  &SUBSYS\n    &COORD\n      &READ_COORDS XYZFILE mol.xyz\n    &END COORD\n")
        f.write("    &CELL\n      ABC [Angstrom] %.3f %.3f %.3f\n      PERIODIC NONE\n    &END CELL\n" % (BOX, BOX, BOX))
        f.write("  &END SUBSYS\n  &DFT\n")
        # 写绝对路径：CP2K 只在 cwd 或 $DATA_DIR 里找裸文件名，工作目录里没有这些数据文件
        f.write("    BASIS_SET_FILE_NAME %s\n    POTENTIAL_FILE_NAME %s\n"
                % (os.path.join(datadir, basis), os.path.join(datadir, pot)))
        f.write("    CUTOFF %.0f\n    &SCF\n      MAX_ITER 80\n      EPS_SCF 1.0E-8\n      &OUTER_SCF\n        MAX_ITER 20\n        EPS_SCF 1.0E-8\n      &END OUTER_SCF\n    &END SCF\n" % CUTOFF)
        f.write("    &XC\n      &XC_FUNCTIONAL %s\n      &END XC_FUNCTIONAL\n" % SEMILLOCAL)
        f.write("      &VDW_POTENTIAL\n        &NON_LOCAL\n          FUNCTIONAL %s\n          PARAM_1 %.4f\n          PARAM_2 %.6f\n          RHO_CUT %d\n          CUTOFF %.0f\n        &END NON_LOCAL\n      &END VDW_POTENTIAL\n" % (functional, b, C, RHO_CUT, CUTOFF))
        f.write("    &END XC\n  &END DFT\n&END FORCE_EVAL\n")
    return inp, d


def run(inp, workdir):
    env = dict(os.environ)
    env["LD_LIBRARY_PATH"] = os.path.join(ENV, "lib") + os.pathsep + env.get("LD_LIBRARY_PATH", "")
    # 工作目录是复用的：先清掉上一跑的 *.out / *.out.rc，
    # 否则旧档会混进新档，等于伪造出处（本仓"工件没重扫就被当成新证据"的前账）
    for fn in os.listdir(workdir):
        if fn.endswith(".out") or fn.endswith(".out.rc") or fn.endswith(".rep"):
            os.remove(os.path.join(workdir, fn))
    p = subprocess.run([CP2K, "-i", inp], cwd=workdir, capture_output=True, text=True, timeout=5400)
    out = os.path.join(workdir, "cp2k.out")
    with open(out, "w", encoding="utf-8") as f:
        # CP2K 把程序输出写到 <PROJECT>.out 文件里，stdout 基本是空的
        # （第一版就是因为只捕 stdout 而什么都没抓到，误判成"输入被拒"）
        for fn in sorted(os.listdir(workdir)):
            if fn.endswith(".out") and fn != "cp2k.out":
                f.write("\n===PROJECT FILE %s===\n" % fn)
                f.write(open(os.path.join(workdir, fn), encoding="utf-8",
                             errors="ignore").read())
        f.write("\n===STDERR===\n")
        f.write(p.stderr or "")
    with open(out + ".rc", "w", encoding="utf-8") as f:
        f.write("%d\n" % p.returncode)
    return p.returncode, out


def grab(out, keys):
    got = {}
    for l in open(out, encoding="utf-8", errors="ignore"):
        for k in keys:
            if k.lower() in l.lower() and k not in got:
                got[k] = l.strip()[:160]
    return got


def main():
    say("# R4 · CP2K 三臂形式对照  半局域=%s  CUTOFF=%.0f Ry  箱=%.1f A  单 k 点" % (SEMILLOCAL, CUTOFF, BOX))
    say("# 生成 %s" % _dt.datetime.now(_dt.timezone.utc).isoformat())
    if not os.path.exists(CP2K):
        say("!! CP2K 不存在：%s —— 先确认 conda 安装已完成（libcp2k.so 是否已链接）" % CP2K)
        return 3
    datadir, basis, pot = find_data()
    if not datadir:
        say("!! 找不到 BASIS_MOLOPT / GTH_POTENTIALS，share/cp2k/data 里有什么：")
        for c in ("share/cp2k", "share"):
            d = os.path.join(ENV, c)
            if os.path.isdir(d):
                say("   %s -> %s" % (d, sorted(os.listdir(d))[:12]))
        return 4
    say("# 数据目录 %s  basis=%s  pot=%s" % (datadir, basis, pot))
    os.makedirs(OUTDIR, exist_ok=True)

    for sname, sfile in SYSTEMS:
        atoms = xyz_to_cp2k(os.path.join(S22, sfile))
        say("")
        say("## %s (%s)  natoms=%d" % (sname, sfile, len(atoms)))
        for tag, functional, b, C in ARMS:
            inp, wd = make_inp("%s__%s" % (tag, sfile[:-4]), functional, b, C, atoms, datadir, basis, pot)
            say("   [%s] 核形=%s b=%.4f C=%.6f" % (tag, functional, b, C))
            try:
                rc, out = run(inp, wd)
            except Exception as e:
                say("      跑失败：%s: %s" % (type(e).__name__, str(e)[:120]))
                continue
            say("      rc=%d  out=%s" % (rc, os.path.basename(out)))
            g = grab(out, ["SCF run converged", "non-local correlation energy",
                           "Total ENERGY", "PSI DENSITY CONVERGED", "subspace spin",
                           "Cannot find keyword", "has no member", "Unrecognized",
                           "Error while reading", "The following error occurred"])
            for k, v in g.items():
                say("        %-28s %s" % (k, v))
            if not g:
                say("        （没抓到任何关键行 —— 说明输入语法就被拒了，看 cp2k.out 头部）")
    say("")
    say("判读纪律：本脚本只登记三臂各给出什么，不下结论；")
    say("C 臂与 PySCF 对不上（量级）就整份作废，A/B 之差才有意义。")
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "%s_r4_cp2k_three_arms.out" % stamp)
    with open(p, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("OUT=%s" % p)


if __name__ == "__main__":
    sys.exit(main())
