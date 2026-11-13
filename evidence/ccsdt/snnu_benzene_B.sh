#!/usr/bin/env bash
# <CLUSTER>：苯二聚体(B)（S22_20，平行位移几何）—— 八个体系里最后一个没有反泊松参考的。
#
# 为什么补它。§1 与 §4.1 现在写的是"反泊松覆盖七个体系，剩的只有苯二聚体(B)"。
# 它是 S22 里与 sandwich 并列的另一个苯二聚体几何，主表有它的 dE_NLC 与归属跨度，
# 独独没有波恩-奥本海默那一侧。这一跑同时补齐 CCSD(T) 与 omegaB97X-V 的反泊松，
# 补上之后八个体系全有同一约定的参考，那句话就不用再带一个"剩"字。
#
# 顺序照旧，两道守卫都过了才押机时：
#   阶段 0  水二聚体 -6.856（通路）
#   阶段 1  苯二聚体(A) CCSD(T) 冻核 -1.4999（跨作业确定性；这是同一次 CCSD(T) 的第二个几何）
#   阶段 2  苯二聚体(B) CCSD(T)（冻核 + 全电子）
#   阶段 3  苯二聚体(B) DFT 反泊松（level 2 + level 1）
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
export MAXMEM_MB=$(( AVAIL_KB * 70 / 100 / 1024 ))
LOGD=$ROOT/out; mkdir -p "$LOGD"
echo "== host=$(hostname) cpus=$(nproc) threads=$OMP_NUM_THREADS maxmem=${MAXMEM_MB}MB =="
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

f=$LOGD/b_validate_water.log
SYSTEMS="水二聚体" BASES="6-31g*" $PY -u "$RUN/nlcsplit/step_m_ccsdt.py" > "$f" 2>&1
chk "$f" -6.856 0.0015 water || { echo GUARD_FAIL_water; exit 5; }

f=$LOGD/b_validate_dimerA.log
SYSTEMS="苯二聚体(A)" BASES="6-31g*" $PY -u "$RUN/nlcsplit/step_m_ccsdt.py" > "$f" 2>&1
chk "$f" -1.4999 0.0015 benzene-dimer-A || { echo GUARD_FAIL_dimerA; exit 5; }
echo GUARDS_PASS

f=$LOGD/ccsdt_benzene_dimer_B.log
echo "== running 苯二聚体(B) CCSD(T) @ $(date -u +%FT%TZ) =="
SYSTEMS="苯二聚体(B)" BASES="6-31g*" $PY -u "$RUN/nlcsplit/step_m_ccsdt.py" > "$f" 2>&1
echo "   rc=$? lines=$(wc -l < "$f")"; awk '$1=="CCSD(T)"{print "   ",$0}' "$f"

f=$LOGD/dft_dimer_B.log
echo "== running 苯二聚体(B) DFT 反泊松 @ $(date -u +%FT%TZ) =="
$PY -u "$ROOT/dft_cp_dimer_B.py" > "$f" 2>&1
echo "   rc=$? lines=$(wc -l < "$f")"; grep -E "LEVEL=|guard" "$f" | tail -4
echo "== $(date -u +%FT%TZ) B_ALL_DONE =="
cd "$LOGD" && sha256sum b_validate_*.log ccsdt_benzene_dimer_B.log dft_dimer_B.log
