# Solver execution model

Preflight resolves/version-checks all datasets and rejects unsupported topology/domain/missing characterizations. The runner builds one immutable state, advances via event-aligned SSPRK2 transactions, writes diagnostics/ledgers, evaluates periodicity at the fixed cycle angle, then derives outputs. A failed step rolls back atomically. A run writes to a temporary artifact set and publishes only after manifest/hash completion. Cancellation occurs only between accepted transactions. Sweep points are independent runs; warm-start is an explicit hashed input.
