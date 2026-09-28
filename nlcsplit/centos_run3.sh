#!/bin/bash
# CentOS 批处理 v3：基组阶梯（Step 2 判据补测）。阻塞等待 v2 批的锁，不并发抢内存。
cd /root/gamess_work || exit 1
exec 200>/tmp/nlcsplit_centos.lock
flock 200                      # 阻塞直到前一批释放
export OMP_NUM_THREADS=6
PY=./nlcsplit/venv/bin/python
LOG=logs
TS=$(date -u +%Y%m%dT%H%M%SZ)
NCLV=1 timeout 5400 $PY -u nlcsplit/step_g_basis.py > $LOG/${TS}_centos-step_g.out 2>&1
echo "$TS step_g rc=$? $(wc -l < $LOG/${TS}_centos-step_g.out) lines" >> $LOG/MANIFEST.txt
echo "[batch3] done $(date +%T)" >> $LOG/${TS}_centos-step_g.out
