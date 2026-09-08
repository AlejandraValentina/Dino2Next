# Independent bounded prototype and architecture review

Reviewer: `/root/s01_reviewer`. Material authors: `/root/s03_runtime_builder` (global) and `/root/bcr_science_review` (local); acoustic author: `/root/bcr_science_review`; state-interface author: `/root`. This reviewer did not author those proposed methods or the state-interface document.

**Verdict: the isolated material mechanism and acoustic resolution evidence are corroborated. No complete GEN1 recipe, BCR adjudication, VAL008/VAL010 acceptance or S06 acceptance is granted.** Detailed source hashes and actual evidence are in the adjacent JSON reports.

## Material mechanism

The published `7c8ed3b2c2726633f8376f9b4fc52d1dd906e959` global prototype was reviewed from an immutable Git extraction, not from a concurrently edited file. Seven original tests passed independently; every stored step of all nine contacts was recovered with the accepted EOS, and global inventory/exterior-ledger residuals were recomputed. Mass, all species and all origin inventories remain unchanged in that Lagrangian demonstration. It does not use the reference contact trajectory in its evolution.

Two concrete integration defects were reported: missing admissibility check of the second Euler endpoint before the final SSPRK combination, and incomplete diagnostic transaction identity/status. A deliberately instrumented RHS reproduced a negative second-endpoint width with an admissible final width. The author preserved the original version and repaired both defects. Ten revised tests passed independently; the same probe now rejects at FE2_STATE with an unchanged input and a rejected transaction. All nine contact NPZ trajectories remain byte-identical. The reviewed revised global source is `be0a1d24dde91ff7cc54c6e7111a320195f113d019cbb068b98800337a68ca32`.

The separate local prototype was then reviewed at source `c2f9d81ce57a8cae741839b5522185e10485c7cabe1070a935500a13387d3eee`. Eight tests passed independently. All nine raw/source bindings, final regional EOS states, stage exterior fluxes and diagnostic transaction links were checked. An independent compensated reconstruction gives maximum ST003-normalized global residual `1.73957e-16`. Geometric small cuts are reorganized within the same material; the contact persists and crosses ordinary base faces. Raw files do not contain every intermediate Q, so the author's maximum-over-time pressure is not represented here as an independently reproduced maximum.

The published starting point is relevant: [Pan et al., section 2.3](https://arxiv.org/html/1704.00519v1) describes material-volume balances and paired interface pressure/work exchange. The prototypes use that principle, not the paper's complete algorithm. NASA recovery, Davis speeds, 1D remap/exclusion policy and their guards remain explicit adaptations requiring their own proofs and verification. The paper does not establish the proposed `.35 dx` rule or a NASA GEN1 accuracy guarantee.

The local mechanism supports another bounded integration prototype. It still uses first-order ordinary states/remap; it does not yet reproduce the selected MUSCL/bulk flux/guard path. Thin physical slabs, exits, collisions, entering material, variable area and qualified shock interaction are unresolved. Conservation alone does not establish their accuracy or practical cost. No additional general multidimensional framework or new physical immiscibility closure is justified.

## Acoustic evidence

The N1600 qualifier differs mathematically from the previously accepted qualifier only in mesh coverage. I replayed it independently with output redirected to a separate artifact; all interval bounds, normalizations and source bindings match exactly. Actual replay cost was 19.27 seconds. Disclosure: I authored the original upstream qualifier, which received independent review in the prior baseline; this review checks the other author's coverage adaptation and replay, not a new independent approval of my original derivation.

I recomputed the Fourier operators and uncertainty-aware gates from both raw trajectories at all 101 times and both epsilon scalings. Maximum relative upper error is `0.00636967` at CFL `.05` and `0.00646775` at `.1`; absolute and phase gates also pass. The calculation includes rounding of the summed total-pressure reference. Folded-domain differences are below `8.58e-13 A0`. Recorded reduction costs are 34.33 and 18.83 seconds, respectively.

These results establish sufficient resolution for bounded nonlinear-kernel confirmation only. Positive homogeneity applies to this dimensionless reduction; both nonlinear kernel amplitudes must execute. Two CFL values demonstrate sensitivity, not temporal order or a rigorous zero-step-size bound. The proposed table explicitly separates convergence and precision obligations and preserves historical R4 failures. Its complete coverage, practical kernel cost and final contractual adjudication remain pending.

## State interface

The additive state-interface direction is clear at SHA256 `64de00f84835b8fffd936936540303407845222adab3aafb66bff1c5d8402813`. It retains homogeneous S05 and its mesh restrictions, uses one authoritative extensive regional inventory, and names volume/length pressure averages and mass-weighted ratios separately. The constant-regional-state overlap rule uses physical volumes; higher-order overlap integration remains a separate obligation. This closes the ambiguity reported in the earlier draft.

This is an architecture direction review, not approval of an implemented API or numerical recipe. Regional geometry/source integration, near-contact reconstruction, full admissibility, events, physical sources and consumer tests must be adjudicated and verified before S06 can merge. Existing S05 acceptance is historical and unchanged; affected new routes cannot inherit numerical PASS automatically.
