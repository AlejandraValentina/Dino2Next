SV-010 free-end reference
========================

`free_component_cell_averages(edges, time, epsilon)` returns the analytic incident
and negative reflected Gaussian cell means. Existing standing-wave and legacy
reference functions are unchanged.

`free_observation_reference(N, sample_index, epsilon)` returns source-bound,
qualified cell-integral Fourier coefficients for N=200,400,800; j=0..100; and
1e-5 or5e-6. Use its A0 only as the fixed continuous normalization. The returned
incident/reflected records contain C, phase_eligible and error_upper. The pressure
record is their sum with an enclosed addition-rounding allowance. These are
reference values, never candidate acceptance results.

Regenerate `free_observation_qualification.json` with Python3.12:

    python validation/references/VAL-010/qualify_free.py

The qualifier ports the accepted research Simpson/interval certificate and adds
float64 coefficient rounding bounds and installed source/catalogue hashes. It
has no candidate import and requires mpmath1.3.0. All303 sample/mesh pairs are
interval-classified; half-amplitude scaling preserves intervals and masks. The
existing `qualification.json` belongs to the shared legacy reference qualification
workflow; it must be regenerated separately after any reference-source change.
No claim of independent review is made by this reference author.
