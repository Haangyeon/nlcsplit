#!/usr/bin/env bash
# 归档"Hirshfeld 两份实现是否等价"的对照读数（秒级：只建网格 + 自由原子 SCF，不跑复合物）。
#
# 为什么单独留档：这条决定了 `evidence/common_grid/NOTE_hirshfeld_two_implementations_20261013.md`
# 里那三种可能里到底哪一条成立。判据写在那份注记里，读数必须由脚本落档，
# 不能只在终端里看一眼就下结论（本仓硬规矩一：认文件不认通知）。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/common_grid/${STAMP}_probe_hirshfeld_recipe_equivalence.out"

# 线程压到 2：满表批还在跑，这条对照不需要快，只需要不打扰它。
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  python3 -u evidence/common_grid/probe_hirshfeld_recipe_equivalence.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "wrote $OUT rc=$RC"
exit "$RC"
