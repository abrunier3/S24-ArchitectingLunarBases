from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List


@dataclass
class PartNode:
    name: str
    attributes_raw: Dict[str, str] = field(default_factory=dict)
    attributes_val: Dict[str, Any] = field(default_factory=dict)
    children: Dict[str, "PartNode"] = field(default_factory=dict)

    ports: Dict[str, Dict[str, Any]] = field(default_factory=dict)   
    metadata: Dict[str, Any] = field(default_factory=dict)           


@dataclass
class Model:
    package_name: Optional[str] = None
    parts: Dict[str, PartNode] = field(default_factory=dict)

    interfaces: List[Dict[str, str]] = field(default_factory=list)   