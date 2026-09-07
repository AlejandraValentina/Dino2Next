from pathlib import Path
required = [
 "docs/science/C1.0/GEN1_CONTRACT.md", "docs/science/C1.0/PHYSICS_SPEC.md",
 "docs/science/C1.0/NUMERICAL_METHOD_SPEC.md", "docs/science/C1.0/VALIDATION_SPEC.md",
 "docs/architecture/A1.0/SOFTWARE_ARCHITECTURE.md", "docs/ux/UX1.0/ENGINEERING_WORKFLOW.md",
]
missing = [p for p in required if not Path(p).is_file()]
if missing: raise SystemExit("missing contracts: " + ", ".join(missing))
if any("SCIENTIFIC_BASELINE_NOT_READY" in Path(p).read_text() for p in required):
    raise SystemExit("stale baseline state")
print("contract foundation present")
