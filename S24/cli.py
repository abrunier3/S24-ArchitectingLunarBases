from __future__ import annotations
"""
S24 Command Line Interface

Entry point for running the SysML → JSON → USD pipeline.
"""

"""
How to run:

# Single root (unchanged):
python -m S24.cli build \
  --sysml database/sysml/assembly.sysml \
  --json database/json/assembly.json \
  --materials-sysml database/sysml/materials.sysml \
  --materials-json database/json/materials.json \
  --assets database/assets \
  --scene database/scenes/Assembly.usda \
  --root HabitationModule

# Multiple roots:
python -m S24.cli build \
  --sysml database/sysml/assembly.sysml \
  --json database/json/assembly.json \
  --materials-sysml database/sysml/materials.sysml \
  --materials-json database/json/materials.json \
  --assets database/assets \
  --scene database/scenes/Assembly.usda \
  --root HabitationModule Rover ISRU_Plant

# All roots (auto-detect top-level parts):
python -m S24.cli build \
  --sysml database/sysml/assembly.sysml \
  --json database/json/assembly.json \
  --materials-sysml database/sysml/materials.sysml \
  --materials-json database/json/materials.json \
  --assets database/assets \
  --scene database/scenes/Assembly.usda \
  --root-all

"""
import argparse
from pathlib import Path

from S24.sysml.exporter import sysml_to_json, write_json, sysml_to_materials, write_materials_json
from S24.jsonio.vetting import VettingProc
from S24.usd.builder import USDBuilder
from S24.usd.material_library import generate_material_library


# -------------------------
# Helpers
# -------------------------

def _detect_top_level_roots(vetted_parts: dict) -> list[str]:
    """
    Detect top-level root parts by finding parts that are NOT
    children of any other part.

    A part is a child if its name appears as a prefix component
    in another part's name (e.g. 'HabitationModule.O2Tank1'),
    or if the vetted data has parent info.

    Simple heuristic: top-level parts are those whose name
    does not contain a dot (no parent path separator).
    If all names are flat, we look for parts that are not
    referenced as children by any other part.
    """
    all_names = set(vetted_parts.keys())

    # Strategy 1: if names use dot notation (parent.child), top-level = no dot
    dotted = [n for n in all_names if "." in n]
    if dotted:
        roots = sorted(n for n in all_names if "." not in n)
        if roots:
            return roots

    # Strategy 2: check if VettedPart has a parent_name or similar attribute
    roots = []
    child_names = set()
    for name, vp in vetted_parts.items():
        # Collect children if the vetted part tracks them
        if hasattr(vp, "children") and vp.children:
            for child in vp.children:
                child_name = child if isinstance(child, str) else getattr(child, "name", None)
                if child_name:
                    child_names.add(child_name)

    if child_names:
        roots = sorted(n for n in all_names if n not in child_names)
        if roots:
            return roots

    # Strategy 3: fallback — all parts are roots
    return sorted(all_names)


# -------------------------
# CLI Actions
# -------------------------

def build_pipeline(
    *,
    sysml_path: Path,
    json_path: Path,
    assets_dir: Path,
    scene_path: Path,
    root_names: list[str],
    root_all: bool,
    namespace: str,
    materials_sysml_path: Path,
    materials_json_path: Path,
) -> None:
    """
    Run the full S24 pipeline.

    Inputs:
        sysml_path : Path to SysML v2 file
        json_path  : Output JSON path
        assets_dir : Root directory for USD assets
        scene_path : Output USD scene path
        root_names : List of root part names (can be empty if root_all=True)
        root_all   : If True, auto-detect all top-level parts
        namespace  : URN namespace

    Output:
        None (writes files to disk)
    """

    # --- SysML → JSON ---
    sysml_text = sysml_path.read_text(encoding="utf-8")
    parts = sysml_to_json(sysml_text, namespace=namespace)
    write_json(parts, json_path)

    # --- SysML Materials → JSON ---
    mat_text = materials_sysml_path.read_text(encoding="utf-8")
    materials = sysml_to_materials(mat_text)
    write_materials_json(materials, str(materials_json_path))

    # --- Vet JSON ---
    vetting = VettingProc(str(json_path))
    vetted_parts = vetting.by_name

    # --- Vet material references ---
    known_material_ids = {m["materialId"] for m in materials}
    for name, vp in vetted_parts.items():
        if vp.material_ref not in known_material_ids:
            raise ValueError(
                f"Part '{name}' references material '{vp.material_ref}' "
                f"which does not exist in the material library. "
                f"Known materials: {sorted(known_material_ids)}"
            )

    # --- Generate material library USD ---
    mat_library_path = str(Path(assets_dir) / "mtl" / "lunar_materials.usda")
    generate_material_library(str(materials_json_path), mat_library_path)

    # --- Resolve root names ---
    if root_all:
        roots = _detect_top_level_roots(vetted_parts)
        print(f"[S24] Auto-detected {len(roots)} root(s): {', '.join(roots)}")
    else:
        roots = root_names

    # Validate roots exist
    for r in roots:
        if r not in vetted_parts:
            available = sorted(vetted_parts.keys())
            raise ValueError(
                f"Root part '{r}' not found in vetted parts. "
                f"Available parts: {available}"
            )

    # --- Build USD ---
    builder = USDBuilder(
        vetted_parts,
        database_dir="database",
        overwrite=True,
        use_paths_from_vetted=False,
    )
    builder.build_all_parts()

    # --- Write assembly scene(s) ---
    scene_base = Path(scene_path)

    if len(roots) == 1:
        # Single root → single scene file (backward compatible)
        builder.write_assembly_scene(
            scene_name=scene_base.name,
            root_name=roots[0],
            include_root_as_instance=True,
        )
        print(f"[S24] Scene written: {scene_base}")
    else:
        # Multiple roots → one scene per root
        for root_name in roots:
            scene_name = f"{scene_base.stem}_{root_name}{scene_base.suffix}"
            builder.write_assembly_scene(
                scene_name=scene_name,
                root_name=root_name,
                include_root_as_instance=True,
            )
            print(f"[S24] Scene written: {scene_base.parent / scene_name}")

        print(f"[S24] Built {len(roots)} scene(s) total.")


# -------------------------
# Argument Parser
# -------------------------

def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="S24",
        description="SysML v2 → USD digital system pipeline",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Run full pipeline")

    build.add_argument("--sysml", type=Path, required=True)
    build.add_argument("--json", type=Path, required=True)
    build.add_argument("--assets", type=Path, required=True)
    build.add_argument("--scene", type=Path, required=True)

    # Root selection: --root (one or more names) OR --root-all (auto-detect)
    root_group = build.add_mutually_exclusive_group(required=True)
    root_group.add_argument(
        "--root",
        type=str,
        nargs="+",
        help="Root part name(s) to build scenes for",
    )
    root_group.add_argument(
        "--root-all",
        action="store_true",
        default=False,
        help="Auto-detect and build all top-level root parts",
    )

    build.add_argument(
        "--namespace",
        type=str,
        default="lunarspaceport1",
        help="URN namespace",
    )

    build.add_argument("--materials-sysml", type=Path, required=True)
    build.add_argument("--materials-json", type=Path, required=True)

    return parser


# -------------------------
# CLI Entry Point
# -------------------------

def main() -> None:
    parser = make_parser()
    args = parser.parse_args()

    if args.command == "build":
        build_pipeline(
            sysml_path=args.sysml,
            json_path=args.json,
            assets_dir=args.assets,
            scene_path=args.scene,
            root_names=args.root or [],
            root_all=args.root_all if hasattr(args, "root_all") else False,
            namespace=args.namespace,
            materials_sysml_path=args.materials_sysml,
            materials_json_path=args.materials_json,
        )


if __name__ == "__main__":
    main()
