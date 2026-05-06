import os
import json
import subprocess

import omni.ext
import omni.ui as ui
import omni.timeline


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))

DES_PATH = os.path.join(
    REPO_ROOT,
    "clean_database",
    "usd",
    "scenes",
    "modified_des.json"
)

WAYPOINTS_PATH = os.path.join(
    REPO_ROOT,
    "clean_database",
    "scenes",
    "waypoints.usda"
)

TERRAIN_PATH = os.path.join(
    REPO_ROOT,
    "clean_database",
    "scenes",
    "lunar_surface_v4.usdc"
)

REPRESENTED_MISSION_HOURS = 40.0
FOLLOW_CAMERA_PATH = "/World/DES_FollowCamera"

ROUTE_MAP = {
    "Regolith Cargo Rover 1": {
        "prim_path": "/World/RegolithRover",
        "route_path": "/World/ConnectionWaypoints/ISRUExcavationToISRUPlant",
        "start_time": 0.0,
        "end_time": 20.0,
    },
    "LOX Cargo Rover": {
        "prim_path": "/World/LOXRover",
        "route_path": "/World/ConnectionWaypoints/ISRUPlantToPropellantDepot",
        "start_time": 20.0,
        "end_time": 40.0,
    },
}


class LSP1PipelineExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        print("[LSP1 Pipeline] STARTUP")

        self.timeline_sub = None
        self.elapsed_seconds = 0.0
        self.des_data = None
        self.is_loaded = False
        self.route_cache = {}

        self.window = ui.Window("LSP1 Pipeline", width=520, height=430)

        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label("LSP1 Pipeline")
                self.status = ui.Label("Status: waiting")

                ui.Button("Pull GitHub", clicked_fn=self._pull_github)
                ui.Button("Load DES Playback", clicked_fn=self._load_all)
                ui.Button("Play", clicked_fn=self._play)
                ui.Button("Pause", clicked_fn=self._pause)
                ui.Button("Reset", clicked_fn=self._reset)

                self.time_label = ui.Label("Mission Time: --")
                self.des_time_label = ui.Label("DES Playback Time: --")
                self.camera_label = ui.Label("Camera: --")

                ui.Separator()

                self.regolith_label = ui.Label("Regolith Rover: --")
                self.regolith_load_label = ui.Label("Regolith Load: --")
                self.lox_label = ui.Label("LOX Rover: --")
                self.lox_load_label = ui.Label("LOX Load: --")

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
                [git_exe, "-C", REPO_ROOT, "pull", "origin", "main"],
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
            print("[LSP1 Pipeline] REPO_ROOT:", REPO_ROOT)
            print("[LSP1 Pipeline] DES PATH:", DES_PATH)
            print("[LSP1 Pipeline] DES exists:", os.path.exists(DES_PATH))
            print("[LSP1 Pipeline] WAYPOINTS PATH:", WAYPOINTS_PATH)
            print("[LSP1 Pipeline] WAYPOINTS exists:", os.path.exists(WAYPOINTS_PATH))
            print("[LSP1 Pipeline] TERRAIN PATH:", TERRAIN_PATH)
            print("[LSP1 Pipeline] TERRAIN exists:", os.path.exists(TERRAIN_PATH))

            with open(DES_PATH, "r", encoding="utf-8") as f:
                self.des_data = json.load(f)

            self._load_waypoints_under_world()
            self._load_terrain_model()

            self.elapsed_seconds = 0.0
            self.is_loaded = True
            self.route_cache = {}

            self._ensure_timeline()
            self._update_all(0.0)

            self.status.text = "Status: loaded DES + waypoints + 3D terrain"

        except Exception as e:
            self.status.text = f"Status: load failed: {e}"
            print("[LSP1 Pipeline] Load failed:", repr(e))

    def _load_terrain_model(self):
        try:
            import omni.usd
            from pxr import UsdGeom

            stage = omni.usd.get_context().get_stage()
            if not stage:
                print("[LSP1 Pipeline] No stage found.")
                return

            terrain_file = TERRAIN_PATH.replace("\\", "/")

            print("[LSP1 Pipeline] TERRAIN local path:", terrain_file)
            print("[LSP1 Pipeline] TERRAIN exists:", os.path.exists(TERRAIN_PATH))

            if not os.path.exists(TERRAIN_PATH):
                print("[LSP1 Pipeline] STOP: terrain file does not exist.")
                return

            if not stage.GetPrimAtPath("/World").IsValid():
                stage.DefinePrim("/World", "Xform")

            terrain_path = "/World/Lunar_Surface_v4"

            old_prim = stage.GetPrimAtPath(terrain_path)
            if old_prim and old_prim.IsValid():
                stage.RemovePrim(terrain_path)
                print("[LSP1 Pipeline] Removed old:", terrain_path)

            terrain_xform = UsdGeom.Xform.Define(stage, terrain_path)
            terrain_prim = terrain_xform.GetPrim()

            terrain_prim.GetReferences().ClearReferences()
            terrain_prim.GetReferences().AddReference(terrain_file)

            xform = UsdGeom.Xformable(terrain_prim)
            xform.ClearXformOpOrder()

            # Placement only. No terrain-following / Z-height sampling.
            xform.AddTranslateOp().Set((1.5, 0.0, 0.0))
            xform.AddScaleOp().Set((1000.0, 1000.0, 1000.0))

            print("[LSP1 Pipeline] SUCCESS: loaded 3D lunar terrain model.")

        except Exception as e:
            print("[LSP1 Pipeline] Terrain model load failed:", repr(e))

    def _load_waypoints_under_world(self):
        try:
            import omni.usd
            from pxr import Usd

            stage = omni.usd.get_context().get_stage()
            if not stage:
                print("[LSP1 Pipeline] No stage open.")
                return

            print("[LSP1 Pipeline] WAYPOINTS PATH:", WAYPOINTS_PATH)
            print("[LSP1 Pipeline] WAYPOINTS exists:", os.path.exists(WAYPOINTS_PATH))

            if not os.path.exists(WAYPOINTS_PATH):
                print("[LSP1 Pipeline] Waypoints file not found.")
                return

            if not stage.GetPrimAtPath("/World").IsValid():
                stage.DefinePrim("/World", "Xform")

            waypoint_stage = Usd.Stage.Open(WAYPOINTS_PATH)
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

            target_path = "/World/ConnectionWaypoints"
            target_prim = stage.GetPrimAtPath(target_path)

            if not target_prim.IsValid():
                target_prim = stage.DefinePrim(target_path, "Xform")

            target_prim.GetReferences().ClearReferences()
            target_prim.GetReferences().AddReference(
                WAYPOINTS_PATH.replace("\\", "/"),
                source_prim_path
            )

            print("[LSP1 Pipeline] Loaded waypoints into", target_path)

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

        des_duration = self._get_des_duration_seconds()
        des_time = min(self.elapsed_seconds, des_duration)

        self._update_all(des_time)

    def _update_all(self, des_time):
        represented_hours = self._des_time_to_mission_hours(des_time)

        self.time_label.text = (
            f"Mission Time: {represented_hours:.2f} hr / "
            f"{REPRESENTED_MISSION_HOURS:.2f} hr"
        )

        self.des_time_label.text = f"DES Playback Time: {des_time:.2f}"

        snap = self._get_snapshot(des_time)
        if not snap:
            return

        self._apply_waypoint_motion(des_time)
        self._update_follow_camera(des_time)
        self._update_dashboard(snap)

    def _get_des_duration_seconds(self):
        if not self.des_data:
            return 0.0

        log = self.des_data.get("log", {})
        if not log:
            return 0.0

        return max(float(k) for k in log.keys())

    def _des_time_to_mission_hours(self, des_time):
        des_duration = self._get_des_duration_seconds()

        if des_duration <= 0:
            return 0.0

        return (des_time / des_duration) * REPRESENTED_MISSION_HOURS

    def _get_snapshot(self, des_time):
        if not self.des_data:
            return None

        log = self.des_data.get("log", {})
        if not log:
            return None

        times = sorted(float(k) for k in log.keys())

        selected = times[0]
        for t in times:
            if t <= des_time:
                selected = t
            else:
                break

        return log.get(str(int(selected)))

    def _apply_waypoint_motion(self, des_time):
        try:
            import omni.usd
            from pxr import UsdGeom, Gf

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            for actor_name, route_info in ROUTE_MAP.items():
                prim_path = route_info["prim_path"]
                route_path = route_info["route_path"]
                start_time = route_info["start_time"]
                end_time = route_info["end_time"]

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

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            if des_time < 20.0:
                target_path = "/World/RegolithRover"
                target_name = "Regolith Rover"
            else:
                target_path = "/World/LOXRover"
                target_name = "LOX Rover"

            target_prim = stage.GetPrimAtPath(target_path)
            if not target_prim or not target_prim.IsValid():
                self.camera_label.text = f"Camera: missing {target_path}"
                return

            cache = UsdGeom.XformCache()
            target_pos = cache.GetLocalToWorldTransform(target_prim).ExtractTranslation()

            camera = UsdGeom.Camera.Define(stage, FOLLOW_CAMERA_PATH)
            cam_prim = camera.GetPrim()

            xformable = UsdGeom.Xformable(cam_prim)
            xformable.ClearXformOpOrder()

            cam_pos = Gf.Vec3d(
                target_pos[0] + 40.0,
                target_pos[1] + 10.0,
                target_pos[2] + 20.0
            )

            xformable.AddTranslateOp().Set(cam_pos)
            xformable.AddRotateXYZOp().Set(Gf.Vec3f(70.0, 0.0, 120.0))

            camera.GetFocalLengthAttr().Set(12.0)
            camera.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 1000000.0))

            self.camera_label.text = f"Camera: following {target_name}"

        except Exception as e:
            print("[LSP1 Pipeline] Follow camera failed:", repr(e))

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
        regolith = snap.get("Regolith Cargo Rover 1", {})
        lox = snap.get("LOX Cargo Rover", {})

        self.regolith_label.text = f"Regolith Rover: {regolith.get('state', '--')}"
        self.regolith_load_label.text = f"Regolith Load: {regolith.get('current_load', '--')} kg"

        self.lox_label.text = f"LOX Rover: {lox.get('state', '--')}"
        self.lox_load_label.text = f"LOX Load: {lox.get('current_load', '--')} kg"

    def on_shutdown(self):
        print("[LSP1 Pipeline] SHUTDOWN")

        self.timeline_sub = None

        if hasattr(self, "window") and self.window:
            self.window.destroy()
            self.window = None
