"""Explicit display-to-SI conversion; no physical-domain policy."""

from dataclasses import dataclass
from math import isfinite, pi
from types import MappingProxyType


class ValueContractError(ValueError):
    """Stable software diagnostic shared by the S01 value boundaries."""

    def __init__(self, code, path, message, *, component="units", metadata=None):
        super().__init__(message)
        self.code = code
        self.path = path
        self.message = message
        self.component = component
        self.metadata = MappingProxyType(dict(metadata or {}))


# dimension, SI multiplier, SI offset. Temperature is absolute, not a delta.
_UNITS = MappingProxyType({
    "m": ("length", 1.0, 0.0), "mm": ("length", 1e-3, 0.0),
    "m2": ("area", 1.0, 0.0), "mm2": ("area", 1e-6, 0.0),
    "m3": ("volume", 1.0, 0.0), "cm3": ("volume", 1e-6, 0.0),
    "Pa": ("pressure", 1.0, 0.0), "kPa": ("pressure", 1e3, 0.0),
    "bar": ("pressure", 1e5, 0.0),
    "rad": ("angle", 1.0, 0.0), "deg": ("angle", pi / 180, 0.0),
    "K": ("temperature", 1.0, 0.0), "degC": ("temperature", 1.0, 273.15),
    "rad/s": ("speed", 1.0, 0.0), "rpm": ("speed", 2 * pi / 60, 0.0),
    "W": ("power", 1.0, 0.0), "kW": ("power", 1e3, 0.0),
})

SI_UNITS = MappingProxyType({
    "length": "m", "area": "m2", "volume": "m3", "pressure": "Pa",
    "angle": "rad", "temperature": "K", "speed": "rad/s", "power": "W",
})


@dataclass(frozen=True, slots=True)
class Quantity:
    value: float
    unit: str
    dimension: str

    def __post_init__(self):
        to_si(self)


def to_si(quantity: Quantity) -> float:
    """Return a finite SI float, including the explicit Celsius offset."""
    if not isinstance(quantity, Quantity):
        raise ValueContractError("INVALID_VALUE", "", "Expected Quantity")
    if not isinstance(quantity.unit, str) or quantity.unit not in _UNITS:
        raise ValueContractError("UNIT_DIMENSION_MISMATCH", "/unit", "Unknown unit")
    dimension, factor, offset = _UNITS[quantity.unit]
    if quantity.dimension != dimension:
        raise ValueContractError("UNIT_DIMENSION_MISMATCH", "/dimension", "Unit dimension mismatch")
    if type(quantity.value) not in (int, float):
        raise ValueContractError("INVALID_VALUE", "/value", "Expected a real JSON number")
    try:
        value = float(quantity.value)
        result = value * factor + offset
    except OverflowError:
        result = float("inf")
    if not isfinite(result):
        raise ValueContractError("NONFINITE_VALUE", "/value", "SI value must be finite")
    return result
