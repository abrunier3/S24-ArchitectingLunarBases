from __future__ import annotations
"""
S24 Command Line Interface

Entry point for running the SysML → JSON → USD pipeline.
"""

"""
How to run:

python -m S24.cli build \
  --sysml database/sysml/habitation.sysml \
  --json database/json/habmod.json \
  --assets database/assets \
  --scene database/scenes/HabitationAssembly.usda \
  --root HabitationModule

"""
import argparse
from pathlib import Path

from S24.sysml.exporter import sysml_to_json, write_json, sysml_to_materials, write_materials_json
from S24.jsonio.vetting import VettingProc
from S24.usd.builder import USDBuilder
from S24.usd.material_library import generate_material_library


# -------------------------
# CLI Actions
# -------------------------

def build_pipeline(
    *,
    sysml_path: Path,
    json_path: Path,
    assets_dir: Path,
    scene_path: Path,
    root_name: str,
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
        root_name  : Root part name
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




    # --- Build USD ---
    builder = USDBuilder(
        vetted_parts,
        database_dir="database",
        overwrite=True,
        use_paths_from_vetted=False,
    )
    builder.build_all_parts()
    builder.write_assembly_scene(
        scene_name=Path(scene_path).name,  # ex: "HabitationAssembly.usda"
        root_name=root_name,
        include_root_as_instance=True,
    )


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
    build.add_argument("--root", type=str, required=True)

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
            root_name=args.root,
            namespace=args.namespace,
            materials_sysml_path=args.materials_sysml,
            materials_json_path=args.materials_json,
        )


if __name__ == "__main__":
    main()
