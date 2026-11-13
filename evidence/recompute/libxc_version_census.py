"""本机每一份 libxc 的版本与 NLC 符号普查（把 `main.md:64` 那句话绑到文件上）。

背景（一句话）：正文说"本机两份 libxc（conda-forge 5.2.3 与 PySCF 自带 7.0.0）只导出
`xc_nlc_coef`，给不出积分值"。外部裁断把"libxc 版本冲突（7.1.2、5.2.3、7.0.0）的来源与实际
运行环境核对"列为仍缺的核验——三个号并存是不是矛盾，取决于每个号绑的是哪一份文件。

本脚本不读文档，直接点名盘上每一份 `libxc.so`，各报三样：
  * `conda-meta` / `xc_version_string()` 自报的确切版本；
  * `nm -D` 在探测的 6 个非局域入口里实际导出的符号；
  * soname（`.9` / `.12` / `.15` / 裸名）作交叉核对。

两条从上一版踩出来的坑，写在这里免得再踩：
  1. **取版本要用 `xc_version_string()`**，不是 `xc_version()`。用错符号名时四份子进程全 `rc=-11`
     （SIGSEGV）且**一行输出都没有**——崩溃把已算好的数一起吃掉了，所以这里每份库单独起子进程，
     "这份从本 python 加载就崩"才成一条证据而不是整次普查消失。
  2. **范围要铺两个 conda 根**。只扫 `/mnt/e/conda_envs/*` 会**找不到 5.2.3**——它在
     `~/miniconda3/envs/psi4env/`，那是 2026-09-29 归档（`20260929T110830Z_libxc_referee.out:45`）
     点过名的位置。工具没报错不等于不存在。

artifact_kind=machine_census ⇒ 报的是**本机环境**，不是分子体系的测量值；
版本字符串若要进正文，须与本档同现（`software.md` / §4 那句关于 libxc 的论断的出处就是这里）。
"""
import glob
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

CHILD = r'''
import ctypes, json, sys
p = sys.argv[1]
out = {"path": p, "version": None, "version_via": None, "syms": [], "err": None}
try:
    lib = ctypes.CDLL(p)
except Exception as e:
    out["err"] = "CDLL: %s: %s" % (type(e).__name__, e)
    print(json.dumps(out)); raise SystemExit(0)
for name in ("xc_version_string", "xc_version"):
    try:
        f = getattr(lib, name)
        f.restype = ctypes.c_char_p
        out["version"] = f().decode()
        out["version_via"] = name
        break
    except AttributeError:
        continue
    except Exception as e:
        out["err"] = "%s: %s" % (name, e)
for s in ("xc_nlc_coef", "xc_nlc_vxc", "xc_nld_vxc", "xc_vdwnl_kernel",
          "xc_setup_kernel", "xc_run"):
    try:
        getattr(lib, s)
        out["syms"].append(s)
    except AttributeError:
        pass
print(json.dumps(out))
'''

NLC_PROBE = ("xc_nlc_coef", "xc_nlc_vxc", "xc_nld_vxc", "xc_vdwnl_kernel",
             "xc_setup_kernel", "xc_run")
ROOTS = ("/mnt/e/conda_envs", os.path.expanduser("~/miniconda3"))
PYSCF = os.path.expanduser(
    "~/.local/lib/python3.10/site-packages/pyscf/lib/deps/lib/libxc.so")


def candidates():
    out = []
    for root in ROOTS:
        out += sorted(glob.glob(os.path.join(root, "envs", "*", "lib", "libxc.so")))
        out += sorted(glob.glob(os.path.join(root, "*", "lib", "libxc.so")))
    out.append(PYSCF)
    return [c for c in dict.fromkeys(out) if os.path.exists(c)]


def conda_meta_version(path):
    """从 conda-meta 里读包版本——不加载 so，所以不受符号/崩溃问题影响。"""
    env = os.path.dirname(os.path.dirname(path))          # <env>/lib/libxc.so → <env>
    hits = sorted(glob.glob(os.path.join(env, "conda-meta", "libxc-*.json")))
    for h in hits:
        try:
            return json.load(open(h)).get("version"), os.path.basename(h)
        except Exception:
            continue
    return None, None


def main():
    print("# artifact_kind=machine_census —— 本机环境普查，不是分子体系的测量值")
    print("# 生成 %s  host=%s" % (datetime.now(timezone.utc).isoformat(),
                                 subprocess.run(["hostname"], capture_output=True,
                                                text=True).stdout.strip()))
    print("# git HEAD %s" % subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                                           capture_output=True, text=True).stdout.strip())
    cands = candidates()
    print("# 候选 %d 份（两个 conda 根 + PySCF 自带）：%s" % (len(cands), ", ".join(cands)))
    if not cands:
        print("!! 一份都没找到——这是普查失败，不是'本机没有 libxc'的证据；先查 glob 范围")
        return 2

    rows = []
    for p in cands:
        sonames = sorted(os.path.basename(x) for x in glob.glob(p + ".*"))
        nm = subprocess.run(["bash", "-lc",
                             "nm -D '%s' 2>/dev/null | grep -oE '%s' | sort -u"
                             % (p, "|".join(NLC_PROBE))],
                            capture_output=True, text=True).stdout.split()
        c = subprocess.run([sys.executable, "-c", CHILD, p], capture_output=True, text=True)
        rec = {"path": p, "sonames": sonames, "nm": nm, "child_rc": c.returncode}
        if c.returncode == 0 and c.stdout.strip():
            rec.update(json.loads(c.stdout.strip().splitlines()[-1]))
        else:
            rec["version"] = None
            rec["note"] = "子进程 rc=%s %s" % (c.returncode,
                                            (c.stderr.strip()[-160:] or "无 stderr"))
        cmv, cmf = conda_meta_version(p)
        rec["conda_meta"] = cmv
        rows.append(rec)
        print("\n== %s" % p)
        print("   soname      : %s" % (sonames or "裸名"))
        print("   nm -D 非局域符号: %s" % (rec["nm"] or "探测的 6 个全无"))
        print("   自报版本    : %s（经 %s）   conda-meta 包版本: %s"
              % (rec.get("version"), rec.get("version_via"), rec.get("conda_meta")))
        print("   ctypes 取得到 : %s%s"
              % (", ".join(rec.get("syms") or []) or "无",
                 "   err=" + rec["err"] if rec.get("err") else ""))
        if rec.get("note"):
            print("   %s" % rec["note"])

    print("\n# 判读（只对盘上证据负责）：")
    only_coef, ver_conflict = [], []
    for r in rows:
        exported = set(r["nm"]) | set(r.get("syms") or [])
        if exported == {"xc_nlc_coef"}:
            only_coef.append(r["path"])
        else:
            only_coef.append("!! " + r["path"] + " 导出 " + ",".join(sorted(exported)))
        if r.get("version") and r.get("conda_meta") and r["version"] != r["conda_meta"]:
            ver_conflict.append("%s 自报 %s ≠ conda-meta %s" % (r["path"], r["version"],
                                                                r["conda_meta"]))
    for line in only_coef:
        print("   %s" % line)
    print("# 版本自报与 conda-meta 不一致的份数：%d%s"
          % (len(ver_conflict), ("  " + "; ".join(ver_conflict)) if ver_conflict else ""))
    vers = sorted({r["version"] for r in rows if r.get("version")})
    print("# 本机 libxc 构建共 %d 份，去重版本 %d 个：%s" % (len(rows), len(vers), ", ".join(vers)))
    print("# 正文 `main.md:64` 现写'两份（conda-forge 5.2.3 与 PySCF 自带 7.0.0）'——"
          "份数与版本清单以本档为准，措辞若要改属落笔口径事项，须作者点头")
    return 0


if __name__ == "__main__":
    sys.exit(main())
