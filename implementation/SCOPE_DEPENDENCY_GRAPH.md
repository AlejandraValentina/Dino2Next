# Scope dependency graph

Registry source: `implementation/scope_registry.json`. Every edge below names an actual consumed public interface. Order is topological; numbering is not a substitute for dependency acceptance.

| Producer | Consumer | Interface | Reason |
|---|---|---|---|
| S00 | S01 | `FoundationChecks` | Run the installed acceptance and integrity tools |
| S01 | S02 | `ConfigSnapshot` | Consume SI quantities, hashes and schema metadata |
| S01 | S03 | `ConfigSnapshot` | Bind SI inputs and immutable dataset hash |
| S02 | S04 | `GeometryModel` | Evaluate stage volume and displacement rate |
| S03 | S04 | `ThermoModel` | Recover state from extensive chemical masses and energy |
| S02 | S05 | `GeometryModel` | Consume physical face/average geometry |
| S03 | S05 | `ThermoModel` | Recover NASA states |
| S05 | S06 | `DuctState` | Read conservative mesh/state arrays |
| S03 | S06 | `ThermoModel` | Use consistent thermodynamic derivatives and state recovery |
| S03 | S07 | `ThermoModel` | Evaluate donor thermodynamics |
| S04 | S07 | `VolumeInventory` | Return paired increments to the volume |
| S06 | S07 | `NumericalKernel` | Consume reconstructed traces |
| S05 | S08 | `DuctState` | Own persistent passage state |
| S07 | S08 | `BoundaryCoupler` | Produce interface traces and paired fluxes |
| S01 | S09 | `ConfigSnapshot` | Bind raw and derived resource identity |
| S03 | S09 | `ThermoModel` | Use the certified EOS |
| S08 | S09 | `PortPassage` | Evaluate the fixed characterization passage |
| S02 | S10 | `GeometryModel` | Get time-aligned geometry |
| S04 | S10 | `VolumeInventory` | Update extensive state |
| S08 | S10 | `PortPassage` | Consume paired passage transfers |
| S08 | S11 | `PortPassage` | Connect the explicit physical passages |
| S10 | S11 | `EngineVolumes` | Resolve endpoint inventories |
| S09 | S11 | `CharacterizedLoss` | Use characterized lambda in all coupled verification fixtures |
| S04 | S12 | `VolumeInventory` | Compose extensive primitive ledgers |
| S10 | S12 | `EngineVolumes` | Implement the cylinder closure interface |
| S11 | S12 | `EngineTopology` | Resolve transfer/exhaust event IDs |
| S03 | S13 | `ThermoModel` | Use formation-inclusive species properties |
| S10 | S13 | `EngineVolumes` | Read cylinder inventory |
| S12 | S13 | `ScavengingModel` | Require conservative merged state at SOC |
| S03 | S14 | `ThermoModel` | Use pinned transport/EOS properties |
| S11 | S14 | `EngineTopology` | Locate physical walls and loss regions |
| S09 | S14 | `CharacterizedLoss` | Exclude W2 characterization regions from local K |
| S12 | S14 | `ScavengingModel` | Combined source verification includes zone exchange |
| S13 | S14 | `CombustionModel` | Combined source verification includes prescribed chemistry |
| S10 | S15 | `EngineVolumes` | Consume cylinder/crankcase work ledgers |
| S12 | S15 | `ScavengingModel` | Consume accepted scavenging cycle metrics |
| S13 | S15 | `CombustionModel` | Consume burn/energy diagnostics |
| S14 | S15 | `PhysicalSources` | Consume wall/gas/mechanical loss ledgers |
| S06 | S16 | `NumericalKernel` | Execute SSPRK stage proposals |
| S07 | S16 | `BoundaryCoupler` | Pair global stage transfers |
| S09 | S16 | `CharacterizedLoss` | Evaluate guarded loss map |
| S11 | S16 | `EngineTopology` | Order physical components/events |
| S12 | S16 | `ScavengingModel` | Apply zone rates and events |
| S13 | S16 | `CombustionModel` | Apply reaction coordinate |
| S14 | S16 | `PhysicalSources` | Assemble heat/shear source rates |
| S15 | S16 | `PerformanceResult` | Assess output defects |
| S01 | S17 | `ConfigSnapshot` | Use canonical immutable resources |
| S16 | S17 | `EngineRunner` | Execute supported point/sweep requests |
| S15 | S17 | `PerformanceResult` | Serialize backend authoritative outputs |
| S01 | S18 | `ConfigSnapshot` | Hash fixture/reference resources |
| S06 | S18 | `NumericalKernel` | Consume canonical candidate runner |
| S09 | S18 | `CharacterizedLoss` | Read characterization provenance |
| S16 | S18 | `EngineRunner` | Run combined/periodic fixtures |
| S17 | S19 | `ApplicationAPI` | Consume generated client, schemas and immutable revision endpoints |
| S00 | S19 | `FoundationChecks` | Explicit tooling handoff for frontend package/lock/tsconfig after S00 completion |
| S17 | S20 | `ApplicationAPI` | Consume run/preflight/cancel/sweep endpoints |
| S19 | S20 | `ModelWorkspace` | Use shell route outlet and stable field links |
| S17 | S21 | `ApplicationAPI` | Read authoritative traces, result and provenance |
| S19 | S21 | `ModelWorkspace` | Use shell route outlet and unit preferences |
| S18 | S22 | `ValidationRunner` | Consume gate results |
| S20 | S22 | `RunWorkspace` | Drive run workflow |
| S21 | S22 | `ResultsWorkspace` | Render accepted results |
| S17 | S22 | `ApplicationAPI` | Wire local application service |
| S00 | S22 | `FoundationChecks` | Explicit final packaging metadata handoff; no scientific dependency selection |

## Explicit tooling handoffs
- S00 owns `frontend/package.json`, `frontend/package-lock.json`, `frontend/tsconfig.json` at foundation. S19 may extend them solely for React/Vitest/Playwright after S00 is complete; later UI scopes cannot edit them independently.
- S00 owns `pyproject.toml` at foundation. S22 owns final packaging composition after dependencies complete. Packaging changes do not authorize changing scientific dependencies or algorithms.
- Other cross-scope edits return to the owner scope; no blanket shared directories.

S18 is an aggregator, not a prerequisite for earlier scientific test execution. Each fixture owner supplies a standalone pytest acceptance adapter; S18 later consumes it. This removes the previous validation-runner dependency cycle.

## MR-008 bounded S05 to S06 handoff
- S05 retains ownership of `src/dino2next/gasdynamics/`. S06 may edit only `src/dino2next/gasdynamics/__init__.py` (additive public exposure), `src/dino2next/gasdynamics/regional.py` (regional extension), and `src/dino2next/gasdynamics/README.md` (documentation), under its explicit MR-008 material_path_handoff declaration.
- This grants no shared directory, sibling file, S05 test path, other-scope access, or replacement of accepted homogeneous behavior. New tests remain in S06-owned test paths.
