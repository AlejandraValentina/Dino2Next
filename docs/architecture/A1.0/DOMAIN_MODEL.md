# Domain model

`EngineProject` owns immutable-versioned geometry, model parameters, component characterizations and units preferences. `SimulationRequest` binds one project revision, operating point/sweep and solver profile. `SimulationRun` is immutable after submission and transitions QUEUED→PREFLIGHT→RUNNING→SUCCEEDED|FAILED|CANCELLED. `SimulationResult` owns scientific outputs and manifest. `Diagnostic` has code, severity, component, time/angle and evidence. `ValidationResult` binds fixture/version/reference/metric/threshold/artifacts. `TraceSeries` stores axis, unit, meaning, provenance and values. `RpmSweepResult` contains ordered operating-point run IDs and never interpolates failed points as success.

Domain objects use SI internally, explicit schema versions and content hashes. Project edits create revisions; runs reference a revision and cannot observe later edits. Deterministic replay requires identical contract/data/code/environment hashes.
