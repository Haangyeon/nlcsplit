#!/usr/bin/env bash
# 给 `tools/check_manifest_regression.sh` 做双向自检：它必须**能抓到**丢条目，也必须**不误抓**正常状态。
#
# 为什么不能只跑一次"VERDICT OK"就收：一个把所有目录都判 OK 的实现与一个真在工作的实现
# 交出的输出一模一样。本仓这两天已经为"从没响过的闸"付过学费（见 NOTE_s22_full_first_cells §五），
# 所以新写的检查器一律要现场演示一次"该响的时候响"。
#
# 安全边界（这是唯一动到真实清单的地方，所以全部约束写死在这里）：
#   - 只碰 `evidence/common_grid/MANIFEST.sha256`：**纯第一层**目录，没有子目录手工登记，
#     且这份本来就能由 `tools/make_evidence_manifest.sh common_grid` 重生成 ⇒ 最坏情况可再生。
#   - 动手之前先 `cp` 到 /tmp 并记 sha256；结束时**按 sha256 逐字节复核**还原，不一致就直接非零退出并说出备份路径。
#   - 全程不 commit、不 push、不碰别的目录。
set -u
cd /mnt/e/Project/GAMESS || exit 2
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
MF=evidence/common_grid/MANIFEST.sha256
BAK=/tmp/mf_selftest_$$.bak
OUT="evidence/release_qa/${STAMP}_manifest_regression_selftest.out"

say() { echo "$@" | tee -a "$OUT"; }

[ -f "$MF" ] || { say "!! 没有 $MF"; exit 2; }
cp "$MF" "$BAK"
SHA_BEFORE=$(sha256sum "$MF" | cut -d' ' -f1)
say "# 清单丢条目检查器的双向自检  $(date -u +%FT%TZ)"
say "# 靶文件 $MF   sha256(前)=$SHA_BEFORE   备份=$BAK"

# 选靶：**从 HEAD 那份清单里取**（检查器的基线就是 HEAD）。
# 若拿工作树今天新加的条目当靶，删掉它检查器本来就该沉默 —— 那不是坏闸，那是用例选错了。
VICTIM=$(git show "HEAD:$MF" | awk 'NF >= 2 {print $2; exit}' | sed 's/^\*//')
[ -n "$VICTIM" ] || { say "!! HEAD 清单里读不出条目，用例无法构造"; exit 2; }
awk -v v="$VICTIM" '{n=$2; sub(/^\*/,"",n); if (n==v) found=1} END{exit found?0:1}' "$MF" \
  || { say "!! 靶条目 $VICTIM 不在工作树清单里，换一个"; exit 2; }
say "# 靶条目（HEAD 与工作树都在）= $VICTIM"
say

# 精确按"条目名字段相等"删一行。
# 上一版这里用 `grep -v -F -e "*$VICTIM$"`，而 **-F 之下 `$` 是字面美元符**，
# 三个模式一条都没匹配上 ⇒ 文件根本没被改，用例 A 其实没跑，检查器"没响"是完全正确的行为。
# 这种"没构造出失败态却得出'闸是坏的'"的坑，只能靠下一步那行断言兜住。
N_BEFORE=$(wc -l < "$MF")
awk -v v="$VICTIM" '{n=$2; sub(/^\*/,"",n); if (n!=v) print}' "$MF" > "$MF.tmp" && mv "$MF.tmp" "$MF"
N_AFTER=$(wc -l < "$MF")
if [ "$N_AFTER" -ne "$((N_BEFORE - 1))" ]; then
  say "!! 用例 A 构造失败：删一行后行数 $N_BEFORE -> $N_AFTER（应当正好少 1）。"
  say "   检查器还没被测，先别下结论。已从备份还原。"
  cp "$BAK" "$MF"
  echo 2 > "$OUT.rc"; echo "# exit=2 at $(date -u +%FT%TZ)" >> "$OUT"
  exit 2
fi
say "# 已确实删掉 1 行：$N_BEFORE -> $N_AFTER"
say
bash tools/check_manifest_regression.sh > /tmp/cmr_a.$$ 2>&1
RCA=$?
HIT=$(grep -c -- "$VICTIM" /tmp/cmr_a.$$)
say "## 用例 A（该响）：rc=$RCA 且输出点名该条目 = $HIT"
sed -n '/^!!/,/^$/p' /tmp/cmr_a.$$ | head -6 | sed 's/^/   /' | tee -a "$OUT" >/dev/null

# ---- 还原，并按字节复核
cp "$BAK" "$MF"
SHA_AFTER=$(sha256sum "$MF" | awk '{print $1}')
bash tools/check_manifest_regression.sh > /tmp/cmr_b.$$ 2>&1
RCB=$?
say "## 还原：sha256(后)=$SHA_AFTER  $([ "$SHA_BEFORE" = "$SHA_AFTER" ] && echo 逐字节相同 || echo '不一致 —— 立刻人工核对备份')"
say "## 用例 B（不该响）：rc=$RCB  $(tail -1 /tmp/cmr_b.$$)"

VERDICT=DONE
[ "$RCA" -ne 0 ] || VERDICT=REFUSED_CHECKER_NEVER_FIRES
[ "$HIT" -ge 1 ] || VERDICT=REFUSED_CHECKER_DIDNAME_THE_ENTRY
[ "$SHA_BEFORE" = "$SHA_AFTER" ] || VERDICT=REFUSED_RESTORE_MISMATCH
[ "$RCB" -eq 0 ] || VERDICT=REFUSED_CHECKER_FALSE_POSITIVE
rm -f "$BAK" /tmp/cmr_a.$$ /tmp/cmr_b.$$

RCO=$([ "$VERDICT" = DONE ] && echo 0 || echo 1)
echo | tee -a "$OUT"
say "VERDICT $VERDICT —— A 必须响(rc≠0 且点名条目)、还原必须逐字节相同、B 必须不响(rc=0)。"
say "# exit=$RCO at $(date -u +%FT%TZ)"
echo "$RCO" > "$OUT.rc"
[ -f "$MF" ] || say "!! 靶文件不见了，从 $BAK 恢复不了就要人工处理"
exit "$RCO"
