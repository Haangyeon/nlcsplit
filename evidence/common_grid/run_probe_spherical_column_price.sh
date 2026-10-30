#!/usr/bin/env bash
# 跑「球平均列定价」探针并归档（裁断第 2 步的后续：(a) 与 (c) 之间要的是发表量上的差）。
#
# 为什么要 runner 脚本而不是内联：本仓硬规矩一——认文件不认通知。带时间戳/变量的多行 shell
# 经 Git Bash → wsl bash -lc 传过去时变量被吃空过四次，有一次打印了 `wrote  rc=`
# 看着像成功、文件根本没生成。逻辑落盘，退出码由脚本自己写进 .out 与 .rc。
#
# 自证条件（少一个都算没跑成，不许退化成"退出码 0 即通过"）：
#   产物非空、`.rc` 在、档里有且只有一行 VERDICT、`# exit=` 自报行在、
#   artifact_kind 自报行在（这是"假想定义定价"档，混进正文表格是我最容易犯的错）。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/common_grid/${STAMP}_spherical_column_price.out"

python3 -u evidence/common_grid/probe_spherical_column_price.py > "$OUT" 2>&1
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
if ! grep -q '^# artifact_kind=probe_definition_price' "$OUT"; then
  echo "!! 缺 artifact_kind 自报行——这份档的数字不许进正文，身份行丢了就没法机器判别"
  exit 1
fi
if ! grep -q '^# exit=' "$OUT"; then
  echo "!! 缺 # exit= 自报行"
  exit 1
fi
echo "wrote $OUT rc=$RC  行数=$(wc -l < "$OUT")  VERDICT行=$NV"
exit "$RC"
