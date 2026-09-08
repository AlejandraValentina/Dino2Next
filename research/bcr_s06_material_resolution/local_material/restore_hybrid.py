"""Restore only hash-verified portable research evidence; no tests are run."""
from pathlib import Path
from hashlib import sha256
import json,zipfile

root=Path(__file__).resolve().parent
manifest=json.loads((root/'hybrid-data-manifest.json').read_text())
archive=root/'hybrid-data.zip'
assert sha256(archive.read_bytes()).hexdigest()==manifest['zip_sha256']
with zipfile.ZipFile(archive) as z:
    assert set(z.namelist())=={row['path'] for row in manifest['members']}
    for row in manifest['members']:
        target=(root/row['path']).resolve()
        assert root in target.parents, 'Archive member outside evidence directory'
        data=z.read(row['path'])
        assert len(data)==row['size'] and sha256(data).hexdigest()==row['sha256']
        if target.exists():
            assert target.is_file() and sha256(target.read_bytes()).hexdigest()==row['sha256'], 'Existing evidence differs; preserve it'
        else:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
print('Portable evidence restored/verified byte-exact; no numerical PASS asserted')
