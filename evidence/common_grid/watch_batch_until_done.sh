#!/usr/bin/env bash
# 守着批和两发复现跑完，然后一次性汇报——避免每轮都手查一次、把轮次耗在轮询上。
# 只读：绝不碰任何作业、不改任何文件（除了自己的归档）。
set -u
cd <REPO> || exit 3
LIMIT=${LIMIT:-21600}          # 最多守 6 h，超时就带着现状退出，不无限挂
SLEEP=${SLEEP:-300}            # 每 5 min 看一次
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/common_grid/${STAMP}_watch_batch.out"
START=$(date +%s)

say() { echo "$@" | tee -a "$OUT"; }
say "# 守望起始 $(date -u +%FT%TZ)  每 ${SLEEP}s 一次，上限 ${LIMIT}s"

while :; do
  N=$(ls evidence/common_grid/*s22_full_certificate*.out.rc 2>/dev/null | wc -l)
  W1="跑中"; for f in evidence/common_grid/*_certificate_reproduction_l1_waterdimer_th1.out; do
      [ -f "$f.rc" ] && W1="$(cat "$f.rc")"; done
  say "$(date -u +%FT%TZ)  满表 $N/22   水格OMP=1复现 rc=$W1"
  if [ "$N" -ge 22 ]; then
    say "DONE —— 满表齐了。下一步：bash tools/run_w4_closeout.sh（8 步，顺序不可换）"
    echo 0 > "$OUT.rc"; break
  fi
  if [ $(( $(date +%s) - START )) -gt "$LIMIT" ]; then
    say "TIMEOUT —— 到上限仍未齐，带现状退出（别把这条读成失败：批只是还在跑）"
    echo 2 > "$OUT.rc"; break
  fi
  sleep "$SLEEP"
done
say "# exit=$(cat "$OUT.rc") at $(date -u +%FT%TZ)"
exit 0
