#!/usr/bin/env bash
# 测试条数清点的归档跑（出货前基线 / 出货后改口都用它）。
# 为什么单列一份 runner：正文 `software.md` 里"ships N test modules / those collect M /
# 留在树外的 K 条全是某某模块"是**现在时**主张，加一次测试就过期一次，
# 而过期的整数不会被数字闸门抓到（它只拦带小数点的量）。所以每次动过随包测试清单，
# 出货前后各跑一次并留档，改口时引档名而不是引记忆。
# 判读：分组数必须等于全量（脚本自己会拒绝相加不等）；
#       "不随包"那一组在出货前必然包含新加的测试 —— 那是 §5 "every table" 还不成立的直接证据。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8
OUT="evidence/release_qa/$(date -u +%Y%m%dT%H%M%SZ)_test_count_census.out"
python3 -u evidence/release_qa/test_count_census.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
