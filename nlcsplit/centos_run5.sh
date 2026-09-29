#!/bin/bash
# CentOS 批处理 v5：把"能收敛"的证据补齐。
#  (1) 六体系 level 2 + 反泊松（level 1 的校正值还没网格收敛：-6.450→-6.153）
#  (2) 苯二聚体两构型 level 1（现在只有 level 0；SCF 里 VV10 双重和占 ~98%，可能跑不完，
#      脚本是逐体系打印的，被 timeout 截断也保留已完成行）
cd /root/gamess_work || exit 1
exec 200>/tmp/nlcsplit_centos.lock
flock 200
export OMP_NUM_THREADS=6
PY=./nlcsplit/venv/bin/python
LOG=logs
TS=$(date -u +%Y%m%dT%H%M%SZ)
export S22DIR=/root/gamess_work/nlcsplit/s22
export NCPC=1
NCLV=2 timeout 14400 $PY -u nlcsplit/step_h_s22.py 水二聚体 氨二聚体 甲烷二聚体 苯-水 苯-氨 苯-甲烷 > $LOG/${TS}_centos-step_h_l2cp.out 2>&1
echo "$TS step_h_l2cp rc=$? $(wc -l < $LOG/${TS}_centos-step_h_l2cp.out) lines" >> $LOG/MANIFEST.txt
export NCPC=0
NCLV=1 timeout 14400 $PY -u nlcsplit/step_h_s22.py 苯二聚体\(A\) 苯二聚体\(B\) > $LOG/${TS}_centos-step_h_benz_l1.out 2>&1
echo "$TS step_h_benz_l1 rc=$? $(wc -l < $LOG/${TS}_centos-step_h_benz_l1.out) lines" >> $LOG/MANIFEST.txt
echo "[batch5] done $(date +%T)" >> $LOG/${TS}_centos-DONE5.txt
