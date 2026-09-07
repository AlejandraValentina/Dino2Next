from pathlib import Path
from hashlib import sha256
import pytest
from dino2next.thermo import ThermoDataset,ThermoModel


@pytest.fixture(scope='session')
def thermo():
    root=Path(__file__).resolve().parents[3]
    base=root/'docs/science/C1.0/datasets'
    paths=[base/'thermo_runtime_continuous_v1.json',base/'thermo_species.json',
           base/'thermo_transport.yaml',root/'research/bcr_s03_nasa_inversion/generate.py']
    digest=lambda p:sha256(p.read_bytes()).hexdigest()
    return ThermoModel(ThermoDataset.from_files(*paths,expected_sha256=digest(paths[0]),
        expected_raw_sha256=digest(paths[1]),expected_transport_sha256=digest(paths[2]),
        expected_generator_sha256=digest(paths[3])))
