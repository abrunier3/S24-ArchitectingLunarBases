import json
import omni.usd
from pxr import UsdGeom, Gf


def run_scenario(scenario_path, sim_time):
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        raise RuntimeError("No USD stage is currently open.")

    with open(scenario_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rover_path = next(a["prim_path"] for a in data["actors"] if a["id"] == "LOX_CARGO_ROVER")
    rover = stage.GetPrimAtPath(rover_path)
    if not rover or not rover.IsValid():
        raise RuntimeError(f"Rover prim not found: {rover_path}")

    route = data["routes"][0]["waypoints"]

    move_start = next(e for e in data["events"] if e["type"] == "move_start")
    move_end = next(e for e in data["events"] if e["type"] == "move_end")

    t0 = move_start["time"]
    t1 = move_end["time"]

    if sim_time <= t0:
        pos = route[0]

    elif sim_time >= t1:
        pos = route[-1]

    else:
        u = (sim_time - t0) / (t1 - t0)

        scaled = u * (len(route) - 1)
        segment = min(int(scaled), len(route) - 2)
        local = scaled - segment

        p0 = route[segment]
        p1 = route[segment + 1]

        pos = [
            p0[0] + (p1[0] - p0[0]) * local,
            p0[1] + (p1[1] - p0[1]) * local,
            p0[2] + (p1[2] - p0[2]) * local,
        ]

    xf = UsdGeom.Xformable(rover)
    ops = xf.GetOrderedXformOps()

    translate_op = None
    for op in ops:
        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
            translate_op = op
            break

    if translate_op is None:
        xf.ClearXformOpOrder()
        translate_op = xf.AddTranslateOp()

    translate_op.Set(Gf.Vec3d(*pos))
