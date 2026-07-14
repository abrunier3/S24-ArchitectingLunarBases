from __future__ import annotations

from pathlib import Path
import os
import sys


def main() -> int:
    extension_root = Path(__file__).resolve().parent
    repo_root = extension_root.parent.parent
    sys.path.insert(0, str(extension_root))

    from lsp1_pipeline.manifest_builder import main as builder_main

    scenario_slug = os.environ.get("SCENARIO_SLUG", "ECLIPSE_Project").strip()
    if not scenario_slug or any(
        character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"
        for character in scenario_slug
    ):
        raise ValueError(f"Invalid scenario identifier: {scenario_slug!r}")
    scenario_json = (
        repo_root / "clean_database" / "json" / scenario_slug / f"{scenario_slug}.json"
    )
    scenario_results = repo_root / "outputs" / "scenarios" / scenario_slug / "des_results.json"

    return builder_main([
        "--system-json", str(scenario_json),
        "--waypoints-usd", str(repo_root / "clean_database" / "scenes" / "waypoints.usda"),
        "--des-json", str(scenario_results),
        "--scene-usd", str(repo_root / "clean_database" / "usd" / "scenes" / "scene.usda"),
        "--terrain-usd", str(repo_root / "clean_database" / "scenes" / "Lunar_surface_v4.usdc"),
        "--output", str(repo_root / "extensions" / "lsp1.pipeline" / "data" / "manifest.json"),
    ])


if __name__ == "__main__":
    raise SystemExit(main())
