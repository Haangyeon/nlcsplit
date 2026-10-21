#!/usr/bin/env bash
# W4 满表收口：按**固定顺序**跑完"表出得来 → 才重生成清单 → 再核对没丢登记 → 最后跑闸门"。
#
# 为什么需要这个脚本：本仓的硬规矩二写着"MANIFEST 在所有证据编辑定稿之后最后重生成，
# 顺序反了 gate C2 会抓到你自己"。而这条顺序此前只存在于人脑子里——批跑完那一刻
# 正是最容易先重生成清单、再补跑汇总的时刻，那样汇总表本身就不在清单里了。
# 顺序写死在脚本里，比写在注释里可靠。
#
# 每步都落自己的 rc；任何一步非零就**停在那里**，不带病往下走，也不回头去改前面的产物。
# 只增不改：产物文件名带 UTC 时间戳。
# 这个脚本随时可以试跑：满表不齐时它会在第 1 步就停下，**不碰清单**（下面的 -z 分支就是这条保证的演示）。
set -u
cd /mnt/e/Project/GAMESS || exit 2
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/common_grid/${STAMP}_w4_closeout.out"
FAIL=0
say() { echo "$@" | tee -a "$OUT"; }
step() { say; say "## 步 $1：$2"; }

say "# W4 满表收口  起始 $(date -u +%FT%TZ)  host=$(hostname)"
say "# git HEAD $(git rev-parse HEAD)"

# ---- 1 满表必须由脚本出得来（不过就到此为止，绝不先去重生成清单；失败原因见下面的 rc 分派）
step 1 "summarize_s22_full.py 出满表"
# TAG=table_closeout：收口这一跑与手工试跑分开，免得证据目录里出现两份都叫 `_table`
# 而一份是 rc=1 的"满表不出"——名字含糊正是本仓这几天反复在修的那类坑。
S22_SUM_TAG=table_closeout bash evidence/common_grid/run_summarize_s22_full.sh >> "$OUT" 2>&1
RC1=$?
say "   rc=$RC1"
if [ "$RC1" -ne 0 ]; then
  # 失败文案**不预设失败形状**（2026-10-15 实测：那次 rc=1 的真实原因是逐列认证不符、
  # 缺格数=0，而旧文案硬说"上面列了缺哪些格"——读日志的人会被导向错的方向。
  # 外部裁断 §7.1 第 5 条又指出：rc=2（没测齐）走到这里也会印"缺哪些格"。
  # 所以按 rc 分派，并把判决档里 `!!` 那几行**原样**贴出来，让档自己说话。）
  TB=$(ls -t evidence/common_grid/*_summarize_s22_full_table_closeout.out 2>/dev/null | head -1)
  say "STOP —— 第 1 步没过（rc=$RC1）。不猜原因，贴档里实际报的行："
  say "   判决档：${TB:-（没找到 table_closeout 档，这本身就是要查的事）}"
  if [ "$RC1" -eq 2 ]; then
    say "   rc=2 的含义是**没测**——两种形状都归这一类：交叉认证没测齐（旧档落空/六列不齐/身份不唯一/"
    say "        声明外多出一格），或满表本身缺格（某一格只剩残件/没有 rc=0 的档/有档但读不出行）。"
    say "        2026-10-18 裁断第 1 步把后一种从 rc=1 挪到这里：残件不许被报成'出了表但数值不符'。"
  elif [ "$RC1" -eq 1 ]; then
    say "   rc=1 的含义是**格齐、认证齐，但新旧读数不符**（只有满表与既有表不同源这一类）。"
    say "        看下面的 !! 行是哪类；缺格与读不出行现在不会走到这一支。"
  fi
  if [ -n "$TB" ]; then
    while IFS= read -r ln; do say "   档内原样：$ln"; done < <(grep '^!! ' "$TB" | head -6)
  fi
  say "   清单**没动**：这正是本脚本存在的理由，别让'先把清单跑绿'插到表前面。"
  echo "$RC1" > "$OUT.rc"
  say "# exit=$RC1 at $(date -u +%FT%TZ)"
  exit "$RC1"
fi

# ---- 1b 各格线程配置的记录（派生自批日志）。必须在重生清单**之前**跑，
#      否则这份记录自己会变成没人登记的散档。它不判通过与否（VERDICT NOTE），
#      非零只可能是批日志缺了"提交 S22_NN (K 线程)"那类行——那种情况要人看见。
step 1b "record_cell_thread_config.py（线程配置记录，派生）"
REC="evidence/common_grid/$(date -u +%Y%m%dT%H%M%SZ)_cell_thread_config.out"
PYTHONIOENCODING=utf-8 python3 -u evidence/common_grid/record_cell_thread_config.py > "$REC" 2>&1
RC1B=$?
echo "$RC1B" > "$REC.rc"
echo "# exit=$RC1B at $(date -u +%FT%TZ)" >> "$REC"
say "   rc=$RC1B  档 $(basename "$REC")（派生自批日志，不是原件自报）"
[ "$RC1B" -eq 0 ] || FAIL=1

# ---- 2 表已定稿 ⇒ 现在才是重生清单的时刻
step 2 "重生成 evidence/*/MANIFEST.sha256"
bash tools/make_evidence_manifest.sh >> "$OUT" 2>&1
RC2=$?
say "   rc=$RC2"
[ "$RC2" -eq 0 ] || { say "STOP —— 清单脚本自己拒了某个目录（多半是那目录有子目录手工登记）。"; FAIL=1; }

# ---- 3 逐目录核对：相对 HEAD 没有条目消失
step 3 "tools/check_manifest_regression.sh"
bash tools/check_manifest_regression.sh >> "$OUT" 2>&1
RC3=$?
say "   rc=$RC3"
[ "$RC3" -eq 0 ] || FAIL=1

# ---- 4 权威陈旧度：调 lib.js 的函数，不在 shell 里手搓比对
step 4 "staleManifests(process.cwd())"
STALE=$(node -e "const l=require('./tools/hooks/lib.js');const s=l.staleManifests(process.cwd());console.log(Array.isArray(s)?s.length:s)" 2>&1 | tail -1)
say "   staleManifests = $STALE"
[ "$STALE" = "0" ] || { say "   不为 0 ⇒ 有证据文件没进清单"; FAIL=1; }

# ---- 5 正文闸门
step 5 "claim_gate / precommit_gate"
node tools/claim_gate.js >> "$OUT" 2>&1; RC5A=$?
node tools/hooks/precommit_gate.js >> "$OUT" 2>&1; RC5B=$?
say "   claim_gate rc=$RC5A  precommit rc=$RC5B"
[ "$RC5A" -eq 0 ] && [ "$RC5B" -eq 0 ] || FAIL=1

# ---- 6 全稿"零手抄"：每行的数值组合要能在归档里共现（不依赖任何中英名字映射）
step 6 "tools/audit_table_row_provenance.js"
node tools/audit_table_row_provenance.js >> "$OUT" 2>&1
RC6=$?
say "   rc=$RC6"
# 它只在"某个数值在任何档里都找不到"时才 rc=1；跨档拼一行是合法的，不算失败。
[ "$RC6" -eq 0 ] || FAIL=1

# ---- 7 体系列唯一性：四对"同式不同几何"的格必须分得开，否则表里出现两行一样的体系
#      （全 22 格里 4 对：05/13、07/15、11/20、14/21；判据脚本自己会报还差几对没成对落档）
#      键 = (片段A, 片段B, 片间最短 dmin)，全部从各格 .out 抬头现读，不靠名字映射。
step 7 "evidence/common_grid/check_cell_key_uniqueness.py"
python3 evidence/common_grid/check_cell_key_uniqueness.py >> "$OUT" 2>&1
RCU=$?
say "   唯一性 rc=$RCU（0 唯一 / 1 撞键 / 2 一格都没读到 = 没测）"
# 判定逻辑只在那一个文件里：这里曾经内联过一份，同一约定两处实现是本仓反复出事的病根。
[ "$RCU" -eq 0 ] || FAIL=1

say
if [ "$FAIL" -eq 0 ]; then
  say "VERDICT DONE —— 满表出得来、线程配置有记录、清单已重生成、无条目丢失、陈旧 0、两闸门 rc=0、全稿零手抄、体系列唯一。"
  say "# exit=0 at $(date -u +%FT%TZ)"
  echo 0 > "$OUT.rc"
  exit 0
fi
say "VERDICT NOTCLEAN —— 上面有非零步。未提交条目归零不在本脚本范围内（那是作者的保留动作，且必须 Windows 侧）。"
say "# exit=1 at $(date -u +%FT%TZ)"
echo 1 > "$OUT.rc"
exit 1
