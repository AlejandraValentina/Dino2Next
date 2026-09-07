# S08 — dynamic-ports

**Objective:** PHY-005 T3 persistent port dynamics.

**Dependencies:** S07. **Authority:** C1.0, A1.0, UX1.0 sections cited by this objective. **Allowed files:** `src/dino2next/ports/`, `tests/numerical/ports/`, `validation/fixtures/VAL-013/`, `VAL-014/`, `VAL-016/`, `VAL-020/`. **Forbidden:** unrelated modules, normative contracts, thresholds, fixtures and scientific model choices.

Implement exact contracted behavior and stable failure codes through public typed interfaces. Create unit/contract tests plus every affected VAL adapter; references must remain independent. Acceptance: `python -m compileall src`, `python scripts/check_contracts.py`, `pytest tests/numerical/ports validation/fixtures/VAL-013 validation/fixtures/VAL-014 validation/fixtures/VAL-016`, plus the affected gate class in VERIFICATION_EXECUTION_MATRIX when its runner exists. Preserve commands, logs, raw/derived artifacts and hashes.

Done requires contract compliance, deterministic replay, green acceptance and independent reviewer approval. On an absent scientific decision, emit `SCIENTIFIC_CHANGE_REQUIRED`; on failed verification, preserve failure and do not relax acceptance. Roll back the scope branch if invariants cannot be restored.
