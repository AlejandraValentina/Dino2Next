# Application and API contract

Versioned endpoints/resources: projects and revisions; preflight; simulation requests/runs; run diagnostics; trace/result manifests; RPM sweeps; run comparison; validation execution/results. Commands are idempotent through request keys. HTTP/API errors carry stable code, path, reason, correction and scientific consequence. Long runs are polled or streamed as status events; scientific state remains backend-owned. Schema incompatibility fails explicitly.
