# Codex workflow

Builder reads authority and active scope, makes the smallest complete change, runs acceptance, records artifacts and opens a PR. Independent Reviewer reads contracts first, checks diff/tests/results, and may reject unsupported science or self-oracles. Foundation CI runs PR_FAST only. Later scientific adapters use scripts/run_gate.py with explicit VAL IDs and fail if unavailable. Failures are fixed in-scope or escalated as `SCIENTIFIC_CHANGE_REQUIRED`; never rationalized by threshold changes.
