import json
import omni.usd

from pxr import UsdGeom, Gf


class ScenarioPlayer:
    def __init__(self):
        self.scenario = None
        self.time = 0.0
        self.state = {}
        self.active_moves = {}
        self._applied_event_indices = set()

    def load(self, scenario_path: str):
        with open(scenario_path, "r", encoding="utf-8") as f:
            self.scenario = json.load(f)

        self.time = 0.0
        self.state = {}
        self.active_moves = {}
        self._applied_event_indices = set()

        for actor in self.scenario.get("actors", []):
            actor_id = actor.get("id")
            if actor_id:
                self.state[actor_id] = {}

    def update(self, t: float):
        self.time = float(t)

        if not self.scenario:
            return

        events = self.scenario.get("events", [])

        for i, event in enumerate(events):
            if i in self._applied_event_indices:
                continue

            if float(event.get("time", 0.0)) <= self.time:
                self._apply_event(event)
                self._applied_event_indices.add(i)

        self._update_motion()

    def _apply_event(self, event: dict):
        event_type = event.get("type")
        actor = event.get("actor")

        if not actor:
            return

        if actor not in self.state:
            self.state[actor] = {}

        if event_type == "state_update":
            self.state[actor].update(event.get("updates", {}))

        elif event_type == "move_start":
            route_id = event.get("route_id")
            end_time = self._find_matching_move_end(actor, route_id)

            self.active_moves[actor] = {
                "route_id": route_id,
                "start_time": float(event.get("time", 0.0)),
                "end_time": float(end_time),
            }

            self.state[actor].update(event.get("updates", {}))

        elif event_type == "move_end":
            route_id = event.get("route_id")

            self.state[actor].update(event.get("updates", {}))

            if actor in self.active_moves:
                del self.active_moves[actor]

            self._place_actor_at_route_end(actor, route_id)

    def _find_matching_move_end(self, actor: str, route_id: str):
        for event in self.scenario.get("events", []):
            if (
                event.get("type") == "move_end"
                and event.get("actor") == actor
                and event.get("route_id") == route_id
            ):
                return event.get("time")

        raise ValueError(f"No move_end found for actor={actor}, route_id={route_id}")

    def _actor_map(self):
        return {
            actor.get("id"): actor
            for actor in self.scenario.get("actors", [])
            if actor.get("id")
        }

    def _update_motion(self):
        stage = omni.usd.get_context().get_stage()

        if not stage:
            return

        actor_map = self._actor_map()

        for actor_id, move in self.active_moves.items():
            actor_info = actor_map.get(actor_id)

            if not actor_info:
                print(f"[ScenarioPlayer] Actor missing from JSON actors list: {actor_id}")
                continue

            prim_path = actor_info.get("prim_path")
            prim = stage.GetPrimAtPath(prim_path)

            if not prim or not prim.IsValid():
                print(f"[ScenarioPlayer] Missing rover prim: {prim_path}")
                continue

            start = float(move["start_time"])
            end = float(move["end_time"])

            if end <= start:
                progress = 1.0
            else:
                progress = max(0.0, min(1.0, (self.time - start) / (end - start)))

            route_id = move["route_id"]
            waypoints = self._get_waypoints_for_route(stage, route_id)

            if not waypoints:
                print(f"[ScenarioPlayer] No waypoints found for route: {route_id}")
                continue

            position = self._interp_polyline(waypoints, progress)
            self._set_prim_translate(prim, position)

            self.state.setdefault(actor_id, {})["route_progress"] = progress

    def _get_waypoints_for_route(self, stage, route_id: str):
        waypoint_root = self.scenario.get("waypoint_root", "/World/ConnectionWaypoints")

        route_path = f"{waypoint_root}/{route_id}"
        route_prim = stage.GetPrimAtPath(route_path)

        if not route_prim or not route_prim.IsValid():
            # common fallback if the waypoint USDA got nested as /World/World
            fallback_path = f"/World/World/ConnectionWaypoints/{route_id}"
            route_prim = stage.GetPrimAtPath(fallback_path)

            if route_prim and route_prim.IsValid():
                print(f"[ScenarioPlayer] Using fallback waypoint path: {fallback_path}")
            else:
                print(f"[ScenarioPlayer] Missing route prim: {route_path}")
                return []

        waypoints = []

        for child in route_prim.GetChildren():
            if not child.IsValid():
                continue

            idx = None
            idx_attr = child.GetAttribute("waypoint:index")

            if idx_attr and idx_attr.HasAuthoredValue():
                idx = int(idx_attr.Get())

            if idx is None:
                name = child.GetName()
                try:
                    idx = int(name.split("_")[-1])
                except Exception:
                    idx = len(waypoints)

            xformable = UsdGeom.Xformable(child)
            matrix = xformable.ComputeLocalToWorldTransform(0)
            pos = matrix.ExtractTranslation()

            waypoints.append((idx, [float(pos[0]), float(pos[1]), float(pos[2])]))

        waypoints.sort(key=lambda item: item[0])

        return [point for _, point in waypoints]

    def _place_actor_at_route_end(self, actor_id: str, route_id: str):
        stage = omni.usd.get_context().get_stage()

        if not stage:
            return

        actor_map = self._actor_map()
        actor_info = actor_map.get(actor_id)

        if not actor_info:
            return

        prim_path = actor_info.get("prim_path")
        prim = stage.GetPrimAtPath(prim_path)

        if not prim or not prim.IsValid():
            print(f"[ScenarioPlayer] Missing rover prim at route end: {prim_path}")
            return

        waypoints = self._get_waypoints_for_route(stage, route_id)

        if not waypoints:
            print(f"[ScenarioPlayer] Cannot place actor; no route waypoints: {route_id}")
            return

        final_position = waypoints[-1]
        self._set_prim_translate(prim, final_position)

    def _interp_polyline(self, points, progress: float):
        if len(points) == 0:
            return [0.0, 0.0, 0.0]

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

    def _set_prim_translate(self, prim, position):
        xform = UsdGeom.Xformable(prim)

        translate_op = None

        for op in xform.GetOrderedXformOps():
            if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                translate_op = op
                break

        if translate_op is None:
            translate_op = xform.AddTranslateOp()

        translate_op.Set(Gf.Vec3d(position[0], position[1], position[2]))
