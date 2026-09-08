# Agent authority

Precedence: `docs/science/C1.0` → `docs/architecture/A1.0` → `docs/ux/UX1.0` → active scope. Never change equations, closures, species, fixtures, thresholds, failure meanings, Cd/lambda semantics or output meanings inside an implementation scope. Never add clipping or an undocumented physical fallback. If required, report `SCIENTIFIC_CHANGE_REQUIRED` and stop that scope. One scope per branch `codex/SXX-short-name`; builder tests, independent reviewer checks contracts, then CI and PR. Legacy code is not a dependency.

Read implementation/CODEX_START_HERE.md before selecting work. Registry-backed scopes and dependency/validation ownership are checked by scripts/check_scopes.py. Run scripts/run_gate.py PR_FAST with the configured environment. Open readiness issues block affected scientific scopes; do not infer missing clauses from a frozen status label. Future test paths are obligations, not already passing tests.

Active baseline revision: C1.0-R5. BCR-S06-MATERIAL-RESOLUTION selects only MR-008 interior representation and MR-010 resolution obligations, after independent review. R4 and TI-001..005 remain except for explicit bounded supersession. H-01..H-06 remain CLOSED; S06 remains pending complete implementation and verification. No unrelated scientific change is authorized; unsupported consumer events require explicit contracts before implementation.
