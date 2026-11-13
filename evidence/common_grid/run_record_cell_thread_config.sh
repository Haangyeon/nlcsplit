#!/usr/bin/env bash
# 归档"各格线程配置记录"（派生自批日志）。
#
# 为什么又单独写一个 runner 而不内联：今晚我第 **4** 次把带 `$(date -u ...)` / `$f` 的多行
# shell 内联穿过 Git Bash → wsl bash -lc，结果变量被吃空——刚才那次更阴险，它打印了
# `wrote  rc=`（看着像成功），实际文件根本没生成。本仓硬规矩一就是为这个立的：
# **认文件不认通知**。凡要产出证据文件的批处理，逻辑落盘成脚本再执行。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/common_grid/${STAMP}_cell_thread_config.out"

python3 -u evidence/common_grid/record_cell_thread_config.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"

# 自证：必须真的看见文件与两行退出码，否则这次就算没跑。
if [ ! -s "$OUT" ] || [ ! -f "$OUT.rc" ]; then
  echo "!! 归档没生成（OUT=$OUT），不要当成已记录"
  exit 1
fi
echo "wrote $OUT rc=$RC  行数=$(wc -l < "$OUT")  格行数=$(grep -c '^| S22' "$OUT")"
exit "$RC"
