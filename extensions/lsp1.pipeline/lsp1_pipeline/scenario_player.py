import json
from pathlib import Path

import omni.usd
from pxr import UsdGeom, Gf


class ScenarioPlayer:
    def __init__(self):
        self.scenario = None
        self.time = 0.0
        self.state = {}
        self.active_moves = {}

    def load(self, scenario_path: str):
        with open(scenario_path, "r", encoding="utf-8") as f:
            self.scenario = json.load(f)
        self.time = 0.0
        self.state = self.scenario.get("initial_state", {}).copy()
        self.active_moves = {}

    def update(self, t: float):
        self.time = t
        if not self.scenario:
            return

        # Apply all events up to current time
        for event in self.scenario.get("events", []):
            if event.get("_applied", False):
                continue
            if event["time"] <= t:
                self._apply_event(event)
                event["_applied"] = True

        # Update active rover motions
        self._update_motion()

    def _apply_event(self, event: dict):
        event_type = event["type"]
        actor = event["actor"]

        if actor not in self.state:
            self.state[actor] = {}

        if event_type == "state_update":
            self.state[actor].update(event.get("updates", {}))

        elif event_type == "move_start":
            route_id = event["route_id"]
            route = self._get_route(route_id)
            move_end_time = self._find_matching_move_end(actor, route_id)
            self.active_moves[actor] = {
                "route": route,
                "start_time": event["time"],
                "end_time": move_end_time,
            }
            self.state[actor].update(event.get("updates", {}))

        elif event_type == "move_end":
            self.state[actor].update(event.get("updates", {}))
            if actor in self.active_moves:
                del self.active_moves[actor]
            self._place_actor_at_route_end(actor, event["route_id"])

    def _get_route(self, route_id: str):
        for route in self.scenario.get("routes", []):
            if route["route_id"] == route_id:
                return route
        raise ValueError(f"Route not found: {route_id}")

    def _find_matching_move_end(self, actor: str, route_id: str):
        for event in self.scenario.get("events", []):
            if (
                event["type"] == "move_end"
                and event["actor"] == actor
                and event["route_id"] == route_id
            ):
                return event["time"]
        raise ValueError(f"No move_end found for actor={actor}, route={route_id}")

    def _update_motion(self):
        stage = omni.usd.get_context().get_stage()
        if not stage:
            return

        actor_map = {a["id"]: a for a in self.scenario.get("actors", [])}

        for actor_id, move in self.active_moves.items():
            actor_info = actor_map.get(actor_id)
            if not actor_info:
                continue

            prim = stage.GetPrimAtPath(actor_info["prim_path"])
            if not prim or not prim.IsValid():
                continue

            waypoints = move["route"]["waypoints"]
            start = move["start_time"]
            end = move["end_time"]

            if end <= start:
                progress = 1.0
            else:
                progress = max(0.0, min(1.0, (self.time - start) / (end - start)))

            pos = self._interp_polyline(waypoints, progress)
            xform = UsdGeom.Xformable(prim)
            xform.ClearXformOpOrder()
            xform.AddTranslateOp().Set(Gf.Vec3d(pos[0], pos[1], pos[2]))

            self.state.setdefault(actor_id, {})["route_progress"] = progress

    def _place_actor_at_route_end(self, actor_id: str, route_id: str):
        stage = omni.usd.get_context().get_stage()
        if not stage:
            return

        actor_map = {a["id"]: a for a in self.scenario.get("actors", [])}
        actor_info = actor_map.get(actor_id)
        if not actor_info:
            return

        route = self._get_route(route_id)
        final_pos = route["waypoints"][-1]

        prim = stage.GetPrimAtPath(actor_info["prim_path"])
        if not prim or not prim.IsValid():
            return

        xform = UsdGeom.Xformable(prim)
        xform.ClearXformOpOrder()
        xform.AddTranslateOp().Set(Gf.Vec3d(final_pos[0], final_pos[1], final_pos[2]))

    def _interp_polyline(self, pts, progress):
        if len(pts) == 1:
            return pts[0]

        segment_count = len(pts) - 1
        scaled = progress * segment_count
        idx = min(int(scaled), segment_count - 1)
        local_t = scaled - idx

        p0 = pts[idx]
        p1 = pts[idx + 1]

        return [
            p0[0] + (p1[0] - p0[0]) * local_t,
            p0[1] + (p1[1] - p0[1]) * local_t,
            p0[2] + (p1[2] - p0[2]) * local_t,
        ]