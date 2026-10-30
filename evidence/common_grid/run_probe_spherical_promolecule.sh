#!/usr/bin/env bash
# 跑球平均判别探针并归档（裁断第 2 步）。
#
# 为什么单独写 runner：本仓硬规矩一——认文件不认通知。带时间戳/变量的多行 shell
# 经 Git Bash → wsl bash -lc 传过去时变量被吃空过四次，有一次还打印了 `wrote  rc=`
# 看着像成功、文件根本没生成。所以逻辑落盘成脚本，退出码由脚本自己写进 .out 与 .rc。
#
# 自证条件（少一个都算没跑成，不许退化成"退出码 0 即通过"）：
#   产物非空、`.rc` 在、档里有 VERDICT 行、`# exit=` 自报行在。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/common_grid/${STAMP}_spherical_promolecule_thread_probe.out"

python3 -u evidence/common_grid/probe_spherical_promolecule_thread.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"

if [ ! -s "$OUT" ] || [ ! -f "$OUT.rc" ]; then
  echo "!! 归档没生成（OUT=$OUT），不要当成跑过了"
  exit 1
fi
NV=$(grep -c '^VERDICT ' "$OUT")
if [ "$NV" -ne 1 ]; then
  echo "!! 档里 VERDICT 行数 = $NV（应为 1）——崩溃与判定长得一样，退出码不可信"
  exit 1
fi
if ! grep -q '^# exit=' "$OUT"; then
  echo "!! 缺 # exit= 自报行"
  exit 1
fi
echo "wrote $OUT rc=$RC  行数=$(wc -l < "$OUT")  VERDICT行=$NV"
exit "$RC"
