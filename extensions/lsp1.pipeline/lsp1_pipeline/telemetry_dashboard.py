import json
import os
import omni.ui as ui
import omni.timeline

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))
JSON_FILE_PATH = os.path.join(REPO_ROOT, "database", "json", "scenarios", "ISRU_nominal_temp.json")
SECONDS_PER_SIM_HOUR = 2.0

print("THIS_DIR =", THIS_DIR)
print("REPO_ROOT =", REPO_ROOT)
print("JSON_FILE_PATH =", JSON_FILE_PATH)
print("JSON exists =", os.path.exists(JSON_FILE_PATH))

with open(JSON_FILE_PATH, "r") as f:
    data = json.load(f)

snapshots = {}
for k, v in data.items():
    try:
        snapshots[float(k)] = v
    except ValueError:
        pass

times = sorted(snapshots.keys())

def get_snapshot(t):
    for i in reversed(times):
        if i <= t:
            return snapshots[i]
    return snapshots[times[0]]

class SimpleTelemetry:
    def __init__(self):
        self.time = 0.0
        self.window = ui.Window("Lunar Telemetry", width=400, height=220)

        with self.window.frame:
            with ui.VStack():
                self.time_label = ui.Label("Sim Time: 0.00 hr")
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
        dt = event.payload.get("dt", 0.0)
        self.time += dt
        sim_time = self.time / SECONDS_PER_SIM_HOUR
        snap = get_snapshot(sim_time)

        self.time_label.text = f"Sim Time: {sim_time:.2f} hr"

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

if "_simple_dash" in globals():
    try:
        _simple_dash.window.destroy()
    except Exception:
        pass

_simple_dash = SimpleTelemetry()
print("Dashboard launched.")