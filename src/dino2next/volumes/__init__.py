"""PHY-003 single-zone extensive balances and shared signed stage ledgers."""

from dataclasses import asdict, dataclass
from math import fsum, isfinite
from sys import float_info

from dino2next.geometry import GeometryModel
from dino2next.thermo import SPECIES, ThermoModel, ThermoState
from dino2next.units import ValueContractError

TRACERS = ("F0", "F1", "R", "X")
ROUND_OFF = 256 * float_info.epsilon


def fail(code, path, message, **metadata):
    raise ValueContractError(code, path, message, component="volumes", metadata=metadata)


def number(value, path, code="INVENTORY_INADMISSIBLE"):
    if type(value) not in (int, float):
        fail(code, path, "Expected finite SI scalar")
    try:
        value = float(value)
    except OverflowError:
        fail(code, path, "Scalar exceeds binary64")
    if not isfinite(value):
        fail(code, path, "Expected finite SI scalar")
    return value


def vector(values, length, path, *, signed=False, code="INVENTORY_INADMISSIBLE"):
    if not isinstance(values, (tuple, list)) or len(values) != length:
        fail(code, path, f"Expected {length} components")
    result = tuple(number(v, f"{path}/{i}", code) for i, v in enumerate(values))
    if not signed and any(v < 0 for v in result):
        fail(code, path, "Negative constituent inventory")
    return result


def identity(value, path, code="TRANSFER_LEDGER_MISMATCH"):
    if type(value) is not str or not value.strip():
        fail(code, path, "Required identity is missing")
    return value


def total(values, path):
    try:
        return number(fsum(values), path)
    except OverflowError:
        fail("INVENTORY_INADMISSIBLE", path, "Inventory sum exceeds binary64")


def ordering(obj):
    for key, expected in (("species_order", SPECIES), ("tracer_order", TRACERS)):
        value = getattr(obj, key)
        if not isinstance(value, (tuple, list)) or tuple(value) != expected:
            fail("TRANSFER_LEDGER_MISMATCH", "/" + key, "Unexpected constituent ordering")
        object.__setattr__(obj, key, tuple(value))


class _JSONValue:
    __slots__ = ()

    def to_mapping(self):
        import json
        return {"schema_version": "1.0", **json.loads(json.dumps(asdict(self), allow_nan=False))}


@dataclass(frozen=True, slots=True)
class VolumeInventory(_JSONValue):
    species_mass: tuple[float, ...]
    internal_energy: float
    tracer_mass: tuple[float, ...]
    species_order: tuple[str, ...] = SPECIES
    tracer_order: tuple[str, ...] = TRACERS

    def __post_init__(self):
        ordering(self)
        object.__setattr__(self, "species_mass", vector(self.species_mass, 5, "/species_mass"))
        object.__setattr__(self, "tracer_mass", vector(self.tracer_mass, 4, "/tracer_mass"))
        object.__setattr__(self, "internal_energy", number(self.internal_energy, "/internal_energy"))
        mass, origin = self.mass, total(self.tracer_mass, "/tracer_mass")
        if mass <= 0:
            fail("INVENTORY_INADMISSIBLE", "/species_mass", "Single-zone state requires positive mass")
        if abs(origin - mass) > ROUND_OFF * max(origin, mass):
            fail("INVENTORY_INADMISSIBLE", "/tracer_mass", "Origin and chemical masses differ",
                 chemical_mass=mass, tracer_mass=origin)

    @property
    def mass(self):
        return total(self.species_mass, "/species_mass")


@dataclass(frozen=True, slots=True)
class InventoryIncrement(_JSONValue):
    """Signed extensive change, kg/J; positive into the named inventory."""
    species_mass: tuple[float, ...]
    internal_energy: float
    tracer_mass: tuple[float, ...]
    species_order: tuple[str, ...] = SPECIES
    tracer_order: tuple[str, ...] = TRACERS
    mass_unit: str = "kg"
    energy_unit: str = "J"
    sign_convention: str = "POSITIVE_INTO_VOLUME"

    def __post_init__(self):
        ordering(self)
        object.__setattr__(self, "species_mass", vector(self.species_mass, 5, "/species_mass", signed=True))
        object.__setattr__(self, "tracer_mass", vector(self.tracer_mass, 4, "/tracer_mass", signed=True))
        object.__setattr__(self, "internal_energy", number(self.internal_energy, "/internal_energy"))
        if (self.mass_unit, self.energy_unit, self.sign_convention) != ("kg", "J", "POSITIVE_INTO_VOLUME"):
            fail("TRANSFER_LEDGER_MISMATCH", "/units", "Increment requires signed extensive SI units")

    def scaled(self, factor):
        factor = number(factor, "/factor")
        return InventoryIncrement(tuple(factor * x for x in self.species_mass),
                                  factor * self.internal_energy, tuple(factor * x for x in self.tracer_mass))


@dataclass(frozen=True, slots=True)
class InventoryRate(_JSONValue):
    species_mass: tuple[float, ...]
    internal_energy: float
    tracer_mass: tuple[float, ...]
    species_order: tuple[str, ...] = SPECIES
    tracer_order: tuple[str, ...] = TRACERS
    mass_unit: str = "kg/s"
    energy_unit: str = "W"
    sign_convention: str = "POSITIVE_INTO_VOLUME"
    transfer_energy: float = 0.0
    heat: float = 0.0
    pressure_work: float = 0.0

    def __post_init__(self):
        ordering(self)
        object.__setattr__(self, "species_mass", vector(self.species_mass, 5, "/species_mass", signed=True))
        object.__setattr__(self, "tracer_mass", vector(self.tracer_mass, 4, "/tracer_mass", signed=True))
        for key in ("internal_energy", "transfer_energy", "heat", "pressure_work"):
            object.__setattr__(self, key, number(getattr(self, key), "/" + key))
        if (self.mass_unit, self.energy_unit, self.sign_convention) != ("kg/s", "W", "POSITIVE_INTO_VOLUME"):
            fail("TRANSFER_LEDGER_MISMATCH", "/units", "Rate requires signed rate SI units")
        if self.internal_energy != total((self.transfer_energy, self.heat, -self.pressure_work), "/internal_energy"):
            fail("TRANSFER_LEDGER_MISMATCH", "/internal_energy", "Rate energy must match separate transfer/heat/work entries")

    def integrated(self, dt):
        dt = number(dt, "/dt")
        if dt <= 0:
            fail("INVENTORY_INADMISSIBLE", "/dt", "Integration interval must be positive")
        return InventoryIncrement(tuple(dt * x for x in self.species_mass),
                                  dt * self.internal_energy, tuple(dt * x for x in self.tracer_mass))


@dataclass(frozen=True, slots=True)
class StageVolume(_JSONValue):
    volume: float
    dV_dt: float
    time: float
    stage_id: str
    volume_id: str

    def __post_init__(self):
        identity(self.stage_id, "/stage_id")
        identity(self.volume_id, "/volume_id")
        for key in ("volume", "dV_dt", "time"):
            object.__setattr__(self, key, number(getattr(self, key), "/" + key, "VOLUME_NONPOSITIVE"))
        if self.volume <= 0:
            fail("VOLUME_NONPOSITIVE", "/volume", "Physical volume must be positive")

    @classmethod
    def from_geometry(cls, geometry, theta, omega, *, time, stage_id, volume_id, kind):
        if not isinstance(geometry, GeometryModel) or kind not in ("cylinder", "crankcase"):
            fail("VOLUME_NONPOSITIVE", "/geometry", "Expected GeometryModel and selected volume kind")
        values = geometry.volumes(theta)
        omega = number(omega, "/omega", "VOLUME_NONPOSITIVE")
        if kind == "cylinder":
            return cls(values.Vc, values.dVc_dtheta * omega, time, stage_id, volume_id)
        return cls(values.Vcc, values.dVcc_dtheta * omega, time, stage_id, volume_id)


@dataclass(frozen=True, slots=True)
class StagePressure(_JSONValue):
    pressure: float
    time: float
    stage_id: str
    volume_id: str

    def __post_init__(self):
        identity(self.stage_id, "/stage_id")
        identity(self.volume_id, "/volume_id")
        object.__setattr__(self, "time", number(self.time, "/time"))
        object.__setattr__(self, "pressure", number(self.pressure, "/pressure"))
        if self.pressure <= 0:
            fail("INVENTORY_INADMISSIBLE", "/pressure", "Stage pressure must be positive")


@dataclass(frozen=True, slots=True)
class StageWork(_JSONValue):
    pressure: StagePressure
    geometry: StageVolume

    def __post_init__(self):
        if not isinstance(self.pressure, StagePressure) or not isinstance(self.geometry, StageVolume):
            fail("TRANSFER_LEDGER_MISMATCH", "/p_dV", "Expected stage pressure and geometry")
        if (self.pressure.time, self.pressure.stage_id, self.pressure.volume_id) != (
                self.geometry.time, self.geometry.stage_id, self.geometry.volume_id):
            fail("TRANSFER_LEDGER_MISMATCH", "/p_dV", "Pressure and volume rate are from different stages")
        number(self.value, "/p_dV")

    @property
    def value(self):
        """Positive pressure work out of the gas, W = p * dV/dt."""
        return self.pressure.pressure * self.geometry.dV_dt


@dataclass(frozen=True, slots=True)
class FractionRoundoff(_JSONValue):
    species_sum: float
    tracer_sum: float
    species_rescaled: bool
    tracers_rescaled: bool

    def __post_init__(self):
        for name in ("species_sum", "tracer_sum"):
            object.__setattr__(self, name, number(getattr(self, name), "/" + name))
        if type(self.species_rescaled) is not bool or type(self.tracers_rescaled) is not bool:
            fail("INVENTORY_INADMISSIBLE", "/roundoff", "Expected boolean correction records")


@dataclass(frozen=True, slots=True)
class VolumeState(_JSONValue):
    inventory: VolumeInventory
    geometry: StageVolume
    thermo: ThermoState
    tracer_fractions: tuple[float, ...]
    roundoff: FractionRoundoff

    def __post_init__(self):
        if not isinstance(self.inventory, VolumeInventory) or not isinstance(self.geometry, StageVolume):
            fail("INVENTORY_INADMISSIBLE", "/state", "Expected immutable inventory and stage geometry")
        if not isinstance(self.thermo, ThermoState) or not isinstance(self.roundoff, FractionRoundoff):
            fail("INVENTORY_INADMISSIBLE", "/state", "Expected NASA state and roundoff record")
        object.__setattr__(self, "tracer_fractions", vector(self.tracer_fractions, 4, "/tracer_fractions"))
        Y, sy, cy = _fractions(self.inventory.species_mass, self.inventory.mass)
        tags, st, ct = _fractions(self.inventory.tracer_mass, self.inventory.mass)
        diagnostic = self.thermo.diagnostic
        if (self.thermo.rho != self.inventory.mass / self.geometry.volume or
                self.thermo.Y != Y or self.tracer_fractions != tags or
                self.roundoff != FractionRoundoff(sy, st, cy, ct) or
                diagnostic is None or diagnostic.kind != "energy" or
                diagnostic.target != self.inventory.internal_energy / self.inventory.mass):
            fail("INVENTORY_INADMISSIBLE", "/state", "Primitive state does not bind this extensive inventory")


def _fractions(masses, mass):
    fractions = tuple(value / mass for value in masses)
    summed = total(fractions, "/fractions")
    if abs(summed - 1) > ROUND_OFF:
        fail("INVENTORY_INADMISSIBLE", "/fractions", "Derived fractions exceed TS-004 summation roundoff")
    corrected = summed != 1.0
    return (tuple(value / summed for value in fractions) if corrected else fractions), summed, corrected


def state(inventory, volume, thermo):
    if not isinstance(inventory, VolumeInventory) or not isinstance(volume, StageVolume):
        fail("INVENTORY_INADMISSIBLE", "/state", "Expected inventory and stage volume")
    if not isinstance(thermo, ThermoModel):
        fail("INVENTORY_INADMISSIBLE", "/thermo", "Accepted NASA ThermoModel required")
    Y, sy, cy = _fractions(inventory.species_mass, inventory.mass)
    tags, st, ct = _fractions(inventory.tracer_mass, inventory.mass)
    try:
        primitive = thermo.invert_energy(inventory.mass / volume.volume,
                                        inventory.internal_energy / inventory.mass, Y)
    except ValueContractError as exc:
        fail("INVENTORY_INADMISSIBLE", "/thermo" + exc.path, "Extensive state cannot recover admissible NASA state",
             cause_code=exc.code, cause_message=exc.message)
    return VolumeState(inventory, volume, primitive, tags, FractionRoundoff(sy, st, cy, ct))


def pressure_work(value):
    if not isinstance(value, VolumeState):
        fail("TRANSFER_LEDGER_MISMATCH", "/state", "Pressure work requires a VolumeState")
    geometry = value.geometry
    return StageWork(StagePressure(value.thermo.p, geometry.time, geometry.stage_id,
                                   geometry.volume_id), geometry)


@dataclass(frozen=True, slots=True)
class TransferLedger(_JSONValue):
    id: str
    source_id: str
    receiver_id: str
    endpoint_id: str
    stage_id: str
    time_interval: tuple[float, float]
    stage_time: float
    increment: InventoryIncrement

    def __post_init__(self):
        for key in ("id", "source_id", "receiver_id", "endpoint_id", "stage_id"):
            identity(getattr(self, key), "/" + key)
        if self.source_id == self.receiver_id or self.endpoint_id not in (self.source_id, self.receiver_id):
            fail("TRANSFER_LEDGER_MISMATCH", "/endpoint_id", "Distinct source and receiver endpoints required")
        interval = vector(self.time_interval, 2, "/time_interval", signed=True, code="TRANSFER_LEDGER_MISMATCH")
        time = number(self.stage_time, "/stage_time", "TRANSFER_LEDGER_MISMATCH")
        if interval[1] <= interval[0] or time not in interval or not isfinite(interval[1] - interval[0]):
            fail("TRANSFER_LEDGER_MISMATCH", "/time_interval", "Require positive interval and endpoint stage time")
        object.__setattr__(self, "time_interval", interval)
        object.__setattr__(self, "stage_time", time)
        if not isinstance(self.increment, InventoryIncrement):
            fail("TRANSFER_LEDGER_MISMATCH", "/increment", "Ledger requires extensive increment, not a rate")
        chemical = total(self.increment.species_mass, "/increment")
        tracers = total(self.increment.tracer_mass, "/increment")
        scale = total(tuple(abs(v) for v in self.increment.species_mass + self.increment.tracer_mass), "/increment")
        if abs(chemical - tracers) > ROUND_OFF * scale:
            fail("TRANSFER_LEDGER_MISMATCH", "/increment", "Transfer chemical and origin mass totals differ")


def pair_transfer(id, source_id, receiver_id, stage_id, time_interval, stage_time, to_receiver):
    if not isinstance(to_receiver, InventoryIncrement):
        fail("TRANSFER_LEDGER_MISMATCH", "/increment", "Shared transfer must be extensive")
    receiver = TransferLedger(id, source_id, receiver_id, receiver_id, stage_id,
                              time_interval, stage_time, to_receiver)
    source = TransferLedger(id, source_id, receiver_id, source_id, stage_id,
                            time_interval, stage_time, to_receiver.scaled(-1))
    return source, receiver


def validate_transfer_pairs(transfers):
    if not isinstance(transfers, (tuple, list)) or any(not isinstance(x, TransferLedger) for x in transfers):
        fail("TRANSFER_LEDGER_MISMATCH", "/transfers", "Expected paired TransferLedger records")
    groups = {}
    for record in transfers:
        groups.setdefault(record.id, []).append(record)
    for key, records in groups.items():
        if len(records) != 2:
            fail("TRANSFER_LEDGER_MISMATCH", "/transfers", "Each ID must have exactly two copies", transfer_id=key)
        a, b = records
        if (a.source_id, a.receiver_id, a.stage_id, a.time_interval, a.stage_time) != (
                b.source_id, b.receiver_id, b.stage_id, b.time_interval, b.stage_time) or a.endpoint_id == b.endpoint_id:
            fail("TRANSFER_LEDGER_MISMATCH", "/transfers", "Paired endpoint metadata differ", transfer_id=key)
        av = a.increment.species_mass + (a.increment.internal_energy,) + a.increment.tracer_mass
        bv = b.increment.species_mass + (b.increment.internal_energy,) + b.increment.tracer_mass
        if any(x != -y for x, y in zip(av, bv)):
            fail("TRANSFER_LEDGER_MISMATCH", "/transfers", "Shared transfer copies are not exact opposites", transfer_id=key)
    return tuple(transfers)


def balance_rates(transfers, heat, p_dV, *, volume_id):
    transfers = validate_transfer_pairs(transfers)
    heat = number(heat, "/heat")
    if not isinstance(p_dV, StageWork) or volume_id != p_dV.geometry.volume_id:
        fail("TRANSFER_LEDGER_MISMATCH", "/p_dV", "Work belongs to a different volume")
    stage = p_dV.geometry
    if len({record.time_interval for record in transfers}) > 1:
        fail("TRANSFER_LEDGER_MISMATCH", "/transfers", "Stage ledger intervals differ")
    selected = []
    for record in transfers:
        if record.stage_id != stage.stage_id or record.stage_time != stage.time:
            fail("TRANSFER_LEDGER_MISMATCH", "/transfers", "Transfer and source stages differ")
        if record.endpoint_id == volume_id:
            dt = record.time_interval[1] - record.time_interval[0]
            selected.append(InventoryRate(tuple(v / dt for v in record.increment.species_mass),
                                          record.increment.internal_energy / dt,
                                          tuple(v / dt for v in record.increment.tracer_mass),
                                          transfer_energy=record.increment.internal_energy / dt))
    species = tuple(total(tuple(r.species_mass[i] for r in selected), "/species_mass") for i in range(5))
    tracers = tuple(total(tuple(r.tracer_mass[i] for r in selected), "/tracer_mass") for i in range(4))
    transfer_energy = total(tuple(r.internal_energy for r in selected), "/transfer_energy")
    return InventoryRate(species, total((transfer_energy, heat, -p_dV.value), "/internal_energy"), tracers,
                         transfer_energy=transfer_energy, heat=heat, pressure_work=p_dV.value)


def apply_increment(inventory, increment):
    if not isinstance(inventory, VolumeInventory) or not isinstance(increment, InventoryIncrement):
        fail("INVENTORY_INADMISSIBLE", "/increment", "Expected inventory and extensive increment, not rate")
    return VolumeInventory(tuple(total((a, b), "/species_mass") for a, b in zip(inventory.species_mass, increment.species_mass)),
                           total((inventory.internal_energy, increment.internal_energy), "/internal_energy"),
                           tuple(total((a, b), "/tracer_mass") for a, b in zip(inventory.tracer_mass, increment.tracer_mass)))
