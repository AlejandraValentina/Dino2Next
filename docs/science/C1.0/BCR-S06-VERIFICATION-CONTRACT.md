> **Normative — C1.0-R4** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
> Adoption requires independent review and exact-HEAD checks; branch contents alone are not acceptance.

# BCR-S06-VERIFICATION-CONTRACT

The 2026-09-08 authorization covers four S06 verification decisions only. This PR
is separate from implementation PR8. It preserves C1.0-R3 bytes and its manifest
under history/C1.0-R3. S01-S05 remain accepted. Nothing here constitutes S06
acceptance or experimental/predictive validation. NASA TI-001..005, T3, W2,
composition, losses, combustion, flux definitions and SSPRK2 remain unchanged.

Historical numerical results belong to77caaba3614d747eb12e2d36f926a7f17950ea91;
software checks and CI belong to8cf8de398bd47dcf896989109b479f35cdfa51a6. Original
failures are retained. The bounded constructor/coverage/diagnostic changes between
them do not establish numerical acceptance at a new HEAD.

## SV-008 — computational guard zones

R3 prescribed computational domain[0,1], constant end states and rejection when
the characteristic domain of dependence reached an edge. Seven contact setups
violate that isolation precondition before .001s. The material interface does NOT
leave[0,1]: x=.5+u*t ends at .5,.6,.4. The rejection concerns acoustic/causal
isolation, not material displacement. The original rejection remains evidence.

Adopt uniform computational guard zones, with measurement window W=[0,1]m.
Preserve x_contact=.5, every original state/composition, final time, sampling,
CFL and window resolution N. Set dx=1/N over the whole mesh and A=1m2. On each
side add M=ceil(N*S*t_final)+4 cells, so the computational domain is
[-M/N,1+M/N]. Extend initial left/right states constantly into these cells; use
the same constant far end states without sponge, damping or physical source.
Window endpoints0,1 and interface.5 remain mesh faces.

Use the following PRIOR analytic speed certificates, in m/s:

    S_contacts = 1293; t_final=.001; N=100,200,400
    S_shocks = 2544; t_final=.0002; N=80,160,320,640

The derived NASA dataset supplies exact rational Bernstein bounds over both
temperature intervals: b=min(cv_k/R_k)>=100119156791/40000000000. Mixture cv/R
is an R-weighted convex combination, so a^2<=2200*R_max*(1+1/b), giving
a<=1192.069197. Contacts have |u|<=100 analytically. In each shock problem
pR<p*<pL, the left wave is a rarefaction, the right wave a compression, and
u*^2=(p*-pR)*(vR-v*)<=(pL-pR)*vR. With all three original composition pairs
and ratios2,5,10, the maximum u* bound is1351.520892. The shock-front speed is
bounded directly by Rankine-Hugoniot, without inferring convexity from cv>0:
S_front^2=R_R*700*(r-1)/(1-T*/(r*700))
<=R_R*700*(r+(r+1)/(2*b)), with r=p*/pR<=pL/pR. Use the maximum of this
front bound and u_bound+a_bound, across all original cases, then its upward
integer ceiling. This gives2544, and bounds both discontinuity motion and
characteristic influence through each fan.

These shock bounds include the fan, not just end states. For the left fan use
r0=pL/pR<=10: p*/pL>=1/r0 and T>=700*(1/r0)^(1/(b+1))>=362.766K.
For the right Hugoniot use r=p*/pR<=r0. The right Hugoniot and
cv/R>=b imply T<=700*(b+(r+1)/2)/(b+(1+1/r)/2)<=1834.958K. Thus the sound
bound's contracted temperature domain applies. Independent reference construction
must still verify its pressure root, wave admissibility and every original case.

The clearance from either computational boundary to W exceeds S*t_final by
at least four cell widths, the reconstruction/sensor stencil margin. This is a
continuum causal-isolation guarantee, not a claim that the algebraic support of
an explicit numerical update travels at precisely the characteristic speed.
Record max(|u|+a) at all candidate physical stages. Exceeding the predeclared S
is SETUP_CAUSAL_BOUND_FAILED; do not enlarge guards after inspecting errors.

Compute every error norm only over W, with its ORIGINAL length1m and original
density, pressure, velocity and mass scales. Guard cells never dilute L1 or L2.
Report full-domain conservation and a separate window ledger using actual paired
face transfers at0 and1. Retain all original contact and shock thresholds and
the independent NASA Riemann reference requirement. Run every original subcase.
The changed computational domain requires new execution; old failures are not
reclassified as successful candidate tests.

## SV-009 — smooth acoustic extrema

### Prior requirement and evidence

R3 NK-002 uses MC outside strong acoustic compression and for all material modes;
VAL-009 demands density/velocity L1 and L2 last-two orders >=1.8 above the floor.
Actual R3 L2 orders near1.75/1.73 fail. A missing L2 assertion was an implementation
defect and was repaired in8cf8de3; that repair exposes, not resolves, this failure.
Independent scalar periodic cosine transport with the same speed, time, sampling,
CFL and SSPRK2 reproduces decreasing L2 order while L1 approaches2. This separates
limiter behavior from NASA, boundary physics and the implementation's eigenbasis.

### Bounded alternatives and selection rationale

A would retain MC and redefine requirements by norm. Standard limiter degradation
at extrema explains why a blanket second-order claim is inappropriate, but does
not supply a justified universal L2 exponent of1.7 or an adequate GEN1 replacement
accuracy budget. The measured exponent is not used as a new threshold. This BCR
therefore retains the requested L2 accuracy and selects B: localized acoustic
extremum-preserving slope limiting. Material transport remains MC because species
and provenance discontinuities require its existing treatment. This is a GEN1
adaptation, not a claim that MC is incorrectly implemented or unsuitable for every
engineering application.

The published basis is Sekora and Colella, *Extremum-Preserving Limiters for MUSCL
and PPM*, [arXiv0903.4200v2, section2.1](https://arxiv.org/html/0903.4200v2#S2.SS1).
Only its slope construction is adopted. Its fourth-order difference stage,
characteristic tracing and PPM reconstruction are not adopted. Positivity is not
inferred from this limiter; the existing face and shared conservative stage guards
remain mandatory. Independent scalar tests establish motivation, not kernel PASS.

### Complete acoustic slope definition (NK-002)

At center cell i, project V(i-1)-V(i-2), V(i)-V(i-1), V(i+1)-V(i),
V(i+2)-V(i+1) using the SAME NK-001 center-cell primitive basis L_i. For each
acoustic family separately call these dmm, dm, dp, dpp; dc=(dm+dp)/2.
If near(i) is true, retain original minmod(dm,dp). If near(i) is false and
min(dm*dp,dmm*dpp)>=0, retain original MC(dm,dp). Otherwise define undivided
curvatures qm=dm-dmm, qc=dp-dm, qp=dpp-dp, s2=sign(qc), sign(0)=0:

    curvature = min(abs(qc), max(s2*qm,0), max(s2*qp,0))
    side = abs(dm) if s2*dc < 0 else abs(dp)
    bound = min((3/2)*(5/4)*curvature, 2*side)
    acoustic_slope = sign(dc)*min(abs(dc),bound)

The constant5/4 is the published C_VL value, selected before kernel errors are
examined, not fitted to this fixture. This formula absorbs h^2 into undivided
second differences. Equality in the extremum detector uses the ordinary MC path.
Material density, all chemical fractions and all provenance fractions retain
their original MC slopes everywhere. No projection in differing neighbor bases
may be differenced as if it were a single scalar field.

Recombine amplitudes with the original inverse basis. Preserve compression sensor,
near stencil, flattening, joint face contraction, EOS domain, shared flux guard,
HLLC/flux B routing, physical boundary fluxes, geometric sources and SSPRK2 exactly.
No case-ID-dependent method switch, clipping, new fallback or new time policy is
introduced. Constant-p,u material advection has zero acoustic differences in exact
arithmetic; floating evaluation equivalence must be checked before reusing VAL027.

### Coverage and consequences

Keep all original VAL009 meshes, CFLs, times, two amplitudes, L1/L2 thresholds and
Fourier amplitude/phase limits. Record extremum diagnostics as explanation without
subtracting their errors. Rerun affected contacts, shocks, acoustic, rigid/free
reflection, geometry, admissibility/NP and temporal tests. Original qualification
is not transferred automatically to the changed kernel. At minimum all S06-owned
fixtures must have valid post-change evidence or an independently demonstrated
equivalence for a specifically unchanged obligation. Reuse requires source/input/
reference identity and relevance, not merely identical reported PASS counts.

## SV-010 — characteristic reflection operator

R3 measures total pressure C/Cref at every sample. Let a=g(x-ct) and
b=g(2-x-ct), with g(z)=epsilon*exp(-((z-.25)/.05)^2). At ct=.75 both centers
are1 and a=b pointwise, hence p'=a-b=0 and Cref=0 exactly. This occurs at
required sample75 for both amplitudes. Floating cancellation noise cannot define
a physical phase, and no denominator offset or sample removal is authorized.

Replace that undefined relative operator by characteristic reflection components:

    w+ = (p-p0 + rho0*c*u)/2 = a
    w- = (p-p0 - rho0*c*u)/2 = -b
    p0=rho0=1; c=sqrt(1.4); sigma=.05; k=2*pi
    C_h(w) = sum_i wbar_i * integral(cell_i, exp(-i*k*x) dx)
    A0 = abs(integral(0,1, g(x)*exp(-i*k*x) dx)) > 0

For the candidate use the recovered cell pressure/velocity with fixed rho0, not
local rho in the acoustic decomposition. For the reference apply the SAME C_h
to exact analytic Gaussian cell averages; do not compare a discrete cell-average
operator with a different continuous operator. The continuous integral defines
only the fixed nonzero scale A0, approximately8.6462771789e-7 at epsilon1e-5;
it scales linearly for epsilon/2. This explicitly changes the former observation
discretization and separates directional waves instead of their canceling sum.

All101 original samples j=0..100, ct=j/100, remain mandatory. For each component
and also for their total pressure sum require |C_candidate-C_reference|/A0<=.01
at every sample, including75 and all tiny-signal tails. No measured remainder is
subtracted. This absolute complex gate covers zero-reference instants.

Define the declared phase-resolution mask from the reference ONLY:
abs(C_reference,h)>=.01*A0. The cutoff is the existing absolute1% resolution
budget, not a fitted candidate error or an assertion that weaker nonzero signals
have mathematically undefined phase. Qualify and freeze the mask before running
the candidate. For the original three meshes and either epsilon it gives incident
j=0..83 and reflected j=67..100, retaining resolvable pulse tails. Both components
are assessed at75. On this mask require relative amplitude error<=.01 and
abs(arg(C_candidate*conj(C_reference)))<=pi/N for each component, at the original
mesh/CFL assessment levels. A zero candidate in an observable interval fails
amplitude; its phase is undefined, never phase PASS. Outside the mask mark phase
NOT_ASSESSED_BELOW_DECLARED_ABSOLUTE_RESOLUTION and enforce the absolute gate.
Only a zero coefficient has undefined phase; no phase PASS is claimed for either
category. This changes coverage/interpretation explicitly: relative phase applies
to directional signals resolved above the declared physical absolute budget,
and absolute vector error covers all weaker tails and every cancellation.

Nonzero observability follows analytically: whenever the center is inside W,
at least one sigma-wide side is inside. Rotate C by its center phase. Its real
part is bounded below by epsilon*sigma*[cos(2*pi*sigma)*sqrt(pi)*erf(1)/2
-sqrt(pi)*erfc(.25/sigma)]. This is positive. The cell-average operator differs
from the continuous coefficient by at most2*pi*dx*epsilon*sigma*sqrt(pi);
subtracting this bound at the coarsest N200 still leaves a strictly positive
lower bound. The additional tail mask is qualified with high-precision exact
cell integrals. At N200, the incident j83 and j84 magnitudes are approximately
.0120913079*A0 and .00557899248*A0, with the other grids giving the same mask.
Reference arithmetic must have an absolute enclosure no larger than
min(.001,.1*sin(pi/N))*.01*A0 and certify each coefficient's side of the cutoff.
Differences between two precision settings alone are sensitivity checks, not
certified enclosures. Failure to qualify is REFERENCE_NOT_QUALIFIED.

Retain epsilon/2, every field/time/mesh, existing boundaries and conservation
checks. Peak/time diagnostics do not replace amplitude or phase. Rigid-wall
operators and thresholds are unchanged; a kernel change still requires regression
evidence. This decision preserves the1% and pi/N physical budgets but does not
claim equivalence to a relative phase that was undefined for total pressure.

## SV-027 — additional fixed temporal refinement

Preserve the original fixed N40, periodic rho=1+.01*sin(2*pi*x), u=.3, p=1,
gamma1.4,R1, t_final=.1, selected material MUSCL-MC/HLLC/SSPRK2 operator and
normalization. Keep all four original dt=.002,.001,.0005,.00025 runs and their
failures. Append dt=.000125 explicitly. The finest acceptance threshold remains
1e-10, and the first-two refinement orders must remain1.8..2.2. All801 finest
endpoints are reference times; each candidate level is compared at EVERY one of
its endpoints. Do not hide a maximum by retaining only the former401 samples.

The original finest error1.030122570577774e-10 fails1e-10 and remains FAIL.
Independent scalar MC/SSPRK2 reproduced it. The actual full-kernel8cf8de3 extra
level gives maximum density L1=2.502510698665361e-11 with all800 steps accepted
and both stage guards at theta1. This is motivation for resolution extension,
not a scalar substitute for the full run or acceptance of a changed kernel.

### Explicit reference target and qualification

The reference target is the exact-real selected semidiscrete spatial operator
on uniform faces x_i=i/40, dx=1/40, u=3/10, initialized with the ORIGINAL exact
analytic cell averages. It is not an ODE
which declares a separately rounded stored Q0 to be exact. This formalization is
part of the BCR: reference/candidate initialization and arithmetic errors count
against the original mathematical target. Never repair, overwrite or silently
project the candidate's stored state onto an invariant manifold.

For this target the exact material-contact invariant lift is

    Q=(rho, (3/10)*rho, 5/2+(9/200)*rho, chemical masses, origin masses)
    rhoY_N2=rho; rhoZ_R=rho; all other chemical/origin components=0.

Its pressure is1 and velocity3/10 exactly. Center-cell acoustic differences and
the compression sensor vanish. HLLC yields the physical donor contact flux;
the material density slope remains MC, including after SV-009. Geometric and
physical sources are zero. The resulting scalar RHS is
f_i(rho)=-12*[(rho_i+MC_i/2)-(rho_(i-1)+MC_(i-1)/2)]. The exact solution remains
within the positive mathematical contact domain; accepted candidate guards must
still be checked and any changed compared RHS invalidates reference reuse.

Retain full same-RHS DOP853 with rtol2.3e-14, atol1e-16, maxstep.0001 and the
original1e-13/1e-15 crosscheck, now at801 times. Cross discrepancies are diagnostics,
not absolute error certificates. Independently qualify its density reference
against a continuous scalar-contact enclosure, and report every conserved-field
discrepancy using the exact lift coefficients. This cannot qualify an arbitrary
off-manifold flow or a changed spatial operator.

The portable certificate uses exact-rational Bernstein bounds for the residual
of a continuous piecewise cubic Hermite trajectory. Every possible MC branch is
enclosed; ambiguous intervals subdivide or enclose all branches. Floating root
locations are not trusted. All possible branch Jacobian rows give global infinity
logarithmic norm<=48s^-1 (ordinary Lipschitz bound72s^-1). Integrate the bounded
residual with the exp(48t) amplification, using a rational Taylor/tail upper bound.
Enclose the exact analytic initial density with outward interval trig evaluation
and propagate its mismatch to the stored scalar start. At all801 times compare
the stored full DOP reference with the exact rational lift, then add the scalar
solution enclosure times each lift coefficient. Bind scripts, initial inputs,
trajectory arrays, time grids and source hashes. This counts the full reference's
off-manifold storage and floating integration discrepancy instead of asserting
that its rounded conservative states have exact constant pressure/velocity.

The bounded diagnostic certificate gives an independent scalar target enclosure
of5.1506038792e-13 and maximum full-reference conserved-field error bound
1.7473040787e-12; density maximum-time L1 bound6.3884833613e-13. Against that
target the original candidate's density maximum error lies in
[1.0247539273e-10,1.0350551351e-10], entirely above1e-10, while the actual extra
level lies in[2.4488266142e-11,2.5518386919e-11], entirely below it. These values
describe the bound8cf8de3 diagnostic and preserved original evidence, not new
expected test values or acceptance of a later implementation.

Qualification requires the resulting absolute density bound<=1e-11, and sufficient
separation to interpret the measured convergence; otherwise REFERENCE_NOT_QUALIFIED.
The original failure remains observable even with the independent scalar enclosure.
Initial/cross-precision agreement or Richardson extrapolation alone cannot be
presented as a certified error bound. A changed kernel must reestablish the exact
contact reduction and rerun its full reference/candidate sequences. No automatic
transfer of8cf8de3 qualification or scope acceptance is authorized.

## Review and adoption

Each decision author and independent scientific reviewer must be identified in
portable evidence. This proposal must not merge with an incomplete decision or a
failed required check. Only after contract integration may PR8 adopt the baseline;
S06 itself requires complete numerical acceptance and its own exact-HEAD review/CI.
