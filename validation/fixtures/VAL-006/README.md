# S06 canonical mathematical execution

The gamma adapter is explicitly `NUMERICAL_FIXTURE_ONLY`. It shares no
thermodynamic implementation or calibration claims with the NASA runtime.
References for VAL-006/007/009/010/011 were built independently and carry
separate 80-digit qualification evidence. VAL-027 is expressly a temporal
comparison with DOP853 on the same selected semidiscrete RHS.

Install the pinned dependencies in the existing Python 3.12 environment:

```sh
python -m pip install -r src/dino2next/numerics/requirements.txt
python -m pip install -r validation/references/VAL-006/requirements.txt
python -m pip install -r validation/references/VAL-027/requirements.txt
export PYTEST_ADDOPTS=--import-mode=importlib
```

The collection option is necessary because the contract requires repeated
`test_acceptance.py` names in directories such as `VAL-006`, which are not
Python package identifiers. It changes collection only, not assertions,
fixtures, thresholds or selection of tests. No shared packaging file changes.

Each acceptance adapter runs all its frozen cases, meshes and CFL values.
Raw candidate and reference fields, actual steps, retries, limiter records,
compensated ledgers and source identities are written under `artifacts/VAL-*`.
Interrupted executions and `EXECUTED_METRICS_PENDING_ASSESSMENT` are not PASS.

VAL-008 remains blocked by its frozen boundary setup precondition. No adapter
or manufactured PASS is supplied for that fixture; complete S06 acceptance
and downstream dependency acceptance remain unavailable.
