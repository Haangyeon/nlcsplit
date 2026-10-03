import sys, os, tempfile
sys.path.insert(0, "evidence/ccsdt")
from ladder_parse import parse_ladder

OLD = ["20260930T235900Z_stepm_three_systems_631g.out",
       "20261001T000400Z_stepm_three_systems_avdz.out",
       "20261002T043400Z_snnu_benzene_ladder.out",
       "20261002T0630Z_snnu_benzene_dimer_ccsdt.out",
       "20261002T1030Z_snnu_benzene_dimer_B.out",
       "20261002T0715Z_snnu_benzene_avdz.out",
       "20261002T1208Z_snnu_sandwich_avdz_SUPERSEDED.out"]
rows = parse_ladder(["evidence/ccsdt/" + f for f in OLD])
new = parse_ladder(["scratch/local_cp_rebuild_dimers.log"])
print("superseded archives -> %d rows; corrected local rebuild -> %d rows"
      % (len(rows), len(new)))
pos = [k for k in new if new[k]["de_kcal"] > 0]
print("rows with a POSITIVE interaction energy (the sign the first regex dropped): %s"
      % ([(k, new[k]["de_kcal"]) for k in sorted(pos)] or "none"))

d = tempfile.mkdtemp()
HDR = "== Step M · X CCSD(T) 锚点 ==\n### basis = b\n"
RUN = "  复合物 nao=36 nbas=20 nelec=20；单体 nao=36/36；每片段冻核 [1, 1]，合计 2\n" \
      "  --- frozen(cores) ---\n"


def expect(text, why, want_raise=True):
    p = os.path.join(d, "t%d.out" % abs(hash(text)))
    open(p, "w").write(text)
    try:
        got = parse_ladder([p])
        fired = False
    except SystemExit as e:
        fired, msg = True, str(e)
    ok = "OK  " if fired == want_raise else "BAD "
    print("  %s %-58s raised=%s%s" % (ok, why, fired,
                                      "" if fired == want_raise else "  <-- guard is decoration"))
    if fired and want_raise:
        print("        %s" % msg[:150])
    return got if not fired else None


expect("nothing here\n", "a file with no CCSD(T) row at all")
expect(HDR + RUN + "    CCSD(T)      -1.0  -2.0  +0.0734   1.0\n",
       "a complete block parses (positive value included)", want_raise=False)
expect(HDR + "    CCSD(T)      -1.0  -2.0  +0.0734   1.0\n",
       "a header-less row that has no headered twin")
expect(HDR + RUN + "    CCSD(T)      -1.0  -2.0  N/A   1.0\n",
       "a row whose fields are not numbers")
expect(HDR + RUN + "    CCSD(T)      -1.0  -2.0  +0.0734   1.0\n"
       + RUN + "    CCSD(T)      -9.0  -8.0  +0.0734   1.0\n",
       "the same key twice with a different complex energy")
expect(HDR + "    CCSD(T)      -1.0  -2.0  +0.0734   1.0\n" + RUN
       + "    CCSD(T)      -1.0  -2.0  +0.0734   1.0\n",
       "an echo row that IS re-presented with a header later (accepted)", want_raise=False)
expect(HDR + "    CCSD(T)      -5.0  -2.0  +0.0734   1.0\n" + RUN
       + "    CCSD(T)      -1.0  -2.0  +0.0734   1.0\n",
       "an echo row whose numbers appear NOWHERE with a header (the twin check itself)")
got = expect(HDR + RUN + "    CCSD(T)      -1.0  -2.0  +0.0734   1.0\n"
             "    CCSD(T)      -1.0  -2.0  +0.0734   1.0\n",
             "duplicate agreeing rows", want_raise=False)
print("  positive control parsed de_kcal = %s" % (got and got[("X", "b", "frozen")]["de_kcal"]))
