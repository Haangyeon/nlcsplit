#!/usr/bin/env bash
# level-2 rung for the cross-scheme attribution of the water dimer -- the ONE missing datum in
# "does the partition spread survive grid convergence?" (asked twice by external review, 2026-10-20).
#
# Why a script file and not a command line: run_crossfamily_check.sh records the 2026-10-12 finding
# that a stamp + redirect passed through Git Bash -> `wsl bash -lc '...'` gets its `$f` eaten, so no
# archive is created while the background notification still says exit 0. Discipline lives in files.
#
# Cost anchor, measured rather than guessed: the same script on the same machine self-reported
# 44.1 s at level 0 (N=4440) and 846.2 s at level 1 (N=18336) -> exponent ~2.2 in N. Level 2 is
# N=39755 (measured below, printed before the heavy work) -> expected ~72 min. Nothing else runs.
#
# Clocks: the stamp comes from the HOST clock passed in via STAMP, because this repository has been
# bitten by a WSL clock that runs days behind and then stamps artifacts with it. Both clocks are
# printed into the archive so a wrong stamp is detectable after the fact.
set -u
cd <REPO> || exit 3
S=${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}
OUT=evidence/common_grid/${S}_hirshfeld_crossfamily_l2_water.out
{
  echo "# stamper host clock UTC : $(cat <REPO>/.HOSTCLOCK 2>/dev/null || echo '<not supplied>')"
  echo "# stamper WSL  clock UTC : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# runner                 : evidence/common_grid/run_crossfamily_level2_water.sh"
} > "$OUT"
LEVEL=2 NAMES="水二聚体" python3 -u evidence/common_grid/hirshfeld_crossfamily.py >> "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
