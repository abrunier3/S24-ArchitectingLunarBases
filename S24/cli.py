from __future__ import annotations
"""
S24 Command Line Interface

Entry point for running the SysML → JSON → USD pipeline.
"""

"""
How to run:

# Single root:
python -m S24.cli build \
  --sysml database/sysml/assembly.sysml \
  --json database/json/assembly.json \
  --materials-sysml database/sysml/materials.sysml \
  --materials-json database/json/materials.json \
  --assets database/assets \
  --scene database/scenes/Assembly.usda \
  --root HabitationModule

# Multiple roots (single USD scene):
python -m S24.cli build \
  --sysml database/sysml/assembly.sysml \
  --json database/json/assembly.json \
  --materials-sysml database/sysml/materials.sysml \
  --materials-json database/json/materials.json \
  --assets database/assets \
  --scene database/scenes/Assembly.usda \
  --root HabitationModule Rover ISRU_Plant

# All roots (auto-detect):
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

    # --- Resolve roots ---
    if root_all:
        # Let write_assembly_scene auto-detect (root_names=None, root_name=None)
        roots = None
        print("[S24] Auto-detecting root parts...")
    else:
        roots = root_names
        # Validate
        for r in roots:
            if r not in vetted_parts:
                raise ValueError(
                    f"Root part '{r}' not found. "
                    f"Available: {sorted(vetted_parts.keys())}"
                )

    # --- Single USD scene with all roots ---
    builder.write_assembly_scene(
        scene_name=Path(scene_path).name,
        root_names=roots,
        include_root_as_instance=True,
    )
    print(f"[S24] Scene written: {scene_path}")


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

    root_group = build.add_mutually_exclusive_group(required=True)
    root_group.add_argument(
        "--root",
        type=str,
        nargs="+",
        help="Root part name(s)",
    )
    root_group.add_argument(
        "--root-all",
        action="store_true",
        default=False,
        help="Auto-detect all top-level root parts",
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
