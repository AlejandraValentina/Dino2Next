# Agent authority

Precedence: `docs/science/C1.0` → `docs/architecture/A1.0` → `docs/ux/UX1.0` → active scope. Never change equations, closures, species, fixtures, thresholds, failure meanings, Cd/lambda semantics or output meanings inside an implementation scope. Never add clipping or an undocumented physical fallback. If required, report `SCIENTIFIC_CHANGE_REQUIRED` and stop that scope. One scope per branch `codex/SXX-short-name`; builder tests, independent reviewer checks contracts, then CI and PR. Legacy code is not a dependency.
