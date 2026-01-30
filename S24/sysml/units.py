from __future__ import annotations

from typing import Tuple


def convert_numeric_with_units(name: str, value: float) -> Tuple[str, float]:
    """
    Convert known attributes to SI and rename with suffix.
    """
    v = float(value)

    if name.endswith("_volume"):
        # liters -> m^3
        return f"{name}_m3", v / 1000.0

    if name.endswith("_usableO2Capacity"):
        # liters -> m^3
        return f"{name}_m3", v / 1000.0

    if name.endswith("_operatingPressure") or name.endswith("_maxPressure"):
        # kPa -> Pa
        return f"{name}_Pa", v * 1000.0

    if name.endswith("_dryMass"):
        # kg stays kg
        return f"{name}_kg", v

    if name.endswith("_wallThickness"):
        # m stays m
        return f"{name}_m", v

    return name, v
