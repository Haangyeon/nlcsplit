#!/usr/bin/env bash
# W3 验收归档跑：certify(包内新入口) vs 已归档的包内 dispatcher 读数（水二聚体 level 1）。
# 输出只增不改：档名带 UTC 时间戳，退出码写进 .rc，`# exit=` 自写行追进 .out。
# 用法：bash evidence/common_grid/run_certificate_reproduction.sh
set -u
cd <REPO>/evidence/common_grid || exit 3
export PYTHONIOENCODING=utf-8 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
OUT="$(date -u +%Y%m%dT%H%M%SZ)_certificate_reproduction_l1_waterdimer.out"
ROOT=<REPO> python3 -u certificate_reproduction.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
