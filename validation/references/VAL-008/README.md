# Independent VAL-008 reference

`reference.py` imports no candidate module. `Case(pair, velocity=0,
pressure_ratio=None)`, `solve(case)`, `point_states(x,time)` and
`cell_averages(edges,time,order=32)` implement the frozen18 cases. The two N2/CO2
shock families remain separate cases despite becoming identical when both
temperatures are700K. Arrays contain `rho,u,p,T,rhoY,conserved`. The12 conserved
columns are rho, momentum, total energy, five species and four origin inventories;
R is column10. Every primitive is directly averaged. In particular, mean pressure
is not EOS(mean conserved state).

The implementation independently constructs TI-001 from RAW coefficients. It
keeps the lower formation constants, changes only high h/s integration constants,
and uses the high branch at1000K. Entropy composition constants cancel along each
fixed-composition wave. Contact averages are exact material-state integrals.
Shocks use a left isentrope and right Hugoniot with separate compositions and a
common pressure/velocity root. The left integral uses adaptive GK15/7, split at
NASA breaks. Entropy, thermal-domain, wave ordering and right Lax checks are
mandatory. The fan uses a separately evaluated positive Gauss32 velocity integral
and safeguarded Newton inversion; no interpolation table, constant gamma or
candidate flux is used.

SV-008 computational guards belong to the adapter. This reference accepts the
complete extended edge array and supplies constant exterior states. Qualification
uses the original measurement window[0,1], never guard-diluted scales.

## Qualification and error allocation

`qualify.py` checks all101 times at every original resolution, retaining separate
case records. It compares Gauss16/32 after splitting every wave break and smooth
fan panels to width at most4m/s in xi. That discrepancy is a diagnostic only.
The independent error bound is constructed by `interval_bounds.py`:

* mpmath outward intervals enclose32 complete temperature boxes, padded beyond
  the80-digit-checked star root. Interval Taylor algebra, not finite differences,
  bounds every fourth derivative in xi via D_xi=(1/xi_T)D_T. The negative fan
  derivative is bounded away from zero. cp/a also receives an order16 Taylor
  coefficient bound.
* The positive Gauss16/32 rules reproduce degree4 as well as cubics and obey
  abs(error)<=B4*L^5/960. This follows by applying the fourth-order Taylor
  remainder about the panel midpoint separately to the integral and positive
  quadrature functional. The even remainder moment itself is exactly reproduced;
  cubic exactness alone would not justify this constant. Summing panels with
  nominal L<=4 (including the reported endpoint-rounding increment) and converting dxi to dx gives
  the explicitly reported cell-average bound, including the earliest samples
  where a whole fan fits in one cell. No asymptotic16/32 convergence ratio is
  assumed.
* The same argument at Taylor order16 bounds the two-panel velocity integral.
  Its error plus the explicit fan-root residual is propagated with interval
  first-derivative bounds. The exact conservation identity
  integral U dxi=[xi U-F] supplies an independent check of all conserved
  components. The full-window form is checked at every sampling time.
* Decimal-token80 thermodynamics independently solve entropy/Hugoniot/pressure
  matching to obtain a root estimate. `root_certificate.py` then proves strict
  Krawczyk inclusion in a radius1e-32 box using the analytic interval Jacobian
  and a separately enclosed Gauss32x64-panel integral residual. Forward error
  uses outward differences between exact stored binary values and that certified
  box, including derived velocity and wave speeds. It never rounds the80-digit
  root to binary before taking the difference, nor treats a residual as a root
  enclosure. A separate
  Cantera3.2 process derives the shifts anew and checks99 initial/star/fan states.

The floating arithmetic model is explicitly IEEE binary64 basic operations with
relative error<=eps and sqrt/log/exp/small integer powers with error<=4eps.
`floating_bounds.py` propagates absolute error through every arithmetic operation
using outward value intervals. Exact decimal NASA/molar coefficients are enclosed
independently and their differences from the stored binary coefficients are
included. Interval polynomial sign brackets certify Gaussian nodes; their weight
formula is enclosed independently, including discrepancies in NumPy's nodes and
weights. Entropy subtraction and formation-energy cancellation use absolute
errors, not relative errors of the nearly cancelling result. Positive weighted
sums and wave-location errors are then included in cell averages. Contacts use
the same derived arithmetic calculation and an explicit assertion; there is no
arbitrary normalized floor or gamma4096 multiplier. This is a numerical bound
under the stated arithmetic model, not a formal proof of the operating system's
libm. Peer review must assess this assumption and propagation before candidate use.

The required reference allocation is below5e-5 normalized,10% of the smallest
absolute VAL-008 threshold5e-4. All reported field bounds are explicit. Shock
convergence still requires errors resolved above reference uncertainty; no new
shock peak threshold is introduced. No reference result implies kernel PASS,
experimental validation or predictive validation.

## Reproduction

Use Python3.12 and `requirements.txt`; run `qualify.py`. In a separate environment
with `requirements-cantera.txt`, run `cantera_check.py` after generating inputs
with `prepare_cantera.py` in the first environment. The qualifier binds those
actually executed checks and the source inventory. Run the Cantera check before
the qualifier. `qualify.py --reuse-sampling` may reuse the preserved initial
sampling diagnostic only when reference/RAW/fixture/environment and snapshot
hashes match; all changed analytic and floating bounds are recomputed. That
diagnostic's guessed arithmetic allowance was rejected and is not acceptance.
Raw snapshots/logs remain under
`artifacts/S06-R4/reference008`; their hashes are recorded. Run `test_reference.py`
for the bounded interface/conservation checks. There is no candidate import or
kernel campaign in these commands.
