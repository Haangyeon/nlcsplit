#!/bin/bash
# CentOS(10.8.51.23:24522) 串行批处理 v2：几何修正（geomlib 水二聚体受体 H 朝向）之后重跑。
# 只在 /root/gamess_work/ 内读写；不碰 /root/GAMESS_BLW；同一时刻只允许一个批处理。
cd /root/gamess_work || exit 1
exec 200>/tmp/nlcsplit_centos.lock
flock -n 200 || { echo "已有批处理在跑，退出"; exit 1; }
export OMP_NUM_THREADS=6
PY=./nlcsplit/venv/bin/python
LOG=logs
mkdir -p $LOG
TS=$(date -u +%Y%m%dT%H%M%SZ)
# 顺序：先便宜的（几何只影响二聚体），再贵的
NLCSYS='(H2O)2' NCLV=0,1 timeout 1800 $PY -u nlcsplit/step_b_scan.py > $LOG/${TS}_centos-step_b_h2o2.out 2>&1
echo "$TS step_b_h2o2 rc=$? $(wc -l < $LOG/${TS}_centos-step_b_h2o2.out) lines" >> $LOG/MANIFEST.txt
timeout 3600 $PY -u nlcsplit/step2_convergence.py > $LOG/${TS}_centos-step2.out 2>&1
echo "$TS step2 rc=$? $(wc -l < $LOG/${TS}_centos-step2.out) lines" >> $LOG/MANIFEST.txt
timeout 3600 $PY -u nlcsplit/step_f_dispersion.py '(H2O)2' > $LOG/${TS}_centos-step_f_h2o2.out 2>&1
echo "$TS step_f_h2o2 rc=$? $(wc -l < $LOG/${TS}_centos-step_f_h2o2.out) lines" >> $LOG/MANIFEST.txt
timeout 3600 $PY -u nlcsplit/step_f_dispersion.py '(C6H6)2' > $LOG/${TS}_centos-step_f_benz.out 2>&1
echo "$TS step_f_benz rc=$? $(wc -l < $LOG/${TS}_centos-step_f_benz.out) lines" >> $LOG/MANIFEST.txt
timeout 9000 $PY -u nlcsplit/step_c_relaxation.py > $LOG/${TS}_centos-step_c.out 2>&1
echo "$TS step_c rc=$? $(wc -l < $LOG/${TS}_centos-step_c.out) lines" >> $LOG/MANIFEST.txt
echo "[batch2] all done $(date +%T)" > $LOG/${TS}_centos-DONE.txt
