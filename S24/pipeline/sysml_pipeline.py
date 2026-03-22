import os, sys
import json
from typing import Dict, Any

from S24.utils import setup_paths
from S24.sysml.main_api import sysml_to_json
from S24.validation.plotter import build_system_graph
from S24.validation.plotter import plot_system_graph
from S24.jsonio.writer import write_json, write_json_assets

def run_sysml_pipeline(
    sysml_file: str,
    *,
    use_repo: bool = True,
    namespace: str = "lunarspaceport1",
    verbose: int = 1,
    plot: bool = True,
) -> Dict[str, Any]:

    paths = setup_paths(sysml_file=sysml_file, use_repo=use_repo)

    SYSML_FILE = paths["SYSML_FILE"]
    JSON_FILE = paths["JSON_FILE"]
    JSON_ASSETS_DIR = paths["JSON_ASSETS"]

    if verbose >= 1:
        print(f"[LOAD] {SYSML_FILE}")

    with open(SYSML_FILE, "r", encoding="utf-8") as f:
        sysml_text = f.read()

    data = sysml_to_json(sysml_text, namespace=namespace)

    if verbose >= 1:
        print("\n[METADATA]")
        print(json.dumps(data["metadata"], indent=2))

    parts = data["parts"]
    connections = data["connections"]

    G = build_system_graph(parts, connections)

    if plot:
        plot_system_graph(G)

    output_path = write_json(data, JSON_FILE)

    if verbose >= 1:
        print(f"\n[WRITE] Full JSON → {output_path}")

    asset_paths = write_json_assets(
        parts,
        JSON_ASSETS_DIR,
        verbose=verbose
    )

    if verbose >= 2:
        print("\n[CONNECTIONS]")
        for c in connections:
            print(c)

    return {
        "data": data,
        "graph": G,
        "paths": {
            "main_json": output_path,
            "assets": asset_paths,
        }
    }