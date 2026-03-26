import re
from typing import Any, Dict, List, Optional

from S24.sysml.ast import Model, PartNode

def parse_sysml(sysml_text: str) -> Model:
    '''
    Parses the model to a structured python object: Model with rules such as ingore Requirements blocks etc.
    '''

    sysml_text = _normalize_multiline_attributes(sysml_text)

    model = Model()
    current_stack: List[PartNode] = []
    brace_stack: List[str] = []
    current_port: Optional[Dict[str, Any]] = None

    for raw_line in sysml_text.splitlines():
        line = _strip_comment(raw_line).strip()
        if not line:
            continue

        m = re.match(r"package\s+(?:'([^']+)'|(\w+))\s*\{", line)
        if m:
            pkg_name = m.group(1) or m.group(2)

            if "Requirement" in pkg_name or "Requirements" in pkg_name:
                brace_stack.append("ignore_pkg")
                continue

            if model.package_name is None:
                model.package_name = pkg_name

            brace_stack.append("package")
            continue

        if brace_stack and brace_stack[-1] == "ignore_pkg":
            if line == "}":
                brace_stack.pop()
            continue

        if line.startswith("private import"):
            continue

        if re.match(r"view\s+", line):
            continue

        if line.startswith("metadata"):
            if current_stack:
                key = f"metadata_{len(current_stack[-1].metadata) + 1}"
                current_stack[-1].metadata[key] = line
            continue

        m = re.match(r"part\s+(?:def\s+)?(\w+)(?:\s*:\s*\w+)?\s*\{", line)
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

        m = re.match(r"port\s+(\w+)\s*\{", line)
        if m and current_stack:
            port_name = m.group(1)
            current_port = {
                "name": port_name,
                "direction": [],
                "items": []
            }
            current_stack[-1].ports[port_name] = current_port
            brace_stack.append("port")
            continue

        m = re.match(
            r"interface\s+(\w+)\s*:\s*([\w:]+)\s+connect\s+([\w\.]+)\s+to\s+([\w\.]+);",
            line
        )
        if m:
            iface_name = m.group(1)
            iface_type = m.group(2)
            src = m.group(3)
            dst = m.group(4)

            # flow = None
            # if "LOX" in iface_type.upper():
            #     flow = "LOX"

            model.interfaces.append({
                "name": iface_name,
                "type": iface_type,
                "flow": iface_type.upper(),
                "from": src,
                "to": dst,
            })
            continue

        if line == "}":
            if brace_stack:
                ctx = brace_stack.pop()

                if ctx == "part":
                    if current_stack:
                        current_stack.pop()

                elif ctx == "port":
                    current_port = None

            continue

        if current_port:
            m = re.match(r"(in|out)\s+item\s+(\w+);", line)
            if m:
                direction, item_name = m.groups()
                current_port["direction"].append(direction)
                current_port["items"].append(item_name)
            continue

        if current_stack:
            m = re.match(r"attribute\s+(\w+)\s*=\s*(.+);", line)
            if m:
                attr_name = m.group(1)
                raw_val = m.group(2).strip()
                current_stack[-1].attributes_raw[attr_name] = raw_val
                continue
    return model

#------------------------------------------------------------------------------------
# Helpers
def _normalize_multiline_attributes(text: str) -> str:
    lines = text.splitlines()
    new_lines = []
    buffer = ""

    for line in lines:
        stripped = line.strip()

        if buffer:
            buffer += " " + stripped
            if ";" in stripped:
                new_lines.append(buffer)
                buffer = ""
        else:
            if stripped.startswith("attribute") and not stripped.endswith(";"):
                buffer = stripped
            else:
                new_lines.append(line)

    if buffer:
        new_lines.append(buffer)

    return "\n".join(new_lines)


def _strip_comment(line: str) -> str:
    """
    Remove // comments from a line.
    """
    return line.split("//", 1)[0].rstrip()


def _print_model_un(model: Model):
    '''
    Debugging-printing def of the model when parsed from SysML to python. PRINT UN-EVALUATED MODELS
    '''
    def print_part(part, level=0):
        prefix = "  " * level

        print(f"{prefix}📦 Part: {part.name}")

        # attributes
        if part.attributes_raw:
            print(f"{prefix}  🔹 Attributes:")
            for k, v in part.attributes_raw.items():
                print(f"{prefix}    - {k} = {v}")

        # ports
        if getattr(part, "ports", None) and part.ports:
            print(f"{prefix}  🔌 Ports:")
            for pname, pinfo in part.ports.items():
                print(f"{prefix}    - {pname} (dir={pinfo['direction']})")

        # metadata
        if getattr(part, "metadata", None) and part.metadata:
            print(f"{prefix}  🏷 Metadata:")
            for k, v in part.metadata.items():
                print(f"{prefix}    - {k}: {v}")

        # children
        for child in part.children.values():
            print_part(child, level + 1)

    print("\n================= PARSED MODEL (EXPRESSIONS NOT EVALUATED)=================")
    print(f"Package: {model.package_name}\n")

    for part in model.parts.values():
        print_part(part)

    # interfaces
    if getattr(model, "interfaces", None) and model.interfaces:
        print("\n🔗 Interfaces (Connections):")
        for iface in model.interfaces:
            print(f"  - {iface['name']}: {iface['from']} → {iface['to']}")

    print("================================================\n")