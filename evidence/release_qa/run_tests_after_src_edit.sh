#!/usr/bin/env bash
# 改了随包源码（如 nlcsplit/geomlib.py、partition.py）之后，把"非 slow 测试仍全绿"归档一份。
#
# 为什么单独归档：正文 §5 与 CONTRIBUTING 都在说"读者一条命令能复现"，而这条命令的真值
# 取决于**当前工作树的源码**，不取决于三周前那次跑绿。每次动过随包文件就重跑并落档，
# 才让"测试随包全绿"这句话有对应的原件可指。
# 退出码由本脚本自己写进 .rc 与文件末尾 "# exit="，不看后台通知的 exit 0（本仓硬规矩一）。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
TAG="${SRC_EDIT_TAG:-after_src_edit}"
DIR=evidence/release_qa
OUT="$DIR/${STAMP}_pytest_notslow_${TAG}.out"

# 线程压到 2：本机此刻可能还有 W4 满表批在跑，别让一次回归把核抢光拖慢批。
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 \
  python3 -u -m pytest nlcsplit/tests -q -m "not slow" > "$OUT" 2>&1
RC=$?
# 抬头补一行改了哪些随包文件（相对 HEAD），免得日后看不出这份绿是对哪棵树绿的。
{ echo "# 随包源码相对 HEAD 的改动：$(git diff --name-only HEAD -- nlcsplit/ | tr '\n' ' ')"; \
  echo "# git HEAD $(git rev-parse HEAD)"; \
  cat "$OUT"; } > "$OUT.tmp" && mv "$OUT.tmp" "$OUT"
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "wrote $OUT rc=$RC"
exit "$RC"
