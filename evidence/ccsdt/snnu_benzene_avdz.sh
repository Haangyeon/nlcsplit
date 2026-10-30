#!/usr/bin/env bash
# <CLUSTER>：三个苯系复合物在 aug-cc-pVDZ 下的 CCSD(T) 反泊松阶梯。
#
# 为什么这一跑改变正文的主张强度。main.md §3.2 的核心警告是"两个同量级的效应互相分不开"：
# 只换基组时相关参考自己的移动，比泛函对它的偏差更大。这句话目前在三个氢键体系上是
# **量过的**（水/氨/甲烷在 6-31g* 与 aug-cc-pVDZ 两档都有，见
# evidence/ccsdt/20261001T000400Z_stepm_three_systems_avdz.out），而苯系只有 6-31g* 一档，
# 所以对那三个 π 体系我只能说"偏差没有统一符号"，不能说"基组效应压过它"。
# 补上 aug-cc-pVDZ 之后，同一个 span 比较在六个体系上成立，图 3 的判据也才扩得过去。
#
# 顺序照旧：先复现已归档的数，红了就不押机时。守卫是自测过的形态
# （正确值 PASS、错值 FAIL、解析不到 FAIL），不再靠"看起来打印了个数"。
set -u
ROOT=$HOME/nlcc-<CLUSTER>
RUN=$ROOT/.publish/nlcsplit
cd "$ROOT" || { echo "NO_ROOT"; exit 3; }
[ -f "$RUN/nlcsplit/step_m_ccsdt.py" ] || { echo "NO_SCRIPT $RUN"; exit 3; }
PY=$(command -v python3)
export PYTHONPATH="$RUN"
export S22DIR="$ROOT/scratch/lit/s22"
export OMP_NUM_THREADS=16
AVAIL_KB=$(awk '/MemAvailable/{print $2; exit}' /proc/meminfo)
MAXMEM_MB=$(( AVAIL_KB * 70 / 100 / 1024 ))     # 与苯二聚体那一跑错开，别把节点内存一起吃掉
export MAXMEM_MB
LOGD=$ROOT/out; mkdir -p "$LOGD"
echo "== host=$(hostname) cpus=$(nproc) threads=$OMP_NUM_THREADS maxmem=${MAXMEM_MB}MB (MemAvailable=$((AVAIL_KB/1024))MB) =="
$PY -c "import sys,pyscf;print(sys.version.split()[0],'pyscf',pyscf.__version__)" || { echo IMPORT_FAIL; exit 4; }

chk() {   # <log> <期望> <容差> <标签>
  local f=$1 ref=$2 tol=$3 tag=$4 v
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

# 阶段 0：水二聚体 aug-cc-pVDZ，母仓归档 -5.248（冻核）
f=$LOGD/avdz_validate_water.log
SYSTEMS="水二聚体" BASES="aug-cc-pvdz" $PY -u "$RUN/nlcsplit/step_m_ccsdt.py" > "$f" 2>&1
echo "== validate water@avdz rc=$? @ $(date -u +%FT%TZ) =="
chk "$f" -5.248 0.0015 water-avdz || { echo "GUARD_FAIL：不跑苯系（版本/约定不是那一档）"; exit 5; }
echo "GUARD_PASS"

for s in 苯-水 苯-氨 苯-甲烷; do
  f=$LOGD/avdz_ccsdt_$s.log
  if [ -s "$f" ] && grep -q "CCSD(T)" "$f" && ! grep -q Traceback "$f"; then
    echo "skip $s（已有完成的 log）"; continue
  fi
  echo "== running $s @ aug-cc-pVDZ @ $(date -u +%FT%TZ) =="
  SYSTEMS="$s" BASES="aug-cc-pvdz" $PY -u "$RUN/nlcsplit/step_m_ccsdt.py" > "$f" 2>&1
  echo "   rc=$? lines=$(wc -l < "$f")"
  awk '$1=="CCSD(T)"{print "   ",$0}' "$f" | head -2
done
echo "== $(date -u +%FT%TZ) AVDZ_ALL_DONE =="
cd "$LOGD" && sha256sum avdz_*.log
