# Data and configuration contract

Human project files are YAML validated against JSON Schema; run requests/results/manifests are canonical JSON plus binary columnar trace files. Every numeric field stores SI value and dimension; UI-unit preference is separate. Cd/lambda maps, NASA data, geometry curves and experimental series are immutable versioned resources with station metadata, uncertainty and SHA-256. Unknown fields are rejected for normative schemas. Migrations are explicit and never reinterpret values silently.
