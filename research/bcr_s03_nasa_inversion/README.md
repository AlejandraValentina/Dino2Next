# BCR-S03-NASA-INVERSION bounded evidence

Research-only reproduction; this is not the production ThermoModel, VAL-001
qualification, downstream qualification, or experimental/predictive validation.
Python 3.12; install the pinned `requirements.txt` in an isolated virtualenv.
From any checkout, at its repository root:

```sh
python research/bcr_s03_nasa_inversion/generate.py --check
python research/bcr_s03_nasa_inversion/checks.py --check
```

Omit `--check` to regenerate the respective committed output. Checks never import
production code. The source hash is the accepted immutable RAW hash from C1.0-R2,
commit `4a358b13ec357bb6e4ae07f5c418d41a17229d42` (accepted S02). The first five
species, their mass basis, Ru, polynomial coefficients and lower formation/entropy
references are preserved. The remaining RAW entries are outside NASA5 GEN1.

`generate.py` derives the two high-branch additive integration constants in
80-digit Decimal arithmetic. The normative continuous function anchors high h/s
at the low value at 1000 K and integrates the unchanged high cp or cp/T from that
anchor. The stored shifts are an audited 80-digit materialization, not independently
fitted coefficients or exact transcendental constants. Applying them and anchoring
are mathematically equivalent before numerical rounding. The derivative cp may
retain its RAW jump; h, s and e are continuous. Both RAW and derived satisfy e=h-RT.
Lower h/s/e change by zero; high h/e/s changes are constant, reported per species
with units in the dataset and per mixture in `results.json`. These representation
differences are distinct from inversion numerical error and from unestimated
physical source uncertainty.

The dataset contains exact rational Bernstein convex-hull lower/upper bounds on
cv/R for complete closed intervals covering [300,1000] and [1000,2200]. Every lower
bound is strictly positive: this is a proof over the continuous domain, not a
sample grid. R is positive, cp=cv+R is positive, and continuity joins strictly
increasing interval e/h functions. Nonnegative normalized mass mixtures inherit
these properties and therefore have unique admissible e/h inverses.

`checks.py` independently evaluates anchored polynomials with Decimal and invokes
Cantera 3.2.0 with shifted NASA constants. Explicit per-branch adapters duplicate
one branch into both Cantera intervals to handle equality without inheriting its
boundary convention. Standard entropy is compared at its reference pressure;
mixture entropy additionally contains the unchanged ideal mixing/pressure terms.
Fixtures cover the five species, air, and COMMON-001 premix/products for phi
0.6/0.7/0.8; endpoints, exact/near join, positive cv, derivative identities,
energy/enthalpy inversion, opposite-side seeds, both crossing directions, input
target preservation, deterministic results and independent Cantera inversion.
No clipping, target energy replacement, or branch extrapolation is used.

The `raw_counterexample` in results preserves the original pure-water state and
computes two roots strictly inside the correct RAW branches with the same rho/e/Y,
their residuals and their separation above the unchanged VAL-001 1e-8 K budget.
All used coefficients are available in the SHA-pinned source and repeated in the
derived dataset. Paths are checkout-relative; no local E: drive or private data
is needed. The original local diagnosis is not treated as production acceptance.
