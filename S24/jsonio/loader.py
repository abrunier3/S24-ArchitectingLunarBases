import json
from typing import Any, List, Union


def load_parts_json(source: Union[str, List[dict]]) -> List[dict]:
    """
    Load JSON parts either from:
      - a file path
      - an already-loaded list of dicts
    """
    if isinstance(source, list):
        return source

    if isinstance(source, str):
        with open(source, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    raise TypeError("source must be a file path or list of dicts")
