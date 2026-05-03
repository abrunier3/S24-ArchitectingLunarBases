import os
import json

import omni.ext
import omni.ui as ui
import omni.timeline
import omni.usd

from pxr import UsdGeom, Gf


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))

DES_PATH = os.path.join(
    REPO_ROOT,
    "clean_database",
    "usd",
    "scenes",
    "modified_des.json"
)

SECONDS_PER_SIM_SECOND = 1.0


class LSP1PipelineExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        print("[LSP1 Pipeline] STARTUP")

        self.timeline_sub = None
        self.elapsed_seconds = 0.0
        self.des_data = None
        self.is_loaded = False

        self.window = ui.Window("LSP1 Pipeline", width=500, height=380)

        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label("LSP1 Pipeline")

                ui.Button("Load DES Playback", clicked_fn=self._load_all)
                ui.Button("Play", clicked_fn=self._play)
                ui.Button("Pause", clicked_fn=self._pause)
                ui.Button("Reset", clicked_fn=self._reset)

                self.status = ui.Label("Status: waiting")
                self.time_label = ui.Label("Sim Time: 0.00 sec")

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

            self._ensure_timeline()
            self._update_all(0.0)

            self.status.text = "Status: loaded modified_des.json"
            print("[LSP1 Pipeline] Loaded modified_des.json")

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

        sim_time = self.elapsed_seconds / SECONDS_PER_SIM_SECOND
        self._update_all(sim_time)

    def _update_all(self, sim_time):
        self.time_label.text = f"Sim Time: {sim_time:.2f} sec"

        snap = self._get_snapshot(sim_time)
        if not snap:
            return

        self._apply_des_positions(snap)
        self._update_dashboard(snap)

    def _get_snapshot(self, sim_time):
        if not self.des_data:
            return None

        log = self.des_data.get("log", {})
        if not log:
            return None

        times = sorted(float(k) for k in log.keys())

        selected = times[0]
        for t in times:
            if t <= sim_time:
                selected = t
            else:
                break

        key = str(int(selected))
        return log.get(key)

    def _apply_des_positions(self, snap):
        stage = omni.usd.get_context().get_stage()
        if not stage:
            self.status.text = "Status: no USD stage open"
            return

        actor_map = {
            "Regolith Cargo Rover 1": "/World/RegolithRover",
            "LOX Cargo Rover": "/World/LOXRover",
        }

        for actor_name, prim_path in actor_map.items():
            actor_data = snap.get(actor_name)
            if not actor_data:
                continue

            pos = actor_data.get("position_m")
            if not pos:
                continue

            prim = stage.GetPrimAtPath(prim_path)
            if not prim or not prim.IsValid():
                print(f"[LSP1 Pipeline] Missing prim: {prim_path}")
                continue

            xform = UsdGeom.Xformable(prim)
            xform.ClearXformOpOrder()
            xform.AddTranslateOp().Set(Gf.Vec3d(pos[0], pos[1], pos[2]))

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
