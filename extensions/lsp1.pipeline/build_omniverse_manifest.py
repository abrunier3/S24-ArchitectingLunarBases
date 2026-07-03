from __future__ import annotations

from pathlib import Path
import sys


def main() -> int:
    extension_root = Path(__file__).resolve().parent
    repo_root = extension_root.parent.parent
    sys.path.insert(0, str(extension_root))

    from lsp1_pipeline.manifest_builder import main as builder_main

    return builder_main([
        "--system-json", str(repo_root / "clean_database" / "json" / "ECLIPSE_Project" / "ECLIPSE_Project.json"),
        "--waypoints-usd", str(repo_root / "clean_database" / "scenes" / "waypoints.usda"),
        "--des-json", str(repo_root / "outputs" / "des_results.json"),
        "--scene-usd", str(repo_root / "clean_database" / "usd" / "scenes" / "scene.usda"),
        "--terrain-usd", str(repo_root / "clean_database" / "scenes" / "Lunar_surface_v4.usdc"),
        "--output", str(repo_root / "extensions" / "lsp1.pipeline" / "data" / "manifest.json"),
    ])


if __name__ == "__main__":
    raise SystemExit(main())
