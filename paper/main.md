# Fragment-Resolved Nonlocal Correlation: Pair Attribution of the VV10 Term
## Draft — §1 Introduction and §2 Method (prose)

数值出处用 `[S#]` 标，对应 `MAIN-skeleton.md` 里的表与 `nlcsplit/logs/`。
本稿只写不依赖未到位数据的两节；§3 的正文等 level-2 反泊松表与参考值到位后补。

---

## 1. Introduction

Range-separated hybrid functionals with the VV10 nonlocal-correlation
functional — ωB97X-V and ωB97M-V in particular — have become a default choice
for non-covalent interactions. The nonlocal term is a two-electron-density
double integral over all pairs of grid points,

E_NL = ½ ∫∫ ρ(r) ρ(r′) Φ(r, r′) d³r d³r′,

and every production quantum-chemistry package evaluates it in a way that
destroys the pair index: PySCF's `nr_nlc_vxc` calls its own C kernel
`libdft.VXC_vv10nlc`, which bins the kernel and returns only point-folded
values, and libxc does the same. The consequence is structural, not numerical:
once the double sum has been folded into a per-point energy density, the
question "how much of this nonlocal correlation belongs to the interaction
between fragment A and fragment B?" has no answer inside those programs.

We provide that answer. `nlcsplit` evaluates the same double sum explicitly,
keeping the (i, j) pair index, and attributes each grid point to a fragment
through a real-space partition, so that E_NL decomposes into intra-fragment
blocks E_AA and inter-fragment pair blocks E_AB. The decomposition is exact by
construction — the sum of the blocks reproduces the total to machine precision
— but exactness is not the point and we do not sell it as such: grouping the
summation indices is trivially additive. Two things are not trivial, and they
are the content of this paper.

The first is **attribution**. The non-uniqueness lives in which fragment owns
each grid point (and, in the same spirit, how the local term β∫ρ is assigned),
not in how the sum is grouped. We therefore quantify the spread over four
published real-space partitions — Becke, Becke with the radius adjustment,
Becke–Treutler, and Stratmann's — on eight S22 complexes, and report it as a
per-system uncertainty rather than asserting one scheme as correct. The spread
is 0.004–0.310 kcal/mol in absolute terms and 0.8–18.2% relative to |E_AB|,
and it shows no systematic ordering by interaction type: the benzene sandwich
sits at 1.8% while benzene–water sits at 18.2% [S2]. It is also independent of
the one-electron basis, where the grid converges and the basis converges
toward the complete-basis-set limit: across five bases the scheme spread is
0.038–0.040 kcal/mol for the water dimer, so no choice of basis removes
it [S2]. A single blanket uncertainty figure would misrepresent the data; we
report it system by system.

The second, and chemically the more consequential, is **what the term actually
is**. Within a hybrid functional the exchange-correlation contribution to an
interaction energy splits as ΔE_xc = ΔE_xc^rest + ΔE_NLC, where "rest" collects
the semi-local exchange-correlation and the fraction of exact exchange, and the
local piece β∫ρ drops out of any superposition difference identically — β is a
constant and ∫ρ equals the electron count, so Δβ∫ρ vanishes to 3.7×10⁻⁵
kcal/mol in our level-1 test [S3]. That leaves the double sum as the only part
of the nonlocal term that can carry inter-fragment structure, and measuring it
shows that treating it as "the dispersion" is unsafe. For the water dimer it
supplies 16% of ΔE_xc. For the two benzene dimer configurations of S22 the
same quantity ranges from 54% to 100% [S4] — and those two structures differ
only in the relative orientation of the same pair of molecules, so the failure
of the identification is visible within one chemical system, without any
cross-system comparison. In the methane dimer the nonlocal term exceeds the
whole of ΔE_xc (ΔE_NLC = −0.517 against ΔE_xc = −0.232), i.e. the rest of the
exchange-correlation is net repulsive there.

Our positioning relative to the closest prior work is deliberate. Dasgupta and
Paesani (JCTC 2023, DOI 10.1021/acs.jctc.3c00903) also decompose interaction
energies of dispersion-corrected functionals, using second-generation
ALMO-EDA, E_Int = E_Pol + E_Frz + E_CT + E_Disp, and they obtain E_Disp as the
difference against a dispersion-free reference calculation — that is, they
treat the VV10 correction as one undivided block and ask whether that block is
accurate. We work inside that block. A systematic search of OpenAlex restricted
to titles and abstracts returns zero records for "nonlocal correlation" with
"energy decomposition", zero for "vdW-DF" with "energy decomposition", and one
for VV10 with "atom pair" [S1]; none of the retrieved records attributes the
nonlocal term to fragment pairs.

Two limits are stated here rather than in a closing section, because both
bound what the numbers may be used for. First, this is not an energy
decomposition analysis: we do not separate electrostatics, exchange-repulsion,
polarization or charge transfer, and we do not apply a basis-set
superposition-error correction to interaction energies. Second, the explicit
sum is not more accurate than the production kernels it is compared against —
the interpolation residual of PySCF's native kernel is of order 4×10⁻⁶
kcal/mol, far below any chemical interest, and the ≈0.1–0.9 kcal/mol offsets
that an earlier version of this work attributed to interpolation were in fact
a pairing error in our own kernel. The value of the explicit implementation is
that it retains the pair index, nothing more.

## 2. Method

### 2.1 The VV10 kernel and the pairing convention

With ρ the electron density and σ = |∇ρ|²,

w0(r) = √( C σ²/ρ⁴ + (4π/3) ρ ),  κ(r) = b (3π/2) (ρ/9π)^{1/6},
g = w0(r_i) R² + κ(r_i),  g′ = w0(r_j) R² + κ(r_j),  Φ = −3 / (2 g g′ (g+g′)),

with (b, C) = (6.0, 0.01) for ωB97X-V, and E_NLC = E_NL + β∫ρ,
β = (1/32)(3/b²)^{3/4}. The pairing of ω and κ in g and g′ is a genuine choice,
and the cross pairing g = w0(r_j) R² + κ(r_i) — which an earlier implementation
of ours used — is wrong: it raises monomer energies by +0.138 kcal/mol for
water, +0.418 for argon and +0.914 for benzene, and the offset is itself
grid-dependent, so it cannot be subtracted as a constant [S1, S5]. The
same-centre pairing above reproduces PySCF's native kernel to 3×10⁻⁵ kcal/mol
and ORCA 6.0.1 to 6×10⁻⁴ kcal/mol on the water monomer [S5].

### 2.2 Blocks, half-blocks and additivity

`pair_energy(A, B)` returns the half block ½ Σ_{i∈A} Σ_{j∈B} w_i w_j Φ_ij, so
that the inter-fragment term reported by `fragment_decomposition` is
E_AB = 2·pair_energy(A,B) and

E_NL = Σ_A E_AA + Σ_{A<B} E_AB

holds by construction. We record the additivity residual rather than trusting
it: across all systems and partitions reported here it is 0.00–3.5×10⁻¹⁸ Ha
[S2, S6]. R² is evaluated through the polarisation identity
|a|²+|b|²−2a·b in blocked gemm operations rather than through an explicit
displacement tensor, which reduces peak memory by roughly a factor of five at
this system size.

### 2.3 Attribution schemes and the far-field cut

Grid points are assigned to atoms by PySCF's own partition machinery
(`gen_grid.get_partition` with `radi.BRAGG_RADII`), in four variants — Becke,
Becke with the radius adjustment, Becke–Treutler, Stratmann — plus a nearest-
atom hard partition on the common grid as a control. Points with ρ below
`rho_floor` (default 10⁻¹²) are excluded from the double sum; this removes
10.7–22.6% of points while changing E_AB by 2.1×10⁻¹¹ kcal/mol between floors
of 10⁻⁸ and 10⁻¹⁶, and the dropped points carry at most 2.3×10⁻⁶ electrons
[S7]. The local term β∫ρ is a one-body functional of the density and is not
pair-resolved; as noted above it cancels identically from superposition
differences, which is what makes it legitimate to decompose only the double
sum.

### 2.4 Geometries and reference values

All dimer geometries are taken verbatim from the official GMTKN55 repository
(github.com/grimme-lab/GMTKN55, tag v1, `S22/NN/struc.xyz`; original source
Jureček et al., PCCP 5, 1811 (2003)), fetched by `tools/get_s22.sh`. Fragment
boundaries are derived from covalent connectivity with a 1.65 Å cutoff — longer than the longest covalent bond appearing in these
systems (aromatic C–C, 1.397 Å; a general C–C single bond is 1.54 Å) and shorter
than the shortest hydrogen bond (O···H 1.95 Å) — and the code refuses to proceed
unless exactly two fragments result. This is not a formality: in the official
S22 water-dimer file the atoms are ordered so that the fragments interleave,
and a hard-coded index split would mix the two molecules silently. For the
water dimer we additionally report ωB97X-V/6-31G* optimised geometry
(R(O···O) = 2.901 Å, 0.009 Å from the reference value) [S6].

### 2.5 Verification

Three routes to E_NLC are computed and compared at run time, with a hard
failure if they disagree: our explicit pair sum, PySCF's native kernel
(`numint.nr_nlc_vxc`), and — for the water monomer — ORCA 6.0.1. Energy
accounting is checked independently: for a hybrid functional the exact-exchange
energy is folded into `vhf.exc` by `get_veff` and is absent from `nr_rks`, so
we close e_tot = e_nuc + e₁ + e_coul + e_xc to ≤9×10⁻¹² kcal/mol rather than
assuming any particular partition of the XC terms. Cross-version and
cross-machine reproducibility is checked between PySCF 2.12.1 and 2.14.0,
which generate 10% different numbers of grid points at the same level while
reproducing every energy component digit for digit [S8].

---
### 出处对照
[S1] `RESEARCH-20260929-lit.md` §1, §6 · [S2] `MAIN-skeleton.md` 表2/表4b、
`nlcsplit/logs/step_h.json` · [S3] `step_f_dispersion.py` 输出 ·
[S4] 表4b · [S5] `step_e_kernel.py`、`PROGRESS-ide-S3.md` ·
[S6] CentOS `logs/20260928T165857Z_centos-step_c.out` ·
[S7] `step_d_floor.py`、`PROGRESS-nlcsplit.md` 22:45 ·
[S8] CentOS `logs/20260928T165857Z_centos-step_f_h2o2.out`
