#!/usr/bin/env bash
# 归档"出货前置核对"的读数（含随包测试模块数——正文那处现在时计数只能从这个档填，不许手抄）。
#
# 顺序说明：本核对**只读**，任何时候跑都不改任何东西，所以它可以在批还在跑的时候归档；
# 需要等到最后的只有 MANIFEST 重生成（见 tools/run_w4_closeout.sh）。
# 另外顺手做一次阴性对照：拿一份被人为删掉一个白名单条目的副本喂给同一个检查器，
# 它必须报 NOTCLEAN 并点名那个条目——没见过它失败的核对不算核对。
set -u
cd /mnt/e/Project/GAMESS || exit 3

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/release_qa/${STAMP}_preflight_ship_check.out"

node tools/preflight_ship_check.js > "$OUT" 2>&1
RC=$?
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"

cp tools/make_public_repo.js scratch/mpr_broken.js
node -e 'const fs=require("fs");let s=fs.readFileSync("scratch/mpr_broken.js","utf8");const b=s;s=s.replace("\x27test_certificate.py\x27]","]");if(s===b){console.error("patch 没生效，阴性对照无意义");process.exit(2)}fs.writeFileSync("scratch/mpr_broken.js",s);' \
  && node tools/preflight_ship_check.js scratch/mpr_broken.js >> "$OUT" 2>&1
RCNEG=$?
rm -f scratch/mpr_broken.js
echo "# 阴性对照 rc=$RCNEG（必须非 0，且输出里点名 test_certificate.py）at $(date -u +%FT%TZ)" >> "$OUT"

# 判语：真名单必须通过（RC=0），坏名单必须失败（RCNEG!=0）
if [ "$RC" -eq 0 ] && [ "$RCNEG" -ne 0 ]; then
  echo "VERDICT DONE" >> "$OUT"; echo 0 > "$OUT.rc"
else
  echo "VERDICT REFUSED —— 真名单 rc=$RC，坏名单 rc=$RCNEG（两个条件缺一不可）" >> "$OUT"
  echo 1 > "$OUT.rc"
fi
echo "wrote $OUT rc=$(cat "$OUT.rc")"
exit "$(cat "$OUT.rc")"
