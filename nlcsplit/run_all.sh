#!/bin/bash
# 串行跑 nlcsplit 的三个验证/测量脚本。
#  - flock 单实例锁：避免两个 agent 同时跑、互相覆盖证据
#  - 每个脚本的输出落到带时间戳的新文件（不就地覆盖），并在 MANIFEST 里登记
# 用法: bash run_all.sh [step1|step2|step_c|step_b]...   不给参数=全跑
cd /mnt/e/Project/GAMESS || exit 1
export OMP_NUM_THREADS=4
LOGDIR=nlcsplit/logs
mkdir -p "$LOGDIR"
LOCK=/tmp/nlcsplit_runner.lock

if ! flock -n 9; then
    echo "另一个 runner 还在持锁，本次退出"; exit 1
fi 9>"$LOCK"

TAGS=("$@"); [ ${#TAGS[@]} -eq 0 ] && TAGS=(step1 step2 step_c step_b)
declare -A CMD=(
  [step1]="nlcsplit/step1_validate.py"
  [step2]="nlcsplit/step2_convergence.py"
  [step_c]="nlcsplit/step_c_relaxation.py"
  [step_b]="nlcsplit/step_b_scan.py"
)
TS=$(date -u +%Y%m%dT%H%M%SZ)
for t in "${TAGS[@]}"; do
    f="$LOGDIR/${TS}_${t}.out"
    echo "[runner] $t -> $f  ($(date +%T))"
    timeout 5400 python3 -u ${CMD[$t]} > "$f" 2>&1
    rc=$?
    echo "$TS $t rc=$rc $(wc -l < "$f") lines $f" >> "$LOGDIR/MANIFEST.txt"
done
echo "[runner] all done $(date +%T)"
