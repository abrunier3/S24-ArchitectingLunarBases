# JSON loading utilities 

from __future__ import annotations

import os, json
from typing import Any, Dict, Union, List


def load_parts_json(source: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Accepts:
      - list[dict]: already-parsed JSON
      - str path to a .json file
      - str containing JSON text (if it starts with '[' or '{')
    Returns: list[dict] (your parts array)
    """
    # Already parsed
    if isinstance(source, list):
        return source

    if not isinstance(source, str):
        raise JsonVettingError(f"Expected list or str for JSON source, got {type(source).__name__}")

    s = source.strip()

    # If it's a path to an existing file
    if os.path.exists(s) and os.path.isfile(s):
        with open(s, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # Otherwise treat as JSON text
        if not (s.startswith("[") or s.startswith("{")):
            raise JsonVettingError(
                "JSON source is a string but is neither a valid file path nor JSON text."
            )
        data = json.loads(s)

    # Normalize top-level: if dict with "parts", use it; else require list
    if isinstance(data, dict) and "parts" in data:
        data = data["parts"]

    if not isinstance(data, list) or not data:
        raise JsonVettingError("Top-level JSON must be a non-empty list of parts (or dict with key 'parts').")

    # Ensure elements are dicts
    if not all(isinstance(x, dict) for x in data):
        raise JsonVettingError("Top-level list must contain only objects/dicts.")

    return data
