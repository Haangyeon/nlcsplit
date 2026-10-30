#!/usr/bin/env bash
# Archive the grid-convergence table (both claims) and the negative-control reading.
#
# Three products, one run, each with the repository's mandatory triple (stdout .out, its own `.rc`
# written by the job itself, and an in-file `# exit=` line).  This is a script file and not a
# command line for the reason recorded in run_crossfamily_check.sh: a stamp plus a redirect passed
# through Git Bash -> `wsl bash -lc '...'` loses its variables and the archive never appears, while
# the background notification still reports exit 0.
#
# The convergence table is run twice on purpose.  Without --ladders-only it answers the FULL-SET
# claim ("the spread survives grid convergence across the cells we publish") and must say whether
# every cell actually has a same-code ladder; with it, the same files answer the SCOPED claim
# ("over the cells that do have a ladder, the deterministic span is stable").  One number, one
# question: the two codes are different claims and neither is allowed to be quoted for the other.
set -u
cd <REPO> || exit 3
S=${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}
D=evidence/common_grid
HOST=$(cat <REPO>/.HOSTCLOCK 2>/dev/null || echo '<not supplied>')
rc_of() { [ -f "$1" ] && cat "$1" || echo "<missing .rc>"; }

run_one() {
  local tag=$1; shift
  local OUT=$D/${S}_grid_convergence_${tag}.out
  {
    echo "# stamper host clock UTC : $HOST"
    echo "# stamper WSL  clock UTC : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "# runner                 : evidence/common_grid/run_grid_convergence_archive.sh"
    echo "# command                : $*"
    echo "# level-2 water archive exit evidence: .rc=$(rc_of $D/20261021T091653Z_hirshfeld_crossfamily_l2_water.out.rc)"
    echo "# level-0 currentcode archive exit evidence: .rc=$(rc_of $D/20261021T092258Z_hirshfeld_crossfamily_l0_currentcode.out.rc)"
  } > "$OUT"
  python3 -u "$@" >> "$OUT" 2>&1
  local RC=$?
  echo "$RC" > "$OUT.rc"
  echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
  echo "  $OUT rc=$RC bytes=$(stat -c %s "$OUT")"
}

run_one full_set  $D/grid_level_convergence.py
run_one scoped    $D/grid_level_convergence.py --ladders-only
run_one negctl    $D/grid_level_convergence_negative_control.py
echo "stamp=$S"
