# Bounded S06 verification-contract evidence

This directory contains reproducible mathematical diagnostics for the four
decisions of BCR-S06-VERIFICATION-CONTRACT. These are not engine experiments,
production acceptance, or a substitution for complete S06 fixture execution.

The original contract is preserved under docs/science/C1.0/history/C1.0-R3.
Historical candidate evidence is bound to77caaba; the published implementation
and extra temporal diagnostic are bound to8cf8de3. No result is relabeled as a
new-kernel result.

Use Python3.12 and the pinned requirements in this directory. Generated arrays
and logs belong under ignored artifacts/S06-BCR, not in the frozen source tree.
Scientific review and BCR adoption precede implementation acceptance.

Run `python research/bcr_s06_verification/checks.py` after installing the pinned
requirements. This checks the normative evidence manifest and reruns analytical
guard/reflection proofs, interval Simpson qualification, scalar MC/extremum
diagnostics, exact rational continuous-defect bounds and the contact-target lift.
It reads the preserved full-kernel arrays from `frozen/`; it does not execute a
new kernel or promote those old arrays to acceptance of another commit.

The original source paths/hashes and path-only adaptations are recorded in
portability.json. The published-slope equations use the HTML rendering numbers
39–57 of section2.1 (PDF35–51), not the paper's PPM construction. Diagnostic
orders motivate the decision; original MC fractional orders are not new expected
acceptance thresholds. Full-kernel-diagnostic.json binds code, inputs and raw
arrays. Source/raw hashes are frozen by the C1 evidence manifest; generated
certificate hashes record the actual run and may differ with environment metadata.
