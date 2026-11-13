#!/usr/bin/env bash
# <CLUSTER> 上的苯系 CCSD(T) 锚点。与 tcc 那份 LSF 脚本同一判据、同一顺序：
#   阶段 0 先复现母仓已归档的水二聚体数，过线才把机时押在苯上。
# 为什么换集群：tcc 那台 36 槽整机满（bhosts = closed_Full），而 main.md §3.2
# 那句"苯系本机跑不动"是**限制**不是结果 —— 有空闲 CPU 就该把它算掉。
set -u
ROOT=$HOME/nlcc-<CLUSTER>
RUN=$ROOT/.publish/nlcsplit          # 随包发布的那棵树里有 step_m_ccsdt.py
cd "$ROOT" || { echo "NO_ROOT"; exit 3; }
[ -f "$RUN/nlcsplit/step_m_ccsdt.py" ] || { echo "NO_SCRIPT $RUN"; exit 3; }
PY=$(command -v python3)
export PYTHONPATH="$RUN"
export S22DIR="$ROOT/scratch/lit/s22"
export OMP_NUM_THREADS=32 MAXMEM_MB=60000
LOGD=$ROOT/out; mkdir -p "$LOGD"
echo "== host=$(hostname) cpus=$(nproc) threads=$OMP_NUM_THREADS maxmem=${MAXMEM_MB}MB =="
$PY -c "import sys,pyscf,numpy,scipy;print(sys.version.split()[0],'pyscf',pyscf.__version__,pyscf.__file__)" || { echo IMPORT_FAIL; exit 4; }
echo "== s22 文件数=$(ls "$S22DIR" | wc -l) =="

# ---------- 阶段 0：水二聚体校验（母仓归档值 −6.856 kcal/mol，6-31g* 冻核反泊松）----------
WLOG=$LOGD/validate_water.log
SYSTEMS="水二聚体" BASES="6-31g*" $PY -u "$RUN/nlcsplit/step_m_ccsdt.py" > "$WLOG" 2>&1
wrc=$?
WVAL=$(awk '$1=="CCSD(T)" && $4 ~ /^-/ {print $4; exit}' "$WLOG")
echo "water_ccsdT=[$WVAL] rc=$wrc"
if ! $PY - "$WVAL" <<'PYCHK'
import sys
try:
    x = float(sys.argv[1])
except Exception:
    print("guard: 汇总行没解析出数 —— 校验不通过"); sys.exit(1)
ref, tol = -6.856, 0.0015          # 表只印三位小数，容差按打印位给
d = abs(x - ref)
print("guard: |%.4f - (%.3f)| = %.4f %s %.4f -> %s"
      % (x, ref, d, "<=" if d <= tol else ">", tol, "PASS" if d <= tol else "FAIL"))
sys.exit(0 if d <= tol else 1)
PYCHK
then echo "GUARD_FAIL：不跑苯（通路/版本/约定有问题，别押机时）"; exit 5; fi
echo "GUARD_PASS"

# ---------- 阶段 1-3：苯-水 → 苯-氨 → 苯-甲烷（AO 递增，每体系单独一份 log）----------
for s in 苯-水 苯-氨 苯-甲烷; do
  f=$LOGD/ccsdt_$s.log
  if [ -s "$f" ] && grep -q "== 汇总" "$f" && ! grep -q Traceback "$f"; then
    echo "skip $s（已有完成的 log）"; continue
  fi
  echo "== running $s @ $(date -u +%FT%TZ) =="
  SYSTEMS="$s" BASES="6-31g*" $PY -u "$RUN/nlcsplit/step_m_ccsdt.py" > "$f" 2>&1
  echo "   rc=$? lines=$(wc -l < "$f")"
  grep -E "^  苯" "$f" | tail -2
done
echo "== $(date -u +%FT%TZ) ALL_DONE =="
cd "$LOGD" && sha256sum *.log
