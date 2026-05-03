import os
import json

import omni.ext
import omni.ui as ui
import omni.timeline
import omni.usd

from .scenario_player import ScenarioPlayer


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))

DEFAULT_SCENARIO_PATH = os.path.join(
    REPO_ROOT,
    "database",
    "json",
    "scenarios",
    "DESwaypoints.json"
)

DEFAULT_DES_PATH = os.path.join(
    REPO_ROOT,
    "database",
    "json",
    "scenarios",
    "ISRU_nominal_temp.json"
)

SECONDS_PER_SIM_HOUR = 2.0


class LSP1PipelineExtension(omni.ext.IExt):

    def on_startup(self, ext_id):
        print("[LSP1 Pipeline] Startup")

        self.ext_id = ext_id
        self.window = None

        self.player = ScenarioPlayer()
        self.scenario_path = DEFAULT_SCENARIO_PATH
        self.des_path = DEFAULT_DES_PATH

        self.elapsed_seconds = 0.0
        self.is_loaded = False
        self.is_playing = False

        self.des_data = None
        self.des_mode = None
        self.des_times = []

        self.timeline_sub = None

        self._build_ui()

    def on_shutdown(self):
        print("[LSP1 Pipeline] Shutdown")

        self.timeline_sub = None

        if self.window:
            self.window.destroy()
            self.window = None

    def _build_ui(self):
        self.window = ui.Window("LSP1 Pipeline", width=460, height=520)

        with self.window.frame:
            with ui.VStack(spacing=8, height=0):

                ui.Label("LSP1 Pipeline", height=24)

                ui.Separator()

                ui.Label("Scenario Path")
                self.scenario_field = ui.StringField()
                self.scenario_field.model.set_value(self.scenario_path)

                ui.Label("DES Telemetry Path")
                self.des_field = ui.StringField()
                self.des_field.model.set_value(self.des_path)

                with ui.HStack(height=32, spacing=6):
                    ui.Button("Load", clicked_fn=self._on_load)
                    ui.Button("Play", clicked_fn=self._on_play)
                    ui.Button("Pause", clicked_fn=self._on_pause)
                    ui.Button("Reset", clicked_fn=self._on_reset)

                ui.Separator()

                self.status_label = ui.Label("Status: Not loaded")
                self.time_label = ui.Label("Sim Time: 0.00 hr")

                ui.Separator()

                ui.Label("DES Dashboard", height=24)

                self.lox_label = ui.Label("LOX Stored: --")
                self.power_label = ui.Label("Power Output: --")
                self.rover_label = ui.Label("Rover Battery: --")
                self.route_label = ui.Label("Rover Route Progress: --")

    def _on_load(self):
        self.scenario_path = self.scenario_field.model.get_value_as_string()
        self.des_path = self.des_field.model.get_value_as_string()

        try:
            self.player.load(self.scenario_path)
            self._load_des(self.des_path)

            self.elapsed_seconds = 0.0
            self.is_loaded = True
            self.is_playing = False

            self.player.update(0.0)
            self._update_dashboard(0.0)

            self._ensure_timeline_subscription()

            self.status_label.text = "Status: Loaded scenario + DES telemetry"
            print("[LSP1 Pipeline] Loaded")

        except Exception as e:
            self.status_label.text = f"Status: Load failed: {e}"
            print("[LSP1 Pipeline] Load failed:", e)

    def _on_play(self):
        if not self.is_loaded:
            self._on_load()

        self.is_playing = True

        timeline = omni.timeline.get_timeline_interface()
        timeline.play()

        self.status_label.text = "Status: Playing"

    def _on_pause(self):
        self.is_playing = False

        timeline = omni.timeline.get_timeline_interface()
        timeline.pause()

        self.status_label.text = "Status: Paused"

    def _on_reset(self):
        self.elapsed_seconds = 0.0

        if self.is_loaded:
            self.player.load(self.scenario_path)
            self.player.update(0.0)
            self._update_dashboard(0.0)

        self.status_label.text = "Status: Reset"

    def _ensure_timeline_subscription(self):
        if self.timeline_sub:
            return

        timeline = omni.timeline.get_timeline_interface()
        stream = timeline.get_timeline_event_stream()

        self.timeline_sub = stream.create_subscription_to_pop_by_type(
            omni.timeline.TimelineEventType.CURRENT_TIME_TICKED,
            self._on_timeline_tick
        )

    def _on_timeline_tick(self, event):
        if not self.is_loaded or not self.is_playing:
            return

        dt = event.payload.get("dt", 0.0)
        self.elapsed_seconds += dt

        sim_hours = self.elapsed_seconds / SECONDS_PER_SIM_HOUR

        self.player.update(sim_hours)
        self._update_dashboard(sim_hours)

    def _load_des(self, path):
        with open(path, "r", encoding="utf-8") as f:
            self.des_data = json.load(f)

        # Supports two formats:
        # 1. {"timeseries": {"ISRU_PLANT.lox_stored_kg": [...]}}
        # 2. {"0.0": {...}, "1.0": {...}}
        if "timeseries" in self.des_data:
            self.des_mode = "timeseries"
        else:
            self.des_mode = "snapshots"
            self.des_times = []
            for k in self.des_data.keys():
                try:
                    self.des_times.append(float(k))
                except Exception:
                    pass
            self.des_times = sorted(self.des_times)

    def _update_dashboard(self, sim_hours):
        self.time_label.text = f"Sim Time: {sim_hours:.2f} hr"

        self._update_rover_progress()
        self._update_des_values(sim_hours)

    def _update_rover_progress(self):
        try:
            state = self.player.state

            rover_state = None
            for actor_id, actor_state in state.items():
                if "rover" in actor_id.lower() or "route_progress" in actor_state:
                    rover_state = actor_state
                    break

            if rover_state and "route_progress" in rover_state:
                pct = float(rover_state["route_progress"]) * 100.0
                self.route_label.text = f"Rover Route Progress: {pct:.1f}%"
            else:
                self.route_label.text = "Rover Route Progress: --"

        except Exception:
            self.route_label.text = "Rover Route Progress: --"

    def _update_des_values(self, sim_hours):
        if not self.des_data:
            return

        if self.des_mode == "timeseries":
            self._update_from_timeseries(sim_hours)
        else:
            self._update_from_snapshots(sim_hours)

    def _update_from_timeseries(self, sim_hours):
        timeseries = self.des_data.get("timeseries", {})
        playback_dt = float(self.des_data.get("playback_dt", 1.0))
        idx = int(sim_hours / playback_dt)

        def get_series_value(key):
            series = timeseries.get(key)
            if not series:
                return None
            safe_idx = max(0, min(idx, len(series) - 1))
            return series[safe_idx]

        plant_lox = get_series_value("ISRU_PLANT.lox_stored_kg")
        depot_lox = get_series_value("LZ_ALPHA.lox_stored_kg")
        rover_battery = get_series_value("Regolith Cargo Rover.battery_charge")
        power = get_series_value("Solar_Power_System.current_power_output")

        if plant_lox is not None:
            self.lox_label.text = f"ISRU LOX Stored: {float(plant_lox):.1f} kg"
        elif depot_lox is not None:
            self.lox_label.text = f"Depot LOX Stored: {float(depot_lox):.1f} kg"
        else:
            self.lox_label.text = "LOX Stored: --"

        if power is not None:
            self.power_label.text = f"Power Output: {float(power):.1f}"
        else:
            self.power_label.text = "Power Output: --"

        if rover_battery is not None:
            self.rover_label.text = f"Rover Battery: {float(rover_battery):.1f}"
        else:
            self.rover_label.text = "Rover Battery: --"

    def _update_from_snapshots(self, sim_hours):
        if not self.des_times:
            return

        selected_time = self.des_times[0]
        for t in self.des_times:
            if t <= sim_hours:
                selected_time = t
            else:
                break

        snap = self.des_data.get(str(selected_time), {})

        try:
            self.lox_label.text = f"LOX Stored: {snap['ISRU_Plant']['LOX_Stored']}"
        except Exception:
            self.lox_label.text = "LOX Stored: --"

        try:
            self.power_label.text = f"Power Output: {snap['Solar_Power_System']['current_power_output']}"
        except Exception:
            self.power_label.text = "Power Output: --"

        try:
            self.rover_label.text = f"Rover Battery: {snap['Regolith Cargo Rover']['battery_charge']}"
        except Exception:
            self.rover_label.text = "Rover Battery: --"
