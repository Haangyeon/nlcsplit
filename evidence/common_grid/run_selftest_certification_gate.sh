#!/usr/bin/env bash
# 跑交叉认证守卫的自测（1 正例 + 6 负控）并归档。
#
# 为什么单独写 runner 而不内联：本仓硬规矩一 —— 认文件不认通知。
# 带 `$(date -u ...)` / 循环变量的多行 shell 经 Git Bash → wsl bash -lc 传过去时
# 变量被吃空过四次（有一次还打印了 `wrote  rc=` 看着像成功、文件根本没生成）。
# 所以逻辑落盘成脚本，退出码由脚本自己写进 `.out` 与 `.rc`，末尾再自证产物非空。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/common_grid/${STAMP}_selftest_certification_gate.out"

python3 -u evidence/common_grid/selftest_certification_gate.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"

if [ ! -s "$OUT" ] || [ ! -f "$OUT.rc" ]; then
  echo "!! 自测归档没生成（OUT=$OUT），不要当成跑过了"
  exit 1
fi
# 用例数是**外部声明**的，不从产物里数出来（否则加一条负控就自动"通过"，
# 正是裁断第 1 步要打掉的那种静默缩面）。加/减用例必须同时改这里。
EXPECT=7
N=$(grep -c '^   PASS\|^   FAIL' "$OUT")
if [ "$N" -ne "$EXPECT" ]; then
  echo "!! 自测打印了 $N 个用例判决行，外部声明是 $EXPECT —— 用例数不对，退出码不可信"
  exit 1
fi
echo "wrote $OUT rc=$RC  行数=$(wc -l < "$OUT")  用例判决行=$N"
exit "$RC"
