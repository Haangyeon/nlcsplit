#!/usr/bin/env bash
# 取回 SNNU 51083（小体系 aug-cc-pVDZ 泛函反泊松）并入库。
# 这一份在版本库里（不是 scratch/）：PROGRESS 指着它，换机器/换客户端也得能一条命令收档。
# 规矩：先问远端 sha256 与 UTC mtime，再 scp，再本地比哈希；不一致就地退出，不拼终端回显。
set -euo pipefail
cd /e/Project/GAMESS
# 在任何 ssh 之前先建目录：ssh 的 stdout 就重定向进 scratch/，全新克隆没有这层目录会当场失败
mkdir -p scratch/remote
# 远端路径写死成绝对路径：`~` 在本地会展开成 Windows 的家目录，那是本仓记过的那类"落点错"
RD=/home/haangyeon/nlcc-snnu/out_dftavdz_small

echo "== 远端状态与指纹 =="
ssh -o ConnectTimeout=25 -o BatchMode=yes snnu \
  "squeue -u haangyeon -o '%.8i %.6T %.8M'; \
   cd $RD && sha256sum ./dft_cp_avdz.log ./sbatch_51083.out; \
   echo \"log_mtime_utc=\$(date -u -r ./dft_cp_avdz.log +%Y%m%dT%H%M)Z\"; \
   tail -3 ./dft_cp_avdz.log" > scratch/harvest_remote.txt 2>scratch/harvest_remote.err
cat scratch/harvest_remote.txt

# 作业还在跑就别收：半截文件入库比不入库更糟
if grep -q "RUNNIN" scratch/harvest_remote.txt; then
  echo "STILL_RUNNING - 不收，等它结束"; exit 6
fi
# 泛函侧那三行没打全就说明生产者死在中途：那份是失败档，名字要写清楚
if ! grep -q "DONE DFT_SET=small" scratch/harvest_remote.txt; then
  echo "NO_DONE_MARKER - 这份只能当失败档收，正文不许引它的数"; exit 7
fi

LOGSHA=$(awk '/dft_cp_avdz.log$/{print $1}' scratch/harvest_remote.txt | head -1)
OUTSHA=$(awk '/sbatch_51083.out$/{print $1}' scratch/harvest_remote.txt | head -1)
TS=$(grep -oE 'log_mtime_utc=[0-9T]+Z' scratch/harvest_remote.txt | cut -d= -f2)
# TS 形如 20261004T0352Z —— 保留那个 Z：本仓刚记过档名里的 Z 不可当装饰，它是"这条是 UTC"的声明
[ -n "$LOGSHA" ] && [ -n "$OUTSHA" ] && [ -n "$TS" ] || { echo "PARSE_FAIL - 指纹没读出来"; exit 8; }
case "$TS" in *Z) ;; *) echo "TS 不带 Z，拒绝按猜的时区命名: $TS"; exit 8;; esac

echo "== scp =="
scp -o ConnectTimeout=25 -q "snnu:$RD/dft_cp_avdz.log" scratch/remote/small2_dft_cp_avdz.log
scp -o ConnectTimeout=25 -q "snnu:$RD/sbatch_51083.out" scratch/remote/small2_sbatch_51083.out

echo "== 本地核哈希 =="
G1=$(sha256sum scratch/remote/small2_dft_cp_avdz.log | cut -d' ' -f1)
G2=$(sha256sum scratch/remote/small2_sbatch_51083.out | cut -d' ' -f1)
[ "$G1" = "$LOGSHA" ] || { echo "LOG HASH MISMATCH: $G1 vs $LOGSHA"; exit 9; }
[ "$G2" = "$OUTSHA" ] || { echo "OUT HASH MISMATCH: $G2 vs $OUTSHA"; exit 9; }
echo "both identical: $G1 / $G2"

D1="evidence/l2cp/${TS}_snnu51083-dft_cp_avdz_small.out"
D2="evidence/l2cp/${TS}_snnu51083-sbatch.out"
cp scratch/remote/small2_dft_cp_avdz.log "$D1"
cp scratch/remote/small2_sbatch_51083.out "$D2"
sha256sum "$D1" "$D2"
git add "$D1" "$D2"
echo "STAGED: $D1 $D2"
echo "== 下一步（人工）：MANIFEST 最后重生成、改 §3.2 与 S31、跑 md2tex 与 claim-gate 再提交 =="
