# USD

# LunarSpaceport-1 — OpenUSD Pipeline (USD Directory)

This directory contains the **OpenUSD-side pipeline** for LunarSpaceport-1.  
Its purpose is to convert **structured component descriptions (canonical JSON)** into a scalable set of **USD assets** (geometry/material/component layers) and then **compose assemblies** (scenes) by instancing and positioning components according to a vetted hierarchy.

The current focus is strictly the **USD representation and composition workflow** (SysML v2 authoring + SysML→JSON conversion are treated as upstream inputs).

---

## What this code does

### 1) Input: Canonical part JSON
We consume JSON that represents **parts** (components) and their relationships:

- Identity: `name`, `id`, `type`
- Spatial: `dims_m`, `metersPerUnit`, `upAxis`, and optional translation `X/Y/Z`
- Engineering attributes: arbitrary scalar properties (pressure, mass, capacity, etc.)
- Metadata paths: where geometry/material layers live (optional policy—either supplied or generated)
- Hierarchy: `parent` and/or `children` to form an assembly tree

This JSON is treated as the **contract** between SysML v2 and OpenUSD.

---

### 2) Vetting / normalization (JSON “compiler front-end”)
Before writing any USD, the JSON is **validated and normalized** to avoid silent failures later.

The vetting logic acts like a compiler front-end in three steps:

**Pass 1 — Structural validation**
- Each element must be a dict.
- Required keys exist (`name`, `id`, `dimensions`, `metadata`, etc.).
- Types are checked (numbers, strings, lists of correct length).
- Basic semantic checks (e.g., dimensions must be positive).
- Produces a typed internal representation: `VettedPart`.

**Pass 2 — Hierarchy reconciliation**
- Ensures referenced parents/children exist.
- Reconciles inconsistencies bidirectionally:
  - If a child declares `parent`, ensure the parent lists it in `children`.
  - If a parent lists `children`, ensure each child points back via `parent`.
- Detects contradictions (a child cannot have two different parents).

**Pass 3 — Graph validity**
- Detects cycles using DFS (e.g., A → B → C → A).
- Ensures at least one root exists.
- (Optional) ensures everything is reachable under a root.

The output of vetting is a dictionary:
- `by_name: Dict[str, VettedPart]`
- Keyed by unique `part.name` for fast lookups during USD writing and composition.

---

### 3) USD asset generation (per part)
For each vetted part, the pipeline generates **three USD layers**:

#### A) Geometry Layer (`assets/geoms/<PartName>_geom.usda`)
A pure geometry file containing a single mesh prim:
- `/<PartName>_Geom` (UsdGeom.Mesh)

Currently, geometry is generated as a **rectangular prism** using `dims_m`.
Later, this can be replaced by:
- Referencing external meshes
- Loading CAD-derived meshes
- Procedural geometry generation
- Variant sets (LODs, manufacturing variants, etc.)

#### B) Material Layer (`assets/mats/<PartName>_mat.usda`)
A minimal shading file containing:
- `/Materials/<MaterialName>` (UsdShade.Material)
- `/Materials/<MaterialName>/PreviewSurface` (UsdShade.Shader, UsdPreviewSurface)

This is currently a lightweight “preview” material for sanity-check visualization.
Later, this can expand into:
- MDL/MaterialX workflows
- Textures
- Material libraries and shared references

#### C) Component Layer (`assets/components/<PartName>.usda`)
The component file is the **authoritative “component definition”**. It contains:
- `/<PartName>` (UsdGeom.Xform) as the **root prim**
- `/<PartName>/geom` (UsdGeom.Mesh) that **references** the geometry layer
- `/<PartName>/materials` (UsdGeom.Scope) that **references** the material layer
- A binding from material to geometry where possible

It also authors part-specific data as **USD attributes**:
- `asset:id`, `asset:type`
- `spatial:dims_m`, `spatial:metersPerUnit`, `spatial:upAxis`
- `attr:<key>` for scalar engineering attributes

Important note:  
USD has a strict notion of **metadata keys** (registered keys). For most engineering values, we use **attributes** (safe + queryable) rather than `prim.SetMetadata(...)`.

---

### 4) Assembly scene composition (scene layer)
Once component files exist, we generate an assembly scene that composes the system by referencing components into a scene graph:

- `/World` (UsdGeom.Xform)
- `/World/<RootAssembly>` (UsdGeom.Xform)
- `/World/<RootAssembly>/<Child>/<Grandchild>/...`

Each placed prim:
- Has a **translate op** taken from `dimensions.X/Y/Z` in JSON
- Adds a **reference** to the corresponding component file:
  - `assets/components/<PartName>.usda` at `/<PartName>` inside that file
- Can optionally be marked `instanceable=True` for repeated components

This stage is the “system integration view” and should scale to large system trees.

---

## What this offers (capabilities)

✅ Deterministic generation of USD assets from JSON  
✅ Strong validation to catch hierarchy and schema issues early  
✅ Separation of concerns:
- geometry authored once
- materials authored once
- components reference geometry/material
- scenes reference components  
✅ Composition-friendly structure aligned with OpenUSD best practices  
✅ Extensible architecture to support:
- instancing
- variants
- shared libraries
- multi-level assemblies
- linking to SysML traceability later

---

## Minimal usage example

```python
from lsp_usd.vetting.vetting import VettingProc
from lsp_usd.usd.builder import USDBuilder

model = VettingProc(file="data/partner_json/habmod.json")
by_name = model.by_name

builder = USDBuilder(by_name, assets_dir="assets", overwrite=True)
builder.build_all_parts()

scene_path = builder.write_assembly_scene(
    scene_path="scenes/HabitationAssembly.usda",
    root_name="HabitationModule",
    instanceable=False,
    include_root_as_instance=True,
)

print("Wrote scene:", scene_path)
