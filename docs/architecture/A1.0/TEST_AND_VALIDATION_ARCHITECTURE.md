# Test and validation architecture

Directories: `tests/unit`, `tests/numerical`, `tests/scientific`, `tests/integration`, `tests/contract`, `tests/system`, `tests/frontend`; immutable `validation/fixtures`, `validation/references`, `validation/expected`. Unit tests check software behavior. Numerical verification checks equations. Scientific/experimental validation checks physical evidence. Reference generators live outside candidate modules, declare independence and never import candidate flux/coupling implementations.

CI classes: PR_FAST (format/lint/type/unit/contracts/light fixtures/frontend); PR_SCIENTIFIC_AFFECTED (affected canonical subset); MILESTONE_FULL (cumulative suite); HEAVY_VERIFICATION (manual/scheduled high refinement); EXPERIMENTAL (controlled data access). Status pages must show outstanding heavy gates.
