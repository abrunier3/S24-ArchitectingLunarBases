from pathlib import Path
import shutil

def _find_project_root(start: Path = None) -> Path:
    """
    Finds project root by searching for .git or pyproject.toml.
    Works in both scripts and notebooks.
    """

    if start is None:
        try:
            start = Path(__file__).resolve()   # works in scripts
        except NameError:
            start = Path.cwd()                # fallback for notebooks

    current = start if start.is_dir() else start.parent

    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
        if (parent / "pyproject.toml").exists():
            return parent

    raise RuntimeError("Could not find project root.")


def _resolve_sysml_file(sysml_file: str, SYSML_DIR: Path) -> Path:
    """
    Resolves the SysML file location according to pipeline rules.

    Supports:
    - User uses a sysml file from our database : "{file_name}" or "{file_name}.sysml"
    - User brings in a specific sysml file     : "/some/path/{file_name}" or "/some/path/{file_name}.sysml"
    """

    sysml_path = Path(sysml_file)

    # Ensure .sysml extension 
    if sysml_path.suffix == "":
        sysml_path = sysml_path.with_suffix(".sysml")

    # Case 1: Only filename (no directory) 
    if len(sysml_path.parts) == 1:
        candidate = SYSML_DIR / sysml_path.name

        if candidate.exists():
            return candidate
        else:
            raise FileNotFoundError(
                f"SysML file '{sysml_path.name}' not found in {SYSML_DIR}"
            )

    # Case 2: Path provided 
    else:
        if not sysml_path.exists():
            raise FileNotFoundError(
                f"Provided SysML path does not exist: {sysml_path}"
            )

        destination = SYSML_DIR / sysml_path.name

        # Copy if not already present
        if not destination.exists():
            shutil.copy(sysml_path, destination)

        return destination


def resolve_database_paths(sysml_file: str, use_repo: bool = True):

    # root direcctory 
    if use_repo:
        ROOT = _find_project_root()
    else:
        ROOT = Path.cwd()

    # database directory 
    _database_dir = ROOT / "clean_database"

    # core directories
    SYSML_DIR = _database_dir / "sysml"
    CAD_DIR = _database_dir / "cad_models"
    METADATA_DIR = _database_dir / "metadata"

    # usd directories
    _usd_dir = _database_dir / "usd"

    SCENES_DIR = _usd_dir / "scenes"

    _asset_dir = _usd_dir / "assets"
    COMPONENTS_DIR = _asset_dir / "components"
    GEOM_DIR = _asset_dir / "geoms"
    MATERIAL_DIR = _asset_dir / "material"

    # extra JSON directories
    JSON_DIR = _database_dir / "json"
    JSON_FILE_DIR = JSON_DIR / f"{Path(sysml_file).stem}"
    JSON_ASSETS = JSON_FILE_DIR / "assets"
    JSON_FILE = JSON_FILE_DIR / f"{Path(sysml_file).stem}.json"

    # mkdir all the directories
    all_dirs = [
        SYSML_DIR,
        JSON_DIR,
        CAD_DIR,
        METADATA_DIR,
        _usd_dir,
        SCENES_DIR,
        _asset_dir,
        COMPONENTS_DIR,
        GEOM_DIR,
        MATERIAL_DIR,
        JSON_ASSETS
    ]

    for d in all_dirs:
        d.mkdir(parents=True, exist_ok=True)

    # handling of sysml file
    SYSML_FILE = _resolve_sysml_file(sysml_file, SYSML_DIR)

    return {
        "ROOT"           : ROOT,
        "DATABASE_DIR"   : _database_dir,
        "SYSML_DIR"      : SYSML_DIR,
        "JSON_DIR"       : JSON_DIR,
        "CAD_DIR"        : CAD_DIR,
        "METADATA_DIR"   : METADATA_DIR,
        "USD_DIR"        : _usd_dir,
        "SCENES_DIR"     : SCENES_DIR,
        "ASSET_DIR"      : _asset_dir,
        "COMPONENTS_DIR" : COMPONENTS_DIR,
        "GEOM_DIR"       : GEOM_DIR,
        "MATERIAL_DIR"   : MATERIAL_DIR,
        "SYSML_FILE"     : SYSML_FILE,
        "JSON_FILE"      : JSON_FILE,
        "JSON_ASSETS"    : JSON_ASSETS
    }