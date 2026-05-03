import os
import json

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

REPRESENTED_MISSION_HOURS = 40.0

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

        self.window = ui.Window("LSP1 Pipeline", width=520, height=400)

        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label("LSP1 Pipeline")

                ui.Button("Load DES Playback", clicked_fn=self._load_all)
                ui.Button("Play", clicked_fn=self._play)
                ui.Button("Pause", clicked_fn=self._pause)
                ui.Button("Reset", clicked_fn=self._reset)

                self.status = ui.Label("Status: waiting")
                self.time_label = ui.Label("Mission Time: --")
                self.des_time_label = ui.Label("DES Playback Time: --")

                ui.Separator()

                self.regolith_label = ui.Label("Regolith Rover: --")
                self.regolith_load_label = ui.Label("Regolith Load: --")

                self.lox_label = ui.Label("LOX Rover: --")
                self.lox_load_label = ui.Label("LOX Load: --")

    def _load_all(self):
        try:
            print("[LSP1 Pipeline] DES PATH:", DES_PATH)
            print("[LSP1 Pipeline] DES exists:", os.path.exists(DES_PATH))

            with open(DES_PATH, "r", encoding="utf-8") as f:
                self.des_data = json.load(f)

            self.elapsed_seconds = 0.0
            self.is_loaded = True
            self.route_cache = {}

            self._ensure_timeline()
            self._update_all(0.0)

            self.status.text = "Status: loaded DES + scene waypoints"

        except Exception as e:
            self.status.text = f"Status: load failed: {e}"
            print("[LSP1 Pipeline] Load failed:", repr(e))

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

        key = str(int(selected))
        return log.get(key)

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
                    print(f"[LSP1 Pipeline] No waypoint points found for {route_path}")
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
                    print(f"[LSP1 Pipeline] Missing rover prim: {prim_path}")
                    continue

                xformable = UsdGeom.Xformable(prim)

                translate_op = None
                for op in xformable.GetOrderedXformOps():
                    if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                        translate_op = op
                        break

                if translate_op is None:
                    translate_op = xformable.AddTranslateOp()

                translate_op.Set(Gf.Vec3d(pos[0], pos[1], pos[2]))

        except Exception as e:
            print("[LSP1 Pipeline] Waypoint motion failed:", repr(e))

    def _get_route_points(self, stage, route_path):
        if route_path in self.route_cache:
            return self.route_cache[route_path]

        try:
            from pxr import UsdGeom

            route_prim = stage.GetPrimAtPath(route_path)
            if not route_prim or not route_prim.IsValid():
                print(f"[LSP1 Pipeline] Missing route prim: {route_path}")
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
            print(f"[LSP1 Pipeline] Cached {len(points)} waypoints for {route_path}")

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

    def _update_follow_camera(self, des_time):
        try:
            import omni.usd
            from pxr import UsdGeom, Gf, Sdf
            from omni.kit.viewport.utility import get_active_viewport_window

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            if des_time < 20.0:
                target_path = "/World/RegolithRover"
            else:
                target_path = "/World/LOXRover"

            target_prim = stage.GetPrimAtPath(target_path)
            if not target_prim or not target_prim.IsValid():
                print(f"[LSP1 Pipeline] Missing camera target: {target_path}")
                return

            cache = UsdGeom.XformCache()
            target_pos = cache.GetLocalToWorldTransform(target_prim).ExtractTranslation()

            cam_path = Sdf.Path(FOLLOW_CAMERA_PATH)
            cam_prim = stage.GetPrimAtPath(cam_path)

            if not cam_prim or not cam_prim.IsValid():
                camera = UsdGeom.Camera.Define(stage, cam_path)
                cam_prim = camera.GetPrim()

                camera.GetFocalLengthAttr().Set(18.0)
                camera.GetHorizontalApertureAttr().Set(45.0)
                camera.GetVerticalApertureAttr().Set(30.0)

                print("[LSP1 Pipeline] Created DES follow camera")

            camera = UsdGeom.Camera(cam_prim)

            xformable = UsdGeom.Xformable(cam_prim)
            xformable.ClearXformOpOrder()

            # Direct aerial/top-down view.
            camera_pos = Gf.Vec3d(
                target_pos[0],
                target_pos[1],
                target_pos[2] + CAMERA_HEIGHT
            )

            xformable.AddTranslateOp().Set(camera_pos)

            # USD cameras look down local -Z by default.
            # With no rotation, this is a straight-down aerial camera.
            # Leave rotation out for now.

            try:
                viewport = get_active_viewport_window()
                if viewport:
                    viewport.viewport_api.camera_path = FOLLOW_CAMERA_PATH
                    print(f"[LSP1 Pipeline] Viewport switched to {FOLLOW_CAMERA_PATH}")
            except Exception as e:
                print("[LSP1 Pipeline] Could not switch viewport camera:", repr(e))

            print(f"[LSP1 Pipeline] Camera following {target_path} at {camera_pos}")

        except Exception as e:
            print("[LSP1 Pipeline] Follow camera failed:", repr(e))
    
    def _update_dashboard(self, snap):
        regolith = snap.get("Regolith Cargo Rover 1", {})
        lox = snap.get("LOX Cargo Rover", {})

        regolith_state = regolith.get("state", "--")
        regolith_load = regolith.get("current_load", "--")

        lox_state = lox.get("state", "--")
        lox_load = lox.get("current_load", "--")

        self.regolith_label.text = f"Regolith Rover: {regolith_state}"
        self.regolith_load_label.text = f"Regolith Load: {regolith_load} kg"

        self.lox_label.text = f"LOX Rover: {lox_state}"
        self.lox_load_label.text = f"LOX Load: {lox_load} kg"

    def on_shutdown(self):
        print("[LSP1 Pipeline] SHUTDOWN")

        self.timeline_sub = None

        if hasattr(self, "window") and self.window:
            self.window.destroy()
            self.window = None
