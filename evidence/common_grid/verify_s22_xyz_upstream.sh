#!/usr/bin/env bash
# 把本地 22 份 S22 官方几何与上游 tag v1 逐字节重核哈希（网络恢复后欠的一条完整性凭据）。
#
# 为什么要这一档：满表的每一格都建立在 `scratch/lit/s22/S22_NN.xyz` 上，
# 而这些文件是 2026-10-11 用 `scratch/lit/get_s22.sh` 从
# raw.githubusercontent.com/grimme-lab/GMTKN55/v1 取回的。断网期间无法复核，
# 所以台账里挂了一条"未闭合"。今天网络通了，就把这条了掉——
# 它同时是"证书可复现"的一部分：审稿人按同一 URL 取回的字节必须和我们算过的一致。
#
# 跑在哪一侧：**Windows / Git Bash 侧**。WSL 里没有到 <your-proxy> 的直连
# （`get_s22.sh` 抬头就写了这条），在 WSL 里跑这个脚本只会拿到 22 个 FAIL，
# 那是网络，不是几何被改过。
#
# 退出码：0 = 22/22 逐字节相同且各已落档原件抬头记的 sha 也相同；
#         1 = 有任何不一致（几何被改过或抬头对不上）——**这种情况必须人工查，不许重跑盖掉**；
#         2 = 一条都没取回来（网络/代理问题）⇒ 未测，不是通过。
set -u
cd /e/Project/GAMESS 2>/dev/null || cd "$(dirname "$0")/../.." || exit 2
export HTTPS_PROXY=http://<your-proxy>
BASE="https://raw.githubusercontent.com/grimme-lab/GMTKN55/v1/S22"
TMP="scratch/lit/upstream_check"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="evidence/common_grid/${STAMP}_verify_s22_xyz_upstream.out"
mkdir -p "$TMP"

echo "# S22 官方几何与上游 tag v1 的逐字节复核  起始 $(date -u +%FT%TZ)" > "$OUT"
echo "# 上游 $BASE/<NN>/struc.xyz（与 2026-10-11 取回时同一个 tag v1，同一份 get_s22.sh）" >> "$OUT"
echo "# 本地 scratch/lit/s22/S22_NN.xyz；临时副本 $TMP/NN.xyz（可删，产物只是这份 .out）" >> "$OUT"

ok=0; bad=0; net=0
for n in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22; do
    if ! curl -sf --max-time 30 -o "$TMP/$n.xyz" "$BASE/$n/struc.xyz"; then
        printf "   S22_%s  取回失败（网络/代理）—— 未测\n" "$n" >> "$OUT"
        net=$((net+1)); continue
    fi
    up=$(sha256sum "$TMP/$n.xyz"      | cut -d' ' -f1)
    lo=$(sha256sum "scratch/lit/s22/S22_$n.xyz" | cut -d' ' -f1)
    # 已落档的证书原件抬头自己记过 sha：三方（上游 / 盘上 / 原件自报）必须同值
    arc=$(grep -h "^# sha256 S22_$n.xyz  " evidence/common_grid/*"_s22_full_certificate_S22_${n}_l1_small.out" 2>/dev/null | tail -1 | sed 's/.*= //')
    if [ "$up" = "$lo" ]; then
        tag="逐字节相同"
        [ -n "$arc" ] && [ "$arc" != "$lo" ] && tag="盘上=上游，但**证书抬头对不上**" && bad=$((bad+1))
        [ -n "$arc" ] && [ "$arc" = "$lo" ] && tag="$tag，证书抬头同值（三方一致）"
        [ -z "$arc" ] && tag="$tag，该格尚无已落档原件（不参与三方）"
        [ "$tag" != "盘上=上游，但**证书抬头对不上**" ] && ok=$((ok+1))
    else
        tag="!! 不一致：上游 $up vs 盘上 $lo"
        bad=$((bad+1))
    fi
    printf "   S22_%s  %s\n" "$n" "$tag" >> "$OUT"
done

{
  echo
  echo "# 计数：三方/两方一致 $ok，不一致 $bad，取不回 $net"
  if [ "$bad" -gt 0 ]; then
    echo "VERDICT NOTCLEAN —— 有格几何与上游不同 ⇒ 先查是哪一侧的字节变了，**不许重跑盖掉证据**"
    echo "# exit=1 at $(date -u +%FT%TZ)" >> "$OUT"; echo 1 > "$OUT.rc"; exit 1
  fi
  if [ "$ok" -lt 22 ]; then
    echo "VERDICT 未测（只核了 $ok/22，取回失败 $net 条）—— 这不是通过"
    echo "# exit=2 at $(date -u +%FT%TZ)" >> "$OUT"; echo 2 > "$OUT.rc"; exit 2
  fi
  echo "VERDICT OK —— 22/22 与上游 tag v1 逐字节相同；已落档各格的证书抬头 sha 三方一致"
} >> "$OUT"
echo "# exit=0 at $(date -u +%FT%TZ)" >> "$OUT"
echo 0 > "$OUT.rc"
echo "wrote $OUT rc=0"
exit 0
