"""Bounded BCR integrity and controls; never whole S06 or GEN1 acceptance."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PREFIX = 'research/bcr_s06_material_resolution/'


def check():
    manifest = json.loads((ROOT / 'docs/science/C1.0/S06_MATERIAL_RESOLUTION_EVIDENCE_SHA256.json').read_text(encoding='utf-8'))
    assert manifest['classification'] == 'BOUNDED_REVIEWED_BCR_EVIDENCE_NOT_S06_ACCEPTANCE'
    for name, expected in manifest['files'].items():
        rel = PurePosixPath(name)
        assert name.startswith(PREFIX) and rel.as_posix() == name
        assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in name and ':' not in name
        path = ROOT / name
        assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(HERE)
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    return len(manifest['files'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--controls', action='store_true')
    args = parser.parse_args()
    count = check()
    if args.controls:
        # Separate processes retain each frozen research module's import identity.
        tests = [
            'material/test_prototype.py', 'local_material/test_local.py',
            'local_material/test_hybrid.py', 'local_material/test_hybrid_flux_b.py',
            'local_material/test_fast_overlap.py', 'local_material/test_fast_hybrid.py',
            'regional_geometry/test_geometry.py', 'area_hybrid/test_area.py',
            'area_hybrid/test_advisor.py',
        ]
        for name in tests:
            subprocess.run([sys.executable, '-m', 'pytest', str(HERE / name), '-q'], cwd=ROOT, check=True)
        subprocess.run([sys.executable, str(HERE / 'acoustic/kernel_review/check_portable.py')], cwd=ROOT, check=True)
    print(json.dumps({'result': 'BOUNDED_BCR_CHECKS_PASS' if args.controls else 'BCR_EVIDENCE_HASHES_PASS',
                      'files': count, 'controls_executed': args.controls,
                      'scientific_scope_acceptance': 'NOT_ASSERTED',
                      'omitted_step_streams_reaudited': False}))


if __name__ == '__main__':
    main()
