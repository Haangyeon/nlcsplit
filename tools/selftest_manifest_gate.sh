#!/usr/bin/env bash
# 给 `tools/make_evidence_manifest.sh` 做四向自检：该拒的必须拒、该放的必须放、该结转的必须真在清单里。
#
# 为什么必须四个用例：这道闸是目标第 4 条"清单不得静默删登记"的全部内容，
# 而从它写出来那天起没人见过它响；更糟的是它对 `attribution_referee`（16 条子目录登记）**每天都拒**，
# 于是"staleManifests()=0"与"一条登记都不许丢"按旧实现互斥。
# 单测"该拒"会放过逢目录必拒的坏实现；单测"该放"会放过从不工作的坏实现；
# 不测"结转后条目还在"会放过**悄悄丢登记**的坏实现——而丢登记正是这道闸存在的理由。
#
# 沙箱：evidence/.manifest_gate_selftest 道具目录，测完删。
set -u
cd /mnt/e/Project/GAMESS || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
FIX=evidence/.manifest_gate_selftest
OUT="evidence/release_qa/${STAMP}_manifest_gate_selftest.out"
RC_A=-1; RC_B=-1; RC_C=-1; RC_D=-1
KEEP_A=""; KEEP_C=""
rm -rf "$FIX"; mkdir -p "$FIX/outputs"
say() { echo "$@" | tee -a "$OUT"; }

say "# tools/make_evidence_manifest.sh 四向自检  $(date -u +%FT%TZ)"

# ---- 道具内容：第一层两个真文件 + 子目录一个真原件 + 一个假条目
echo aaa > "$FIX/one.out"; echo bbb > "$FIX/two.out"; echo ccc > "$FIX/outputs/sub_original.out"
( cd "$FIX"
  sha256sum -b one.out > MANIFEST.sha256
  sha256sum -b outputs/sub_original.out >> MANIFEST.sha256
  echo "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef *outputs/GONE.out" >> MANIFEST.sha256 )

say; say "## A：旧清单含一条**磁盘上不存在**的子目录原件 ⇒ 必须拒、rc≠0、原清单一字不动"
BEFORE=$(sha256sum "$FIX/MANIFEST.sha256" | awk '{print $1}')
bash tools/make_evidence_manifest.sh .manifest_gate_selftest >> "$OUT" 2>&1; RC_A=$?
KEEP_A=$(sha256sum "$FIX/MANIFEST.sha256" | awk '{print $1}')
say "   rc=$RC_A  清单 $([ "$BEFORE" = "$KEEP_A" ] && echo 未被改动 OK || echo 被改写——不合格)"

# ---- B：把假条目拿掉，只留真实存在的子目录原件 ⇒ 必须放行，而且那条必须还在清单里
grep -v "GONE.out" "$FIX/MANIFEST.sha256" > "$FIX/.mf.tmp" && mv "$FIX/.mf.tmp" "$FIX/MANIFEST.sha256"
say; say "## B/C：只剩**存在**的子目录原件 ⇒ B 必须放行(rc=0)；C 必须证明那条被结转、没被静默删"
bash tools/make_evidence_manifest.sh .manifest_gate_selftest >> "$OUT" 2>&1; RC_B=$?
CARRIED=$(awk 'NF>=2 {print $2}' "$FIX/MANIFEST.sha256" | sed 's/^\*//' | grep -c '^outputs/sub_original.out$')
L1=$(awk 'NF>=2 {print $2}' "$FIX/MANIFEST.sha256" | sed 's/^\*//' | grep -vc '/')
say "   B rc=$RC_B"
say "   C 结转子目录条目 $CARRIED 条（应为 1）；第一层 $(wc -l < "$FIX/MANIFEST.sha256") 行里有 $L1 条第一层登记（应为 2）"
RC_C=$([ "$CARRIED" = "1" ] && [ "$L1" = "2" ] && echo 0 || echo 1)
say "   C rc=$RC_C"

# ---- D：真实第一层文件被删 ⇒ 必须拒（这才是旧版那道闸的本意，只是过去误伤了 B/C）
rm -f "$FIX/two.out"
say; say "## D：登记过的第一层文件被删 ⇒ 必须拒（真丢了，不是格式问题）"
bash tools/make_evidence_manifest.sh .manifest_gate_selftest >> "$OUT" 2>&1; RC_D=$?
say "   rc=$RC_D"

rm -rf "$FIX"
[ -d "$FIX" ] && say "!! 道具目录没删干净：$FIX"

VERDICT=DONE
[ "$RC_A" -ne 0 ] || VERDICT=FAIL_A_should_refuse
[ "$BEFORE" = "$KEEP_A" ] || VERDICT=FAIL_A_clobbered
[ "$RC_B" -eq 0 ] || VERDICT=FAIL_B_should_pass
[ "$RC_C" -eq 0 ] || VERDICT=FAIL_C_entry_dropped
[ "$RC_D" -ne 0 ] || VERDICT=FAIL_D_should_refuse
say
say "VERDICT $VERDICT"
say "# 判据：A 拒且不改、B 放行、C 子目录条目必须**还在**、D 第一层真丢了要拒。"
RCO=$([ "$VERDICT" = DONE ] && echo 0 || echo 1)
echo "$RCO" > "$OUT.rc"
say "# exit=$RCO at $(date -u +%FT%TZ)"
exit "$RCO"
