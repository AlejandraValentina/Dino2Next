> **Normative — C1.0-R2** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
>
> This contract defines implementation requirements. Unexecuted verification gates remain mandatory and may not be relaxed without a Baseline Change Request (BCR).

# Physics specification

## PHY-001 — geometry
Crank radius $r=S/2$, rod $l>r$, piston displacement $x=r(1-\cos\theta)+l-\sqrt{l^2-r^2\sin^2\theta}$ and $V_c=V_{clear}+A_p x$. Crankcase volume is its measured TDC reference minus piston displacement. Port/window area is measured $A_i(\theta)$ with count applied exactly once. All lengths m, areas m², volumes m³, angles rad internally.

## PHY-002 — thermochemistry
Ideal-gas mixture of gaseous isooctane C8H18, O2, N2, CO2 and H2O; four independent fractions and the fifth by closure. Dry air O2:N2=1:3.76. NASA7 coefficients and formation enthalpies are versioned inputs; low polynomial below 1000 K, high at/above, no extrapolation outside 300–2200 K. $R(Y)=R_u\sum Y_k/M_k$, $h=\sum Y_kh_k(T)$, $u=h-RT$, $c_p=\sum Y_kc_{p,k}$, $c_v=c_p-R$, $\gamma=c_p/c_v$. Pressure 50 kPa–5 MPa. Premix $0.6\le\phi\le0.8$. Global reaction C8H18+12.5O2→8CO2+9H2O, reactant-limited, no dissociation. Formation energy is included; LHV is a diagnostic, never added again.

## PHY-003 — 0D volumes and scavenging
Each 0D inventory conserves chemical masses and total internal energy. $\dot U=\sum \dot m h_0-p\dot V+\dot Q_w$. Cylinder uses two pressure-equilibrated zones: A receives transfer flow, B receives exhaust re-entry. Outflow composition/enthalpy is the model-selected mixture with $\beta=m_A/(m_A+\chi m_B)$; transfer backflow split uses $m_A/(m_A+m_B)$. A→B exchange time is $\tau=\kappa/\omega$. Birth uses no seed mass; EPC merge exactly conserves masses, tracers and energy. Hardware-specific positive $\chi,\kappa$ require characterization.

## PHY-004 — quasi-1D passages and topology
$\partial_t(AU)+\partial_x(AF)=S$, $U=(\rho,\rho u,\rho E,\rho Y_k,\rho\tau_j)$, $F=(\rho u,\rho u^2+p,u(\rho E+p),\rho uY_k,\rho u\tau_j)$. Momentum geometry source is $p\,\partial_xA$; wall heat and shear are separate physical sources. Topology is ambient→intake→crankcase; N independent transfers→cylinder; cylinder→exhaust port→variable-area tuned exhaust→ambient. No general junction. Exterior boundary uses specified static ambient pressure plus stagnation state/composition for entering characteristics; validity $ka\le0.05$, $|M_{out}|\le0.2$.

## PHY-005 — dynamic ports and loss characterization
Every port is a persistent finite-volume T3 quasi-1D passage with physical $A(x,\theta)$, perimeter and nonzero stored volume. Window opening changes communication area, never stored volume; closing preserves inventory. W2 occupies declared $\Omega_w$, $\int_{\Omega_w}w dx=1$: $S_\rho=0$, $S_m=-\lambda wA\rho u|u|/2$, $S_{\rho E}=S_{\rho Y}=S_{\rho\tau}=0$, $\lambda\ge0$. It is passive and adiabatic; kinetic loss becomes internal energy and entropy.

Raw measured Cd retains stations, area, direction and uncertainty. $Cd_0=|\dot m_{T3,\lambda=0}|/|\dot m_{ideal,C03}|$. Lambda is characterized offline. Cd alone is used only where the observation Jacobian is full-rank and conditioned; NP sectors require raw Cd plus static pressure at the start of $\Omega_w$. Missing/nonidentifiable/out-of-domain data fail explicitly. Runtime interpolates the versioned lambda map only inside certified cells; no extrapolation, negative lambda, clipping, Cd renaming or double loss.

## PHY-006 — combustion
At port-closed SOC, determine reactant-limited extent. Normalized Wiebe burn fraction uses supplied SOC, duration, $a,n,\eta$; advance a reaction coordinate and species stoichiometry while conserving formation-inclusive total energy. No combustion when ports are open; no ignition outside the specified thermochemical guards.

## PHY-007 — heat transfer
Cylinder/head/piston: Annand $h=a_A(k/B)Re^{0.7}$ with measured wall temperatures and $0.35\le a_A\le0.8$. Crankcase: required measured lumped $H_{cc}(N,T,T_w)$, $\dot Q=H_{cc}(T_w-T)$. Ducts: Gnielinski with laminar/turbulent treatment and linear transition over Re 2300–4000, validity Re≤1e6, Pr 0.6–1, $D_h/L\le0.1$, prescribed wall temperature and characterized pulsation factor $C_q$. Cantera 3.2 mixture transport dataset is version-pinned. Positive heat means into gas.

## PHY-008 — losses
Distributed wall shear uses Churchill Darcy factor with declared roughness, Reynolds and hydraulic diameter; Re→0 uses the analytic laminar limit. Measured local K is applied only at its characterized region and never where Cd/W2 already represents the loss. Shear opposes motion while total-energy source remains zero for adiabatic friction. Mechanical loss is an input FMEP map; absent qualification makes brake outputs unavailable.

## PHY-009 — tracers and metrics
F0 fresh delivered, F1 transferred, R retained burned-history and X exterior-origin are provenance tracers, not species. Relabel operations have exact ledgers. Delivery, trapping, scavenging, charging, residual and short-circuit fractions use the restored cycle-integrated definitions in PHYSICS_RESTORATION_ANNEX PH-002; zero denominator returns UNDEFINED_METRIC.

## PHY-010 — work and performance
$W_c=\oint p_c dV_c$, $W_{cc}=\oint p_{cc}dV_{cc}$, indicated metrics derive from cylinder work; pumping/crankcase work remains separate. Brake work equals indicated system work minus qualified mechanical/auxiliary losses. Each output declares indicated, pumping, friction or brake semantics.

## C1.0-R2 documentary restoration
Detailed clauses: PHYSICS_RESTORATION_ANNEX.md and LOSS_CHARACTERIZATION_NORMATIVE_ANNEX.md. These are normative companions for their explicit clause IDs; R2 adjudications are enumerated in NORMATIVE_CONSOLIDATION_RECORD.md. No silent precedence override is permitted.

## R2 executable companions

BOUNDARY_CONTRACT.md, TIME_EVENT_PERIODICITY_CONTRACT.md and EXECUTABLE_VALIDATION_CATALOGUE.md / EXECUTABLE_VALIDATION_FIXTURES.json complete the implementation contract. REFERENCE_EXECUTION_CONTRACT.md fixes the independent reference recipes. Heavy verification remains MANDATORY_VERIFICATION_DURING_IMPLEMENTATION, not an implementation prerequisite waived by readiness.
