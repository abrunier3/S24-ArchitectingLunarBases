# S24 — SysML v2 → JSON → USD Pipeline (Digital Model Builder)

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
  Persistent “model database” where generated assets and large datasets live.

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
