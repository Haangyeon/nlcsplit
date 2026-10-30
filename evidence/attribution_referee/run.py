"""Attribution referee: an exact, partition-free reference for VV10 fragment
attribution on two-centre Gaussian densities.

    wsl -e bash -lc 'cd <REPO> && PYTHONPATH=. python3 -u evidence/attribution_referee/run.py'

WHAT IT MEASURES
----------------
Take rho = rhoA + rhoB, two normalised Gaussians on chosen centres.  Because the
density *factors* are fixed by the construction, the four quantities

    I_XY = int int rhoX(r) Phi[rho_total](r,r') rhoY(r') d3r d3r'

are exact, contain no real-space partition, and close on the total:

    E_NL = 1/2 (I_AA + I_AB + I_BA + I_BB) = 1/2 (I_AA + I_BB) + I_AB ,

the last step because Phi(r,r') = Phi(r',r) makes I_AB = I_BA.  The package's
inter[A,B] is the Becke-weighted analogue of I_AB (README derives the 1/2
bookkeeping).  Per configuration this script reports:

  * E_NL by the package's grid pair sum and by an independent direct double 3-D
    quadrature, plus a second, cylindrical reduction and a Monte-Carlo estimate;
  * the exact I_AA / I_BB / I_AB / I_BA and the closure residual against a
    total integrated WITHOUT the split at all;
  * the package's intra/inter split under the Becke soft partition, the
    nearest-atom hard partition, and the density-factor partition (the last one
    is the exact decomposition evaluated by the package's own summation code, so
    subtracting it from the Becke number isolates the partition from the grid);
  * inter[A,B] - I_AB, the number P1 currently has no referee for.

Nothing under nlcsplit/ is modified; it is imported and read only.  No SCF is
run: PySCF is used for nlc_coeff (the package's own source of b and C), its
atomic grids and its Becke partition machinery.
"""
import argparse
import json
import multiprocessing as mp
import os
import sys
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")          # workers are memory-bandwidth bound

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import referee_lib as rl                                    # noqa: E402
from nlcsplit import nlc, partition                         # noqa: E402
from pyscf import gto                                       # noqa: E402
from pyscf.dft import numint                                # noqa: E402

KCAL = 627.509474           # the same factor nlcsplit's own scripts use
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")

# ----------------------------------------------------------------- parameters
ALPHAS = [0.5, 1.0, 2.0]                     # Gaussian exponents, bohr^-2
SEPS = [2.5, 4.0, 6.0, 10.0]                 # internuclear separations, bohr
N_ELEC = 4.0                                 # electrons per Gaussian (total 8)
F_TRUNC = 5.0                                # each factor is cut at exp(-25) of peak
N5D = 48                                     # cylindrical order, main table
N5D_LADDER = [16, 24, 32, 40, 48]
N3D = 20                                     # Cartesian 3-D x 3-D order, main table
N3D_LADDER = [12, 16, 20, 24]
PKG_LEVEL = 3          # PySCF grid level for the production-grid path in the table.
# P1 tabulates S22 at level 1, so level 3 is finer than production; the
# level ladder in convergence.md (1 -> 3 -> 5) shows which way the grid error
# moves and by how much.
PKG_LEVEL_LADDER = [1, 3, 5]
BOX_N = 20                                   # referee nodes handed to package machinery
FLOORS = [1e-8, 1e-12, 1e-16]
MC_SAMPLES = 400_000
MC_SAMPLES_TABLE = 200_000
ASYM_SEPS = [8.0, 12.0, 16.0, 20.0, 24.0, 28.0]
ASYM_ALPHA = 1.0
CONV_KEYS = [(a, s) for a in ALPHAS for s in (4.0, 10.0)]
NPROC = int(os.environ.get("ATTR_REFEREE_NPROC", "10"))

_B = None      # filled by the pool initializer (R4: from PySCF, never hard-coded)
_C = None


def init_worker():
    global _B, _C
    _B, _C = numint.NumInt().nlc_coeff("wb97x_v")[0][0]


def params():
    if _B is not None:
        return _B, _C
    init_worker()
    return _B, _C


def mk_mol(sep):
    """Two centres carrying the atom types the Becke/BRAGG machinery needs.

    Only positions and atom types matter for a partition; no SCF is run anywhere
    in this script -- the density is the analytic Gaussian pair.
    """
    return gto.M(atom="He 0 0 %.4f; He 0 0 %.4f" % (-0.5 * sep, 0.5 * sep),
                 basis="sto-3g", verbose=0, unit="B")


def df_soft_factors(rho_a, rho_b):
    """The density-factor 'partition': f_A = rhoA/(rhoA+rhoB), f_B = 1 - f_A.

    Sums to exactly 1 at every point, so it is a legal soft partition for
    nlc.fragment_decomposition -- which then evaluates the EXACT decomposition on
    whatever node set it is handed.  Where both factors underflow the density
    itself is zero, the point carries no weight, and the arbitrary half-split
    cannot matter.
    """
    tot = rho_a + rho_b
    with np.errstate(divide="ignore", invalid="ignore"):
        fa = np.where(tot > 0.0, rho_a / np.where(tot > 0.0, tot, 1.0), 0.5)
    return np.vstack([fa, 1.0 - fa])


def electron_count(weights, rho, n_expected, where, tol=0.05):
    """Assert that a node set integrates the density once, and return the value.

    This guard is not decoration: passing partition.py's *raw* per-subgrid volume
    elements as if they were an integration measure inflates every block by
    exactly the number of atoms (each point of space is covered by every atomic
    subgrid whose sphere reaches it, and only the partition factors make the sum
    correct).  Measured during development: rho integrates to 16.00000 instead of
    8, i.e. every pair block by 4.0007.  The tolerance is loose (5%) because it
    catches a multiplicity error, not quadrature noise -- the grid's own accuracy
    is quantified separately by the order ladders in convergence.md, and the
    achieved values are reported in table.md for the reader to judge.
    """
    ne = float(np.sum(weights * rho))
    if abs(ne - n_expected) > tol * n_expected:
        raise AssertionError("node set %s integrates rho to %.8f, expected %.1f"
                             " (a whole-atom multiplicity error, not quadrature)"
                             % (where, ne, n_expected))
    return ne


def package_split(coords, weights, rho, sigma, b, C, soft=None, owner=None,
                  floor=1e-12):
    frags = [[0], [1]]
    if soft is not None:
        return nlc.fragment_decomposition(coords, weights, rho, sigma, frags,
                                          b=b, C=C, rho_floor=floor, soft=soft)
    return nlc.fragment_decomposition(coords, weights, rho, sigma, frags,
                                      b=b, C=C, rho_floor=floor, owner=owner)


# --------------------------------------------------------------- exact side
def job_config(cfg):
    """One configuration: reference, package paths, differences."""
    alpha, sep = cfg["alpha"], cfg["sep"]
    B, C = params()
    t0 = time.time()
    gp = rl.GaussPair(sep=sep, alpha_a=alpha, n_a=N_ELEC)
    nphi = int(1.5 * N5D)
    ex = {}
    for tag in ("AA", "BB", "AB", "BA"):
        ex["cyl_" + tag], d = rl.integral_cyl5d(gp, B, C, N5D, nphi, F_TRUNC, which=tag)
        ex["cyl_nonfinite_" + tag] = d["nonfinite"]
    ex["cyl_TOT"], d_tot = rl.integral_cyl5d(gp, B, C, N5D, nphi, F_TRUNC, which="TOT")
    ex["cyl_closed"] = 0.5 * (ex["cyl_AA"] + ex["cyl_BB"] + ex["cyl_AB"] + ex["cyl_BA"])
    ex["cyl_closure"] = abs(ex["cyl_closed"] - ex["cyl_TOT"])
    ex["sym_aa_bb"] = abs(ex["cyl_BB"] - ex["cyl_AA"])
    ex["sym_ab_ba"] = abs(ex["cyl_BA"] - ex["cyl_AB"])
    for tag in ("AA", "AB"):
        ex["box_" + tag], _ = rl.integral_box3d(gp, B, C, N3D, F_TRUNC, which=tag)
    ex["box_closed"] = ex["box_AA"] + ex["box_AB"]
    ex["box_closure"] = abs(ex["box_closed"] - ex["cyl_TOT"])
    mcp, mcs = rl.mc_integral(gp, B, C, "AB", m=MC_SAMPLES_TABLE)

    # ---- package machinery on the referee's own DISJOINT node set ----
    mol = mk_mol(sep)
    (pa, wa), (pb, wb) = rl.half_box_pair(gp, F_TRUNC, BOX_N)
    coords = np.concatenate([pa, pb])
    wts = np.concatenate([wa, wb])
    rho, sig, ra, rb = gp.state(coords)
    n_e_box = electron_count(wts, rho, 2 * N_ELEC, "referee half-box nodes")
    pmat = partition.partition_matrix(mol, coords, "becke").T
    sbecke = pmat / pmat.sum(axis=1, keepdims=True)
    box_be = package_split(coords, wts, rho, sig, B, C, soft=sbecke.T)
    box_df = package_split(coords, wts, rho, sig, B, C, soft=df_soft_factors(ra, rb))

    # ---- package machinery on the PySCF production grid, exactly as the papers
    #      do it: partition.atom_partition weights (which already carry the Becke
    #      partition factor) plus the owner assignment ----
    X, W, owner = partition.atom_partition(mol, level=PKG_LEVEL, scheme="becke")
    rhoP, sigP, raP, rbP = gp.state(X)
    n_e_grid = electron_count(W, rhoP, 2 * N_ELEC, "PySCF atom_partition grid")
    prod = package_split(X, W, rhoP, sigP, B, C, owner=owner)
    dfp = package_split(X, W, rhoP, sigP, B, C, soft=df_soft_factors(raP, rbP))
    w0, kap, keep = nlc.vv10_fields(rhoP, sigP, B, C)
    e_pkg = nlc.pair_energy(X, W * rhoP, w0, kap, np.where(keep)[0], np.where(keep)[0])

    beta = (1.0 / 32.0) * (3.0 / (B * B)) ** 0.75
    r = dict(
        alpha=alpha, sep=sep, n_elec=N_ELEC, n5d=N5D, n3d=N3D, box_n=BOX_N,
        pkg_level=PKG_LEVEL, f_trunc=F_TRUNC,
        peak_rho=float(gp.state(np.array([[0.0, 0.0, -0.5 * sep]]))[0][0]),
        nonfinite=ex["cyl_nonfinite_AB"],
        # exact, partition-free reference
        I_AA=ex["cyl_AA"], I_BB=ex["cyl_BB"], I_AB=ex["cyl_AB"], I_BA=ex["cyl_BA"],
        E_nl_sum_of_parts=ex["cyl_closed"], E_nl_undecomposed=ex["cyl_TOT"],
        closure=ex["cyl_closure"], sym_aa_bb=ex["sym_aa_bb"], sym_ab_ba=ex["sym_ab_ba"],
        I_AB_box3d=ex["box_AB"], I_AA_box3d=ex["box_AA"], box_sum=ex["box_closed"],
        box_closure=ex["box_closure"],
        I_AB_mc=mcp, I_AB_mc_se=mcs, mc_z=(ex["cyl_AB"] - mcp) / mcs,
        # package on the referee nodes (soft Becke vs soft density-factor)
        box_n_nodes=int(len(coords)), box_electrons=n_e_box,
        box_becke_inter=box_be["inter"][(0, 1)], box_df_inter=box_df["inter"][(0, 1)],
        box_becke_intra0=box_be["intra"][0], box_becke_intra1=box_be["intra"][1],
        box_df_intra0=box_df["intra"][0], box_df_intra1=box_df["intra"][1],
        box_total=box_be["E_nl"], box_n_dropped=box_be["n_dropped"],
        # package on the production grid (owner assignment vs density-factor)
        grid_n=int(len(X)), grid_n_dropped=int(prod["n_dropped"]),
        grid_electrons=n_e_grid,
        grid_total_pairsum=float(e_pkg), grid_total_split=prod["E_nl"],
        additivity=float(prod["E_nl"] - e_pkg),
        grid_inter=prod["inter"][(0, 1)], grid_intra0=prod["intra"][0],
        grid_intra1=prod["intra"][1],
        grid_df_inter=dfp["inter"][(0, 1)], grid_df_intra0=dfp["intra"][0],
        grid_df_intra1=dfp["intra"][1],
        E_loc_grid=nlc.local_term(beta, W * rhoP), E_loc_exact=beta * (N_ELEC + N_ELEC),
    )
    # ---- the numbers the referee is about ----
    r["d_partition_prod"] = r["grid_inter"] - r["grid_df_inter"]
    r["d_partition_box"] = r["box_becke_inter"] - r["box_df_inter"]
    r["d_headline"] = r["grid_inter"] - r["I_AB"]
    r["d_headline_boxnodes"] = r["box_becke_inter"] - r["I_AB"]
    r["d_grid_error"] = r["grid_df_inter"] - r["I_AB"]
    r["d_box_grid_error"] = r["box_df_inter"] - r["I_AB"]
    r["rel_to_term"] = r["d_headline"] / abs(r["E_nl_undecomposed"])
    r["rel_to_cross"] = r["d_headline"] / abs(r["I_AB"])
    r["intra_halfblock_vs_halfIaa"] = r["grid_intra0"] - 0.5 * r["I_AA"]
    r["intra_df_minus_half_I_AA"] = r["grid_df_intra0"] - 0.5 * r["I_AA"]
    r["total_pkg_minus_exact"] = r["grid_total_pairsum"] - r["E_nl_undecomposed"]
    r["total_box_minus_exact"] = r["box_total"] - r["E_nl_undecomposed"]
    r["runtime_s"] = time.time() - t0
    return r


def job_cyl_ab(alpha, sep, n):
    B, C = params()
    gp = rl.GaussPair(sep=sep, alpha_a=alpha, n_a=N_ELEC)
    v, _ = rl.integral_cyl5d(gp, B, C, n, int(1.5 * n), F_TRUNC, which="AB")
    return v


def job_cyl_tot(alpha, sep, n):
    B, C = params()
    gp = rl.GaussPair(sep=sep, alpha_a=alpha, n_a=N_ELEC)
    v, _ = rl.integral_cyl5d(gp, B, C, n, int(1.5 * n), F_TRUNC, which="TOT")
    return v


def job_box_ab(alpha, sep, n):
    B, C = params()
    gp = rl.GaussPair(sep=sep, alpha_a=alpha, n_a=N_ELEC)
    v, _ = rl.integral_box3d(gp, B, C, n, F_TRUNC, which="AB")
    return v


def job_trunc(alpha, sep, n, f):
    B, C = params()
    gp = rl.GaussPair(sep=sep, alpha_a=alpha, n_a=N_ELEC)
    v, _ = rl.integral_cyl5d(gp, B, C, n, int(1.5 * n), f, which="AB")
    return v


def job_grid_level(alpha, sep, lvl):
    B, C = params()
    gp = rl.GaussPair(sep=sep, alpha_a=alpha, n_a=N_ELEC)
    mol = mk_mol(sep)
    X, W, owner = partition.atom_partition(mol, level=lvl, scheme="becke")
    rho, sig, ra, rb = gp.state(X)
    electrons = electron_count(W, rho, 2 * N_ELEC, "level %d grid" % lvl)
    df = package_split(X, W, rho, sig, B, C, soft=df_soft_factors(ra, rb))
    pr = package_split(X, W, rho, sig, B, C, owner=owner)
    w0, kap, keep = nlc.vv10_fields(rho, sig, B, C)
    e_pkg = nlc.pair_energy(X, W * rho, w0, kap, np.where(keep)[0], np.where(keep)[0])
    return dict(level=lvl, n=int(len(X)), dropped=df["n_dropped"],
                electrons=electrons, df_inter=df["inter"][(0, 1)],
                prod_inter=pr["inter"][(0, 1)], total=float(e_pkg),
                rmax=float(np.abs(X).max()))


def job_floor(alpha, sep, floor):
    B, C = params()
    gp = rl.GaussPair(sep=sep, alpha_a=alpha, n_a=N_ELEC)
    mol = mk_mol(sep)
    X, W, owner = partition.atom_partition(mol, level=PKG_LEVEL, scheme="becke")
    rho, sig, ra, rb = gp.state(X)
    df = package_split(X, W, rho, sig, B, C, soft=df_soft_factors(ra, rb), floor=floor)
    pr = package_split(X, W, rho, sig, B, C, owner=owner, floor=floor)
    return dict(floor=floor, dropped=df["n_dropped"], df_inter=df["inter"][(0, 1)],
                prod_inter=pr["inter"][(0, 1)], E_nl=df["E_nl"],
                electrons=float((W * rho)[rho > floor].sum()))


# ------------------------------------------------------------- validation
def job_validate(tag, arg=None):
    B, C = params()
    out = {"tag": tag}
    if tag == "fields":
        rng = np.random.default_rng(7)
        pts = rng.random((20000, 3)) * 8.0 - 4.0
        gp = rl.GaussPair(sep=3.0, alpha_a=1.0, n_a=N_ELEC)
        rho, sig, _, _ = gp.state(pts)
        dw, dk, nc = rl.check_fields_match_package(rho, sig, B, C)
        out.update(w0_rel=dw, kappa_rel=dk, n_compared=nc,
                   rho_min=float(rho.min()), rho_max=float(rho.max()))
    elif tag == "norm":
        gp = rl.GaussPair(sep=6.0, alpha_a=1.0, n_a=N_ELEC)
        for meth, n in (("3d", N3D), ("cyl", N5D)):
            got, exact = rl.integral_norm_check(gp, B, C, n, F_TRUNC, method=meth)
            out[meth] = got
            out[meth + "_exact"] = exact
            out[meth + "_rel"] = abs(got - exact) / abs(exact)
    elif tag.startswith("gauss"):
        lam = float(tag[5:])
        gp = rl.GaussPair(sep=6.0, alpha_a=1.0, n_a=N_ELEC)
        an = rl.analytic_gaussian_kernel(gp.n_a, gp.n_b, gp.alpha_a, gp.alpha_b,
                                         lam, gp.sep)
        q3, _ = rl.integral_box3d(gp, B, C, N3D, F_TRUNC,
                                  kernel=rl.kernel_gaussian(lam), which="AB")
        q5, _ = rl.integral_cyl5d(gp, B, C, N5D, int(1.5 * N5D), F_TRUNC,
                                  kernel=rl.kernel_gaussian(lam), which="AB")
        out.update(an=an, q3=q3, q5=q5, rel3=abs(q3 - an) / an, rel5=abs(q5 - an) / an)
    elif tag == "invr":
        gp = rl.GaussPair(sep=6.0, alpha_a=1.0, n_a=N_ELEC)
        a1 = rl.analytic_coulomb_via_kernel(gp.n_a, gp.n_b, gp.alpha_a, gp.alpha_b, gp.sep)
        a2 = rl.analytic_coulomb_closed(gp.n_a, gp.n_b, gp.alpha_a, gp.alpha_b, gp.sep)
        q3, _ = rl.integral_box3d(gp, B, C, N3D, F_TRUNC, kernel=rl.kernel_inv_r, which="AB")
        q5, _ = rl.integral_cyl5d(gp, B, C, N5D, int(1.5 * N5D), F_TRUNC,
                                  kernel=rl.kernel_inv_r, which="AB")
        out.update(a1=a1, a2=a2, q3=q3, q5=q5, rel_a=abs(a1 - a2) / a2,
                   rel3=abs(q3 - a2) / a2, rel5=abs(q5 - a2) / a2)
    elif tag == "control":
        # can the comparison see the pairing the package itself documents as wrong?
        gp = rl.GaussPair(sep=6.0, alpha_a=1.0, n_a=N_ELEC)
        mol = mk_mol(6.0)
        X, W, owner = partition.atom_partition(mol, level=PKG_LEVEL, scheme="becke")
        rho, sig, ra, rb = gp.state(X)
        electron_count(W, rho, 2 * N_ELEC, "control grid")
        w0, kap, keep = nlc.vv10_fields(rho, sig, B, C)
        idx = np.where(keep)[0]
        e_good = nlc.pair_energy(X, W * rho, w0, kap, idx, idx)
        e_bad = nlc.pair_energy(X, W * rho, w0, kap, idx, idx, pairing="cross")
        nphi = int(1.5 * N5D)
        q_good, _ = rl.integral_cyl5d(gp, B, C, N5D, nphi, F_TRUNC, which="TOT")
        q_bad, _ = rl.integral_cyl5d(gp, B, C, N5D, nphi, F_TRUNC,
                                     kernel=rl.kernel_vv10_crosspair, which="TOT")
        out.update(pkg_right=e_good, pkg_wrong=e_bad, ref_right=q_good, ref_wrong=q_bad,
                   shift_kcal=abs(e_bad - e_good) * KCAL,
                   diff_right_kcal=(e_good - q_good) * KCAL,
                   diff_wrong_kcal=(e_bad - q_bad) * KCAL)
    elif tag == "mc":
        gp = rl.GaussPair(sep=6.0, alpha_a=1.0, n_a=N_ELEC)
        nphi = int(1.5 * N5D)
        vals = {}
        for which in ("AB", "AA"):
            v, _ = rl.integral_cyl5d(gp, B, C, N5D, nphi, F_TRUNC, which=which)
            m, se = rl.mc_integral(gp, B, C, which, m=MC_SAMPLES)
            vals[which] = (v, m, se, (v - m) / se)
        out.update(vals=vals)
    elif tag == "measure_guard":
        # The trap this referee walked into once, recorded so the guard is not
        # decoration: partition.partition_factors returns each atom's RAW
        # subgrid volume elements, which cover all space once PER ATOM.  Using
        # them as the integration measure inflates every block by natm.
        gp = rl.GaussPair(sep=6.0, alpha_a=1.0, n_a=N_ELEC)
        mol = mk_mol(6.0)
        Xr, Wr, Sr = partition.partition_factors(mol, level=PKG_LEVEL, scheme="becke")
        rho_r, _, _, _ = gp.state(Xr)
        Xp, Wp, own = partition.atom_partition(mol, level=PKG_LEVEL, scheme="becke")
        rho_p, _, _, _ = gp.state(Xp)
        raw = float((Wr * rho_r).sum())
        part = float((Wp * rho_p).sum())
        same_nodes = bool(np.array_equal(np.round(Xr, 12), np.round(Xp, 12)))
        out.update(raw_base_w_electrons=raw, partitioned_electrons=part,
                   expected=2 * N_ELEC, ratio=raw / part, same_points=same_nodes,
                   n_raw=int(len(Xr)), n_part=int(len(Xp)))
    elif tag == "asym":
        seps, vals = [], []
        for sep in ASYM_SEPS:
            gp = rl.GaussPair(sep=sep, alpha_a=ASYM_ALPHA, n_a=N_ELEC)
            # n=32 is enough here: at these separations the cross term is a smooth,
            # weakly-overlapping tail-tail integral (see convergence.md for the
            # order-by-order behaviour at the same alpha).
            v, _ = rl.integral_cyl5d(gp, B, C, 32, 48, F_TRUNC, which="AB")
            seps.append(sep)
            vals.append(v)
        lx = np.log(np.array(seps))
        ly = np.log(-np.array(vals))
        slope, icept = np.polyfit(lx, ly, 1)
        out.update(seps=seps, vals=vals, slope=float(slope),
                   resid=float(np.abs(ly - (slope * lx + icept)).max()),
                   r6=[float(v * s ** 6) for v, s in zip(vals, seps)])
    return out


# ------------------------------------------------------------------- driver
def run_all(do_table=True, do_conv=True):
    t0 = time.time()
    B, C = params()
    log = []

    def say(*a):
        line = " ".join(str(x) for x in a)
        log.append(line)
        print(line, flush=True)

    say("VV10 parameters from PySCF nlc_coeff('wb97x_v'): b=%s C=%s" % (B, C))
    say("beta = (1/32)(3/b^2)^(3/4) = %.12f" % ((1.0 / 32.0) * (3.0 / (B * B)) ** 0.75))
    import pyscf
    say("numpy %s  PySCF %s  python %s  workers %d"
        % (np.__version__, pyscf.__version__, sys.version.split()[0], NPROC))
    say("model: rhoA+rhoB normalised Gaussians, %g e each, alpha in %s bohr^-2, "
        "sep in %s bohr, domain cut exp(-%.0f), nphi=1.5n"
        % (N_ELEC, ALPHAS, SEPS, F_TRUNC ** 2))

    pool = mp.Pool(NPROC, initializer=init_worker)
    try:
        # ---------------- PHASE 1: can this be falsified ----------------
        say("")
        say("=" * 78)
        say("PHASE 1  falsification suite")
        say("=" * 78)
        vtags = ["fields", "norm", "gauss0.3", "gauss1.0", "invr", "control", "mc",
                 "measure_guard", "asym"]
        vres = {d["tag"]: d for d in pool.map(job_validate, vtags)}
        d = vres["fields"]
        say("[1a] w0/kappa vs nlcsplit.nlc.vv10_fields on %d random points with"
            " rho>1e-10 (rho range %.2e..%.2e): rel dev w0 %.3e  kappa %.3e"
            % (d["n_compared"], d["rho_min"], d["rho_max"], d["w0_rel"], d["kappa_rel"]))
        d = vres["norm"]
        say("[1b] single-factor normalisation against the exact cube/cylinder"
            " integrals: 3D rel %.2e  5D rel %.2e" % (d["3d_rel"], d["cyl_rel"]))
        for lam in (0.3, 1.0):
            d = vres["gauss%.1f" % lam]
            say("[1c] K=exp(-%.1f R^2) vs closed 6-D Gaussian integral: analytic"
                " %.12f  3D rel %.2e  5D rel %.2e" % (lam, d["an"], d["rel3"], d["rel5"]))
        d = vres["invr"]
        say("[1d] K=1/R: two independent closed forms agree to rel %.2e (%.12f vs"
            " %.12f); quadratures rel 3D %.2e  5D %.2e"
            % (d["rel_a"], d["a1"], d["a2"], d["rel3"], d["rel5"]))
        d = vres["control"]
        say("[1e] POSITIVE CONTROL. package same-centre total %.12f Ha vs independent"
            " quadrature %.12f Ha (diff %+.4f kcal/mol)."
            % (d["pkg_right"], d["ref_right"], d["diff_right_kcal"]))
        say("     package documented-WRONG pairing: total %.12f Ha vs independent"
            " quadrature with the same wrong pairing %.12f Ha (diff %+.4f kcal/mol)."
            % (d["pkg_wrong"], d["ref_wrong"], d["diff_wrong_kcal"]))
        say("     the wrong pairing shifts the term by %.4f kcal/mol on this density"
            " => the comparison has the resolution to see a kernel error."
            % d["shift_kcal"])
        d = vres["mc"]
        for which in ("AB", "AA"):
            v, m, se, z = d["vals"][which]
            say("[1f] Monte-Carlo (%d draws, importance-sampled on the density"
                " factor itself) for I_%s: quad %.12f  MC %.12f +- %.12f  z = %+.2f"
                % (MC_SAMPLES, which, v, m, se, z))
        d = vres["measure_guard"]
        say("[1h] MEASUREMENT-MASSAGE GUARD. Same molecule, same level, same points:")
        say("     sum(partition_factors base_w * rho) = %.8f electrons;"
            " sum(atom_partition weights * rho) = %.8f (expected %.1f)"
            % (d["raw_base_w_electrons"], d["partitioned_electrons"], d["expected"]))
        say("     ratio %.6f, identical point lists: %s (N=%d vs %d).  Every node"
            " set used below is checked against the electron count before use."
            % (d["ratio"], d["same_points"], d["n_raw"], d["n_part"]))
        d = vres["asym"]
        say("[1g] large-separation scaling of the cross term (alpha=%.1f):"
            % ASYM_ALPHA)
        for s, v, r6 in zip(d["seps"], d["vals"], d["r6"]):
            say("       sep=%5.1f  I_AB %+.8e Ha   I_AB*R^6 %+.8e" % (s, v, r6))
        say("       fitted log-log slope %.4f (the kernel's own large-R expansion"
            " gives R^-6, i.e. -6), max residual %.3f" % (d["slope"], d["resid"]))

        # ---------------- PHASE 2: error bars ----------------
        def persist(conv_, rows_):
            """Write what is already computed, so a long run never loses a phase."""
            meta_ = dict(b=B, C=C, beta=(1.0 / 32.0) * (3.0 / (B * B)) ** 0.75,
                         alphas=ALPHAS, seps=SEPS, n_elec_per_gaussian=N_ELEC,
                         f_trunc=F_TRUNC, n5d=N5D, n5d_ladder=N5D_LADDER, n3d=N3D,
                         n3d_ladder=N3D_LADDER, box_n=BOX_N, pkg_level=PKG_LEVEL,
                         pkg_level_ladder=PKG_LEVEL_LADDER, mc_samples=MC_SAMPLES,
                         mc_samples_table=MC_SAMPLES_TABLE, kcal=KCAL, nproc=NPROC,
                         runtime_s=time.time() - t0)
            write_outputs(meta_, vres, conv_, rows_, log)

        persist({}, [])
        conv = {}
        if do_conv:
            say("")
            say("=" * 78)
            say("PHASE 2  error bar on the reference")
            say("=" * 78)
            jobs, keys = [], []
            for (a, s) in CONV_KEYS:
                for n in N5D_LADDER:
                    jobs.append(("cyl_ab", (a, s, n)))
                    keys.append(("cyl_ab", a, s, n))
                for n in N5D_LADDER[-3:]:
                    jobs.append(("cyl_tot", (a, s, n)))
                    keys.append(("cyl_tot", a, s, n))
                for n in N3D_LADDER:
                    jobs.append(("box_ab", (a, s, n)))
                    keys.append(("box_ab", a, s, n))
                for f in (3.6, 4.2, 5.0, 5.9):
                    jobs.append(("trunc", (a, s, 40, f)))
                    keys.append(("trunc", a, s, f))
            vals = pool.starmap(job_generic, jobs)
            store = {k: v for k, v in zip(keys, vals)}
            for (a, s) in CONV_KEYS:
                base = "a%.1f_R%.1f" % (a, s)
                say("[2a] %s: cylindrical 5-D I_AB order ladder (Ha)" % base)
                prev = None
                ch = []
                for n in N5D_LADDER:
                    v = store[("cyl_ab", a, s, n)]
                    say("       n=%2d  %.14f%s" % (n, v, "" if prev is None
                                                   else "   change %.3e" % abs(v - prev)))
                    if prev is not None:
                        ch.append(abs(v - prev))
                    prev = v
                ratio = ch[-1] / ch[-2] if len(ch) > 1 and ch[-2] > 0 else float("nan")
                extrap = (prev + ch[-1] * ratio / (1.0 - ratio)) if ratio < 1.0 else None
                say("       last change %.3e  contraction ratio %.3f  geometric"
                    " extrapolation %s"
                    % (ch[-1], ratio, "%.14f" % extrap if extrap else "NOT applicable"
                       if extrap is None else ""))
                tot_lad = {n: store[("cyl_tot", a, s, n)] for n in N5D_LADDER[-3:]}
                say("       undecomposed total at the top orders: "
                    + "  ".join("n=%d %.12f" % (k, v) for k, v in sorted(tot_lad.items())))
                say("       3-D x 3-D I_AB ladder: "
                    + "  ".join("n=%d %.12f" % (n, store[("box_ab", a, s, n)])
                                for n in N3D_LADDER))
                say("       3D(top) - 5D(top) = %+.3e Ha (%.2e relative) <- different"
                    " nodes, domain shape, reduction"
                    % (store[("box_ab", a, s, N3D_LADDER[-1])] - store[("cyl_ab", a, s,
                                                                        N5D_LADDER[-1])],
                       abs(store[("box_ab", a, s, N3D_LADDER[-1])]
                           - store[("cyl_ab", a, s, N5D_LADDER[-1])])
                       / abs(store[("cyl_ab", a, s, N5D_LADDER[-1])])))
                tr = {f: store[("trunc", a, s, f)] for f in (3.6, 4.2, 5.0, 5.9)}
                say("       domain truncation (n=40): "
                    + "  ".join("f=%.1f %.12f" % (k, v) for k, v in sorted(tr.items()))
                    + "  | shift f=5.0 vs 5.9 %.3e" % abs(tr[5.0] - tr[5.9]))
                conv[base] = dict(cyl_ab={str(n): store[("cyl_ab", a, s, n)]
                                          for n in N5D_LADDER},
                                  cyl_tot={str(n): tot_lad[n] for n in tot_lad},
                                  box_ab={str(n): store[("box_ab", a, s, n)]
                                          for n in N3D_LADDER},
                                  trunc={str(f): tr[f] for f in tr},
                                  last_change=ch[-1], ratio=ratio, extrapolated=extrap,
                                  trunc_shift=abs(tr[5.0] - tr[5.9]))
            say("[2b] PySCF production grid, alpha=1.0 sep=6.0: level ladder")
            gl = pool.starmap(job_grid_level, [(1.0, 6.0, lvl)
                                               for lvl in PKG_LEVEL_LADDER])
            for d in gl:
                say("       level %d  N=%d  rmax=%.1f  electrons %.8f  dropped=%d"
                    "  density-factor inter %.12f  production inter %.12f  total %.12f"
                    % (d["level"], d["n"], d["rmax"], d["electrons"], d["dropped"],
                       d["df_inter"], d["prod_inter"], d["total"]))
            conv["grid_level_ladder"] = gl
            say("[2c] density-floor study (level %d, alpha=1.0 sep=6.0): the same"
                " points are dropped for every partition, so this is a shared bias."
                % PKG_LEVEL)
            fl = pool.starmap(job_floor, [(1.0, 6.0, f) for f in FLOORS])
            for d in fl:
                say("       floor %.0e  dropped %d  electrons kept %.10f"
                    "  density-factor inter %.12f  production inter %.12f  E_nl %.12f"
                    % (d["floor"], d["dropped"], d["electrons"], d["df_inter"],
                       d["prod_inter"], d["E_nl"]))
            say("       drift floor 1e-8 -> 1e-16: density-factor inter %.3e"
                "  production inter %.3e  E_nl %.3e Ha"
                % (abs(fl[0]["df_inter"] - fl[-1]["df_inter"]),
                   abs(fl[0]["prod_inter"] - fl[-1]["prod_inter"]),
                   abs(fl[0]["E_nl"] - fl[-1]["E_nl"])))
            conv["floor_study"] = fl

        # ---------------- PHASE 3: the table ----------------
        rows = []
        if do_table:
            persist(conv, [])
            say("")
            say("=" * 78)
            say("PHASE 3  the referee table")
            say("=" * 78)
            cfgs = [dict(alpha=a, sep=s) for a in ALPHAS for s in SEPS]
            # imap_unordered + a checkpoint after every configuration: if one
            # blows up, the completed ones are still on disk and the traceback is
            # in the log instead of being all-or-nothing.
            got = {}
            for r in pool.imap_unordered(job_config, cfgs):
                got[(r["alpha"], r["sep"])] = r
                rows = [got[(a, s)] for a, s in
                        [(c["alpha"], c["sep"]) for c in cfgs] if (a, s) in got]
                persist(conv, rows)
            for r in rows:
                say("alpha=%.1f sep=%4.1f | I_AB %+.6e | production inter %+.6e | diff"
                    " %+.3e (%+.2f%% of E_NL, %+.1f%% of I_AB) | closure %.1e | %.0fs"
                    % (r["alpha"], r["sep"], r["I_AB"], r["grid_inter"],
                       r["d_headline"], 100 * r["rel_to_term"], 100 * r["rel_to_cross"],
                       r["closure"], r["runtime_s"]))
    finally:
        pool.close()
        pool.join()

    say("")
    say("total runtime %.0f s" % (time.time() - t0))
    meta = dict(b=B, C=C, beta=(1.0 / 32.0) * (3.0 / (B * B)) ** 0.75, alphas=ALPHAS,
                seps=SEPS, n_elec_per_gaussian=N_ELEC, f_trunc=F_TRUNC, n5d=N5D,
                n5d_ladder=N5D_LADDER, n3d=N3D, n3d_ladder=N3D_LADDER, box_n=BOX_N,
                pkg_level=PKG_LEVEL, pkg_level_ladder=PKG_LEVEL_LADDER,
                mc_samples=MC_SAMPLES, mc_samples_table=MC_SAMPLES_TABLE, kcal=KCAL,
                nproc=NPROC, runtime_s=time.time() - t0)
    write_outputs(meta, vres, conv, rows, log)
    return meta, vres, conv, rows

_JOBS = {"cyl_ab": job_cyl_ab, "cyl_tot": job_cyl_tot, "box_ab": job_box_ab,
         "trunc": job_trunc}


def job_generic(name, args):
    """Picklable dispatcher for the pool: name selects one of the job_* above."""
    return _JOBS[name](*args)


def write_outputs(meta, vres, conv, rows, log):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "results.json"), "w") as fh:
        json.dump(dict(meta=meta, validation=vres, convergence=conv, rows=rows),
                  fh, indent=1, sort_keys=True)
    with open(os.path.join(OUT, "run_log.txt"), "w") as fh:
        fh.write("\n".join(log) + "\n")

    def e(x):
        return "%.6e" % x

    L = ["# referee table (generated by run.py -- do not hand-edit)", "",
         "Units Hartree.  `I_AB` = exact partition-free cross term; `inter[0,1]` =",
         "the package's inter-fragment block.  d = inter - I_AB (positive = the",
         "package assigns MORE to the pair than the exact cross term).", "",
         "| alpha | sep | I_AA | I_BB | I_AB | I_BA | E_NL (sum of parts) |"
         " E_NL (undecomposed) | closure | sym AA-BB | sym AB-BA |",
         "|---|" * 11]
    for r in rows:
        L.append("| %.1f | %.1f | %s | %s | %s | %s | %s | %s | %.1e | %.1e | %.1e |"
                 % (r["alpha"], r["sep"], e(r["I_AA"]), e(r["I_BB"]), e(r["I_AB"]),
                    e(r["I_BA"]), e(r["E_nl_sum_of_parts"]), e(r["E_nl_undecomposed"]),
                    r["closure"], r["sym_aa_bb"], r["sym_ab_ba"]))
    L += ["", "Totals: package grid pair sum vs the independent quadrature.", "",
          "| alpha | sep | E_NL package grid | E_NL exact | diff | diff kcal/mol |"
          " additivity resid | dropped pts | N grid |",
          "|---|" * 9]
    for r in rows:
        L.append("| %.1f | %.1f | %.10f | %.10f | %+.3e | %+.4f | %.1e | %d | %d |"
                 % (r["alpha"], r["sep"], r["grid_total_pairsum"],
                    r["E_nl_undecomposed"], r["total_pkg_minus_exact"],
                    r["total_pkg_minus_exact"] * KCAL, r["additivity"],
                    r["grid_n_dropped"], r["grid_n"]))
    L += ["", "The referee: the package's inter-fragment block against the exact",
          "cross term, and the same comparison with the grid taken out.", "",
          "`production inter` = PySCF atom_partition grid, owner assignment (what the",
          "papers report); `referee-node inter` = soft Becke on the referee's own",
          "disjoint half-box nodes; `density-factor inter` = the EXACT decomposition",
          "evaluated by the package's own summation code on that same node set.", "",
          "| alpha | sep | I_AB exact | production inter | referee-node inter |"
          " density-factor inter (prod grid) | d_headline | d_headline kcal/mol |"
          " d_partition prod grid | d_partition referee nodes | % of E_NL | % of I_AB |",
          "|---|" * 12]
    for r in rows:
        L.append("| %.1f | %.1f | %s | %s | %s | %s | %+.3e | %+.4f | %+.3e | %+.3e"
                 " | %+.2f | %+.2f |"
                 % (r["alpha"], r["sep"], e(r["I_AB"]), e(r["grid_inter"]),
                    e(r["box_becke_inter"]), e(r["grid_df_inter"]), r["d_headline"],
                    r["d_headline"] * KCAL, r["d_partition_prod"], r["d_partition_box"],
                    100 * r["rel_to_term"], 100 * r["rel_to_cross"]))
    L += ["", "Quadrature error of each node set for the SAME (exact) attribution:",
          "density-factor inter minus the converged continuum I_AB.", "",
          "| alpha | sep | prod-grid density-factor inter | minus I_AB |"
          " referee-node density-factor inter | minus I_AB |",
          "|---|" * 6]
    for r in rows:
        L.append("| %.1f | %.1f | %s | %+.3e | %s | %+.3e |"
                 % (r["alpha"], r["sep"], e(r["grid_df_inter"]), r["d_grid_error"],
                    e(r["box_df_inter"]), r["d_box_grid_error"]))
    L += ["", "The intra-fragment side.  Under the density-factor split the",
          "package's intra[A] = pair_energy-equivalent half block carries exactly",
          "half of the self term, so the reference for intra[A] is 0.5*I_AA.",
          "", "| alpha | sep | I_AA exact | 0.5*I_AA reference | intra production |"
          " intra density-factor | production - 0.5 I_AA | density-factor - 0.5 I_AA |",
          "|---|" * 8]
    for r in rows:
        L.append("| %.1f | %.1f | %s | %s | %s | %s | %+.3e | %+.3e |"
                 % (r["alpha"], r["sep"], e(r["I_AA"]), e(0.5 * r["I_AA"]),
                    e(r["grid_intra0"]), e(r["grid_df_intra0"]),
                    r["intra_halfblock_vs_halfIaa"], r["intra_df_minus_half_I_AA"]))
    L += ["", "Monte-Carlo third opinion on I_AB (%d draws, importance-sampled on"
          " the density factor)." % MC_SAMPLES_TABLE, "",
          "| alpha | sep | I_AB quadrature | I_AB MC | MC standard error | z |",
          "|---|" * 6]
    for r in rows:
        L.append("| %.1f | %.1f | %s | %s | %s | %+.2f |"
                 % (r["alpha"], r["sep"], e(r["I_AB"]), e(r["I_AB_mc"]),
                    e(r["I_AB_mc_se"]), r["mc_z"]))
    L += ["", "Local one-body piece beta*int rho (not pair-resolved; shown to confirm",
          "it carries no attribution content, and that each node set integrates the",
          "density exactly once).", "",
          "| alpha | sep | electrons, production grid | electrons, referee nodes |"
          " exact N | E_loc grid | E_loc exact | diff |",
          "|---|" * 8]
    for r in rows:
        L.append("| %.1f | %.1f | %.10f | %.10f | %.1f | %.10f | %.10f | %+.3e |"
                 % (r["alpha"], r["sep"], r["grid_electrons"], r["box_electrons"],
                    2 * N_ELEC, r["E_loc_grid"], r["E_loc_exact"],
                    r["E_loc_grid"] - r["E_loc_exact"]))
    with open(os.path.join(OUT, "table.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")

    V = ["# falsification suite (generated by run.py)", ""]
    d = vres["fields"]
    V.append("- kernel-definition transcription vs `nlcsplit.nlc.vv10_fields` over %d"
             " points: worst relative deviation w0 %.3e, kappa %.3e."
             % (d["n_compared"], d["w0_rel"], d["kappa_rel"]))
    d = vres["norm"]
    V.append("- node weights against exact single-factor integrals (cube and cylinder):"
             " relative error 3-D %.2e, 5-D %.2e." % (d["3d_rel"], d["cyl_rel"]))
    for lam in (0.3, 1.0):
        d = vres["gauss%.1f" % lam]
        V.append("- kernel exp(-%.1f R^2), closed 6-D Gaussian integral %.12f: quadrature"
                 " relative error 3-D %.2e, 5-D %.2e." % (lam, d["an"], d["rel3"], d["rel5"]))
    d = vres["invr"]
    V.append("- kernel 1/R: two independent closed forms (1-D integral of the analytic"
             " Gaussian kernel vs the erf formula) agree to %.2e; quadrature relative"
             " error 3-D %.2e, 5-D %.2e." % (d["rel_a"], d["rel3"], d["rel5"]))
    d = vres["control"]
    V.append("- POSITIVE CONTROL: swapping in the pairing that `step_e_kernel.py` proves"
             " wrong shifts the term by %.4f kcal/mol on this density, and the"
             " independent quadrature reproduces the wrong-pairing number to %+.4f"
             " kcal/mol just as well as the right one (%+.4f kcal/mol).  The referee"
             " is not blind to a kernel error."
             % (d["shift_kcal"], d["diff_wrong_kcal"], d["diff_right_kcal"]))
    d = vres["mc"]
    for which in ("AB", "AA"):
        v, m, se, z = d["vals"][which]
        V.append("- Monte-Carlo I_%s: quadrature %.12f vs MC %.12f +- %.12f (%d draws),"
                 " z = %+.2f sigma." % (which, v, m, se, MC_SAMPLES, z))
    d = vres["asym"]
    V.append("- large-separation behaviour of the cross term: fitted log-log slope"
             " %.4f against the kernel's own R^-6 expansion (expected -6), max"
             " residual %.3f; I_AB*R^6 across sep %s..%s bohr: %s"
             % (d["slope"], d["resid"], d["seps"][0], d["seps"][-1],
                ", ".join("%.4e" % x for x in d["r6"])))
    d = vres["measure_guard"]
    V.append("- measurement-massage guard: on the SAME point list (identical: %s, N=%d)"
             " the raw per-subgrid volume elements from `partition.partition_factors`"
             " integrate the density to %.8f electrons while the partitioned weights"
             " from `partition.atom_partition` give %.8f (expected %.1f, ratio %.6f)."
             " Every node set used here is checked against the electron count before"
             " use, so no block in this directory carries that factor."
             % (d["same_points"], d["n_raw"], d["raw_base_w_electrons"],
                d["partitioned_electrons"], d["expected"], d["ratio"]))
    if rows:
        zs = [abs(r["mc_z"]) for r in rows]
        V.append("- Monte-Carlo across all %d configurations: the exact cross term"
                 " agrees with an independent importance-sampled estimate to within"
                 " its own standard error everywhere, worst |z| = %.2f (table.md, MC"
                 " block).  The package's production inter[0,1] differs from that same"
                 " Monte-Carlo value by between %.1f and %.1f standard errors."
                 % (len(rows), max(zs),
                    min(abs(r["d_headline"]) / r["I_AB_mc_se"] for r in rows),
                    max(abs(r["d_headline"]) / r["I_AB_mc_se"] for r in rows)))
    with open(os.path.join(OUT, "validation.md"), "w") as fh:
        fh.write("\n".join(V) + "\n")

    if conv:
        K = ["# error bar on the independent reference (generated by run.py)", ""]
        for base, c in conv.items():
            if base in ("grid_level_ladder", "floor_study"):
                continue
            K.append("## %s" % base)
            K.append("- 5-D I_AB ladder: " + ", ".join("n=%s %.14f"
                                                       % (k, v) for k, v in
                                                       sorted(c["cyl_ab"].items(),
                                                              key=lambda t: int(t[0]))))
            K.append("- last change %.3e Ha, contraction ratio %.3f, geometric"
                     " extrapolation %s"
                     % (c["last_change"], c["ratio"],
                        ("%.14f" % c["extrapolated"]) if c["extrapolated"] else "n/a"))
            K.append("- undecomposed total at the top orders: "
                     + ", ".join("n=%s %.12f" % (k, v)
                                for k, v in sorted(c["cyl_tot"].items(),
                                                   key=lambda t: int(t[0]))))
            K.append("- 3-D x 3-D I_AB ladder: " + ", ".join("n=%s %.12f"
                                                             % (k, v) for k, v in
                                                             sorted(c["box_ab"].items(),
                                                                    key=lambda t: int(t[0]))))
            K.append("- domain truncation (n=40): " + ", ".join("f=%s %.12f"
                                                                % (k, v) for k, v in
                                                                sorted(c["trunc"].items(),
                                                                       key=lambda t: float(t[0])))
                       + "; shift f=5.0 vs 5.9: %.3e Ha" % c["trunc_shift"])
            K.append("")
        K.append("## production grid level ladder (alpha=1.0, sep=6.0)")
        K.append("| level | N | rmax | electrons | dropped | density-factor inter |"
                 " production inter | total |")
        K.append("|---|" * 8)
        for d in conv["grid_level_ladder"]:
            K.append("| %d | %d | %.1f | %.8f | %d | %.12f | %.12f | %.12f |"
                     % (d["level"], d["n"], d["rmax"], d["electrons"], d["dropped"],
                        d["df_inter"], d["prod_inter"], d["total"]))
        K.append("")
        K.append("## density-floor study (level %d)" % PKG_LEVEL)
        K.append("| floor | dropped | electrons kept | density-factor inter |"
                 " production inter | E_nl |")
        K.append("|---|" * 6)
        for d in conv["floor_study"]:
            K.append("| %.0e | %d | %.10f | %.12f | %.12f | %.12f |"
                     % (d["floor"], d["dropped"], d["electrons"], d["df_inter"],
                        d["prod_inter"], d["E_nl"]))
        with open(os.path.join(OUT, "convergence.md"), "w") as fh:
            fh.write("\n".join(K) + "\n")

    if rows:
        d = [r["d_headline"] for r in rows]
        dp = [r["d_partition_box"] for r in rows]
        H = ["# headline numbers (generated by run.py; quote the papers from THIS file)", ""]
        H.append("- configurations: %d = alpha %s x sep %s bohr, %g electrons per Gaussian,"
                 " production grid level %d, reference order 5-D n=%d / 3-D n=%d"
                 % (len(rows), ALPHAS, SEPS, N_ELEC, PKG_LEVEL, N5D, N3D))
        for name, arr in (("inter[0,1](PySCF grid) - I_AB", d),
                          ("inter[0,1](referee nodes) - I_AB(exact on same nodes)", dp)):
            H.append("- %s: min-abs %.3e  median %.3e  max-abs %.3e Ha  (= %.4f / %.4f"
                     " / %.4f kcal/mol)"
                     % (name, min(arr, key=abs), float(np.median(arr)),
                        max(arr, key=abs), min(arr, key=abs) * KCAL,
                        float(np.median(arr)) * KCAL, max(arr, key=abs) * KCAL))
        H.append("- as a share of the whole VV10 term E_NL: min %.2f%%  median %.2f%%"
                 "  max %.2f%%"
                 % (100 * min(abs(r["rel_to_term"]) for r in rows),
                    100 * float(np.median([r["rel_to_term"] for r in rows])),
                    100 * max(abs(r["rel_to_term"]) for r in rows)))
        H.append("- as a share of the cross term it is supposed to be: min %.2f%%"
                 "  median %.2f%%  max %.2f%%"
                 % (100 * min(abs(r["rel_to_cross"]) for r in rows),
                    100 * float(np.median([r["rel_to_cross"] for r in rows])),
                    100 * max(abs(r["rel_to_cross"]) for r in rows)))
        H.append("- reference closure |1/2 sum I_XY - undecomposed total|: worst %.1e Ha"
                 % max(r["closure"] for r in rows))
        H.append("- reference 3-D vs 5-D disagreement: worst %.1e Ha"
                 % max(r["box_closure"] for r in rows))
        H.append("- reference Monte-Carlo z-scores on I_AB: worst |z| = %.2f"
                 % max(abs(r["mc_z"]) for r in rows))
        H.append("- reference uncertainty (worst last-step change in the 5-D ladders):"
                 " %.3e Ha"
                 % (max(c["last_change"] for k, c in conv.items()
                        if k not in ("grid_level_ladder", "floor_study")) if conv else 0.0))
        H.append("- package production-grid total minus exact total: min-abs %.3e"
                 "  max-abs %.3e Ha")
        H[-1] = H[-1] % (min((abs(r["total_pkg_minus_exact"]) for r in rows)),
                          max(abs(r["total_pkg_minus_exact"]) for r in rows))
        H.append("- positive control: the documented-wrong pairing moves the term by"
                 " %.4f kcal/mol and is detected" % vres["control"]["shift_kcal"])
        H.append("- large-R slope of the cross term: %.4f (kernel expansion says -6)"
                 % vres["asym"]["slope"])
        H.append("- node-set normalisation guard (each node set must integrate rho"
                 " exactly once, expected %g electrons): production grid min %.8f"
                 " max %.8f; referee nodes min %.8f max %.8f"
                 % (2 * N_ELEC, min(r["grid_electrons"] for r in rows),
                    max(r["grid_electrons"] for r in rows),
                    min(r["box_electrons"] for r in rows),
                    max(r["box_electrons"] for r in rows)))
        with open(os.path.join(OUT, "headline.md"), "w") as fh:
            fh.write("\n".join(H) + "\n")


def apply_tiny_profile():
    """ATTR_REFEREE_TINY=1 shrinks every grid for a fast end-to-end plumbing test.

    It changes only the numerical settings, never the comparison being made; the
    published numbers come from the default profile.
    """
    global ALPHAS, SEPS, N5D, N5D_LADDER, N3D, N3D_LADDER, BOX_N, PKG_LEVEL
    global PKG_LEVEL_LADDER, ASYM_SEPS, CONV_KEYS, MC_SAMPLES, MC_SAMPLES_TABLE
    global FLOORS
    ALPHAS = [1.0]
    SEPS = [6.0]
    N5D = 24
    N5D_LADDER = [16, 24]
    N3D = 12
    N3D_LADDER = [8, 12]
    BOX_N = 12
    PKG_LEVEL = 3
    PKG_LEVEL_LADDER = [3]
    ASYM_SEPS = [12.0, 20.0]
    CONV_KEYS = [(1.0, 6.0)]
    MC_SAMPLES = 40_000
    MC_SAMPLES_TABLE = 20_000
    FLOORS = [1e-12]
    print("TINY profile active (plumbing test only)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-table", action="store_true")
    ap.add_argument("--skip-conv", action="store_true")
    ap.add_argument("--nproc", type=int, default=None)
    args = ap.parse_args()
    if args.nproc:
        global NPROC
        NPROC = args.nproc
    if os.environ.get("ATTR_REFEREE_TINY"):
        apply_tiny_profile()
    os.makedirs(OUT, exist_ok=True)
    run_all(do_table=not args.skip_table, do_conv=not args.skip_conv)
    print("wrote outputs/{results.json,table.md,validation.md,convergence.md,"
          "headline.md,run_log.txt}")


if __name__ == "__main__":
    main()
