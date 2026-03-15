# S24 Lunar Assets — CAD Model Registry

This repository stores all CAD models (.step files) and their SysML metadata for the S24 lunar base DEE pipeline.

---

## 🚀 Mission Control Hub

UPDATED ---- 👉 **[Open LSP-1 DEE ]([https://abrunier3.github.io/S24-ArchitectingLunarBases/](https://github.com/abrunier3/S24-ArchitectingLunarBases/blob/main/Lunar%20Spaceport-1%20Digital%20Engineering%20Ecosystem%20-%20HTML%20Stakeholder%20Interface.html))**
OBSOLETE ---- 👉 **[Open Mission Control Hub](https://abrunier3.github.io/S24-ArchitectingLunarBases/)**

The hub gives access to both tools:
- **Assembly Builder** — register STEP files, define metadata, generate SysML v2 for the USD pipeline
- **DES Simulation Explorer** — load simulation logs and visualize time-series data

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
```

---

## 🔧 Tools

| Tool | URL |
|------|-----|
| Mission Control Hub | https://abrunier3.github.io/S24-ArchitectingLunarBases/ |
| Assembly Builder | https://abrunier3.github.io/S24-ArchitectingLunarBases/assembly_builder.html |
| DES Simulation Explorer | https://abrunier3.github.io/S24-ArchitectingLunarBases/lunar_spaceport_plotter.html |
| Single Part Form | https://abrunier3.github.io/S24-ArchitectingLunarBases/sysml_generator.html |
| Unified Workbench | https://abrunier3.github.io/S24-ArchitectingLunarBases/unified_mission_workbench_r5.html |

---

*Maintained by the S24 DEE pipeline — any questions, open an Issue.*
