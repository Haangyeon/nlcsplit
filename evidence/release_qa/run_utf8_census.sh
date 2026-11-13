#!/usr/bin/env bash
# 跑出货前的 UTF-8 普查并归档（裁断第 3 步那条"UTF-8 输出最终复核"的可复查原件）。
#
# 为什么要 runner 而不是内联：本仓硬规矩一——认文件不认通知。带时间戳/变量的多行 shell
# 经 Git Bash → wsl bash -lc 传过去时变量被吃空过，内联还出过"通知报 exit 0、档里是崩溃"。
# 退出码由脚本自己写进 .out 与 .rc。
#
# rc 语义（这份普查是**判决型**的，不是"跑完=通过"）：
#   rc=0 ⇒ VERDICT CLEAN（evidence/** 里没有真文本编码缺陷）
#   rc=1 ⇒ VERDICT NEEDS_FIX（有，档里逐份列了偏移）——**这是预期内的失败，不是脚本坏了**
# 自证条件：产物非空、`.rc` 在、有且只有一行 VERDICT、有 artifact_kind 身份行、有 `# 扫过` 计数行。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/release_qa/${STAMP}_utf8_census.out"

python3 -u evidence/release_qa/utf8_census.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"

if [ ! -s "$OUT" ] || [ ! -f "$OUT.rc" ]; then
  echo "!! 归档没生成（OUT=$OUT），不要当成跑过了"
  exit 1
fi
NV=$(grep -c '^VERDICT ' "$OUT")
if [ "$NV" -ne 1 ]; then
  echo "!! 档里 VERDICT 行数 = $NV（应为 1）——崩溃与判决长得一样，退出码不可信"
  exit 1
fi
if ! grep -q '^# artifact_kind=machine_census' "$OUT"; then
  echo "!! 缺 artifact_kind 身份行"
  exit 1
fi
if ! grep -q '^# 扫过 ' "$OUT"; then
  echo "!! 缺『# 扫过』计数行——没扫到东西不能算普查过"
  exit 1
fi
echo "wrote $OUT rc=$RC  行数=$(wc -l < "$OUT")  VERDICT行=$NV"
exit "$RC"
