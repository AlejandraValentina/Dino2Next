# UI binding contract

S17 produces a FieldDescriptor for every supported editable leaf. S19 renders only descriptors with a consumed backend path; no free-form scientific controls. The descriptor carries an exact JSON pointer, unit conversion metadata, domain path, solver input path and provenance key. Unknown descriptors fail closed as FIELD_UNSUPPORTED. Read-only result fields cannot be posted as inputs.

| UI group / owner | Schema producer | Domain consumer | Application | Solver input consumer | Provenance |
|---|---|---|---|---|---|
| Geometry / S19 | S02 schemas/geometry | GeometryModel | S17 immutable project revision | S10 EngineVolumes, S11 EngineTopology | revision + source geometry hash |
| Port characterization / S19 | S09 schemas/port_loss | CharacterizedLoss | S17 attach characterized artifact | S08 passage via S09 evaluated source | raw-data, map and certificate hashes |
| Thermochemistry / S19 | S03 schemas/thermochemistry | ThermoModel | S17 validated dataset reference | S06 kernel/S13 combustion | dataset hash; no frontend species computation |
| Thermal/loss inputs / S19 | S14 schemas/thermal_loss | PhysicalSources | S17 validated revision | S16 source assembly | measured/calibrated source references |
| Operating point / S19 | S17 request schema | SimulationRequest | S17 preflight | S16 EngineRunner | frozen request hash |
| Run controls / S20 | S17 API schema | SimulationRun | start/cancel/status | S16 accepted-step lifecycle | run ID + revision + event sequence |
| Results/compare / S21 | S17 result schema | TraceSeries/PerformanceResult | read/export | read-only S15 outputs | run/units/claim-level/quality flags |

S17 tests every scientific editable descriptor against an actual request-to-domain-to-engine mapping. S19 tests absence of a consumer disables editing. S20 tests unsupported/invalid preflight blocks start, cancellation preserves last accepted state, stale events cannot replace newer state. S21 tests indicated/brake labels, missing brake data, failed/unverified run markings and mismatched-unit comparison. No frontend output becomes authoritative through client arithmetic.

J01–J04 are tested in frontend/tests/s19/journeys.spec.ts; J05/J06/J08 in s20; J07/J09 in s21. Route contracts are in PUBLIC_INTERFACE_CONTRACT.md. Each journey asserts navigation, data round trip, validation failure and keyboard/focus behavior; API test data is CONTRACT_TEST_ONLY.
