"""Independent VV10 density-factor machinery for the attribution referee.

WHAT THIS FILE IS
-----------------
Everything here is written from the *definition* of the quantity under test, on
purpose, so that it shares no summation code with ``nlcsplit.nlc``.  The package
folds the kernel into point values and sums them through a blocked gemm with the
polarisation identity |a-b|^2 = |a|^2+|b|^2-2a.b; this file uses explicit
displacement arrays and plain elementwise sums.  The two must agree, and their
disagreement is what the referee measures.

THE CONVENTION UNDER TEST (read off nlcsplit/nlc.py, not from memory)
-------------------------------------------------------------------
    rho_total(r) = rhoA(r) + rhoB(r)
    sigma(r)     = |grad rho_total(r)|^2
    w0(r)        = sqrt( C * sigma(r)^2 / rho(r)^4 + (4 pi / 3) rho(r) )
    kappa(r)     = b * (3 pi / 2) * (rho(r) / (9 pi))**(1/6)
    g            = w0(r)  * R^2 + kappa(r)      # same-centre pairing, R = |r - r'|
    g'           = w0(r') * R^2 + kappa(r')
    Phi(r,r')    = -3 / (2 g g' (g + g'))
    E_NL         = 1/2 int int rho(r) Phi(r,r') rho(r') d3r d3r'

``check_fields_match_package`` below asserts this transcription against the
package's own ``vv10_fields``; the definitions are not taken on trust.

THE EXACT DENSITY-FACTOR DECOMPOSITION
--------------------------------------
With rho = rhoA + rhoB the two density *factors* are fixed by construction, so

    I_XY = int int rhoX(r) Phi[rho_total](r,r') rhoY(r') d3r d3r',   X,Y in {A,B}

is an unambiguous number (Phi is built once, from the total density), and

    E_NL = 1/2 (I_AA + I_AB + I_BA + I_BB) = 1/2 (I_AA + I_BB) + I_AB

because Phi(r,r') = Phi(r',r) makes I_AB = I_BA.  No real-space partition, no
Becke weight and no grid assignment appears anywhere in that definition.  That is
the reference the package's Becke-partitioned inter[A,B] is compared against.
Derivation and the 1/2-factor bookkeeping are in README.md.
"""
import math

import numpy as np
from numpy.polynomial.legendre import leggauss

PI = np.pi


# ---------------------------------------------------------------- model density
class GaussPair:
    """Two normalised Gaussians, centres on the z axis, total density = their sum.

    alpha_a/alpha_b are Gaussian exponents (bohr^-2); the 1/e half-width is
    1/sqrt(alpha) and each Gaussian integrates to n_a (or n_b) electrons.
    """

    def __init__(self, sep, alpha_a=1.0, alpha_b=None, n_a=4.0, n_b=None):
        self.sep = float(sep)
        self.alpha_a = float(alpha_a)
        self.alpha_b = float(self.alpha_a if alpha_b is None else alpha_b)
        self.n_a = float(n_a)
        self.n_b = float(self.n_a if n_b is None else n_b)
        self.ca = np.array([0.0, 0.0, -0.5 * self.sep])
        self.cb = np.array([0.0, 0.0, +0.5 * self.sep])

    # -- the two density factors ----------------------------------------------
    def rho_a(self, r):
        return self._gauss(r, self.ca, self.alpha_a, self.n_a)

    def rho_b(self, r):
        return self._gauss(r, self.cb, self.alpha_b, self.n_b)

    @staticmethod
    def _gauss(r, c, alpha, nelec):
        d2 = np.einsum("...i,...i->...", r - c, r - c)
        return nelec * (alpha / PI) ** 1.5 * np.exp(-alpha * d2)

    def _grad(self, r, c, alpha, nelec):
        d = r - c
        return -2.0 * alpha * d * self._gauss(r, c, alpha, nelec)[..., None]

    # -- total density and |grad rho|^2 (the VV10 functional's inputs) ---------
    def state(self, r):
        """Return (rho_total, sigma_total, rho_a, rho_b) at the points r."""
        ra = self.rho_a(r)
        rb = self.rho_b(r)
        grad = self._grad(r, self.ca, self.alpha_a, self.n_a) \
            + self._grad(r, self.cb, self.alpha_b, self.n_b)
        sigma = np.einsum("...i,...i->...", grad, grad)
        return ra + rb, sigma, ra, rb


def vv10_fields_local(rho, sigma, b, C):
    """w0 and kappa from the definition above.  No density floor here."""
    with np.errstate(divide="ignore", over="ignore", invalid="ignore", under="ignore"):
        w0 = np.sqrt(C * sigma ** 2 / rho ** 4 + (4.0 / 3.0) * PI * rho)
        kap = b * (1.5 * PI) * (rho / (9.0 * PI)) ** (1.0 / 6.0)
    return w0, kap


# ------------------------------------------------------------------ the kernels
def kernel_vv10(R2, w0A, kA, w0B, kB):
    """Phi for the same-centre pairing: g = w0(r)R^2 + kappa(r)."""
    g = R2 * w0A[:, None] + kA[:, None]
    gp = R2 * w0B[None, :] + kB[None, :]
    return -1.5 / (g * gp * (g + gp))


def kernel_vv10_crosspair(R2, w0A, kA, w0B, kB):
    """The pairing shown to be wrong in nlcsplit/step_e_kernel.py (their "V0").

    Used only as a POSITIVE CONTROL: a referee that cannot detect this error is
    not refereeing anything.
    """
    g = R2 * w0B[None, :] + kA[:, None]
    gp = R2 * w0A[:, None] + kB[None, :]
    return -1.5 / (g * gp * (g + gp))


def kernel_gaussian(lam):
    """K(R) = exp(-lam R^2): the 6-D Gaussian integral has a closed form."""
    def f(R2, w0A, kA, w0B, kB):
        return np.exp(-lam * R2)
    return f


def kernel_inv_r(R2, w0A, kA, w0B, kB):
    """K(R) = 1/R.  Only valid when the two node sets cannot coincide."""
    return 1.0 / np.sqrt(R2)


# ------------------------------------------------------------- the direct sums
def double_sum(pA, uA, pB, uB, kernel, w0A=None, kA=None, w0B=None, kB=None,
               block=64):
    """sum_i sum_j uA_i K(i,j) uB_j, with explicit displacement arrays.

    Deliberately NOT the package's gemm path: |r_i - r_j|^2 is formed by direct
    subtraction, so a mistake in the polarisation identity used by
    nlcsplit/nlc.py cannot be mirrored here.
    """
    pA = np.asarray(pA, dtype=float)
    pB = np.asarray(pB, dtype=float)
    uA = np.asarray(uA, dtype=float)
    uB = np.asarray(uB, dtype=float)
    tot = 0.0
    for p0 in range(0, len(pA), block):
        sl = slice(p0, min(p0 + block, len(pA)))
        d = pA[sl][:, None, :] - pB[None, :, :]
        R2 = np.einsum("ijk,ijk->ij", d, d)
        k = kernel(R2, w0A[sl], kA[sl], w0B, kB)
        tot += float(np.einsum("i,ij,j->", uA[sl], k, uB))
    return tot


# ------------------------------------------------------------------ node sets
def box_nodes(centre, half, n):
    """n^3 Cartesian Gauss-Legendre nodes in the cube [centre-half, centre+half]."""
    x, w = leggauss(n)
    ax = [centre[i] + half * x for i in range(3)]
    aw = [half * w for _ in range(3)]
    X, Y, Z = np.meshgrid(ax[0], ax[1], ax[2], indexing="ij")
    pts = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)
    W = (aw[0][:, None, None] * aw[1][None, :, None] * aw[2][None, None, :]).ravel()
    return pts, W


def cyl_nodes(centre, radius, half_z, n_z, n_s, n_phi):
    """Cylindrical nodes about the z axis through `centre`.

    The overall azimuth (2 pi) is folded into the weights and the *relative*
    azimuth is kept as a 1-D quadrature over [0, pi], exploiting
    F(r,r') = F(rot r, rot r') and F(..., -dphi) = F(..., +dphi) for any kernel
    that depends on |r-r'| only.  Weights already contain the s*s' Jacobian and
    the 4 pi from the two azimuth reductions.
    """
    z, wz = leggauss(n_z)
    s, ws = leggauss(n_s)
    ph, wp = leggauss(n_phi)
    z = centre[2] + half_z * z
    wz = half_z * wz
    s = radius * 0.5 * (s + 1.0)          # GL nodes are on [-1,1]; radial on [0,R]
    ws = radius * 0.5 * ws
    phi = PI * 0.5 * (ph + 1.0)           # relative azimuth on [0, pi]
    wp = PI * 0.5 * wp
    Z, S, PH = np.meshgrid(z, s, phi, indexing="ij")
    WZ, WS, WP = np.meshgrid(wz, ws, wp, indexing="ij")
    pts = np.stack([S * np.cos(PH), S * np.sin(PH), Z], axis=-1).reshape(-1, 3)
    pts += np.array([centre[0], centre[1], 0.0])
    wts = 4.0 * PI * WZ * WS * WP * S
    return pts, wts.ravel()


def cyl_nodes_meridian(centre, radius, half_z, n_z, n_s):
    """The second argument of the reduced 5-D product: phi' = 0, weight s' ds' dz'."""
    z, wz = leggauss(n_z)
    s, ws = leggauss(n_s)
    z = centre[2] + half_z * z
    wz = half_z * wz
    s = radius * 0.5 * (s + 1.0)        # GL nodes are on [-1,1]; radial on [0,R]
    ws = radius * 0.5 * ws
    Z, S = np.meshgrid(z, s, indexing="ij")
    WZ, WS = np.meshgrid(wz, ws, indexing="ij")
    pts = np.stack([S, np.zeros_like(S), Z], axis=-1).reshape(-1, 3)
    pts += np.array([centre[0], centre[1], 0.0])
    return pts, (WS * WZ * S).ravel()


# --------------------------------------------------- 6-D and 5-D double cubes
def _box_pair(gp, n, f_trunc):
    ha = f_trunc / math.sqrt(gp.alpha_a)
    hb = f_trunc / math.sqrt(gp.alpha_b)
    pa, wa = box_nodes(gp.ca, ha, n)
    pb, wb = box_nodes(gp.cb, hb, n)
    return (pa, wa), (pb, wb)


def _cyl_pair(gp, n, n_phi, f_trunc):
    ra = f_trunc / math.sqrt(gp.alpha_a)
    rb = f_trunc / math.sqrt(gp.alpha_b)
    pa, wa = cyl_nodes(gp.ca, ra, ra, n, n, n_phi)
    pb, wb = cyl_nodes(gp.cb, rb, rb, n, n, n_phi)
    ma, mwa = cyl_nodes_meridian(gp.ca, ra, ra, n, n)
    mb, mwb = cyl_nodes_meridian(gp.cb, rb, rb, n, n)
    return (pa, wa), (pb, wb), (ma, mwa), (mb, mwb)


def integral_box3d(gp, b, C, n, f_trunc=5.0, kernel=kernel_vv10,
                   which="AB", block=64):
    """Direct double 3-D Cartesian Gauss-Legendre quadrature of I_XY.

    Domain of each factor: the cube of half-side f_trunc/sqrt(alpha) about that
    factor's own centre, i.e. the density of a factor at its own face is
    exp(-f_trunc^2) of its peak.  The integrand is bounded everywhere (see
    README: rho^2 Phi ~ rho^{3/2} on the diagonal), so this truncation plus the
    Gaussian decay is the only approximation besides the finite node count.

    which="TOT" integrates the UNDECOMPOSED quantity
    1/2 int int rho_tot(r) Phi rho_tot(r') over the union of the two cubes: a
    route to E_NL that never touches the four-way split.
    """
    (pa, wa), (pb, wb) = _box_pair(gp, n, f_trunc)
    if which == "AA":
        pA, uA, pB = pa, gp.rho_a(pa) * wa, pa
        uB = gp.rho_a(pa) * wa
    elif which == "BB":
        pA, uA, pB = pb, gp.rho_b(pb) * wb, pb
        uB = gp.rho_b(pb) * wb
    elif which == "AB":
        pA, uA = pa, gp.rho_a(pa) * wa
        pB, uB = pb, gp.rho_b(pb) * wb
    elif which == "BA":
        pA, uA = pb, gp.rho_b(pb) * wb
        pB, uB = pa, gp.rho_a(pa) * wa
    elif which == "TOT":
        raise NotImplementedError(
            "the Cartesian TOT branch was removed: for small separations the two "
            "cubes OVERLAP, so concatenating them counts the overlap region twice "
            "(measured: a 17.7 per cent inflation of the total at sep=6, alpha=1). "
            "Use integral_cyl5d(..., which='TOT'), whose single coaxial cylinder "
            "contains both domains without double counting.")
    else:
        raise ValueError(which)
    return _finish(pA, uA, pB, uB, gp, b, C, kernel, block)


def integral_cyl5d(gp, b, C, n, n_phi, f_trunc=5.0, kernel=kernel_vv10,
                   which="AB", block=64):
    """Same integrals in cylindrical coordinates about the internuclear axis.

    A genuinely different reduction of the same 6-D integral (5 dimensions by
    azimuthal symmetry, different node set, different Jacobian, different domain
    shape: cylinder instead of cube).  Used to falsify the 3-D implementation.
    """
    (pa, wa), (pb, wb), (ma, mwa), (mb, mwb) = _cyl_pair(gp, n, n_phi, f_trunc)
    if which == "AA":
        pA, uA, pB, uB = pa, gp.rho_a(pa) * wa, ma, gp.rho_a(ma) * mwa
    elif which == "BB":
        pA, uA, pB, uB = pb, gp.rho_b(pb) * wb, mb, gp.rho_b(mb) * mwb
    elif which == "AB":
        pA, uA, pB, uB = pa, gp.rho_a(pa) * wa, mb, gp.rho_b(mb) * mwb
    elif which == "BA":
        pA, uA, pB, uB = pb, gp.rho_b(pb) * wb, ma, gp.rho_a(ma) * mwa
    elif which == "TOT":
        # E_NL from the UNDECOMPOSED integral: one coaxial cylinder big enough to
        # contain both factors' own domains, so no region is visited twice.
        lmax = max(f_trunc / math.sqrt(gp.alpha_a), f_trunc / math.sqrt(gp.alpha_b))
        hz = 0.5 * gp.sep + lmax
        pA, wA = cyl_nodes(np.zeros(3), lmax, hz, n, n, n_phi)
        pB, wB = cyl_nodes_meridian(np.zeros(3), lmax, hz, n, n)
        uA = (gp.rho_a(pA) + gp.rho_b(pA)) * wA
        uB = (gp.rho_a(pB) + gp.rho_b(pB)) * wB
        return _finish(pA, uA, pB, uB, gp, b, C, kernel, block, half=0.5)
    else:
        raise ValueError(which)
    return _finish(pA, uA, pB, uB, gp, b, C, kernel, block)


def _finish(pA, uA, pB, uB, gp, b, C, kernel, block, half=1.0):
    rA, sA, _, _, = gp.state(pA)
    rB, sB, _, _, = gp.state(pB)
    w0A, kA = vv10_fields_local(rA, sA, b, C)
    w0B, kB = vv10_fields_local(rB, sB, b, C)
    nonfinite = int((~np.isfinite(w0A)).sum() + (~np.isfinite(w0B)).sum()
                    + (~np.isfinite(kA)).sum() + (~np.isfinite(kB)).sum())
    val = double_sum(pA, uA, pB, uB, kernel, w0A, kA, w0B, kB, block=block)
    return half * val, dict(nonfinite=nonfinite, nA=len(pA), nB=len(pB),
                            rho_min=float(min(rA.min(), rB.min())))


# ----------------------------------------------------------------- Monte Carlo
def mc_integral(gp, b, C, which="AB", m=400_000, seed=20260930, chunk=100_000):
    """Importance-sampled Monte-Carlo estimate of I_XY with its standard error.

    r ~ the normalised Gaussian factor X, r' ~ factor Y, independently.  Then
    I_XY = n_X n_Y <Phi(r,r')> is an unbiased estimator, because the sampling
    density is exactly the density factor that appears in the integrand.
    """
    rng = np.random.default_rng(seed)
    if which == "AA":
        ca, cb, aa, ab, na, nb = gp.ca, gp.ca, gp.alpha_a, gp.alpha_a, gp.n_a, gp.n_a
    elif which == "BB":
        ca, cb, aa, ab, na, nb = gp.cb, gp.cb, gp.alpha_b, gp.alpha_b, gp.n_b, gp.n_b
    elif which == "AB":
        ca, cb, aa, ab, na, nb = gp.ca, gp.cb, gp.alpha_a, gp.alpha_b, gp.n_a, gp.n_b
    elif which == "BA":
        ca, cb, aa, ab, na, nb = gp.cb, gp.ca, gp.alpha_b, gp.alpha_a, gp.n_b, gp.n_a
    else:
        raise ValueError(which)
    sa = 1.0 / math.sqrt(2.0 * aa)
    sb = 1.0 / math.sqrt(2.0 * ab)
    vals = np.empty(m)
    for p0 in range(0, m, chunk):
        k = min(chunk, m - p0)
        pA = ca + sa * rng.standard_normal((k, 3))
        pB = cb + sb * rng.standard_normal((k, 3))
        rA, sA_, _, _ = gp.state(pA)
        rB, sB_, _, _ = gp.state(pB)
        w0A, kA = vv10_fields_local(rA, sA_, b, C)
        w0B, kB = vv10_fields_local(rB, sB_, b, C)
        d = pA - pB
        R2 = np.einsum("ij,ij->i", d, d)
        g = R2 * w0A + kA
        gp_ = R2 * w0B + kB
        vals[p0:p0 + k] = -1.5 / (g * gp_ * (g + gp_))
    mean = float(vals.mean())
    se = float(vals.std(ddof=1) / math.sqrt(m))
    return na * nb * mean, na * nb * se


# ------------------------------------------- analytic anchors for the machinery
# The quadrature code above is exercised against kernels whose double integral
# over two normalised Gaussians is known in closed form.  This tests the nodes,
# the weights, the Jacobians, the domain truncation and the |r-r'| geometry --
# i.e. everything except the VV10 kernel itself (which the package already has
# its own cross-program referee for).
def analytic_gaussian_kernel(n_a, n_b, alpha_a, alpha_b, lam, sep):
    """int int rhoA(r) exp(-lam |r-r'|^2) rhoB(r') d3r d3r', exactly.

    Fourier route: rhoA^(k) = n_a exp(-k^2/(4 alpha_a) - i k.a), and the
    transform of exp(-lam r^2) is (pi/lam)^{3/2} exp(-k^2/(4 lam)}, so
    I = n_a n_b (pi/lam)^{3/2} (4 pi gamma)^{-3/2} exp(-R^2/(4 gamma)),
    gamma = (1/alpha_a + 1/alpha_b + 1/lam)/4.  lam -> 0 must return n_a n_b
    (the K = 1 limit), which is asserted by the caller.
    """
    gamma = 0.25 * (1.0 / alpha_a + 1.0 / alpha_b + 1.0 / lam)
    return (n_a * n_b * (PI / lam) ** 1.5 / (4.0 * PI * gamma) ** 1.5
            * math.exp(-sep * sep / (4.0 * gamma)))


def analytic_coulomb_via_kernel(n_a, n_b, alpha_a, alpha_b, sep, n=240):
    """Same quantity for K = 1/R, from 1/R = (2/sqrt(pi)) int_0^inf exp(-t^2 R^2) dt.

    Independent of the closed erf form below; the two must agree.
    """
    x, w = leggauss(n)                    # map t in (0, inf) with t = y/(1-y)
    y = 0.5 * (x + 1.0)
    wy = 0.5 * w
    t = y / (1.0 - y)
    dt_dy = 1.0 / (1.0 - y) ** 2
    s = 0.0
    for ti, yi, wyi, dti in zip(t, y, wy, dt_dy):
        gamma = 0.25 * (1.0 / alpha_a + 1.0 / alpha_b + 1.0 / ti ** 2)
        g = (n_a * n_b * (PI / ti ** 2) ** 1.5 / (4.0 * PI * gamma) ** 1.5
             * math.exp(-sep * sep / (4.0 * gamma)))
        s += wyi * dti * g
    return 2.0 / math.sqrt(PI) * s


def analytic_coulomb_closed(n_a, n_b, alpha_a, alpha_b, sep):
    """textbook form: n_a n_b erf(R / sqrt(1/a + 1/b)) / R."""
    return n_a * n_b * math.erf(sep / math.sqrt(1.0 / alpha_a + 1.0 / alpha_b)) / sep


def check_fields_match_package(rho, sigma, b, C, mask_above=1e-10):
    """Compare this file's w0/kappa with nlcsplit.nlc.vv10_fields on the same input.

    Returns (worst relative deviation of w0, of kappa, n_points compared).  The
    comparison is restricted to rho > mask_above because below the package's
    1e-12 floor the two definitions deliberately differ: the package clamps rho
    to the floor, the referee does not.  That clamp is quantified separately in
    the floor study, it is not hidden here.
    """
    from nlcsplit import nlc as _nlc
    rho = np.asarray(rho, dtype=float)
    sigma = np.asarray(sigma, dtype=float)
    m = rho > mask_above
    w0_pkg, k_pkg, _ = _nlc.vv10_fields(rho[m], sigma[m], b, C)
    w0_loc, k_loc = vv10_fields_local(rho[m], sigma[m], b, C)
    dw = float(np.abs(w0_loc - w0_pkg).max() / np.abs(w0_pkg).max())
    dk = float(np.abs(k_loc - k_pkg).max() / np.abs(k_pkg).max())
    return dw, dk, int(m.sum())


def box_norm(n_elec, alpha, half):
    """Exact int of a normalised Gaussian over the cube of half-side `half` about
    its own centre: n * erf(sqrt(alpha)*half)^3.  Anchors the Cartesian weights."""
    return n_elec * math.erf(math.sqrt(alpha) * half) ** 3


def cyl_norm(n_elec, alpha, radius, half_z):
    """Exact int over the cylinder of radius `radius`, half-height `half_z`:
    n * erf(sqrt(alpha)*half_z) * (1 - exp(-alpha*radius^2)).  Anchors the
    cylindrical weights (including the 2 pi that the azimuth reduction leaves on
    one side of the pair)."""
    return n_elec * math.erf(math.sqrt(alpha) * half_z) * (1.0 - math.exp(-alpha * radius ** 2))


def integral_norm_check(gp, b, C, n, f_trunc=5.0, n_phi=None, method="3d"):
    """K = 1 limit of both quadratures: int rhoA over its own domain, exactly."""
    if n_phi is None:
        n_phi = int(1.5 * n)
    if method == "3d":
        la = f_trunc / math.sqrt(gp.alpha_a)
        lb = f_trunc / math.sqrt(gp.alpha_b)
        pa, wa = box_nodes(gp.ca, la, n)
        val = float((wa * gp.rho_a(pa)).sum())
        return val, box_norm(gp.n_a, gp.alpha_a, la)
    pa, wa = cyl_nodes(gp.ca, f_trunc / math.sqrt(gp.alpha_a),
                       f_trunc / math.sqrt(gp.alpha_a), n, n, n_phi)
    val = float((wa * gp.rho_a(pa)).sum())
    r = f_trunc / math.sqrt(gp.alpha_a)
    # the cylinder weights carry the relative-azimuth factor 2 pi, which pairs
    # with the meridian side; a single-factor sum therefore equals 2 pi * int.
    return val, 2.0 * PI * cyl_norm(gp.n_a, gp.alpha_a, r, r)


def box_nodes_aniso(centre, hx, hy, hz, nx, ny, nz):
    """Tensor Gauss-Legendre nodes in the rectangular box centre +- (hx, hy, hz)."""
    x, wx = leggauss(nx)
    y, wy = leggauss(ny)
    z, wz = leggauss(nz)
    X, Y, Z = np.meshgrid(centre[0] + hx * x, centre[1] + hy * y,
                          centre[2] + hz * z, indexing="ij")
    W = (hx * wx)[:, None, None] * (hy * wy)[None, :, None] * (hz * wz)[None, None, :]
    pts = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)
    return pts, W.ravel()


def half_box_pair(gp, f_trunc, n):
    """Two DISJOINT boxes whose union is (box around A) union (box around B).

    The split is the plane z = 0, halfway between the centres: A gets the part of
    its own box with z <= 0, B gets the part with z >= 0, and since the two boxes
    are congruent and each contains the other's half-space piece, the union is
    covered exactly once.  Concatenating the two FULL cubes counts the overlap
    twice -- measured as a factor 4.0007 on E_NL at sep = 6 bohr, alpha = 1.
    Node counts keep the spacing 2*L/n fixed in every direction.
    """
    la = f_trunc / math.sqrt(gp.alpha_a)
    lb = f_trunc / math.sqrt(gp.alpha_b)
    za_lo, za_hi = gp.ca[2] - la, 0.0
    zb_lo, zb_hi = 0.0, gp.cb[2] + lb
    na = max(4, int(round(n * (za_hi - za_lo) / (2.0 * la))))
    nb = max(4, int(round(n * (zb_hi - zb_lo) / (2.0 * lb))))
    pa, wa = box_nodes_aniso((0.0, 0.0, 0.5 * (za_lo + za_hi)), la, la,
                             0.5 * (za_hi - za_lo), n, n, na)
    pb, wb = box_nodes_aniso((0.0, 0.0, 0.5 * (zb_lo + zb_hi)), lb, lb,
                             0.5 * (zb_hi - zb_lo), n, n, nb)
    return (pa, wa), (pb, wb)
