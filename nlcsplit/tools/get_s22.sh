#!/bin/bash
# 取 GMTKN55 官方仓库(grimme-lab/GMTKN55, tag v1)里的 S22 复合物结构文件。
# 用途：给 nlcsplit 的 S22 子集提供**可引的官方几何**，避免自己构造二聚体坐标。
# 出站：本机 WSL 无直连，走 Windows 侧代理 <your-proxy>（实测 raw.githubusercontent 200）。
cd "$(dirname "$0")/.." || exit 1
mkdir -p lit/s22
export HTTPS_PROXY="${HTTPS_PROXY:-}"   # 需要时自行 export，不需要则空值即直连
ok=0
for n in 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22; do
    url="https://raw.githubusercontent.com/grimme-lab/GMTKN55/v1/S22/${n}/struc.xyz"
    if curl -sf --max-time 30 -o "lit/s22/S22_${n}.xyz" "$url"; then
        ok=$((ok+1))
    else
        echo "FAIL $n"
    fi
done
echo "取回 $ok/22 个结构文件"
