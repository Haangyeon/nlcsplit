#!/usr/bin/env bash
# 线程数扫描：Hirshfeld 归属矩阵 S 的自差 / 互比 随 OMP_NUM_THREADS 怎么变。
#
# 为什么单独成文件（而不是 bash -lc '... $T ...' 内联）：内联穿过 Git Bash → wsl 时
# `$T` 会被外层吃掉，我刚才就这么翻过一次——三个"不同线程"的档其实跑的是同一个设置，
# 结论看着齐全全是假的。凡是要产出证据文件的批处理，逻辑必须落在盘上的脚本里（本仓硬规矩）。
#
# 为什么这条值得跑：它把"Hirshfeld 那一列不可逐位复现"从一句警告变成一个可处置的事实——
#   若只有 >1 线程会抖 ⇒ 病根是多线程浮点归约顺序 × 尾部 ρ/Σρ 的下溢放大，
#   处置是"出货用单线程"或"给分母加阈值"，**不需要换定义、不需要整列重算**。
# 每档都自带线程抬头（`probe_hirshfeld_recipe_equivalence.py` 现在会打印 OMP/OPENBLAS/MKL），
# 免得日后又出现两份互相矛盾的档而没人知道差在哪个环境变量上。
set -u
cd <REPO> || exit 3
export PYTHONIOENCODING=utf-8
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
SUM="evidence/common_grid/${STAMP}_thread_sweep_summary.out"
: > "$SUM"

for T in 1 2 4 8; do
  out="evidence/common_grid/${STAMP}_thread${T}_hirshfeld_equivalence.out"
  OMP_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T MKL_NUM_THREADS=$T \
    python3 -u evidence/common_grid/probe_hirshfeld_recipe_equivalence.py > "$out" 2>&1
  rc=$?
  echo "$rc" > "$out.rc"
  echo "# exit=$rc at $(date -u +%FT%TZ)" >> "$out"
  self=$(grep -oE "包内两次 = [0-9.e+-]+" "$out" | head -1)
  cross=$(grep -oE "互比 max\|ΔS\| = [0-9.e+-]+" "$out" | head -1)
  verdict=$(grep -oE "^VERDICT [A-Z_]+" "$out" | head -1)
  echo "T=$T  rc=$rc  ${self:-无自差行}  ${cross:-无互比行}  ${verdict:-无判语}" | tee -a "$SUM"
done

echo "# 明细见同前缀的 _thread{1,2,4,8}_hirshfeld_equivalence.out" | tee -a "$SUM"
RC=$( [ "$(grep -c 'rc=0' "$SUM")" = "1" ] && echo 0 || echo 1 )
echo "$RC" > "$SUM.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$SUM"
echo "wrote $SUM rc=$RC"
exit "$RC"
