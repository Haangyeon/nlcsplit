#!/usr/bin/env bash
# 把 A 件修正后的八格同单位重测汇总成一张表并归档。
# 表由 summarize_after_unitfix.py 从各格 .out 原件现算，缺任何一格就拒绝出表（rc=1），
# 所以这份归档的存在本身就是"八格齐 + 家族内跨度逐位复现归档"的证据。
# 坑：Windows 侧 python 的控制台是 GBK，表头里的 Å 直接 UnicodeEncodeError；
#     本脚本走 WSL 并显式指定 UTF-8 输出。
set -u
cd <REPO>/evidence/common_grid || exit 3
export PYTHONIOENCODING=utf-8
OUT="$(date -u +%Y%m%dT%H%M%SZ)_after_unitfix_summary_table.out"
python3 -u summarize_after_unitfix.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
