#!/usr/bin/env bash
# 跨线程比较自由原子 UHF 的解是不是同一个（1-RDM 哈希 + 能量 + ⟨S²⟩）。
#
# 为什么必须是盘上脚本而不是内联：今晚我已经第三次栽在
# `wsl bash -lc '... $T ...'` 里 `$T` 被外层 Git Bash 吃掉，结果
# `OMP_NUM_THREADS=` 空值 → libgomp 报 "Invalid value" → 两份 json 都没写出来，
# 而我差点把那次"没有文件"当成"结果一致"。这正是记忆里
# [[archive-via-script-file]] 那条的原样复发，这次连报错都一模一样。
#
# 要回答的问题（比"两份实现差多少"更基本）：换 BLAS 线程数会不会改变自由原子 UHF
# 收敛到的解？若会 ⇒ Hirshfeld 那一列的抖动源头在 SCF 层，不在归一化那一步，
# 分母阈值治不了它，正文就只能在表注里承认敏感度或固定线程出货。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/common_grid/${STAMP}_free_atom_cross_thread.out"
TMP=$(mktemp -d)

for T in 1 2 4 8; do
  OMP_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T MKL_NUM_THREADS=$T \
    python3 -u evidence/common_grid/probe_free_atom_cross_thread.py > "$TMP/t$T.json" 2>"$TMP/t$T.err"
  rc=$?
  if [ $rc -ne 0 ] || [ ! -s "$TMP/t$T.json" ]; then
    echo "!! T=$T 没产出（rc=$rc）：$(tail -3 "$TMP/t$T.err")" | tee -a "$OUT"
    echo 1 > "$OUT.rc"; echo "# exit=1 at $(date -u +%FT%TZ)" >> "$OUT"
    rm -rf "$TMP"; exit 1
  fi
done

python3 - "$TMP" >> "$OUT" 2>&1 <<'PY'
import json, sys
d = sys.argv[1]
runs = {T: json.load(open(f"{d}/t{T}.json")) for T in (1, 2, 4, 8)}
base = runs[1]
print("# 自由原子解是否随 BLAS 线程数改变（基准 = 1 线程）")
for T in (1, 2, 4, 8):
    r = runs[T]
    diffs = []
    for s in ("H", "C", "N"):
        a, b = base["atoms"][s], r["atoms"][s]
        same = a["dm_hash"] == b["dm_hash"]
        diffs.append("%s %s dE=%.1e" % (s, "同" if same else "异", abs(a["e"] - b["e"])))
    print("  T=%-2d  线程环境=%s  %s" % (T, r["threads"], "  ".join(diffs)))
    if not all(base["atoms"][s]["dm_hash"] == r["atoms"][s]["dm_hash"] for s in ("H", "C", "N")):
        print("       ⇒ T=%d 与 1 线程**不是同一个解**" % T)
verdict = ("THREAD_INVARIANT_FREE_ATOMS"
           if all(all(base["atoms"][s]["dm_hash"] == runs[T]["atoms"][s]["dm_hash"]
                      for s in ("H", "C", "N")) for T in (2, 4, 8))
           else "THREAD_DEPENDENT_FREE_ATOMS")
print("\nVERDICT %s" % verdict)
if verdict.endswith("DEPENDENT_FREE_ATOMS"):
    print("   ⇒ 抖动源头在自由原子 SCF 那一层：分母下溢阈值治不了它。"
          "正文那一列要么固定线程出货，要么承认 ~1e-2 的方法敏感度。")
else:
    print("   ⇒ 自由原子这一层与线程无关 ⇒ 抖在权重归一化/求值那一步，"
          "阈值方案仍可能对症，值得再做一步定位。")
sys.exit(0 if verdict.startswith("THREAD_INVARIANT") else 3)
PY
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
rm -rf "$TMP"
echo "wrote $OUT rc=$RC"
exit "$RC"
