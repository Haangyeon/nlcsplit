#!/usr/bin/env bash
# 对**暂存 wheel** 跑 GAMESS/许可泄漏闸门并归档。
# 为什么要单独一份：`node tools/audit_no_gamess.js` 自己会 `pip install --target`，
# 但它的判语对象是"将要出货的那一件"。内联跑会踩本仓记过的坑（Git Bash → wsl 吃空变量，
# 归档没生成而通知仍报 exit 0），所以取数通路落成脚本。
# 用法：bash evidence/release_qa/run_audit_on_staged_wheel.sh <wheel 路径>
set -u
cd <REPO> || exit 3
WHL="${1:?缺 wheel 路径}"
[ -f "$WHL" ] || { echo "wheel 不存在：$WHL"; exit 3; }
TS=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/release_qa/${TS}_audit_on_staged_wheel.out"
TDIR="/tmp/audit_staged_$TS"
node tools/audit_no_gamess.js --target "$TDIR" --src "$WHL" > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# 对象 = $WHL" >> "$OUT"
echo "# 对象 sha256 = $(sha256sum "$WHL" | awk '{print $1}')" >> "$OUT"
echo "# 注意：这一件是**从工作树直建**的对照 wheel，不是出货件（会把 INTERNAL_ONLY_MODULES 装进来）。" >> "$OUT"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
rm -rf "$TDIR"
echo "out=$OUT  rc=$RC"
