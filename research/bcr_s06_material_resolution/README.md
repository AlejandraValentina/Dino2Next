# BCR-S06-MATERIAL-RESOLUTION — prototyping and adjudication package

Status: PROTOTYPING; no normative recipe approved yet. BaseC1.0-R4/main15b070b6; implementationPR8 remains cc5c4ed66a2f8ea94cdeeeeeb32aa39e6dceb161. This new BCR is separate from mergedPR9 and from the implementationPR.

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
