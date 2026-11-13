#!/usr/bin/env bash
# Level 2 for the THREE cells still missing a second adequately fine rung:
#   苯-氨 (benzene...ammonia), 苯-甲烷 (benzene...methane), 苯二聚体(B) (the T-shaped dimer).
# These are exactly the three the convergence table reports as NOT MEASURED for the secondary
# claim; with them measured, every one of the eight published cells either has a pair of rungs at
# or above the published level or is shown to move, instead of three cells being left blank.
#
# Order is cheapest-first so that a crash late in the run still leaves the two cheap cells archived.
#
# Cost. Point counts scale almost exactly with a fixed factor between the two fine levels (the
# four measured same-code pairs sit inside a narrow band), so the level-2 point count of each cell
# is predictable from its own level-1 count; seconds per point is NOT, and the two aromatic cells
# already measured differ by a factor this run cannot assume away.  Using the closest measured
# same-size cell as the price anchor (benzene...water for the two 14-atom cells, benzene dimer (A)
# for the 24-atom one) the expectation is roughly 2.7 h, 2.8 h and 5.2 h, about eleven hours in
# total.  That index has never been validated across systems; treat it as a quote and read 用时 out
# of the archive when each cell lands.
#
# One archive for three cells, one process, no idle gap.  The convergence script's admission gate
# excludes any file whose own `# exit=` line and `.rc` sibling disagree, so a crash partway leaves
# partial evidence that cannot silently enter the table.
set -u
cd <REPO> || exit 3
S=${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}
OUT=evidence/common_grid/${S}_hirshfeld_crossfamily_l2_three_pi_cells.out
{
  echo "# stamper host clock UTC : $(cat <REPO>/.HOSTCLOCK 2>/dev/null || echo '<not supplied>')"
  echo "# stamper WSL  clock UTC : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# runner                 : evidence/common_grid/run_crossfamily_level2_three_pi_cells.sh"
  echo "# box state at launch    : $(uptime 2>/dev/null | sed 's/^ *//')"
  echo "# nothing else of mine runs on this box; the three cells run one after another, so 用时 below"
  echo "# is NOT contended by my own work. Any other load present at launch is in the line above."
  echo "# thread env inherited by the child (this runner sets nothing):"
  echo "#   nproc                        = $(nproc 2>/dev/null || echo '<nproc unavailable>')"
  echo "#   /proc/self Cpus_allowed_list = $(awk '/Cpus_allowed_list/{print $2}' /proc/self/status 2>/dev/null || echo '<unreadable>')"
  echo "#   OMP_NUM_THREADS              = ${OMP_NUM_THREADS:-<unset>}"
  echo "#   OPENBLAS_NUM_THREADS         = ${OPENBLAS_NUM_THREADS:-<unset>}"
} > "$OUT"
LEVEL=2 NAMES="苯-氨 苯-甲烷 苯二聚体(B)" \
  python3 -u evidence/common_grid/hirshfeld_crossfamily.py >> "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
