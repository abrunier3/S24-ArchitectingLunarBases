# S24 Architecting Lunar Bases

This repository contains the ECLIPSE lunar base digital engineering pipeline:

- a browser interface for mission/system configuration;
- SysML/JSON assets for the current ECLIPSE project;
- DES simulation code and GitHub Actions workflows;
- USD scene generation for Omniverse visualization.

## Current Interface

Open the latest pipeline interface:

https://abrunier3.github.io/S24-ArchitectingLunarBases/JennIndex.html

Older root-level HTML prototypes were removed to keep the repository focused and shareable.

## Active Repository Structure

```text
S24/
  DES_pipeline_version/      Active DES simulation engine
  pipeline/                  SysML graph/pipeline runners
  sysml/                     SysML parsing/evaluation utilities
  usd/                       CAD/USD scene generation utilities

clean_database/
  sysml/ECLIPSE_Project.sysml
  json/ECLIPSE_Project/      Current system JSON and active asset metadata
  json/ECLIPSE_Project/materials.json
  cad_models/                CAD/USD module assets
  scenes/                    Lunar terrain and waypoint USD files
  usd/scenes/scene.usda      Generated Omniverse scene

outputs/
  graph.json                 Connectivity graph output
  des_results.json           DES simulation output
  cad_previews/              CAD preview artifacts used by the interface

extensions/lsp1.pipeline/
  build_omniverse_manifest.py
  lsp1_pipeline/             Omniverse extension
  data/manifest.json         Visualization manifest consumed by the extension

.github/workflows/
  run_graph.yml              Builds graph output from SysML
  run_des.yml                Runs DES and regenerates USD/manifest outputs
  convert_cad.yml            Builds CAD preview artifacts
  deploy-pages.yml           Publishes the browser interface
```

## Notes

- `clean_database/` is the active source of truth for the current project.
- `outputs/` contains generated files, but they are consumed by the interface and Omniverse pipeline, so they are intentionally kept.
- `notebooks/` are retained as proof-of-concept and exploratory material.
- The repository cleanup removed old prototype folders, legacy USD/SysML experiments, old root-level interfaces, and inactive project JSON/SysML variants.

## User Guide

See [docs/USER_GUIDE.md](docs/USER_GUIDE.md) for end-to-end instructions covering the browser interface, first-time Omniverse extension installation, and DES playback visualization.
