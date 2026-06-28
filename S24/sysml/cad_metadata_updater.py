from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any


AUTO_BLOCK_RE = re.compile(
    r"\n\s*// BEGIN AUTO CAD METADATA: (?P<name>\w+)\n"
    r".*?"
    r"\n\s*// END AUTO CAD METADATA: (?P=name)\n",
    re.DOTALL,
)


def _format_number(value: float) -> str:
    if not math.isfinite(value):
        return "0"
    return f"{value:.12g}"


def _find_part_block(text: str, part_name: str) -> tuple[int, int, str] | None:
    match = re.search(rf"(?m)^(?P<indent>\s*)part\s+{re.escape(part_name)}\s*\{{", text)
    if not match:
        return None

    depth = 0
    for index in range(match.start(), len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return match.start(), index + 1, match.group("indent")
    return None


def _rotate_xyz(point: list[float], rotate_deg: list[float]) -> list[float]:
    x, y, z = [float(value) for value in point]
    rx, ry, rz = [math.radians(float(value or 0.0)) for value in rotate_deg]

    cy, sy = math.cos(rx), math.sin(rx)
    y, z = y * cy - z * sy, y * sy + z * cy

    cy, sy = math.cos(ry), math.sin(ry)
    x, z = x * cy + z * sy, -x * sy + z * cy

    cy, sy = math.cos(rz), math.sin(rz)
    x, y = x * cy - y * sy, x * sy + y * cy
    return [x, y, z]


def _transform_center_of_mass(
    center_m: list[float],
    *,
    normalization: dict[str, Any],
) -> list[float]:
    scale = normalization.get("scale") or [1.0, 1.0, 1.0]
    rotate_xyz = normalization.get("rotate_xyz") or [0.0, 0.0, 0.0]
    translate = normalization.get("translate") or [0.0, 0.0, 0.0]

    scaled = [float(center_m[i]) * float(scale[i]) for i in range(3)]
    rotated = _rotate_xyz(scaled, rotate_xyz)
    return [rotated[i] + float(translate[i]) for i in range(3)]


def _physical_metadata_from_preview(
    preview_meta: dict[str, Any],
    *,
    cad_path: str | None = None,
) -> dict[str, Any] | None:
    source_metadata = preview_meta.get("source_metadata") or {}
    geometry = source_metadata.get("geometry") or {}
    if geometry.get("extraction_status") != "success":
        if cad_path:
            return _physical_metadata_from_usd(cad_path)
        return None
    return geometry


def _physical_metadata_from_usd(cad_path: str) -> dict[str, Any] | None:
    try:
        from pxr import Usd, UsdGeom
        from S24.cad.convert_workflow import (
            _actual_usd_path,
            _extract_meshes,
            _extract_usd_geometry_properties,
        )
    except ImportError as exc:
        print(f"[CAD] Could not import USD mesh extractor for {cad_path}: {exc}")
        return None

    stage = Usd.Stage.Open(_actual_usd_path(cad_path))
    if not stage:
        print(f"[CAD] Could not open USD for physical metadata: {cad_path}")
        return None

    meters_per_unit = float(UsdGeom.GetStageMetersPerUnit(stage) or 1.0)
    meshes = _extract_meshes(stage, meters_per_unit)
    geometry = _extract_usd_geometry_properties(meshes)
    if geometry.get("extraction_status") != "success":
        print(
            f"[CAD] Could not extract physical metadata from {cad_path}: "
            f"{geometry.get('message', 'unknown reason')}"
        )
        return None
    return geometry


def _build_sysml_attributes(
    *,
    module_name: str,
    asset: dict[str, Any],
    preview_meta: dict[str, Any],
    normalization: dict[str, Any],
    cad_path: str | None = None,
) -> dict[str, Any] | None:
    geometry = _physical_metadata_from_preview(preview_meta, cad_path=cad_path)
    if not geometry:
        return None

    fit_scale = normalization.get("fit_scale") or [1.0, 1.0, 1.0]
    uniform_fit = float(fit_scale[0] or 1.0)
    source_metadata = preview_meta.get("source_metadata") or {}

    attrs: dict[str, Any] = {
        "cadAreaScaleFactor": uniform_fit ** 2,
        "cadLengthScaleFactor": uniform_fit,
        "cadMetadataScaleFactor": uniform_fit,
        "cadVolumeScaleFactor": uniform_fit ** 3,
    }

    source_file = source_metadata.get("file_name") or Path(
        str(preview_meta.get("source_cad_path") or "")
    ).name
    if source_file:
        attrs["cadSourceFile"] = source_file

    cad_format = source_metadata.get("cad_format")
    if cad_format:
        attrs["cadFormat"] = str(cad_format).upper()

    if "volume_m3" in geometry:
        attrs["cadSourceVolumeM3"] = float(geometry["volume_m3"])
        attrs["cadVolumeM3"] = float(geometry["volume_m3"]) * (uniform_fit ** 3)

    if "surface_area_m2" in geometry:
        attrs["cadSourceSurfaceAreaM2"] = float(geometry["surface_area_m2"])
        attrs["cadSurfaceAreaM2"] = float(geometry["surface_area_m2"]) * (uniform_fit ** 2)

    center = geometry.get("center_of_mass_m")
    if isinstance(center, list) and len(center) == 3:
        attrs["cadSourceCenterOfMassXM"] = float(center[0])
        attrs["cadSourceCenterOfMassYM"] = float(center[1])
        attrs["cadSourceCenterOfMassZM"] = float(center[2])
        transformed = _transform_center_of_mass(center, normalization=normalization)
        attrs["cadCenterOfMassXM"] = transformed[0]
        attrs["cadCenterOfMassYM"] = transformed[1]
        attrs["cadCenterOfMassZM"] = transformed[2]

    metadata = asset.get("metadata") or {}
    if metadata.get("cadSourceUpAxis"):
        attrs["cadSourceUpAxis"] = str(metadata["cadSourceUpAxis"])
    if metadata.get("cadSourceFrontAxis"):
        attrs["cadSourceFrontAxis"] = str(metadata["cadSourceFrontAxis"])

    return attrs


def _render_block(module_name: str, attrs: dict[str, Any], *, indent: str) -> str:
    child_indent = indent + "    "
    lines = [
        f"{child_indent}// BEGIN AUTO CAD METADATA: {module_name}",
    ]
    for key in sorted(attrs):
        value = attrs[key]
        if isinstance(value, (int, float)):
            lines.append(f"{child_indent}attribute {key} = {_format_number(float(value))};")
        else:
            escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{child_indent}attribute {key} = "{escaped}";')
    lines.append(f"{child_indent}// END AUTO CAD METADATA: {module_name}")
    return "\n".join(lines) + "\n"


def update_sysml_part_metadata(
    *,
    sysml_path: Path,
    module_name: str,
    attrs: dict[str, Any],
) -> bool:
    text = sysml_path.read_text(encoding="utf-8")
    part = _find_part_block(text, module_name)
    if not part:
        return False

    start, end, indent = part
    block_text = text[start:end]
    block_text = AUTO_BLOCK_RE.sub("\n", block_text)
    insert_at = block_text.rfind("\n" + indent + "}")
    if insert_at < 0:
        return False

    auto_block = _render_block(module_name, attrs, indent=indent)
    block_text = block_text[:insert_at] + "\n" + auto_block + block_text[insert_at:]
    sysml_path.write_text(text[:start] + block_text + text[end:], encoding="utf-8")
    return True


def _update_asset_json(asset_path: Path, attrs: dict[str, Any]) -> None:
    asset = json.loads(asset_path.read_text(encoding="utf-8"))
    numeric_attrs = asset.setdefault("attributes", {})
    metadata = asset.setdefault("metadata", {})
    for key, value in attrs.items():
        if isinstance(value, (int, float)):
            numeric_attrs[key] = value
        else:
            metadata[key] = value
    asset_path.write_text(json.dumps(asset, indent=2) + "\n", encoding="utf-8")


def update_cad_metadata_from_previews(
    *,
    sysml_path: Path,
    assets_dir: Path,
    previews_dir: Path,
    repo_root: Path,
) -> int:
    from S24.usd.scene_builder import _cad_normalization

    updated = 0
    for asset_path in sorted(assets_dir.glob("*.json")):
        module_name = asset_path.stem
        try:
            preview_path = previews_dir / f"{module_name}_meta.json"
            if not preview_path.exists():
                continue

            asset = json.loads(asset_path.read_text(encoding="utf-8"))
            preview_meta = json.loads(preview_path.read_text(encoding="utf-8"))
            metadata = asset.get("metadata") or {}
            cad_path = (
                preview_meta.get("usd_path")
                or metadata.get("cadUsdPath")
                or metadata.get("geometryRef")
            )
            if not cad_path:
                print(f"[CAD] Skipping {module_name}: no CAD path found")
                continue

            normalization = _cad_normalization(
                str(cad_path),
                repo_root=repo_root,
                dimensions=asset.get("dimensions"),
                metadata=metadata,
            )
            attrs = _build_sysml_attributes(
                module_name=module_name,
                asset=asset,
                preview_meta=preview_meta,
                normalization=normalization,
                cad_path=str(cad_path),
            )
            if not attrs:
                print(f"[CAD] Skipping {module_name}: no physical CAD metadata available")
                continue

            if update_sysml_part_metadata(
                sysml_path=sysml_path,
                module_name=module_name,
                attrs=attrs,
            ):
                _update_asset_json(asset_path, attrs)
                updated += 1
                print(f"[CAD] Updated SysML CAD metadata for {module_name}")
            else:
                print(f"[CAD] Skipping {module_name}: part not found in SysML")
        except Exception as exc:
            print(f"[CAD] Skipping {module_name}: {type(exc).__name__}: {exc}")

    return updated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Update SysML parts with scaled CAD physical metadata.",
    )
    parser.add_argument("--sysml", default="clean_database/sysml/ECLIPSE_Project.sysml")
    parser.add_argument("--assets-dir", default="clean_database/json/ECLIPSE_Project/assets")
    parser.add_argument("--previews-dir", default="outputs/cad_previews")
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args(argv)

    count = update_cad_metadata_from_previews(
        sysml_path=Path(args.sysml),
        assets_dir=Path(args.assets_dir),
        previews_dir=Path(args.previews_dir),
        repo_root=Path(args.repo_root).resolve(),
    )
    print(f"[CAD] SysML CAD metadata updated for {count} part(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
