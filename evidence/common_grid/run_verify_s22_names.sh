#!/usr/bin/env bash
# 归档"S22 文件夹号↔官方标签"核对的读数（原件只增不改，退出码自己落盘）。
# 离线可跑：读的是已落盘的 scratch/lit/gmtkn55_S22.res，脚本不联网。
set -u
cd <REPO>/evidence/common_grid || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="${STAMP}_verify_s22_official_names.out"

python3 -u verify_s22_official_names.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "wrote $OUT rc=$RC"
exit "$RC"
