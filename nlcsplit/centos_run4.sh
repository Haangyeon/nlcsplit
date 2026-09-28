#!/bin/bash
# CentOS 批处理 v4：S22 子集（官方几何）全表。阻塞等前面批次释放锁，串行不抢内存。
cd /root/gamess_work || exit 1
exec 200>/tmp/nlcsplit_centos.lock
flock 200
export OMP_NUM_THREADS=6
PY=./nlcsplit/venv/bin/python
LOG=logs
TS=$(date -u +%Y%m%dT%H%M%SZ)
export S22DIR=/root/gamess_work/nlcsplit/s22
# 苯二聚体两种构型最贵，先跑；其余体系 level 1 一遍
NCLV=0 timeout 7200 $PY -u nlcsplit/step_h_s22.py 苯二聚体\(A\) 苯二聚体\(B\) > $LOG/${TS}_centos-step_h_benz_l0.out 2>&1
echo "$TS step_h_benz_l0 rc=$? $(wc -l < $LOG/${TS}_centos-step_h_benz_l0.out) lines" >> $LOG/MANIFEST.txt
NCLV=1 timeout 7200 $PY -u nlcsplit/step_h_s22.py 水二聚体 氨二聚体 甲烷二聚体 苯-水 苯-氨 苯-甲烷 > $LOG/${TS}_centos-step_h_l1.out 2>&1
echo "$TS step_h_l1 rc=$? $(wc -l < $LOG/${TS}_centos-step_h_l1.out) lines" >> $LOG/MANIFEST.txt
echo "[batch4] done $(date +%T)" >> $LOG/${TS}_centos-step_h_l1.out
