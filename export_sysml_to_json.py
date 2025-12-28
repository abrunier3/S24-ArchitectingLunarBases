import json
import re
from pathlib import Path

# Example SysML patterns it supports:
# part def Car {
# part def Engine {
PART_DEF_PATTERN = re.compile(r'^\s*part\s+def\s+(\w+)\s*\{?')

# attribute weight: Real = 1200;
# attribute color: String;
ATTRIBUTE_PATTERN = re.compile(
    r'^\s*attribute\s+(\w+)\s*:\s*([\w\.]+)\s*(?:=\s*([^;]+))?;?'
)

def parse_sysml_parts(path: str):
    text = Path(path).read_text()
    lines = text.splitlines()

    parts = []
    current_part = None
    brace_depth = 0

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        # Detect "part def ..."
        m_part = PART_DEF_PATTERN.match(line)
        if m_part:
            # Close previous part if any
            if current_part is not None:
                parts.append(current_part)

            part_name = m_part.group(1)
            current_part = {
                "name": part_name,
                "kind": "part",
                "attributes": []
            }

            # Track opening brace on same line, if present
            brace_depth = line.count("{") - line.count("}")
            if brace_depth < 0:
                brace_depth = 0
            continue

        # If we're inside a part block, look for attributes and end of block
        if current_part is not None:
            # Track braces to detect end of block
            brace_depth += line.count("{")
            brace_depth -= line.count("}")

            # Attribute line
            m_attr = ATTRIBUTE_PATTERN.match(line)
            if m_attr:
                attr_name = m_attr.group(1)
                attr_type = m_attr.group(2)
                default_value = m_attr.group(3).strip() if m_attr.group(3) else None

                current_part["attributes"].append(
                    {
                        "name": attr_name,
                        "type": attr_type,
                        "default": default_value
                    }
                )

            # End of part block
            if brace_depth <= 0:
                parts.append(current_part)
                current_part = None
                brace_depth = 0

    # In case file ended without closing brace
    if current_part is not None:
        parts.append(current_part)

    return {"parts": parts}


def convert_to_json(sysml_file: str, json_file: str):
    model = parse_sysml_parts(sysml_file)
    Path(json_file).write_text(json.dumps(model, indent=2))
    print(f"Wrote JSON to {json_file}")


if __name__ == "__main__":
    # change these to your filenames
    convert_to_json("o2tank.sysml", "o2tank.json")