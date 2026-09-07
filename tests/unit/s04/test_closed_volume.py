from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import math

import pytest

from dino2next.geometry import CrankGeometry, GeometryModel
from dino2next.thermo import ThermoDataset, ThermoModel, DERIVED_SHA256, RAW_SHA256, TRANSPORT_SHA256, GENERATOR_SHA256
from dino2next.units import ValueContractError
from dino2next.volumes import (
    VolumeInventory, InventoryIncrement, InventoryRate, StageVolume, StagePressure, StageWork,
    apply_increment, balance_rates, state, pressure_work,
)


@pytest.fixture(scope="module")
def thermo():
    root = Path(__file__).resolve().parents[3]
    data = root / "docs/science/C1.0/datasets"
    return ThermoModel(ThermoDataset.from_files(
        data / "thermo_runtime_continuous_v1.json", data / "thermo_species.json",
        data / "thermo_transport.yaml", root / "research/bcr_s03_nasa_inversion/generate.py",
        expected_sha256=DERIVED_SHA256, expected_raw_sha256=RAW_SHA256,
        expected_transport_sha256=TRANSPORT_SHA256, expected_generator_sha256=GENERATOR_SHA256))


@pytest.mark.parametrize("species", range(5))
@pytest.mark.parametrize("T", [350, 999.999999, 1000, 1000.000001, 1600])
def test_closed_inventory_recovers_nasa_without_overwriting_energy(thermo, species, T):
    Y = tuple(float(i == species) for i in range(5))
    primitive = thermo.evaluate(T, 1e5, Y)
    mass = .001
    inventory = VolumeInventory(tuple(y * mass for y in Y), primitive.e * mass, (0, 0, mass, 0))
    snapshot = inventory.to_mapping()
    geometry = StageVolume(mass / primitive.rho, 0, 0, "stage0", "cylinder")
    recovered = state(inventory, geometry, thermo)
    assert abs(recovered.thermo.T - T) <= 1e-8
    assert recovered.thermo.rho == inventory.mass / geometry.volume
    assert recovered.thermo.diagnostic.target == inventory.internal_energy / inventory.mass
    assert inventory.to_mapping() == snapshot
    if species in (3, 4) or (species == 0 and T == 350):
        assert inventory.internal_energy < 0
    rate = balance_rates((), 0, pressure_work(recovered), volume_id="cylinder")
    assert rate.internal_energy == 0
    assert apply_increment(inventory, rate.integrated(.01)) == inventory


def test_heat_and_work_separate_signs_and_extensive_update(thermo):
    initial = thermo.evaluate(700, 1e5, (0, 1, 0, 0, 0))
    inv = VolumeInventory((0, .001, 0, 0, 0), .001 * initial.e, (.001, 0, 0, 0))
    geometry = StageVolume(.001 / initial.rho, .0002, 0, "s0", "v")
    result = state(inv, geometry, thermo)
    work = pressure_work(result)
    rate = balance_rates((), 30, work, volume_id="v")
    assert rate.heat == 30
    assert rate.pressure_work == result.thermo.p * .0002
    assert rate.transfer_energy == 0
    assert rate.internal_energy == rate.heat - rate.pressure_work
    updated = apply_increment(inv, rate.integrated(.01))
    assert updated.internal_energy == pytest.approx(inv.internal_energy + .01 * rate.internal_energy)
    assert updated.species_mass == inv.species_mass
    assert updated.tracer_mass == inv.tracer_mass


def test_geometry_dependency_stage_displacement_and_crankcase_sign():
    model = GeometryModel(CrankGeometry(.052, .05, .101, 1.2e-5, 3e-4))
    common = {"time": .03, "stage_id": "s1", "volume_id": "volume"}
    cylinder = StageVolume.from_geometry(model, math.pi / 2, 100, kind="cylinder", **common)
    crankcase = StageVolume.from_geometry(model, math.pi / 2, 100, kind="crankcase", **common)
    exact = model.volumes(math.pi / 2)
    assert cylinder.volume == exact.Vc
    assert cylinder.dV_dt == exact.dVc_dtheta * 100
    assert crankcase.volume == exact.Vcc
    assert crankcase.dV_dt == -cylinder.dV_dt


@pytest.mark.parametrize("field,value", [("time", 1), ("stage_id", "old"), ("volume_id", "other")])
def test_pressure_work_rejects_stale_stage(field, value):
    geometry = StageVolume(.001, .0001, 0, "s0", "v")
    pressure = StagePressure(1e5, 0, "s0", "v")
    with pytest.raises(ValueContractError) as exc:
        StageWork(replace(pressure, **{field: value}), geometry)
    assert exc.value.code == "TRANSFER_LEDGER_MISMATCH"


@pytest.mark.parametrize("volume", [0, -1, float("nan"), float("inf"), True])
def test_nonpositive_or_invalid_volume(volume):
    with pytest.raises(ValueContractError) as exc:
        StageVolume(volume, 0, 0, "s", "v")
    assert exc.value.code == "VOLUME_NONPOSITIVE"


@pytest.mark.parametrize("masses,energy,tags", [
    ([0] * 5, 0, [0] * 4), ([-1e-30, 1, 0, 0, 0], 0, [1, 0, 0, 0]),
    ([1, 0, 0, 0, 0], float("nan"), [1, 0, 0, 0]),
    ([1, 0, 0, 0, 0], -100, [0, 0, 0, 0]),
    ([1, 0, 0, 0, 0], -100, [1, -1e-30, 0, 0]),
    ([1], 0, [1, 0, 0, 0]), ([1e308] * 5, 0, [1e308] * 4),
])
def test_inadmissible_inventory_is_not_repaired(masses, energy, tags):
    with pytest.raises(ValueContractError) as exc:
        VolumeInventory(masses, energy, tags)
    assert exc.value.code == "INVENTORY_INADMISSIBLE"


def test_out_of_nasa_domain_preserves_input_and_cause(thermo):
    inventory = VolumeInventory((.001, 0, 0, 0, 0), -1e20, (.001, 0, 0, 0))
    before = inventory.to_mapping()
    with pytest.raises(ValueContractError) as exc:
        state(inventory, StageVolume(.001, 0, 0, "s", "v"), thermo)
    assert exc.value.code == "INVENTORY_INADMISSIBLE"
    assert exc.value.metadata["cause_code"] == "EOS_OUT_OF_DOMAIN"
    assert inventory.to_mapping() == before


def test_fraction_roundoff_is_recorded_without_changing_mass(thermo):
    primitive = thermo.evaluate(700, 1e5, (0, 1, 0, 0, 0))
    tags = (math.nextafter(.001, math.inf), 0, 0, 0)
    inv = VolumeInventory((0, .001, 0, 0, 0), .001 * primitive.e, tags)
    result = state(inv, StageVolume(.001 / primitive.rho, 0, 0, "s", "v"), thermo)
    assert result.roundoff.tracers_rescaled
    assert result.tracer_fractions == (1, 0, 0, 0)
    assert inv.tracer_mass == tags


def test_values_detach_inputs_and_increment_never_mutates():
    masses, tags = [1, 0, 0, 0, 0], [1, 0, 0, 0]
    inv = VolumeInventory(masses, -100, tags)
    masses[0] = tags[0] = 0
    assert inv.mass == 1
    with pytest.raises(FrozenInstanceError):
        inv.internal_energy = 0
    output = inv.to_mapping()
    output["species_mass"][0] = 10
    assert inv.mass == 1
    rate = InventoryRate([0] * 5, 2, [0] * 4, heat=2)
    assert rate.mass_unit == "kg/s" and rate.energy_unit == "W"
    increment = rate.integrated(.5)
    assert increment.mass_unit == "kg" and increment.energy_unit == "J"
    assert apply_increment(inv, increment).internal_energy == -99
    assert inv.internal_energy == -100
    with pytest.raises(ValueContractError):
        apply_increment(inv, rate)
    with pytest.raises(ValueContractError):
        apply_increment(inv, InventoryIncrement((-2, 0, 0, 0, 0), 0, (-2, 0, 0, 0)))


def test_volume_state_cannot_relabel_another_inventory(thermo):
    p = thermo.evaluate(700, 1e5, (0, 1, 0, 0, 0))
    inv = VolumeInventory((0, .001, 0, 0, 0), .001 * p.e, (.001, 0, 0, 0))
    result = state(inv, StageVolume(.001 / p.rho, 0, 0, "s", "v"), thermo)
    with pytest.raises(ValueContractError):
        replace(result, inventory=replace(inv, internal_energy=inv.internal_energy + 1))
    with pytest.raises(ValueContractError):
        replace(result, tracer_fractions=[.5, .5, 0, 0])
