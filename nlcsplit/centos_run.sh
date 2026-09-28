#!/bin/bash
# CentOS(10.8.51.23:24522) 上的串行批处理：V2 核下的正式表。
# 只在 /root/gamess_work/ 内读写；不碰 /root/GAMESS_BLW。
cd /root/gamess_work || exit 1
export OMP_NUM_THREADS=6
PY=./nlcsplit/venv/bin/python
LOG=logs
mkdir -p $LOG
TS=$(date -u +%Y%m%dT%H%M%SZ)
for t in step_b step_c step2; do
    f=$LOG/${TS}_centos-$t.out
    echo "[batch] $t -> $f  $(date +%T)"
    timeout 7200 $PY -u nlcsplit/${t}_*.py > "$f" 2>&1
    echo "$TS $t rc=$? $(wc -l < "$f") lines $f" >> $LOG/MANIFEST.txt
done
echo "[batch] all done $(date +%T)"
