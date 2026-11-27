"""Opt-in operations model for timed extraction, liquefaction and surface logistics."""

import math

import simpy

from S24.DES_pipeline_version.LunarRover import LunarRover
from S24.DES_pipeline_version.scenario_equations import evaluate_equations, get_equation_contract


TOL = 1e-9


def number(mapping, key, default=0, *, positive=False):
    value = float(mapping.get(key, default))
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{key} must be finite and {'positive' if positive else 'nonnegative'}")
    return value


class Stock:
    def __init__(self, env, capacity=math.inf, initial=0):
        self.env = env
        self.capacity = capacity
        self.mass = initial
        self.changed = env.event()
        if not 0 <= initial <= capacity:
            raise ValueError("Invalid initial stock")

    @property
    def space(self):
        return self.capacity - self.mass

    def add(self, delta):
        mass = self.mass + delta
        if not -TOL <= mass <= self.capacity + TOL:
            raise RuntimeError(f"Stock outside its capacity: {mass} / {self.capacity}")
        self.mass = mass
        self.changed.succeed()
        self.changed = self.env.event()


class EnergyBudget:
    """Integrate independent electrical and receiver-side thermal rates at event times."""

    def __init__(self, config, line_count):
        self.line_count = line_count
        self.active = 0
        self.chargers = {}
        self.time = 0
        self.peak_core = 0.0
        self.peak_thermal = 0.0
        self.peak_total_electric = 0.0
        self.totals = dict.fromkeys((
            "electric_available_kwh", "electric_core_kwh", "electric_charging_kwh",
            "electric_unserved_kwh", "electric_curtailed_kwh",
            "thermal_to_reactors_kwh", "all_lines_processing_hr",
        ), 0.0)
        self.supply = number(config, "electric_available_kw")
        self.idle = number(config, "electric_idle_kw")
        self.full = number(config, "electric_full_kw")
        self.heat_per_line = number(config, "thermal_per_line_kw")

    def advance(self, time):
        dt = time - self.time
        core = self.idle + (self.full - self.idle) * self.active / self.line_count
        charging = sum(self.chargers.values())
        net = self.supply - core - charging
        if dt > 0:
            self.peak_core = max(self.peak_core, core)
            self.peak_total_electric = max(self.peak_total_electric, core + charging)
            self.peak_thermal = max(self.peak_thermal, self.heat_per_line * self.active)
        self.totals["electric_available_kwh"] += self.supply * dt
        self.totals["electric_core_kwh"] += core * dt
        self.totals["electric_charging_kwh"] += charging * dt
        self.totals["electric_unserved_kwh"] += max(0, -net) * dt
        self.totals["electric_curtailed_kwh"] += max(0, net) * dt
        self.totals["thermal_to_reactors_kwh"] += self.heat_per_line * self.active * dt
        self.totals["all_lines_processing_hr"] += dt * (self.active == self.line_count)
        self.time = time


class BatchOperations:
    def __init__(self, config):
        self.env = simpy.Environment()
        self.config = config
        self.operations = config["batch_operations"]
        self.builder = config["scenario_builder"]
        self.events = []
        self.lines = {}
        self.vehicles = {}
        self.outputs = {}
        self.excavated = 0.0
        self.dumped = 0.0
        self.delivered_lox = 0.0
        self.max_mass_residual = 0.0
        self.duration = number(config["simulation"], "duration_hr", positive=True)
        for spec in self.operations["lines"]:
            name = spec["plant_id"]
            if name in self.lines:
                raise ValueError(f"Duplicate plant: {name}")
            self.lines[name] = {
                "spec": spec,
                "feed": Stock(self.env, number(spec, "feed_capacity_kg", positive=True),
                              number(spec, "initial_feed_kg")),
                "solid_in_process_kg": 0.0, "residue": Stock(self.env),
                "gas_kg": 0.0, "liquefying_kg": 0.0,
                "completed": 0, "missed": 0, "processed_kg": 0.0, "oxygen_kg": 0.0,
                "liquid_kg": 0.0,
            }
        if not self.lines:
            raise ValueError("At least one processing line is required")
        self.initial_feed = sum(line["feed"].mass for line in self.lines.values())
        self.energy = EnergyBudget(self.operations["power"], len(self.lines))
        self.liquefiers = {}
        for spec in self.operations["liquefiers"]:
            name = spec["id"]
            output = spec["output_id"]
            if name in self.liquefiers or output in self.outputs:
                raise ValueError("Liquefier and its output must each have a unique ID")
            self.outputs[output] = Stock(self.env, number(spec, "capacity_kg", positive=True))
            self.liquefiers[name] = (spec, simpy.Store(self.env))
        for name, line in self.lines.items():
            spec = line["spec"]
            if spec["liquefier_id"] not in self.liquefiers:
                raise ValueError(f"{name} has no liquefier")
            if number(spec, "batch_kg", positive=True) > line["feed"].capacity:
                raise ValueError(f"{name}: batch exceeds feed capacity")
            self.env.process(self.process_batches(name, line))
        for spec, queue in self.liquefiers.values():
            self.env.process(self.liquefy(spec, queue))
        self.depots = {
            name: Stock(self.env, number({"capacity": capacity}, "capacity", positive=True))
            for name, capacity in self.operations.get("depots_kg", {}).items()
        }
        self.depot_berths = {name: simpy.Resource(self.env) for name in self.depots}
        for name, line in self.lines.items():
            spec = line["spec"]
            regolith = spec["regolith_rover"]
            self.add_rover(regolith, "Regolith")
            haul = self.route(regolith["id"], "Regolith", destination=name)
            if "residue" in regolith:
                residue = self.route(regolith["id"], "Residue", source=name)
                self.route(regolith["id"], "ResidueReturn", source=residue["to"],
                           destination=haul["from"])
            self.env.process(self.supply_feed(name, line, regolith))
            if "lox_rover" in spec:
                lox = spec["lox_rover"]
                self.add_rover(lox, "LOX")
                liquefier = self.liquefiers[spec["liquefier_id"]][0]
                route = self.route(lox["id"], "LOX", source=liquefier["output_id"])
                if route["to"] not in self.depots:
                    raise ValueError(f"{lox['id']}: LOX route has no receiving depot")
                if sum("lox_rover" in item["spec"] and item["spec"]["liquefier_id"] == liquefier["id"]
                       for item in self.lines.values()) != 1:
                    raise ValueError("A liquid output supports one dedicated delivery vehicle")
                self.env.process(self.deliver_lox(route, lox))

    def log(self, actor, event, **details):
        _, residual = self.mass_balance()
        self.max_mass_residual = max(self.max_mass_residual, *map(abs, residual.values()))
        if self.max_mass_residual > 1e-7:
            raise RuntimeError(f"Material balance does not close: {residual}")
        self.events.append({"time_hr": self.env.now, "actor": actor, "event": event, **details})

    def equations(self, actor, fallback_type):
        equations = self.builder.get("module_equations", {})
        return equations.get(actor, equations.get(fallback_type, ""))

    def process_batches(self, name, line):
        spec = line["spec"]
        mass = number(spec, "batch_kg", positive=True)
        interval = number(spec, "slot_interval_hr", positive=True)
        first = number(spec, "first_slot_hr")
        queue = self.liquefiers[spec["liquefier_id"]][1]
        slots = math.ceil(max(0, self.duration - first) / interval)
        for index in range(slots):
            slot = first + index * interval
            if slot >= self.duration:
                break
            if slot < self.env.now - TOL:
                line["missed"] += 1
                self.log(name, "batch_missed", slot_hr=slot)
                continue
            if slot > self.env.now:
                yield self.env.timeout(slot - self.env.now)
            if line["feed"].mass + TOL < mass:
                line["missed"] += 1
                self.log(name, "batch_missed", slot_hr=slot)
                continue
            duration = number(spec, "processing_hr", positive=True)
            oxygen = mass * number(spec, "oxygen_yield")
            result = evaluate_equations(
                self.equations(name, "ISRUPlant"),
                {"RegolithIn": mass, "ProcessingTime": duration, "OxygenOut": oxygen,
                 "OxygenYield": number(spec, "oxygen_yield"), "SimulationTime": self.env.now},
                effect_outputs={"OxygenOut", "ProcessingTime"},
            )
            oxygen = result.get("OxygenOut", oxygen)
            duration = result.get("ProcessingTime", duration)
            if not 0 <= oxygen <= mass or duration <= 0:
                raise ValueError(f"{name}: invalid extraction equation outputs")
            line["feed"].add(-mass)
            line["solid_in_process_kg"] = mass
            self.energy.advance(self.env.now)
            self.energy.active += 1
            self.log(name, "batch_started", mass_kg=mass, duration_hr=duration)
            yield self.env.timeout(duration)
            self.energy.advance(self.env.now)
            self.energy.active -= 1
            line["solid_in_process_kg"] = 0
            line["residue"].add(mass - oxygen)
            line["gas_kg"] += oxygen
            line["oxygen_kg"] += oxygen
            line["completed"] += 1
            line["processed_kg"] += mass
            self.log(name, "batch_completed", mass_kg=mass, oxygen_kg=oxygen)
            if oxygen > 0:
                yield queue.put((name, oxygen))

    def liquefy(self, spec, queue):
        output = self.outputs[spec["output_id"]]
        rate = number(spec, "rate_kg_hr", positive=True)
        max_packet = number(spec, "packet_kg", positive=True)
        if max_packet > output.capacity:
            raise ValueError("A liquefaction packet cannot exceed output capacity")
        while True:
            origin, mass = yield queue.get()
            line = self.lines[origin]
            count = math.ceil(mass / max_packet)
            packet = mass / count
            for _ in range(count):
                while output.space + TOL < packet:
                    yield output.changed
                line["gas_kg"] -= packet
                line["liquefying_kg"] += packet
                self.log(spec["id"], "liquefaction_started", origin=origin, mass_kg=packet)
                yield self.env.timeout(packet / rate)
                line["liquefying_kg"] -= packet
                output.add(packet)
                line["liquid_kg"] += packet
                self.log(spec["id"], "liquid_available", origin=origin, destination=spec["output_id"],
                         mass_kg=packet)

    def add_rover(self, spec, resource):
        name = spec["id"]
        if name in self.vehicles:
            raise ValueError(f"Vehicle already assigned: {name}")
        battery = number(spec, "battery_kwh")
        rover_type = "RegolithRover" if resource == "Regolith" else "LOXRover"
        rover = LunarRover(self.env, name, "cargo", {
            "maxCapacity": number(spec, "payload_kg", positive=True),
            "energyPerKmPerKg": 0,
            "batteryCapacity": battery, "batteryCharge": battery,
            "totalDistanceTraveled": 0.0, "totalEnergyConsumed": 0.0,
            "hoursPerKm": 1 / number(spec, "speed_kph", positive=True),
        }, self.equations(name, rover_type))
        self.vehicles[name] = {
            "rover": rover, "cargo": None, "phase": None,
            "battery_added_kwh": 0.0,
        }

    def route(self, name, flow, source=None, destination=None):
        routes = [
            route for route in self.builder["resource_routes"]
            if route["rover_id"] == name and route["flow"].lower() == flow.lower()
            and (source is None or route["from"] == source)
            and (destination is None or route["to"] == destination)
        ]
        if len(routes) != 1:
            raise ValueError(f"{name}: expected one {flow} route for {source} → {destination}")
        number(routes[0], "distance_km")
        if "distance_km" not in routes[0]:
            raise ValueError(f"{name}: route is missing distance_km")
        return routes[0]

    def phase(self, vehicle, phase, duration, rate=0.0, **details):
        rover = vehicle["rover"]
        if vehicle["phase"] is not None:
            raise RuntimeError(f"Concurrent phases for {rover.name}")
        if rate > 0 and rate * duration > rover.batteryCharge + TOL:
            raise RuntimeError(f"{rover.name}: insufficient onboard charge for {phase}")
        vehicle["phase"] = (phase, self.env.now, rate)
        self.log(rover.name, "phase_start", phase=phase, duration_hr=duration, **details)
        yield self.env.timeout(duration)
        self.settle_vehicle(vehicle, self.env.now)
        vehicle["phase"] = None
        self.log(rover.name, "phase_end", phase=phase, **details)

    @staticmethod
    def settle_vehicle(vehicle, time):
        if vehicle["phase"] is None:
            return
        phase, start, rate = vehicle["phase"]
        rover = vehicle["rover"]
        energy = (time - start) * rate
        if energy < 0:
            added = min(-energy, max(0, rover.batteryCapacity - rover.batteryCharge))
            rover.batteryCharge += added
            vehicle["battery_added_kwh"] += added
        else:
            rover.batteryCharge -= energy
            rover.totalEnergyConsumed += energy
        vehicle["phase"] = (phase, time, rate)

    def travel_plan(self, vehicle, route, resource, cargo_mass, power):
        rover = vehicle["rover"]
        distance = number(route, "distance_km")
        result = rover.evaluateTransport(resource, cargo_mass, distance,
                                         slope_deg=route.get("mean_slope_deg", 0))
        duration = result["TravelTime"]
        if duration < 0 or (distance > 0 and duration == 0):
            raise ValueError(f"{rover.name}: invalid travel duration")
        if not math.isclose(result[f"{resource}Out"], cargo_mass, abs_tol=TOL):
            raise ValueError("Timed transport requires mass-preserving rover equations")
        energy = result["EnergyConsumed"] if "EnergyConsumed" in get_equation_contract(rover.scenarioEquations)["outputs"] else power * duration
        if energy < 0 or (duration == 0 and energy != 0):
            raise ValueError(f"{rover.name}: invalid travel energy")
        return duration, energy, distance

    def drive(self, vehicle, plan, route, direction):
        duration, energy, distance = plan
        origin, destination = route["from"], route["to"]
        if direction == "return":
            origin, destination = destination, origin
        yield from self.phase(vehicle, f"drive_{direction}", duration,
                              energy / duration if duration else 0, origin=origin,
                              destination=destination, distance_km=distance,
                              route_id=route.get("id"), route_direction=direction)
        vehicle["rover"].totalDistanceTraveled += distance

    def recharge(self, vehicle, spec):
        name = vehicle["rover"].name
        rate = number(spec, "charge_kw", positive=True)
        efficiency = number(spec, "charge_efficiency", positive=True)
        if efficiency > 1:
            raise ValueError("Charging efficiency must not exceed 1")
        duration = number(spec, "charge_hr", positive=True)
        self.energy.advance(self.env.now)
        self.energy.chargers[name] = rate
        yield from self.phase(vehicle, "charge", duration, -rate * efficiency)
        self.energy.advance(self.env.now)
        del self.energy.chargers[name]

    def supply_feed(self, name, line, spec):
        vehicle = self.vehicles[spec["id"]]
        rover = vehicle["rover"]
        route = self.route(rover.name, "Regolith", destination=name)
        residue = spec.get("residue")
        residue_route = self.route(rover.name, "Residue", source=name) if residue else None
        duty_kw = number(spec, "duty_kw")
        period = number(spec, "schedule_period_hr", positive=True)
        day_count = math.ceil(self.duration / period)
        calendar = [(day * period + offset, kind)
                    for day in range(day_count)
                    for kind, offsets in (
                        ("regolith", spec["supply_slots_hr"]),
                        ("residue", residue["slots_hr"] if residue else []),
                    ) for offset in offsets]
        charge_interval = number(spec, "charge_interval_hr")
        if charge_interval:
            calendar += [(index * charge_interval, "charge")
                         for index in range(1, math.ceil(self.duration / charge_interval))]
        for when, mission in sorted(calendar):
            if when >= self.duration:
                break
            if when < self.env.now - TOL:
                if mission != "charge":
                    self.log(rover.name, "mission_missed", mission=mission, slot_hr=when, reason="busy")
                    continue
            elif when > self.env.now:
                yield self.env.timeout(when - self.env.now)
            if self.env.now >= self.duration:
                break
            if mission == "charge":
                yield from self.recharge(vehicle, spec)
                continue
            supplying = mission == "regolith"
            stock = line["feed"] if supplying else line["residue"]
            travel_route = route if supplying else residue_route
            handling = spec if supplying else residue
            mass = min(rover.maxCapacity if supplying else number(residue, "payload_kg", positive=True),
                       stock.space if supplying else stock.mass)
            if mass <= TOL:
                self.log(rover.name, "mission_missed", mission=mission, slot_hr=when, reason="stock")
                continue
            resource = "Regolith" if supplying else "Residue"
            out = self.travel_plan(vehicle, travel_route, resource, mass, duty_kw)
            back = self.travel_plan(vehicle, travel_route, resource, 0, duty_kw)
            load = number(handling, "load_hr")
            unload = number(handling, "unload_hr")
            reposition = []
            if not supplying:
                # Every scheduled mission begins at the excavation/charging point.
                approach = self.travel_plan(vehicle, route, "Regolith", 0, duty_kw)
                reposition.append((approach, route, "out"))
                direct_return = self.route(rover.name, "ResidueReturn", source=travel_route["to"],
                                           destination=route["from"])
                back = self.travel_plan(vehicle, direct_return, "Residue", 0, duty_kw)
            required = out[1] + back[1] + sum(plan[1] for plan, _, _ in reposition)
            required += (load + unload) * duty_kw
            minimum = number(spec, "reserve_kwh")
            if rover.batteryCharge + TOL < minimum + required:
                if spec.get("recharge_as_needed"):
                    self.log(rover.name, "mission_missed", mission=mission, slot_hr=when, reason="charging")
                    yield from self.recharge(vehicle, spec)
                    continue
                self.log(rover.name, "mission_missed", mission=mission, slot_hr=when, reason="battery")
                continue
            for plan, reposition_route, direction in reposition:
                yield from self.drive(vehicle, plan, reposition_route, direction)
            self.log(rover.name, "mission_started", mission=mission, mass_kg=mass)
            yield from self.phase(vehicle, f"load_{mission}", load, duty_kw, mass_kg=mass)
            if supplying:
                self.excavated += mass
            else:
                stock.add(-mass)
            # Residue is an alternate cargo rating of the same physical vehicle.
            vehicle["cargo"] = (mission, mass)
            yield from self.drive(vehicle, out, travel_route, "out")
            yield from self.phase(vehicle, f"unload_{mission}", unload, duty_kw, mass_kg=mass)
            if supplying:
                stock.add(mass)
            else:
                self.dumped += mass
            vehicle["cargo"] = None
            self.log(rover.name, "material_delivered", resource=resource, mass_kg=mass,
                     destination=travel_route["to"])
            if supplying:
                yield from self.drive(vehicle, back, travel_route, "return")
            else:
                yield from self.drive(vehicle, back, direct_return, "out")
            self.log(rover.name, "mission_completed", mission=mission, mass_kg=mass)

    def deliver_lox(self, route, spec):
        vehicle = self.vehicles[spec["id"]]
        rover = vehicle["rover"]
        source, destination = self.outputs[route["from"]], self.depots[route["to"]]
        threshold = number(spec, "dispatch_kg", positive=True)
        poll = number(spec, "poll_hr", positive=True)
        while True:
            if source.mass + TOL < threshold:
                yield self.env.timeout(poll)
                continue
            mass = min(source.mass, rover.maxCapacity)
            out = self.travel_plan(vehicle, route, "LOX", mass, 0)
            back = self.travel_plan(vehicle, route, "LOX", 0, 0)
            if out[1] + back[1] > rover.batteryCharge + TOL:
                raise RuntimeError(f"{rover.name}: inadequate battery for round trip")
            yield from self.phase(vehicle, "load_lox", number(spec, "load_hr"), mass_kg=mass)
            source.add(-mass)
            vehicle["cargo"] = ("lox", mass)
            yield from self.drive(vehicle, out, route, "out")
            if mass > destination.capacity + TOL:
                raise ValueError("LOX cargo exceeds the destination's entire capacity")
            vehicle["phase"] = ("depot_wait", self.env.now, 0.0)
            self.log(rover.name, "depot_wait_started", destination=route["to"])
            with self.depot_berths[route["to"]].request() as berth:
                yield berth
                while destination.space + TOL < mass:
                    yield destination.changed
                vehicle["phase"] = None
                self.log(rover.name, "depot_wait_ended", destination=route["to"])
                yield from self.phase(vehicle, "unload_lox", number(spec, "unload_hr"), mass_kg=mass)
                destination.add(mass)
                self.delivered_lox += mass
                vehicle["cargo"] = None
                self.log(rover.name, "material_delivered", resource="LOX", mass_kg=mass,
                         destination=route["to"])
            yield from self.drive(vehicle, back, route, "return")

    def mass_balance(self):
        cargo = dict.fromkeys(("regolith", "residue", "lox"), 0.0)
        for vehicle in self.vehicles.values():
            if vehicle["cargo"]:
                kind, mass = vehicle["cargo"]
                cargo[kind] += mass
        feed = sum(line["feed"].mass + line["solid_in_process_kg"] + line["processed_kg"]
                   for line in self.lines.values())
        residues = sum(line["processed_kg"] - line["oxygen_kg"] - line["residue"].mass
                       for line in self.lines.values())
        oxygen = sum(line["oxygen_kg"] - line["gas_kg"] - line["liquefying_kg"]
                     for line in self.lines.values())
        liquid = sum(stock.mass for stock in self.outputs.values())
        depot = sum(stock.mass for stock in self.depots.values())
        return cargo, {
            "feed": self.initial_feed + self.excavated - cargo["regolith"] - feed,
            "residue": residues - cargo["residue"] - self.dumped,
            "oxygen": oxygen - liquid - depot - cargo["lox"],
        }

    def snapshot(self, time):
        self.energy.advance(time)
        lines = {
            name: {**{key: line[key] for key in (
                "solid_in_process_kg", "gas_kg", "liquefying_kg", "completed", "missed",
                "processed_kg", "oxygen_kg", "liquid_kg",
            )}, "feed_kg": line["feed"].mass, "residue_kg": line["residue"].mass}
            for name, line in self.lines.items()
        }
        vehicles = {}
        cargo, residual = self.mass_balance()
        for name, vehicle in self.vehicles.items():
            self.settle_vehicle(vehicle, time)
            rover = vehicle["rover"]
            kind, mass = vehicle["cargo"] or (None, 0.0)
            vehicles[name] = {
                "phase": vehicle["phase"][0] if vehicle["phase"] else "waiting",
                "cargo_resource": kind, "cargo_kg": mass, "battery_kwh": rover.batteryCharge,
                "battery_added_kwh": vehicle["battery_added_kwh"],
                "traction_and_handling_kwh": rover.totalEnergyConsumed,
                "completed_distance_km": rover.totalDistanceTraveled,
            }
        liquid = {name: stock.mass for name, stock in self.outputs.items()}
        depots = {name: stock.mass for name, stock in self.depots.items()}
        return {
            "time_hr": time, "lines": lines, "vehicles": vehicles, "liquid_stocks_kg": liquid,
            "depots_kg": depots, "mass_in_transit_kg": cargo, "excavated_kg": self.excavated,
            "residue_dumped_kg": self.dumped, "delivered_lox_kg": self.delivered_lox,
            "mass_residual_kg": residual,
            "energy": {
                **self.energy.totals, "electric_peak_core_kw": self.energy.peak_core,
                "thermal_peak_to_reactors_kw": self.energy.peak_thermal,
                "electric_peak_with_charging_kw": self.energy.peak_total_electric,
            },
        }

    def run(self):
        step = number(self.config["simulation"], "sample_hr", 1, positive=True)
        times = [index * step for index in range(math.ceil(self.duration / step))
                 if index * step < self.duration]
        snapshots = []
        for time in [*times, self.duration]:
            while self.env.peek() <= time:
                self.env.step()
            snapshots.append(self.snapshot(time))
        return {"summary": snapshots[-1], "time_series": snapshots, "events": self.events,
                "max_event_mass_residual_kg": self.max_mass_residual}
