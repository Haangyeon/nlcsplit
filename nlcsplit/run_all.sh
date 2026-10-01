#!/bin/bash
# nlcsplit 的复现驱动：一张表对应一个脚本，这个文件负责"谁能被一键跑出来"。
#
# 为什么重写：旧版只认 step1/step2/step_c/step_b 四个，而母仓里有十三个 step_*.py——
# 也就是说**主表 step_h_s22.py、标度阶梯 step_j_scaling.py、布居数表 step_k_population.py
# 从来不在任何入口里**。软件文写"每个表映射一个脚本"，读者拿到的驱动器却跑不出那几个表。
# 旧版还把 `cd <REPO>` 写死在脚本里（发布时靠脱敏副本蒙过去）。
#
# 纪律不变：
#  - 单实例锁：用 mkdir 的可移植锁，不用 flock（flock 在 macOS / Git Bash 上不存在，
#    本机的 Windows 侧就是第一个踩到的地方；两个 runner 同跑会互相覆盖证据，真发生过）
#  - **每个随包发布的 step_*.py 都必须登记在下面的 CMD 表里**：导出闸门 X 会拿发布树
# 与这张表对账，漏一个就拒绝出货。这条纪律是 2026-10-01 补的——上一次修好漏登记时
# 没留下任何守卫，于是第 14 个脚本（step_m_ccsdt.py）进来就重演了一遍。
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
  [step_m]="nlcsplit/step_m_ccsdt.py"
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
  [step_m]="需要 S22 官方几何（同 step_h）+ pyscf 的 cc/mp 模块；默认只跑水二聚体 6-31g*（约数分钟），SYSTEMS=/BASES= 可扩到氨/甲烷与 aug-cc-pVDZ，那一档以十分钟计"
  [figures]="需要 matplotlib；写 figs/fig{1,2,3,4}_*.png（fig4 的数取自 evidence/ccsdt 与 orca_widen 的归档 stdout，读不全就拒绝出图）"
)
declare -A PRESETS=(
  [quick]="step1 step2 step_d step_e step_f"
  [verify]="step1 step2 step_b step_d step_e step_f step_g step_i figures"
  [tables]="step_h"
  [all-argless]="step1 step2 step_b step_d step_e step_f step_g step_h step_i figures"
)

if [ "${1:-}" = "--list" ]; then
  echo "组："
  for g in "${!PRESETS[@]}"; do printf '  %-12s = %s\n' "$g" "${PRESETS[$g]}"; done
  echo "单脚本 tag：$(printf '%s ' "${!CMD[@]}")"
  echo "需要参数：$(printf '%s ' "${!NEEDS_ARG[@]}")"
  for t in "${!NOTE[@]}"; do echo "  前置 $t：${NOTE[$t]}"; done
  exit 0
fi

LOCKDIR="${NLCSPLIT_RUNNER_LOCKDIR:-/tmp/nlcsplit_runner.lock.d}"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
    echo "另一个 runner 还持有 $LOCKDIR，本次退出（确认它已死再 rmdir）"; exit 1
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null' EXIT

TAGS=("$@"); [ ${#TAGS[@]} -eq 0 ] && TAGS=(${PRESETS[quick]})
[ $# -eq 1 ] && [ -n "${PRESETS[$1]+x}" ] && TAGS=(${PRESETS[$1]})

TS=$(date -u +%Y%m%dT%H%M%SZ)
rc_all=0
for t in "${TAGS[@]}"; do
    if [ -z "${CMD[$t]+x}" ]; then echo "[runner] 未知 tag：$t（--list 看清单）"; rc_all=1; continue; fi
    if [ -n "${NEEDS_ARG[$t]+x}" ]; then
        echo "[runner] 跳过 $t：${NEEDS_ARG[$t]}"; rc_all=1; continue
    fi
    f="$LOGDIR/${TS}_${t}.out"
    echo "[runner] $t -> $f  ($(date +%T))  ${NOTE[$t]:-}"
    # 每个 step 都用**自己的默认值**跑：NCSYS 在 step_b 意为"体系列表"、在 step_g 意为"基组表"，
    # NCLV/NCPC 是全局档位——只要有一个从外面漏进来，下一个脚本就会算在另一套配置上，
    # 而日志里看不出区别。要改配置就单独直接调那个脚本，别经过这里。
    unset NCSYS NCLV NCPC
    {
      echo "=== runner env @ $(date -u +%FT%TZ) ==="
      echo "OMP_NUM_THREADS=$OMP_NUM_THREADS  tag=$t  cmd=${CMD[$t]}"
      echo "残留的 NC*/S22DIR：$(env | grep -E '^(NCSYS|NCLV|NCPC|S22DIR)=' | tr '\n' ' ')"
      echo "（step_d_floor 自己会把 BLAS 线程压到 2，与上面的 4 不一致是已知且故意的：改它会换 BLAS 归约顺序，那些数已带哈希归档）"
      echo "=== 以下为脚本原文输出 ==="
    } > "$f"
    # `timeout` 在 macOS 与 Git Bash 上也不存在；没有它就直接跑，但把"没有超时保护"写进日志，
    # 别让读者以为卡住的那一步受着 5400 s 的约束。
    if command -v timeout >/dev/null 2>&1; then
        RUN=(timeout "${RUN_ALL_TIMEOUT:-5400}" python3 -u "${CMD[$t]}")
    else
        echo "（本机没有 timeout，本步不受 ${RUN_ALL_TIMEOUT:-5400} s 上限保护）" >> "$f"
        RUN=(python3 -u "${CMD[$t]}")
    fi
    "${RUN[@]}" >> "$f" 2>&1
    rc=$?
    echo "$TS $t rc=$rc $(wc -l < "$f") lines $f" >> "$LOGDIR/MANIFEST.txt"
    [ $rc -ne 0 ] && { echo "[runner] $t rc=$rc  见 $f"; rc_all=1; }
done
echo "[runner] done $(date +%T)  overall_rc=$rc_all"
exit $rc_all
