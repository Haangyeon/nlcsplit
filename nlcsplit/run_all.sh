#!/bin/bash
# nlcsplit 的复现驱动：一张表对应一个脚本，这个文件负责"谁能被一键跑出来"。
#
# 为什么重写：旧版只认 step1/step2/step_c/step_b 四个，而母仓里有十三个 step_*.py——
# 也就是说**主表 step_h_s22.py、标度阶梯 step_j_scaling.py、布居数表 step_k_population.py
# 从来不在任何入口里**。软件文写"每个表映射一个脚本"，读者拿到的驱动器却跑不出那几个表。
# 旧版还把 `cd /mnt/e/Project/GAMESS` 写死在脚本里（发布时靠脱敏副本蒙过去）。
#
# 纪律不变：
#  - flock 单实例锁（两个 runner 会互相覆盖证据，本机真的发生过）
#  - 每个脚本的输出落到带 UTC 时间戳的新文件，不就地覆盖，并登记进 logs/MANIFEST.txt
#  - 默认只跑**不需要参数、不需要可选依赖、不需要空载机器**的那一组；
#    其余按组显式点，因为"跑错了把机子占两小时"比"少跑一个"更糟
#
# 用法:  bash nlcsplit/run_all.sh                 # = quick
#        bash nlcsplit/run_all.sh tables          # 主表（要先有 S22 几何）
#        bash nlcsplit/run_all.sh step_d step_e   # 手工点
#        bash nlcsplit/run_all.sh --list          # 列清单与前置条件，不执行
set -u

cd "$(dirname "$(readlink -f "$0")")/.." || { echo "找不到仓库根"; exit 1; }
export PYTHONPATH=.
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
LOGDIR=nlcsplit/logs
mkdir -p "$LOGDIR"
LOCK=/tmp/nlcsplit_runner.lock
if ! flock -n 9; then echo "另一个 runner 还在持锁，本次退出"; exit 1; fi 9>"$LOCK"

# tag -> 命令。前置条件写在这里，不在这里自动准备（下载/长算应由人决定）。
declare -A CMD=(
  [step1]="nlcsplit/step1_validate.py"
  [step2]="nlcsplit/step2_convergence.py"
  [step_b]="nlcsplit/step_b_scan.py"
  [step_c]="nlcsplit/step_c_relaxation.py"
  [step_d]="nlcsplit/step_d_floor.py"
  [step_e]="nlcsplit/step_e_kernel.py"
  [step_f]="nlcsplit/step_f_dispersion.py"
  [step_g]="nlcsplit/step_g_basis.py"
  [step_h]="nlcsplit/step_h_s22.py"
  [step_i]="nlcsplit/step_i_gridrepr.py"
  [step_j]="nlcsplit/step_j_scaling.py"
  [step_k]="nlcsplit/step_k_population.py"
  [step_l]="nlcsplit/step_l_sweep_compare.py"
  [figures]="nlcsplit/figures.py"
)
# 需要命令行参数的：不给参数就**拒绝跑**，而不是让它拿默认值出一个看起来对的数。
declare -A NEEDS_ARG=(
  [step_k]="LEVEL (0..9)；例：bash nlcsplit/run_all.sh step_k 3"
  [step_l]="MAXLEVEL (0..9)；O(N^2)，level 8 单档已数十分钟"
)
declare -A NOTE=(
  [step_c]="需要 scipy（pip install nlcsplit[relax]）；几何松弛，非主表依赖"
  [step_h]="需要 S22 官方几何：先 bash nlcsplit/tools/get_s22.sh；这是正文表 2/3 的来源"
  [step_j]="墙钟标度，**必须空载**：脚本自己带 R 态外部任务计数，脏样本会标 valid_timing=false"
  [step_l]="与被比脚本同为 O(N^2)，level 9 以小时计"
  [figures]="需要 matplotlib；写 figs/fig{1,2,3}_*.png"
)
declare -A GROUPS=(
  [quick]="step1 step2 step_d step_e step_f"
  [verify]="step1 step2 step_b step_d step_e step_f step_g step_i figures"
  [tables]="step_h"
  [all-argless]="step1 step2 step_b step_d step_e step_f step_g step_h step_i figures"
)

if [ "${1:-}" = "--list" ]; then
  echo "组："
  for g in "${!GROUPS[@]}"; do printf '  %-12s = %s\n' "$g" "${GROUPS[$g]}"; done
  echo "单脚本 tag：$(printf '%s ' "${!CMD[@]}")"
  echo "需要参数：$(printf '%s ' "${!NEEDS_ARG[@]}")"
  for t in "${!NOTE[@]}"; do echo "  前置 $t：${NOTE[$t]}"; done
  exit 0
fi

TAGS=("$@"); [ ${#TAGS[@]} -eq 0 ] && TAGS=($([ -n "${GROUPS[quick]}" ] && echo "${GROUPS[quick]}"))
[ $# -eq 1 ] && [ -n "${GROUPS[$1]+x}" ] && TAGS=(${GROUPS[$1]})

TS=$(date -u +%Y%m%dT%H%M%SZ)
rc_all=0
for t in "${TAGS[@]}"; do
    if [ -z "${CMD[$t]+x}" ]; then echo "[runner] 未知 tag：$t（--list 看清单）"; rc_all=1; continue; fi
    if [ -n "${NEEDS_ARG[$t]+x}" ]; then
        echo "[runner] 跳过 $t：${NEEDS_ARG[$t]}"; rc_all=1; continue
    fi
    f="$LOGDIR/${TS}_${t}.out"
    echo "[runner] $t -> $f  ($(date +%T))  ${NOTE[$t]:-}"
    timeout "${RUN_ALL_TIMEOUT:-5400}" python3 -u "${CMD[$t]}" > "$f" 2>&1
    rc=$?
    echo "$TS $t rc=$rc $(wc -l < "$f") lines $f" >> "$LOGDIR/MANIFEST.txt"
    [ $rc -ne 0 ] && { echo "[runner] $t rc=$rc  见 $f"; rc_all=1; }
done
echo "[runner] done $(date +%T)  overall_rc=$rc_all"
exit $rc_all
