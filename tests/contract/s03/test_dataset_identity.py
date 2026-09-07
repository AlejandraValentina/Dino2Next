from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from pathlib import Path

import pytest

from dino2next.config import freeze_config
from dino2next.thermo import (
    ThermoDataset, ThermoModel, DERIVED_SHA256, RAW_SHA256,
    TRANSPORT_SHA256, GENERATOR_SHA256, SPECIES,
)
from dino2next.units import ValueContractError


@pytest.fixture
def dataset():
    root = Path(__file__).resolve().parents[3]
    base = root / "docs/science/C1.0/datasets"
    return ThermoDataset.from_files(
        base / "thermo_runtime_continuous_v1.json", base / "thermo_species.json",
        base / "thermo_transport.yaml", root / "research/bcr_s03_nasa_inversion/generate.py",
        expected_sha256=DERIVED_SHA256, expected_raw_sha256=RAW_SHA256,
        expected_transport_sha256=TRANSPORT_SHA256, expected_generator_sha256=GENERATOR_SHA256)


def test_identity_and_frozen_storage(dataset):
    assert dataset.sha256 == DERIVED_SHA256
    assert dataset.raw_sha256 == RAW_SHA256
    assert dataset.sha256 != dataset.raw_sha256
    assert tuple(row.name for row in dataset.species) == SPECIES
    assert dataset.name == "DINO2NEXT_NASA5_CONTINUOUS"
    assert dataset.version == "1.0.0"
    with pytest.raises(FrozenInstanceError):
        dataset.species = ()
    with pytest.raises(FrozenInstanceError):
        dataset.species[0].high = ()


@pytest.mark.parametrize("field", ["derived_bytes", "raw_bytes", "transport_bytes", "generator_bytes"])
def test_changed_original_bytes_rejected(dataset, field):
    with pytest.raises(ValueContractError) as exc:
        replace(dataset, **{field: getattr(dataset, field) + b" "})
    assert exc.value.code == "DATASET_HASH_MISMATCH"


@pytest.mark.parametrize("field", ["expected_sha256", "expected_raw_sha256", "expected_transport_sha256", "expected_generator_sha256"])
def test_expected_hash_required_and_verified(dataset, field):
    with pytest.raises(ValueContractError) as exc:
        replace(dataset, **{field: "0" * 64})
    assert exc.value.code == "DATASET_HASH_MISMATCH"


def test_consistent_but_unapproved_alternative_rejected(dataset):
    altered = dataset.derived_bytes + b" "
    with pytest.raises(ValueContractError) as exc:
        replace(dataset, derived_bytes=altered, expected_sha256=sha256(altered).hexdigest())
    assert exc.value.code == "DATASET_HASH_MISMATCH"


def test_snapshot_binding(dataset):
    refs = [{"id": name, "sha256": digest, "media_type": "application/octet-stream"}
            for name, digest in zip(("runtime", "raw", "transport", "generator"),
                                    (DERIVED_SHA256, RAW_SHA256, TRANSPORT_SHA256, GENERATOR_SHA256))]
    snapshot = freeze_config({"schema_version": "1.0", "payload": {}, "resource_refs": refs})
    model = ThermoModel(dataset, snapshot)
    assert model.config_snapshot.sha256 == snapshot.sha256
    assert model.evaluate(700, 1e5, [0, 1, 0, 0, 0]).dataset_sha256 == DERIVED_SHA256
    for i in range(4):
        incomplete = freeze_config({"schema_version": "1.0", "payload": {}, "resource_refs": refs[:i] + refs[i + 1:]})
        with pytest.raises(ValueContractError) as exc:
            ThermoModel(dataset, incomplete)
        assert exc.value.code == "DATASET_HASH_MISMATCH"


def test_mutable_bytes_rejected(dataset):
    with pytest.raises(ValueContractError) as exc:
        replace(dataset, raw_bytes=bytearray(dataset.raw_bytes))
    assert exc.value.code == "DATASET_HASH_MISMATCH"


def test_missing_file_is_not_verified(tmp_path):
    with pytest.raises(ValueContractError) as exc:
        ThermoDataset.from_files(*(tmp_path / "absent",) * 4,
                                expected_sha256=DERIVED_SHA256, expected_raw_sha256=RAW_SHA256,
                                expected_transport_sha256=TRANSPORT_SHA256, expected_generator_sha256=GENERATOR_SHA256)
    assert exc.value.code == "DATASET_HASH_MISMATCH"


def test_direct_public_values_detach_mutable_inputs(dataset):
    model = ThermoModel(dataset)
    props = model.species_properties(700)
    mutable_cp = list(props.cp)
    clone = replace(props, cp=mutable_cp, names=list(props.names))
    mutable_cp[0] = 0
    assert clone.cp == props.cp
    state = model.evaluate(700, 1e5, [0, 1, 0, 0, 0])
    mutable_y = list(state.Y)
    clone_state = replace(state, Y=mutable_y)
    mutable_y[1] = 0
    assert clone_state.Y == state.Y
    recovered = model.invert_energy(state.rho, state.e, state.Y)
    bracket = list(recovered.diagnostic.temperature_bracket)
    diagnostic = replace(recovered.diagnostic, temperature_bracket=bracket)
    bracket[0] = 0
    assert diagnostic.temperature_bracket == recovered.diagnostic.temperature_bracket
    mapping = recovered.to_mapping()
    assert mapping["schema_version"] == "1.0"
    mapping["Y"][1] = 0
    assert recovered.Y[1] == 1
    assert dataset.to_mapping()["schema_version"] == "1.0"


def test_invalid_direct_public_values_fail(dataset):
    model = ThermoModel(dataset)
    props = model.species_properties(700)
    for kwargs in ({"cp": [1]}, {"names": ["other"] * 5}, {"cv": [0] * 5}):
        with pytest.raises(ValueContractError):
            replace(props, **kwargs)
    state = model.evaluate(700, 1e5, [0, 1, 0, 0, 0])
    for kwargs in ({"T": 299}, {"rho": 0}, {"Y": [1, 1, 0, 0, 0]},
                   {"diagnostic": {}}, {"dataset_sha256": RAW_SHA256}):
        with pytest.raises(ValueContractError):
            replace(state, **kwargs)
