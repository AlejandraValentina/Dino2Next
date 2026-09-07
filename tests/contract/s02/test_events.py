from dataclasses import FrozenInstanceError
from math import pi, nextafter

import pytest

from dino2next.geometry import CrankGeometry, EventSpec, EventOccurrence, GeometryModel
from dino2next.units import ValueContractError


def model(events):
    return GeometryModel(CrankGeometry(.05, .04, .08, 8e-6, 150e-6), event_specs=events)


def test_shared_boundary_once_negative_cycles_and_stable_ids():
    geometry = model([EventSpec(0, "CYCLE_BOUNDARY", "engine"), EventSpec(pi, "OPENING", "port")])
    whole = geometry.events_between(-2 * pi, 4 * pi)
    split = geometry.events_between(-2 * pi, pi) + geometry.events_between(pi, 4 * pi)
    assert whole == split
    assert len(whole) == 6
    assert len({event.occurrence_id for event in whole}) == 6
    assert [event.theta for event in whole] == [-pi, 0, pi, 2 * pi, 3 * pi, 4 * pi]
    assert geometry.events_between(pi, pi) == []
    with pytest.raises(FrozenInstanceError):
        whole[0].cycle = 7
    whole.clear()
    assert len(geometry.events_between(-2 * pi, 4 * pi)) == 6


def test_ts005_order_independent_of_configuration_order():
    events = [EventSpec(0, kind, "cylinder") for kind in
              ("CYCLE_BOUNDARY", "SOC", "EXHAUST_CLOSURE", "CLOSING")]
    first = model(events).events_between(-.1, 0)
    second = model(list(reversed(events))).events_between(-.1, 0)
    assert first == second
    assert [e.kind for e in first] == ["CLOSING", "EXHAUST_CLOSURE", "SOC", "CYCLE_BOUNDARY"]


def test_near_events_are_diagnosed_not_merged():
    geometry = model([EventSpec(1, "OPENING", "a"), EventSpec(1, "CLOSING", "c"),
                      EventSpec(nextafter(1, 2), "OPENING", "b")])
    events = geometry.events_between(0, 2)
    assert len(events) == 3
    assert events[0].theta != events[2].theta
    assert all(e.diagnostics == ("ROUNDING_COINCIDENCE",) for e in events)


@pytest.mark.parametrize("events", [
    [EventSpec(1, "OPENING", "a"), EventSpec(1, "OPENING", "a")],
    [EventSpec(1, "SOC", "burn"), EventSpec(1, "BURN_END", "burn")],
])
def test_ambiguous_definitions_rejected(events):
    with pytest.raises(ValueContractError) as error:
        model(events)
    assert error.value.code == "GEOMETRY_INVALID"


@pytest.mark.parametrize("theta,kind", [(-1, "OPENING"), (2 * pi, "OPENING"), (1, "CYCLE_BOUNDARY"),
                                       (float("nan"), "OPENING"), (0, "UNKNOWN")])
def test_invalid_event_spec(theta, kind):
    with pytest.raises(ValueContractError) as error:
        EventSpec(theta, kind, "x")
    assert error.value.code == "GEOMETRY_INVALID"


def test_enumeration_does_not_mutate_geometry_or_perform_transitions():
    geometry = model([EventSpec(1, "TRANSFER_OPENING", "t"), EventSpec(2, "SOC", "c")])
    before = geometry.volumes(.5)
    geometry.events_between(0, 100)
    assert geometry.volumes(.5) == before
    with pytest.raises(ValueContractError):
        geometry.events_between(2, 1)


def test_direct_occurrence_detaches_diagnostics():
    diagnostics = ["ROUNDING_COINCIDENCE"]
    event = EventOccurrence(1, "OPENING", "port", 0, "id", "0:id", diagnostics)
    diagnostics.clear()
    assert event.diagnostics == ("ROUNDING_COINCIDENCE",)
