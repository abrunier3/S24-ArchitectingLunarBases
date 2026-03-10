from pathlib import Path
import subprocess
import sys


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    python_exe = sys.executable

    cmd = [
        python_exe,
        "-m",
        "S24.cli",
        "build",
        "--sysml", str(repo_root / "database" / "sysml" / "assembly.sysml"),
        "--json", str(repo_root / "database" / "json" / "assembly.json"),
        "--materials-sysml", str(repo_root / "database" / "sysml" / "materials.sysml"),
        "--materials-json", str(repo_root / "database" / "json" / "materials.json"),
        "--assets", str(repo_root / "database" / "assets"),
        "--scene", str(repo_root / "database" / "scenes" / "Assembly.usda"),
        "--root-all",
    ]

    print("Running local build...")
    print(" ".join(f'"{c}"' if " " in c else c for c in cmd))
    print()

    result = subprocess.run(cmd, cwd=repo_root)

    print()
    if result.returncode == 0:
        print("Build finished successfully.")
        print(f"Assembly scene: {repo_root / 'database' / 'scenes' / 'Assembly.usda'}")
    else:
        print(f"Build failed with exit code {result.returncode}")

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
