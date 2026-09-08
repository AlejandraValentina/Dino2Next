# Bounded material-region prototype (not accepted production)

Authorization: user attachment c5e323c7-55c0-4230-b129-761d6c829df4, 2026-09-08. Owner: /root/s03_runtime_builder. Owned paths: this material/ directory only. No normative contracts, production modules, historical evidence or branches changed.

Objective: demonstrate conservative 1D separated regions with accepted NASA thermodynamics, then expose wave/interaction limitations before any integration decision.

Published starting point: Pan et al. 2017, https://arxiv.org/html/1704.00519v1, section 2.3: material-volume conservative inventories and paired pressure/work exchanges. The prototype specializes Reynolds transport to moving 1D intervals; it does not reproduce the paper's multidimensional level sets, scale separation or EOS examples. Adaptation: each region contains the existing five-species mixture and four origin inventories, evaluated by the accepted NASA ThermoModel. Inviscid, chemically frozen transport has no diffusion across a material surface; this does not introduce immiscibility or forbid future physical mixing closures.

Proposed implementation interface: State(edges, inventory[n,12], labels), RegionSolver(model).initialize(physical intervals), .step(state,dt), .sample(state,fixed_edges). Inventory order matches accepted Q12; area is one square metre in this bounded prototype. Initial physical region locations are required. No inverse history reconstruction from a homogeneous cell average.

All computational interval faces initially move with a state-derived HLLC contact speed. Shared ALE flux at that speed is (0,p*,p*u*,0,...). Edges and extensive inventories advance together with SSPRK2. This Lagrangian demonstration is broader than a localized Eulerian interface patch: a production coupling/remap decision remains explicitly OPEN. Spatial order is initially one, not the selected production MUSCL operator. Do not transfer existing kernel acceptance.

Admissibility: accepted NASA inversion, nonnegative constituent inventories, positive widths; failed complete trial returns unchanged state and caller may halve dt. Small widths impose a step restriction; no tiny-region deletion or forced mixing. Crossing a fixed observation face changes geometric overlap, not material identity. Projection retains pieces, and aggregates conserved quantities separately from volume-averaged physical pressure. No pressure/energy correction. Smooth initial composition is represented by sampled physical parcel states; no fictitious sharp material label is inferred from species names.

First verification: nine contractual contacts, stationary and both signs of velocity, face crossing, every inventory ledger and exterior p/u. Then nonuniform pressure/wave and shock interaction controls. Reorganization test splits an interval conservatively without merging distinct states; arbitrary coalescence remains unsupported. Typed rejection and small-width rollback controls required. Report actual measured costs and errors, not VAL-008 PASS.

Commands: WSL Ubuntu /tmp/dino2next-foundation-venv/bin/python with PYTHONPATH=/mnt/e/dino2/Dino2Next-S06-MR/src; run local pytest and explicit prototype driver. Artifacts remain inside this owned research directory until parent publishes selected evidence. No full NASA campaign before bounded independent review.
