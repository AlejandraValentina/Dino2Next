from pathlib import Path

import pytest

from dino2next.thermo import (
    ThermoDataset, ThermoModel, DERIVED_SHA256, RAW_SHA256,
    TRANSPORT_SHA256, GENERATOR_SHA256,
)


@pytest.fixture(scope="session")
def model():
    root = Path(__file__).resolve().parents[3]
    base = root / "docs/science/C1.0/datasets"
    return ThermoModel(ThermoDataset.from_files(
        base / "thermo_runtime_continuous_v1.json", base / "thermo_species.json",
        base / "thermo_transport.yaml", root / "research/bcr_s03_nasa_inversion/generate.py",
        expected_sha256=DERIVED_SHA256, expected_raw_sha256=RAW_SHA256,
        expected_transport_sha256=TRANSPORT_SHA256, expected_generator_sha256=GENERATOR_SHA256))
