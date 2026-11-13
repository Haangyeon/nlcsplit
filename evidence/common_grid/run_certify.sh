#!/usr/bin/env bash
# Task 9 认证（包内路径复现修后包外读数）复跑器。
# 上一次产出已入库：20261013T_certify_inpackage_vs_external.out(.rc)，VERDICT OK，差值全部 ≤1e-3。
# 本脚本把输出名打上时间戳——归档只增不改，重跑不会覆盖掉那份已登记进 MANIFEST 的原件。
# 注意：脚本自身在一次被中断的编辑里只剩骨架（RC 写死 0、.rc 写成空行、"# exit=" 后面没有值），
# 那样产出的归档不合格，所以末段按 run_crossfamily_check.sh 的口径补回。
set -u
cd <REPO>/evidence/common_grid || exit 3
OUT="$(date -u +%Y%m%dT%H%M%SZ)_certify_inpackage_vs_external.out"
python3 -u certify_inpackage_vs_external.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
