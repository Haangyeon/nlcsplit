"""交叉认证守卫的自测：正例 / 六种负控，全部喂**真实档的临时副本**。

为什么要有这个文件（2026-10-18 外部裁断第 1 步的收尾件）：
`summarize_s22_full.py` 原来有六条**静默缩面**路径（旧档 glob 落空、六列不齐、
抬头读不出名、`if old:` 整块跳过、名字不在集合、列级 continue）。补了断言之后，
断言本身如果没被证伪过，就又是一条"无法失败的守卫"。所以这里逐条打掉它。

三条纪律（都来自本仓踩过的坑，不是通用建议）：
1. **不抄代码**：从出货文件 `import` 真实模块（上一轮栽在把待测代码抄进字符串常量，
   转义毁掉正则，于是三个负控"全部通过"其实一行被测代码都没跑）。
2. **不用合成数字当结果**：夹具是 `evidence/common_grid/` 真实原件的逐份副本，
   负控只做**删/改行或截成残件**的最小扰动；产物一律自报 `artifact_kind=selftest`。
3. **"负控通过"除退出码外还要断言产物里出现了预期的那句话** ——
   空文件与"确实拒绝"在退出码上长得一样（本仓第 4 次同形失效）。

用法（WSL，pyscf 只在这边）：
    bash evidence/common_grid/run_selftest_certification_gate.sh
"""
import glob
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REAL = HERE
SRC = os.path.join(HERE, "summarize_s22_full.py")
# 夹具复制到 /tmp 之后，被测代码里 `dirname(dirname(HERE))` 会推到一个没有 nlcsplit 的目录
# （首跑就死在这里，ModuleNotFoundError）。所以把**真实仓根**挂进 sys.path：
# nlcsplit 必须来自真仓，不能让夹具自带一份包内代码 —— 那样测的就不是随包那份实现了。
REPO = os.path.dirname(os.path.dirname(REAL))
sys.path.insert(0, REPO)


def load_real_module():
    """从出货文件本身加载，不复制任何逻辑。"""
    spec = importlib.util.spec_from_file_location("judge_under_test", SRC)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def sandbox():
    """把 evidence/common_grid 整目录逐份复制进临时盘，让所有 glob 行为与真目录一致。"""
    d = tempfile.mkdtemp(prefix="certgate_")
    dst = os.path.join(d, "common_grid")
    shutil.copytree(REAL, dst)
    return d, dst


def run(m, here):
    m.HERE = here
    m.SKIPPED = []
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = m.main()
    return rc, buf.getvalue()


def edit(path, drop_regex=None, sub=None, truncate=False):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    if truncate:
        open(path, "w").write(txt.splitlines()[0] + "\n")
        return
    if drop_regex:
        keep = [l for l in txt.splitlines() if drop_regex not in l]
        assert len(keep) < len(txt.splitlines()), "扰动没删掉任何一行：夹具失效"
        open(path, "w", encoding="utf-8").write("\n".join(keep) + "\n")
    if sub:
        a, b = sub
        assert a in txt, "扰动没命中目标串：夹具失效"
        open(path, "w", encoding="utf-8").write(txt.replace(a, b, 1) + "\n")


def find_old(dst, needle):
    """在**判据实际使用的那条 glob** 里找含 needle 的旧档，且必须唯一命中。

    首跑就栽在这里：当时用宽模式 `hirshfeld_crossfamily_l1_` 匹配，结果扰动打在一份
    非 `_after_unitfix` 的旧副本上，判据根本不读它 ⇒ 负控"没红"，看着像守卫漏了，
    其实是夹具没进判决面。所以这里复用 `summarize_s22_full` 的 glob，并断言唯一命中。
    """
    import fnmatch
    pat = "2026*_hirshfeld_crossfamily_l1_*_after_unitfix.out"
    hits = []
    for fn in sorted(glob.glob(os.path.join(dst, pat))):
        if not fnmatch.fnmatch(os.path.basename(fn), pat):
            continue
        t = open(fn, encoding="utf-8", errors="ignore").read()
        if needle in t:
            hits.append(fn)
    if len(hits) != 1:
        raise AssertionError("夹具目标不唯一/未命中：needle=%r 命中 %d 份 %s"
                             % (needle, len(hits), [os.path.basename(x) for x in hits]))
    return hits[0]


def main():
    m = load_real_module()
    print("# artifact_kind=selftest —— 守卫自测，不是测量结果，数字不得进任何正文")
    print("# 生成 %s" % datetime.now(timezone.utc).isoformat())
    print("# 被测文件 %s（sha256=%s）" % (os.path.basename(SRC), _sha(SRC)[:16]))
    print("# 宿主时钟 UTC=%s" % datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))

    cases = []

    # ---- 正例（旧形态回归）：真目录的副本，判决必须与线上完全一致（4 列 OVER ⇒ rc=1）
    d, dst = sandbox()
    rc, art = run(m, dst)
    cases.append(("正例=真实副本必须复现既有判决 rc=1 且点到那四格",
                  rc == 1 and "S22_11" in art and "OVER +0.0064" in art and "已认证 8/8 格" in art,
                  rc, art))
    shutil.rmtree(d, ignore_errors=True)

    # ---- 负控 1：旧档 glob 落空 ⇒ 必须 rc=2 并点名"落空"，不许出 VERDICT OK
    d, dst = sandbox()
    for fn in [f for f in os.listdir(dst) if "hirshfeld_crossfamily_l1_" in f]:
        os.remove(os.path.join(dst, fn))
    rc, art = run(m, dst)
    cases.append(("负控1 旧档全空 ⇒ rc=2 且打印 glob 落空",
                  rc == 2 and "glob 落空" in art, rc, art))
    shutil.rmtree(d, ignore_errors=True)

    # ---- 负控 2：某一格少一列（以前 :157 直接 continue，静默丢格）
    d, dst = sandbox()
    p = find_old(dst, "苯二聚体(A)")
    edit(p, drop_regex="家族内 stratmann")
    rc, art = run(m, dst)
    cases.append(("负控2 旧档少一列 ⇒ rc=2 且点名六列不齐/缺列",
                  rc == 2 and ("六列不齐" in art or "缺列" in art), rc, art))
    shutil.rmtree(d, ignore_errors=True)

    # ---- 负控 3：档内自报名被改成声明外的名字（以前按档名反推，会静默失交）
    d, dst = sandbox()
    p = find_old(dst, "氨二聚体")
    edit(p, sub=("== 氨二聚体 ", "== 氦二聚体 "))
    rc, art = run(m, dst)
    cases.append(("负控3 自报名与声明不符 ⇒ rc=2、身份行点名、且已认证数掉到 7/8",
                  rc == 2 and "已认证 7/8 格" in art
                  and ("身份不唯一" in art or "声明与实物不符" in art or "≠ 声明" in art),
                  rc, art))
    shutil.rmtree(d, ignore_errors=True)

    # ---- 负控 4：把声明改小也不许放过（预期必须外部固定，不许跟着实物降）
    d, dst = sandbox()
    keep = m.EXPECT_OVERLAP
    m.EXPECT_OVERLAP = {k: v for k, v in keep.items() if k != "S22_01"}
    rc, art = run(m, dst)
    m.EXPECT_OVERLAP = keep
    cases.append(("负控4 声明里去掉一格 ⇒ 那一格的旧档变成声明外多出的格，必须 rc=2",
                  rc == 2 and "声明与实物不符" in art, rc, art))
    shutil.rmtree(d, ignore_errors=True)

    # ---- 负控 5：旧档是**残件**（截到只剩抬头一行）⇒ 不许当"没有这一格"，也不许当认证
    # 外部裁断点名要这条：目录里那份 605 B 的启动即断档，既不该算第 23 格，也不该算测量失败格，
    # 但必须证明"解析失败"走 rc=2 而不是静默缩面（`edit(truncate=True)` 这个夹具以前定义了却没人用）。
    d, dst = sandbox()
    p = find_old(dst, "水二聚体")
    edit(p, truncate=True)
    rc, art = run(m, dst)
    cases.append(("负控5 旧档截成残件 ⇒ rc=2 且点名那份档六列不齐/计为没测",
                  rc == 2 and os.path.basename(p) in art
                  and ("六列不齐" in art or "读不出" in art) and "计为没测" in art,
                  rc, art))
    shutil.rmtree(d, ignore_errors=True)

    # ---- 负控 6：喂**盘上真实的那份 605 B 残件**，不是合成截断
    # 外部裁断点名的正是这份档（`20261013T152010Z_..._S22_03_l1_small.out`，启动即断、无 `.rc`）。
    # 负控 5 证明"解析失败会红"，这条证明"真残件独占一格时满表不出、且分类是**没测**(rc=2)而不是数值不符(rc=1)"——
    # 后者要求 `missing` 判在 `mismatch` 之前，否则线上那串恒定的四列 OVER 会把它盖掉。
    d, dst = sandbox()
    RESID = "20261013T152010Z_s22_full_certificate_S22_03_l1_small.out"
    rp = os.path.join(dst, RESID)
    if not (os.path.exists(rp) and os.path.getsize(rp) == 605 and not os.path.exists(rp + ".rc")):
        raise AssertionError("夹具前提不成立：残件 %s 不在沙箱里/大小不是 605/它竟然有 .rc"
                             % RESID)
    for fn in [f for f in os.listdir(dst)
               if "s22_full_certificate" in f and "_S22_03" in f and f != RESID]:
        os.remove(os.path.join(dst, fn))
        if os.path.exists(os.path.join(dst, fn) + ".rc"):
            os.remove(os.path.join(dst, fn) + ".rc")
    rc, art = run(m, dst)
    cases.append(("负控6 真实 605 B 残件独占 S22_03 ⇒ rc=2 且点名该格与那份档",
                  rc == 2 and "S22_03" in art and RESID in art and "没测" in art,
                  rc, art))
    shutil.rmtree(d, ignore_errors=True)

    bad = 0
    print("\n== 逐例 ==")
    for name, ok, rc, art in cases:
        nonempty = len(art) > 200
        status = "PASS" if (ok and nonempty) else "FAIL"
        if status == "FAIL":
            bad += 1
        print("   %-6s %s  rc=%s  产物=%d B%s"
              % (status, name, rc, len(art), "" if nonempty else "（空产物，退出码不可信）"))
        if status == "FAIL":
            # 只印 400 B 看不出为什么红（上一轮就因此差点把"守卫没红"和"夹具没命中"混成一件事）。
            # 把判决面的行全部抽出来：失效行 + 已认证计数行 + 不符行。
            keys = ("交叉认证失效", "交叉认证没测齐", "已认证", "新旧不符", "glob 落空")
            for ln in art.splitlines():
                if any(k in ln for k in keys):
                    print("        %s" % ln[:220])
    print("\nVERDICT %s —— 7 例（1 正例 + 6 负控）" % ("OK" if bad == 0 else "GATE_BROKEN"))
    print("# 注：正例的 rc=1 与那四个 OVER 数值是**既有判决的复现**，不是新读数；"
          "本文件不产出任何进正文的数。")
    return 0 if bad == 0 else 1


def _sha(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


if __name__ == "__main__":
    if subprocess.os.environ.get("CERTGATE_CHILD") != "1":
        sys.exit(main())
    sys.exit(main())
