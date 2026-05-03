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

FOLLOW_CAMERA_PATH = "/World/DES_FollowCamera"
CAMERA_HEIGHT = 180.0

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

                ui.Button("Load DES Playback", clicked_fn=self._load_all)
                ui.Button("Play", clicked_fn=self._play)
                ui.Button("Pause", clicked_fn=self._pause)
                ui.Button("Reset", clicked_fn=self._reset)

                self.status = ui.Label("Status: waiting")
                self.time_label = ui.Label("Mission Time: --")
                self.des_time_label = ui.Label("DES Playback Time: --")
                self.camera_label = ui.Label("Camera: --")

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

    def _update_follow_camera(self, des_time):
        try:
            import omni.usd
            from pxr import UsdGeom, Gf

            stage = omni.usd.get_context().get_stage()
            if not stage:
                print("[LSP1 Pipeline] No stage for camera")
                return

            if des_time < 20.0:
                target_path = "/World/RegolithRover"
                target_name = "Regolith Rover"
            else:
                target_path = "/World/LOXRover"
                target_name = "LOX Rover"

            target_prim = stage.GetPrimAtPath(target_path)
            if not target_prim or not target_prim.IsValid():
                print("[LSP1 Pipeline] Missing camera target:", target_path)
                self.camera_label.text = f"Camera: missing {target_path}"
                return

            cache = UsdGeom.XformCache()
            target_pos = cache.GetLocalToWorldTransform(target_prim).ExtractTranslation()

            camera = UsdGeom.Camera.Define(stage, FOLLOW_CAMERA_PATH)
            cam_prim = camera.GetPrim()

            xformable = UsdGeom.Xformable(cam_prim)
            xformable.ClearXformOpOrder()

            # Offset camera behind + above rover
            cam_pos = Gf.Vec3d(
                target_pos[0] + 120.0,   # left/right offset
                target_pos[1] - 120.0,   # forward/back offset
                target_pos[2] + 140.0    # height
            )
            
            xformable.AddTranslateOp().Set(cam_pos)
            
            # Rotate camera downward and angled
            # (X = tilt down, Z = rotate around vertical axis)
            xformable.AddRotateXYZOp().Set(Gf.Vec3f(60.0, 0.0, 45.0))

            # USD camera looks along local -Z by default.
            # No rotation = straight-down aerial view.
            camera.GetFocalLengthAttr().Set(18.0)
            camera.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 1000000.0))

            self.camera_label.text = f"Camera: following {target_name}"

            print(f"[LSP1 Pipeline] Camera updated at {cam_pos}")

        except Exception as e:
            print("[LSP1 Pipeline] Follow camera failed:", repr(e))
            try:
                self.camera_label.text = f"Camera failed: {e}"
            except Exception:
                pass

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




    def _make_waypoints_transparent(self):
        try:
            import omni.usd
            from pxr import UsdShade, UsdGeom, Sdf, Gf

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            mat_path = Sdf.Path("/World/WaypointTransparentMat")
            material = UsdShade.Material.Define(stage, mat_path)

            shader = UsdShade.Shader.Define(stage, mat_path.AppendPath("Shader"))
            shader.CreateIdAttr("UsdPreviewSurface")

            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
                Gf.Vec3f(0.2, 0.8, 1.0)
            )
            shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.08)

            material.CreateSurfaceOutput().ConnectToSource(
                shader.ConnectableAPI(), "surface"
            )

            count = 0

            for prim in stage.Traverse():
                path = str(prim.GetPath())

                if "/World/ConnectionWaypoints" not in path:
                    continue

                if prim.IsA(UsdGeom.Gprim):
                    gprim = UsdGeom.Gprim(prim)

                    # Direct display opacity.
                    gprim.CreateDisplayOpacityAttr().Set([0.08])

                    # Simple material bind, no binding-strength token.
                    UsdShade.MaterialBindingAPI(prim).Bind(material)

                    count += 1

            print(f"[LSP1 Pipeline] Applied waypoint transparency to {count} prims")

        except Exception as e:
            print("[LSP1 Pipeline] Waypoint transparency failed:", repr(e))

    
    def _create_lro_surface_plane(self):
        try:
            import omni.usd
            from pxr import UsdGeom, UsdShade, Sdf, Gf

            stage = omni.usd.get_context().get_stage()
            if not stage:
                return

            texture_path = os.path.join(
                REPO_ROOT,
                "clean_database",
                "scenes",
                "Lunar_surface_v1.png"
            ).replace("\\", "/")

            plane_path = "/World/LRO_Surface_Plane"
            mat_path = "/World/Looks/LRO_Surface_Material"

            # Create or replace flat surface plane
            plane = UsdGeom.Mesh.Define(stage, plane_path)

            plane.GetPointsAttr().Set([
                Gf.Vec3f(-2500, -2500, -25),
                Gf.Vec3f( 2500, -2500, -25),
                Gf.Vec3f( 2500,  2500, -25),
                Gf.Vec3f(-2500,  2500, -25),
            ])

            plane.GetFaceVertexCountsAttr().Set([4])
            plane.GetFaceVertexIndicesAttr().Set([0, 1, 2, 3])

            # Add UV coordinates so PNG maps correctly
            st = UsdGeom.PrimvarsAPI(plane).CreatePrimvar(
                "st",
                Sdf.ValueTypeNames.TexCoord2fArray,
                UsdGeom.Tokens.varying
            )
            st.Set([
                Gf.Vec2f(0, 0),
                Gf.Vec2f(1, 0),
                Gf.Vec2f(1, 1),
                Gf.Vec2f(0, 1),
            ])

            # Create material
            material = UsdShade.Material.Define(stage, mat_path)

            shader = UsdShade.Shader.Define(stage, mat_path + "/Shader")
            shader.CreateIdAttr("UsdPreviewSurface")

            tex = UsdShade.Shader.Define(stage, mat_path + "/Texture")
            tex.CreateIdAttr("UsdUVTexture")
            tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(texture_path)
            tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")
            tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)

            shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
                tex.ConnectableAPI(),
                "rgb"
            )

            shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.9)

            material.CreateSurfaceOutput().ConnectToSource(
                shader.ConnectableAPI(),
                "surface"
            )

            UsdShade.MaterialBindingAPI(plane.GetPrim()).Bind(material)

            print("[LSP1 Pipeline] LRO surface plane created:", texture_path)

        except Exception as e:
            print("[LSP1 Pipeline] LRO surface plane failed:", repr(e))
    
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
