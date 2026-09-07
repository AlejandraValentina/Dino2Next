"""Byte-exact C1 integrity. This verifies integrity, not scientific sufficiency."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'docs/science/C1.0'
MANIFEST = f'{PREFIX}/C1_BASELINE_MANIFEST_SHA256.json'
REQUIRED = frozenset(f'{PREFIX}/{name}.md' for name in (
    'GEN1_CONTRACT', 'PRODUCT_AND_CAPABILITY_CONTRACT', 'PHYSICS_SPEC',
    'NUMERICAL_METHOD_SPEC', 'VALIDATION_SPEC', 'SCIENTIFIC_DECISIONS',
    'BASELINE_DECISION_REGISTER', 'BASELINE_TRACEABILITY_MATRIX',
    'VERIFICATION_EXECUTION_MATRIX', 'LEGACY_DISPOSITION',
))
REQUIRED |= frozenset(f'{PREFIX}/{name}.md' for name in ('NUMERICAL_KERNEL_NORMATIVE_ANNEX','PHYSICS_RESTORATION_ANNEX','LOSS_CHARACTERIZATION_NORMATIVE_ANNEX','STAGE_EVENT_RESTORATION_ANNEX','VALIDATION_FIXTURE_RESTORATION','EXPERIMENTAL_DATA_CONTRACT','NORMATIVE_CONSOLIDATION_RECORD'))
REQUIRED |= frozenset(f'{PREFIX}/{name}.md' for name in ('BOUNDARY_CONTRACT', 'TIME_EVENT_PERIODICITY_CONTRACT', 'EXECUTABLE_VALIDATION_CATALOGUE', 'REFERENCE_EXECUTION_CONTRACT', 'BCR-C1R2-H01-BOUNDARY', 'BCR-C1R2-H02-TIME-PERIODICITY', 'BCR-C1R2-H03-VALIDATION-FIXTURES'))
REQUIRED_DATA = frozenset(f'{PREFIX}/{name}' for name in ('EXECUTABLE_VALIDATION_FIXTURES.json', 'VALIDATION_CONTRACT_COVERAGE.json', 'NORMATIVE_ID_INDEX.json', 'datasets/thermo_species.json', 'datasets/thermo_transport.yaml'))
VERSION = 'C1.0-R2'
STATUS = 'SCIENTIFIC_IMPLEMENTATION_BASELINE_FROZEN'

class IntegrityError(ValueError):
    pass

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise IntegrityError(f'DUPLICATE_KEY: {key}')
        result[key] = value
    return result

def check(root: Path = ROOT) -> dict:
    root = root.resolve()
    try:
        manifest = json.loads((root / MANIFEST).read_text(encoding='utf-8'), object_pairs_hook=unique_object)
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrityError(f'MANIFEST_UNREADABLE: {exc}') from exc
    if manifest.get('version') != VERSION or manifest.get('status') != STATUS:
        raise IntegrityError('MANIFEST_VERSION_OR_STATUS')
    files = manifest.get('files')
    if not isinstance(files, dict) or not (REQUIRED | REQUIRED_DATA) <= files.keys():
        raise IntegrityError('REQUIRED_NORMATIVE_FILE_UNLISTED')
    actual = {p.relative_to(root).as_posix() for p in (root / PREFIX).rglob('*') if p.is_file()}
    unlisted = actual - files.keys() - {MANIFEST}
    if unlisted:
        raise IntegrityError(f'UNLISTED_NORMATIVE_FILES: {sorted(unlisted)}')
    for name, expected in files.items():
        rel = PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts or not name.startswith(PREFIX + '/') or name == MANIFEST:
            raise IntegrityError(f'UNSAFE_MANIFEST_PATH: {name}')
        p = root / name
        if p.is_symlink() or not p.resolve().is_relative_to(root / PREFIX):
            raise IntegrityError(f'UNSAFE_MANIFEST_PATH: {name}')
        if not isinstance(expected, str) or len(expected) != 64 or any(c not in '0123456789abcdef' for c in expected):
            raise IntegrityError(f'INVALID_HASH: {name}')
        if not p.is_file():
            raise IntegrityError(f'NORMATIVE_FILE_MISSING: {name}')
        actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        if actual_hash != expected:
            raise IntegrityError(f'HASH_MISMATCH: {name}: expected {expected}, got {actual_hash}')
        if name in REQUIRED and STATUS not in p.read_text(encoding='utf-8'):
            raise IntegrityError(f'NORMATIVE_STATUS_MISSING: {name}')
    if set(manifest.get('normative_files', [])) != REQUIRED:
        raise IntegrityError('NORMATIVE_ROSTER_MISMATCH')
    predecessor = root / manifest['predecessor_manifest_path']
    if hashlib.sha256(predecessor.read_bytes()).hexdigest() != manifest['predecessor_manifest_sha256']:
        raise IntegrityError('PREDECESSOR_MANIFEST_MISMATCH')
    previous = json.loads(predecessor.read_text())
    for name, digest in previous['files'].items():
        archived = predecessor.parent / Path(name).relative_to(PREFIX)
        if hashlib.sha256(archived.read_bytes()).hexdigest() != digest:
            raise IntegrityError('PREDECESSOR_BYTES_MISMATCH: ' + name)
    return {'check': 'manifest_integrity', 'result': 'PASS', 'version': VERSION, 'files': len(files)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(check(args.root), sort_keys=True))
    except IntegrityError as exc:
        parser.exit(1, f'{exc}\n')
