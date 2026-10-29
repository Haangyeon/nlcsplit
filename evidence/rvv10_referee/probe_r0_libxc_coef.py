"""R0 · 用功能号向 libxc 7.1.2 要 VV10 / rVV10 的参数表（每个 id 一个子进程）。

为什么要子进程隔离：上一版探针在 ctypes 调用里**段错误**（rc=139），把后面本来能取到的
证据一起带走了（原件 `20261012T041942Z_probe_nlc_authority.out` 末行 `# exit=139`）。
本脚本每个 id 单独一个进程，崩了就记"崩"，不影响其余 id —— 这是"取证通路本身不能是单点故障"。

已实测到的前提（同目录 `r0` 档）：libxc 7.1.2 只导出 `xc_nlc_coef`，
`xc_nlc_vxc`/`xc_nld_vxc`/`xc_vdwnl_kernel`/`xc_setup_kernel`/`xc_run` 一律没有
⇒ libxc 给不出积分值，当不了裁判；但它**是功能号与参数的权威表**，
且 `xc_funcs.h` 把 SCAN-VV10(584)/SCAN-RVV10(292)、SCANL-VV10(704)/SCANL-RVV10(703)
列为**不同功能号** ⇒ rVV10 不是"只换参数的 VV10"。

本脚本要的就是这句话的参数证据：每个 id 的 (b, C)，以及 `xc_functional_get_number`
能不能用名字反查到 id（上一版全返回 -1 是因为我用的名字不对，不是符号坏了）。
"""
import ctypes
import subprocess
import sys

LIB = "/mnt/e/conda_envs/xcprobe/lib/libxc.so.15"
HDR = "/mnt/e/conda_envs/xcprobe/include/xc_funcs.h"

# 功能号直接抄自本机 libxc 7.1.2 的 xc_funcs.h（下面会逐条回读原文行自证）
IDS = [(255, "XC_GGA_XC_VV10"), (292, "XC_MGGA_C_SCAN_RVV10"), (469, "XC_HYB_GGA_XC_LC_VV10"),
       (584, "XC_MGGA_C_SCAN_VV10"), (585, "XC_MGGA_C_REVSCAN_VV10"),
       (652, "XC_MGGA_XC_VCML_RVV10"), (703, "XC_MGGA_C_SCANL_RVV10"), (704, "XC_MGGA_C_SCANL_VV10")]

CHILD = r'''
import ctypes, sys
lib = ctypes.CDLL("/mnt/e/conda_envs/xcprobe/lib/libxc.so.15")
i = int(sys.argv[1]); b = ctypes.c_double(0.0); C = ctypes.c_double(0.0)
f = lib.xc_nlc_coef
f.restype = ctypes.c_int
f.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)]
rc = f(ctypes.c_int(i), ctypes.byref(b), ctypes.byref(C))
print("rc=%d b=%.4f C=%.6f" % (rc, b.value, C.value))
'''

lines = []


def say(s):
    print(s, flush=True)
    lines.append(str(s))


say("# R0 · libxc 7.1.2 的 VV10 / rVV10 参数表（逐 id 子进程隔离）")
say("# 库：%s" % LIB)

ver = ctypes.CDLL(LIB)
try:
    ver.xc_version.restype = ctypes.CFUNCTYPE(ctypes.c_char_p)
except Exception:
    pass

txt = open(HDR, errors="ignore").read().splitlines()
say("")
say("## 功能号自证（原文行，来自本机 xc_funcs.h）")
for num, name in IDS:
    raw = [l.strip() for l in txt if ("#define  %s " % name) in l or ("#define %s " % name) in l]
    say("   %-28s %s" % (name, raw[0][:105] if raw else "!! 头文件里找不到该行"))

say("")
say("## 逐 id 调 xc_nlc_coef（崩了记崩，不影响其它 id）")
say("   %-4s %-28s %s" % ("id", "name", "结果"))
for num, name in IDS:
    try:
        p = subprocess.run([sys.executable, "-c", CHILD, str(num)],
                           capture_output=True, text=True, timeout=120)
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip().splitlines()
        if p.returncode != 0:
            say("   %-4d %-28s 进程 rc=%d %s" % (num, name, p.returncode,
                                                 err[-1][:70] if err else ""))
        else:
            say("   %-4d %-28s %s" % (num, name, out))
    except Exception as e:
        say("   %-4d %-28s EXC %s: %s" % (num, name, type(e).__name__, str(e)[:60]))

say("")
say("## 名字反查 id（上一版 -1 的真相：我用的是别名而不是 libxc 的规范名）")
gnum = ctypes.CDLL(LIB).xc_functional_get_number
gnum.restype = ctypes.c_int
gnum.argtypes = [ctypes.c_char_p]
for probe in ["VV10", "RVV10", "MGGA_C_SCAN_RVV10", "XC_MGGA_C_SCAN_RVV10",
              "MGGA_C_SCAN_VV10", "MGGA_XC_WB97M_V", "MGGA_XC_B97M_V", "MGGA_XC_WB97X_V"]:
    say("   %-26s -> id %d" % (probe, gnum(probe.encode())))

say("")
say("判读：本脚本只登记 libxc 给什么，不下结论。")
say("若 VV10 一列与 rVV10 一列给出**不同的 (b,C)**，则'PySCF 把 rVV10 参数塞进 VV10 核形'")
say("这件事至少是**值得查的实现不一致**；但要写进正文仍需能算积分的裁判（libxc 已证不能）。")

import datetime as dt
stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "%s_r0_libxc_coef_table.out" % stamp)
with open(p, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n# exit=0 at %s\n" % dt.datetime.now(dt.timezone.utc).isoformat())
print("OUT=%s" % p)
