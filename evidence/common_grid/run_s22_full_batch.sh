#!/usr/bin/env bash
# W4 满 S22 本机批：把 14 个未测的 S22 官方复合物逐个跑成"一格一档"的归属证书原件。
#
# 为什么在本机跑而不是集群（偏离记录，按规矩写在脚本头）：
#   2026-10-13 15:0x 两次尝试 ssh <CLUSTER> 都停在 kex_exchange_identification（走的是
#   frp 公网隧道 101.132.159.118:51758）。按 <CLUSTER> 安全规程不反复重连。
#   目标里的降级判据就是这条：配额/通路不足 ⇒ 改本机分批并行，并留可续跑。
# 机器：20 核 / 31 GB。并发按体系大小分档，重体系少开，避免把内存和超线程吃穿。
# 可续跑：某格已有 rc=0 的档就跳过；失败的档保留（判语与 rc 就是证据），重跑只生成新时间戳档。
# 成本代理是原子数；正式每格用时打在自己的 .out 末尾"用时"行，汇总脚本按原件取。
set -u
cd <REPO>/evidence/common_grid || exit 3
export PYTHONIOENCODING=utf-8

STAMP=$(date -u +%Y%m%dT%H%M%SZ)
LOG="s22_full_batch_${STAMP}.log"

say() { echo "$@" | tee -a "$LOG"; }

run_cell() { # run_cell <NN> <线程数>
  local nn="$1" th="$2"
  if ls 2026*_s22_full_certificate_S22_${nn}_*.out.rc >/dev/null 2>&1; then
    while read -r rc; do
      [ "$rc" = "0" ] && { say "  跳过 S22_${nn}（已有 rc=0 档）"; return 0; }
    done < <(for f in 2026*_s22_full_certificate_S22_${nn}_*.out.rc; do cat "$f"; done)
  fi
  local out
  out="$(date -u +%Y%m%dT%H%M%SZ)_s22_full_certificate_S22_${nn}_l1_small.out"
  say "  提交 S22_${nn} (${th} 线程) -> $out"
  OMP_NUM_THREADS=$th OPENBLAS_NUM_THREADS=$th MKL_NUM_THREADS=$th \
    python3 -u s22_full_certificate.py "$nn" > "$out" 2>&1
  local rc=$?
  echo "$rc" > "$out.rc"
  echo "# exit=$rc at $(date -u +%FT%TZ)" >> "$out"
  say "  完成 S22_${nn} rc=$rc bytes=$(stat -c %s "$out")"
}

wave() { # wave <并发数> <线程数> <cell...>
  local par="$1" th="$2"; shift 2
  local i=0
  for nn in "$@"; do
    run_cell "$nn" "$th" &
    i=$((i + 1))
    if [ "$((i % par))" -eq 0 ]; then wait; fi
  done
  wait
}

say "# W4 本机批 起始 $STAMP host=$(hostname) 核=$(nproc)"
say "# 偏离：集群隧道不可达，改本机并行；判据与同源约束写在 s22_full_certificate.py 文件头"

# 单格定价模式：S22_ONE=03 S22_TH=6 bash run_s22_full_batch.sh
# 满表是扩范围（正文既有每格都已有原件），所以先测准一格的成本再决定要不要开多小时批。
if [ -n "${S22_ONE:-}" ]; then
  run_cell "$S22_ONE" "${S22_TH:-6}"
  say "# exit=0 at $(date -u +%FT%TZ)"
  exit 0
fi

# 四波按原子数分档（成本代理 = 原子数，双重和是 O(N²)）：
# 波一 ≤12 原子 7 格：6 并发 × 3 线程
wave 6 3 02 01 03 08 16 04 09
say "波一完成 $(date -u +%FT%TZ)"
# 波二 15–20 原子 5 格：5 并发 × 4 线程
wave 5 4 19 17 18 10 12
say "波二完成 $(date -u +%FT%TZ)"
# 波三 24–26 原子 6 格：3 并发 × 6 线程
wave 3 6 05 11 13 20 22 06
say "波三完成 $(date -u +%FT%TZ)"
# 波四 28–30 原子 4 格：2 并发 × 10 线程
wave 2 10 14 21 07 15
say "波四完成 $(date -u +%FT%TZ)"

say "## 汇总：各格退出码"
for f in 2026*_s22_full_certificate_S22_*_l1_small.out.rc; do
  [ -e "$f" ] || continue
  say "   $(basename "$f" .rc) = $(cat "$f")"
done
say "# exit=0 at $(date -u +%FT%TZ)"
