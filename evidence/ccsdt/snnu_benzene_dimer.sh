#!/usr/bin/env bash
# <CLUSTER> 上的苯二聚体(A) CCSD(T) 锚点。
#
# 为什么单独再来一跑。evidence/ccsdt/20261002T043400Z 那一跑按同一理由把苯二聚体排除在
# 押机时之外（192 AO，比苯系的 114-118 AO 大一档，当时的墙钟外推不确定），所以 §3.2 现在
# 只有六个体系有相关参考。苯二聚体(A) 正是主表里"苯 sandwich"那一行——dE_NLC 已经报过、
# 归属跨度已经报过，唯独没有波恩-奥本海默那一侧的数。补上它，锚点就从六个变成七个，
# 而且第七个是色散主导的旗舰体系。
#
# 顺序照旧：先把两个便宜的校验跑完，过了才把机时押在 192 AO 上。
#   阶段 0  水二聚体，复现母仓归档的 -6.856（同一 call path、同一约定；红=通路有问题）
#   阶段 1  苯-甲烷，复现 20261002T043400Z 的 -1.0583（跨作业确定性；红=别押机时）
#   阶段 2  苯二聚体(A)，本体
set -u
ROOT=$HOME/nlcc-<CLUSTER>
RUN=$ROOT/.publish/nlcsplit          # 随包发布的那棵树里有 step_m_ccsdt.py
cd "$ROOT" || { echo "NO_ROOT"; exit 3; }
[ -f "$RUN/nlcsplit/step_m_ccsdt.py" ] || { echo "NO_SCRIPT $RUN"; exit 3; }
PY=$(command -v python3)
export PYTHONPATH="$RUN"
export S22DIR="$ROOT/scratch/lit/s22"
export OMP_NUM_THREADS=32
# 192 AO 的 (μν|λσ) 一体化存就要 192^4×8 B ≈ 10.9 GB，比苯系那一档大得多，所以内存
# 不写死：按节点当下真的还剩多少取 80%。本集群 RealMemory 声明是假的（=1），
# Slurm 不会替我限，超了就是 OOM。
AVAIL_KB=$(awk '/MemAvailable/{print $2; exit}' /proc/meminfo)
MAXMEM_MB=$(( AVAIL_KB * 80 / 100 / 1024 ))
export MAXMEM_MB
LOGD=$ROOT/out; mkdir -p "$LOGD"
echo "== host=$(hostname) cpus=$(nproc) threads=$OMP_NUM_THREADS maxmem=${MAXMEM_MB}MB (MemAvailable=$((AVAIL_KB/1024))MB) =="
$PY -c "import sys,pyscf,numpy,scipy;print(sys.version.split()[0],'pyscf',pyscf.__version__,pyscf.__file__)" || { echo IMPORT_FAIL; exit 4; }
echo "== s22 文件数=$(ls "$S22DIR" | wc -l) =="

# chk <log> <期望值> <容差> <标签>：从 CCSD(T) 行取第 4 列，与期望比对。
# 取不到数一律算失败——"没解析出来"和"解析出来且相符"在两处归档里长得一样，
# 那正是本目录上一条注释记下的失效形态。
chk() {
  local f=$1 ref=$2 tol=$3 tag=$4
  local v
  v=$(awk '$1=="CCSD(T)" && $4 ~ /^-/ {print $4; exit}' "$f")
  echo "$tag ccsdT=[$v]"
  $PY - "$v" "$ref" "$tol" "$tag" <<'PYCHK'
import sys
tag = sys.argv[4]
try:
    x, ref, tol = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
except Exception:
    print("guard: %s 没解析出数 —— 校验不通过（不是 0，是没有值）" % tag); sys.exit(1)
d = abs(x - ref)
print("guard: %s |%.4f - (%.4f)| = %.4f %s %.4f -> %s"
      % (tag, x, ref, d, "<=" if d <= tol else ">", tol, "PASS" if d <= tol else "FAIL"))
sys.exit(0 if d <= tol else 1)
PYCHK
}

for spec in "水二聚体|-6.856|0.0015|water" "苯-甲烷|-1.0583|0.0015|benzene-methane"; do
  IFS='|' read -r s ref tol tag <<< "$spec"
  f=$LOGD/dimer_validate_${tag}.log
  SYSTEMS="$s" BASES="6-31g*" $PY -u "$RUN/nlcsplit/step_m_ccsdt.py" > "$f" 2>&1
  echo "== validate $s rc=$? @ $(date -u +%FT%TZ) =="
  if ! chk "$f" "$ref" "$tol" "$tag"; then
    echo "GUARD_FAIL($tag)：不跑苯二聚体（通路/版本/约定有问题，别押机时）"; exit 5
  fi
done
echo "GUARDS_PASS"

f=$LOGD/ccsdt_benzene_dimer_A.log
echo "== running 苯二聚体(A) @ $(date -u +%FT%TZ) =="
SYSTEMS="苯二聚体(A)" BASES="6-31g*" $PY -u "$RUN/nlcsplit/step_m_ccsdt.py" > "$f" 2>&1
rc=$?
echo "== 苯二聚体(A) rc=$rc lines=$(wc -l < "$f") @ $(date -u +%FT%TZ) =="
grep -E "nao|RHF=|CCSD=|MP2|CCSD\(T\)|Traceback|Error" "$f" | tail -20
cd "$LOGD" && sha256sum dimer_validate_*.log ccsdt_benzene_dimer_A.log
echo "== $rc DIMER_DONE =="
