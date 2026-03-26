from typing import Dict, Any, List
from pathlib import Path
import json

from S24.utils.setup_paths import _find_project_root


def build_submission_manifest(
    asset_paths: List[str],
    *,
    verbose: int = 1
) -> Dict[str, Any]:
    """
    STEP 3: Model Submission

    Builds a unified part-level manifest that links:
    - JSON part data
    - CAD model availability
    - Transform (position/orientation)
    - Metadata useful for USD/Omniverse

    Parameters
    ----------
    asset_paths : List[str]
        Paths to per-part JSON files

    verbose : int
        0 → silent
        1 → summary
        2 → detailed per-part output

    Returns
    -------
    Dict[str, Any]
        {
            "parts": [...],
            "summary": {...}
        }
    """

    root = _find_project_root()
    database_dir = root / "clean_database"
    cad_dir = database_dir / "cad_models"

    manifest_parts = []

    for json_path in asset_paths:
        json_path = Path(json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            part_data = json.load(f)

        part_name = part_data["name"]


        cad_folder = cad_dir / part_name.lower()
        cad_file = None

        if cad_folder.exists():
            cad_candidates = list(cad_folder.glob("*.usd*"))
            if cad_candidates:
                cad_file = cad_candidates[0]

        cad_found = cad_file is not None


        transform = part_data.get("transform", {})
        position = transform.get("position_m", [0, 0, 0])
        rotation = transform.get("rotation_deg", [0, 0, 0])


        dimensions = part_data.get("dimensions", {})
        attributes = part_data.get("attributes", {})
        material = part_data.get("materialRef")
        geometry_ref = part_data.get("metadata", {}).get("geometryRef")


        entry = {
            "name": part_name,
            "id": part_data.get("id"),

            # --- Data sources ---
            "json_path": str(json_path),
            "cad_path": str(cad_file) if cad_found else None,
            "cad_found": cad_found,

            # --- Spatial info ---
            "position_m": position,
            "rotation_deg": rotation,

            # --- Geometry / semantics ---
            "dimensions": dimensions,
            "attributes": attributes,
            "material": material,
            "geometry_ref": geometry_ref,

            # --- Ports (useful later for routing/visualization)
            "ports": part_data.get("ports", []),
        }

        manifest_parts.append(entry)


        if verbose >= 2:
            status = "CAD FOUND" if cad_found else "CAD MISSING"
            print(f"[PART] {part_name}")
            print(f"  JSON: {json_path}")
            print(f"  CAD : {cad_file if cad_found else 'MISSING'}")
            print(f"  Pos : {position}")
            print(f"  Rot : {rotation}")
            print(f"  → {status}\n")

    total = len(manifest_parts)
    cad_ok = sum(1 for p in manifest_parts if p["cad_found"])
    cad_missing = total - cad_ok

    if verbose >= 1:
        print("\n" + "="*50)
        print("STEP 3: MODEL SUBMISSION SUMMARY")
        print("="*50)
        print(f"Total parts      : {total}")
        print(f"CAD found        : {cad_ok}")
        print(f"CAD missing      : {cad_missing}")
        print("="*50)

    return {
        "parts": manifest_parts,
        "summary": {
            "total_parts": total,
            "cad_found": cad_ok,
            "cad_missing": cad_missing,
        }
    }