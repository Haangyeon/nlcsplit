#!/usr/bin/env bash
# level-0 rung for the cross-scheme attribution, run with the CURRENT package code
# (nlcsplit/partition.py = ec6c0c56...). The only archived level-0 artifact
# (20261009T155042Z) was produced by partition.py = d57ab021, i.e. before the out-of-family
# partitions were merged into the package, and merging visibly moved the Hirshfeld/Voronoi
# column (water level-1 all-six span 0.0650 under d57ab021 vs 0.0433 under ec6c0c56, while the
# family-internal span is 0.0433 in both). So a l0(d57ab)->l1(ec6c0) pair is NOT a grid ladder:
# the rung difference is confounded with a code difference. This run makes the ladder single-code.
#
# Systems: water (the one with the level-2 job) + methane (second system, so the statement is not
# a single point). Nominal cost read from the archived self-report of this same script:
# 44.1 s (water, N=4440) + 182.9 s (methane, N=6736) under d57ab021 -> a few minutes here.
# The level-2 water job is running concurrently on this box; wall times printed by this run are
# therefore contended and are NOT to be used as a cost anchor for anything.
#
# Thread provenance: this repository has a recorded credential gap "比对基线档未记线程数". The
# archived crossfamily files record no thread count at all, so this runner stamps what the runner
# shell can see (the python child inherits it; no OMP override is set anywhere). That is the most
# that can be honestly claimed, and it is why the deterministic family-internal span -- not the
# all-six span, which includes the thread-sensitive Hirshfeld column -- is the primary quantity
# for the convergence statement.
set -u
cd <REPO> || exit 3
S=${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}
OUT=evidence/common_grid/${S}_hirshfeld_crossfamily_l0_currentcode.out
{
  echo "# stamper host clock UTC : $(cat <REPO>/.HOSTCLOCK 2>/dev/null || echo '<not supplied>')"
  echo "# stamper WSL  clock UTC : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# runner                 : evidence/common_grid/run_crossfamily_level0_currentcode.sh"
  echo "# parallel env of runner shell (child inherits; nothing here sets a thread count):"
  echo "#   nproc                    = $(nproc 2>/dev/null || echo '<nproc unavailable>')"
  echo "#   /proc/self Cpus_allowed_list = $(awk '/Cpus_allowed_list/{print $2}' /proc/self/status 2>/dev/null || echo '<unreadable>')"
  echo "#   OMP_NUM_THREADS          = ${OMP_NUM_THREADS:-<unset>}"
  echo "#   OPENBLAS_NUM_THREADS     = ${OPENBLAS_NUM_THREADS:-<unset>}"
  echo "# concurrent job on this box: level-2 water (task launched 09:16Z), so 用时 below is contended"
} > "$OUT"
LEVEL=0 NAMES="水二聚体 甲烷二聚体" python3 -u evidence/common_grid/hirshfeld_crossfamily.py >> "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
