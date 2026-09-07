# VAL-001 independent reference

The reference evaluates the TI-001 definition independently in Decimal80, derives
the high integration constants directly from the immutable RAW coefficients, and
cross-checks each of 108 composition/temperature rows with Cantera 3.2.0. It imports
neither production thermo nor the BCR generator/evaluator. Cantera receives explicit
derived constants and the prescribed high branch at equality. Pressure-dependent
density follows the ideal-gas equation for all four contracted pressures during
acceptance. All original 384 tuples remain required; 300 K adds 48 tuples.

Install `requirements.txt` in a separate Python 3.12 reference environment, then:

```sh
python validation/references/VAL-001/build_reference.py
python validation/references/VAL-001/build_reference.py --check
```

The second command checks exact reproduction in the recorded environment; version
metadata intentionally identifies that environment. `reference.json` binds source,
derived representation, generator, reference code, fixture, catalogue and package
lock hashes. Its qualification is the independent property cross-check, not a
production acceptance result. Production tests compare properties and both inverse
temperatures/residuals against these independently calculated values and preserve
raw candidate/reference rows in `artifacts/S03/VAL-001-results.json`.

Acceptance also independently recomputes the exact rational Bernstein bounds
over the full two temperature intervals, checks that the installed production cp
coefficients match, and re-evaluates both original RAW roots in Decimal80. The
preserved BCR result bytes are bound in the reference provenance. The old ambiguity
therefore remains a regression; it is not erased by adopting the derived dataset.

RAW-minus-derived offsets are reported separately. Physical uncertainty is not
estimated. Pure species are mathematical stress cases; mixture and geometry data
are numerical fixtures. None is experimental or predictive validation.
