> **Normative — C1.0-R1** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
>
> This contract defines implementation requirements. Unexecuted verification gates remain mandatory and may not be relaxed without a Baseline Change Request (BCR).

# Structural scientific decisions

| ID | Selected decision | Why |
|---|---|---|
| PHY-DEC-001 | 0D cylinder/crankcase + persistent quasi-1D passages | Captures 2T wave dynamics with identifiable GEN1 scope. |
| PHY-DEC-002 | Isooctane gas, five NASA species, global reactant-limited reaction | Closed thermodynamic meaning without pretending gasoline or kinetic chemistry. |
| PHY-DEC-003 | Conservative two-zone scavenging | Represents short circuit/residual history with identifiable parameters and exact ledgers. |
| PHY-DEC-004 | T3 dynamic port, W2 passive loss, offline lambda characterization | Instantaneous branch coupling and Cd-only inversion were falsified in C05/C08. |
| PHY-DEC-005 | Annand/Hcc/Gnielinski and Churchill/measured-K/FMEP boundaries | Domain-specific closures; prevents heat/loss double counting. |
| NUM-DEC-001 | Finite volume, HLLC-Davis plus localized AR-002 interpolated shock flux | Passed explicit-shock NP, contact, area and reflection gates with conservation. |
| NUM-DEC-002 | NASA characteristic MUSCL with MC/minmod shock stencil | Controls shock-wave interaction while preserving smooth/contact accuracy. |
| NUM-DEC-003 | SSPRK2 unsplit, AF+pΔA, shared conservative coupling | One temporal state and ledger across 0D/1D/source interfaces. |
| NUM-DEC-004 | Reject transaction, halve dt, max 16; no clipping | Preserves inventories and makes failure observable. |
| VAL-DEC-001 | Verification ladder and immutable heavy gates | Numerical verification, physical validation and held-out prediction remain distinct. |
| LEG-DEC-001 | SALVAGE knowledge only; no mandatory legacy code | Greenfield implementation must stand on C1 contracts. |
