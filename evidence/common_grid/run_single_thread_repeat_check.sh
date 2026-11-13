#!/usr/bin/env bash
# 两个**独立进程**都跑单线程，自由原子 1-RDM 是否逐位相同。
# 这一步决定 §十二 那条"固定单线程出货"是真能把 Hirshfeld 列变可复现，
# 还是只是一句写在表注里的安慰。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8 PYTHONHASHSEED=0
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/common_grid/${STAMP}_single_thread_repeat_across_processes.out"
TMP=$(mktemp -d)

for i in 1 2 3; do
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    python3 -u evidence/common_grid/probe_free_atom_cross_thread.py > "$TMP/r$i.json" 2>"$TMP/r$i.err" \
    || { echo "!! 第 $i 次跑失败：$(tail -3 "$TMP/r$i.err")" | tee -a "$OUT";
         echo 1 > "$OUT.rc"; rm -rf "$TMP"; exit 1; }
done

python3 - "$TMP" >> "$OUT" 2>&1 <<'PY'
import json, sys
d = sys.argv[1]
runs = [json.load(open(f"{d}/r{i}.json")) for i in (1, 2, 3)]
base = runs[0]
print("# 单线程、三个独立进程（每次都是新建解释器，避免进程内缓存掩盖问题）")
allsame = True
for i, r in enumerate(runs, 1):
    row = []
    for s in ("H", "C", "N"):
        same = base["atoms"][s]["dm_hash"] == r["atoms"][s]["dm_hash"]
        allsame = allsame and same
        row.append("%s %s" % (s, "同" if same else "异"))
    print("  进程%d  线程=%s  %s" % (i, r["threads"], "  ".join(row)))
print("\nVERDICT %s" % ("SINGLE_THREAD_IS_REPRODUCIBLE" if allsame
                        else "SINGLE_THREAD_STILL_VARIES"))
if allsame:
    print("   ⇒ '固定单线程'是一条**真的**能让 Hirshfeld 列逐位复现的路子（代价见 §十一：苯系数格数小时/格）。")
else:
    print("   ⇒ 连单线程都不稳 ⇒ 线程配置写进表注也只是记录，不是复现；"
          "要真复现只剩「占据平均的自由原子参考」这一条，那是换定义。")
sys.exit(0 if allsame else 3)
PY
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
rm -rf "$TMP"
echo "wrote $OUT rc=$RC"
exit "$RC"
