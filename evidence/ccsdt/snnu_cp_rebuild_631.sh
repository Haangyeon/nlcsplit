#!/usr/bin/env bash
# <CLUSTER>：鬼函数修正后的 CCSD(T) 反泊松阶梯重跑，第一批 = 6-31g*，八个体系，冻核与全电子各一次。
#
# 为什么整条要重跑。step_m_ccsdt.py 的第一版把单体建在**自己的**基组里（少了对方的函数），
# 那算出来的是未校正的相互作用能，而栏目标题写的是 dE_CP。水二聚体上两者差 1.98 kcal/mol
# （-6.8559 对 -4.8789，本机 2026-10-03 实测），足以把 §3.2 里"泛函偏深"读成"偏浅"。
# 修的是单体那一侧，复合物那一侧一个字节没动 —— 所以阶段 0 拿复合物自己的 RHF 参考当守卫：
# 它验的正是部署本身（几何解析、基组、PySCF 版本、积分），而这条守卫的值不受本次修改影响，
# 换句话说，如果它还是过了，那么跑完之后新旧档案之间唯一的差别就只能来自鬼函数。
#
# 顺序由便宜到贵，为的是作业被砍时先拿到能填表的那几行。
set -u
ROOT=$HOME/nlcc-<CLUSTER>
RUN=$ROOT/.publish/nlcsplit
cd "$ROOT" || { echo "NO_ROOT"; exit 3; }
[ -f "$RUN/nlcsplit/step_m_ccsdt.py" ] || { echo "NO_SCRIPT $RUN"; exit 3; }
PY=$(command -v python3)
export PYTHONPATH="$RUN"
export S22DIR="$ROOT/scratch/lit/s22"
export OMP_NUM_THREADS=16
export PYTHONUTF8=1
AVAIL_KB=$(awk '/MemAvailable/{print $2; exit}' /proc/meminfo)
export MAXMEM_MB=$(( AVAIL_KB * 70 / 100 / 1024 ))
LOGD=$ROOT/out_rebuild631; mkdir -p "$LOGD"
echo "== host=$(hostname) cpus=$(nproc) threads=$OMP_NUM_THREADS maxmem=${MAXMEM_MB}MB =="
$PY -c "import sys,pyscf;print(sys.version.split()[0],'pyscf',pyscf.__version__)" \
  || { echo IMPORT_FAIL; exit 4; }
sha256sum "$RUN/nlcsplit/step_m_ccsdt.py"

rhf_ref() {   # <体系> <归档 RHF 参考 (Ha)> —— 复合物那一侧，与本次修改无关
  $PY - "$1" "$2" <<'PYR'
import os, sys
from nlcsplit import geomlib, step_m_ccsdt
name, expect = sys.argv[1], float(sys.argv[2])
atoms, frags = geomlib.s22_system(name, os.environ["S22DIR"])
mol = step_m_ccsdt.build([a[0] for a in atoms], [a[1] for a in atoms], "6-31g*")
mf = mol.RHF(); mf.max_memory = int(os.environ["MAXMEM_MB"]); mf.kernel()
d = abs(mf.e_tot - expect)
print("guard nao=%-4d %s RHF %.10f vs archived %.10f -> %.2e %s"
      % (mol.nao, name, mf.e_tot, expect, d,
         "PASS" if (mf.converged and d <= 1e-8) else "FAIL"))
sys.exit(0 if (mf.converged and d <= 1e-8) else 1)
PYR
}

rhf_ref "水二聚体" -152.0272662226 || { echo "GUARD_FAIL_water"; exit 5; }
rhf_ref "苯二聚体(A)" -461.3980350170 || { echo "GUARD_FAIL_sandwich"; exit 5; }
echo "GUARDS_PASS  (两条都是复合物的 RHF，容差 1e-8 Ha)"
echo

run() {   # <标签> <体系列表> [基组]
  local tag=$1 syslist=$2 basis=${3:-6-31g*} f
  f=$LOGD/ccsdt_${tag}.log
  echo "== $tag  systems=$syslist  basis=$basis  @ $(date -u +%FT%TZ) =="
  SYSTEMS="$syslist" BASES="$basis" $PY -u "$RUN/nlcsplit/step_m_ccsdt.py" > "$f" 2>&1
  echo "   rc=$? lines=$(wc -l < "$f")"
  awk '$1=="CCSD(T)"{printf "   %-8s %18s %18s %14s\n",$1,$2,$3,$4}' "$f"
  grep -E "单体 nao" "$f" | head -4
  echo "   @ $(date -u +%FT%TZ)"
}

run three_dimers "水二聚体,氨二聚体,甲烷二聚体"
run pi_three     "苯-水,苯-氨,苯-甲烷"
run dimer_A      "苯二聚体(A)"
run dimer_B      "苯二聚体(B)"

echo "== ALL_DONE 6-31g* @ $(date -u +%FT%TZ) =="
cd "$LOGD" && sha256sum ccsdt_*.log
