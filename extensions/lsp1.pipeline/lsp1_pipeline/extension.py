import os
import json
import subprocess

import omni.ext
import omni.ui as ui
import omni.timeline


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
EXT_ROOT = os.path.normpath(os.path.join(THIS_DIR, ".."))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))

DEFAULT_MANIFEST_PATH = os.path.join(EXT_ROOT, "data", "manifest.json")


class LSP1PipelineExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        print("[LSP1 Pipeline] STARTUP")

        self.timeline_sub = None
        self.elapsed_seconds = 0.0
        self.des_data = None
        self.des_log = {}
        self.des_log_times = []
        self.manifest = None
        self.actors = []
        self.is_loaded = False
        self.route_cache = {}
        self.actor_labels = {}

        self.window = ui.Window("LSP1 Pipeline", width=520, height=430)

        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label("LSP1 Pipeline")
                self.status = ui.Label("Status: waiting")

                ui.Button("Pull GitHub Omniverse", clicked_fn=self._pull_github)
                ui.Button("Load DES Playback", clicked_fn=self._load_all)
                ui.Button("Play", clicked_fn=self._play)
                ui.Button("Pause", clicked_fn=self._pause)
                ui.Button("Reset", clicked_fn=self._reset)

                self.time_label = ui.Label("Mission Time: --")
                self.des_time_label = ui.Label("DES Playback Time: --")
                self.camera_label = ui.Label("Camera: --")

                ui.Separator()

                self.actor_dashboard = ui.VStack(spacing=4)
                with self.actor_dashboard:
                    ui.Label("Actor telemetry: --")

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
                [git_exe, "-C", REPO_ROOT, "pull", "origin", "OMNIVERSE-Integration"],
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
            else:
                self.status.text = "Status: Git pull failed. See log."

        except Exception as e:
            self.status.text = f"Status: Git pull error: {e}"
            print("[LSP1 Pipeline] Git pull error:", repr(e))

    def _load_all(self):
        try:
            self.manifest = self._load_manifest()
            self.actors = self.manifest.get("actors", [])
            self._build_actor_dashboard()

            scene_path = self._resolve_manifest_path(self.manifest.get("scene_usd"))
            des_path = self._resolve_manifest_path(self.manifest.get("des_log"))
            waypoints_path = self._resolve_manifest_path(self.manifest.get("waypoints_usd"))
            terrain_path = self._get_terrain_path()

            print("[LSP1 Pipeline] REPO_ROOT:", REPO_ROOT)
            print("[LSP1 Pipeline] MANIFEST PATH:", DEFAULT_MANIFEST_PATH)
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

            self._normalize_des_log()
            self._open_scene_stage(scene_path)
            self._load_waypoints_under_world()
            self._load_terrain_model()

            self.elapsed_seconds = 0.0
            self.is_loaded = True
            self.route_cache = {}

            self._ensure_timeline()
            self._update_all(0.0)

            self.status.text = "Status: loaded manifest + scene + DES + waypoints"

        except Exception as e:
            self.status.text = f"Status: load failed: {e}"
            print("[LSP1 Pipeline] Load failed:", repr(e))

    def _load_manifest(self):
        with open(DEFAULT_MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        if "actors" not in manifest:
            raise ValueError("Visualization manifest missing required key: actors")

        return manifest

    def _resolve_manifest_path(self, rel_or_abs_path):
        if not rel_or_abs_path:
            return None

        if os.path.isabs(rel_or_abs_path):
            return os.path.normpath(rel_or_abs_path)

        base_dir = os.path.dirname(DEFAULT_MANIFEST_PATH)
        return os.path.normpath(os.path.join(base_dir, rel_or_abs_path))

    def _get_terrain_path(self):
        terrain = self.manifest.get("terrain") or {}
        return self._resolve_manifest_path(terrain.get("usd"))

    def _normalize_des_log(self):
        raw_log = self.des_data.get("log", self.des_data)

        if not isinstance(raw_log, dict):
            raise ValueError("DES data must be a dict or contain a dict under 'log'")

        self.des_log = raw_log
        self.des_log_times = sorted(
            (float(k), k)
            for k in self.des_log.keys()
        )

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
                route_path = actor.get("route_path")
                if not route_path:
                    route_path = f"{waypoint_root}/{actor['route_name']}"

                start_time = float(actor.get("start_time", 0.0))
                end_time = float(actor.get("end_time", start_time))

                points = self._get_route_points(stage, route_path)
                if not points:
                    print("[LSP1 Pipeline] No waypoint points found for", route_path)
                    continue

                if des_time <= start_time:
                    pos = points[0]
                elif des_time >= end_time:
                    pos = points[-1]
                else:
                    progress = (des_time - start_time) / (end_time - start_time)
                    pos = self._interp_polyline(points, progress)

                prim = stage.GetPrimAtPath(prim_path)
                if not prim or not prim.IsValid():
                    print("[LSP1 Pipeline] Missing rover prim:", prim_path)
                    continue

                xformable = UsdGeom.Xformable(prim)

                translate_op = None
                for op in xformable.GetOrderedXformOps():
                    if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                        translate_op = op
                        break

                if translate_op is None:
                    translate_op = xformable.AddTranslateOp()

                # Fixed waypoint XYZ only.
                # No terrain Z projection.
                translate_op.Set(Gf.Vec3d(pos[0], pos[1], pos[2]))

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
            start_time = float(actor.get("start_time", 0.0))
            end_time = float(actor.get("end_time", start_time))

            if start_time <= des_time <= end_time:
                return actor

            if start_time <= des_time:
                active = actor

        return active or self.actors[0]

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
        if not points:
            return [0, 0, 0]

        if len(points) == 1:
            return points[0]

        progress = max(0.0, min(1.0, progress))

        segment_count = len(points) - 1
        scaled = progress * segment_count
        idx = min(int(scaled), segment_count - 1)
        local_t = scaled - idx

        p0 = points[idx]
        p1 = points[idx + 1]

        return [
            p0[0] + (p1[0] - p0[0]) * local_t,
            p0[1] + (p1[1] - p0[1]) * local_t,
            p0[2] + (p1[2] - p0[2]) * local_t,
        ]

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
