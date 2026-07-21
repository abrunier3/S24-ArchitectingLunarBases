import os
import json
import math
import subprocess

import omni.ext
import omni.ui as ui
import omni.timeline


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
EXT_ROOT = os.path.normpath(os.path.join(THIS_DIR, ".."))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))

DEFAULT_MANIFEST_PATH = os.path.join(EXT_ROOT, "data", "manifest.json")
SCENARIO_OUTPUTS_DIR = os.path.join(REPO_ROOT, "outputs", "scenarios")
ROVER_FORWARD_YAW_OFFSET_DEG = -90.0
ROVER_TERRAIN_CLEARANCE_M = 0.0


class LSP1PipelineExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        print("[LSP1 Pipeline] STARTUP")

        self.timeline_sub = None
        self.elapsed_seconds = 0.0
        self.des_data = None
        self.des_log = {}
        self.des_log_times = []
        self.manifest = None
        self.manifest_path = DEFAULT_MANIFEST_PATH
        self.actors = []
        self.is_loaded = False
        self.route_cache = {}
        self.actor_labels = {}
        self.routes_visible = False
        self.show_routes_button = None
        self.scenario_selector = None
        self.scenario_combo = None
        self.scenario_manifest_paths = [None]

        self.window = ui.Window("LSP1 Pipeline", width=520, height=430)

        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label("LSP1 Pipeline")
                self.status = ui.Label("Status: waiting")

                ui.Button("Pull GitHub Omniverse", clicked_fn=self._pull_github)
                ui.Label("Choose Scenario")
                self.scenario_selector = ui.VStack(spacing=4)
                ui.Button("Play", clicked_fn=self._play)
                ui.Button("Pause", clicked_fn=self._pause)
                ui.Button("Reset", clicked_fn=self._reset)
                self.show_routes_button = ui.Button(
                    "Show Routes",
                    clicked_fn=self._toggle_routes,
                )

                self.time_label = ui.Label("Mission Time: --")
                self.des_time_label = ui.Label("DES Playback Time: --")
                self.camera_label = ui.Label("Camera: --")

                ui.Separator()

                self.actor_dashboard = ui.VStack(spacing=4)
                with self.actor_dashboard:
                    ui.Label("Actor telemetry: --")

        self._refresh_scenario_selector()

    def _pull_github(self):
        log_path = os.path.join(REPO_ROOT, "lsp1_git_pull_log.txt")

        def log(message):
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(str(message) + "\n")
            except Exception:
                pass
            print(message)

        try:
            self.status.text = "Status: pulling GitHub..."

            git_folder = os.path.join(REPO_ROOT, ".git")
            if not os.path.exists(git_folder):
                self.status.text = "Status: Git pull failed. Not a git repo."
                log(f"ERROR: .git folder not found at {git_folder}")
                return

            git_candidates = [
                "git",
                r"C:\Program Files\Git\cmd\git.exe",
                r"C:\Program Files\Git\bin\git.exe",
                r"C:\Program Files (x86)\Git\cmd\git.exe",
            ]

            git_exe = None
            for candidate in git_candidates:
                try:
                    result = subprocess.run(
                        [candidate, "--version"],
                        capture_output=True,
                        text=True,
                        shell=False
                    )
                    if result.returncode == 0:
                        git_exe = candidate
                        break
                except Exception:
                    pass

            if git_exe is None:
                self.status.text = "Status: Git not found by Omniverse."
                log("ERROR: Git executable not found.")
                return

            pull_result = subprocess.run(
                [git_exe, "-C", REPO_ROOT, "pull", "origin", "cleanup-branch"],
                capture_output=True,
                text=True,
                shell=False
            )

            log("----- git pull -----")
            log(f"Return code: {pull_result.returncode}")
            log(f"STDOUT:\n{pull_result.stdout}")
            log(f"STDERR:\n{pull_result.stderr}")

            if pull_result.returncode == 0:
                self.status.text = "Status: Git pull successful."
                self._refresh_scenario_selector()
            else:
                self.status.text = "Status: Git pull failed. See log."

        except Exception as e:
            self.status.text = f"Status: Git pull error: {e}"
            print("[LSP1 Pipeline] Git pull error:", repr(e))

    def _scenario_manifest_entries(self):
        entries = []
        if not os.path.isdir(SCENARIO_OUTPUTS_DIR):
            return entries

        for scenario_slug in sorted(os.listdir(SCENARIO_OUTPUTS_DIR), key=str.lower):
            manifest_path = os.path.join(
                SCENARIO_OUTPUTS_DIR,
                scenario_slug,
                "omniverse",
                "manifest.json",
            )
            if not os.path.isfile(manifest_path):
                continue

            label = scenario_slug
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                scenario = manifest.get("scenario") or {}
                label = str(scenario.get("name") or scenario.get("slug") or scenario_slug)
            except Exception as exc:
                print("[LSP1 Pipeline] Invalid scenario manifest:", manifest_path, repr(exc))
                continue

            entries.append((label, manifest_path))

        return entries

    def _refresh_scenario_selector(self):
        if not self.scenario_selector:
            return

        entries = self._scenario_manifest_entries()
        self.scenario_manifest_paths = [None] + [path for _, path in entries]

        try:
            self.scenario_selector.clear()
        except Exception:
            pass

        with self.scenario_selector:
            labels = ["Select a scenario to load"] + [label for label, _ in entries]
            self.scenario_combo = ui.ComboBox(0, *labels)
            self.scenario_combo.model.get_item_value_model().add_value_changed_fn(
                self._on_scenario_selected
            )
            if not entries:
                ui.Label("No scenario-specific Omniverse packages found. Run DES first.")

    def _on_scenario_selected(self, model):
        selection = model.as_int
        if selection <= 0 or selection >= len(self.scenario_manifest_paths):
            return

        self._load_all(self.scenario_manifest_paths[selection])

    def _load_all(self, manifest_path=None):
        try:
            self.manifest_path = os.path.normpath(manifest_path or self.manifest_path)
            self.manifest = self._load_manifest(self.manifest_path)
            self.actors = self.manifest.get("actors", [])
            self._build_actor_dashboard()

            scene_path = self._resolve_manifest_path(self.manifest.get("scene_usd"))
            des_path = self._resolve_manifest_path(self.manifest.get("des_log"))
            waypoints_path = self._resolve_manifest_path(self.manifest.get("waypoints_usd"))
            terrain_path = self._get_terrain_path()

            print("[LSP1 Pipeline] REPO_ROOT:", REPO_ROOT)
            print("[LSP1 Pipeline] MANIFEST PATH:", self.manifest_path)
            print("[LSP1 Pipeline] SCENE PATH:", scene_path)
            print("[LSP1 Pipeline] SCENE exists:", os.path.exists(scene_path))
            print("[LSP1 Pipeline] DES PATH:", des_path)
            print("[LSP1 Pipeline] DES exists:", os.path.exists(des_path))
            print("[LSP1 Pipeline] WAYPOINTS PATH:", waypoints_path)
            print("[LSP1 Pipeline] WAYPOINTS exists:", os.path.exists(waypoints_path))
            print("[LSP1 Pipeline] TERRAIN PATH:", terrain_path)
            print("[LSP1 Pipeline] TERRAIN exists:", os.path.exists(terrain_path) if terrain_path else False)

            with open(des_path, "r", encoding="utf-8") as f:
                self.des_data = json.load(f)

            if self.des_data.get("status") == "error":
                error_text = "; ".join(self.des_data.get("errors") or ["unknown DES error"])
                raise ValueError(f"DES run failed: {error_text}")

            self._normalize_des_log()
            self._open_scene_stage(scene_path)
            self._ensure_actor_prims()
            self._ensure_module_instance_prims()
            self._load_waypoints_under_world()
            self._load_terrain_model()
            self._apply_module_terrain_projection()
            self._apply_default_rover_terrain_poses()
            self._draw_route_slope_debug()
            self.routes_visible = False
            self._set_route_slope_debug_visible(False)
            self._update_show_routes_button()

            self.elapsed_seconds = 0.0
            self.is_loaded = True
            self.route_cache = {}

            self._ensure_timeline()
            self._update_all(0.0)

            route_projection = (
                self.manifest.get("terrain_projection", {})
                .get("routes", {})
            )
            warning_count = int(route_projection.get("warning_count", 0) or 0)
            caution_count = int(route_projection.get("caution_count", 0) or 0)
            self.status.text = (
                "Status: loaded scenario "
                f"{(self.manifest.get('scenario') or {}).get('name', 'unnamed')}"
                " + scene + DES + waypoints"
                f" | slope warnings: {warning_count}, cautions: {caution_count}"
            )

        except Exception as e:
            self.status.text = f"Status: load failed: {e}"
            print("[LSP1 Pipeline] Load failed:", repr(e))

    def _load_manifest(self, manifest_path=None):
        manifest_path = manifest_path or self.manifest_path
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        if "actors" not in manifest:
            raise ValueError("Visualization manifest missing required key: actors")

        return manifest

    def _resolve_manifest_path(self, rel_or_abs_path):
        if not rel_or_abs_path:
            return None

        if os.path.isabs(rel_or_abs_path):
            return os.path.normpath(rel_or_abs_path)

        base_dir = os.path.dirname(self.manifest_path)
        return os.path.normpath(os.path.join(base_dir, rel_or_abs_path))

    def _get_terrain_path(self):
        terrain = self.manifest.get("terrain") or {}
        return self._resolve_manifest_path(terrain.get("usd"))

    def _normalize_des_log(self):
        raw_log = self.des_data.get("log", self.des_data)

        if not isinstance(raw_log, dict):
            raise ValueError("DES data must be a dict or contain a dict under 'log'")

        self.des_log = raw_log
        # Current DES results wrap the time-indexed telemetry in ``log`` and
        # keep run metadata (for example ``written_at`` and ``status``) at the
        # root.  Older results used the time-indexed dictionary directly.
        # Accept both formats and ignore any non-time keys defensively.
        time_entries = []
        for key in self.des_log:
            try:
                time_entries.append((float(key), key))
            except (TypeError, ValueError):
                continue

        if not time_entries:
            raise ValueError("DES log contains no time-indexed telemetry entries")

        self.des_log_times = sorted(time_entries)

    def _build_actor_dashboard(self):
        self.actor_labels = {}
        try:
            self.actor_dashboard.clear()
        except Exception:
            pass

        with self.actor_dashboard:
            for actor in self.actors:
                actor_id = actor.get("id", "")
                label = actor.get("label", actor_id)
                ui.Label(label)

                fields = actor.get("dashboard_fields", [])
                field_labels = {}

                for field in fields:
                    key = field.get("key")
                    field_label = field.get("label", key)
                    field_labels[key] = ui.Label(f"  {field_label}: --")

                self.actor_labels[actor_id] = field_labels

    def _open_scene_stage(self, scene_path):
        if not scene_path:
            return

        if not os.path.exists(scene_path):
            raise FileNotFoundError(f"Scene USD not found: {scene_path}")

        import omni.usd

        omni.usd.get_context().open_stage(scene_path.replace("\\", "/"))

    def _ensure_actor_prims(self):
        """Create one referenced scene prim for every simulated rover instance."""
        try:
            import omni.usd
            from pxr import UsdGeom

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            for actor in self.actors:
                prim_path = actor.get("prim_path")
                source_path = actor.get("source_prim_path", prim_path)
                if not prim_path or not source_path or prim_path == source_path:
                    continue

                source_prim = stage.GetPrimAtPath(source_path)
                if not source_prim or not source_prim.IsValid():
                    print(
                        "[LSP1 Pipeline] Cannot create actor instance; source prim missing:",
                        source_path,
                    )
                    continue

                existing = stage.GetPrimAtPath(prim_path)
                if existing and existing.IsValid():
                    stage.RemovePrim(prim_path)

                actor_xform = UsdGeom.Xform.Define(stage, prim_path)
                actor_xform.GetPrim().GetReferences().AddInternalReference(source_path)
                print(
                    "[LSP1 Pipeline] Created actor instance:",
                    prim_path,
                    "from",
                    source_path,
                )
        except Exception as exc:
            print("[LSP1 Pipeline] Actor instance creation failed:", repr(exc))

    def _ensure_module_instance_prims(self):
        """Reference the source CAD prim for each additional placed instance."""
        try:
            import omni.usd
            from pxr import UsdGeom

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return
            modules = (
                self.manifest.get("terrain_projection", {})
                .get("modules", {})
                .get("modules", {})
            )
            for module_name, info in modules.items():
                prim_path = info.get("prim_path", f"/World/{module_name}")
                source_path = f"/World/{info.get('source_module', module_name)}"
                if prim_path == source_path:
                    continue
                source_prim = stage.GetPrimAtPath(source_path)
                if not source_prim or not source_prim.IsValid():
                    print("[LSP1 Pipeline] Module source prim missing:", source_path)
                    continue
                existing = stage.GetPrimAtPath(prim_path)
                if existing and existing.IsValid():
                    stage.RemovePrim(prim_path)
                instance_xform = UsdGeom.Xform.Define(stage, prim_path)
                instance_xform.GetPrim().GetReferences().AddInternalReference(source_path)
                print("[LSP1 Pipeline] Created module instance:", prim_path)
        except Exception as exc:
            print("[LSP1 Pipeline] Module instance creation failed:", repr(exc))

    def _load_terrain_model(self):
        try:
            import omni.usd
            from pxr import UsdGeom

            terrain_cfg = self.manifest.get("terrain") or {}
            terrain_path = self._get_terrain_path()

            if not terrain_path:
                print("[LSP1 Pipeline] No terrain configured.")
                return

            stage = omni.usd.get_context().get_stage()
            if not stage:
                print("[LSP1 Pipeline] No stage found.")
                return

            terrain_file = terrain_path.replace("\\", "/")

            print("[LSP1 Pipeline] TERRAIN local path:", terrain_file)
            print("[LSP1 Pipeline] TERRAIN exists:", os.path.exists(terrain_path))

            if not os.path.exists(terrain_path):
                print("[LSP1 Pipeline] STOP: terrain file does not exist.")
                return

            if not stage.GetPrimAtPath("/World").IsValid():
                stage.DefinePrim("/World", "Xform")

            terrain_prim_path = terrain_cfg.get("prim_path", "/World/Lunar_Surface")

            old_prim = stage.GetPrimAtPath(terrain_prim_path)
            if old_prim and old_prim.IsValid():
                stage.RemovePrim(terrain_prim_path)
                print("[LSP1 Pipeline] Removed old:", terrain_prim_path)

            terrain_xform = UsdGeom.Xform.Define(stage, terrain_prim_path)
            terrain_prim = terrain_xform.GetPrim()

            terrain_prim.GetReferences().ClearReferences()
            terrain_prim.GetReferences().AddReference(terrain_file)

            xform = UsdGeom.Xformable(terrain_prim)
            xform.ClearXformOpOrder()

            translate = terrain_cfg.get("translate", [0.0, 0.0, 0.0])
            scale = terrain_cfg.get("scale", [1.0, 1.0, 1.0])

            xform.AddTranslateOp().Set(tuple(translate))
            xform.AddScaleOp().Set(tuple(scale))

            print("[LSP1 Pipeline] SUCCESS: loaded 3D lunar terrain model.")

        except Exception as e:
            print("[LSP1 Pipeline] Terrain model load failed:", repr(e))

    def _apply_module_terrain_projection(self):
        try:
            import omni.usd
            from pxr import UsdGeom, Gf

            modules = (
                self.manifest.get("terrain_projection", {})
                .get("modules", {})
                .get("modules", {})
            )
            if not modules:
                print("[LSP1 Pipeline] No module terrain projection in manifest.")
                return

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            moved = 0
            for module_name, info in modules.items():
                terrain_z = info.get("placement_z_m", info.get("terrain_z_m"))
                if terrain_z is None:
                    continue

                prim = stage.GetPrimAtPath(info.get("prim_path", f"/World/{module_name}"))
                if not prim or not prim.IsValid():
                    continue

                xformable = UsdGeom.Xformable(prim)
                translate_op = None
                rotate_op = None
                for op in xformable.GetOrderedXformOps():
                    if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                        translate_op = op
                    elif op.GetOpType() == UsdGeom.XformOp.TypeRotateXYZ:
                        rotate_op = op

                if translate_op is None:
                    translate_op = xformable.AddTranslateOp()

                position_xy = info.get("position_xy_m") or [0.0, 0.0]
                x = float(position_xy[0])
                y = float(position_xy[1])
                translate_op.Set(Gf.Vec3d(x, y, float(terrain_z)))

                rotation = info.get("placement_rotation_deg")
                if isinstance(rotation, list) and len(rotation) >= 3:
                    if rotate_op is None:
                        rotate_op = xformable.AddRotateXYZOp()
                    rotate_op.Set(Gf.Vec3f(
                        float(rotation[0]),
                        float(rotation[1]),
                        float(rotation[2]),
                    ))
                moved += 1

            print(f"[LSP1 Pipeline] Applied terrain pose to {moved} module prim(s).")

        except Exception as e:
            print("[LSP1 Pipeline] Module terrain projection failed:", repr(e))

    def _apply_default_rover_terrain_poses(self):
        """Ground source rover prims before DES movement begins."""
        try:
            import omni.usd
            from pxr import UsdGeom, Gf

            route_projection = (
                self.manifest.get("terrain_projection", {})
                .get("routes", {})
                .get("routes", {})
            )
            stage = omni.usd.get_context().get_stage()
            if not stage or not route_projection:
                return

            for rover_name, flow in (("RegolithRover", "Regolith"), ("LOXRover", "LOX")):
                route_info = next(
                    (
                        info for info in route_projection.values()
                        if str(info.get("flow") or "").lower() == flow.lower()
                        and info.get("sampled_poses")
                    ),
                    None,
                )
                if not route_info:
                    continue

                pose = route_info["sampled_poses"][0]
                position = pose.get("position_m")
                rotation = pose.get("rotation_deg")
                prim = stage.GetPrimAtPath(f"/World/{rover_name}")
                if not prim or not prim.IsValid() or not position:
                    continue

                xformable = UsdGeom.Xformable(prim)
                translate_op = next(
                    (
                        op for op in xformable.GetOrderedXformOps()
                        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate
                    ),
                    None,
                )
                rotate_op = next(
                    (
                        op for op in xformable.GetOrderedXformOps()
                        if op.GetOpType() == UsdGeom.XformOp.TypeRotateXYZ
                    ),
                    None,
                )
                if translate_op is None:
                    translate_op = xformable.AddTranslateOp()
                translate_op.Set(Gf.Vec3d(*position))
                if rotation:
                    if rotate_op is None:
                        rotate_op = xformable.AddRotateXYZOp()
                    rotate_op.Set(Gf.Vec3f(*rotation))

            print("[LSP1 Pipeline] Applied default terrain poses to rover source prims.")
        except Exception as exc:
            print("[LSP1 Pipeline] Default rover terrain placement failed:", repr(exc))

    def _draw_route_slope_debug(self):
        try:
            import omni.usd
            from pxr import UsdGeom, Gf, Sdf

            route_projection = (
                self.manifest.get("terrain_projection", {})
                .get("routes", {})
                .get("routes", {})
            )
            if not route_projection:
                print("[LSP1 Pipeline] No route slope debug data in manifest.")
                return

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            root_path = "/World/TerrainRouteSlopeDebug"
            old_prim = stage.GetPrimAtPath(root_path)
            if old_prim and old_prim.IsValid():
                stage.RemovePrim(root_path)

            UsdGeom.Xform.Define(stage, root_path)
            drawn = 0

            for route_name, route_info in route_projection.items():
                route_root = UsdGeom.Xform.Define(stage, f"{root_path}/{route_name}")
                route_root.GetPrim().CreateAttribute(
                    "route:maxSlopeDeg",
                    Sdf.ValueTypeNames.Double,
                ).Set(float(route_info.get("max_slope_deg") or 0.0))
                route_root.GetPrim().CreateAttribute(
                    "route:status",
                    Sdf.ValueTypeNames.String,
                ).Set(str(route_info.get("status", "")))

                for segment in route_info.get("original_segments", []):
                    p0 = segment.get("from_m")
                    p1 = segment.get("to_m")
                    if not p0 or not p1:
                        continue

                    seg_idx = int(segment.get("index", drawn))
                    curve = UsdGeom.BasisCurves.Define(
                        stage,
                        f"{root_path}/{route_name}/Segment_{seg_idx:03d}",
                    )
                    curve.CreateTypeAttr("linear")
                    curve.CreateBasisAttr("bezier")
                    curve.CreateCurveVertexCountsAttr([2])
                    curve.CreatePointsAttr([
                        Gf.Vec3f(float(p0[0]), float(p0[1]), float(p0[2]) + 1.0),
                        Gf.Vec3f(float(p1[0]), float(p1[1]), float(p1[2]) + 1.0),
                    ])
                    curve.CreateWidthsAttr([8.0])
                    curve.SetWidthsInterpolation(UsdGeom.Tokens.constant)
                    color = segment.get("color_rgb") or [0.65, 0.65, 0.65]
                    curve.CreateDisplayColorAttr([
                        Gf.Vec3f(float(color[0]), float(color[1]), float(color[2]))
                    ])

                    prim = curve.GetPrim()
                    prim.CreateAttribute("slope:maxDeg", Sdf.ValueTypeNames.Double).Set(
                        float(segment.get("max_slope_deg") or 0.0)
                    )
                    prim.CreateAttribute("slope:status", Sdf.ValueTypeNames.String).Set(
                        str(segment.get("status", ""))
                    )
                    drawn += 1

            self._draw_projected_waypoints(stage, route_projection)

            print(f"[LSP1 Pipeline] Drew {drawn} slope-colored route segment(s).")

        except Exception as e:
            print("[LSP1 Pipeline] Route slope debug draw failed:", repr(e))

    def _draw_projected_waypoints(self, stage, route_projection):
        """Expose terrain-projected route waypoints under a stable Stage path."""
        from pxr import UsdGeom, Gf, Sdf

        root_path = self.manifest.get("waypoint_root", "/World/ConnectionWaypoints")
        existing = stage.GetPrimAtPath(root_path)
        if existing and existing.IsValid():
            stage.RemovePrim(root_path)

        UsdGeom.Xform.Define(stage, root_path)
        marker_count = 0
        for route_name, route_info in route_projection.items():
            route_root = UsdGeom.Xform.Define(stage, f"{root_path}/{route_name}")
            route_root.GetPrim().CreateAttribute(
                "route:flow",
                Sdf.ValueTypeNames.String,
            ).Set(str(route_info.get("flow") or ""))

            # The raw waypoint USD layer is authored in the UI's z=0 frame.
            # These copies use the terrain-projected z coordinates from the
            # visualization manifest, so they are both visible and inspectable.
            points = route_info.get("terrain_waypoints_m") or []
            if not points:
                # Compatibility with manifests written before
                # ``terrain_waypoints_m`` was introduced: original segment
                # endpoints are already terrain-projected by the sampler.
                for segment in route_info.get("original_segments", []):
                    start = segment.get("from_m")
                    end = segment.get("to_m")
                    if start and (not points or points[-1] != start):
                        points.append(start)
                    if end and (not points or points[-1] != end):
                        points.append(end)
            if not points:
                points = route_info.get("original_waypoints_m", [])
            for waypoint_idx, point in enumerate(points):
                if not isinstance(point, list) or len(point) < 3:
                    continue
                marker = UsdGeom.Sphere.Define(
                    stage,
                    f"{root_path}/{route_name}/Waypoint_{waypoint_idx:03d}",
                )
                marker.CreateRadiusAttr(7.0)
                marker.CreateDisplayColorAttr([Gf.Vec3f(1.0, 0.9, 0.25)])
                marker_xform = UsdGeom.Xformable(marker.GetPrim())
                marker_xform.AddTranslateOp().Set(
                    Gf.Vec3d(float(point[0]), float(point[1]), float(point[2]) + 1.5)
                )
                marker_count += 1

        print(f"[LSP1 Pipeline] Added {marker_count} terrain-projected waypoint marker(s).")

    def _set_route_slope_debug_visible(self, visible):
        try:
            import omni.usd
            from pxr import UsdGeom

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            for prim_path in (
                "/World/TerrainRouteSlopeDebug",
                self.manifest.get("waypoint_root", "/World/ConnectionWaypoints"),
            ):
                prim = stage.GetPrimAtPath(prim_path)
                if not prim or not prim.IsValid():
                    continue

                imageable = UsdGeom.Imageable(prim)
                if visible:
                    imageable.MakeVisible()
                else:
                    imageable.MakeInvisible()

        except Exception as e:
            print("[LSP1 Pipeline] Route visibility update failed:", repr(e))

    def _update_show_routes_button(self):
        try:
            if self.show_routes_button:
                self.show_routes_button.text = (
                    "Hide Routes" if self.routes_visible else "Show Routes"
                )
        except Exception:
            pass

    def _toggle_routes(self):
        if not self.is_loaded:
            self._load_all()
            if not self.is_loaded:
                return

        self.routes_visible = not self.routes_visible
        if self.routes_visible:
            self._draw_route_slope_debug()

        self._set_route_slope_debug_visible(self.routes_visible)
        self._update_show_routes_button()

        self.status.text = (
            "Status: routes visible"
            if self.routes_visible
            else "Status: routes hidden"
        )

    def _load_waypoints_under_world(self):
        try:
            import omni.usd
            from pxr import Usd

            waypoints_path = self._resolve_manifest_path(self.manifest.get("waypoints_usd"))
            waypoint_root = self.manifest.get("waypoint_root", "/World/ConnectionWaypoints")

            stage = omni.usd.get_context().get_stage()
            if not stage:
                print("[LSP1 Pipeline] No stage open.")
                return

            print("[LSP1 Pipeline] WAYPOINTS PATH:", waypoints_path)
            print("[LSP1 Pipeline] WAYPOINTS exists:", os.path.exists(waypoints_path))

            if not os.path.exists(waypoints_path):
                print("[LSP1 Pipeline] Waypoints file not found.")
                return

            if not stage.GetPrimAtPath("/World").IsValid():
                stage.DefinePrim("/World", "Xform")

            waypoint_stage = Usd.Stage.Open(waypoints_path)
            if not waypoint_stage:
                print("[LSP1 Pipeline] Could not open waypoints file.")
                return

            source_prim_path = None
            for prim in waypoint_stage.Traverse():
                if prim.GetName() == "ConnectionWaypoints":
                    source_prim_path = str(prim.GetPath())
                    break

            if not source_prim_path:
                print("[LSP1 Pipeline] No ConnectionWaypoints found in file.")
                return

            target_prim = stage.GetPrimAtPath(waypoint_root)

            if not target_prim.IsValid():
                target_prim = stage.DefinePrim(waypoint_root, "Xform")

            target_prim.GetReferences().ClearReferences()
            target_prim.GetReferences().AddReference(
                waypoints_path.replace("\\", "/"),
                source_prim_path
            )

            print("[LSP1 Pipeline] Loaded waypoints into", waypoint_root)

        except Exception as e:
            print("[LSP1 Pipeline] Waypoint load failed:", repr(e))

    def _play(self):
        if not self.is_loaded:
            self._load_all()

        omni.timeline.get_timeline_interface().play()
        self.status.text = "Status: playing"

    def _pause(self):
        omni.timeline.get_timeline_interface().pause()
        self.status.text = "Status: paused"

    def _reset(self):
        self.elapsed_seconds = 0.0

        if self.is_loaded:
            self._update_all(0.0)

        self.status.text = "Status: reset"

    def _ensure_timeline(self):
        if self.timeline_sub:
            return

        stream = omni.timeline.get_timeline_interface().get_timeline_event_stream()
        self.timeline_sub = stream.create_subscription_to_pop_by_type(
            omni.timeline.TimelineEventType.CURRENT_TIME_TICKED,
            self._on_tick
        )

    def _on_tick(self, event):
        if not self.is_loaded:
            return

        dt = event.payload.get("dt", 0.0)
        self.elapsed_seconds += dt

        playback = self.manifest.get("playback", {})
        seconds_per_unit = float(playback.get("seconds_per_sim_time_unit", 1.0))
        if seconds_per_unit <= 0:
            seconds_per_unit = 1.0

        des_duration = self._get_des_duration()
        des_time = min(self.elapsed_seconds / seconds_per_unit, des_duration)

        self._update_all(des_time)

    def _update_all(self, des_time):
        represented_hours = self._des_time_to_mission_hours(des_time)
        display_duration = self._get_display_duration_hours()

        self.time_label.text = (
            f"Mission Time: {represented_hours:.2f} hr / "
            f"{display_duration:.2f} hr"
        )

        self.des_time_label.text = f"DES Time: {des_time:.2f}"

        snap = self._get_snapshot(des_time)
        if not snap:
            return

        self._apply_waypoint_motion(des_time)
        self._update_follow_camera(des_time)
        self._update_dashboard(snap)

    def _get_des_duration(self):
        if not self.des_log_times:
            return 0.0

        return self.des_log_times[-1][0]

    def _get_display_duration_hours(self):
        playback = self.manifest.get("playback", {})
        configured = playback.get("display_duration_hours")
        if configured is not None:
            return float(configured)

        return self._get_des_duration()

    def _des_time_to_mission_hours(self, des_time):
        des_duration = self._get_des_duration()
        display_duration = self._get_display_duration_hours()

        if des_duration <= 0:
            return 0.0

        return (des_time / des_duration) * display_duration

    def _get_snapshot(self, des_time):
        if not self.des_log_times:
            return None

        selected_key = self.des_log_times[0][1]
        for t, key in self.des_log_times:
            if t <= des_time:
                selected_key = key
            else:
                break

        return self.des_log.get(selected_key)

    def _apply_waypoint_motion(self, des_time):
        try:
            import omni.usd
            from pxr import UsdGeom, Gf

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            waypoint_root = self.manifest.get("waypoint_root", "/World/ConnectionWaypoints")

            for actor in self.actors:
                prim_path = actor["prim_path"]
                movement = self._get_actor_movement(actor, des_time, include_future=True)
                if movement:
                    route_name = movement["route_name"]
                    route_path = movement.get("route_path")
                    if not route_path:
                        route_path = f"{waypoint_root}/{route_name}"
                    start_time = float(movement.get("start_time", 0.0))
                    end_time = float(movement.get("end_time", start_time))
                else:
                    route_name = actor["route_name"]
                    route_path = actor.get("route_path")
                    if not route_path:
                        route_path = f"{waypoint_root}/{route_name}"
                    start_time = float(actor.get("start_time", 0.0))
                    end_time = float(actor.get("end_time", start_time))

                if end_time <= start_time:
                    continue

                # Prefer terrain-projected manifest poses. Fall back to route
                # points only for older manifests/debug runs.
                poses = self._get_manifest_route_poses(route_name)
                points = [pose["position_m"] for pose in poses] if poses else []
                if not points:
                    points = self._get_manifest_route_points(route_name)
                if not points:
                    points = self._get_route_points(stage, route_path)
                if not points:
                    print("[LSP1 Pipeline] No waypoint points found for", route_path)
                    continue

                if des_time <= start_time:
                    progress = 0.0
                elif des_time >= end_time:
                    progress = 1.0
                else:
                    progress = (des_time - start_time) / (end_time - start_time)

                reverse = bool(movement.get("reverse", False)) if movement else False
                if reverse:
                    progress = 1.0 - progress

                route_rotation = None
                if poses:
                    pos, tangent, route_rotation = self._sample_route_pose(poses, progress)
                else:
                    pos, tangent = self._sample_polyline_pose(points, progress)

                if reverse and tangent:
                    tangent = [-float(value) for value in tangent]
                    route_rotation = None

                prim = stage.GetPrimAtPath(prim_path)
                if not prim or not prim.IsValid():
                    print("[LSP1 Pipeline] Missing rover prim:", prim_path)
                    continue

                xformable = UsdGeom.Xformable(prim)

                translate_op = None
                rotate_op = None
                for op in xformable.GetOrderedXformOps():
                    if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                        translate_op = op
                    elif op.GetOpType() == UsdGeom.XformOp.TypeRotateXYZ:
                        rotate_op = op

                if translate_op is None:
                    translate_op = xformable.AddTranslateOp()

                translate_op.Set(Gf.Vec3d(
                    pos[0],
                    pos[1],
                    pos[2] + ROVER_TERRAIN_CLEARANCE_M,
                ))
                rotation = route_rotation or self._route_tangent_rotation(
                    tangent,
                    prim=prim,
                    stage=stage,
                )
                if rotation:
                    if rotate_op is None:
                        rotate_op = xformable.AddRotateXYZOp()
                    rotate_op.Set(Gf.Vec3f(*rotation))

        except Exception as e:
            print("[LSP1 Pipeline] Waypoint motion failed:", repr(e))

    def _update_follow_camera(self, des_time):
        try:
            import omni.usd
            from pxr import UsdGeom, Gf

            follow_cfg = self.manifest.get("follow_camera", {})
            camera_path = follow_cfg.get("path", "/World/DES_FollowCamera")
            offset = follow_cfg.get("offset", [40.0, 10.0, 20.0])
            rotate = follow_cfg.get("rotateXYZ", [70.0, 0.0, 120.0])

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            active_actor = self._get_active_actor(des_time)
            if not active_actor:
                self.camera_label.text = "Camera: no active actor"
                return

            target_path = active_actor["prim_path"]
            target_name = active_actor.get("label", active_actor.get("id", target_path))

            target_prim = stage.GetPrimAtPath(target_path)
            if not target_prim or not target_prim.IsValid():
                self.camera_label.text = f"Camera: missing {target_path}"
                return

            cache = UsdGeom.XformCache()
            target_pos = cache.GetLocalToWorldTransform(target_prim).ExtractTranslation()

            camera = UsdGeom.Camera.Define(stage, camera_path)
            cam_prim = camera.GetPrim()

            xformable = UsdGeom.Xformable(cam_prim)
            xformable.ClearXformOpOrder()

            cam_pos = Gf.Vec3d(
                target_pos[0] + float(offset[0]),
                target_pos[1] + float(offset[1]),
                target_pos[2] + float(offset[2])
            )

            xformable.AddTranslateOp().Set(cam_pos)
            xformable.AddRotateXYZOp().Set(Gf.Vec3f(*rotate))

            camera.GetFocalLengthAttr().Set(float(follow_cfg.get("focal_length", 12.0)))
            camera.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 1000000.0))

            self.camera_label.text = f"Camera: following {target_name}"

        except Exception as e:
            print("[LSP1 Pipeline] Follow camera failed:", repr(e))

    def _get_active_actor(self, des_time):
        if not self.actors:
            return None

        active = None
        for actor in self.actors:
            movement = self._get_actor_movement(actor, des_time, include_future=False)
            if movement:
                return actor

            start_time = float(actor.get("start_time", 0.0))

            movements = actor.get("movements", [])
            if movements:
                end_time = float(movements[-1].get("end_time", start_time))
            else:
                end_time = float(actor.get("end_time", start_time))

            if start_time <= des_time:
                active = actor

        return active or self.actors[0]

    def _get_actor_movement(self, actor, des_time, *, include_future=True):
        movements = actor.get("movements", [])
        if not movements:
            return None

        selected = None
        for movement in movements:
            start_time = float(movement.get("start_time", 0.0))
            end_time = float(movement.get("end_time", start_time))

            if start_time <= des_time <= end_time:
                return movement

            if start_time <= des_time:
                selected = movement

        if selected is not None:
            return selected

        if include_future:
            return movements[0]

        return None

    def _get_manifest_route_points(self, route_name):
        cache_key = f"manifest:{route_name}"
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]

        route_info = (
            self.manifest.get("terrain_projection", {})
            .get("routes", {})
            .get("routes", {})
            .get(route_name, {})
        )
        points = route_info.get("sampled_waypoints_m") or []
        if not points:
            self.route_cache[cache_key] = []
            return []

        parsed = [
            [float(point[0]), float(point[1]), float(point[2])]
            for point in points
            if isinstance(point, list) and len(point) >= 3
        ]
        self.route_cache[cache_key] = parsed
        print("[LSP1 Pipeline] Cached", len(parsed), "terrain-projected waypoints for", route_name)
        return parsed

    def _get_manifest_route_poses(self, route_name):
        cache_key = f"manifest-poses:{route_name}"
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]

        route_info = (
            self.manifest.get("terrain_projection", {})
            .get("routes", {})
            .get("routes", {})
            .get(route_name, {})
        )
        poses = route_info.get("sampled_poses") or []
        parsed = []
        for pose in poses:
            position = pose.get("position_m")
            rotation = pose.get("rotation_deg")
            if (
                isinstance(position, list) and len(position) >= 3
                and isinstance(rotation, list) and len(rotation) >= 3
            ):
                parsed.append({
                    "position_m": [
                        float(position[0]),
                        float(position[1]),
                        float(position[2]),
                    ],
                    "rotation_deg": [
                        float(rotation[0]),
                        float(rotation[1]),
                        float(rotation[2]),
                    ],
                })

        self.route_cache[cache_key] = parsed
        if parsed:
            print("[LSP1 Pipeline] Cached", len(parsed), "terrain-fitted rover poses for", route_name)
        return parsed

    def _get_route_points(self, stage, route_path):
        if route_path in self.route_cache:
            return self.route_cache[route_path]

        try:
            from pxr import UsdGeom

            route_prim = stage.GetPrimAtPath(route_path)
            if not route_prim or not route_prim.IsValid():
                print("[LSP1 Pipeline] Missing route prim:", route_path)
                self.route_cache[route_path] = []
                return []

            cache = UsdGeom.XformCache()
            children = list(route_prim.GetChildren())

            waypoint_children = [
                child for child in children
                if child.GetName().startswith("Waypoint_")
            ]

            waypoint_children.sort(key=lambda p: p.GetName())

            points = []
            for child in waypoint_children:
                mat = cache.GetLocalToWorldTransform(child)
                pos = mat.ExtractTranslation()
                points.append([pos[0], pos[1], pos[2]])

            self.route_cache[route_path] = points
            print("[LSP1 Pipeline] Cached", len(points), "waypoints for", route_path)

            return points

        except Exception as e:
            print("[LSP1 Pipeline] Route point load failed:", repr(e))
            self.route_cache[route_path] = []
            return []

    def _interp_polyline(self, points, progress):
        return self._sample_polyline_pose(points, progress)[0]

    def _sample_polyline_pose(self, points, progress):
        if not points:
            return [0, 0, 0], None

        if len(points) == 1:
            return points[0], None

        progress = max(0.0, min(1.0, progress))

        lengths = []
        total = 0.0
        for idx in range(len(points) - 1):
            p0 = points[idx]
            p1 = points[idx + 1]
            segment_length = math.sqrt(
                (p1[0] - p0[0]) ** 2
                + (p1[1] - p0[1]) ** 2
                + (p1[2] - p0[2]) ** 2
            )
            lengths.append(segment_length)
            total += segment_length

        if total <= 0:
            return points[0], None

        target = progress * total
        travelled = 0.0
        for idx, segment_length in enumerate(lengths):
            if travelled + segment_length >= target:
                p0 = points[idx]
                p1 = points[idx + 1]
                local_t = (
                    (target - travelled) / segment_length
                    if segment_length > 0 else 0.0
                )
                pos = [
                    p0[0] + (p1[0] - p0[0]) * local_t,
                    p0[1] + (p1[1] - p0[1]) * local_t,
                    p0[2] + (p1[2] - p0[2]) * local_t,
                ]
                tangent = [
                    p1[0] - p0[0],
                    p1[1] - p0[1],
                    p1[2] - p0[2],
                ]
                return pos, tangent

            travelled += segment_length

        return points[-1], [
            points[-1][0] - points[-2][0],
            points[-1][1] - points[-2][1],
            points[-1][2] - points[-2][2],
        ]

    def _sample_route_pose(self, poses, progress):
        points = [pose["position_m"] for pose in poses]
        if not points:
            return [0, 0, 0], None, None
        if len(points) == 1:
            return points[0], None, poses[0]["rotation_deg"]

        progress = max(0.0, min(1.0, progress))
        lengths = []
        total = 0.0
        for idx in range(len(points) - 1):
            p0 = points[idx]
            p1 = points[idx + 1]
            segment_length = math.sqrt(
                (p1[0] - p0[0]) ** 2
                + (p1[1] - p0[1]) ** 2
                + (p1[2] - p0[2]) ** 2
            )
            lengths.append(segment_length)
            total += segment_length

        if total <= 0:
            return points[0], None, poses[0]["rotation_deg"]

        target = progress * total
        travelled = 0.0
        for idx, segment_length in enumerate(lengths):
            if travelled + segment_length >= target:
                p0 = points[idx]
                p1 = points[idx + 1]
                local_t = (
                    (target - travelled) / segment_length
                    if segment_length > 0 else 0.0
                )
                pos = [
                    p0[0] + (p1[0] - p0[0]) * local_t,
                    p0[1] + (p1[1] - p0[1]) * local_t,
                    p0[2] + (p1[2] - p0[2]) * local_t,
                ]
                tangent = [
                    p1[0] - p0[0],
                    p1[1] - p0[1],
                    p1[2] - p0[2],
                ]
                rot0 = poses[idx]["rotation_deg"]
                rot1 = poses[idx + 1]["rotation_deg"]
                rotation = [
                    rot0[axis] + (rot1[axis] - rot0[axis]) * local_t
                    for axis in range(3)
                ]
                return pos, tangent, rotation

            travelled += segment_length

        return points[-1], [
            points[-1][0] - points[-2][0],
            points[-1][1] - points[-2][1],
            points[-1][2] - points[-2][2],
        ], poses[-1]["rotation_deg"]

    def _rover_forward_yaw_offset(self, stage, prim):
        try:
            geom = stage.GetPrimAtPath(f"{prim.GetPath()}/Geometry")
            if geom and geom.IsValid():
                attr = geom.GetAttribute("cad:userSourceFrontAxis")
                if attr and attr.Get():
                    return 0.0
        except Exception:
            pass
        return ROVER_FORWARD_YAW_OFFSET_DEG

    def _route_tangent_rotation(self, tangent, *, prim=None, stage=None):
        if not tangent:
            return None

        dx, dy, dz = [float(value) for value in tangent[:3]]
        horizontal = math.hypot(dx, dy)
        if horizontal <= 1e-6:
            return None

        yaw_deg = math.degrees(math.atan2(dy, dx))
        pitch_deg = math.degrees(math.atan2(dz, horizontal))
        yaw_offset = (
            self._rover_forward_yaw_offset(stage, prim)
            if stage is not None and prim is not None
            else ROVER_FORWARD_YAW_OFFSET_DEG
        )

        # Older rover CADs used local +Y as forward. Converted CADs with a
        # selected cad:userSourceFrontAxis are normalized so local +X is forward.
        return [pitch_deg, 0.0, yaw_deg + yaw_offset]

    def _update_dashboard(self, snap):
        for actor in self.actors:
            actor_id = actor.get("id")
            actor_snap = snap.get(actor_id, {})
            field_labels = self.actor_labels.get(actor_id, {})

            for field in actor.get("dashboard_fields", []):
                key = field.get("key")
                label = field.get("label", key)
                unit = field.get("unit", "")
                value = actor_snap.get(key, "--")
                suffix = f" {unit}" if unit and value != "--" else ""

                if key in field_labels:
                    field_labels[key].text = f"  {label}: {value}{suffix}"

    def on_shutdown(self):
        print("[LSP1 Pipeline] SHUTDOWN")

        self.timeline_sub = None

        if hasattr(self, "window") and self.window:
            self.window.destroy()
            self.window = None
