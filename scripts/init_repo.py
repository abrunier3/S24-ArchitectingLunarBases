#!/usr/bin/env python3
"""
Repository initialization script for GC-Sysml-OpenUSD.

Creates the full project structure for:
- S24 Python package
- database assets and models
- notebooks and scripts

Safe to run multiple times.
Will NOT overwrite existing files.
"""

from pathlib import Path


# ----------------------------
# Helpers
# ----------------------------

def mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def touch(path: Path) -> None:
    if not path.exists():
        path.touch()


# ----------------------------
# Main structure creation
# ----------------------------

def main() -> None:
    root = Path.cwd()

    # =========================
    # Python package: S24
    # =========================
    s24 = root / "S24"
    mkdir(s24)
    touch(s24 / "__init__.py")

    # --- sysml ---
    sysml = s24 / "sysml"
    mkdir(sysml)
    touch(sysml / "__init__.py")
    touch(sysml / "ast.py")
    touch(sysml / "parser.py")
    touch(sysml / "evaluator.py")
    touch(sysml / "units.py")
    touch(sysml / "exporter.py")

    # --- jsonio ---
    jsonio = s24 / "jsonio"
    mkdir(jsonio)
    touch(jsonio / "__init__.py")
    touch(jsonio / "errors.py")
    touch(jsonio / "loader.py")
    touch(jsonio / "vetting.py")

    # --- usd ---
    usd = s24 / "usd"
    mkdir(usd)
    touch(usd / "__init__.py")
    touch(usd / "utils.py")
    touch(usd / "geometry.py")
    touch(usd / "materials.py")
    touch(usd / "components.py")
    touch(usd / "assembly.py")
    touch(usd / "builder.py")

    # --- pipeline ---
    pipeline = s24 / "pipeline"
    mkdir(pipeline)
    touch(pipeline / "__init__.py")
    touch(pipeline / "build_habitation.py")

    # --- CLI ---
    touch(s24 / "cli.py")

    # =========================
    # Database
    # =========================
    database = root / "database"
    mkdir(database)

    assets = database / "assets"
    mkdir(assets)
    mkdir(assets / "geoms")
    mkdir(assets / "mats")
    mkdir(assets / "components")

    mkdir(database / "scenes")
    mkdir(database / "sysml_models")
    mkdir(database / "system_dynamics")
    mkdir(database / "lunar_topography")

    # =========================
    # Notebooks
    # =========================
    notebooks = root / "notebooks"
    mkdir(notebooks)
    touch(notebooks / "case_study.ipynb")

    # =========================
    # Scripts
    # =========================
    scripts = root / "scripts"
    mkdir(scripts)
    touch(scripts / "__init__.py")

    print("✅ Repository structure initialized successfully.")


if __name__ == "__main__":
    main()
