"""W0 附件 2 · 用 libxc 自己的符号表把 NLC 参数取出来（不经 PySCF 的任何映射）。

上一版探针（`probe_nlc_parameter_authority.py`）的 (A) 块全灭，根因写进它的输出里了：
PySCF 2.12.1 的 `pyscf.dft.libxc` **没有 `xc_code` 这个名字**，所以我拿不到功能 id。
这一版不借 PySCF：直接从 libxc.so 取 `xc_functional_get_number(const char*)` 把**名字换成 id**，
再用 `xc_nlc_coef(id, &b, &C)` 要参数。两个符号都用 getattr 探，缺哪个就如实记"未取得"。

为什么这件事必须做：现在要判的是"PySCF 给 ωB97M-V / B97M-V 的那组 (b,C) 是不是错"
（证据在 `pyscf/dft/xcfun.py` L314-L316，三行同为同一组）。
"应该是多少"不能由我口述，也不能由文献印象补 —— 本仓规矩：断言要么有原件，要么写"未取得"。

注意 libxc 只给参数、给不出积分值（2026-09-29 的 ctypes 符号审计已定案：
它只导出 `xc_nlc_coef`，`xc_nlc_vxc` 等一律没有），所以 libxc 当不了"能量裁判"，
它在这条线上的角色就是**参数表权威**。
"""
import ctypes
import glob
import os

import pyscf

CANDS = (glob.glob(os.path.join(os.path.dirname(pyscf.__file__), "lib", "**", "libxc.so*"), recursive=True)
         + glob.glob(os.path.expanduser("~/.local/lib/**/libxc.so*"), recursive=True))
NAMES = ["VV10", "RVV10", "RVV10-LC", "LC-VV10", "WB97X-V", "WB97M-V", "B97M-V",
         "PBE-RVV10", "PBE0-RVV10", "SCAN-RVV10", "R2SCAN-RVV10", "REVSCAN-VV10",
         "SCAN-VV10", "REVSCAN-VV10", "B97D-V", "PBE0-VV10"]

print("libxc.so 候选:", CANDS)
lib = None
for p in CANDS:
    try:
        lib = ctypes.CDLL(p)
        print("加载:", p)
        break
    except Exception as e:
        print("加载失败:", p, type(e).__name__, str(e)[:60])
if lib is None:
    raise SystemExit("未取得：一个 libxc.so 也加载不了")

for sym in ("xc_functional_get_number", "xc_func_get_number"):
    fn = getattr(lib, sym, None)
    print("符号 %s: %s" % (sym, "有" if fn else "无"))
get_number = getattr(lib, "xc_functional_get_number", None) or getattr(lib, "xc_func_get_number", None)
nlc_coef = getattr(lib, "xc_nlc_coef", None)
if get_number is None or nlc_coef is None:
    raise SystemExit("未取得：缺 get_number 或 xc_nlc_coef，本条证据拿不到")

get_number.restype = ctypes.c_int
get_number.argtypes = [ctypes.c_char_p]
nlc_coef.restype = None
nlc_coef.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]

print("")
print("%-16s %6s %10s %12s" % ("libxc name", "id", "b", "C"))
print("-" * 48)
seen = set()
for nm in NAMES:
    if nm in seen:
        continue
    seen.add(nm)
    try:
        rid = get_number(nm.encode())
    except Exception as e:
        print("%-16s  call ERR %s" % (nm, str(e)[:40]))
        continue
    if rid < 0:
        print("%-16s %6s  —— libxc 里没这个名字（注意：缺失不等于不存在，可能只是别名）" % (nm, "-1"))
        continue
    b = ctypes.c_double(0.0)
    C = ctypes.c_double(0.0)
    nlc_coef(ctypes.c_int(rid), ctypes.byref(b), ctypes.byref(C))
    print("%-16s %6d %10.4f %12.6f" % (nm, rid, b.value, C.value))

print("")
print("对照（被审对象，来自本项目实测的 PySCF 表，见同目录 probe_nlc_authority 档）：")
print("  pyscf nlc_coeff(wb97xv) / (wb97mv) / (b97mv) 返回同一组；scan_rvv10 返回另一组。")
print("判读：只登记两边各给什么，谁对谁错不由本脚本说。")
