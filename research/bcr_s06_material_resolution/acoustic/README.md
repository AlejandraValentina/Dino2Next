# VAL-010 resolution prototype — proposal, not an adopted contract

Ownership: independent acoustic reduction and reference-only observation
qualification. No production import or kernel execution occurs here. This
proposal needs an independent reviewer; its author cannot adjudicate it.

`upstream.json` identifies the exact original scripts from implementation
HEAD cc5c4ed. The reference qualifier is copied with its only mathematical
coverage change being N=1600 instead of N=200,400,800. Its unchanged composite
Simpson remainder and outward interval arithmetic qualify every coefficient,
float conversion, normalization and reference mask before the reduction runs.
The copied reference.py is identity evidence; neither prototype imports it.
The qualifier provenance author and paths explicitly identify this adaptation.

Run with Python 3.12, numpy 2.2.6, scipy 1.15.3 and mpmath 1.3.0:

```sh
python qualify_free.py
python acoustic_reduction.py
python -c "import acoustic_reduction as a; a.run(1600,.1)"
python summarize.py
```

The reduction solves the dimensionless directional advection/reflection system
with the accepted SV-009 scalar reconstruction and SSPRK2. N1600/CFL .05 is the
single additional spatial level predefined by the user. N1600/CFL .1 is solely
a temporal comparison, undertaken after .05 completed successfully. Both retain
all 101 samples, the Gaussian tails, exact cell-integrated Fourier weights,
reference-only 1% A0 masks, 1% amplitude/absolute limits and pi/N phase limit.
The assessment adds the certified reference uncertainty to each error gate.
Positive homogeneity of all slope operations, linear flux/boundary and RK2
implies identical normalized results for epsilon=1e-5 and 5e-6. This is an exact
statement about this dimensionless reduction, not an assumption about the
nonlinear kernel: the kernel must execute both amplitudes independently.

The folded extended-domain computation remains an independent boundary check.
Neither it nor the local modified equation substitutes for a candidate oracle.
The reference certificate covers the analytic observation, not a certified
global error bound for the numerical evolution.

## Proposed obligations, explicitly replacing only free-end resolution assignment

All rows below mean both epsilon values and all 101 samples. Original rigid
standing-wave obligations remain unchanged. Every row retains all errors,
phase eligibility labels, L1/L2 and observed orders in its report. No row may
hide tails or remove failed historical values.

| N | CFL | Stability and conservation | Convergence obligation | Absolute precision | Relative precision | Phase |
|---|---|---|---|---|---|---|
| 200 | .2 | Required | Temporal sensitivity report | Report | Report | Report |
| 200 | .1 | Required | Temporal sensitivity report | Report | Report | Report |
| 200 | .05 | Required | Spatial sequence | Report | Report | Report |
| 400 | .2 | Required | Temporal sensitivity report | Report | Report | Report |
| 400 | .1 | Required | Temporal sensitivity report | Report | Report | Report |
| 400 | .05 | Required | Spatial sequence | Report | Report | Report |
| 800 | .2 | Required | Temporal sensitivity report | Report | Report | Report |
| 800 | .1 | Required | Temporal sensitivity report | Report | Report | Report |
| 800 | .05 | Required | Spatial sequence | Report | Report | Report |
| 1600 | .1 | Required | Fixed-N temporal comparison | <=.01 A0 | <=.01 on mask | <=pi/1600 on mask |
| 1600 | .05 | Required | Spatial endpoint and temporal comparison | <=.01 A0 | <=.01 on mask | <=pi/1600 on mask |

Here stability means completing every prescribed sample with admissible states
and no hidden retry or interrupted run; conservation means the unchanged
kernel inventory/external-flux/source ledger obligations, not just bounded
coefficients. The independent reduction does not certify those kernel ledgers.
The spatial sequence at CFL .05 must show strictly decreasing time-maximum
absolute Fourier error for each of incident, reflected and total pressure from
N200 to 400 to 800 to 1600, after accounting for reference uncertainty. Report
the successive log2 ratios and the existing field L1/L2 orders; no new claim of
global second order follows from the local centered-stencil modified equation.
For the fixed-N temporal comparison both .1 and .05 must satisfy every final
precision gate. Report coefficient differences and error margins for all
samples. Two dt values establish sensitivity, not observed temporal order or a
rigorous bound at dt=0. Any stronger temporal-order obligation must be stated
and supported separately before claiming it was verified.

This table is a scientific change in obligations. Historical N200/N400/N800
results remain VERIFICATION_FAILURE under R4, with the original metrics and
identities in historical/. Reporting them under a new convergence obligation
does not turn those historical failures into PASS. New kernel results cannot
be accepted until this assignment is adjudicated, implementation verified and
the qualified resolution's measured cost judged practical. N1600 is not an
authorization to add indefinitely finer grids. No transport method, EOS, flux,
boundary, reconstruction, integrator or material representation changes here.

## Integration and limits

The future contract impact is restricted to SV-010/free-end fixture resolution
assignment and its reference coverage. S06 adapter must apply the table and
record original-contract status separately; consumers inherit the unchanged
numerical method. S05 state storage is unaffected by this acoustic proposal.
All newly required kernel rows, both epsilon values, ledgers, current source
identities and the original unaffected rigid coverage remain obligations.
This synthetic mathematical verification is neither experimental nor
predictive validation. See summary.json for measured independent costs;
kernel costs and results are pending and must be added separately.
