> **Normative — C1.0-R3** · Status: `SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN`
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

## R2 selected adjudications

BCR-C1R2-H01-BOUNDARY, BCR-C1R2-H02-TIME-PERIODICITY and BCR-C1R2-H03-VALIDATION-FIXTURES are APPROVED/SELECTED. BC-001…008, TS-001…007 and the current executable fixture catalogue are normative. Interior AR002 and H04–06 remain unchanged. No pending numerical execution is asserted PASS.

## R3 — BCR-S03-NASA-INVERSION

SELECTED: alternative B, DINO2NEXT_NASA5_CONTINUOUS 1.0.0 under TI-001…005. Alternative A retains set-valued inversion/gaps and is not selected for GEN1 conservative state recovery. The 1e-8 K inversion budget is unchanged. No physical uncertainty or engine accuracy is inferred from continuity.

## C1.0-R4 bounded S06 decisions

BCR-S06-VERIFICATION-CONTRACT SV-008/009/010/027 is the normative companion for the four affected gates. It preserves original failed evidence, all unrelated physics, amplitude/error budgets and accepted TI-001..005. SV-009 changes only smooth acoustic limiting and requires affected kernel regressions. SV-008 preserves the original error window despite added computational guards. SV-010 separates directional reflection signals, qualifying a reference-defined observation mask and retaining absolute checks on every sample. SV-027 retains original levels and threshold and adds .000125s; reference qualification is not a two-run discrepancy mislabeled as certification. No implementation, numerical, experimental or predictive acceptance follows from document existence.

## C1.0-R5 bounded material and resolution adjudication

BCR-S06-MATERIAL-RESOLUTION MR-008 selects the represented regional interior
state and numerical route, retaining NASA TI-001..005 and physical pressure.
MR-010 explicitly assigns the free-reflection precision obligations to its
resolution table; historical R4 failures retain their original results.
These clauses supersede only conflicting homogeneous-state assumptions for
the represented regional route and the specified SV-010/free resolution
obligations. R4 guard zones, unrelated physics, thresholds, masks, tails,
operators and rigid-boundary obligations remain in force. The ordinary
homogeneous route remains explicit; evidence reuse requires actual identity
of consumed sources, state, arithmetic and reference, not merely equal fluxes.

S06 delivers the additive S05 extension under the three exact file handoffs
in its registry and must verify every affected gate. Interior selection does
not implement or qualify material birth/exit, donor reversal or source/event
coupling: their dependent consumers require explicit prior contracts and
verification, with unsupported operations rejected transactionally. S01-S05
historical acceptance remains; S06 acceptance, full-engine cost, experimental
validation and predictive validation are not established by this adjudication.
