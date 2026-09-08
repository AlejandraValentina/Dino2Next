# BCR-S06-MATERIAL-RESOLUTION â€” prototyping and adjudication package

Status: PROTOTYPING AND BOUNDED ADJUDICATION REVIEW; no normative recipe approved yet. Base C1.0-R4/main15b070b6; implementation PR8 is 2d04c16fc77b603596f7db04a8ed7d35953afa17, with the independently reviewed exact sparse-sum software change. Historical reference cc5c4ed6 is preserved. This BCR is PR10, separate from merged PR9 and from implementation PR8.

The user explicitly authorized bounded prototyping and independent scientific/architecture adjudication of two mechanisms:

* MR-008: one-dimensional conservative material subregions with the accepted NASA EOS. Material region, chemical species and origin tracer remain distinct. Prove stationary/moving contacts, face crossings, inventories and exterior pressure before addressing all thermal/composition and shock cases. A contact prototype is not a qualified fullkernel.
* MR-010: accuracy obligations assigned explicitly to resolution/CFL. Preserve1%, reference masks, tails,101samples and both epsilon. Test exactly the predefined independent N1600/CFL.05 diagnostic before deciding on a fullkernel confirmation or further transport change. HistoricalR4FAIL remainsFAIL; no indefinite mesh search.

NoNASA,T3,W2,chemistry,experiment ormultidimensional scope is reopened. S01-S05 acceptance and historical manifests remain intact. Required S05 interface extensions, small-subregion handling, initialization, smooth-composition behavior, stage coupling, computational cost and invalidated verification must be explicitly reviewed before normative adoption.

## Portable evidence

The evidence subdirectory publishes the minimum consumed states, observations and source hashes needed to review the existing compatibility failures without a localE: drive. Originalfull logs and interrupted campaigns remain retained at their recorded hashes; this package does not relabel them or claim their missing coverage. ABC pressure and spatial error fractions remain distinct;81.40% is a location fraction, not exact causal attribution. Projections of raw arrays are explicitly identified and never presented as fullledger evidence.

## Ownership and review

material/: prototype author /root/s03_runtime_builder; independent architecture/science reviewer /root/s01_reviewer, with parent review as needed.
acoustic/: independent reduction/qualification author /root/bcr_science_review; separate reviewer /root/s01_reviewer orparent (neither authored those scientific calculations).
Package/evidence/publication: /root. No reviewer may approve their own scientific contribution. Final publishedHEAD review and requiredchecks precede any BCRmerge; implementation acceptance is a separate later gate.

Contracts/manifests will be revised only after the prototypes demonstrate their role and the complete selected formulation is independently reviewed. Until then this package makes no normativechanges and does not accept S06.

## Reviewed progress after the initial snapshot

The actual independent review package is under reviews/. It corroborates the initial material demonstration and the local moving-material-face extension, closes the second-Euler-endpoint admissibility and diagnostic-transaction defects after fixes and reruns, and corroborates the N1600 reference/reduction evidence. It explicitly does not approve a complete GEN1 recipe. Original pre-fix evidence is retained; the trajectory arrays that remain bitwise identical are identified in the closure reports.

STATE_INTERFACE_PROPOSAL.md records an additive S05 direction and explicit observable weighting, with geometry/reconstruction obligations still open. The local_material/ large raw records are stored losslessly in a hash-verified ZIP; run its restore_evidence.py before replaying raw-data audits. software_equivalence/ contains the independently reviewed exact-sum and streaming-storage evidence used for full-kernel acoustic experiments. These software checks do not replace the pending numerical checks.

The subsequent increments now include independently reviewed ordinary-MUSCL coupling and exact faster overlap enumeration, nine composition/thermal/motion controls, and a directed NASA shock at N80/N160. Those are prototype evidence, not the full contractual VAL008 matrix. Large hybrid records are losslessly packaged separately: run `local_material/restore_hybrid.py`; the earlier `restore_evidence.py` and archive remain unchanged.

The variable-area prototype evolves cumulative volume W and extensive inventories together. Review found and fixed endpoint-representation and thin-region projection defects. Their original sources, results and findings remain in the package. Independent closure reviews now corroborate W-overlap and ordinary-bulk consistency, including the thin-region reproducers. The final bounded interior formulation awaits its explicit adjudication. The volumetric timestep advisor was reviewed as a predictor with stage guards, not a general NASA positivity theorem. Material birth/exit and physical boundary transfer remain explicit consumer obligations; no full GEN1 boundary recipe is claimed.

All four predefined N1600 full-kernel confirmations completed and were independently audited (both epsilon and CFL .1/.05). All 101 observations in each satisfy the unchanged absolute, relative and phase bounds, with conservation corroborated. `acoustic/kernel_data/` contains the full sampled conserved fields, execution records, assessments and costs; its manifest states that the large per-step streams are not included, although their complete independent audits and hashes are preserved. The source files consumed are copied under `acoustic/kernel_sources/` with original hashes. `acoustic/MR010_ADJUDICATION_PROPOSAL.md` proposes the explicit resolution table and retains the historical failures. Four fine runs do not complete the coarse convergence matrix, rigid-boundary coverage or S06 acceptance.

Measured acoustic cost is 20â€“36 minutes per canonical transit with four initially concurrent processes, not a full-engine benchmark or a claim of practical GEN1 cost. The accepted baseline remains C1.0-R4 until a separately reviewed normative change is integrated.
