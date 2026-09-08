# Regional geometry with variable area: proposal, not selected recipe

This research extends the questions in STATE_INTERFACE_PROPOSAL.md. It changes neither that proposal nor accepted S05, NASA, W2 or T3. The source of exact geometry is accepted PolynomialSegment, with A(x) specified explicitly as a polynomial in its local coordinate. No area interpolation is inferred from base-cell averages. The implemented control handles one polynomial segment only; multi-segment joins and production mesh coupling remain open.

For a static duct, quasi-1D Euler has ∂t(AU)+∂x(AF)=S, with momentum source p A' and zero geometric energy source. Integrating on a moving region [l,r] gives

    I = ∫[l,r] A U dx
    I' = A(l)(F_l − s_l U_l) − A(r)(F_r − s_r U_r) + (0, ∫[l,r] p A' dx, 0,...)
    V = ∫[l,r] A dx
    V' = A(r)s_r − A(l)s_l.

These are a Reynolds-transport specialization of the conservative regional balance, not a new caloric EOS. For first-order constant regional pressure, the source is exactly p[A(r)−A(l)]. Higher-order pressure reconstruction would require the integral of its product with A'; this control does not select that reconstruction. On a moving material face with s=u*, the area-scaled ALE flux becomes (0,A p*,A p* u*,0,...); it must be copied with opposite signs and the same stage geometry. On an ordinary fixed face, s=0. A general moving numerical face carries swept mass, energy, species and origins through F−sU; omitting those terms would violate GCL.

## Concrete failure of naive geometry staging

Take A(x)=1+x², W(x)=x+x³/3, edges l=1/2,r=1, speeds both 1/5 and dt=1/10. Updating positions by forward Euler and then recomputing exact volume gives a volume 1/5000 larger than the forward-Euler update V+dt[A(r)s_r−A(l)s_l]. Thus the inconsistency occurs already in FE1, even before the final SSPRK combination.

For unequal constant speeds s_l=1/10,s_r=1/5, the final SSPRK2 position state and the SSPRK2 update of volume differ by

    V(x_final) − V_RK = −(s_r³−s_l³) dt³/6 = −7/6000000.

These are exact rational identities in test_geometry.py. Equal speeds happen to cancel this final defect for quadratic A but do not repair the FE-stage violation. Neither endpoint admissibility nor a final-only test is enough to establish stage GCL.

## Minimal candidate coupling to adjudicate

Use cumulative volume coordinates W_f=∫[x0,x_f] A(x)dx as authoritative geometric unknowns. Advance W_f'=A(x_f)s_f with exactly the same SSPRK stages as the extensive inventories. Region volume is the linear difference W_right−W_left. Recover each physical face from the monotone map x_f=W^{-1}(W_f). Then the convex combination of W gives the same convex combination of volumes. Do not independently advance an authoritative x array and adjust energy afterward to conceal a volume discrepancy.

This is a proposed **change of discrete geometric coordinate**. SSPRK2 applied to W and inverted to x is not identical to SSPRK2 applied directly to x. Both approximate x'=s, but existing time-accuracy evidence cannot be transferred automatically. This is not claimed to be the only possible GCL treatment; it is the single bounded coupling examined here.

The minimum state implication is one cumulative-volume coordinate per integration face, exact geometry/provider identity and an explicitly derived physical coordinate. Inventories remain the only fluid conservative representation. A restart must preserve the chosen authoritative coordinate and its identity. Before production, the interface proposal must adjudicate which coordinate is authoritative, how boundary events are located, and how coordinate roundoff and stage crossing are diagnosed.

The prototype uses exact rational evaluations of the declared binary64 polynomial to bracket W inversion between adjacent representable x values. It returns both the bracket and the signed exact residual W(x_returned)−W_target. This avoids calling a rounded coordinate an exact inverse. The largest observed residual is 3.56601e-16 m³. No stored energy or composition is changed to compensate for it. A production residual/error policy is not selected by this measurement.

## What was actually checked

Five tests passed: accepted polynomial integration, exact inverse bracket/residual, the counterexamples above, pressure-area cancellation, and all-inventory stage GCL under the proposed W coordinate. These are algebra/software checks, not full variable-area numerical verification.

The stationary thermal/composition contact has N2 at 600 K on one side and CO2 at 1800 K on the other, p=100 kPa,u=0, with quadratic A. Its two regions separately show zero inventory RHS through cancellation of pressure flux and pΔA. The geometric source has no energy term. This is a legitimate inviscid rest equilibrium; no nonzero-uniform-u variable-area solution is asserted.

The manufactured moving-mesh control samples a spatially uniform static physical fluid while prescribed numerical faces move. It uses known uniform physical flux/pressure solely to test the transport/GCL algebra; it is **not** a Riemann solver, material-motion solution, or new pressure-enforcement branch. Ten steps and both Euler endpoints/final combinations were audited with the accepted NASA inverse. For N2/600 K and CO2/1800 K, maximum temperature error is 2.91e-9 K and pressure discrepancy 1.62e-7 Pa; the CO2 internal energy is negative and remains so. Conservative inventory-identity residual is at most 7.28e-13 under the explicitly diagnostic max(|inventory|,1) normalization, dominated by momentum cancellation roundoff. No ST-003/VAL gate is claimed. The measured audit cost was approximately 0.50 s.

Needed next decision: explicitly accept/reject the geometric coordinate and stage coupling before adding variable area to the regional solver. Variable-pressure source reconstruction, events/segment joins, remap topology and physical-wave accuracy are not covered. Existing local material and global ALE files remain untouched. No contract or acceptance status is changed.
