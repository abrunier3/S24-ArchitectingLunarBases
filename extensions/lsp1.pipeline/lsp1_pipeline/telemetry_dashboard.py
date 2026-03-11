import json
import omni.ui as ui
import omni.timeline
import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))
JSON_FILE_PATH = os.path.join(REPO_ROOT, "database", "json", "scenarios", "ISRU_nominal_temp.json")
SECONDS_PER_SIM_HOUR = 2.0

# --- Load JSON ---
with open(JSON_FILE_PATH) as f:
    data = json.load(f)

times = sorted([float(t) for t in data.keys()])

def get_snapshot(t):
    for i in reversed(times):
        if i <= t:
            return data[str(i)]
    return data[str(times[0])]

# --- Dashboard ---
class SimpleTelemetry:
    def __init__(self):
        self.time = 0.0

        self.window = ui.Window("Lunar Telemetry", width=400, height=400)

        with self.window.frame:
            with ui.VStack():
                self.time_label = ui.Label("Time: 0")
                self.lox_label = ui.Label("LOX: --")
                self.power_label = ui.Label("Power: --")
                self.rover_label = ui.Label("Rover Battery: --")

        timeline = omni.timeline.get_timeline_interface()
        stream = timeline.get_timeline_event_stream()

        self.sub = stream.create_subscription_to_pop_by_type(
            omni.timeline.TimelineEventType.CURRENT_TIME_TICKED,
            self.update
        )

    def update(self, event):
        dt = event.payload.get("dt", 0)
        self.time += dt

        sim_time = self.time / SECONDS_PER_SIM_HOUR
        snap = get_snapshot(sim_time)

        self.time_label.text = f"Sim Time: {sim_time:.2f} hr"

        try:
            self.lox_label.text = f"LOX Stored: {snap['ISRU_Plant']['LOX_Stored']}"
        except:
            pass

        try:
            self.power_label.text = f"Power Output: {snap['Solar_Power_System']['current_power_output']}"
        except:
            pass

        try:
            self.rover_label.text = f"Rover Battery: {snap['Regolith Cargo Rover']['battery_charge']}"
        except:
            pass

dash = SimpleTelemetry()