"""出货前的一道校验：`evidence/**` 里哪些档不是合法 UTF-8（裁断第 3 步"UTF-8 输出最终复核"）。

为什么先普查再立规矩：10-15 那次是**撞见**一份表头"既不是 UTF-8 也不是 GBK"的档，
然后就给那一份写说明。但"发生过两回"和"总体有多少、是不是同一个根"是两个问题，
后者决定这是不是一个要进出货流程的系统性缺陷。所以这里全量过一遍，只判不改。

**判据要先分类，计数本身不是判据**（第一版就栽在这里：把 18 份 ORCA 二进制工作档
`job.gbw` / `job.densities` / `job.densitiesinfo` 报成"编码坏了"——它们按格式本来就不是文本）。
所以本脚本报三个数：
  * 非 UTF-8 总数；
  * 其中**按扩展名就该是二进制**的份数（`BINARY_OK`）；
  * 剩下的**真文本缺陷**，并对每份再问一次"那到底是不是混合编码"：
    分别记录 `gbk` / `cp936` / `gb18030` 首次失败的字节偏移。
    `gb18030` 能全解**不等于**文件没问题——它是超集，会把错的也解成看着像汉字。
    真缺陷的形状是"前半 GBK、后半 UTF-8"，即一次归档被两侧打印（本机踩过，见档内注记）。

artifact_kind=machine_census ⇒ 报的是**盘上文件的编码**，不是分子体系的测量值。
"""
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BINARY_OK = (".gbw", ".densities", ".densitiesinfo", ".png", ".jpg", ".pdf",
             ".zip", ".gz", ".npy", ".whl", ".pkl", ".xyz.gz")


def first_fail(raw, enc):
    try:
        raw.decode(enc)
        return None
    except UnicodeDecodeError as e:
        return e.start


def main():
    print("# artifact_kind=machine_census —— 盘上文件编码普查，不是测量结果")
    print("# 生成 %s  根=%s" % (datetime.now(timezone.utc).isoformat(), ROOT))
    n = n_bad = n_bin = 0
    text_bad = []
    for base, dirs, files in os.walk(os.path.join(ROOT, "evidence")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fn in sorted(files):
            p = os.path.join(base, fn)
            n += 1
            raw = open(p, "rb").read()
            off = first_fail(raw, "utf-8")
            if off is None:
                continue
            n_bad += 1
            if fn.lower().endswith(BINARY_OK):
                n_bin += 1
                continue
            rel = os.path.relpath(p, ROOT)
            text_bad.append((rel, len(raw), off,
                             first_fail(raw, "gbk"), first_fail(raw, "cp936"),
                             first_fail(raw, "gb18030")))
    print("# 扫过 %d 份；非 UTF-8 %d 份；其中按扩展名本该是二进制 %d 份（不算缺陷）"
          % (n, n_bad, n_bin))
    print("# 真文本缺陷 %d 份：" % len(text_bad))
    print("   %-64s %7s %9s %9s %9s %9s"
          % ("档", "字节", "utf8断", "gbk断", "cp936断", "gb18030断"))
    for rel, size, u, g, c, g3 in text_bad:
        print("   %-64s %7d %9s %9s %9s %9s"
              % (rel, size, u, g, c, "全解" if g3 is None else g3))
    if text_bad:
        same = len({r[0].split("_")[-1].split(".")[0] for r in text_bad})
        print("# 是否同一个生成器：按档名尾段去重得 %d 组 ⇒ %s"
              % (same, "同一族，先修生成器不是修档" if same == 1 else "不止一族"))
        print("# 形状判读：utf8 与 gbk **都**在某个偏移断掉 ⇒ 混合编码（一次归档被两侧打印），"
              "不是单个字符特殊；gb18030 全解只是超集效应，别当没问题")
    print("\nVERDICT %s —— 真文本缺陷 %d 份 / 全量 %d 份"
          % ("CLEAN" if not text_bad else "NEEDS_FIX", len(text_bad), n))
    return 0 if not text_bad else 1


if __name__ == "__main__":
    sys.exit(main())
