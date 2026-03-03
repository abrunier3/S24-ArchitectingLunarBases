from pathlib import Path

# Root folder of your project (script should live in repo root)
ROOT = Path(__file__).parent

# Target web folder
WEB_DIR = ROOT / "web"

# Desired structure
STRUCTURE = {
    "index.html": None,  # You can rename to assembly_builder.html if needed
    "styles": [
        "base.css",
        "layout.css",
        "components.css",
        "app.css",
    ],
    "js": [
        "app.js",
        "state.js",
        "tree.js",
        "sysml-parser.js",
        "sysml-generator.js",
        "github-api.js",
        "pipeline.js",
        "form.js",
        "utils.js",
    ],
    "components": [
        "modals.js",
        "notifications.js",
    ],
}


def create_file(path: Path):
    if path.exists():
        print(f"⏭  Skipped (exists): {path}")
    else:
        path.touch()
        print(f"✅ Created file: {path}")


def main():
    print("\n--- Scaffolding Web Structure ---\n")

    # Ensure web directory exists
    WEB_DIR.mkdir(exist_ok=True)
    print(f"📁 Ensured directory: {WEB_DIR}")

    for key, value in STRUCTURE.items():

        # Case 1: Root-level file (like index.html)
        if value is None:
            create_file(WEB_DIR / key)

        # Case 2: Folder with files
        else:
            folder_path = WEB_DIR / key
            folder_path.mkdir(exist_ok=True)
            print(f"📁 Ensured directory: {folder_path}")

            for filename in value:
                create_file(folder_path / filename)

    print("\n✨ Done.\n")


if __name__ == "__main__":
    main()