> **Normative — C1.0-R6** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
> Adoption requires independent review and exact-HEAD checks; branch contents alone are not acceptance.

# BCR-S06-VERIFICATION-STAGING

**Baseline:** C1.0-R5 → C1.0-R6. Preserves C1.0-R5 `BCR-S06-MATERIAL-RESOLUTION` (`MR-008`/`MR-010`), `BCR-S06-VERIFICATION-CONTRACT` (`SV-008/009/010/027`), `BCR-S03-NASA-INVERSION`, `NASA` `TI-001..005`, `T3`, `W2`, composition, losses, combustion, flux, `SSPRK2`, thresholds, fixtures, references, `101` samples, `PASS/FAIL` criteria, `ST003` ledger `1e-10`, and all historical failures. **No physics, EOS, closure, species, method, threshold, tolerance, reference, or criterion is changed.** The only modification is **verification staging governance**: when a sufficient subset of `VAL-008` allows downstream consumption.

## 1. Two gates

### GATE_A — `S06_IMPLEMENTATION_ACCEPTED_FOR_DOWNSTREAM`

- **Claim:** The `S06` kernel with `MR-008` (`W/I12`, `W`-weighted `p`, `HLLC-Davis` regional, `SSPRK2` transactional, `AF+pΔA`, `GCL`) preserves `p`-equilibrium on `NASA` multicomponent contacts and resolves `NASA` shocks with conservation and admissibility, with **representative evidence sufficient for `S07→S16` to proceed**. It does **not** claim `S06` fully numerically verified, `NUMERICALLY_VERIFIED_GEN1`, experimental or predictive validation.
- **Fixture:** Same `VAL-008` fixture (`validation/fixtures/VAL-008/input.json`, `fd96f3e5…`, 18 cases, 101 samples, `S=1293` contacts / `2544` shocks, `A=1`, `W=[0,1]`) and same `validation/references/VAL-008/qualification.json` (`REFERENCE_QUALIFIED`, `candidate_imports=false`, `d435bd29…`).
- **Thresholds:** Identical to `C1.0-R5` (`operational` `L1 5e-4` / `Linf 5e-3`, `thermal` `2e-3`/`2e-2` normalized `p/1e5`, `ledger 1e-10`, `shock` `order ≥0.5` on last two levels, `GCL`, `max(|u|+a) ≤ S`).
- **Matrix:** **32 unique corridas** (20 contactos +12 shocks) listed in §2 and in `validation/fixtures/VAL-008/gate_a_matrix.json` (machine-readable). `GATE_A` **passes** iff all 32 **pass** with same per-row `PASS/FAIL` as `C1.0-R5`.
- **Effect:** `S06` becomes `COMPLETE_IMPLEMENTATION` for downstream consumption; `S07` may consume `NumericalKernel` + `RegionalDuctState`; `S18` records `GATE_A` as `PARTIAL_VERIFICATION`; `S22` may integrate `S06` for `S07→S16` without `GATE_B`.

### GATE_B — `NUMERICAL_VERIFICATION_COMPLETE`

- **Claim:** The **full** `VAL-008` matrix of `C1.0-R5` (81 contacts +108 shocks = **189** corridas, 101 samples, 3 `N` / 4 `N` and 3 `CFL`) **all pass** with identical thresholds and reference. This is the campaign that today is in `artifacts/VAL-008/` and in `validation/fixtures/VAL-008/input.json`.
- **Matrix:** `189 − 32 = 157` corridas restantes (61 contactos +96 shocks) listed as `GATE_B` in `gate_a_matrix.json` (`gate: "GATE_B"`). `GATE_B` **reuses** the 32 `GATE_A` artifacts (`raw_sha256`) without rerun.
- **Effect:** When `GATE_B` passes, `S06` becomes `NUMERICALLY_VERIFIED_GEN1` and `S18` can close `VAL-008` as `VERIFIED`. `GATE_B` is **mandatory before any `NUMERICALLY_VERIFIED_GEN1` claim**, but **not before `S07→S16` development**. It may run **in parallel** with `S07→S16` in `S18`/`S22` as `HEAVY_VERIFICATION`.

**Transition:** `GATE_A` is a strict subset of `GATE_B` (same fixture, thresholds, samples, reference). Passing `GATE_A` does **not** guarantee passing `GATE_B`, but failing `GATE_A` implies failing `GATE_B`. `GATE_B` reuses `GATE_A` evidence. `VAL-010` remains `COMPLETE_NO_RERUN` in both gates.

### Non-equivalence

`GATE_A` **does not** imply and **must not be promoted as**:

- `S06` fully numerically verified
- `NUMERICALLY_VERIFIED_GEN1` or `SCIENTIFICALLY_COMPLETE_GEN1`
- experimental validation (`VAL-022/025/026`) or predictive validation
- `GEN1` readiness

`S18`/`S22` must keep `GATE_B` **visible** (`PENDING` until `189/189`) and must **not** promote `NUMERICALLY_VERIFIED_GEN1` until `GATE_B` is `PASS`.

## 2. GATE_A matrix — 32 corridas (machine-readable: `validation/fixtures/VAL-008/gate_a_matrix.json`)

Derived from `research/s06_verification_staging/S06_VERIFICATION_STAGING_PROPOSAL.md` §6, revalidated to cover exactly the phenomena (§3), with duplicates removed and `PASS_REUSABLE` conserved only where identity and pertinence are demonstrated (same `pair`, `velocity`, `ratio`, `N`, `CFL`, `W`, `S`, `101` samples, `reference_qualification`).

| # | gate | case | N | CFL | kind | pair | velocity / ratio | Phenomenon |
|---|---|---|---|---|---|---|---|
| 1 | GATE_A | contact-pair0-u0 | 100 | 0.2 | contact | 0 | 0.0 | `PASS_REUSABLE` operational stationary minimal |
| 2 | GATE_A | contact-pair0-u100 | 100 | 0.2 | contact | 0 | 100.0 | `PASS_REUSABLE` operational +100 |
| 3 | GATE_A | contact-pair1-u100 | 200 | 0.1 | contact | 1 | 100.0 | `PASS_REUSABLE` thermal +100 fine |
| 4 | GATE_A | contact-pair1-u-100 | 100 | 0.2 | contact | 1 | -100.0 | `PASS_REUSABLE` thermal -100 |
| 5 | GATE_A | contact-pair0-u0 | 100 | 0.1 | contact | 0 | 0.0 | operational `CFL` 0.1 (already **PASS** 226.6s) |
| 6 | GATE_A | contact-pair0-u0 | 100 | 0.05 | contact | 0 | 0.0 | `CFL` fine (already **PASS** 462.0s) |
| 7 | GATE_A | contact-pair0-u0 | 200 | 0.2 | contact | 0 | 0.0 | spatial `100→200` (already **PASS** 504.5s) |
| 8 | GATE_A | contact-pair0-u0 | 200 | 0.1 | contact | 0 | 0.0 | spatial + `CFL` (already **PASS** 912.0s) |
| 9 | GATE_A | contact-pair1-u0 | 100 | 0.2 | contact | 1 | 0.0 | thermal stationary |
| 10 | GATE_A | contact-pair1-u100 | 100 | 0.2 | contact | 1 | 100.0 | thermal +100 `N=100` |
| 11 | GATE_A | contact-pair1-u-100 | 100 | 0.1 | contact | 1 | -100.0 | thermal -100 `CFL` |
| 12 | GATE_A | contact-pair2-u0 | 100 | 0.2 | contact | 2 | 0.0 | reactive stationary |
| 13 | GATE_A | contact-pair2-u100 | 100 | 0.2 | contact | 2 | 100.0 | reactive +100 |
| 14 | GATE_A | contact-pair2-u-100 | 100 | 0.2 | contact | 2 | -100.0 | reactive -100 |
| 15 | GATE_A | contact-pair1-u100 | 400 | 0.05 | contact | 1 | 100.0 | **spatial thermal** `100→200→400` |
| 16 | GATE_A | contact-pair0-u0 | 400 | 0.05 | contact | 0 | 0.0 | **spatial operational** `100→200→400` |
| 17 | GATE_A | contact-pair2-u100 | 200 | 0.2 | contact | 2 | 100.0 | reactive +100 `N=200` |
| 18 | GATE_A | contact-pair2-u-100 | 200 | 0.2 | contact | 2 | -100.0 | reactive -100 `N=200` |
| 19 | GATE_A | contact-pair0-u-100 | 100 | 0.2 | contact | 0 | -100.0 | operational -100 `N=100` |
| 20 | GATE_A | contact-pair0-u-100 | 100 | 0.1 | contact | 0 | -100.0 | operational -100 `CFL` |
| 21 | GATE_A | shock-pair0-ratio2 | 80 | 0.2 | shock | 0 | 2.0 | weak `N=80` |
| 22 | GATE_A | shock-pair0-ratio5 | 80 | 0.2 | shock | 0 | 5.0 | medium `N=80` |
| 23 | GATE_A | shock-pair0-ratio10 | 80 | 0.2 | shock | 0 | 10.0 | strong `N=80` |
| 24 | GATE_A | shock-pair0-ratio5 | 160 | 0.05 | shock | 0 | 5.0 | **spatial** `80→160` |
| 25 | GATE_A | shock-pair0-ratio5 | 320 | 0.05 | shock | 0 | 5.0 | `80→320` |
| 26 | GATE_A | shock-pair0-ratio5 | 640 | 0.05 | shock | 0 | 5.0 | `80→640` complete |
| 27 | GATE_A | shock-pair0-ratio5 | 160 | 0.2 | shock | 0 | 5.0 | **CFL** `0.2` |
| 28 | GATE_A | shock-pair0-ratio5 | 160 | 0.1 | shock | 0 | 5.0 | `CFL` `0.1` |
| 29 | GATE_A | shock-pair1-ratio5 | 160 | 0.05 | shock | 1 | 5.0 | thermal `pair1` medium |
| 30 | GATE_A | shock-pair2-ratio10 | 160 | 0.05 | shock | 2 | 10.0 | reactive strong `pair2` |
| 31 | GATE_A | shock-pair1-ratio2 | 80 | 0.2 | shock | 1 | 2.0 | `pair1` weak |
| 32 | GATE_A | shock-pair2-ratio5 | 80 | 0.2 | shock | 2 | 5.0 | `pair2` medium |

*20 contactos (all 3 pairs, all 3 directions, `CFL` 0.2/0.1/0.05 at least in 1 case, 2 spatial sequences `100→400`) +12 shocks (3 `ratio`, 3 pairs, 1 spatial `80→640`, 1 `CFL` complete). No duplicate `(case,N,CFL)`. `PASS_REUSABLE` only where `pair/velocity/ratio/N/CFL/W/S` identity and `reference_qualification` pertinence are demonstrated (same `input.json` and `qualification.json`).*

**GATE_B** = the remaining **157** corridas from `input.json` (61 contacts +96 shocks) not in this table, with same thresholds and `101` samples. `GATE_B` is **not** a new fixture.

## 3. Governance

- `S06` `status` remains `NOT_STARTED` in registry until `GATE_A` passes, then `COMPLETE_IMPLEMENTATION` (downstream) and after `GATE_B` `NUMERICALLY_VERIFIED`. No change to `allowed_paths` (still `src/dino2next/numerics/` + `validation/fixtures/VAL-008/` etc. + `gasdynamics` handoff).
- `S07→S16` may **consume** `NumericalKernel` + `RegionalDuctState` **only after** `GATE_A` `PASS`. They retain `MR-008` identities and must not invent birth/exit/collision physics.
- `S18`/`S22` must keep `GATE_B` **visible** (`PENDING` until `189/189`) and must **not** promote `NUMERICALLY_VERIFIED_GEN1` until `GATE_B` `PASS`.
- `artifacts/VAL-008/campaign_checkpoint.json` gains `gate` field (`"GATE_A"` or `"GATE_B"`). `GATE_A` checkpoint is `32/32`; `GATE_B` checkpoint is `189/189` and reuses `GATE_A` artifacts (`raw_sha256`).
- `validation/fixtures/VAL-008/execution.py` and `tests/numerical/VAL-008/test_acceptance.py` gain `GATE_A` adapters (`test_gate_a_nasa_sequence`, `gate_a_matrix.json`) that reuse `execute()` with same `metric`/`ledger` and `101` samples. The existing `test_complete_nasa_sequence` (189) remains for `GATE_B`.

## 4. Non-goals and preservation

- **No change** to `BCR-S06-MATERIAL-RESOLUTION` (`MR-008`/`MR-010`), `BCR-S06-VERIFICATION-CONTRACT` (`SV-008/009/010/027`), `BCR-S03-NASA-INVERSION`, `NASA` datasets, `T3`/`W2`, species, `R`, `gamma`, `a`, `HLLC-Davis`, `SSPRK2`, `AF+pΔA`, `ST003`, thresholds, `101` samples, or historical failures.
- `validation/fixtures/VAL-008/input.json` (189), `validation/references/VAL-008/qualification.json`, `reference.py`, `validation/expected/VAL-008/acceptance.json`, `docs/science/C1.0/EXECUTABLE_VALIDATION_FIXTURES.json`, `EXECUTABLE_VALIDATION_CATALOGUE.md`, `src/dino2next/gasdynamics/regional.py` and `src/dino2next/numerics/regional.py` are **frozen**.
- `VAL-010` remains `COMPLETE_NO_RERUN` (no rerun unless concrete invalidation).

## 5. Review and adoption

Each decision author and independent scientific reviewer must be identified in portable evidence. This BCR must not merge with an incomplete decision or a failed required check. Only after contract integration may `GATE_A` be executed and `S06` be marked `COMPLETE_IMPLEMENTATION` for downstream.

**Proposal source:** `research/s06_verification_staging/S06_VERIFICATION_STAGING_PROPOSAL.md` (`VERIFICATION_STAGING_RECOMMENDED`, 32 vs 157, `≈3.3h` vs `≈22h`).

