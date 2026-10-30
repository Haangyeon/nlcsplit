#!/usr/bin/env bash
# 汇总满 S22 证书表：把 summarize_s22_full.py 的 stdout 原样归档，并落它自己的退出码。
#
# 为什么缺格时也要归档（S22_SUM_TAG=negctrl_partial 那一档）：
#   "缺一格就不出表"这条如果只在脚本 docstring 里写着，审稿人和下一个 agent 都无法验证它真生效。
#   批还在跑的时候正好是**唯一能廉价观察到这个拒绝**的时刻——跑一份 rc=1、正文写着
#   "满表不出"的原件，等 22 格齐之后再跑一份 rc=0 的正式表。两份一起才是这条闸的证据。
# 规矩：档名带 UTC 时间戳、只增不改；.rc 与文件末尾 "# exit=" 都由本脚本自己写，
#   后台通知的 exit 0 不作数（本仓硬规矩一：认文件不认通知）。
set -u
cd <REPO>/evidence/common_grid || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
TAG="${S22_SUM_TAG:-table}"
OUT="${STAMP}_summarize_s22_full_${TAG}.out"

python3 -u summarize_s22_full.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "wrote $OUT rc=$RC bytes=$(stat -c %s "$OUT")"
exit "$RC"
