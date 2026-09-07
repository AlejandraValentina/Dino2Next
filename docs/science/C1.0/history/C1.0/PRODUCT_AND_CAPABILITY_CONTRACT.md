> **Normative — C1.0** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
>
> This contract defines implementation requirements. Unexecuted verification gates remain mandatory and may not be relaxed without a Baseline Change Request (BCR).

# Product and capability contract

## Mission
Build a defensible, progressively predictive two-stroke engine simulator without copying proprietary implementations.

## GEN1 mandatory configuration
Single-cylinder, naturally aspirated, spark-ignition, crankcase-scavenged, piston-port intake, loop-scavenged engine; explicit independent transfer passages; 0D cylinder and crankcase; persistent quasi-1D intake, transfer, T3 port and tuned exhaust passages; one-revolution periodic operating points and bounded 2000–6000 rpm sweeps.

## Mandatory capabilities
CAP-001 crank-slider and measured geometry; CAP-002 conservative 0D volumes; CAP-003 unsteady quasi-1D gas dynamics; CAP-004 bidirectional dynamic ports; CAP-005 two-zone scavenging; CAP-006 prescribed SI combustion; CAP-007 heat transfer; CAP-008 gas-path/mechanical performance accounting; CAP-009 operating-point convergence and sweeps; CAP-010 provenance and reproducibility.

## Explicit exclusions
Multi-cylinder engines, turbo/supercharging, reed or rotary intake, direct injection, liquid-film/evaporation, kinetic chemistry, structural wall-temperature prediction, general junction networks, catalysts/emissions prediction, multiperiodic operating points and distributed/cloud execution.

## Outputs
Geometry/timing report; p,T,m,U and chemical/provenance composition histories; port mass/enthalpy/species flux; pipe pressure, temperature, velocity and Mach traces; PV diagram; heat-release and wall-heat ledgers; delivery, trapping, scavenging, residual and short-circuit metrics; indicated work/IMEP/torque/power; pumping work; FMEP and brake outputs only with a qualified mechanical-loss map; convergence and conservation diagnostics; complete provenance.

## Claims
After contract implementation and required verification, `NUMERICALLY_VERIFIED_GEN1` may be claimed inside the stated domain. Experimental and predictive claims require their respective independent datasets. Equivalence to EngMod2T, physical validation from synthetic tests, brake power without FMEP, or prediction from calibration data are forbidden claims.
