import json
import os

import omni.timeline
import omni.usd
import omni.ui as ui
import omni.ui.scene as sc

from pxr import UsdGeom, Gf
from omni.kit.viewport.utility import get_active_viewport_window


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(THIS_DIR, "..", "..", ".."))
JSON_FILE_PATH = os.path.join(
    REPO_ROOT,
    "database",
    "json",
    "scenarios",
    "ISRU_nominal_temp.json",
)

SECONDS_PER_SIM_HOUR = 2.0

PLANT_PRIM = "/World/Assemblies/LSP1Assembly/ISRU_PLANT"
DEPOT_PRIM = "/World/Assemblies/LSP1Assembly/Propellant_Depot"


with open(JSON_FILE_PATH) as f:
    raw = json.load(f)

timeseries = raw["timeseries"]
playback_dt = raw.get("playback_dt", 1.0)

plant_series = timeseries["ISRU_PLANT.lox_stored_kg"]
depot_series = timeseries["LZ_ALPHA.lox_stored_kg"]


def get_world_position(stage, prim_path):
    prim = stage.GetPrimAtPath(prim_path)
    if not prim or not prim.IsValid():
        return Gf.Vec3d(0,0,0)

    cache = UsdGeom.XformCache()
    mat = cache.GetLocalToWorldTransform(prim)
    return mat.ExtractTranslation()


def get_value(series, idx):
    idx = max(0, min(idx, len(series)-1))
    return float(series[idx])


class InSceneTelemetry:

    def __init__(self):

        self.stage = omni.usd.get_context().get_stage()
        self.time = 0

        viewport = get_active_viewport_window()

        self.scene_view = sc.SceneView()

        with self.scene_view.scene:

            self.plant_transform = sc.Transform()
            with self.plant_transform:
                self.plant_label = sc.Label(
                    "ISRU\nLOX --",
                    size=28,
                    alignment=ui.Alignment.CENTER,
                    color=0xFF66CCFF,
                )

            self.depot_transform = sc.Transform()
            with self.depot_transform:
                self.depot_label = sc.Label(
                    "DEPOT\nLOX --",
                    size=28,
                    alignment=ui.Alignment.CENTER,
                    color=0xFFFFDD66,
                )

        viewport.viewport_api.add_scene_view(self.scene_view)

        timeline = omni.timeline.get_timeline_interface()
        stream = timeline.get_timeline_event_stream()

        self.sub = stream.create_subscription_to_pop_by_type(
            omni.timeline.TimelineEventType.CURRENT_TIME_TICKED,
            self.update,
        )

        print("Telemetry overlay started")


    def update(self, event):

        dt = event.payload.get("dt",0)
        self.time += dt

        sim_time = self.time / SECONDS_PER_SIM_HOUR
        idx = int(sim_time / playback_dt)

        plant = get_value(plant_series, idx)
        depot = get_value(depot_series, idx)

        plant_pos = get_world_position(self.stage, PLANT_PRIM) + Gf.Vec3d(0,0,10)
        depot_pos = get_world_position(self.stage, DEPOT_PRIM) + Gf.Vec3d(0,0,10)

        self.plant_transform.translation = plant_pos
        self.depot_transform.translation = depot_pos

        self.plant_label.text = f"ISRU\nLOX {plant:.1f} kg"
        self.depot_label.text = f"DEPOT\nLOX {depot:.1f} kg"



if "_telemetry_overlay" in globals():
    try:
        _telemetry_overlay.sub = None
    except:
        pass

_telemetry_overlay = InSceneTelemetry()