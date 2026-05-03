import os
import json

import omni.ext
import omni.ui as ui
import omni.timeline

from .scenario_player import ScenarioPlayer


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))

SCENARIO_PATH = os.path.join(REPO_ROOT, "database", "json", "scenarios", "DESwaypoints.json")
DES_PATH = os.path.join(REPO_ROOT, "database", "json", "scenarios", "ISRU_nominal_temp.json")

SECONDS_PER_SIM_HOUR = 2.0


class LSP1PipelineExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        self.player = ScenarioPlayer()
        self.timeline_sub = None
        self.elapsed_seconds = 0.0
        self.des_data = None
        self.is_loaded = False

        self.window = ui.Window("LSP1 Pipeline", width=460, height=360)

        with self.window.frame:
            with ui.VStack(spacing=8):
                ui.Label("LSP1 Pipeline")

                ui.Button("Load Scenario + DES", clicked_fn=self._load_all)
                ui.Button("Play", clicked_fn=self._play)
                ui.Button("Pause", clicked_fn=self._pause)
                ui.Button("Reset", clicked_fn=self._reset)

                self.status = ui.Label("Status: waiting")
                self.time_label = ui.Label("Sim Time: 0.00 hr")

                ui.Separator()

                self.progress_label = ui.Label("Rover Progress: --")
                self.lox_label = ui.Label("LOX Stored: --")
                self.power_label = ui.Label("Power Output: --")
                self.rover_label = ui.Label("Rover Battery: --")

    def _load_all(self):
        try:
            self.player.load(SCENARIO_PATH)

            with open(DES_PATH, "r", encoding="utf-8") as f:
                self.des_data = json.load(f)

            self.elapsed_seconds = 0.0
            self.is_loaded = True

            self._ensure_timeline()
            self._update_all(0.0)

            self.status.text = "Status: loaded"

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
            self.player.load(SCENARIO_PATH)
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

        sim_hours = self.elapsed_seconds / SECONDS_PER_SIM_HOUR
        self._update_all(sim_hours)

    def _update_all(self, sim_hours):
        self.time_label.text = f"Sim Time: {sim_hours:.2f} hr"

        self.player.update(sim_hours)
        self._update_rover_progress()
        self._update_des_dashboard(sim_hours)

    def _update_rover_progress(self):
        try:
            for actor_id, actor_state in self.player.state.items():
                if "route_progress" in actor_state:
                    pct = float(actor_state["route_progress"]) * 100.0
                    self.progress_label.text = f"Rover Progress: {actor_id} {pct:.1f}%"
                    return

            self.progress_label.text = "Rover Progress: --"

        except Exception:
            self.progress_label.text = "Rover Progress: --"

    def _update_des_dashboard(self, sim_hours):
        if not self.des_data:
            return

        # Supports {"timeseries": {...}} format
        if "timeseries" in self.des_data:
            timeseries = self.des_data.get("timeseries", {})
            playback_dt = float(self.des_data.get("playback_dt", 1.0))
            idx = int(sim_hours / playback_dt)

            def val(key):
                series = timeseries.get(key)
                if not series:
                    return None
                i = max(0, min(idx, len(series) - 1))
                return series[i]

            plant_lox = val("ISRU_PLANT.lox_stored_kg")
            depot_lox = val("LZ_ALPHA.lox_stored_kg")
            power = val("Solar_Power_System.current_power_output")
            battery = val("Regolith Cargo Rover.battery_charge")

            self.lox_label.text = f"ISRU LOX Stored: {plant_lox}" if plant_lox is not None else "LOX Stored: --"
            self.power_label.text = f"Power Output: {power}" if power is not None else "Power Output: --"
            self.rover_label.text = f"Rover Battery: {battery}" if battery is not None else "Rover Battery: --"

    def on_shutdown(self):
        self.timeline_sub = None

        if hasattr(self, "window") and self.window:
            self.window.destroy()
            self.window = None
