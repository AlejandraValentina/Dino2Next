from dataclasses import FrozenInstanceError, replace
import math

import pytest

from dino2next.units import ValueContractError
from dino2next.volumes import (
    InventoryIncrement, InventoryRate, StagePressure, StageVolume, StageWork,
    VolumeInventory, apply_increment, pair_transfer, validate_transfer_pairs, balance_rates,
)


def pair(**updates):
    kwargs = dict(id="face0", source_id="a", receiver_id="b", stage_id="s0",
                  time_interval=(0, .01), stage_time=0,
                  to_receiver=InventoryIncrement((0, .001, .003, 0, 0), -5, (.004, 0, 0, 0)))
    kwargs.update(updates)
    return pair_transfer(**kwargs)


def work(volume_id, *, stage_id="s0", time=0):
    return StageWork(StagePressure(1e5, time, stage_id, volume_id),
                     StageVolume(.001, 0, time, stage_id, volume_id))


def test_one_shared_extensive_transfer_produces_opposite_copies_and_rates():
    a, b = pair()
    assert a.increment.internal_energy == 5
    assert b.increment.internal_energy == -5
    assert validate_transfer_pairs([a, b]) == (a, b)
    ra = balance_rates((a, b), 0, work("a"), volume_id="a")
    rb = balance_rates((a, b), 0, work("b"), volume_id="b")
    assert ra.internal_energy == -rb.internal_energy == 500
    assert ra.species_mass == tuple(-x for x in rb.species_mass)
    assert ra.tracer_mass == tuple(-x for x in rb.tracer_mass)
    ia = VolumeInventory((0, .2, .3, 0, 0), -100, (.5, 0, 0, 0))
    ib = VolumeInventory((0, .1, .4, 0, 0), -200, (.5, 0, 0, 0))
    na, nb = apply_increment(ia, a.increment), apply_increment(ib, b.increment)
    assert math.fsum((na.internal_energy, nb.internal_energy)) == -300
    assert math.fsum((na.mass, nb.mass)) == 1


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "same_endpoint", "energy", "species", "stage", "interval", "time", "receiver"])
def test_pair_mismatch_never_accepted(mutation):
    a, b = pair()
    records = [a, b]
    if mutation == "missing":
        records = [a]
    elif mutation == "duplicate":
        records = [a, b, a]
    elif mutation == "same_endpoint":
        records = [a, a]
    elif mutation == "energy":
        records[1] = replace(b, increment=replace(b.increment, internal_energy=-4))
    elif mutation == "species":
        records[1] = replace(b, increment=replace(b.increment, species_mass=(.001, 0, .003, 0, 0)))
    elif mutation == "stage":
        records[1] = replace(b, stage_id="s1")
    elif mutation == "interval":
        records[1] = replace(b, time_interval=(0, .02))
    elif mutation == "time":
        records[1] = replace(b, stage_time=.01)
    elif mutation == "receiver":
        records[1] = replace(b, receiver_id="c", endpoint_id="c")
    with pytest.raises(ValueContractError) as exc:
        validate_transfer_pairs(records)
    assert exc.value.code == "TRANSFER_LEDGER_MISMATCH"


@pytest.mark.parametrize("changes", [
    {"stage_id": ""}, {"source_id": "b"}, {"time_interval": (0, 0)},
    {"time_interval": (1, 0)}, {"stage_time": .005},
    {"to_receiver": InventoryRate((0, 0, 0, 0, 0), 0, (0, 0, 0, 0))},
    {"to_receiver": InventoryIncrement((1, 0, 0, 0, 0), 0, (0, 0, 0, 0))},
])
def test_invalid_metadata_or_units(changes):
    with pytest.raises(ValueContractError) as exc:
        pair(**changes)
    assert exc.value.code == "TRANSFER_LEDGER_MISMATCH"


def test_different_interface_intervals_and_stale_sources_rejected():
    records = pair() + pair(id="face1", time_interval=(0, .02))
    with pytest.raises(ValueContractError):
        balance_rates(records, 0, work("b"), volume_id="b")
    with pytest.raises(ValueContractError):
        balance_rates(pair(), 0, work("b", stage_id="s1"), volume_id="b")
    with pytest.raises(ValueContractError):
        balance_rates(pair(), 0, work("b", time=.01), volume_id="b")
    with pytest.raises(ValueContractError):
        balance_rates(pair(), 0, work("a"), volume_id="b")


def test_units_ordering_and_nested_immutability():
    a, b = pair(time_interval=[0, .01])
    assert a.time_interval == (0, .01)
    with pytest.raises(FrozenInstanceError):
        a.increment.internal_energy = 0
    data = b.to_mapping()
    assert data["schema_version"] == "1.0"
    assert data["increment"]["species_order"] == ["C8H18,isooctane", "O2", "N2", "CO2", "H2O"]
    assert data["increment"]["tracer_order"] == ["F0", "F1", "R", "X"]
    data["increment"]["species_mass"][0] = 10
    assert b.increment.species_mass[0] == 0
    with pytest.raises(ValueContractError):
        replace(b.increment, mass_unit="kg/s")
    with pytest.raises(ValueContractError):
        replace(b.increment, species_order=["O2"] * 5)
    with pytest.raises(ValueContractError):
        replace(b.increment, tracer_order=["species"] * 4)


def test_stage_transfer_energy_is_total_enthalpy_signed_not_positive_only():
    incoming = InventoryIncrement((0, .001, 0, 0, 0), -500, (.001, 0, 0, 0))
    records = pair(to_receiver=incoming)
    receiver_rate = balance_rates(records, 10, work("b"), volume_id="b")
    assert receiver_rate.transfer_energy == -50000
    assert receiver_rate.heat == 10
    assert receiver_rate.internal_energy == -49990
