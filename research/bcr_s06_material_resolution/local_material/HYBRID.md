# Bounded connection to the existing ordinary-face kernel

This is an author prototype increment after the independently reviewed Y2
software fix. It is not an adjudicated replacement for the S06 method.

`kernel_source.py` is an unchanged, hash-pinned consumer snapshot of PR8's
numerical module: SHA256
84e5fba185fabf8008936c6ca533d0610b8cb87aa87b48833cf3d821328bfac9.
Its base is cc5c4ed plus the independently reviewed exact sparse-sum software
optimization. It is not represented as code already accepted on main.
`kernel_binding.json` retains that distinction. Imports use the accepted S03/S05
interfaces from this checkout and the accepted NASA dataset. No new EOS is used.

Material boundaries and intervals no longer coincident with a single base-grid
cell seed the local patch. Four cells of stencil distance are added on either
side. The complement is split into contiguous ordinary uniform-mesh chunks.
For each chunk the pinned kernel's `reconstruct` and `interior_flux` are called
unchanged, supplying four ghost rows on each side from actual neighboring
regional inventories divided by their own widths. No EOS of an aggregated
mixed observation cell is used as a proxy. The ordinary region can contain
smoothly varying composition; chemical differences alone do not create labels.

Chunk interior high/low fluxes are the kernel's exact fluxes. Chunk end faces
touch the patch and use the regional low-order flux; physical exterior fluxes
remain the same prescribed zero-gradient control. Material faces move with u*
and have a single shared pressure/work flux. Other patch faces are stationary
and use the existing first-order regional HLLC adaptation. Regional HLLC is
evaluated only on patch-touching faces, never before the ordinary kernel has
selected its own flux branch. This prevents an unused HLLC star-state rejection
from disabling a valid ordinary flux-B face.

Each SSPRK stage applies a single theta to the common high-minus-low flux array.
The same selected face value supplies opposite regional transfers. Moving
geometry is fixed for that stage while theta is searched; GCL follows from
the same stage velocities. The guard checks the first FE state, second FE
state and final combination as appropriate, with actual regional NASA recovery.
It uses the original nonnegative linear cap, 54 bisections and up to eight
roundoff reductions. A failed low-order state explicitly rejects the trial
for a smaller dt. This code does not assert a new unconditional positivity
theorem for the regional HLLC flux. No clipping or alternative EOS is allowed.
Guard-candidate IDs, admissible/rejected status and selected flag distinguish
discarded theta trials from the accepted stage transaction and its diagnostics.

Five tests establish: exact high/low ordinary flux identity for no-material
inputs; exact identity outside the material patch; no unused regional HLLC
evaluation on ordinary bulk; a common conservative guard that enforces Y2;
and explicit rejection of an inadmissible low-order state. These are software
and algebra checks, not a shock-accuracy qualification.

The directed thermal contact test uses N2/600 K and CO2/1800 K, p=100000 Pa,
u=100 m/s, .001 s and a material face initially .5+1e-10 m. It crosses an
ordinary base-grid face through the local remap. Every accepted state is
retained so an independent reviewer can reproduce all timewise pressure
maxima. `hybrid-result.json` records ST003 normalization, absolute exterior
throughput, stage fluxes, guard records, identities and measured runtime.
The first author run that evaluated unused regional HLLC is preserved under
history/hybrid-before-selective-flux, not silently replaced as historical proof.

The frozen earlier local prototype and its Y2 correction remain unchanged.
This increment still has a first-order patch/remap. Variable area, physical
boundary events, genuinely thin material regions and accuracy of shock/contact
interaction remain separate obligations. The next directed shock control must
consume the already qualified independent VAL008 NASA reference after this
function/guard implementation is independently reviewed. No new oracle,
global reconstruction or numerical tolerance is selected here.
