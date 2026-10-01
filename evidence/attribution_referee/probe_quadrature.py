"""Numerical QA probe for the independent quadrature used by the referee.

Answers three questions before run.py is trusted:
  (1) do the node weights reproduce EXACT integrals (Gaussian normalisation over
      a cube and over a cylinder, a Gaussian-kernel double integral with a closed
      form, and the 1/R mutual energy of two Gaussians)?
  (2) does the VV10 double integral converge with grid order, and do the two
      independent formulations (Cartesian 3-D x 3-D and cylindrical 5-D) agree?
  (3) how much does the domain truncation cost?

Re-run:
  wsl -e bash -lc 'cd <REPO> && PYTHONPATH=. python3 -u evidence/attribution_referee/probe_quadrature.py'
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import referee_lib as rl                                    # noqa: E402
from pyscf.dft import numint                                # noqa: E402

B, C = numint.NumInt().nlc_coeff("wb97x_v")[0][0]
GP = rl.GaussPair(sep=6.0, alpha_a=1.0, n_a=4.0)
F = 5.0


def rel(a, b):
    return abs(a - b) / max(abs(b), 1e-300)


print("VV10 parameters from PySCF nlc_coeff('wb97x_v'): b=%s C=%s" % (B, C))
print("probe geometry: sep=%.1f bohr alpha=%.1f n_elec(each)=%.1f f_trunc=%.1f"
      % (GP.sep, GP.alpha_a, GP.n_a, F))

print("\n[1] weights against EXACT single-factor normalisations")
for n in (8, 12, 16, 20, 24, 32):
    v3, e3 = rl.integral_norm_check(GP, B, C, n, F, method="3d")
    v5, e5 = rl.integral_norm_check(GP, B, C, n, F, n_phi=int(1.5 * n), method="cyl")
    print("   n=%2d  3D cube %.12f exact %.12f rel %.2e | 5D cyl %.12f exact %.12f rel %.2e"
          % (n, v3, e3, rel(v3, e3), v5, e5, rel(v5, e5)))

print("\n[2] kernel exp(-lam R^2) against the closed 6-D Gaussian integral")
for lam in (0.3, 1.0):
    an = rl.analytic_gaussian_kernel(GP.n_a, GP.n_b, GP.alpha_a, GP.alpha_b, lam, GP.sep)
    print("   lam=%s analytic %.12f" % (lam, an))
    for n in (8, 12, 16, 20, 24, 28):
        q3, _ = rl.integral_box3d(GP, B, C, n, F, kernel=rl.kernel_gaussian(lam), which="AB")
        q5, _ = rl.integral_cyl5d(GP, B, C, n, int(1.5 * n), F,
                                  kernel=rl.kernel_gaussian(lam), which="AB")
        print("     n=%2d 3D %.12f rel %.2e | 5D %.12f rel %.2e"
              % (n, q3, rel(q3, an), q5, rel(q5, an)))

print("\n[3] kernel 1/R: two analytic routes must agree, then both quadratures")
a1 = rl.analytic_coulomb_via_kernel(GP.n_a, GP.n_b, GP.alpha_a, GP.alpha_b, GP.sep)
a2 = rl.analytic_coulomb_closed(GP.n_a, GP.n_b, GP.alpha_a, GP.alpha_b, GP.sep)
print("   int of analytic-Gaussian-kernel route %.14f   erf route %.14f   rel %.2e"
      % (a1, a2, rel(a1, a2)))
for n in (12, 16, 20, 24, 28):
    q3, _ = rl.integral_box3d(GP, B, C, n, F, kernel=rl.kernel_inv_r, which="AB")
    q5, _ = rl.integral_cyl5d(GP, B, C, n, int(1.5 * n), F, kernel=rl.kernel_inv_r, which="AB")
    print("   n=%2d 3D %.12f rel %.2e | 5D %.12f rel %.2e" % (n, q3, rel(q3, a2), q5, rel(q5, a2)))

print("\n[4] VV10 itself: order ladder and cross-formulation agreement")
prev = {}
for n in (16, 24, 32, 40, 48, 56, 64):
    t0 = time.time()
    iab, _ = rl.integral_cyl5d(GP, B, C, n, int(1.5 * n), F, which="AB")
    iaa, _ = rl.integral_cyl5d(GP, B, C, n, int(1.5 * n), F, which="AA")
    ibb, _ = rl.integral_cyl5d(GP, B, C, n, int(1.5 * n), F, which="BB")
    iba, _ = rl.integral_cyl5d(GP, B, C, n, int(1.5 * n), F, which="BA")
    itot, _ = rl.integral_cyl5d(GP, B, C, n, int(1.5 * n), F, which="TOT")
    closure = abs(0.5 * (iaa + ibb + iab + iba) - itot)
    d = "" if "iab" not in prev else "  dI_AB vs prev %.2e" % abs(iab - prev["iab"])
    prev = dict(iab=iab)
    print("   5D n=%2d I_AB %.14f I_AA %.14f I_BB %.14f I_BA %.14f TOT %.14f closure %.2e %.0fs%s"
          % (n, iab, iaa, ibb, iba, itot, closure, time.time() - t0, d))
for n in (12, 16, 20, 24):
    t0 = time.time()
    iab, _ = rl.integral_box3d(GP, B, C, n, F, which="AB")
    iaa, _ = rl.integral_box3d(GP, B, C, n, F, which="AA")
    itot, _ = rl.integral_box3d(GP, B, C, n, F, which="TOT")
    print("   3D n=%2d I_AB %.14f I_AA %.14f TOT %.14f closure %.2e  %.0fs"
          % (n, iab, iaa, itot, abs(iaa + iab - itot), time.time() - t0))

print("\n[5] domain truncation (5D, n=40): f_trunc / sqrt(alpha)")
ref = None
for f in (3.0, 3.6, 4.2, 5.0, 5.9, 6.8):
    iab, _ = rl.integral_cyl5d(GP, B, C, 40, 60, f, which="AB")
    iaa, _ = rl.integral_cyl5d(GP, B, C, 40, 60, f, which="AA")
    if ref is None:
        ref = (iab, iaa)
    print("   f=%.1f  I_AB %.14f (d vs f=3.0 %.2e)  I_AA %.14f (d %.2e)"
          % (f, iab, abs(iab - ref[0]), iaa, abs(iaa - ref[1])))
