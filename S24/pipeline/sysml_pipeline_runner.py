import json
from typing import Dict, Any

from S24.utils import resolve_database_paths
from S24.sysml.main_api import sysml_to_json_transformer
from S24.jsonio.writer import write_json, write_json_assets

def run_sysml_to_json_pipeline(
    sysml_file: str,
    *,
    verbose: int,
    use_repo: bool = True,
    namespace: str = "S24_PIPELINE",
    write_individual: bool = True,
    ) -> Dict[str, Any]:
    
    # Automatically set up the paths in the database (right now the default is the clean_database).
    paths = resolve_database_paths(sysml_file=sysml_file, use_repo=use_repo)
    SYSML_FILE = paths["SYSML_FILE"]
    JSON_FILE = paths["JSON_FILE"]
    JSON_ASSETS_DIR = paths["JSON_ASSETS"]

    # transform sysml text into ready for json writing python parts.
    with open(SYSML_FILE, "r", encoding="utf-8") as f:
        sysml_text = f.read()
    data = sysml_to_json_transformer(verbose=verbose,sysml_text=sysml_text, namespace=namespace)
    metadata = data['metadata']
    parts = data["parts"]
    connections = data['connections']

    # write json file 
    output_path = write_json(data, JSON_FILE)

    # Write individual json files for each part. 
    if write_individual:
        asset_paths = write_json_assets(
            parts,
            JSON_ASSETS_DIR,
        )
    
    # Debugging prints
    if verbose >= 1:
        print(f"\n[WRITE] Full JSON → {output_path}")
        print("\n[METADATA]")
        print(json.dumps(metadata, indent=2))
        print(f"[SUMMARY] Wrote {len(parts)} part files")

        for file_path, part in zip(asset_paths, parts):
            print(f"[WRITE] {part['name']} → {file_path}")

    return {
        "data": data,
        "paths": {
            "main_json": output_path, # main json file path
            "assets": asset_paths,    # individual json part files paths
        }
    }