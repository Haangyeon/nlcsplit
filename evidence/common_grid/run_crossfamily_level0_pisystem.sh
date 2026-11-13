#!/usr/bin/env bash
# The remaining six cells at level 0, under the CURRENT package code (partition.py ec6c0c56).
#
# Why: evidence/common_grid/grid_level_convergence.py can only certify a grid ladder when a
# (partition hash, system) pair has two distinct levels. Under the current hash, level 0 exists for
# water and methane only (20261021T092258Z), so the convergence statement covers 2 of the 8 cells.
# The referee-facing claim needs the pi systems too -- 苯二聚体(A) in particular is the cell whose
# out-of-family span is largest, and a small-systems-only ladder will not carry it.
#
# Launch discipline: run this ONLY when no other measurement is on the box. The archived timings in
# 20261021T092258Z were inflated by a concurrent level-2 job and are recorded as contended, so the
# extrapolation below is taken from the uncontended level-1 self-reports divided by the squared grid
# ratio (level 0 grids are ~1/4 the point count of level 1, so the double sum costs ~1/16):
#   ammonia   ~   60 s | benzene-water ~ 150 s | benzene-ammonia ~ 210 s
#   benzene-methane ~ 160 s | benzene dimer A ~ 410 s | benzene dimer B ~ 400 s   => ~20 min total.
# If the measured total comes out over half an hour, the rest belongs on the cluster, not on this
# box's cores (standing rule), so stop after what is already archived and report the wall times.
#
# Names are the exact registry keys of nlcsplit/step_h_s22.py:build(); the printed block label echoes
# them, which is how the archived level-1 files identify 苯二聚体(A) / 苯二聚体(B).
set -u
cd <REPO> || exit 3
S=${STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}
OUT=evidence/common_grid/${S}_hirshfeld_crossfamily_l0_pisystem_currentcode.out
{
  echo "# stamper host clock UTC : $(cat <REPO>/.HOSTCLOCK 2>/dev/null || echo '<not supplied>')"
  echo "# stamper WSL  clock UTC : $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# runner                 : evidence/common_grid/run_crossfamily_level0_pisystem.sh"
  echo "# box state at launch    : $(uptime 2>/dev/null | sed 's/^ *//')"
  echo "# parallel env of runner shell (child inherits; nothing here sets a thread count):"
  echo "#   nproc                    = $(nproc 2>/dev/null || echo '<nproc unavailable>')"
  echo "#   /proc/self Cpus_allowed_list = $(awk '/Cpus_allowed_list/{print $2}' /proc/self/status 2>/dev/null || echo '<unreadable>')"
  echo "#   OMP_NUM_THREADS          = ${OMP_NUM_THREADS:-<unset>}"
  echo "#   OPENBLAS_NUM_THREADS     = ${OPENBLAS_NUM_THREADS:-<unset>}"
} > "$OUT"
LEVEL=0 NAMES="氨二聚体 苯-水 苯-氨 苯-甲烷 苯二聚体(A) 苯二聚体(B)" \
  python3 -u evidence/common_grid/hirshfeld_crossfamily.py >> "$OUT" 2>&1
RC=$?
echo "$RC" > "$OUT.rc"
echo "# exit=$RC at $(date -u +%FT%TZ)" >> "$OUT"
echo "out=$OUT  rc=$RC  bytes=$(stat -c %s "$OUT")"
