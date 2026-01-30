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

from __future__ import annotations

import argparse
from pathlib import Path

from S24.sysml.exporter import sysml_to_json, write_json
from S24.jsonio.vetting import VettingProc
from S24.usd.builder import USDBuilder


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

    # --- Vet JSON ---
    vetting = VettingProc(file=str(json_path))
    vetted_parts = vetting.by_name

    # --- Build USD ---
    builder = USDBuilder(
        vetted_parts,
        assets_dir=str(assets_dir),
        overwrite=True,
        use_paths_from_vetted=False,
    )

    builder.build_all_parts()
    builder.write_assembly_scene(
        scene_path=str(scene_path),
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
        )


if __name__ == "__main__":
    main()
