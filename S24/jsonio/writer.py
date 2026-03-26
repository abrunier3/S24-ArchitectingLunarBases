import json
import os
from typing import List, Dict, Any

def write_json(data: Dict[str, Any], output_path: str) -> str:
    """
    Write full pipeline output (metadata, parts, connections) to disk.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return output_path


def write_json_assets(
    parts: List[Dict[str, Any]],
    output_dir: str,
) -> List[str]:
    """
    Write each part as a separate JSON file.

    Returns list of written file paths.
    """
    os.makedirs(output_dir, exist_ok=True)

    paths = []

    for part in parts:
        name = part["name"]
        file_path = os.path.join(output_dir, f"{name}.json")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(part, f, indent=2)

        paths.append(file_path)

    return paths

# ----------------------------------------------------------------------------------------------------------------------------------------


# def write_materials_json(materials: List[Dict[str, Any]], output_path: str) -> str:
#     """
#     Write materials list to disk as pretty JSON.
#     Returns output_path.
#     """
#     with open(output_path, "w", encoding="utf-8") as f:
#         json.dump({"materials": materials}, f, indent=2)
#     return output_path