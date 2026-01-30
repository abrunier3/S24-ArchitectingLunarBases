from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


_STR_RE = re.compile(r'"([^"]*)"')
_NUM_RE = re.compile(r"^-?\d+(\.\d+)?$")


@dataclass
class PartNode:
    """
    Represents a SysML 'part' block.
    - attributes_raw: raw RHS strings (expressions or literals)
    - attributes_val: evaluated values (numbers or strings)
    - children: nested parts (including *dims blocks)
    """
    name: str
    attributes_raw: Dict[str, str] = field(default_factory=dict)
    attributes_val: Dict[str, Any] = field(default_factory=dict)
    children: Dict[str, "PartNode"] = field(default_factory=dict)


@dataclass
class Model:
    """
    Parsed SysML model: package_name + top-level parts.
    """
    package_name: Optional[str] = None
    parts: Dict[str, PartNode] = field(default_factory=dict)


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


def parse_sysml(text: str) -> Model:
    """
    Parse a subset of SysML v2:
      - package 'Name' { ... }
      - part <Name> { ... }
      - attribute <name> = <value>;
    Produces nested PartNode tree.
    """
    model = Model()
    current_stack: List[PartNode] = []
    brace_stack: List[str] = []

    for raw_line in text.splitlines():
        line = strip_comment(raw_line).strip()
        if not line:
            continue

        # package
        m = re.match(r"package\s+'([^']+)'\s*\{", line)
        if m:
            model.package_name = m.group(1)
            brace_stack.append("package")
            continue

        # ignore requirement blocks
        if re.match(r"requirement\s+\w+\s*\{", line):
            brace_stack.append("ignore_req")
            continue

        # ignore satisfy statements
        if re.match(r"satisfy\s+\w+\s+by\s+\w+;", line):
            continue

        # part (top-level or nested)
        m = re.match(r"part\s+(\w+)\s*\{", line)
        if m:
            part_name = m.group(1)
            node = PartNode(name=part_name)

            if current_stack:
                current_stack[-1].children[part_name] = node
            else:
                model.parts[part_name] = node

            current_stack.append(node)
            brace_stack.append("part")
            continue

        # closing brace
        if line == "}":
            if brace_stack:
                ctx = brace_stack.pop()
                if ctx == "part" and current_stack:
                    current_stack.pop()
            continue

        # attributes
        if current_stack:
            m = re.match(r"attribute\s+(\w+)\s*=\s*(.+);", line)
            if m:
                attr_name = m.group(1)
                raw_val = m.group(2).strip().rstrip(";")
                current_stack[-1].attributes_raw[attr_name] = raw_val
                continue

    return model
