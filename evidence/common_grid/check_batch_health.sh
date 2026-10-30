#!/usr/bin/env bash
# 满 S22 本机批的健康检查：分清"在算"与"卡住"。判据是 CPU 时间是否在涨，不是文件大小。
#
# 为什么需要（2026-10-13 夜差点误判）：波三三格跑了 67 分钟没出结果，而它们的 `.out`
# 一直停在 611 字节——因为 `s22_full_certificate.py` 是**算完才打印**的。
# 只看文件大小就会以为卡死，进而想杀进程重跑；实际三个进程各占 ~5.4 核（etime 1:01 / time 5:31），
# 在老老实实算 24–26 原子的双重和。杀掉等于白扔一小时并且留下半份档。
# 本仓红线：不动正在跑的作业。要判断死活，用这个，而不是用"有没有输出"。
#
# 用法：bash evidence/common_grid/check_batch_health.sh
# 退出码：0 = 有 CPU 前进（在算）；1 = 一个进程都没有（批结束、没起，**或正卡在波与波之间的
#   barrier 上**——批的语义是"发满 par 个才 wait"，wait 完到下一波起之间有秒级空窗）；
#   3 = 有进程但 CPU 不前进（可疑，人工看）；2 = 跑错一侧（不是 WSL）或进不去仓根 ⇒ 未测，别读成"批结束"。
set -u
cd <REPO> || exit 2
# 先确认"跑对一侧"：批在 WSL 里跑，Windows 侧 Git Bash 的 `ps` 根本看不见那些进程，
# 于是本脚本会在 Windows 侧打出"没有 S22 批进程在跑"——那是**测不到**，不是批结束了。
# 2026-10-13 夜我自己就差点这么误读一次（同一时刻 WSL 里三个进程 CPU 各 4–5 小时、都在前进）。
if ! grep -qi microsoft /proc/version 2>/dev/null; then
  echo "跑错一侧：/proc/version 里没有 microsoft，这不是 WSL ⇒ 本机 ps 看不见批的进程。"
  echo "正确命令：wsl -e bash -c 'bash <REPO>/evidence/common_grid/check_batch_health.sh'"
  echo "VERDICT 未测（不是通过，也不是“批已结束”）"
  exit 2
fi
export LC_ALL=C
GAP=${GAP:-15}

snap() { ps -eo pid,etime,time,pcpu,args | grep '[s]22_full_certificate.py' \
           | awk '{print $1, $2, $3, $4, $NF}'; }
# 取 $NF（最后一个字段就是格号）而不是数第几列：`ps -eo ...,args` 里 args 从 $5 起，
# 而 "python3 -u s22_full_certificate.py 13" 自己还有三个词，写死 $5/$6 都会错——
# 我先前就分别错成显示 "python3" 和 "-u"。数最后一列不受命令行加词影响。

A=$(snap)
if [ -z "$A" ]; then echo "没有 S22 批进程在跑（批已结束或没启动）"; exit 1; fi
sleep "$GAP"
B=$(snap)

echo "# S22 批健康检查（间隔 ${GAP}s 取两次 CPU 时间；本脚本只读，不碰任何进程）"
printf "%-8s %-9s %-9s %-6s %s\n" PID ETIME CPU_TIME PCPU CELL
STALLED=0
# 用 here-doc 喂 while：这样循环体在当前 shell 里跑，STALLED 才留得住
# （`A | while` 会开子shell，判据就丢了——这是本脚本自己的"退出码只信自己落的"那条）。
while read -r pid etime cputime pcpu cell; do
  b=$(printf '%s\n' "$B" | awk -v p="$pid" '$1==p {print $3; exit}')
  a_sec=$(date -u -d "1970-01-01 $cputime" +%s 2>/dev/null || echo 0)
  b_sec=$(date -u -d "1970-01-01 ${b:-00:00:00}" +%s 2>/dev/null || echo 0)
  d=$(( b_sec - a_sec ))
  if [ "$d" -le 0 ]; then STALLED=1; fi
  printf "%-8s %-9s %-9s %-6s %-28s CPU前进=%ss %s\n" \
    "$pid" "$etime" "$cputime" "$pcpu" "$cell" "$d" \
    "$([ "$d" -gt 0 ] && echo OK || echo '可疑（CPU 没前进）')"
done <<EOF
$A
EOF

echo
echo "# 落档进度：$(ls evidence/common_grid/*s22_full_certificate*.out.rc 2>/dev/null | wc -l)/22 格已有 .rc"
if [ "$STALLED" -eq 0 ]; then
  echo "VERDICT RUNNING —— 每个进程的 CPU 时间都在前进，别动它"; exit 0
fi
echo "VERDICT STALL_SUSPECT —— 有进程 CPU 不前进。人工核对，**不要直接杀**（杀掉等于白扔已算时间并留半份档）"; exit 3
