#!/usr/bin/env bash
# 归档"S22 名字↔几何内容一致性核对"的读数（原件只增不改，退出码自己落盘）。
set -u
cd <REPO>/evidence/common_grid || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="${STAMP}_verify_s22_folder_identity.out"

python3 -u verify_s22_folder_identity.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "wrote $OUT rc=$RC"
exit "$RC"
