from __future__ import annotations

from pathlib import Path


def scenario_slug_from_cad_path(cad_path: str) -> str:
    """Return the scenario folder from a scenario-scoped CAD path.

    The older ``cad_models/<module>/<file>`` layout remains readable as the
    ECLIPSE reference scenario during the migration.
    """

    parts = Path(cad_path).as_posix().split("/")
    try:
        index = parts.index("cad_models")
    except ValueError:
        return "ECLIPSE_Project"

    if len(parts) > index + 3:
        return parts[index + 1]
    return "ECLIPSE_Project"
