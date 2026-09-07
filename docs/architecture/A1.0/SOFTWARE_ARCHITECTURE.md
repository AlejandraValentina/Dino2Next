# A1.0 software architecture

Status: `A1.0 — SOFTWARE_ARCHITECTURE_FROZEN`.

Greenfield modular monorepo. The scientific core is a deterministic Python 3.12 package with NumPy/SciPy/Cantera adapters; performance kernels may later use a separately reviewed compiled backend behind identical contracts. A local FastAPI application service exposes versioned schemas. A React/TypeScript frontend consumes that API. SQLite stores project/run metadata; immutable scientific artifacts use content-addressed files. No microservices, plugin framework, distributed scheduler or cloud dependency in GEN1.

Layers: scientific core → application services → API; frontend depends only on API schemas. Validation invokes the same public core interfaces and independent references. Dependencies point inward; UI and persistence never implement physics.
