from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class PartNode:
    name: str
    attributes_raw: Dict[str, str] = field(default_factory=dict)
    attributes_val: Dict[str, Any] = field(default_factory=dict)
    children: Dict[str, "PartNode"] = field(default_factory=dict)


@dataclass
class Model:
    package_name: Optional[str] = None
    parts: Dict[str, PartNode] = field(default_factory=dict)
