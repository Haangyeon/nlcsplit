#!/usr/bin/env bash
# 跑本机 libxc 版本/符号普查并归档（外部裁断"仍缺的核验"第 4 条）。
#
# 为什么要 runner 而不是内联：本仓硬规矩一——认文件不认通知。带时间戳/变量的多行 shell
# 经 Git Bash → wsl bash -lc 传过去时变量被吃空过，内联还出过"通知报 exit 0、档里其实是崩溃"。
# 退出码由脚本自己写进 .out 与 .rc。
#
# 自证条件（少一个都算没跑成）：产物非空、`.rc` 在、有 `# exit=` 自报行、
# 有 `# artifact_kind=machine_census` 身份行、候选份数 > 0（一份都没找到是普查失败，
# 不是"本机没有 libxc"的证据——这正是我上一版 glob 漏掉 psi4env 时踩的坑）。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/recompute/${STAMP}_libxc_version_census.out"

python3 -u evidence/recompute/libxc_version_census.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"

if [ ! -s "$OUT" ] || [ ! -f "$OUT.rc" ]; then
  echo "!! 归档没生成（OUT=$OUT），不要当成跑过了"
  exit 1
fi
if ! grep -q '^# artifact_kind=machine_census' "$OUT"; then
  echo "!! 缺 artifact_kind 身份行——这份档报的是本机环境，混进测量结果就没法机器判别"
  exit 1
fi
NC=$(grep -c '^== ' "$OUT")
if [ "$NC" -lt 1 ]; then
  echo "!! 一份 libxc 都没点到（== 行数=$NC）——先查 glob 范围，别把探测失败写成'本机没有'"
  exit 1
fi
if ! grep -q '^# exit=' "$OUT"; then
  echo "!! 缺 # exit= 自报行"
  exit 1
fi
echo "wrote $OUT rc=$RC  行数=$(wc -l < "$OUT")  普查份数=$NC"
exit "$RC"
