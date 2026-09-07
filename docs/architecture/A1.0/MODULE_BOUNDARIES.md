# Module boundaries

| Module | Owns | May depend on |
|---|---|---|
| units | dimensions/conversion display boundary | standard library |
| geometry | crank/volumes/areas/events | units |
| thermo | NASA EOS/transport adapter | units, pinned datasets |
| numerics | states, reconstruction, flux, SSPRK2, guards | thermo |
| gasdynamics | quasi-1D domains/sources | geometry, thermo, numerics |
| volumes | conservative 0D and two-zone inventories | geometry, thermo |
| ports | T3/W2 and lambda-map runtime | gasdynamics, volumes |
| combustion/scavenging/heat_transfer | selected closures | thermo, volumes |
| engine | explicit GEN1 topology and ledgers | scientific modules |
| convergence | NUM-009 only | engine state protocol |
| results | authoritative output definitions | engine |
| validation | fixtures/metrics, no candidate oracles | public scientific APIs |
| application | projects/runs/preflight/orchestration | schemas, engine, results |
| api | transport/versioning only | application |
| frontend | edit/run/view/compare | generated API client |

Future replacement seams are constructor-injected scientific protocols with one GEN1 implementation each; adding a second implementation requires a BCR where science changes.
