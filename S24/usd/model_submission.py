from typing import Dict, Any, List, Optional
from pathlib import Path
import json

from S24.utils.setup_paths import _find_project_root


USD_EXTENSIONS = (".usd", ".usda", ".usdc", ".usdz")


def _to_repo_relative(path: Path, repo_root: Path) -> str:
    """
    Convert a path to a repo-relative POSIX path.

    This prevents GitHub Actions absolute paths such as:
        /home/runner/work/S24-ArchitectingLunarBases/S24-ArchitectingLunarBases/...

    from being written into persistent JSON/USD metadata.
    """
    path = path.resolve()
    repo_root = repo_root.resolve()

    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        # Fallback for paths outside the repository.
        # This should be rare, but keeps the function robust.
        return path.as_posix()


def _resolve_json_path(json_path: str | Path, repo_root: Path) -> Path:
    """
    Resolve incoming JSON path.

    Allows both:
    - absolute paths
    - repo-relative paths
    """
    p = Path(json_path)

    if p.is_absolute():
        return p

    return repo_root / p


def _find_cad_file(cad_dir: Path, part_name: str) -> Optional[Path]:
    """
    Find a CAD/USD file for a given part.

    Tries:
    1. clean_database/cad_models/<PartName>/
    2. clean_database/cad_models/<partname-lowercase>/

    Returns the first matching USD-family file.
    """
    candidate_folders = [
        cad_dir / part_name,
        cad_dir / part_name.lower(),
    ]

    for folder in candidate_folders:
        if not folder.exists():
            continue

        cad_candidates = [
            p for p in folder.iterdir()
            if p.is_file() and p.suffix.lower() in USD_EXTENSIONS
        ]

        if cad_candidates:
            # Deterministic selection instead of arbitrary filesystem order.
            return sorted(cad_candidates, key=lambda p: p.name.lower())[0]

    return None


def build_submission_manifest(
    asset_paths: List[str],
    *,
    verbose: int = 1
) -> Dict[str, Any]:
    """
    STEP 3: Model Submission.

    Builds a unified part-level manifest that links:
    - JSON part data
    - CAD model availability
    - Transform information
    - Metadata useful for USD/Omniverse

    Important path convention
    -------------------------
    Persistent paths stored in the manifest are repo-relative, not absolute.

    For example, this is correct:
        clean_database/cad_models/RegolithRover/RegolithRover.usdc

    This is intentionally avoided:
        /home/runner/work/S24-ArchitectingLunarBases/S24-ArchitectingLunarBases/...

    Parameters
    ----------
    asset_paths : List[str]
        Paths to per-part JSON files. Can be absolute or repo-relative.

    verbose : int
        0 -> silent
        1 -> summary
        2 -> detailed per-part output

    Returns
    -------
    Dict[str, Any]
        {
            "parts": [...],
            "summary": {...}
        }
    """

    root = _find_project_root().resolve()
    database_dir = root / "clean_database"
    cad_dir = database_dir / "cad_models"

    manifest_parts = []

    for raw_json_path in asset_paths:
        json_path_abs = _resolve_json_path(raw_json_path, root)

        if not json_path_abs.exists():
            raise FileNotFoundError(f"Asset JSON not found: {json_path_abs}")

        with open(json_path_abs, "r", encoding="utf-8") as f:
            part_data = json.load(f)

        part_name = part_data["name"]

        cad_file_abs = _find_cad_file(cad_dir, part_name)
        cad_found = cad_file_abs is not None

        json_path_repo = _to_repo_relative(json_path_abs, root)
        cad_path_repo = _to_repo_relative(cad_file_abs, root) if cad_found else None

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
            # Persistent paths are repo-relative.
            "json_path": json_path_repo,
            "cad_path": cad_path_repo,
            "cad_found": cad_found,

            # Optional debug-only absolute paths.
            # Do not use these for USD references.
            "json_path_abs": str(json_path_abs.resolve()),
            "cad_path_abs": str(cad_file_abs.resolve()) if cad_found else None,

            # --- Spatial info ---
            "position_m": position,
            "rotation_deg": rotation,

            # --- Geometry / semantics ---
            "dimensions": dimensions,
            "attributes": attributes,
            "material": material,
            "geometry_ref": geometry_ref,

            # --- Ports ---
            "ports": part_data.get("ports", []),
        }

        manifest_parts.append(entry)

        if verbose >= 2:
            status = "CAD FOUND" if cad_found else "CAD MISSING"
            print(f"[PART] {part_name}")
            print(f"  JSON repo path : {json_path_repo}")
            print(f"  JSON abs path  : {json_path_abs.resolve()}")
            print(f"  CAD repo path  : {cad_path_repo if cad_found else 'MISSING'}")
            print(f"  CAD abs path   : {cad_file_abs.resolve() if cad_found else 'MISSING'}")
            print(f"  Pos            : {position}")
            print(f"  Rot            : {rotation}")
            print(f"  → {status}\n")

    total = len(manifest_parts)
    cad_ok = sum(1 for p in manifest_parts if p["cad_found"])
    cad_missing = total - cad_ok

    if verbose >= 1:
        print("\n" + "=" * 50)
        print("STEP 3: MODEL SUBMISSION SUMMARY")
        print("=" * 50)
        print(f"Total parts      : {total}")
        print(f"CAD found        : {cad_ok}")
        print(f"CAD missing      : {cad_missing}")
        print("=" * 50)

    return {
        "parts": manifest_parts,
        "summary": {
            "total_parts": total,
            "cad_found": cad_ok,
            "cad_missing": cad_missing,
        }
    }

# from typing import Dict, Any, List
# from pathlib import Path
# import json

# from S24.utils.setup_paths import _find_project_root


# def build_submission_manifest(
#     asset_paths: List[str],
#     *,
#     verbose: int = 1
# ) -> Dict[str, Any]:
#     """
#     STEP 3: Model Submission

#     Builds a unified part-level manifest that links:
#     - JSON part data
#     - CAD model availability
#     - Transform (position/orientation)
#     - Metadata useful for USD/Omniverse

#     Parameters
#     ----------
#     asset_paths : List[str]
#         Paths to per-part JSON files

#     verbose : int
#         0 → silent
#         1 → summary
#         2 → detailed per-part output

#     Returns
#     -------
#     Dict[str, Any]
#         {
#             "parts": [...],
#             "summary": {...}
#         }
#     """

#     root = _find_project_root()
#     database_dir = root / "clean_database"
#     cad_dir = database_dir / "cad_models"

#     manifest_parts = []

#     for json_path in asset_paths:
#         json_path = Path(json_path)

#         with open(json_path, "r", encoding="utf-8") as f:
#             part_data = json.load(f)

#         part_name = part_data["name"]


#         cad_folder = cad_dir / part_name
#         if not cad_folder.exists():
#             cad_folder = cad_dir / part_name.lower()
#         cad_file = None

#         if cad_folder.exists():
#             cad_candidates = list(cad_folder.glob("*.usd*"))
#             if cad_candidates:
#                 cad_file = cad_candidates[0]

#         cad_found = cad_file is not None


#         transform = part_data.get("transform", {})
#         position = transform.get("position_m", [0, 0, 0])
#         rotation = transform.get("rotation_deg", [0, 0, 0])


#         dimensions = part_data.get("dimensions", {})
#         attributes = part_data.get("attributes", {})
#         material = part_data.get("materialRef")
#         geometry_ref = part_data.get("metadata", {}).get("geometryRef")


#         entry = {
#             "name": part_name,
#             "id": part_data.get("id"),

#             # --- Data sources ---
#             "json_path": str(json_path),
#             "cad_path": str(cad_file) if cad_found else None,
#             "cad_found": cad_found,

#             # --- Spatial info ---
#             "position_m": position,
#             "rotation_deg": rotation,

#             # --- Geometry / semantics ---
#             "dimensions": dimensions,
#             "attributes": attributes,
#             "material": material,
#             "geometry_ref": geometry_ref,

#             # --- Ports (useful later for routing/visualization)
#             "ports": part_data.get("ports", []),
#         }

#         manifest_parts.append(entry)


#         if verbose >= 2:
#             status = "CAD FOUND" if cad_found else "CAD MISSING"
#             print(f"[PART] {part_name}")
#             print(f"  JSON: {json_path}")
#             print(f"  CAD : {cad_file if cad_found else 'MISSING'}")
#             print(f"  Pos : {position}")
#             print(f"  Rot : {rotation}")
#             print(f"  → {status}\n")

#     total = len(manifest_parts)
#     cad_ok = sum(1 for p in manifest_parts if p["cad_found"])
#     cad_missing = total - cad_ok

#     if verbose >= 1:
#         print("\n" + "="*50)
#         print("STEP 3: MODEL SUBMISSION SUMMARY")
#         print("="*50)
#         print(f"Total parts      : {total}")
#         print(f"CAD found        : {cad_ok}")
#         print(f"CAD missing      : {cad_missing}")
#         print("="*50)

#     return {
#         "parts": manifest_parts,
#         "summary": {
#             "total_parts": total,
#             "cad_found": cad_ok,
#             "cad_missing": cad_missing,
#         }
#     }
