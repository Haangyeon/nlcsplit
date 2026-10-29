"""W0 附件 · 让权威自己说 ωB97M-V / B97M-V 的 NLC 参数应该是多少（不由我口述）。

疑点（已落盘证据 `pyscf/dft/xcfun.py` L314-L316）：B97M_V、WB97M_V 与 WB97X_V 三行
给的是**同一组 (6.0, 0.01)**，而那组是 ωB97X-V 的 VV10 参数；ωB97M-V / B97M-V 的
非局域项按原始定义是 **rVV10**（与同表 L320 `SCAN_RVV10:(15.7,0.0093)` 一族的参数不同）。

"应该是 (b,C)=多少"这句不能由我写，必须来自独立来源。三条证据分开取：
  (C) 被审对象：PySCF 自己的表 + `nlc_coeff()` 实际返回值（原样抄，含行号）
  (B) Psi4 安装树里 grep 常量（它若实现这些泛函，参数一定编码在源码/数据里）—— 纯读文件，安全
  (A) libxc 本尊 `xc_nlc_coef(int, double*, double*)` 直接 ctypes 调 —— 有崩的风险，放最后

2026-10-12 实发教训：上一版在本块前面调了 `xc_version`（以为是返回 `char*`），
libxc 的版本函数签名不是这个，直接把解释器打崩（rc=139 段错误），
把后面本来能取到的证据一起带走了。所以顺序改成"安全的先跑"，且版本探测整段删除。

判读纪律：拿不到就写"未取得"，不许用记忆或文献印象补齐；
字符串缺失 ≠ 功能不存在（本仓 `string-absence-is-not-absence` 那条教训）。
"""
import ctypes
import glob
import os
import pathlib
import re

rows = []


def note(tag, txt):
    line = "%-30s %s" % (tag, txt)
    print(line, flush=True)
    rows.append(line)


print("=" * 78)
print("(C) 被审对象：PySCF 自己的 VV10_XC 表 + nlc_coeff() 实际返回")
import pyscf  # noqa: E402
from pyscf.dft import numint  # noqa: E402

rp = pathlib.Path(os.path.dirname(pyscf.__file__))
t = (rp / "dft" / "xcfun.py").read_text(errors="ignore")
for i, ln in enumerate(t.splitlines()):
    if re.search(r"^\s*'(WB97M_V|WB97X_V|B97M_V|VV10|RVV10|LC_VV10|SCAN_RVV10|SCAN_VV10|REVSCAN_VV10)'\s*:", ln):
        note("pyscf xcfun.py L%d" % (i + 1), ln.strip())
for xc in ["wb97xv", "wb97mv", "b97mv", "scan_rvv10", "vv10"]:
    try:
        note("  nlc_coeff(%s)" % xc, repr(numint.NumInt().nlc_coeff(xc)))
    except Exception as e:
        note("  nlc_coeff(%s)" % xc, "ERR %s: %s" % (type(e).__name__, str(e)[:70]))

print("")
print("=" * 78)
print("(B) Psi4 安装树 grep 常量（纯读文件）")
psi_roots = [r for r in dict.fromkeys(
    glob.glob(os.path.expanduser("~/miniconda3/envs/*/lib/python*/site-packages/psi4"))
    + glob.glob(os.path.expanduser("~/*conda*/envs/*/lib/python*/site-packages/psi4"))
) if os.path.isdir(r)]
note("psi4 包目录", str(psi_roots[:3]) if psi_roots else "无")
pats = {"name WB97M-V": re.compile(r"(?i)wb97m[\s_\-]?v"),
        "name B97M-V": re.compile(r"(?i)\bb97m[\s_\-]?v\b"),
        "const 14.05": re.compile(r"14\.05"),
        "const 0.0359": re.compile(r"0\.0359"),
        "const 15.7": re.compile(r"\b15\.7\b"),
        "name rvv10": re.compile(r"(?i)rvv10")}
if psi_roots:
    exts = (".py", ".cpp", ".h", ".hpp", ".txt", ".json", ".dat", ".in", ".yaml", ".yml")
    hits = {k: [] for k in pats}
    scanned = 0
    for root in psi_roots:
        for f in pathlib.Path(root).rglob("*"):
            if not f.is_file() or f.suffix not in exts:
                continue
            if f.stat().st_size > 4_000_000:
                continue
            scanned += 1
            try:
                txt = f.read_text(errors="ignore")
            except Exception:
                continue
            lines = txt.splitlines()
            for k, pat in pats.items():
                if len(hits[k]) >= 3:
                    continue
                for m in pat.finditer(txt):
                    ln = txt[:m.start()].count("\n")
                    seg = lines[ln].strip()[:110] if ln < len(lines) else ""
                    hits[k].append("%s:%d  %s" % (f.name, ln + 1, seg))
                    break
    note("扫描文件数", str(scanned))
    for k, v in hits.items():
        if v:
            for one in v[:3]:
                note("psi4 命中[%s]" % k, one)
        else:
            note("psi4 命中[%s]" % k, "无 —— 注意：字符串缺失不等于功能不存在")

print("")
print("=" * 78)
print("(A) libxc 本尊 xc_nlc_coef —— 放最后调，签名风险最大")
libxc_paths = glob.glob(os.path.join(os.path.dirname(pyscf.__file__), "lib", "**", "libxc.so*"), recursive=True)
libxc_paths += glob.glob(os.path.expanduser("~/.local/lib/**/libxc.so*"), recursive=True)
note("libxc.so 候选", str(len(libxc_paths)))
fn = None
for pth in libxc_paths:
    try:
        lib = ctypes.CDLL(pth)
        fn = getattr(lib, "xc_nlc_coef", None)
        if fn:
            note("用这份 libxc", pth)
            break
    except Exception:
        continue
if fn is None:
    note("(A) 结论", "未取得：调不到 xc_nlc_coef 符号")
else:
    fn.restype = None
    fn.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
    names = ["VV10", "RVV10", "RVV10-LC", "WB97X-V", "WB97M-V", "B97M-V",
             "PBE-RVV10", "PBE0-RVV10", "SCAN-RVV10", "REVSCAN-VV10"]
    try:
        from pyscf.dft import libxc as pl
    except Exception as e:
        pl = None
        note("(A) 结论", "拿不到 id 映射: %s" % str(e)[:60])
    if pl is not None:
        for nm in names:
            try:
                rid = pl.xc_code(nm)
            except Exception as e:
                note("  libxc id(%s)" % nm, "ERR %s" % str(e)[:50])
                continue
            b = ctypes.c_double(0.0)
            C = ctypes.c_double(0.0)
            try:
                fn(ctypes.c_int(rid), ctypes.byref(b), ctypes.byref(C))
                note("  libxc xc_nlc_coef(%s)" % nm, "id=%d  b=%.4f  C=%.6f" % (rid, b.value, C.value))
            except Exception as e:
                note("  libxc xc_nlc_coef(%s)" % nm, "call ERR %s" % str(e)[:50])
        note("(A) 状态", "上面每个名字一行要么给数要么给 ERR；崩了就说明后面的没跑到")

print("")
print("=" * 78)
print("判读纪律：本脚本只登记权威给不给得出 (b,C)，不下结论。")
