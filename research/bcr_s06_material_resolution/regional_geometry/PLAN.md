# Variable-area regional geometry: bounded research derivation

Owner /root/s03_runtime_builder; only regional_geometry/ is editable. Consume STATE_INTERFACE_PROPOSAL.md, accepted S05 PolynomialSegment and unchanged NASA ThermoModel. No edits to material/, local_material/, production or normative contracts.

Goal: expose and test exact polynomial volume, ALE area flux, pressure-area source and discrete GCL. First demonstrate why direct SSPRK position updates with recomputed nonlinear volume violate stage GCL. Then test cumulative geometric volume as a candidate primary coordinate, not an approved recipe. Show stationary p-equilibrium on quadratic area and a manufactured moving numerical mesh for static uniform gas. Do not claim uniform nonzero velocity is an exact solution in variable area.

Interfaces: VolumeMap(accepted PolynomialSegment), cumulative(x), inverse(W) with a representable-coordinate bracket/residual; stage algebra advancing W and extensive Q together. Minimal extra geometric datum: cumulative volume coordinate per integration face and exact geometry identity/provider. Physical position is derived. Changing which coordinate SSPRK advances requires adjudication, not an undocumented correction.

Run tests with WSL Python3.12 foundationvenv, PYTHONPATH=<MR>/src. Preserve exact rational counterexample and actual algebra/NASA roundoff results. No full transport or NASA campaign in this task.
