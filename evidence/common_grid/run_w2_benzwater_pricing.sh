#!/usr/bin/env bash
# W2 定价跑：A 件（Hirshfeld 自由原子中心单位口径）修正之后，重测**苯-水**一格的 level 1 读数。
#
# 为什么先只跑这一格：交接件 §五 那张八格表里，跨构造带顶 0.3898 与"苯-水 Hirshfeld 越界 +0.1430"
# 全部由**这一格、这一个构造**决定；它定了 A 口径与 B 口径的差别是否存在。本机成本约 33 min
# （同一格归档实测 1952.7 s 量级），先把定价拿到，再决定要不要花 4 核·小时全量重跑八格。
#
# 单变量纪律：脚本、几何、基组、网格 level、(b,C)、自由原子多重度表全部不动，
# 唯一的改变是 A 件修正（`atom_coord` 由 Å 改回与网格同单位 Bohr）。
# 因此本跑自带一条硬对照：
#   家族内四条 E_AB 与跨度**必须逐位复现归档**（水…苯-水那格的 0.2468）——
#   它们不碰自由原子密度；复现不了就说明我改坏了别的东西，整跑作废。
#   Voronoi 那一行同样不该受 A 件影响（两侧同为 Bohr）。
# 预期只动 Hirshfeld 越界/增量与跨构造总跨度。
#
# 归档三件：stdout 原文 .out、作业自写 `# exit=` 行、独立 .rc。
# 清单（MANIFEST.sha256）等这一跑与后续证据编辑全部定稿后**最后**再重生成，顺序反了 gate C2 会抓自己。
set -u
cd <REPO> || exit 3
S=$(date -u +%Y%m%dT%H%M%SZ)
OUT=evidence/common_grid/${S}_hirshfeld_crossfamily_l1_benzwater_after_unitfix.out
LEVEL=1 NAMES="苯-水" python3 -u evidence/common_grid/hirshfeld_crossfamily.py > "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
