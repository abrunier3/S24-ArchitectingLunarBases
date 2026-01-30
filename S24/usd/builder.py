from __future__ import annotations

import os
from typing import Dict, Optional

from S24.jsonio.vetting import VettedPart

from .utils import ensure_can_write
from .geometry import author_box_geom_layer
from .materials import author_preview_material_layer
from .components import author_component_layer
from .assembly import author_assembly_scene


class USDBuilder:
    """
    Build USD assets (geoms, mats, components) and an assembly scene.

    All outputs go under database/ by default:
      database/assets/{geoms,mats,components}
      database/scenes
    """

    def __init__(
        self,
        by_name: Dict[str, VettedPart],
        *,
        database_dir: str = "database",
        overwrite: bool = True,
        use_paths_from_vetted: bool = False,
    ) -> None:
        self.by_name = by_name
        self.overwrite = overwrite
        self.use_paths_from_vetted = use_paths_from_vetted

        self.database_dir = database_dir
        self.assets_dir = os.path.join(database_dir, "assets")
        self.geoms_dir = os.path.join(self.assets_dir, "geoms")
        self.mats_dir = os.path.join(self.assets_dir, "mats")
        self.comps_dir = os.path.join(self.assets_dir, "components")
        self.scenes_dir = os.path.join(database_dir, "scenes")

        os.makedirs(self.geoms_dir, exist_ok=True)
        os.makedirs(self.mats_dir, exist_ok=True)
        os.makedirs(self.comps_dir, exist_ok=True)
        os.makedirs(self.scenes_dir, exist_ok=True)

    def geom_path_for(self, vp: VettedPart) -> str:
        if self.use_paths_from_vetted:
            return vp.geom_path
        return os.path.join(self.geoms_dir, f"{vp.name}_geom.usda")

    def mat_path_for(self, vp: VettedPart) -> str:
        if self.use_paths_from_vetted:
            return vp.material_path
        return os.path.join(self.mats_dir, f"{vp.name}_mat.usda")

    def comp_path_for(self, vp: VettedPart) -> str:
        return os.path.join(self.comps_dir, f"{vp.name}.usda")

    def material_name_for(self, vp: VettedPart) -> str:
        return f"{vp.name}_Material"

    def build_geometry(self, vp: VettedPart) -> str:
        geom_path = self.geom_path_for(vp)
        ensure_can_write(geom_path, overwrite=self.overwrite)
        prim_name = f"{vp.name}_Geom"
        return author_box_geom_layer(
            geom_path=geom_path,
            prim_name=prim_name,
            dims_m=vp.dims_m,
            meters_per_unit=vp.meters_per_unit,
            up_axis=vp.up_axis,
        )

    def build_material(self, vp: VettedPart) -> str:
        mat_path = self.mat_path_for(vp)
        ensure_can_write(mat_path, overwrite=self.overwrite)
        return author_preview_material_layer(
            mat_path=mat_path,
            material_name=self.material_name_for(vp),
            meters_per_unit=vp.meters_per_unit,
            up_axis=vp.up_axis,
        )

    def build_component(self, vp: VettedPart, *, geom_path: str, mat_path: str) -> str:
        comp_path = self.comp_path_for(vp)
        ensure_can_write(comp_path, overwrite=self.overwrite)

        geom_prim_path = f"/{vp.name}_Geom"
        material_prim_path = f"/Materials/{self.material_name_for(vp)}"

        raw_attrs = vp.raw.get("attributes", {})

        return author_component_layer(
            comp_path=comp_path,
            part_name=vp.name,
            uid=vp.uid,
            ptype=vp.ptype,
            dims_m=vp.dims_m,
            meters_per_unit=vp.meters_per_unit,
            up_axis=vp.up_axis,
            raw_attributes=raw_attrs,
            geom_layer_path=geom_path,
            geom_prim_path=geom_prim_path,
            mat_layer_path=mat_path,
            material_prim_path=material_prim_path,
        )

    def build_all_parts(self) -> Dict[str, Dict[str, str]]:
        outputs: Dict[str, Dict[str, str]] = {}
        for name, vp in self.by_name.items():
            geom = self.build_geometry(vp)
            mat = self.build_material(vp)
            comp = self.build_component(vp, geom_path=geom, mat_path=mat)
            outputs[name] = {"geom": geom, "mat": mat, "component": comp}
        return outputs

    def write_assembly_scene(
        self,
        *,
        scene_name: str = "assembly.usda",
        root_name: Optional[str] = None,
        include_root_as_instance: bool = True,
        instanceable: bool = False,
        debug_refs: bool = False,
    ) -> str:
        ensure_can_write(self.scenes_dir, overwrite=True)  # ensures dirs exist

        if root_name is None:
            roots = [n for n, vp in self.by_name.items() if vp.parent is None]
            if not roots:
                raise ValueError("No root found.")
            root_name = roots[0]

        root_part = self.by_name[root_name]
        scene_path = os.path.join(self.scenes_dir, scene_name)
        ensure_can_write(scene_path, overwrite=self.overwrite)

        return author_assembly_scene(
            scene_path=scene_path,
            root_name=root_name,
            by_name=self.by_name,
            comp_path_for=self.comp_path_for,
            meters_per_unit=float(root_part.meters_per_unit),
            up_axis=str(root_part.up_axis),
            include_root_as_instance=include_root_as_instance,
            instanceable=instanceable,
            debug_refs=debug_refs,
        )
