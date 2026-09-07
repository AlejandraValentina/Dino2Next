# Codex start contract

NEXT_CODEX_SCOPE = S01. S00 = COMPLETE_FOUNDATION after PR_FAST succeeds. Do not start S01 as part of the foundation review. Global readiness remains blocked by the three remaining specification gaps; S01 has no direct scientific gap and depends only on S00.

1. Read root AGENTS, docs/CODEX_READINESS_AUDIT.md, then C1 GEN1_CONTRACT and its authority order. C1 governs science, A1 organization, UX1 journeys, active scope implementation. Hash integrity is necessary, not proof of completeness.
2. Read PUBLIC_INTERFACE_CONTRACT, SCOPE_DEPENDENCY_GRAPH, SCOPE_VALIDATION_MATRIX and the next scope. Every dependency must have accepted artifacts, not merely a closed task.
3. Branch from the accepted foundation using `codex/S01-units-config-provenance` (general pattern `codex/SXX-short-name`). One scope per PR. Never merge another scope implicitly.
4. Builder records objective, owned paths, consumed/produced interfaces and exact test commands before edits. Check Specification preconditions. No invented equations, fixture values, thresholds or output denominators.
5. Reviewer independently checks the diff, public interfaces, units, mutation/failure boundaries, nonzero collected tests and provenance. Rerunning a fixture grants no edit ownership. Reviewer must not approve their own unreviewed scientific interpretation.

## Setup and mandatory commands

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements/foundation.txt
python -m pip install --no-build-isolation --no-deps -e .
npm --prefix frontend ci --ignore-scripts
python scripts/run_gate.py PR_FAST
```

Then run every command in the active scope, including each enumerated VAL adapter. Future adapters must be created by their owner; unavailable fixtures are not skip/PASS. `python scripts/check_scopes.py --readiness` intentionally fails while H-01/H-02/H-03 remain unresolved. It is separate from the foundation structural CI.

## Stop/report rules

IMPLEMENTATION_DEFECT: fix within owned paths and rerun. VERIFICATION_FAILURE: preserve inputs/logs/reference/errors; do not relax acceptance. SCIENTIFIC_CHANGE_REQUIRED: report exact normative ID, missing/contradictory clause, affected consumers/tests, evidence and required adjudication; stop affected work. OUT_OF_SCOPE: return change to its owner, no opportunistic rewrite.

PASS means the named gate ran all its required checks at the reported commit. PR_FAST PASS means tooling/integrity/structural consistency only. It does not mean numerical verification, scientific validation, predictive validation, or globally executable science. Heavy runs remain MANDATORY_VERIFICATION_DURING_IMPLEMENTATION.

Active documentary revision: C1.0-R1. H-04/H-05/H-06 are restored; H-01/H-02/H-03 remain MISSING_PREIMPLEMENTATION_SCIENTIFIC_DECISION. No new scientific choice is authorized by the restoration.
