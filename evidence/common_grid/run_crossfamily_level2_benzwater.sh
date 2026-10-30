#!/usr/bin/env bash
# Level 2 for benzene...water under the CURRENT package code: the first attempt to put an AROMATIC
# cell on two adequate rungs.
#
# Why this cell and why level 2 rather than level 0.  paper/main.md line 431 already states, on
# measured grounds, that level 0 is NOT adequate for the 24-atom aromatic dimer, so a level-0-to-1
# ladder on a pi system compares two rungs of which the lower one the paper itself disqualifies --
# it cannot answer "does the spread survive adequate convergence?".  The pair that can is level 1
# against level 2, and the level-1 rung for this cell already exists under the current hash
# (20261012T050216Z, all-six span is the top of the published band, and it is the cell whose
# out-of-family span the draft quotes).
#
# Cost, measured not assumed.  My first extrapolation for the water level-2 run used time ~ N^2 and
# predicted ~65 min; the run actually finished in 1449.5 s against a level-1 875.0 s at 2.12x the
# points, i.e. wall ~ N^0.67.  With benzene...water at 2353.7 s for level 1 that puts level 2 near
# 3100 s, and the conservative N^1.0 bound near 5000 s: call it 50-85 min.  The exponent rests on
# ONE measured pair, so treat the range as an estimate and read the printed 用时 when it lands.
#
# Single-environment note: this runs on this box because the cluster copy reports a different numpy
# and python patch level, and the whole point of this round is to remove confounds, not to add a
# machine difference between the two rungs being compared.
set -u
cd <REPO> || exit 3
S=${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}
OUT=evidence/common_grid/${S}_hirshfeld_crossfamily_l2_benzwater.out
{
  echo "# stamper host clock UTC : $(cat <REPO>/.HOSTCLOCK 2>/dev/null || echo '<not supplied>')"
  echo "# stamper WSL  clock UTC : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# runner                 : evidence/common_grid/run_crossfamily_level2_benzwater.sh"
  echo "# box state at launch    : $(uptime 2>/dev/null | sed 's/^ *//')"
  echo "# concurrent on this box : the level-0 six-system batch, so 用时 below is contended and is"
  echo "#                          NOT a cost anchor for anything else"
  echo "# parallel env of runner shell (child inherits; nothing here sets a thread count):"
  echo "#   nproc                        = $(nproc 2>/dev/null || echo '<nproc unavailable>')"
  echo "#   /proc/self Cpus_allowed_list = $(awk '/Cpus_allowed_list/{print $2}' /proc/self/status 2>/dev/null || echo '<unreadable>')"
  echo "#   OMP_NUM_THREADS              = ${OMP_NUM_THREADS:-<unset>}"
  echo "#   OPENBLAS_NUM_THREADS         = ${OPENBLAS_NUM_THREADS:-<unset>}"
} > "$OUT"
LEVEL=2 NAMES="苯-水" python3 -u evidence/common_grid/hirshfeld_crossfamily.py >> "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
