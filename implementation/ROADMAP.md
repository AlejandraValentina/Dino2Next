# Implementation roadmap

S00 COMPLETE_FOUNDATION is the tooling gate, contingent on PR_FAST at the reported HEAD. NEXT_CODEX_SCOPE = S01, not started by this audit.

The executable ordering is SCOPE_DEPENDENCY_GRAPH.md, generated from scope_registry.json. Every edge names the consumed interface. Each scope owns its listed paths, acceptance adapters and artifacts. SCOPE_VALIDATION_MATRIX.md assigns every specified mandatory VAL once.

S01–S05 establish values, geometry, thermochemistry and conservative inventories; S06–S14 establish numerical and physical subsystems; S15–S18 produce performance, orchestration, API and validation aggregation; S19–S21 implement UX journeys; S22 composes accepted components. This grouping is explanatory: the graph, not a numeric range, determines readiness to start.

H-01…H-06 block the affected scientific scopes until existing adjudicated specifications are consolidated. No roadmap milestone authorizes inventing those details. Heavy verification remains mandatory during the owning implementation milestone, never silently waived or placed in PR_FAST.
