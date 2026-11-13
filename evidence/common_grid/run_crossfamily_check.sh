#!/usr/bin/env bash
# Task 3：跑第零'波"家族外并进包内"的对跑复现，并按本仓规矩归档。
#
# 为什么要这份包装（2026-10-12 实测）：把 stamp 与重定向写在命令行上、再穿过
#   Git Bash -> wsl bash -lc '...' 的嵌套引号，`$f` 会被吃空 —— 归档根本没生成，
#   而后台任务通知仍然报 exit 0。纪律只能靠落盘的脚本文件，不能靠命令行。
#   （这是硬规矩一条"认文件不认通知"的另一种触发形态：通知连"没生成文件"都不知道。）
#
# 归档三件：stdout 原文 .out、作业自写的 `# exit=` 行、独立 .rc 文件。
# 代价口径：LEVEL=1 只跑三份小体系（水/氨/甲烷二聚体）并开 DOUBLE=1；
#   苯系那一档按已入库计时属于 4 核·小时量级，不放本机这一跑。
set -u
cd <REPO> || exit 3
S=$(date -u +%Y%m%dT%H%M%SZ)
OUT=evidence/common_grid/${S}_crossfamily_inpackage_check_l1_small.out
LEVEL=1 NAMES="水二聚体 氨二聚体 甲烷二聚体" DOUBLE=1 \
  python3 -u evidence/common_grid/crossfamily_inpackage_check.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
