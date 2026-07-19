"""Compile a Step 4 scenario description into generic SimPy processes."""

from __future__ import annotations

import json
import math
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import simpy

from S24.DES_pipeline_version.scenario_config import load_scenario_config
from S24.DES_pipeline_version.scenario_equations import (
    ScenarioEquationError,
    evaluate_selected_equations,
    get_equation_contract,
    parse_equations,
    validate_effect_outputs,
)


ASSET_ROOT = Path("clean_database/json/ECLIPSE_Project/assets")
RESULTS_PATH = Path("lunar_spaceport_results.json")
LOG_PATH = Path("lunar_spaceport_log.json")
MIN_EVENT_DT_HR = 1e-6


def _base_type(instance_id):
    return re.sub(r"_\d+$", "", str(instance_id or ""))


def _symbol(value):
    text = re.sub(r"[^A-Za-z0-9_]", "", str(value or "Resource"))
    return text[:1].upper() + text[1:] if text else "Resource"


def _numeric_attributes(attributes):
    return {
        key: float(value)
        for key, value in (attributes or {}).items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def _load_asset(module_type, asset_root=ASSET_ROOT):
    path = Path(asset_root) / f"{module_type}.json"
    if not path.exists():
        return {"name": module_type, "attributes": {}, "ports": []}
    with path.open() as handle:
        return json.load(handle)


def _equation_outputs(equations):
    return [output for output, _, _ in parse_equations(equations)]


def _module_equations(builder, instance_id, module_type):
    equations = builder.get("module_equations", {})
    return equations.get(instance_id, equations.get(module_type, ""))


def _module_explicit_role(builder, instance_id, module_type):
    classes = builder.get("module_classes", {})
    raw = classes.get(instance_id, classes.get(module_type, ""))
    key = re.sub(r"[^a-z]", "", str(raw).lower())
    return {
        "source": "source",
        "processor": "processor",
        "storage": "storage",
        "consumer": "consumer",
        "powergenerator": "generator",
        "generator": "generator",
        "transporter": "transporter",
        "passive": "consumer",
    }.get(key, "")


def _is_power_generator(module_type, equations=""):
    try:
        outputs = _equation_outputs(equations)
    except ScenarioEquationError:
        outputs = []
    return "power" in str(module_type).lower() or "PowerOut" in outputs


@dataclass(frozen=True)
class ModuleSpec:
    instance_id: str
    module_type: str
    attributes: dict
    equations: str
    incoming_resources: tuple
    outgoing_resources: tuple
    explicit_role: str = ""

    @property
    def role(self):
        if self.explicit_role and self.explicit_role != "transporter":
            return self.explicit_role
        if self.incoming_resources and self.outgoing_resources:
            try:
                outputs = set(_equation_outputs(self.equations))
            except ScenarioEquationError:
                outputs = set()
            same_flow = set(self.incoming_resources) == set(self.outgoing_resources)
            return "storage" if same_flow and "ProcessingTime" not in outputs else "processor"
        if self.outgoing_resources:
            return "source"
        if self.incoming_resources:
            return "storage"
        if _is_power_generator(self.module_type, self.equations):
            return "generator"
        return "consumer"


@dataclass(frozen=True)
class RouteSpec:
    route_id: str
    flow: str
    rover_type: str
    rover_id: str
    source_id: str
    destination_id: str
    stops: tuple
    distance_km: float
    unit: str


@dataclass(frozen=True)
class ScenarioBlueprint:
    modules: dict
    routes: tuple
    power_links: tuple
    duration_hr: float
    rover_capacity_kg: float
    rover_capacity_by_flow_kg: dict
    travel_time_hr_per_km: float
    energy_kwh_per_km_per_kg: float
    power_config: dict
    rover_attributes: dict


def compile_scenario(options, asset_root=ASSET_ROOT):
    config = load_scenario_config(options)
    configured_asset_root = config.get("scenario", {}).get("json_asset_root")
    if configured_asset_root and Path(asset_root) == ASSET_ROOT:
        asset_root = Path(configured_asset_root)
    builder = config.get("scenario_builder", {})
    raw_instances = [
        instance for instance in builder.get("instances", [])
        if instance.get("placed", True)
    ]
    routes = []
    incoming = defaultdict(set)
    outgoing = defaultdict(set)

    for index, raw in enumerate(builder.get("resource_routes", []), start=1):
        flow = _symbol(raw.get("flow"))
        source_id = str(raw.get("from") or "")
        destination_id = str(raw.get("to") or "")
        rover_type = str(raw.get("rover_type") or f"{flow}Rover")
        rover_id = str(raw.get("rover_id") or rover_type)
        route = RouteSpec(
            route_id=str(raw.get("id") or f"route_{index}"),
            flow=flow,
            rover_type=rover_type,
            rover_id=rover_id,
            source_id=source_id,
            destination_id=destination_id,
            stops=tuple(raw.get("stops") or ()),
            distance_km=max(0.0, float(raw.get("distance_km") or 0.0)),
            unit=str(raw.get("unit") or "kg"),
        )
        routes.append(route)
        outgoing[source_id].add(flow)
        incoming[destination_id].add(flow)

    modules = {}
    for raw in raw_instances:
        instance_id = str(raw.get("id") or "")
        module_type = str(raw.get("type") or _base_type(instance_id))
        asset = _load_asset(module_type, asset_root)
        modules[instance_id] = ModuleSpec(
            instance_id=instance_id,
            module_type=module_type,
            attributes=_numeric_attributes(asset.get("attributes")),
            equations=_module_equations(builder, instance_id, module_type),
            incoming_resources=tuple(sorted(incoming[instance_id])),
            outgoing_resources=tuple(sorted(outgoing[instance_id])),
            explicit_role=_module_explicit_role(builder, instance_id, module_type),
        )

    supply = config.get("power", {}).get("supply", {})
    for spec in modules.values():
        if spec.role != "generator":
            continue
        spec.attributes["powerOutput"] = float(
            supply.get("power_output_kw", spec.attributes.get("powerOutput", 0.0))
        )
        spec.attributes["batteryCapacity"] = float(
            supply.get("battery_capacity_kwh", spec.attributes.get("batteryCapacity", 0.0))
        )
        spec.attributes["batteryCharge"] = float(
            supply.get(
                "initial_battery_charge_kwh",
                spec.attributes.get("batteryCharge", spec.attributes["batteryCapacity"]),
            )
        )
        if not 0 <= spec.attributes["batteryCharge"] <= spec.attributes["batteryCapacity"]:
            raise ValueError("Initial battery charge must be between 0 and battery capacity")

    rover_types = {route.rover_type for route in routes}
    return ScenarioBlueprint(
        modules=modules,
        routes=tuple(routes),
        power_links=tuple(builder.get("sysml_interfaces", [])),
        duration_hr=float(config.get("simulation", {}).get("duration_hr", 60.0)),
        rover_capacity_kg=float(config.get("rovers", {}).get("max_capacity_kg", 4000.0)),
        rover_capacity_by_flow_kg={
            _symbol(flow): float(capacity)
            for flow, capacity in config.get("rovers", {}).get("capacity_by_flow_kg", {}).items()
        },
        travel_time_hr_per_km=float(
            config.get("rovers", {}).get("travel_time_hr_per_km", 5.0)
        ),
        energy_kwh_per_km_per_kg=float(
            config.get("rovers", {}).get("energy_kwh_per_km_per_kg", 0.00034)
        ),
        power_config=config.get("power", {}),
        rover_attributes={
            rover_type: _numeric_attributes(
                _load_asset(rover_type, asset_root).get("attributes")
            )
            for rover_type in rover_types
        },
    )


def _module_equation_inputs(module):
    resources = set(module.incoming_resources) | set(module.outgoing_resources)
    allowed = set(module.attributes) | {
        "SimulationTime",
        "ResourceIn",
        "RequestedResource",
    }
    for resource in resources:
        allowed.update({
            f"{resource}In",
            f"{resource}Stored",
            f"Requested{resource}",
        })
    return allowed


def _module_effect_outputs(module):
    resources = set(module.incoming_resources) | set(module.outgoing_resources)
    outputs = {
        "ProcessingTime",
        "EnergyConsumed",
        "PowerIn",
        "PowerOut",
        "EnergyGenerated",
    }
    for resource in resources:
        outputs.update({f"{resource}Out", f"{resource}Stored"})
    return outputs


def _append_equation_errors(messages, label, equations, allowed_inputs, effect_outputs):
    try:
        contract = get_equation_contract(equations)
        unknown = sorted(contract["inputs"] - set(allowed_inputs))
        if unknown:
            messages.append(
                f"[ERROR] {label} uses unknown equation variable(s): {', '.join(unknown)}."
            )
        validate_effect_outputs(equations, effect_outputs)
        return contract["outputs"]
    except ScenarioEquationError as exc:
        messages.append(f"[ERROR] {label}: {exc}")
        return set()


def validate_generic_scenario(options, raise_error=True, asset_root=ASSET_ROOT):
    messages = []
    try:
        blueprint = compile_scenario(options, asset_root)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        messages.append(f"[ERROR] Scenario configuration cannot be compiled: {exc}")
        if raise_error:
            raise ValueError(messages[0]) from exc
        return messages

    if blueprint.duration_hr <= 0:
        messages.append("[ERROR] Simulation duration must be greater than zero.")
    if not blueprint.modules:
        messages.append("[ERROR] The generic scenario has no placed module instance.")
    if not blueprint.routes:
        messages.append("[WARNING] The generic scenario has no resource route.")

    instance_ids = set(blueprint.modules)
    rover_routes = defaultdict(list)
    resource_units = defaultdict(set)
    for route in blueprint.routes:
        if route.source_id not in instance_ids:
            messages.append(f"[ERROR] Route {route.route_id} has unknown source {route.source_id}.")
        if route.destination_id not in instance_ids:
            messages.append(
                f"[ERROR] Route {route.route_id} has unknown destination {route.destination_id}."
            )
        if route.source_id == route.destination_id:
            messages.append(f"[ERROR] Route {route.route_id} has identical endpoints.")
        if not route.rover_id:
            messages.append(f"[ERROR] Route {route.route_id} has no transporter assignment.")
        if route.distance_km <= 0:
            messages.append(f"[ERROR] Route {route.route_id} must have a positive distance.")
        unknown_stops = [stop for stop in route.stops if stop not in instance_ids]
        if unknown_stops:
            messages.append(
                f"[ERROR] Route {route.route_id} has unknown stop(s): {', '.join(unknown_stops)}."
            )
        rover_routes[route.rover_id].append(route)
        resource_units[route.flow].add(route.unit)

    for resource, units in resource_units.items():
        if len(units) > 1:
            messages.append(
                f"[ERROR] Resource {resource} uses incompatible route units: {', '.join(sorted(units))}."
            )

    for module in blueprint.modules.values():
        outputs = _append_equation_errors(
            messages,
            module.instance_id,
            module.equations,
            _module_equation_inputs(module),
            _module_effect_outputs(module),
        )
        for resource in module.outgoing_resources:
            required = f"{resource}Out"
            if module.role != "storage" and required not in outputs:
                messages.append(
                    f"[ERROR] {module.instance_id} must define {required} for its outgoing route."
                )
        if module.role == "processor" and "ProcessingTime" not in outputs:
            messages.append(
                f"[ERROR] {module.instance_id} must define ProcessingTime."
            )
        if module.role == "storage" and module.incoming_resources:
            messages.append(
                f"[INFO] {module.instance_id} uses additive storage when no ResourceStored equation is defined."
            )

    config = load_scenario_config(options)
    builder = config.get("scenario_builder", {})
    for rover_id, assigned_routes in rover_routes.items():
        rover_type = assigned_routes[0].rover_type
        equations = _module_equations(builder, rover_id, rover_type)
        flows = {route.flow for route in assigned_routes}
        rover_inputs = set(blueprint.rover_attributes.get(rover_type, {})) | {
            "SimulationTime",
            "Distance",
            "CargoMass",
            "RoverCapacity",
            "hoursPerKm",
            "energyPerKmPerKg",
            "ResourceIn",
        }
        for flow in flows:
            rover_inputs.add(f"{flow}In")
        rover_effects = {
            "TravelTime",
            "EnergyConsumed",
            "PowerIn",
            *(f"{flow}Out" for flow in flows),
        }
        outputs = _append_equation_errors(
            messages, rover_id, equations, rover_inputs, rover_effects
        )
        for flow in flows:
            if f"{flow}Out" not in outputs:
                messages.append(f"[ERROR] {rover_id} must define {flow}Out.")
        if "TravelTime" not in outputs:
            messages.append(f"[ERROR] {rover_id} must define TravelTime.")
        if "EnergyConsumed" not in outputs:
            messages.append(f"[WARNING] {rover_id} uses the default rover energy law.")
        rover_model = blueprint.power_config.get("module_models", {}).get(
            rover_id,
            blueprint.power_config.get("module_models", {}).get(rover_type, {}),
        )
        if rover_model.get("mode") == "equation":
            _append_equation_errors(
                messages,
                f"{rover_id} power model",
                rover_model.get("equation", ""),
                rover_inputs,
                {"PowerIn", "EnergyConsumed"},
            )

    incoming_power = set()
    outgoing_power = set()
    for link in blueprint.power_links:
        if "power" not in str(link.get("flow") or "").lower():
            continue
        incoming_power.update(link.get("to_instances") or ())
        outgoing_power.update(link.get("from_instances") or ())
    power_models = blueprint.power_config.get("module_models", {})
    for module in blueprint.modules.values():
        outputs = set()
        try:
            outputs = get_equation_contract(module.equations)["outputs"]
        except ScenarioEquationError:
            pass
        model = power_models.get(
            module.instance_id, power_models.get(module.module_type, {})
        )
        if model.get("mode") == "equation":
            _append_equation_errors(
                messages,
                f"{module.instance_id} power model",
                model.get("equation", ""),
                _module_equation_inputs(module),
                {"PowerIn", "EnergyConsumed"},
            )
        elif model.get("mode") == "profile":
            points = model.get("points") or []
            times = [float(point.get("time_hr", 0.0)) for point in points]
            if len(points) < 2 or times != sorted(times):
                messages.append(
                    f"[ERROR] {module.instance_id} power profile requires at least two time-ordered points."
                )
        elif float(model.get("average_kw", 0.0) or 0.0) < 0:
            messages.append(
                f"[ERROR] {module.instance_id} average power demand cannot be negative."
            )
        has_demand = (
            "PowerIn" in outputs
            or "EnergyConsumed" in outputs
            or float(model.get("average_kw", 0.0) or 0.0) > 0
            or model.get("mode") in {"profile", "equation"}
        )
        if module.role != "generator" and has_demand and module.instance_id not in incoming_power:
            messages.append(f"[ERROR] {module.instance_id} consumes power but has no incoming power interface.")
        if module.role == "generator" and module.instance_id not in outgoing_power:
            messages.append(f"[WARNING] {module.instance_id} has no outgoing power interface.")

    errors = [message for message in messages if message.startswith("[ERROR]")]
    if errors and raise_error:
        raise ValueError("\n".join(errors))
    return messages


class GenericModuleRuntime:
    def __init__(self, env, spec, event_log):
        self.env = env
        self.spec = spec
        self.event_log = event_log
        resources = set(spec.incoming_resources) | set(spec.outgoing_resources)
        self.inventory = {
            resource: simpy.Container(env, capacity=float("inf"), init=0.0)
            for resource in resources
        }
        self.input_queue = simpy.Store(env)
        self.operation_resource = simpy.Resource(env, capacity=1)
        self.received = defaultdict(float)
        self.produced = defaultdict(float)
        self.total_energy_kwh = 0.0
        self.pending_energy_kwh = 0.0
        self.processing_time_hr = 0.0
        self.cycles = 0
        self.last_outputs = {}

    def context(self, **extra):
        context = dict(self.spec.attributes)
        context["SimulationTime"] = float(self.env.now)
        for resource, container in self.inventory.items():
            context[f"{resource}Stored"] = float(container.level)
            context.setdefault(f"{resource}In", 0.0)
            context.setdefault(f"{resource}Out", 0.0)
        context.update(extra)
        return context

    def record_energy(self, outputs, duration_hr=0.0):
        energy = outputs.get("EnergyConsumed")
        if energy is None and "PowerIn" in outputs:
            energy = outputs["PowerIn"] * max(0.0, duration_hr)
        energy = max(0.0, float(energy or 0.0))
        self.total_energy_kwh += energy
        self.pending_energy_kwh += energy

    def produce_on_request(self, resource, requested):
        with self.operation_resource.request() as request:
            yield request
            context = self.context(
                RequestedResource=requested,
                **{
                    f"Requested{resource}": requested,
                    f"{resource}In": requested,
                    "ResourceIn": requested,
                },
            )
            wanted = {f"{resource}Out", "ProcessingTime", "EnergyConsumed", "PowerIn"}
            outputs = evaluate_selected_equations(self.spec.equations, context, wanted)
            amount = max(0.0, outputs.get(f"{resource}Out", 0.0))
            duration = max(0.0, outputs.get("ProcessingTime", 0.0))
            if duration:
                yield self.env.timeout(duration)
            self.record_energy(outputs, duration)
            self.produced[resource] += amount
            self.processing_time_hr += duration
            self.cycles += 1
            self.last_outputs = outputs
            self.event_log.append({
                "time_hr": self.env.now,
                "type": "production",
                "module": self.spec.instance_id,
                "flow": resource,
                "amount": amount,
            })
            return amount

    def available(self, resource):
        if self.spec.role == "source":
            return float("inf")
        container = self.inventory.get(resource)
        return float(container.level) if container is not None else 0.0

    def supply(self, resource, requested):
        if self.spec.role == "source":
            return (yield self.env.process(self.produce_on_request(resource, requested)))
        container = self.inventory.setdefault(
            resource, simpy.Container(self.env, capacity=float("inf"), init=0.0)
        )
        if container.level <= 0:
            return 0.0
        amount = min(float(requested), float(container.level))
        yield container.get(amount)
        return amount

    def receive(self, resource, amount):
        amount = max(0.0, float(amount))
        self.received[resource] += amount
        if self.spec.role == "processor":
            container = self.inventory[resource]
            yield container.put(amount)
            yield self.input_queue.put((resource, amount))
        else:
            container = self.inventory.setdefault(
                resource, simpy.Container(self.env, capacity=float("inf"), init=0.0)
            )
            context = self.context(
                ResourceIn=amount,
                **{f"{resource}In": amount},
            )
            stored_name = f"{resource}Stored"
            outputs = evaluate_selected_equations(
                self.spec.equations,
                context,
                {stored_name, "EnergyConsumed", "PowerIn", "ProcessingTime"},
            )
            duration = max(0.0, outputs.get("ProcessingTime", 0.0))
            if duration:
                yield self.env.timeout(duration)
            target_level = outputs.get(stored_name)
            if target_level is None:
                yield container.put(amount)
            else:
                target_level = max(0.0, float(target_level))
                delta = target_level - container.level
                if delta > 0:
                    yield container.put(delta)
                elif delta < 0:
                    yield container.get(-delta)
            self.record_energy(outputs, duration)
            self.last_outputs = outputs
        self.event_log.append({
            "time_hr": self.env.now,
            "type": "delivery",
            "module": self.spec.instance_id,
            "flow": resource,
            "amount": amount,
        })

    def process_inputs(self):
        while True:
            resource, amount = yield self.input_queue.get()
            yield self.inventory[resource].get(amount)
            context = self.context(
                ResourceIn=amount,
                **{f"{resource}In": amount},
            )
            wanted = {
                *(f"{flow}Out" for flow in self.spec.outgoing_resources),
                "ProcessingTime",
                "EnergyConsumed",
                "PowerIn",
            }
            outputs = evaluate_selected_equations(self.spec.equations, context, wanted)
            duration = max(0.0, outputs.get("ProcessingTime", 0.0))
            if duration:
                yield self.env.timeout(duration)
            for output_resource in self.spec.outgoing_resources:
                produced = max(0.0, outputs.get(f"{output_resource}Out", 0.0))
                yield self.inventory[output_resource].put(produced)
                self.produced[output_resource] += produced
            self.record_energy(outputs, duration)
            self.processing_time_hr += duration
            self.cycles += 1
            self.last_outputs = outputs
            self.event_log.append({
                "time_hr": self.env.now,
                "type": "processing_complete",
                "module": self.spec.instance_id,
                "input_flow": resource,
                "input_amount": amount,
                "outputs": {
                    flow: outputs.get(f"{flow}Out", 0.0)
                    for flow in self.spec.outgoing_resources
                },
            })

    def snapshot(self):
        return {
            "Name": self.spec.instance_id,
            "Module_Type": self.spec.module_type,
            "Role": self.spec.role,
            "Inventory": {
                resource: round(container.level, 6)
                for resource, container in self.inventory.items()
            },
            "Received": dict(self.received),
            "Produced": dict(self.produced),
            "Energy_Consumed_kWh": round(self.total_energy_kwh, 6),
            "Processing_Time_hr": round(self.processing_time_hr, 6),
            "Cycles": self.cycles,
            "Equation_Outputs": self.last_outputs,
        }


class GenericRoverRuntime:
    def __init__(self, env, rover_id, rover_type, equations, attributes, blueprint, event_log):
        self.env = env
        self.rover_id = rover_id
        self.rover_type = rover_type
        self.equations = equations
        self.attributes = attributes
        self.blueprint = blueprint
        self.event_log = event_log
        self.distance_km = 0.0
        self.energy_kwh = 0.0
        self.delivered = defaultdict(float)
        self.delivered_by_route = defaultdict(float)
        self.trips = 0
        self.pending_energy_kwh = 0.0

    def capacity_for_flow(self, flow):
        return max(
            0.0,
            float(self.blueprint.rover_capacity_by_flow_kg.get(
                _symbol(flow), self.blueprint.rover_capacity_kg
            )),
        )

    def context(self, cargo=0.0, distance=None, flow=None):
        return {
            **self.attributes,
            "SimulationTime": float(self.env.now),
            "Distance": self.distance_km if distance is None else float(distance),
            "CargoMass": float(cargo),
            "RoverCapacity": self.capacity_for_flow(flow) if flow else self.blueprint.rover_capacity_kg,
            "hoursPerKm": self.blueprint.travel_time_hr_per_km,
            "energyPerKmPerKg": self.blueprint.energy_kwh_per_km_per_kg,
            "ResourceIn": float(cargo),
        }

    def transport_outputs(self, route, cargo):
        context = {
            **self.context(cargo=cargo, distance=route.distance_km, flow=route.flow),
            f"{route.flow}In": cargo,
        }
        wanted = {f"{route.flow}Out", "TravelTime", "EnergyConsumed", "PowerIn"}
        return evaluate_selected_equations(self.equations, context, wanted)

    def run_routes(self, routes, modules, poll_dt=0.05):
        while True:
            made_trip = False
            for route in routes:
                source = modules[route.source_id]
                destination = modules[route.destination_id]
                if source.available(route.flow) <= 0:
                    continue
                cargo = yield self.env.process(
                    source.supply(route.flow, self.capacity_for_flow(route.flow))
                )
                if cargo <= 0:
                    continue
                outputs = self.transport_outputs(route, cargo)
                outbound_time = max(
                    MIN_EVENT_DT_HR,
                    outputs.get(
                        "TravelTime",
                        route.distance_km * self.blueprint.travel_time_hr_per_km,
                    ),
                )
                delivered = min(cargo, max(0.0, outputs.get(f"{route.flow}Out", cargo)))
                outbound_energy = outputs.get("EnergyConsumed")
                if outbound_energy is None:
                    outbound_energy = (
                        route.distance_km
                        * cargo
                        * self.blueprint.energy_kwh_per_km_per_kg
                    )
                return_outputs = self.transport_outputs(route, 0.0)
                return_time = max(
                    MIN_EVENT_DT_HR,
                    return_outputs.get(
                        "TravelTime",
                        route.distance_km * self.blueprint.travel_time_hr_per_km,
                    ),
                )
                return_energy = return_outputs.get("EnergyConsumed")
                if return_energy is None:
                    return_energy = 0.0

                yield self.env.timeout(outbound_time)
                yield self.env.process(destination.receive(route.flow, delivered))
                yield self.env.timeout(return_time)
                self.distance_km += 2.0 * route.distance_km
                trip_energy = max(0.0, float(outbound_energy)) + max(
                    0.0, float(return_energy)
                )
                self.energy_kwh += trip_energy
                self.pending_energy_kwh += trip_energy
                self.delivered[route.flow] += delivered
                self.delivered_by_route[route.route_id] += delivered
                self.trips += 1
                made_trip = True
                self.event_log.append({
                    "time_hr": self.env.now,
                    "type": "transport_complete",
                    "rover": self.rover_id,
                    "route": route.route_id,
                    "flow": route.flow,
                    "amount": delivered,
                    "distance_km_round_trip": 2.0 * route.distance_km,
                })
            if not made_trip:
                yield self.env.timeout(poll_dt)

    def snapshot(self):
        return {
            "Name": self.rover_id,
            "Module_Type": self.rover_type,
            "Role": "transporter",
            "Trips": self.trips,
            "Distance_Traveled_km": round(self.distance_km, 6),
            "Energy_Consumed_kWh": round(self.energy_kwh, 6),
            "Delivered": dict(self.delivered),
            "Delivered_By_Route": dict(self.delivered_by_route),
        }


class GenericPowerRuntime:
    def __init__(self, env, blueprint, modules, rovers):
        self.env = env
        self.blueprint = blueprint
        self.modules = modules
        self.rovers = rovers
        self.dt = max(
            MIN_EVENT_DT_HR,
            float(blueprint.power_config.get("management_dt_hr", 1.0)),
        )
        self.total_generated_kwh = 0.0
        self.total_demand_kwh = 0.0
        self.unserved_energy_kwh = 0.0
        self.generated_series = []
        self.demand_series = []
        generator_specs = [
            module.spec for module in modules.values()
            if module.spec.role == "generator"
        ]
        self.battery_capacity_kwh = sum(
            spec.attributes.get("batteryCapacity", 0.0) for spec in generator_specs
        )
        self.battery_charge_kwh = sum(
            spec.attributes.get("batteryCharge", spec.attributes.get("batteryCapacity", 0.0))
            for spec in generator_specs
        )

    @staticmethod
    def _profile_value(points, time_hr):
        points = sorted(points or (), key=lambda point: float(point.get("time_hr", 0.0)))
        if not points:
            return 0.0
        if time_hr <= float(points[0].get("time_hr", 0.0)):
            return float(points[0].get("power_kw", 0.0))
        for left, right in zip(points, points[1:]):
            left_t = float(left.get("time_hr", 0.0))
            right_t = float(right.get("time_hr", left_t))
            if time_hr <= right_t:
                ratio = 0.0 if right_t == left_t else (time_hr - left_t) / (right_t - left_t)
                return float(left.get("power_kw", 0.0)) + ratio * (
                    float(right.get("power_kw", 0.0)) - float(left.get("power_kw", 0.0))
                )
        return float(points[-1].get("power_kw", 0.0))

    def _demand_from_model(self, model, context):
        if model:
            mode = model.get("mode", "average")
            if mode == "profile":
                return max(0.0, self._profile_value(model.get("points"), self.env.now))
            if mode == "equation":
                outputs = evaluate_selected_equations(
                    model.get("equation", ""), context, {"PowerIn", "EnergyConsumed"}
                )
                if "PowerIn" in outputs:
                    return max(0.0, outputs["PowerIn"])
                return max(0.0, outputs.get("EnergyConsumed", 0.0) / self.dt)
            return max(0.0, float(model.get("average_kw", 0.0)))
        return None

    def _model_demand_kw(self, module):
        models = self.blueprint.power_config.get("module_models", {})
        model = models.get(module.spec.instance_id, models.get(module.spec.module_type))
        modeled = self._demand_from_model(model, module.context())
        if modeled is not None:
            return modeled
        outputs = evaluate_selected_equations(
            module.spec.equations, module.context(), {"PowerIn"}
        )
        return max(0.0, outputs.get("PowerIn", 0.0))

    def _rover_demand_kw(self, rover):
        models = self.blueprint.power_config.get("module_models", {})
        model = models.get(rover.rover_id, models.get(rover.rover_type))
        return self._demand_from_model(model, rover.context()) or 0.0

    def _generation_kw(self, module):
        outputs = evaluate_selected_equations(
            module.spec.equations,
            module.context(),
            {"PowerOut", "EnergyGenerated"},
        )
        if "PowerOut" in outputs:
            return max(0.0, outputs["PowerOut"])
        if "EnergyGenerated" in outputs:
            return max(0.0, outputs["EnergyGenerated"] / self.dt)
        return max(0.0, module.spec.attributes.get("powerOutput", 0.0))

    def run(self):
        while True:
            generated = sum(
                self._generation_kw(module) * self.dt
                for module in self.modules.values()
                if module.spec.role == "generator"
            )
            continuous = 0.0
            event_demand = 0.0
            for module in self.modules.values():
                if module.spec.role != "generator":
                    module_energy = self._model_demand_kw(module) * self.dt
                    module.total_energy_kwh += module_energy
                    continuous += module_energy
                event_demand += module.pending_energy_kwh
                module.pending_energy_kwh = 0.0
            for rover in self.rovers.values():
                continuous += self._rover_demand_kw(rover) * self.dt
                event_demand += rover.pending_energy_kwh
                rover.pending_energy_kwh = 0.0
            demand = continuous + event_demand
            surplus = generated - demand
            if surplus >= 0:
                self.battery_charge_kwh = min(
                    self.battery_capacity_kwh,
                    self.battery_charge_kwh + surplus,
                )
            else:
                needed = -surplus
                supplied = min(self.battery_charge_kwh, needed)
                self.battery_charge_kwh -= supplied
                self.unserved_energy_kwh += needed - supplied
            self.total_generated_kwh += generated
            self.total_demand_kwh += demand
            self.generated_series.append([round(self.env.now, 6), generated])
            self.demand_series.append([round(self.env.now, 6), demand])
            yield self.env.timeout(self.dt)

    def snapshot(self):
        return {
            "Total_Generated_kWh": round(self.total_generated_kwh, 6),
            "Total_Demand_kWh": round(self.total_demand_kwh, 6),
            "Unserved_Energy_kWh": round(self.unserved_energy_kwh, 6),
            "Battery_Charge_kWh": round(self.battery_charge_kwh, 6),
            "Battery_Capacity_kWh": round(self.battery_capacity_kwh, 6),
            "Energy_Generated_Time_Array_kWh": self.generated_series,
            "Total_Demand_Time_Array_kWh": self.demand_series,
        }


def run_generic_scenario(
    options,
    asset_root=ASSET_ROOT,
    results_path=RESULTS_PATH,
    log_path=LOG_PATH,
):
    validation = validate_generic_scenario(options, raise_error=False, asset_root=asset_root)
    errors = [message for message in validation if message.startswith("[ERROR]")]
    if errors:
        raise ValueError("\n".join(errors))

    started = time.perf_counter()
    blueprint = compile_scenario(options, asset_root)
    config = load_scenario_config(options)
    builder = config.get("scenario_builder", {})
    env = simpy.Environment()
    events = []
    modules = {
        module_id: GenericModuleRuntime(env, spec, events)
        for module_id, spec in blueprint.modules.items()
    }
    for module in modules.values():
        if module.spec.role == "processor":
            env.process(module.process_inputs())

    routes_by_rover = defaultdict(list)
    for route in blueprint.routes:
        routes_by_rover[route.rover_id].append(route)
    rovers = {}
    for rover_id, routes in routes_by_rover.items():
        rover_type = routes[0].rover_type
        equations = _module_equations(builder, rover_id, rover_type)
        rover = GenericRoverRuntime(
            env,
            rover_id,
            rover_type,
            equations,
            blueprint.rover_attributes.get(rover_type, {}),
            blueprint,
            events,
        )
        rovers[rover_id] = rover
        env.process(rover.run_routes(routes, modules))

    power = GenericPowerRuntime(env, blueprint, modules, rovers)
    env.process(power.run())
    log = {}

    def snapshot_logger():
        while True:
            log[str(round(env.now, 6))] = {
                **{module_id: module.snapshot() for module_id, module in modules.items()},
                **{rover_id: rover.snapshot() for rover_id, rover in rovers.items()},
                "Power_Manager": power.snapshot(),
            }
            yield env.timeout(1.0)

    env.process(snapshot_logger())
    env.run(until=blueprint.duration_hr)
    log[str(round(blueprint.duration_hr, 6))] = {
        **{module_id: module.snapshot() for module_id, module in modules.items()},
        **{rover_id: rover.snapshot() for rover_id, rover in rovers.items()},
        "Power_Manager": power.snapshot(),
    }

    route_totals = defaultdict(float)
    for rover in rovers.values():
        for route_id, amount in rover.delivered_by_route.items():
            route_totals[route_id] += amount
    outgoing_pairs = {
        (route.source_id, route.flow) for route in blueprint.routes
    }
    flow_totals = defaultdict(float)
    terminal_totals = defaultdict(float)
    flow_units = {}
    for route in blueprint.routes:
        amount = route_totals[route.route_id]
        flow_totals[route.flow] += amount
        flow_units[route.flow] = route.unit
        if (route.destination_id, route.flow) not in outgoing_pairs:
            terminal_totals[route.flow] += amount
    final_results = {
        "Engine": "GenericScenario",
        "Sim_Metrics": {
            "Simulation_Run_Time": round(time.perf_counter() - started, 4),
            "Simulation_Duration_hr": blueprint.duration_hr,
            "Active_Nodes": [spec.module_type for spec in blueprint.modules.values()],
        },
        "Modules": {
            module_id: module.snapshot() for module_id, module in modules.items()
        },
        "Rovers": {rover_id: rover.snapshot() for rover_id, rover in rovers.items()},
        "Resource_Flows": {
            flow: {
                "Unit": flow_units.get(flow, "kg"),
                "Transported": round(amount, 6),
                "Delivered_To_Terminal": round(terminal_totals[flow], 6),
            }
            for flow, amount in flow_totals.items()
        },
        "Power": power.snapshot(),
        "MoEs": {
            "Total_Resource_Transported": round(sum(flow_totals.values()), 6),
            "Total_Resource_Delivered_To_Terminals": round(
                sum(terminal_totals.values()), 6
            ),
            "Total_System_Demand_kWh": round(power.total_demand_kwh, 6),
            "Total_Energy_Generated_kWh": round(power.total_generated_kwh, 6),
            "Unserved_Energy_kWh": round(power.unserved_energy_kwh, 6),
            "Total_Transport_Distance_km": round(
                sum(rover.distance_km for rover in rovers.values()), 6
            ),
        },
        "Events": events,
    }
    results_path = Path(results_path)
    log_path = Path(log_path)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w") as handle:
        json.dump(final_results, handle, indent=2)
    with log_path.open("w") as handle:
        json.dump(log, handle, indent=2)
    return final_results
