from __future__ import annotations

import re
from typing import Any, Tuple

_STR_RE = re.compile(r'"([^"]*)"')
_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")

def strip_comment(line: str) -> str:
    """
    Remove // comments from a line.
    """
    return line.split("//", 1)[0].rstrip()


def parse_literal_token(value_str: str) -> Any:
    """
    Parse a simple literal token:
      - "foo" -> "foo"
      - 1.23 or 42 -> number
      - otherwise -> raw string (expression or symbol)
    """
    s = value_str.strip()

    m = _STR_RE.fullmatch(s)
    if m:
        return m.group(1)

    if _NUM_RE.match(s):
        return float(s) if "." in s else int(s)

    return s

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

