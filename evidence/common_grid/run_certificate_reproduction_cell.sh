#!/usr/bin/env bash
# 通用版证书入口复现归档：可指定体系名与线程数，档名如实带上两者。
#
# 为什么单独写一个（已有 run_certificate_reproduction.sh）：
# 那个跑法把 OMP=4 与"waterdimer"写死，而我现在要答两个新问题——
#   ① 第二格（甲烷二聚体）是否也复现；
#   ② 同一格换线程数（1 vs 4）还复现吗 —— G5 说 Hirshfeld 权重随 BLAS 线程漂，
#      而本检验的门是 1e-4，比那个抖动小一个量级。
# 所以档名必须带 **体系 + 线程数**，否则两份档互相矛盾时又没人知道差在哪个变量上
# （这就是今晚那对"一份 rc=3、一份 rc=0"的档教我的事）。
set -u
cd <REPO>/evidence/common_grid || exit 3
export PYTHONIOENCODING=utf-8

CELL_CN="${1:-水二聚体}"
TH="${2:-4}"
TAG="${3:-waterdimer}"
ROOT=<REPO>
export CERT_CELL="$CELL_CN"
export OMP_NUM_THREADS="$TH" OPENBLAS_NUM_THREADS="$TH" MKL_NUM_THREADS="$TH"

OUT="$(date -u +%Y%m%dT%H%M%SZ)_certificate_reproduction_l1_${TAG}_th${TH}.out"
python3 -u certificate_reproduction.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
{
  echo "# 体系=$CELL_CN  线程=$TH  CERT_CELL=${CERT_CELL}  门 TOL=1e-4"
  echo "# exit=$RC at $(date -u +%FT%TZ)"
} >> "$OUT"
echo "wrote $OUT rc=$RC"
exit "$RC"
