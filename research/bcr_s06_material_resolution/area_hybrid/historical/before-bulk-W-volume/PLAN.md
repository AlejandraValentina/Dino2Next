# Variable-area hybrid prototype, not selected GEN1 implementation

Owned path: area_hybrid/ only. Consume frozen local hybrid, accepted NASA/S05 polynomial geometry, and reviewed regional_geometry VolumeMap. No edits to their sources, production, W2/T3 or contracts.

Authoritative state is face cumulative volume W plus extensive Q12, labels and geometry identity. Positions derive from monotone W inversion; volumes are differences of W. Advance W and inventories together with SSPRK2. Area-scaled ALE flux and pΔA sources share each stage; both FE endpoints and final combination must be guarded. Remap overlap fractions use exact area integrals and original final-remainder bookkeeping within a material label.

Ordinary bulk calls remain the pinned NumericalKernel. Inputs use exact area averages and conservative A*U; region thermodynamics never use EOS of a mixed observation projection. First prototype covers one polynomial segment; segment joins and physical birth/exit remain unsupported rather than suppressed. Tests first cover rest/thermal contact, source/GCL algebra, Y2 rejection and explicit constant-area baseline comparison. No full variable-area campaign or acceptance before independent review.
