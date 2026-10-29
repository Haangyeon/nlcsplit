#!/usr/bin/env bash
# 归档式运行：把 stdout 原文与作业自写退出码一起落盘。
#
# 为什么要有这份文件（同类坑第二次，2026-10-12）：把 stamp 与重定向写在命令行上、
# 再穿过 `Git Bash -> wsl bash -lc '...'`，变量会被吃空 —— 归档根本没生成，
# 而后台任务通知仍然报 exit 0。本仓硬规矩一条是"认文件不认通知"，
# 所以取数通路必须整体落进文件，不能靠命令行拼。
#
# 用法：bash run_and_archive.sh <相对仓库根的脚本> <归档名后缀> [--环境键=值 ...]
#   例：bash run_and_archive.sh probe_nlc_parameter_authority.py probe_nlc_authority
set -u
cd "$(dirname "$0")" || exit 3
TARGET="${1:?需要脚本名}"
SUFFIX="${2:?需要归档名后缀}"
[ -f "$TARGET" ] || { echo "找不到 $TARGET"; exit 4; }

S=$(date -u +%Y%m%dT%H%M%SZ)
OUT="${S}_${SUFFIX}.out"
shift 2
for kv in "$@"; do
  case "$kv" in --*=?*) export "${kv#--}";; --*) export "${kv#--}";; esac
done

python3 -u "$TARGET" > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
