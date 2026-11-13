#!/usr/bin/env bash
# 满 S22 汇总归档跑：把 `summarize_s22_full.py` 的输出落成一份带 rc 的原件。
#
# 为什么单独一个 runner 而不并进 run_s22_full_batch.sh：
#   bash 是按字节偏移边读边执行的，**改一个正在跑的脚本会把批切坏**。
#   满表批跑完后，再单独执行本脚本。
# 判读：缺格时 rc=1 是**预期**（脚本拒绝出半表），不是失败；
#       只有 22 格齐 + 交叉认证列全 OK 才 rc=0。
set -u
cd <REPO>/evidence/common_grid || exit 3
export PYTHONIOENCODING=utf-8
OUT="$(date -u +%Y%m%dT%H%M%SZ)_s22_full_summary_table.out"
python3 -u summarize_s22_full.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
echo "（rc=1 且末行是“缺格”⇒ 满表还没齐，等批跑完再重跑本脚本）"
