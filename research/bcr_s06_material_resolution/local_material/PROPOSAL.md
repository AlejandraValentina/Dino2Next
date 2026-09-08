# Local material-face prototype: revisable BCR proposal

Author: /root/bcr_science_review. This author does not independently approve
the proposal. User authorization c5e323c7 permits this bounded prototype;
production C1/architecture/S05/S06 remain unchanged. The prototype is not
VAL-008 acceptance and does not qualify shock accuracy.

## Published starting point and explicit adaptation

[Pan et al. (2017), section 2.3](https://arxiv.org/html/1704.00519v1)
uses conservative material-volume balances and interface pressure/work
exchange. The present one-dimensional proposal takes that balance principle;
it does not implement the paper's level-set representation, multidimensional
interaction model, conservation correction or small-scale deletion. The NASA
mixture and the local agglomeration/remap below are explicit adaptations to be
reviewed, not claims of a verbatim published algorithm or inherited validation.

For a unit-area interval bounded by xL,xR, authoritative inventory I=width*U
obeys I'=G_L-G_R, G=F-sU. At a material Riemann contact, s=u* and the shared
relative flux is (0,p*,p*u*,0,...,0). Ordinary faces have s=0 and use the
existing Davis-HLLC formula, here with first-order states. Each region contains
a five-species gas mixture and four independent origin inventories; its label
identifies a declared spatial material region, neither species nor origin.
The inviscid chemically frozen equations have no diffusion flux across a
material surface. No new immiscibility, surface-tension or physical mixing
closure follows from representing that surface.

NASA supplies each region's p,T,a from its own I/width. Formation energy stays
in I. Derived fractions follow TS004; no energy or chemical inventory is
adjusted to impose pressure. The star admissibility test uses the same NASA
domain. Uniform p/u preservation is an observed contact property, not a
constraint imposed on waves.

## Concrete local algorithm

1. Initial physical intervals or a restart provide ordered material boundaries
   and regional inventories. With only homogeneous Q, use the explicitly
   homogeneous interpretation; do not infer lost interfaces. Smooth initial
   composition has a continuous-region label, so all its faces remain ordinary.
2. Retain every declared material boundary and the fixed exterior endpoints.
   Between complete time steps, include ordinary base-grid faces only when
   their distance to every material boundary is at least .35*dx. This prototype
   numerical parameter is proposed, not a frozen physical constant. Thus a
   near-aligned tiny cut piece can agglomerate with a neighbor of the same
   material while the physical contact remains at its evolved coordinate.
3. Repartition through overlaps of the old piecewise-constant regional field
   with the new intervals. Transfers only connect equal labels and contiguous
   overlap. Each donor's last transfer is its untransferred remainder. Shared
   transfers preserve all twelve inventories, subject to recorded arithmetic
   roundoff; there is no post hoc pressure/energy repair. Every new state must
   satisfy NASA/simplex before committing. Remap pressure changes in nonuniform
   regions are numerical error, never subtracted from the candidate error.
4. With that topology fixed, evaluate all faces. Ordinary faces stay at their
   base positions. Material faces use HLLC u* and shared p*,p*u* transfers.
   Apply SSPRK2 to the same tuple (ordered x,I) through both stages. Widths
   derive from the evolved edges, so GCL and pressure-work use matching stages.
   Only after the complete step may another topology be constructed.
5. A contact crossing a base-grid face does not cross an integration face:
   that nearby ordinary face was removed. The next complete-step remap inserts
   ordinary faces behind the contact and removes those ahead. There is no
   interpolation between unmatched RK region lists. Failed trials leave the
   immutable input geometry/inventory untouched; diagnostic trial records are
   separate from authoritative state.

The dt uses each actual interval width and acoustic speed relative to its
bounding faces, followed by full-stage admissibility rejection/retry. A truly
thin material slab between two material boundaries is retained and still
limits dt. The algorithm resolves geometric near-alignment, not arbitrary
physical underresolution. It does not delete such a slab, mix it, or replace
its mass by an epsilon. End-point exit, collision/coalescence of distinct
material boundaries and new material entering a physical port need explicit
event/consumer implementation; none is silently handled by this demonstration.

## Results and retained limits

Nine physical contacts cover the original three composition/temperature pairs,
u=0,+100,-100 and .001 s. They start at .5+1e-10 m to exercise a geometric
tiny cut piece. All moving cases cross base faces. Only material faces move;
the rest of the grid stays Eulerian. Maximum pressure perturbation, also
outside the two contact-adjacent intervals, is 3.64e-7 Pa. Contact evolution
and remaps preserve the ST003 normalized ledger within 2.03e-16. Stage GCL
residual is below 9.37e-17 m. These are actual measured prototype results,
not a full catalogue norm or validation claim. All stage fluxes, speeds,
initial/final inventories and remap residuals are portable JSON evidence.

The ledger uses sum(abs(initial inventory)) plus stage-resolved absolute
exterior throughput plus physical Qref. Declared ambient input is air with
O2:N2 mole ratio 1:3.76, p=100000 Pa,Tref=350 K. NASA determines rho_amb,
cv_air and c_amb; Qref is rho_amb*Vtotal, that mass times c_amb for momentum,
and that mass times cv_air*350 for energy. Species and origin residuals use
the total mass scale. There are no physical sources/relabels in these controls.
Paired internal fluxes are represented once and applied with opposite signs;
their cancellation is tested separately from the global residual.

The distinct upstream-pressure-jump control evolves an actual wave into the
material interface and changes the downstream pressure; wave-result.json
records its pressure/velocity/flux history. This rejects the interpretation
that the algorithm merely forces p/u uniform. It is not an independently
qualified shock reference comparison. Five local software/algebra tests pass.
The nine small controls cost about 50 s in the measured WSL environment;
per-case costs and exact source/data hashes are in control-results.json.

The present spatial update is first order on all ordinary faces, although its
flux formula is compatible with the ordinary Eulerian kernel interface.
Therefore this code itself is NOT the final local coupling to accepted MUSCL,
its guards or its shock fallback. A viable next implementation must retain
the accepted ordinary-face operator outside the contact stencil and explicitly
define/verify the regional near-contact reconstruction, guard and remap order.
The piecewise-constant remap is locally first order and may reduce wave accuracy
when a contact interacts with a nonuniform state. Conservation alone does not
remove this accuracy risk. No previous kernel PASS may be automatically reused.

The prototype overlap search is quadratic in interval count, deliberately
simple for a 24-cell demonstration. Production can replace that search with a
monotone two-pointer interval sweep without changing the ordered transfers;
bitwise equivalence and timing must be tested before claiming practical cost.
No full-cycle GEN1 cost is established here. Real thin slabs, high regional
count or unresolved interface collisions remain explicit practical limits.

## Minimal state and consumer impact

Authoritative restart state needs ordered regional edges in metres, immutable
twelve-component extensive inventories, ordered material identities and
geometry/input identity. Cell ownership and overlap fractions are derived;
the old Q12 cell average is a conservative projection, not a second editable
inventory. A regional physical observable such as mean pressure is obtained
by geometric integration of regional pressure. EOS(projected Q) remains a
different, explicitly named homogeneous diagnostic. S05 primitive()/cached
pressure cannot silently supply that physical regional observable.

This bounded implementation assumes A=1. For variable area the regional volume
must use accepted exact integral A(x)dx, moving-boundary fluxes use A(x_f), and
the regional pressure-area source must be derived and tested with the same
stage geometry. No constant-area result approves that extension. S07 sources,
S08-S15 connections, S16 dt/events and S17 persistence must consume the new
state deliberately. Existing 0D volume/port closures are not changed here.

The demonstrated local mechanism removes the specific global-moving-grid and
geometric tiny-cut obstacle. It does not yet close the remaining reconstruction,
physical-boundary, variable-area and shock-accuracy obligations needed for
an implementable accepted S06 recipe. A reviewer must assess those explicit
remaining obligations before any proposal is frozen as GEN1 science.

## Software review correction: second FE admissibility and transactions

The first author freeze omitted a separate check of the second forward-Euler
state Y2 before the convex combination. Its complete source/results remain
unchanged in history/pre-y2-fix and are not current acceptance. The corrected
step validates Y2 geometry/inventories and NASA recovery before combining it
with Yn. Two regressions demonstrate that a negative-inventory or out-of-domain
Y2 can otherwise be hidden by an admissible final average. Parent remap/advance
and child SSPRK2 trials now have transaction IDs, accepted/rejected status and
stage labels; raw fraction records, remaps and flux records are linked to them.
Observation diagnostics do not masquerade as committed-stage records.

All nine contacts and the wave control were rerun at the corrected source;
their final fields equal the historical fields exactly, and all trial checks
completed. Eight tests pass. The additional NASA check has a measured cost;
current per-case timings replace the original approximate 50-second statement
for this corrected version. fix-results.json records the comparison and hashes.
