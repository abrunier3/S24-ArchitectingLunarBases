# S24 Lunar Assets — CAD Model Registry

This repository stores all CAD models (.step files) and their SysML metadata for the S24 lunar base DEE pipeline.

---

## 🚀 Mission Control Hub

UPDATED 3-15-2026 ---- 👉 **[Open LSP-1 DEE ](https://abrunier3.github.io/S24-ArchitectingLunarBases/)**

The hub gives access to both tools:
- **Assembly Builder** — register STEP files, define metadata, generate SysML v2 for the USD pipeline
- **DES Simulation Explorer** — load simulation logs and visualize time-series data

---

## 🛰 S24 Pipeline Interface (NEW)

👉 **[Open ECLIPSE DEE Pipeline](https://abrunier3.github.io/S24-ArchitectingLunarBases/index.html)**

The full end-to-end pipeline interface. Covers:
- **Step 1** — Build Requirements (MSOSA)
- **Step 2** — Mission Network Activation — toggle active nodes and trigger `run_connectivity_graph()` via GitHub Actions
- **Step 3** — Model Submission — upload CAD models and review SysML metadata per module
- **Step 4** — DES Tradespace — set simulation parameters and run `run_scenario()`
- **Step 5** — Simulator — link to Omniverse scene

---

## 📋 How to register a new CAD model

### 1. Push your `.step` file

Place your file in the appropriate subfolder under `models/`:

```
models/
  HabitationModule/
    HabitationModule.step
  ISRUPlant/
    ISRUPlant.step
```

### 2. Open the Assembly Builder

👉 **[Open Assembly Builder directly](https://abrunier3.github.io/S24-ArchitectingLunarBases/assembly_builder.html?assembly=https://raw.githubusercontent.com/abrunier3/S24-ArchitectingLunarBases/main/database/sysml/assembly.sysml)**

> The tool will automatically load the current `database/sysml/assembly.sysml` from this repo.

### 3. Fill in your part's metadata

- Click on your part's node in the tree (or create it with **+ Node**)
- Fill in the dimensions, position, orientation, material, and any custom attributes
- Click **💾 Save Changes**

### 4. Publish or download

- Click **☁ Publish to GitHub** to push directly to `database/sysml/assembly.sysml`
- Or click **⬇ Download** and commit manually:

```bash
git add database/sysml/assembly.sysml
git commit -m "feat: add metadata for <YourPartName>"
git push
```

---

## 🗂 Repository structure

```
models/
  <PartName>/
    <PartName>.step          ← CAD geometry
database/
  sysml/
    assembly.sysml           ← single source of truth for all part metadata
    materials.sysml
  json/                      ← generated JSON (pipeline output)
  scenes/                    ← generated USD scenes (pipeline output)
  assets/                    ← generated USD assets (pipeline output)
outputs/
  graph.json                 ← connectivity graph output (Step 2, written by GitHub Actions)
  des_results.json           ← DES simulation output (Step 4, written by GitHub Actions)
.github/
  workflows/
    build_pipeline.yml       ← SysML → JSON → USD
    deploy_pages.yml         ← Deploy GitHub Pages
    step_detected.yml        ← Auto-register new STEP files
    run_graph.yml            ← Step 2: run_connectivity_graph() on demand
```

---

## 🔧 Tools

| Tool | URL |
|------|-----|
| **ECLIPSE DEE Pipeline** | https://abrunier3.github.io/S24-ArchitectingLunarBases/index.html |
| Mission Control Hub | https://abrunier3.github.io/S24-ArchitectingLunarBases/ |
| Assembly Builder | https://abrunier3.github.io/S24-ArchitectingLunarBases/assembly_builder.html |
| DES Simulation Explorer | https://abrunier3.github.io/S24-ArchitectingLunarBases/lunar_spaceport_plotter.html |
| Single Part Form | https://abrunier3.github.io/S24-ArchitectingLunarBases/sysml_generator.html |
| Unified Workbench | https://abrunier3.github.io/S24-ArchitectingLunarBases/unified_mission_workbench_r5.html |

---

*Maintained by the S24 DEE pipeline — any questions, open an Issue.*

# S24 — SysML v2 → JSON → USD Pipeline (Digital Model Builder) (Framework Summary v1)

S24 is a **Python package** that turns a **SysML v2 system model** into:

1. a **flat JSON** representation (parts + hierarchy + evaluated numeric attributes), then  
2. a set of **USD assets** (geometry / materials / components), then  
3. a **USD assembly scene** that instantiates the full system tree using USD references.

The scope is:
- **SysML → JSON**: parse parts, evaluate expressions safely, convert known units, preserve metadata.
- **JSON vetting**: validate schema, fix parent/child consistency, and ensure a valid acyclic tree.
- **USD authoring**: generate geometry + materials + component layers, then assemble a scene.

This repository is meant to be a clean foundation for a broader digital ecosystem (e.g., adding CAD meshes, system dynamics, ISRU solvers, surrogates).

---

## Repository 

- **`S24/`**  
  The Python package. All core code lives here.

- **`database/`**  
  Persistent "model database" where generated assets and large datasets live.

- **`notebooks/`**  
  Demonstrations and case studies. The main one is `case_study.ipynb`.

- **`scripts/`**  
  Utilities (e.g., repo initializer script).

---

## Key Outputs (What S24 Produces)

### JSON
A list of parts where each part has:
- identity (`id`, `name`, `type`)
- hierarchy (`parent`, `children`)
- dimensions (`dimensions`)
- numeric evaluated attributes (`attributes`)
- string metadata (`metadata`) like geometry/material paths

### USD
A database of USD layers:
- geometry layers (`*_geom.usda`)
- material layers (`*_mat.usda`)
- component layers (`<Part>.usda`)
- an assembly scene (`.usda`) that references components under `/World/...`

---

## Minimum Requirements

- Python **3.10+**
- `pxr` (USD Python bindings) importable in the same Python environment as your notebook/script

   ```bash
   python -m pip install -e .
   ```
