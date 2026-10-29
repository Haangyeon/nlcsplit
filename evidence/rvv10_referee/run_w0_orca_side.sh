#!/usr/bin/env bash
# W0 ORCA 侧跑法。纪律：
#   - 工作目录放 E:（本机规矩：长活/大产物不放 C:），每个 run 独立目录。
#   - 每个 run 自己写退出码到 <name>.out.rc（不走管道：`| tee` 后的 $? 曾把真值 1 写成 0 = 本仓坑 1）。
#   - %pal nprocs 4 固定（WSL 的 MPI 槽上限，16/8 起不来）；苯系要 %maxcore 4000。
#   - 归档 orca 自己写出的 .out 原文；取数交给 generator_w0_compare.py，
#     必须 SCF CONVERGED AFTER + ORCA TERMINATED NORMALLY + 恰好一行 `NL Energy, E(C,NL)` 才放行。
#     grep VV10/nonlocal 在 ORCA 输出里命中 0，不许拿它当存在性判据。
#   - 输入文件名带括号与间隔号，对 shell 不友好：这里一律在各自工作目录里重写成 mol.xyz / job.inp。
set -u
ORCA="$HOME/orca6/orca"
EV="/mnt/e/Project/GAMESS/evidence/rvv10_referee"
IN="$EV/orca_in"
RUN="$EV/orca_run"
mkdir -p "$RUN"
test -x "$ORCA" || { echo "找不到可执行 orca：$ORCA"; echo "# exit=2 at $(date -u +%FT%TZ)"; exit 2; }

nrun=0
fails=0
# rank 目录名由生成脚本决定（测试档 2026-10-12 从 SCAN_RVV10 改成 WB97M_V），
# 这里遍历 orca_in/ 下的实际目录，不把名字写死在本脚本里 —— 上一版写死过一次。
for rd in "$IN"/*/; do
  rank=$(basename "$rd")
  for inp in "$rd"*.inp; do
    dirn=$(basename "$inp" .inp)                 # 例：(H2O)2_mono0
    base=$(echo "$dirn" | tr -d '()' | tr '·' '-')
    wd="$RUN/${rank}__${base}"
    mkdir -p "$wd"
    cp -f "$(dirname "$inp")/${dirn}.xyz" "$wd/mol.xyz"
    {
      grep -v '^\* *xyzfile' "$inp" | grep -v '^#'   # 关键字卡原样，只换坐标文件引用
      echo "* xyzfile 0 1 mol.xyz"
    } > "$wd/job.inp"
    ( cd "$wd" && "$ORCA" job.inp > job.out 2>&1; echo $? > "$wd/job.rc" )
    rc=$(cat "$wd/job.rc")
    conv=$(grep -c "SCF CONVERGED AFTER" "$wd/job.out")
    norm=$(grep -c "ORCA TERMINATED NORMALLY" "$wd/job.out")
    # 门必须锚定行首标签：本份 ORCA 6.0.1 的输出里有**两行**含 "NL Energy" 子串
    # （`SC+NL Energy:` 是总能量、`NL Energy, E(C,NL) :` 才是要取的那项）。
    # 上一版按子串计数，把 12 个正常跑全判成失败（runs_failed=12），而且 head -1 抓到的是总能量。
    nl=$(grep -c "^NL Energy, E(C,NL)" "$wd/job.out")
    echo "$(date -u +%FT%TZ)  ${rank}/${base}  rc=$rc  scf_converged=$conv  terminated=$norm  NL_lines=$nl"
    if [ "$rc" != "0" ] || [ "$norm" != "1" ] || [ "$conv" != "1" ] || [ "$nl" != "1" ]; then
      fails=$((fails+1))
      echo "     ^^ 这一跑不合格，取数阶段会拒发（不删，留证据）"
    fi
    cp -f "$wd/job.out" "$RUN/${rank}__${base}.out"
    cp -f "$wd/job.rc"  "$RUN/${rank}__${base}.out.rc"
    cp -f "$wd/job.inp" "$RUN/${rank}__${base}.inp"
    nrun=$((nrun+1))
  done
done
echo "# runs_done=$nrun  期望 12 = 2 rank x (complex + 2 mono) x 2 体系"
echo "# runs_failed=$fails"
echo "# exit=$fails at $(date -u +%FT%TZ)"
