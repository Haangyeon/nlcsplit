#!/usr/bin/env bash
# W4-本机版：A 件修正后，把剩下 7 格里还没重测的 6 格按同单位重跑（苯-水已单独完成）。
#
# 为什么不走集群（对"≥30 min 直接排集群"这条规矩的一次明说的偏离）：
#   2026-10-12 实测 `squeue -u <OPERATOR>`：51334 p1_dftX RUNNING 且 TIME_LEFT=6-21:13:12，
#   51335 已因 `QOSMaxCpuPerUserLimit` PENDING ⇒ 用户 CPU 配额被另一个项目的长作业占满，
#   再提一个新 sbatch 只会一起排队等数天，不是 4 核·小时出数。
#   去留：不撤别人的/别的项目的作业（红线），改用本机并行；集群留到配额空出来再说。
#
# 分两波，避免 24 原子那两格把内存挤爆：
#   波一（5 格，每格 3 线程）：甲烷 / 水 / 氨 / 苯-甲烷 / 苯-氨
#   波二（2 格，每格 8 线程，串行错峰）：苯(A) / 苯(B)
# 每格独立归档：stdout 原文 .out + 独立 .rc + 作业自写 `# exit=` 行（本仓坑 1、坑 2）。
# 旧档一个字节不改；更正注记在 CORRECTION_20261012_hirshfeld_unit.md。
# 清单（MANIFEST.sha256）等全部证据定稿后**最后**再重生成。
set -u
cd <REPO> || exit 3
SCRIPT=evidence/common_grid/hirshfeld_crossfamily.py
LOGDIR=evidence/common_grid
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
echo "# W4 本机批 起始 $STAMP  host=$(hostname)"

# 波一：五格并行
for cell in 甲烷二聚体 水二聚体 氨二聚体 苯-甲烷 苯-氨; do
  out="${LOGDIR}/${STAMP}_hirshfeld_crossfamily_l1_${cell}_after_unitfix.out"
  ( cd <REPO> && OMP_NUM_THREADS=3 LEVEL=1 NAMES="$cell" \
      python3 -u "$SCRIPT" > "$out" 2>&1; echo $? > "$out.rc";
    echo "# exit=$(cat "$out.rc") at $(date -u +%FT%TZ)" >> "$out" ) &
  echo "  提交 $cell (3 线程) -> $(basename "$out")"
done
wait
echo "波一完成 $(date -u +%FT%TZ)"

# 波二：两格 24 原子，各 8 线程，并行两路（16 线程 < 20 核）
for cell in 苯二聚体\(A\) 苯二聚体\(B\); do
  key=$(echo "$cell" | tr -d '()')
  out="${LOGDIR}/${STAMP}_hirshfeld_crossfamily_l1_${key}_after_unitfix.out"
  ( cd <REPO> && OMP_NUM_THREADS=8 LEVEL=1 NAMES="$cell" \
      python3 -u "$SCRIPT" > "$out" 2>&1; echo $? > "$out.rc";
    echo "# exit=$(cat "$out.rc") at $(date -u +%FT%TZ)" >> "$out" ) &
  echo "  提交 $cell (8 线程) -> $(basename "$out")"
done
wait
echo "波二完成 $(date -u +%FT%TZ)"

echo "## 汇总：各格退出码"
for f in "${LOGDIR}/${STAMP}"*_after_unitfix.out.rc; do
  echo "   $(basename "$f") = $(cat "$f")"
done
echo "# exit=0 at $(date -u +%FT%TZ)"
