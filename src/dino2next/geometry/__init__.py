"""PHY-001 measured geometry and TS-005 event values, with no state transitions."""

from dataclasses import dataclass
from collections.abc import Mapping
from math import cos, sin, sqrt, pi, isfinite, floor
from sys import float_info

from dino2next.units import ValueContractError

TAU = 2 * pi
_ORDER = {"OPENING": 1, "CLOSING": 1, "OPENING_KNOT": 1, "OPENING_EXTREMUM": 1,
          "TRANSFER_OPENING": 2, "EXHAUST_CLOSURE": 2, "SOC_MERGE": 2,
          "SOC": 3, "BURN_END": 3, "CYCLE_BOUNDARY": 4}


def fail(code, path, message):
    raise ValueContractError(code, path, message, component="geometry")


def finite(value, path, code="GEOMETRY_INVALID"):
    if type(value) not in (int, float):
        fail(code, path, "Expected finite SI number")
    try:
        result = float(value)
    except OverflowError:
        fail(code, path, "Number exceeds float64")
    if not isfinite(result):
        fail(code, path, "Expected finite SI number")
    return result


@dataclass(frozen=True, slots=True)
class VolumeGeometry:
    Vc: float
    Vcc: float
    dVc_dtheta: float
    dVcc_dtheta: float

    def __post_init__(self):
        for name in ("Vc", "Vcc", "dVc_dtheta", "dVcc_dtheta"):
            value = finite(getattr(self, name), "/" + name, "VOLUME_NONPOSITIVE")
            if name in ("Vc", "Vcc") and value <= 0:
                fail("VOLUME_NONPOSITIVE", "/" + name, "Volume must be positive")


@dataclass(frozen=True, slots=True)
class CrankGeometry:
    bore: float
    stroke: float
    rod: float
    clearance_volume: float
    crankcase_tdc_volume: float

    def __post_init__(self):
        for name in ("bore", "stroke", "rod", "clearance_volume", "crankcase_tdc_volume"):
            value = finite(getattr(self, name), "/" + name)
            if value <= 0:
                fail("VOLUME_NONPOSITIVE" if "volume" in name else "GEOMETRY_INVALID",
                     "/" + name, "Measured dimension must be positive")
            object.__setattr__(self, name, value)
        if self.rod <= self.stroke / 2:
            fail("GEOMETRY_INVALID", "/rod", "Rod must exceed crank radius")
        swept = self.piston_area * self.stroke
        if not isfinite(swept) or self.crankcase_tdc_volume - swept <= 0:
            fail("VOLUME_NONPOSITIVE", "/crankcase_tdc_volume", "Crankcase must remain positive at BDC")
        if swept <= 0 or not isfinite(self.clearance_volume + swept):
            fail("GEOMETRY_INVALID", "", "Geometry is not representable in float64")

    @property
    def piston_area(self):
        return pi * (self.bore / 2) * (self.bore / 2)

    def volumes(self, theta) -> VolumeGeometry:
        theta = finite(theta, "/theta")
        r, rod = self.stroke / 2, self.rod
        s, c = sin(theta), cos(theta)
        # Rationalized l-sqrt(l²-r²sin²) avoids near-TDC cancellation.
        ratio = r / rod
        root_ratio = sqrt(((rod - r) / rod) * (1 + ratio) + (ratio * c) ** 2)
        displacement = r * (1 - c) + (r * s) * (ratio * s) / (1 + root_ratio)
        derivative = r * s + r * ratio * s * c / root_ratio
        change = self.piston_area * displacement
        rate = self.piston_area * derivative
        return VolumeGeometry(self.clearance_volume + change,
                              self.crankcase_tdc_volume - change, rate, -rate)


@dataclass(frozen=True, slots=True)
class PassageSamples:
    """Physical axial samples, one persistent passage; count is separate provenance."""
    component_id: str
    positions: tuple[float, ...]
    areas: tuple[float, ...]
    perimeters: tuple[float, ...]
    count: int = 1
    area_basis: str = "PER_PASSAGE"

    def __post_init__(self):
        if not isinstance(self.component_id, str) or not self.component_id:
            fail("GEOMETRY_INVALID", "/component_id", "Component identity is required")
        if type(self.count) is not int or self.count < 1:
            fail("GEOMETRY_INVALID", "/count", "Count must be a positive integer")
        if self.area_basis not in ("PER_PASSAGE", "AGGREGATE"):
            fail("AREA_DOMAIN_ERROR", "/area_basis", "Area basis must be explicit")
        for name in ("positions", "areas", "perimeters"):
            raw = getattr(self, name)
            if not isinstance(raw, (list, tuple)):
                fail("GEOMETRY_INVALID", "/" + name, "Expected measured sample array")
            values = tuple(finite(v, f"/{name}/{i}", "AREA_DOMAIN_ERROR") for i, v in enumerate(raw))
            object.__setattr__(self, name, values)
        if len(self.positions) < 2 or len(self.areas) != len(self.positions) or len(self.perimeters) != len(self.positions):
            fail("AREA_DOMAIN_ERROR", "", "At least two aligned samples are required")
        if any(b <= a for a, b in zip(self.positions, self.positions[1:])):
            fail("AREA_DOMAIN_ERROR", "/positions", "Positions must be strictly increasing")
        if any(v <= 0 for v in self.areas + self.perimeters):
            fail("AREA_DOMAIN_ERROR", "", "Persistent passage area and perimeter must be positive")
        if self.area_basis == "PER_PASSAGE":
            try:
                representable = all(isfinite(v * self.count) for v in self.areas)
            except OverflowError:
                representable = False
            if not representable:
                fail("AREA_DOMAIN_ERROR", "/count", "Aggregate area is not representable")

    @property
    def aggregate_areas(self):
        return tuple(v * self.count for v in self.areas) if self.area_basis == "PER_PASSAGE" else self.areas


@dataclass(frozen=True, slots=True)
class EventSpec:
    theta: float
    kind: str
    component_id: str

    def __post_init__(self):
        angle = finite(self.theta, "/theta")
        if not 0 <= angle < TAU:
            fail("GEOMETRY_INVALID", "/theta", "Configure cycle phase in [0, 2pi); no silent wrapping")
        if not isinstance(self.kind, str) or self.kind not in _ORDER:
            fail("GEOMETRY_INVALID", "/kind", "Unknown TS-005 event kind")
        if not isinstance(self.component_id, str) or not self.component_id:
            fail("GEOMETRY_INVALID", "/component_id", "Component identity is required")
        if self.kind == "CYCLE_BOUNDARY" and angle != 0:
            fail("GEOMETRY_INVALID", "/theta", "Cycle boundary is theta=0")
        object.__setattr__(self, "theta", angle)

    @property
    def event_id(self):
        # Length prefix makes arbitrary component names unambiguous.
        return f"{len(self.component_id)}:{self.component_id}:{self.kind}:{self.theta.hex()}"


@dataclass(frozen=True, slots=True)
class EventOccurrence:
    theta: float
    kind: str
    component_id: str
    cycle: int
    event_id: str
    occurrence_id: str
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self):
        finite(self.theta, "/theta")
        if type(self.cycle) is not int or not isinstance(self.kind, str) or self.kind not in _ORDER:
            fail("GEOMETRY_INVALID", "", "Invalid occurrence cycle or kind")
        for name in ("component_id", "event_id", "occurrence_id"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                fail("GEOMETRY_INVALID", "/" + name, "Occurrence identity required")
        if not isinstance(self.diagnostics, (list, tuple)) or any(type(d) is not str for d in self.diagnostics):
            fail("GEOMETRY_INVALID", "/diagnostics", "Expected diagnostic codes")
        object.__setattr__(self, "diagnostics", tuple(self.diagnostics))


@dataclass(frozen=True, slots=True)
class GeometryModel:
    crank: CrankGeometry
    passages: tuple[PassageSamples, ...] = ()
    event_specs: tuple[EventSpec, ...] = ()
    config_hash: str | None = None

    def __post_init__(self):
        if not isinstance(self.crank, CrankGeometry):
            fail("GEOMETRY_INVALID", "/crank", "Expected CrankGeometry")
        if self.config_hash is not None and (not isinstance(self.config_hash, str) or
                len(self.config_hash) != 64 or any(c not in "0123456789abcdef" for c in self.config_hash)):
            fail("GEOMETRY_INVALID", "/config_hash", "Expected SHA-256 content identity")
        for name, kind in (("passages", PassageSamples), ("event_specs", EventSpec)):
            raw = getattr(self, name)
            if not isinstance(raw, (list, tuple)) or any(not isinstance(v, kind) for v in raw):
                fail("GEOMETRY_INVALID", "/" + name, "Invalid value objects")
            object.__setattr__(self, name, tuple(raw))
        if len({p.component_id for p in self.passages}) != len(self.passages):
            fail("GEOMETRY_INVALID", "/passages", "Duplicate passage identity")
        if len({e.event_id for e in self.event_specs}) != len(self.event_specs):
            fail("GEOMETRY_INVALID", "/event_specs", "Duplicate event definition")
        for soc in (e for e in self.event_specs if e.kind == "SOC"):
            if any(e.kind == "BURN_END" and e.component_id == soc.component_id and e.theta == soc.theta
                   for e in self.event_specs):
                fail("GEOMETRY_INVALID", "/event_specs", "Burn end and SOC cannot coincide")

    @classmethod
    def from_snapshot(cls, snapshot):
        """Consume S01 provenance and explicitly dimensioned geometry payload."""
        # Import locally to keep numerical geometry evaluation independent of config I/O.
        from dino2next.config import ConfigSnapshot
        if not isinstance(snapshot, ConfigSnapshot):
            fail("GEOMETRY_INVALID", "", "Expected ConfigSnapshot")
        data = snapshot.payload
        def fields(obj, required, optional, path):
            if not isinstance(obj, Mapping) or set(obj) - required - optional or required - set(obj):
                fail("GEOMETRY_INVALID", path, "Missing or unknown geometry schema field")

        def quantity(obj, dimension, unit, path):
            fields(obj, {"value", "unit", "dimension"}, set(), path)
            if obj["dimension"] != dimension or obj["unit"] != unit:
                fail("GEOMETRY_INVALID", path, "SI dimension/unit mismatch")
            return finite(obj["value"], path + "/value")

        fields(data, {"crank"}, {"passages", "events"}, "/payload")
        names = ("bore", "stroke", "rod", "clearance_volume", "crankcase_tdc_volume")
        fields(data["crank"], set(names), set(), "/payload/crank")
        crank = CrankGeometry(**{
            name: quantity(data["crank"][name], "volume" if "volume" in name else "length",
                           "m3" if "volume" in name else "m", "/payload/crank/" + name)
            for name in names})
        passages, events = [], []
        for collection in ("passages", "events"):
            if not isinstance(data.get(collection, ()), (list, tuple)):
                fail("GEOMETRY_INVALID", "/payload/" + collection, "Expected array")
        for i, item in enumerate(data.get("passages", ())):
            path = f"/payload/passages/{i}"
            fields(item, {"component_id", "positions", "areas", "perimeters", "count", "area_basis"}, set(), path)
            arrays = {}
            for name, dimension, unit in (("positions", "length", "m"), ("areas", "area", "m2"),
                                          ("perimeters", "length", "m")):
                if not isinstance(item[name], (list, tuple)):
                    fail("GEOMETRY_INVALID", path + "/" + name, "Expected dimensioned sample array")
                arrays[name] = tuple(quantity(q, dimension, unit, f"{path}/{name}/{j}")
                                     for j, q in enumerate(item[name]))
            passages.append(PassageSamples(item["component_id"], **arrays,
                                            count=item["count"], area_basis=item["area_basis"]))
        for i, item in enumerate(data.get("events", ())):
            path = f"/payload/events/{i}"
            fields(item, {"theta", "kind", "component_id"}, set(), path)
            events.append(EventSpec(quantity(item["theta"], "angle", "rad", path + "/theta"),
                                    item["kind"], item["component_id"]))
        return cls(crank, tuple(passages), tuple(events), snapshot.sha256)

    def volumes(self, theta) -> VolumeGeometry:
        return self.crank.volumes(theta)

    def passage_geometry(self) -> tuple[PassageSamples, ...]:
        return self.passages

    def events_between(self, start, end) -> list[EventOccurrence]:
        start, end = finite(start, "/start"), finite(end, "/end")
        if end < start:
            fail("GEOMETRY_INVALID", "", "Event interval must be forward")
        events = []
        for spec in self.event_specs:
            # Candidate padding guards quotient rounding; exact membership is final.
            for cycle in range(floor((start - spec.theta) / TAU) - 1,
                               floor((end - spec.theta) / TAU) + 2):
                angle = cycle * TAU + spec.theta
                if start < angle <= end:
                    events.append((angle, _ORDER[spec.kind], spec.event_id, cycle, spec))
        events.sort(key=lambda row: row[:3])
        result = []
        for i, (angle, _, event_id, cycle, spec) in enumerate(events):
            tolerance = 32 * float_info.epsilon * max(1, abs(angle))
            near = False
            for direction in (-1, 1):
                j = i + direction
                while 0 <= j < len(events) and abs(events[j][0] - angle) <= tolerance:
                    if events[j][4].theta != spec.theta:
                        near = True
                        break
                    j += direction
            result.append(EventOccurrence(angle, spec.kind, spec.component_id, cycle, event_id,
                                          f"{cycle}:{event_id}",
                                          ("ROUNDING_COINCIDENCE",) if near else ()))
        return result
