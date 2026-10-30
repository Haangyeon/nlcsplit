#!/usr/bin/env bash
# Level 2 for three more cells, run in ONE process so there is no idle gap between them:
#   氨二聚体 (small, cheap)  ->  甲烷二聚体 (the low end of the published band)
#   ->  苯二聚体(A) (the cell that FAILED the registered gate at level 0->1)
#
# Why this three and not all six remaining: the secondary claim can only be made for cells that
# have two rungs at or above the published level. Ammonia and methane are the cheapest two such
# cells and methane is the band's lower endpoint, so including it makes the endpoints tested rather
# than interpolated. 苯二聚体(A) is included because it is the interesting one: its span grew from
# 0.0120 (level 0) to 0.0274 (level 1), and only a level-2 rung can say whether that is convergence
# or drift. The other three pi cells are left for the cluster decision in task #66.
#
# Cost, with the honesty this session has earned. The two measured level-1 -> level-2 ratios on
# this box are 1.66 (water, uncontended) and 3.98 (benzene-water, contended by a parallel batch).
# Applying that range to the self-reported level-1 times gives:
#   ammonia 1154.8 s -> 1.9k-4.6k s | methane 1375.2 s -> 2.3k-5.5k s | benzene dimer A 6612.7 s
#   -> 11k-26k s.  Total 3.5-10 h, best estimate ~4.5 h.  Every earlier estimate I have made this
#   session from an exponent fitted to two points came out wrong, so treat that range as the claim
#   and read 用时 out of this archive when each cell lands.
#
# One archive for three cells is deliberate: the convergence script's admission gate excludes any
# file whose own `# exit=` line and `.rc` sibling do not agree, so a crash partway leaves partial
# evidence that cannot silently enter the table.
set -u
cd <REPO> || exit 3
S=${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}
OUT=evidence/common_grid/${S}_hirshfeld_crossfamily_l2_three_cells.out
{
  echo "# stamper host clock UTC : $(cat <REPO>/.HOSTCLOCK 2>/dev/null || echo '<not supplied>')"
  echo "# stamper WSL  clock UTC : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# runner                 : evidence/common_grid/run_crossfamily_level2_three_cells.sh"
  echo "# box state at launch    : $(uptime 2>/dev/null | sed 's/^ *//')"
  echo "# nothing else of mine runs on this box; 用时 below is therefore NOT contended"
  echo "# parallel env of runner shell (child inherits; nothing here sets a thread count):"
  echo "#   nproc                        = $(nproc 2>/dev/null || echo '<nproc unavailable>')"
  echo "#   /proc/self Cpus_allowed_list = $(awk '/Cpus_allowed_list/{print $2}' /proc/self/status 2>/dev/null || echo '<unreadable>')"
  echo "#   OMP_NUM_THREADS              = ${OMP_NUM_THREADS:-<unset>}"
  echo "#   OPENBLAS_NUM_THREADS         = ${OPENBLAS_NUM_THREADS:-<unset>}"
} > "$OUT"
LEVEL=2 NAMES="氨二聚体 甲烷二聚体 苯二聚体(A)" \
  python3 -u evidence/common_grid/hirshfeld_crossfamily.py >> "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
