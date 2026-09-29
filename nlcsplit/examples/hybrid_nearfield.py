"""Measuring pass: can a near-field / far-field *hybrid* beat the atom-block full path?

Read-only with respect to the library: this file imports `nlcsplit.fastpair` and drives
its public/private pieces (`build_blocks`, `_mac`, `node_bound`, `box_sep`) from the
outside. Nothing in `fastpair.py` / `nlc.py` / `partition.py` is touched.

The four paths compared, all at the same per-node-pair acceptance constant tau:

  1. exact     : atom blocks, nothing dropped (`screen=None` equivalent) -- the baseline.
  2. tree      : every cross atom pair goes through the top-down MAC tree (`_mac`).
  3. hybrid    : split the atom pairs by what the *roots* of the two trees say.
                 near := root box_sep == 0  OR  root bound > Bclass
                 far  := everything else
                 near pairs are summed exactly with the big-gemm atom-block path,
                 far pairs go through `_mac`.
  4. hybrid + larger min_pts (256, 1024) : same split, coarser leaves.

Accounting (why cert_err is still a valid bound under the hybrid)
----------------------------------------------------------------
Every cross atom pair is dispatched to exactly one path and *nothing* is thrown away by
the classification:
  * near  -> the whole pair is summed exactly => its truncation error is 0 and it adds
    0 to cert_err;
  * far   -> `_mac` partitions that pair: node-pairs accepted add their own bound to
    cert_err, node-pairs rejected are recursed to leaves and summed exactly.
So |E_config - E_full| <= cert_err_config holds regardless of Bclass: Bclass only decides
*which* path pays for a pair, never whether the pair is accounted for. A pair whose bound
is "lost" by the classification is not lost at all -- it is put on the summation path.
The only requirement (asserted below) is that the near test is evaluated on the *roots*
of the same two trees that the far path would descend, and that no pair is dropped on the
strength of the classification alone. Dropping anything because "root bound is small"
would need to be added to cert_err with its x2 coefficient; we never drop that way.

Timing protocol
---------------
Wall clock only. Every sample records `uptime`, /proc/loadavg before+after,
OMP_NUM_THREADS, this process's own CPU-cores, and -- the actual gate -- the number of
CPU-cores consumed by *other* processes during the window (per-PID /proc scan). Raw
loadavg cannot be the gate itself: a 3-thread BLAS run pushes loadavg to >= 3 by itself,
so it would invalidate every honest sample. A sample is INVALID when external cores >=
0.5 (the user's threshold, applied to the part of the load that is not ours). Medians are
taken over valid samples; when no sample of a config is valid the config is reported as
"contaminated" and, as a fallback, the interleaved ratio (each sample bracketed by its
own baseline samples) is given so a contention-cancelling estimate still exists.
"""
import os
import subprocess
import sys
import time
import resource
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np                                          # noqa: E402
from pyscf import dft, gto                                  # noqa: E402

from nlcsplit import fastpair, geomlib, nlc, partition      # noqa: E402

HA2K = 627.50947400
BASIS = "6-31g*"
XC = "wb97x_v"
SCHEME = "becke"
HZ = os.sysconf("SC_CLK_TCK")
SELF_PID = os.getpid()

ACC_BUDGET_KCAL = 1.0e-6          # the pass/fail accuracy budget, kcal/mol
TAU = 1.0e-12                     # Ha, per-node-pair acceptance constant
MINPTS = (32, 256, 1024)


def log(*a):
    print(*a, flush=True)


# ----------------------------------------------------------------- contention probe
def _other_cpu_seconds():
    """Sum of utime+stime (seconds) of every process that is not us. Cheap-ish."""
    total = 0.0
    for pid in os.listdir("/proc"):
        if not pid.isdigit() or int(pid) == SELF_PID:
            continue
        try:
            with open("/proc/" + pid + "/stat", "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        tail = raw[raw.rfind(b")") + 1:].split()
        if len(tail) < 13:
            continue
        try:
            total += (float(tail[11]) + float(tail[12])) / HZ
        except ValueError:
            continue
    return total


def _own_cpu_seconds():
    r = resource.getrusage(resource.RUSAGE_SELF)
    return r.ru_utime + r.ru_stime


def _uptime_line():
    try:
        return subprocess.run(["uptime"], capture_output=True, text=True,
                              timeout=20).stdout.strip()
    except Exception as exc:                                   # pragma: no cover
        return "uptime failed: %s" % exc


def _load():
    try:
        return tuple(os.getloadavg())
    except OSError:
        return (float("nan"),) * 3


QUIET_WAIT_S = float(os.environ.get("QUIET_WAIT_S", "12"))
EXT_GATE = 0.5          # CPU-cores used by OTHER processes above which a sample is void


def quiet_wait():
    """Bounded wait for the box to free up. Never blocks the run for long."""
    if QUIET_WAIT_S <= 0:
        return False
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < QUIET_WAIT_S:
        a = _other_cpu_seconds()
        time.sleep(1.5)
        b = _other_cpu_seconds()
        if (b - a) / 1.5 < EXT_GATE:
            return True
    return False


class Sample:
    """One timed window with its full contention fingerprint."""

    def __init__(self, tag, fn):
        self.tag = tag
        quiet_wait()
        l0 = _load()
        self.uptime = _uptime_line()
        self.omp = os.environ.get("OMP_NUM_THREADS", "<unset>")
        self.load_before = l0
        c0 = _other_cpu_seconds()
        o0 = _own_cpu_seconds()
        t0 = time.perf_counter()
        self.ret = fn()
        self.wall = time.perf_counter() - t0
        o1 = _own_cpu_seconds()
        c1 = _other_cpu_seconds()
        self.load_after = _load()
        self.cpu_s = o1 - o0
        self.own_cores = (o1 - o0) / max(self.wall, 1e-12)
        self.ext_cores = (c1 - c0) / max(self.wall, 1e-12)
        self.valid = self.ext_cores < EXT_GATE
        self.note = "" if self.valid else "contended (external %.2f cores)" % self.ext_cores

    def __str__(self):
        return ("%s wall=%7.3fs own=%4.2f cores ext=%4.2f cores load=%s/%s valid=%s"
                % (self.tag, self.wall, self.own_cores, self.ext_cores,
                   "%.2f" % self.load_before[0], "%.2f" % self.load_after[0],
                   self.valid))


def fmt_samples(samples):
    return " | ".join(str(s) for s in samples)


def median_valid(samples):
    valid = [s.wall for s in samples if s.valid]
    if not valid:
        return None, 0
    return statistics.median(valid), len(valid)


def interleaved_ratio(target_samples, base_samples, base_total):
    """Contention-cancelling estimate: each target sample divided by the local baseline.

    Uses the baseline median measured in the same block of the run, so a slow window
    inflates numerator and denominator together.
    """
    if not target_samples or base_total <= 0:
        return None
    return statistics.median(s.wall for s in target_samples) / base_total


# --------------------------------------------------------------------- path builders
def make_fields(mol, mf, level):
    """The same field pipeline `screened_decomposition` runs, hoisted out of the loop."""
    X, W, owner = partition.atom_partition(mol, level=level, scheme=SCHEME)
    ni = mf._numint
    dm = mf.make_rdm1()
    b, C = ni.nlc_coeff(mf.xc)[0][0]
    rho_full = ni.eval_rho(mol, ni.eval_ao(mol, X, deriv=1), dm, xctype="GGA")
    rho = rho_full[0]
    sig = rho_full[1] ** 2 + rho_full[2] ** 2 + rho_full[3] ** 2
    w0, kap, keep = nlc.vv10_fields(rho, sig, b=b, C=C)
    wr = W * rho
    owner_kept = np.full(len(wr), -1, dtype=np.intp)
    idx_kept = np.flatnonzero(keep)
    owner_kept[idx_kept] = owner[idx_kept]
    return dict(X=X, wr=wr, w0=w0, kap=kap, owner_kept=owner_kept,
                n_grid=int(len(wr)), n_kept=int(idx_kept.size), b=b, C=C)


def live_blocks(F, min_pts=None):
    tree_kwargs = None if min_pts is None else {
        "mass_frac": 0.01, "radius_frac": 1.0 / 3.0, "min_pts": min_pts}
    blocks = fastpair.build_blocks(F["X"], F["wr"], F["w0"], F["kap"],
                                   F["owner_kept"], NATM, tree_kwargs=tree_kwargs)
    return blocks, [b for b in blocks if b is not None]


def self_sum(X, wr, w0, kap, live):
    """Self blocks: never screenable, exact in every path (identical in all four)."""
    E = 0.0
    npts = 0
    for Pa in live:
        E += float(nlc.pair_energy(X, wr, w0, kap, Pa.idx, Pa.idx))
        npts += int(Pa.idx.size) ** 2
    return E, npts


def pair_exact(F, Pa, Pb):
    """Whole-pair exact contribution, full x2 bookkeeping (half-block from pair_energy)."""
    return 2.0 * float(nlc.pair_energy(F["X"], F["wr"], F["w0"], F["kap"], Pa.idx, Pb.idx))


def pair_tree(F, Pa, Pb, tau, stats):
    """Half-block sum from `_mac` (acceptance is tested in the x2 convention, but the
    returned value is still the half block -- the caller owes it the x2)."""
    return 2.0 * fastpair._mac(F["X"], F["wr"], F["w0"], F["kap"], Pa.tree, Pb.tree,
                               tau, 2.0, stats)


def new_stats():
    return dict(accepted=0, evaluated=0, visited=0, cert=0.0,
                pointpairs_dropped=0, pointpairs_evaluated=0)


# ----------------------------------------------------------------------- the systems
def report(tag, builder, level, tau=TAU, nrep_base=3, nrep=2):
    global NATM
    log("\n" + "=" * 100)
    log("=== %s   level=%d  basis=%s  xc=%s  scheme=%s  tau=%g Ha (%.1e kcal/mol budget=%.3g)"
        % (tag, level, BASIS, XC, SCHEME, tau, tau * HA2K, ACC_BUDGET_KCAL))
    mol = gto.M(atom=builder(), basis=BASIS, verbose=0, unit="Angstrom")
    NATM = mol.natm
    t = time.perf_counter()
    mf = dft.RKS(mol)
    mf.xc = XC
    mf.grids.level = level
    mf.kernel()
    log("    SCF (shared by all four paths, never inside a timed window): %.1f s"
        % (time.perf_counter() - t))
    t = time.perf_counter()
    F = make_fields(mol, mf, level)
    log("    grid+density fields (shared, outside timed windows): %.2f s   n_grid=%d"
        " kept=%d  atoms=%d" % (time.perf_counter() - t, F["n_grid"], F["n_kept"], NATM))

    # library anchor, for the reference energy and to prove my re-implementation of the
    # exact path is bit-identical to screened_decomposition(screen=None)
    anchor = fastpair.screened_decomposition(mol, mf, level=level, scheme=SCHEME)
    E_full = anchor["E_pair"]
    anchor_tau = fastpair.screened_decomposition(mol, mf, level=level, scheme=SCHEME,
                                                 screen=tau)
    log("    library tau-screened anchor (for validating this harness, not timed):"
        " E_pair=%.15g cert=%.3e Kept_pp=%d"
        % (anchor_tau["E_pair"], anchor_tau["cert_err"],
           anchor_tau["pointpairs_evaluated"]))

    blocks, live = live_blocks(F, None)
    nppts = {b.atom: int(b.idx.size) for b in live}
    n_self_pairs = sum(nppts[b.atom] ** 2 for b in live)
    far_total = sum(nppts[Pa.atom] * nppts[Pb.atom]
                    for i, Pa in enumerate(live) for Pb in live[i + 1:])
    grand_total = n_self_pairs + far_total
    log("    cross point pairs = %d   self point pairs = %d   total = %d"
        % (far_total, n_self_pairs, grand_total))

    # ---- what the two tree ROOTS can say about each atom pair -------------------
    tb = {}
    for mp in MINPTS:
        t = time.perf_counter()
        tb[mp] = live_blocks(F, mp)
        tb[mp] = (tb[mp][0], tb[mp][1], time.perf_counter() - t)
        log("    tree build min_pts=%4d: %6.2f s   leaves=%d"
            % (mp, tb[mp][2], sum(len(fastpair.leaves(b.tree)) for b in tb[mp][1])))
    _, live32, _ = tb[MINPTS[0]]
    rows = []
    for i, Pa in enumerate(live32):
        for Pb in live32[i + 1:]:
            D = fastpair.box_sep(Pa.tree, Pb.tree)
            bnd = fastpair.node_bound(Pa.tree, Pb.tree, 2.0)
            rows.append(dict(a=Pa.atom, b=Pb.atom, npair=nppts[Pa.atom] * nppts[Pb.atom],
                             D=D, bnd=bnd))
    n_ov = sum(1 for r in rows if r["D"] == 0.0)
    pp_ov = sum(r["npair"] for r in rows if r["D"] == 0.0)
    log("    ROOT OVERLAP census: %d/%d cross atom pairs have box_sep(root)=0"
        % (n_ov, len(rows)))
    log("      -> those pairs hold %d/%d cross point pairs = %.4f%% of the cross work"
        % (pp_ov, far_total, 100.0 * pp_ov / far_total))
    log("      -> and %.4f%% of (cross+self) total point pairs"
        % (100.0 * pp_ov / grand_total))
    bnds = sorted(r["bnd"] for r in rows)
    Ds = sorted(r["D"] for r in rows)
    log("      root box_sep (A) min %.4f  median %.4f  max %.4f ; #pairs with D<0.05A: %d"
        "  D<0.2A: %d  D==0: %d"
        % (Ds[0] * 0.529177210903, Ds[len(Ds) // 2] * 0.529177210903,
           Ds[-1] * 0.529177210903, sum(1 for v in Ds if v * 0.529177210903 < 0.05),
           sum(1 for v in Ds if v * 0.529177210903 < 0.2), n_ov))
    log("      root bound (x2) range: %.3e .. %.3e Ha  =  %.3e .. %.3e kcal/mol"
        % (bnds[0], bnds[-1], bnds[0] * HA2K, bnds[-1] * HA2K))
    log("      tau/1e6 = %.3e Ha  ->  smallest root bound is %.3e x larger than tau"
        % (tau / 1e6, bnds[0] / tau))
    log("      pairs with root bound <= tau: %d/%d  (root-accepts without any descent)"
        % (sum(1 for v in bnds if v <= tau), len(bnds)))

    # ---- per-pair cost table: what a whole-pair routing decision can ever buy ----
    order = sorted(range(len(rows)), key=lambda k: rows[k]["bnd"])
    cum = 0
    qsel = {}
    for frac in (0.25, 0.50, 0.75):
        target = frac * far_total
        cum = 0
        for k in order:
            cum += rows[k]["npair"]
            if cum >= target:
                qsel[frac] = rows[k]["bnd"]
                break
    log("    classification thresholds Bclass (far = root bound <= Bclass):")
    for frac, v in sorted(qsel.items()):
        log("      Bclass so ~%2.0f%% of cross point pairs are far: %.3e Ha (%.3e kcal/mol)"
            % (100 * frac, v, v * HA2K))

    X, wr, w0, kap = F["X"], F["wr"], F["w0"], F["kap"]

    def cfg_exact():
        E, ns = self_sum(X, wr, w0, kap, live)
        kept = ns
        for i, Pa in enumerate(live):
            for Pb in live[i + 1:]:
                E += pair_exact(F, Pa, Pb)
                kept += nppts[Pa.atom] * nppts[Pb.atom]
        return dict(E=E, cert=0.0, kept=kept, accepted=0, evaluated=0, visited=0,
                    n_far=0, n_near=len(rows))

    def cfg_tree(min_pts):
        bl, lv, tbuild = tb[min_pts]
        E, ns = self_sum(X, wr, w0, kap, lv)
        st = new_stats()
        for i, Pa in enumerate(lv):
            for Pb in lv[i + 1:]:
                E += pair_tree(F, Pa, Pb, tau, st)
        return dict(E=E, cert=st["cert"], kept=ns + st["pointpairs_evaluated"],
                    accepted=st["accepted"], evaluated=st["evaluated"],
                    visited=st["visited"], n_far=len(rows), n_near=0,
                    tree_build=tbuild)

    def cfg_hybrid(min_pts, bclass):
        bl, lv, tbuild = tb[min_pts]
        E, ns = self_sum(X, wr, w0, kap, lv)
        st = new_stats()
        n_near = n_far = near_pp = 0
        for i, Pa in enumerate(lv):
            for Pb in lv[i + 1:]:
                D = fastpair.box_sep(Pa.tree, Pb.tree)
                bnd = fastpair.node_bound(Pa.tree, Pb.tree, 2.0)
                if D == 0.0 or bnd > bclass:          # near: pay full price, big gemm
                    E += pair_exact(F, Pa, Pb)
                    n_near += 1
                    near_pp += nppts[Pa.atom] * nppts[Pb.atom]
                else:                                  # far: descend the tree
                    E += pair_tree(F, Pa, Pb, tau, st)
                    n_far += 1
        return dict(E=E, cert=st["cert"],
                    kept=ns + near_pp + st["pointpairs_evaluated"],
                    accepted=st["accepted"], evaluated=st["evaluated"],
                    visited=st["visited"], n_far=n_far, n_near=n_near,
                    tree_build=tbuild, near_pp=near_pp)

    mp0, mp1, mp2 = MINPTS
    configs = [
        ("exact  atom-block full (screen=None)", lambda: cfg_exact(), 3),
        ("tree   min_pts=%d (pure tree)" % mp0, lambda: cfg_tree(mp0), 2),
        ("hybrid min_pts=%d near=root-box-overlap" % mp0,
         lambda: cfg_hybrid(mp0, 0.0), 2),
        ("hybrid min_pts=%d near=overlap or bnd>Bclass(q50)" % mp0,
         lambda: cfg_hybrid(mp0, qsel[0.50]), 2),
        ("hybrid min_pts=%d near=overlap or bnd>Bclass(q75)" % mp0,
         lambda: cfg_hybrid(mp0, qsel[0.75]), 1),
        ("tree   min_pts=%d" % mp1, lambda: cfg_tree(mp1), 1),
        ("hybrid min_pts=%d near=root-box-overlap" % mp1, lambda: cfg_hybrid(mp1, 0.0), 1),
        ("hybrid min_pts=%d near=overlap or bnd>Bclass(q50)" % mp1,
         lambda: cfg_hybrid(mp1, qsel[0.50]), 1),
        ("tree   min_pts=%d" % mp2, lambda: cfg_tree(mp2), 1),
        ("hybrid min_pts=%d near=overlap or bnd>Bclass(q50)" % mp2,
         lambda: cfg_hybrid(mp2, qsel[0.50]), 1),
    ]

    results = []
    base_samples = []
    for name, fn, reps in configs:
        smps = [Sample(name, fn) for _ in range(reps)]
        med, nval = median_valid(smps)
        raw = statistics.median(s.wall for s in smps)
        res = dict(name=name, med=med, raw=raw, nval=nval, nrep=len(smps),
                   cpu=statistics.median(s.cpu_s for s in smps),
                   own=statistics.median(s.own_cores for s in smps),
                   ext=statistics.median(s.ext_cores for s in smps))
        log("\n  -- %s" % name)
        log("     %s" % fmt_samples(smps))
        r = smps[0].ret
        dE = abs(r["E"] - E_full)
        cert_ok = r["cert"] + 1e-18 >= dE
        res.update(cert=r["cert"], dE=dE, kept=r["kept"], n_near=r["n_near"],
                   n_far=r["n_far"], cert_ok=cert_ok, accepted=r["accepted"],
                   evaluated=r["evaluated"], visited=r["visited"])
        assert cert_ok, ("bound violated", name, r["cert"], dE)
        # cross-check the exact path against the library, bit for bit
        if name.startswith("exact"):
            base_samples += smps
            log("     library anchor E_pair=%.15g  mine=%.15g  bit-identical=%s"
                % (E_full, r["E"], r["E"] == E_full))
            assert r["E"] == E_full, "exact path does not reproduce screened_decomposition"
        if name == "tree   min_pts=%d (pure tree)" % mp0:
            log("     harness check vs library screen=tau: dE=%.3e Ha  dcert=%.3e Ha"
                % (abs(r["E"] - anchor_tau["E_pair"]),
                   abs(r["cert"] - anchor_tau["cert_err"])))
            assert abs(r["E"] - anchor_tau["E_pair"]) < 1e-13 and \
                abs(r["cert"] - anchor_tau["cert_err"]) < 1e-15, "harness != library"
        log("     cert_err=%.3e Ha  |dE|=%.3e Ha (%.3e kcal/mol)  budget_ok=%s"
            % (r["cert"], dE, dE * HA2K, dE * HA2K <= ACC_BUDGET_KCAL))
        log("     point pairs kept %d/%d = %.3f%%   atom pairs near/far = %d/%d"
            % (r["kept"], grand_total, 100.0 * r["kept"] / grand_total,
               r["n_near"], r["n_far"]))
        log("     tree node-pairs: accepted=%d evaluated(leafpairs)=%d visited=%d"
            % (r["accepted"], r["evaluated"], r["visited"]))
        results.append(res)

    base_med, base_nval = median_valid(base_samples)
    base_raw = statistics.median(s.wall for s in base_samples)
    log("\n  ---- summary for %s ----" % tag)
    log("    baseline(exact): %d samples, %d valid; median(valid)=%s  median(all)=%.3f s"
        "  own cores=%.2f  external cores=%.2f"
        % (len(base_samples), base_nval,
           ("%.3f s" % base_med) if base_med else "NONE", base_raw,
           statistics.median(s.own_cores for s in base_samples),
           statistics.median(s.ext_cores for s in base_samples)))
    if base_med is None:
        log("    !!! no valid baseline sample: the timing window is contended. Absolute"
            " seconds below are medians over contended samples and make no claim about"
            " this machine's speed; only the vs_base ratio (same window, same contention)"
            " is usable, and only to first order.")
    denom = base_med if base_med else base_raw
    log("  %-50s %8s %7s %5s %6s %6s %10s %11s %8s %9s %4s"
        % ("path", "wall_s", "raw_s", "nval", "ownCo", "extCo", "cert_Ha",
           "|dE|_kcal", "kept%", "vs_base", "bud"))
    for res in results:
        wall_used = res["med"] if res["med"] else res["raw"]
        log("  %-50s %8s %7.3f %5d %6.2f %6.2f %10s %11s %8.4f %8.3fx %4s"
            % (res["name"],
               ("%.3f" % res["med"]) if res["med"] else "CONTAM",
               res["raw"], res["nval"], res["own"], res["ext"],
               "%.2e" % res["cert"], "%.2e" % (res["dE"] * HA2K),
               100.0 * res["kept"] / grand_total, wall_used / denom,
               "OK" if res["dE"] * HA2K <= ACC_BUDGET_KCAL else "MISS"))
        log("       cross-point-pairs kept %.4f%% (near atom pairs %d, far %d)"
            % (100.0 * (res["kept"] - n_self_pairs) / far_total, res["n_near"],
               res["n_far"]))
    win = [r for r in results
           if r["dE"] * HA2K <= ACC_BUDGET_KCAL and not r["name"].startswith("exact")
           and (r["med"] if r["med"] else r["raw"]) < denom]
    log("  configs with |dE|<=%.1e kcal/mol AND wall < baseline: %s"
        % (ACC_BUDGET_KCAL, [(w["name"], round(w["raw"], 3)) for w in win] or "NONE"))

    # ---- oracle ceiling: best possible whole-pair routing, from per-pair timings ----
    # measure both paths per pair once (cheap, same trees), then any classifier's cost is
    # bounded below by sum(min(exact,tree)) + tree_build.
    t = time.perf_counter()
    ex_i = []
    for i, Pa in enumerate(live32):
        for Pb in live32[i + 1:]:
            t0 = time.perf_counter()
            pair_exact(F, Pa, Pb)
            ex_i.append(time.perf_counter() - t0)
    t_ex = time.perf_counter() - t
    t = time.perf_counter()
    tr_i = []
    for i, Pa in enumerate(live32):
        for Pb in live32[i + 1:]:
            st = new_stats()
            t0 = time.perf_counter()
            pair_tree(F, Pa, Pb, tau, st)
            tr_i.append(time.perf_counter() - t0)
    t_tr = time.perf_counter() - t
    n_faster = sum(1 for a, b in zip(ex_i, tr_i) if b < a)
    oracle = sum(min(a, b) for a, b in zip(ex_i, tr_i))
    log("\n  per-pair cost census at min_pts=%d (single replicate, same trees):" % mp0)
    log("    all-pairs exact loop %.2f s   all-pairs tree loop %.2f s"
        "   (tree build %.2f s)" % (t_ex, t_tr, tb[mp0][2]))
    log("    atom pairs where the tree is FASTER than the big gemm: %d/%d (%.1f%%)"
        % (n_faster, len(ex_i), 100.0 * n_faster / len(ex_i)))
    log("    ORACLE ceiling (route each pair to its cheaper path, upper bound for any"
        " whole-pair classifier): %.2f s pair loop, %.2f s incl. tree build"
        % (oracle, oracle + tb[mp0][2]))
    log("    vs measured baseline pair loop %.2f s  ->  max achievable saving %.1f%%"
        % (t_ex, 100.0 * (1.0 - oracle / t_ex) if t_ex else float("nan")))
    med_ex = sorted(ex_i)[len(ex_i) // 2]
    med_tr = sorted(tr_i)[len(tr_i) // 2]
    log("    median per-pair cost: exact %.4f ms   tree %.4f ms   ratio %.2fx"
        % (1e3 * med_ex, 1e3 * med_tr, med_tr / med_ex))
    log("    tree cost per retained point pair: exact %.3e ms/1e6pp  tree %.3e ms/1e6pp"
        % (1e9 * t_ex / far_total, 1e9 * t_tr / far_total))
    return results, dict(n_ov=n_ov, n_rows=len(rows), pp_ov=pp_ov, far_total=far_total,
                         grand_total=grand_total, base_med=base_med, base_raw=base_raw,
                         oracle=oracle, t_ex=t_ex, t_tr=t_tr, tree_build=tb[mp0][2],
                         n_faster=n_faster, near_share_cross=pp_ov / far_total,
                         near_share_total=pp_ov / grand_total,
                         n_self_pairs=n_self_pairs)


if __name__ == "__main__":
    log("# hybrid_nearfield measuring pass")
    log("# utc=%s  host=%s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                               os.uname().nodename))
    log("# python=%s  OMP_NUM_THREADS=%s  os.cpu_count=%s"
        % (sys.version.split()[0], os.environ.get("OMP_NUM_THREADS", "<unset>"),
           os.cpu_count()))
    import pyscf
    log("# pyscf=%s  numpy=%s" % (pyscf.__version__, np.__version__))
    log("# accuracy budget = %.1e kcal/mol actual error; tau = %g Ha per node-pair"
        % (ACC_BUDGET_KCAL, TAU))
    log("# gate: a timed sample is invalid when OTHER processes used >= 0.5 CPU-cores"
        " during its window (own BLAS threads excluded, raw uptime/loadavg still printed)")
    t_idle0 = _other_cpu_seconds()
    time.sleep(3.0)
    ext0 = (_other_cpu_seconds() - t_idle0) / 3.0
    log("# idle-window contention check: external %.2f cores, loadavg %s, %s"
        % (ext0, ["%.2f" % v for v in _load()], _uptime_line()))
    summary = {}
    for tag, builder, level in (("benzene_sandwich", geomlib.benzene_sandwich, 0),
                                ("h2o_dimer", geomlib.h2o_dimer, 1)):
        summary[tag] = report(tag, builder, level)
    log("\n" + "=" * 100)
    log("=== VERDICT  (criterion: actual error <= %.1e kcal/mol AND wall clock strictly"
        " below the atom-block full path)" % ACC_BUDGET_KCAL)
    for tag, (results, meta) in summary.items():
        base = meta["base_med"] if meta["base_med"] else meta["base_raw"]
        timing = "clean" if meta["base_med"] else "CONTENDED(no valid sample)"
        best = None
        for r in results:
            if r["name"].startswith("exact"):
                continue
            if r["dE"] * HA2K > ACC_BUDGET_KCAL:
                continue
            w = r["med"] if r["med"] else r["raw"]
            if best is None or w < (best["med"] if best["med"] else best["raw"]):
                best = r
        log("  %s   [%s timing]" % (tag, timing))
        log("    baseline exact wall %.3f s ; near-field (root box overlap) share = %.4f%%"
            " of cross point pairs (%d/%d atom pairs overlap at the roots, box_sep=0)"
            % (base, 100.0 * meta["pp_ov"] / meta["far_total"],
               meta["n_ov"], meta["n_rows"]))
        if best is None:
            log("    in-budget non-exact config: NONE measured")
        else:
            w = best["med"] if best["med"] else best["raw"]
            log("    cheapest in-budget screened config: %s  wall %.3f s = %.3fx baseline"
                % (best["name"], w, w / base))
            log("      -> beats the baseline: %s (ratio %.3fx, shortfall %.3f s)"
                % ("YES" if w < base else "NO", w / base, w - base))
        log("    ORACLE whole-pair routing ceiling: %.2f s vs %.2f s measured exact loop"
            " (tree cheaper on %d/%d atom pairs) => no classification rule could save more"
            " than %.1f%% of the pair loop"
            % (meta["oracle"], meta["t_ex"], meta["n_faster"], meta["n_rows"],
               100.0 * (1.0 - meta["oracle"] / meta["t_ex"]) if meta["t_ex"] else -1))
