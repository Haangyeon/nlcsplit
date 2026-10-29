#!/usr/bin/env bash
# Re-run the two chemical controls added for the JCTC revision.
# Usage: bash evidence/chemical_controls/run_chemical_controls.sh
# Writes a timestamped archive and its own .rc; do not infer success from a notification.
set -u
cd "$(dirname "$0")"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
out="${stamp}_chemical_controls.out"
rcfile="${out}.rc"
{
  printf '# chemical_controls\n'
  printf '# artifact_kind=measurement\n'
  printf '# stamp=%s\n' "$stamp"
  printf '# host=%s\n' "$(uname -n)"
  printf '# pyscf=%s\n' "$(python3 -c 'import pyscf; print(pyscf.__version__)')"
  printf '# command=dative/run_ab.py then ionic/run_fw.py\n'
} > "$out"
rc=0
python3 -u dative/run_ab.py >> "$out" 2>&1 || rc=$?
python3 -u ionic/run_fw.py >> "$out" 2>&1 || rc=$?
printf '# exit=%d at %s\n' "$rc" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$out"
printf '%d\n' "$rc" > "$rcfile"
echo "$out"
echo "$rcfile"
exit "$rc"
