# S24 Lunar Assets — CAD Model Registry

This repository stores all CAD models (.step files) and their SysML metadata for the S24 lunar base DEE pipeline.

---

## 📋 How to register a new CAD model

### 1. Push your `.step` file

Place your file in the appropriate subfolder under `models/`:

```
models/
  assembly.sysml        ← shared assembly metadata (all parts)
  HabitationModule/
    HabitationModule.step
  ISRUPlant/
    ISRUPlant.step
```

### 2. Open the Assembly Builder

👉 **[Open Assembly Builder](https://abrunier3.github.io/S24-ArchitectingLunarBases/assembly_builder.html?assembly=https://raw.githubusercontent.com/abrunier3/S24-ArchitectingLunarBases/main/database/sysml/assembly.sysml)**

> The tool will automatically load the current `database/sysml/assembly.sysml` from this repo.

### 3. Fill in your part's metadata

- Click on your part's node in the tree (or create it with **+ Node**)
- Fill in the dimensions, position, orientation, material, and any custom attributes
- Click **💾 Save Changes**

### 4. Download and commit

- Click **⬇ Download** to get the updated `assembly.sysml`
- Commit it to `database/sysml/assembly.sysml`

```bash
git add database/sysml/assembly.sysml
git commit -m "feat: add metadata for <YourPartName>"
git push
```

---

## 🗂 Repository structure

```
models/
  assembly.sysml          ← single source of truth for all part metadata
  <PartName>/
    <PartName>.step        ← CAD geometry
```

---

## 📄 Generate SysML for a single part

If you need to generate a standalone `.sysml` file for a single part (without adding it to the assembly), use the single-part form:

👉 **[Open Single Part Form](https://abrunier3.github.io/S24-ArchitectingLunarBases/sysml_generator.html)**

---

## 🔧 Assembly Builder features

- Load existing `assembly.sysml` from GitHub automatically
- Add, rename, delete, and reorder nodes via drag & drop
- Edit metadata for any part directly in the tree
- Import external `.sysml` files via drag & drop or paste
- Preview, copy, or download the generated SysML

---

*Maintained by the S24 DEE pipeline — any questions, open an Issue.*
