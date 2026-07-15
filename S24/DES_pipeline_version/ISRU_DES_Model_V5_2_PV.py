"""
Name:       ISRU_DES_Model_V5_2_PV.py
Scenario:   Discrete event simulation of an ISRU processing plant on the moon. Most technical information gathered from: https://doi.org/10.1073/pnas.2306146122 
Model:      Entities: ...
            Resources: ...
            Containers: ...
            etc.
Author:     Mustafa Siddiqui
Created:    2026-01-14
Updated:    2026-01-29 - Enhanced with power generation, habitation, communications, rovers, and landing zone
"""

"""
References:
[1] https://doi.org/10.1073/pnas.2306146122 
"""

import simpy
import sys
import os

# Make sure the repo root is on the path so package imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from S24.DES_pipeline_version.ISRUPlant import ISRUPlant
from S24.DES_pipeline_version.SolarPowerSystem import SolarPowerSystem
from S24.DES_pipeline_version.PowerManager import (
    EquationPowerConsumer,
    PowerManager,
    PowerModelConsumer,
    StaticPowerConsumer,
)
from S24.DES_pipeline_version.HabitationModule import HabitationModule
from S24.DES_pipeline_version.CommunicationModule import CommunicationModule
from S24.DES_pipeline_version.LunarRover import LunarRover
from S24.DES_pipeline_version.RoverChargingStation import RoverChargingStation
from S24.DES_pipeline_version.LandingLaunchZone import LandingLaunchZone
from S24.DES_pipeline_version.ImportUtility import data_from_json
from S24.DES_pipeline_version.LoggingManager import LoggingManager
from S24.DES_pipeline_version.scenario_config import load_scenario_config
from S24.DES_pipeline_version.scenario_equations import evaluate_equations
import json
import time
import re


def test_function():
    print("Hello! I come to you from ISRU_DES_Model_V4_PV.py. I am a test function to check that the file is running and importing correctly.")

# -------------------------------------------------
# Rover Process (Modified to work with new rover system)
# -------------------------------------------------
def rover(system, regolithBuffer, batchSize, travelTime):
    """Continuously delivers regolith to the plant"""
    while True:
        yield system.timeout(travelTime)
        yield regolithBuffer.put(batchSize)
        print(f"[{system.now:.2f} hr] Rover delivered {batchSize} kg regolith")

def _least_filled_regolith_target(targets, rover_load):
    eligible = [
        target for target in targets
        if target["buffer"].capacity - target["buffer"].level - target["reserved_inbound_kg"] >= rover_load
    ]
    if not eligible:
        return None
    return min(
        eligible,
        key=lambda target: (
            (target["buffer"].level + target["reserved_inbound_kg"]) / target["buffer"].capacity,
            target["instance_id"],
        ),
    )


class RegolithSourceRuntime:
    def __init__(self, system, name, attributes, equations):
        self.system = system
        self.name = name
        self.attributes = dict(attributes)
        self.equations = equations or ""
        self.totalEnergyConsumed = 0.0
        self.pendingPowerDemand = 0.0
        self.lastEquationOutputs = {}
        self.lastRequestedRegolith = 0.0

    def produce(self, requested_kg, simulation_time):
        self.lastRequestedRegolith = float(requested_kg)
        context = {
            key: value for key, value in self.attributes.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        context.update({
            "SimulationTime": float(simulation_time),
            "RequestedRegolith": float(requested_kg),
            "RegolithOut": float(requested_kg),
            "PowerIn": 0.0,
            "EnergyConsumed": 0.0,
        })
        outputs = evaluate_equations(
            self.equations,
            context,
            effect_outputs={"RegolithOut", "PowerIn", "EnergyConsumed"},
        )
        self.lastEquationOutputs = outputs
        produced = outputs.get("RegolithOut", requested_kg)
        energy = outputs.get("EnergyConsumed", 0.0)
        if produced < 0:
            raise RuntimeError(f"{self.name}: RegolithOut cannot be negative")
        if energy < 0:
            raise RuntimeError(f"{self.name}: EnergyConsumed cannot be negative")
        self.totalEnergyConsumed += energy
        self.pendingPowerDemand += energy
        return produced

    def getCurrentPowerDemand(self, dt):
        context = {
            key: value for key, value in self.attributes.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        context.update({
            "SimulationTime": float(self.system.now),
            "RequestedRegolith": self.lastRequestedRegolith,
            "RegolithOut": self.lastRequestedRegolith,
            "PowerIn": 0.0,
            "EnergyConsumed": 0.0,
        })
        outputs = evaluate_equations(
            self.equations,
            context,
            effect_outputs={"RegolithOut", "PowerIn", "EnergyConsumed"},
        )
        continuous_energy = outputs.get("PowerIn", 0.0) * dt
        if continuous_energy < 0:
            raise RuntimeError(f"{self.name}: PowerIn cannot be negative")
        demand = self.pendingPowerDemand + continuous_energy
        self.pendingPowerDemand = 0.0
        self.totalEnergyConsumed += continuous_energy
        return demand

    def getLoggingAttributes(self):
        return {
            "Name": self.name,
            "total_energy_consumed": self.totalEnergyConsumed,
            "scenario_equation_outputs": self.lastEquationOutputs,
        }


class PropellantDepotRuntime:
    def __init__(self, system, name, attributes, equations):
        self.system = system
        self.name = name
        self.attributes = dict(attributes)
        self.equations = equations or ""
        self.loxStored = 0.0
        self.totalEnergyConsumed = 0.0
        self.pendingEventEnergy = 0.0
        self.lastEquationOutputs = {}

    def _evaluate(self, lox_in, dt):
        context = {
            key: value for key, value in self.attributes.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool)
        }
        context.update({
            "SimulationTime": float(self.system.now),
            "dt": float(dt),
            "LOXIn": float(lox_in),
            "LOXStored": float(self.loxStored),
            "PowerIn": 0.0,
            "EnergyConsumed": 0.0,
        })
        outputs = evaluate_equations(
            self.equations,
            context,
            effect_outputs={"LOXIn", "LOXStored", "PowerIn", "EnergyConsumed"},
        )
        self.lastEquationOutputs = outputs
        return outputs

    def receiveLOX(self, amount):
        outputs = self._evaluate(amount, 0.0)
        accepted = outputs.get("LOXIn", amount)
        if accepted < 0 or accepted > amount:
            raise RuntimeError(f"{self.name}: LOXIn must be between 0 and delivered LOX")
        self.loxStored = outputs.get("LOXStored", self.loxStored + accepted)
        if self.loxStored < 0:
            raise RuntimeError(f"{self.name}: LOXStored cannot be negative")
        event_energy = outputs.get("EnergyConsumed", 0.0)
        if event_energy < 0:
            raise RuntimeError(f"{self.name}: EnergyConsumed cannot be negative")
        self.totalEnergyConsumed += event_energy
        self.pendingEventEnergy += event_energy
        print(
            f"[{self.system.now:.2f} hr] {self.name}: Received {accepted:.2f} kg LOX "
            f"(Total stored: {self.loxStored:.2f} kg)"
        )

    def getCurrentPowerDemand(self, dt):
        outputs = self._evaluate(0.0, dt)
        if "LOXStored" in outputs:
            if outputs["LOXStored"] < 0:
                raise RuntimeError(f"{self.name}: LOXStored cannot be negative")
            self.loxStored = outputs["LOXStored"]
        if "PowerIn" in outputs:
            continuous_demand = outputs["PowerIn"] * dt
        else:
            continuous_demand = 0.0
        demand = continuous_demand + self.pendingEventEnergy
        self.pendingEventEnergy = 0.0
        if demand < 0:
            raise RuntimeError(f"{self.name}: PowerIn cannot be negative")
        self.totalEnergyConsumed += continuous_demand
        return demand

    def getLoggingAttributes(self):
        return {
            "Name": self.name,
            "LOX_Stored": self.loxStored,
            "total_energy_consumed": self.totalEnergyConsumed,
            "scenario_equation_outputs": self.lastEquationOutputs,
        }


def regolithRoverController(system, plant_targets, rover_load, rover: LunarRover, poll_dt=0.1):
    """Dispatch a shared rover to the least-filled eligible ISRU plant."""
    while True:
        target = _least_filled_regolith_target(plant_targets, rover_load)
        if target is None:
            yield system.timeout(poll_dt)
            continue

        source = target["source"]
        source_output = min(
            rover_load,
            source.produce(rover_load, system.now),
            rover.maxCapacity,
        )
        if source_output <= 0:
            yield system.timeout(poll_dt)
            continue

        target["reserved_inbound_kg"] += source_output
        reservation_active = True
        try:
            rover.loadCargo(source_output)
            outbound_outputs = rover.evaluateTransport(
                "Regolith", source_output, target["distance_km"]
            )
            yield system.process(rover.travel(target["distance_km"], outbound_outputs))
            unloaded = rover.unloadCargo()
            delivered = outbound_outputs.get("RegolithOut", unloaded)
            if delivered < 0 or delivered > unloaded:
                raise RuntimeError(
                    f"{rover.name}: RegolithOut must be between 0 and RegolithIn"
                )
            yield target["buffer"].put(delivered)
            target["reserved_inbound_kg"] -= source_output
            reservation_active = False
            print(
                f"[{system.now:.2f} hr] {rover.name} delivered {delivered:.2f} kg regolith "
                f"to {target['instance_id']} (input inventory: {target['buffer'].level:.2f} kg)"
            )
            return_outputs = rover.evaluateTransport(
                "Regolith", 0.0, target["distance_km"]
            )
            yield system.process(rover.travel(target["distance_km"], return_outputs))
            print(
                f"[{system.now:.2f} hr] {rover.name} returned empty from "
                f"{target['instance_id']} to its regolith loading point"
            )
        finally:
            if reservation_active:
                target["reserved_inbound_kg"] -= source_output

# -------------------------------------------------
# Plant Controller
# -------------------------------------------------
def plantController(system, plant, regolithBuffer, batchSize):
    """Waits for regolith, then processes it"""
    while True:
        yield regolithBuffer.get(batchSize)
        yield system.process(plant.processRegolith(system, batchSize))


def _scenario_instances(scenario_builder, module_type, fallback_count):
    instances = [
        instance for instance in scenario_builder.get("instances", [])
        if instance.get("type") == module_type and instance.get("placed", True)
    ]
    if instances:
        return instances
    return [
        {
            "id": module_type if fallback_count == 1 else f"{module_type}_{index + 1}",
            "type": module_type,
        }
        for index in range(fallback_count)
    ]


def _module_equations(scenario_builder, instance_id, module_type):
    equations = scenario_builder.get("module_equations", {})
    return equations.get(instance_id, equations.get(module_type, ""))


def _module_power_model(scenario_config, instance_id, module_type):
    models = scenario_config.get("power", {}).get("module_models", {})
    return models.get(instance_id, models.get(module_type))


def _base_instance_type(instance_id):
    return re.sub(r"_\d+$", "", str(instance_id or ""))


def _resource_route(scenario_builder, flow, target_id):
    routes = [
        route for route in scenario_builder.get("resource_routes", [])
        if str(route.get("flow", "")).lower() == flow.lower()
    ]
    direct = next((route for route in routes if route.get("to") == target_id), None)
    return direct or (routes[0] if len(routes) == 1 else None)


def _resource_route_from(scenario_builder, flow, source_id):
    routes = [
        route for route in scenario_builder.get("resource_routes", [])
        if str(route.get("flow", "")).lower() == flow.lower()
    ]
    direct = next((route for route in routes if route.get("from") == source_id), None)
    return direct or (routes[0] if len(routes) == 1 else None)


def _resource_routes_for_rover(scenario_builder, flow, rover_id):
    routes = [
        route for route in scenario_builder.get("resource_routes", [])
        if str(route.get("flow", "")).lower() == flow.lower()
    ]
    assigned = [route for route in routes if route.get("rover_id") == rover_id]
    if assigned:
        return assigned
    return [route for route in routes if not route.get("rover_id")]


def _has_assigned_resource_routes(scenario_builder, flow):
    return any(
        route.get("rover_id")
        for route in scenario_builder.get("resource_routes", [])
        if str(route.get("flow", "")).lower() == flow.lower()
    )


def _resource_route_distance(scenario_builder, flow, target_id, fallback):
    route = _resource_route(scenario_builder, flow, target_id)
    if not route:
        return fallback
    try:
        return float(route.get("distance_km", fallback))
    except (TypeError, ValueError):
        return fallback


# -------------------------------------------------
# LOX Storage Energy
# -------------------------------------------------
def LOXStorageEnergy(system, plant, dt=1.0, energyCoeff=0.31):
    """
    Continuously accounts for LOX storage energy.
    dt = accounting time step (hours)
    """
    while True:
        yield system.timeout(dt)

        storageEnergy = energyCoeff * plant.LOXStored * dt
        plant.recordEnergyDemand(storageEnergy)

def LOXDeliveryController(system, plant: ISRUPlant, roverStore: simpy.Store,
                          destination,
                          distance, transportThreshold, poll_dt=1.0,
                          assignedRoverId=None):
    """
    Per-plant LOX delivery controller (first-come-first-served).

    Each plant runs its own instance of this process. When a plant's LOX
    reaches the transport threshold it waits for an available rover from the
    shared roverStore. This supports one or more LOX rovers without changing
    the plant-side dispatch logic.
    """
    while True:
        yield system.timeout(poll_dt)
        if plant.LOXStored >= transportThreshold:
            print(f"[{system.now:.2f} hr] {plant.name} reached threshold "
                  f"({plant.LOXStored:.2f} kg LOX). Queuing for LOX rover.")

            rover = yield (
                roverStore.get(lambda candidate: getattr(candidate, "instanceId", None) == assignedRoverId)
                if assignedRoverId else roverStore.get()
            )
            try:
                # Rover has arrived: load up to its payload capacity and leave
                # any excess inventory at the plant for a later trip.
                LOXToTransport = min(plant.LOXStored, rover.maxCapacity)
                plant.LOXStored -= LOXToTransport
                print(f"[{system.now:.2f} hr] {plant.name} acquired {rover.name}, "
                      f"beginning delivery of {LOXToTransport:.2f} kg.")
                rover.loadCargo(LOXToTransport)
                outbound_outputs = rover.evaluateTransport("LOX", LOXToTransport, distance)
                yield system.process(rover.travel(distance, outbound_outputs))
                unloaded = rover.unloadCargo()
                delivered = outbound_outputs.get("LOXOut", unloaded)
                if delivered < 0 or delivered > unloaded:
                    raise RuntimeError(f"{rover.name}: LOXOut must be between 0 and LOXIn")
                plant.LOXStored += unloaded - delivered
                destination.receiveLOX(delivered)
                print(f"[{system.now:.2f} hr] {plant.name} delivered "
                      f"{delivered:.2f} kg LOX to {destination.name} "
                      f"(total there: {destination.loxStored:.2f} kg). "
                      f"{rover.name} beginning empty return.")
                return_outputs = rover.evaluateTransport("LOX", 0.0, distance)
                yield system.process(rover.travel(distance, return_outputs))
                print(f"[{system.now:.2f} hr] {rover.name} returned empty to {plant.name}.")
            finally:
                yield roverStore.put(rover)

# -------------------------------------------------
# Check Scenario Validity
# -------------------------------------------------
def check_scenario_validity(active_nodes, raiseError=True):
    #Use the raiseError flag to control whether to raise an exception for invalid scenarios or just return a list of messages.  This allows the function to be used both as a pre-flight check (with exceptions) and as a more user-friendly validator that collects all issues in one go (without exceptions).

    #Create a "fake" optionsDict to reuse the existing active_nodes processing logic and checks in run_scenario.
    optionsDict = {"active_nodes": active_nodes}

    #Compile all Errors and Warnings for the User in a list of messages
    messages = []

    VALID_NODES = {
        "HabitationModule",
        "ISRUPlant",
        "LaunchLandingZone",
        "LOXRover",
        "RegolithRover",
        "SolarPowerSystem",
        "CommunicationModule",
    }

    active_nodes_raw = optionsDict.get("active_nodes", list(VALID_NODES))
    active_nodes = set(active_nodes_raw)

    # Warn about any unrecognised node names so typos are caught early.
    unknown = active_nodes - VALID_NODES
    if unknown:
        print(f"[WARNING] run_scenario: unrecognised active_nodes entry/entries "
              f"will be ignored: {sorted(unknown)}")
        messages.append(f"[WARNING] Unrecognized active_nodes entry/entries will be ignored: {sorted(unknown)}")
    active_nodes &= VALID_NODES  # only keep valid names

    # Hard requirement check.
    missing_core = {"ISRUPlant", "RegolithRover"} - active_nodes
    if missing_core:
        messages.append(f"[ERROR] run_scenario requires at least 'ISRUPlant' and 'RegolithRover' in active_nodes. Missing: {sorted(missing_core)}")
        if raiseError:
            raise ValueError(
                f"run_scenario requires at least 'ISRUPlant' and 'RegolithRover' "
                f"in active_nodes.  Missing: {sorted(missing_core)}"
            )
        else:
            print(f"[ERROR] run_scenario requires at least 'ISRUPlant' and 'RegolithRover' in active_nodes. Missing: {sorted(missing_core)}")

    # Convenience flags — used throughout the function to gate
    # construction, process spawning, printing, and result export.
    use_isru          = "ISRUPlant"          in active_nodes  # always True (checked above)
    use_regolith_rover= "RegolithRover"      in active_nodes  # always True (checked above)
    use_solar         = "SolarPowerSystem"   in active_nodes
    use_habitat       = "HabitationModule"   in active_nodes
    use_comms         = "CommunicationModule"in active_nodes
    use_landing_zone  = "LaunchLandingZone"  in active_nodes
    use_lox_rover     = "LOXRover"           in active_nodes

    # Dependency notes (logged, not errors):
    # • ISRUPlant can run without SolarPowerSystem — it just won't be
    #   power-managed and totalEnergyConsumed won't be throttled.
    # • LOXRover without LaunchLandingZone: rover is built but has no
    #   destination; LOX delivery process is not spawned.
    # • HabitationModule / CommunicationModule without SolarPowerSystem:
    #   they are created but cannot be registered with a power manager,
    #   so their power draws are not accounted for.
    if use_habitat and not use_solar:
        print("[INFO] HabitationModule present but SolarPowerSystem absent — "
              "habitat power draw will not be managed.")
        messages.append("[INFO] HabitationModule present but SolarPowerSystem absent — "
              "habitat power draw will not be managed.")
    if use_comms and not use_solar:
        print("[INFO] CommunicationModule present but SolarPowerSystem absent — "
              "comms power draw will not be managed.")
        messages.append("[INFO] CommunicationModule present but SolarPowerSystem absent — "
              "comms power draw will not be managed.")
    if use_isru and not use_solar:
        print("[INFO] ISRUPlant present but SolarPowerSystem absent — "
              "ISRU power draw will not be managed.")
        messages.append("[INFO] ISRUPlant present but SolarPowerSystem absent — "
              "ISRU power draw will not be managed.")
    if use_landing_zone and not use_solar:
        print("[INFO] LaunchLandingZone present but SolarPowerSystem absent — "
              "landing zone power draw will not be managed.")
        messages.append("[INFO] LaunchLandingZone present but SolarPowerSystem absent — "
              "landing zone power draw will not be managed.")
    if use_lox_rover and not use_landing_zone:
        print("[INFO] LOXRover is active but LaunchLandingZone is not — "
              "LOX delivery process will not be spawned (no destination).")
        messages.append("[INFO] LOXRover is active but LaunchLandingZone is not — "
              "LOX delivery process will not be spawned (no destination).")
    if use_landing_zone and not use_lox_rover:
        print("[INFO] LaunchLandingZone is active but LOXRover is not — "
              "LOX delivery process will not be spawned (no transport).")
        messages.append("[INFO] LaunchLandingZone is active but LOXRover is not — "
              "LOX delivery process will not be spawned (no transport).")
        
    return messages

# -------------------------------------------------
# Run Scenario
# -------------------------------------------------
def run_scenario(optionsDict):
    start_time = time.perf_counter()
    scenario_config = load_scenario_config(optionsDict)

    # =========================================================
    # ACTIVE NODES: Determine which systems are included in this
    # simulation run.  The caller must supply a list of strings
    # under the key "active_nodes".  Unknown node names are
    # flagged as warnings so typos don't silently drop systems.
    #
    # Valid node names:
    #   HabitationModule, ISRUPlant, LaunchLandingZone,
    #   LOXRover, RegolithRover, SolarPowerSystem,
    #   CommunicationModule
    #
    # Hard requirement: ISRUPlant AND RegolithRover must both be
    # present — they form the irreducible core of the simulation.
    # =========================================================
    VALID_NODES = {
        "HabitationModule",
        "ISRUPlant",
        "LaunchLandingZone",
        "LOXRover",
        "RegolithRover",
        "SolarPowerSystem",
        "CommunicationModule",
    }

    active_nodes_raw = optionsDict.get("active_nodes", list(VALID_NODES))
    active_nodes = set(active_nodes_raw)

    # Warn about any unrecognised node names so typos are caught early.
    unknown = active_nodes - VALID_NODES
    if unknown:
        print(f"[WARNING] run_scenario: unrecognised active_nodes entry/entries "
              f"will be ignored: {sorted(unknown)}")
    active_nodes &= VALID_NODES  # only keep valid names

    # Hard requirement check.
    missing_core = {"ISRUPlant", "RegolithRover"} - active_nodes
    if missing_core:
        raise ValueError(
            f"run_scenario requires at least 'ISRUPlant' and 'RegolithRover' "
            f"in active_nodes.  Missing: {sorted(missing_core)}"
        )

    # Convenience flags — used throughout the function to gate
    # construction, process spawning, printing, and result export.
    use_isru          = "ISRUPlant"          in active_nodes  # always True (checked above)
    use_regolith_rover= "RegolithRover"      in active_nodes  # always True (checked above)
    use_solar         = "SolarPowerSystem"   in active_nodes
    use_habitat       = "HabitationModule"   in active_nodes
    use_comms         = "CommunicationModule"in active_nodes
    use_landing_zone  = "LaunchLandingZone"  in active_nodes
    use_lox_rover     = "LOXRover"           in active_nodes

    # Dependency notes (logged, not errors):
    # • ISRUPlant can run without SolarPowerSystem — it just won't be
    #   power-managed and totalEnergyConsumed won't be throttled.
    # • LOXRover without LaunchLandingZone: rover is built but has no
    #   destination; LOX delivery process is not spawned.
    # • HabitationModule / CommunicationModule without SolarPowerSystem:
    #   they are created but cannot be registered with a power manager,
    #   so their power draws are not accounted for.
    if use_habitat and not use_solar:
        print("[INFO] HabitationModule present but SolarPowerSystem absent — "
              "habitat power draw will not be managed.")
    if use_comms and not use_solar:
        print("[INFO] CommunicationModule present but SolarPowerSystem absent — "
              "comms power draw will not be managed.")
    if use_isru and not use_solar:
        print("[INFO] ISRUPlant present but SolarPowerSystem absent — "
              "ISRU power draw will not be managed.")
    if use_landing_zone and not use_solar:
        print("[INFO] LaunchLandingZone present but SolarPowerSystem absent — "
              "landing zone power draw will not be managed.")
    if use_lox_rover and not use_landing_zone:
        print("[INFO] LOXRover is active but LaunchLandingZone is not — "
              "LOX delivery process will not be spawned (no destination).")
    if use_landing_zone and not use_lox_rover:
        print("[INFO] LaunchLandingZone is active but LOXRover is not — "
              "LOX delivery process will not be spawned (no transport).")

    # Experiment data -----------------------------------------
    experiment = "ISRU Processing Plant – Active Nodes: " + ", ".join(sorted(active_nodes))
    scenario_builder = scenario_config.get("scenario_builder", {})
    supported_equation_modules = {
        "ISRUPlant",
        "ISRUExcavation",
        "RegolithRover",
        "LOXRover",
        "SolarPowerSystem",
        "HabitationModule",
        "CommunicationModule",
        "LaunchLandingZone",
        "PropellantDepot",
    }
    unsupported_equations = [
        module_id for module_id, equations in scenario_builder.get("module_equations", {}).items()
        if str(equations or "").strip()
        and _base_instance_type(module_id) not in supported_equation_modules
    ]
    if unsupported_equations:
        raise ValueError(
            "No DES equation runtime exists for module(s): "
            + ", ".join(sorted(unsupported_equations))
        )
    regolith_config = scenario_config["regolith"]
    rover_load = float(regolith_config.get(
        "rover_load_kg",
        regolith_config.get("batch_kg", 4000.0),
    ))
    plant_batch = float(regolith_config.get(
        "plant_batch_kg",
        regolith_config.get("batch_kg", rover_load),
    ))
    plant_input_capacity = float(regolith_config.get(
        "plant_input_capacity_kg",
        regolith_config.get("buffer_capacity_kg", 20000.0),
    ))
    regolith_dispatch_poll_dt = float(regolith_config.get("dispatch_poll_dt_hr", 0.1))
    simDuration = scenario_config["simulation"]["duration_hr"]

    num_regolith_rovers = scenario_config["rovers"]["regolith"]["count"]
    num_lox_rovers      = scenario_config["rovers"]["lox"]["count"]
    num_isru_plants     = scenario_config["isru"]["plant_count"]
    continuous_power    = scenario_config["power"].get("continuous_load_kw", {})
    if num_regolith_rovers < 1:
        raise ValueError("At least one regolith rover is required by the current ISRU process")

    # Model ---------------------------------------------------
    system = simpy.Environment()

    logger = LoggingManager(system, time_step=1.0)
    logger.setup()

    # ---- ISRU Plants (always present — enforced above) ------
    isruPlantData = data_from_json("ISRUV2.json")['ISRUPlant']
    excavationData = data_from_json("ISRUExcavation.json")['ISRUExcavation']
    plant_attributes = dict(isruPlantData.raw['attributes'])
    plant_attributes.setdefault(
        "excavationEnergyCoeff",
        excavationData.raw.get('attributes', {}).get("excavationEnergyCoeff", 0.0),
    )
    plant_instances = _scenario_instances(scenario_builder, "ISRUPlant", num_isru_plants)
    num_isru_plants = len(plant_instances)
    if num_isru_plants < 1:
        raise ValueError("At least one ISRU plant is required by the current ISRU process")
    plants = []
    plant_targets = []
    regolith_sources = {}
    for i, instance in enumerate(plant_instances):
        instance_id = instance["id"]
        route = _resource_route(scenario_builder, "Regolith", instance_id)
        source_instance_id = (route or {}).get("from", "ISRUExcavation")
        if source_instance_id not in regolith_sources:
            source = RegolithSourceRuntime(
                system,
                source_instance_id,
                excavationData.raw['attributes'],
                _module_equations(
                    scenario_builder,
                    source_instance_id,
                    "ISRUExcavation",
                ),
            )
            regolith_sources[source_instance_id] = source
            logger.add(source)
        p = ISRUPlant(
            system,
            f"ISRU_Plant_{i+1}",
            plant_attributes,
            equations=_module_equations(scenario_builder, instance_id, "ISRUPlant"),
        )
        p.instanceId = instance_id
        p.processingRate = scenario_config["isru"]["processing_rate_kg_hr"]
        logger.add(p)
        plants.append(p)
        plant_targets.append({
            "instance_id": instance_id,
            "plant": p,
            "buffer": simpy.Container(system, capacity=plant_input_capacity),
            "reserved_inbound_kg": 0.0,
            "source": regolith_sources[source_instance_id],
            "distance_km": _resource_route_distance(
                scenario_builder,
                "Regolith",
                instance_id,
                scenario_config["routes"]["regolith_distance_km"],
            ),
        })

    # ---- Solar Power System (optional) ----------------------
    solarSystem  = None
    powerManager = None
    if use_solar:
        solarPowerSystemData = data_from_json("SolarPowerSystemV1.json")['SolarPowerSystem']
        solarSystem = SolarPowerSystem(system, "Solar_Power_System", solarPowerSystemData.raw['attributes'])
        logger.add(solarSystem)
        powerManager = PowerManager(
            system,
            solarSystem,
            generationEquations=_module_equations(
                scenario_builder,
                "SolarPowerSystem",
                "SolarPowerSystem",
            ),
        )
        logger.add(powerManager)
        registered_power_model_ids = set()

        def register_power_consumer(consumer, instance_id, module_type):
            model = _module_power_model(scenario_config, instance_id, module_type)
            if model:
                consumer = PowerModelConsumer(consumer, model)
                model_keys = scenario_config.get("power", {}).get("module_models", {})
                registered_power_model_ids.add(
                    instance_id if instance_id in model_keys else module_type
                )
            powerManager.registerConsumer(consumer)
            return consumer

        # Register ISRU plants with power manager
        for p in plants:
            register_power_consumer(p, p.instanceId, "ISRUPlant")
        for source in regolith_sources.values():
            register_power_consumer(source, source.name, "ISRUExcavation")
    else:
        registered_power_model_ids = set()
        register_power_consumer = None

    # ---- Habitation Module (optional) -----------------------
    habitat = None
    if use_habitat:
        habitationModuleData = data_from_json("HabitationModuleV1.json")['HabitationModule']
        habitat = HabitationModule(system, "Habitat-1", habitationModuleData.raw['attributes'])
        habitat_power_kw = continuous_power.get("habitation")
        if habitat_power_kw is not None:
            habitat.setConstantPowerRate(float(habitat_power_kw))
        if _module_power_model(scenario_config, "HabitationModule", "HabitationModule"):
            habitat.setConstantPowerRate(0.0)
        for spike in scenario_config["power"]["spikes"].get("habitation", []):
            habitat.scheduleSpike(spike["time_hr"], spike["energy_kwh"])
        if powerManager:
            register_power_consumer(EquationPowerConsumer(
                habitat,
                _module_equations(scenario_builder, "HabitationModule", "HabitationModule"),
            ), "HabitationModule", "HabitationModule")
        logger.add(habitat)

    # ---- Communication Module (optional) --------------------
    comms = None
    if use_comms:
        communicationModuleData = data_from_json("CommunicationModuleV1.json")['CommunicationModule']
        comms = CommunicationModule(system, "CommArray-1", communicationModuleData.raw['attributes'])
        comms_power_kw = continuous_power.get("communications")
        if comms_power_kw is not None:
            comms.setConstantPowerRate(float(comms_power_kw))
        if _module_power_model(scenario_config, "CommunicationModule", "CommunicationModule"):
            comms.setConstantPowerRate(0.0)
        for spike in scenario_config["power"]["spikes"].get("communications", []):
            comms.scheduleSpike(spike["time_hr"], spike["energy_kwh"])
        if powerManager:
            register_power_consumer(EquationPowerConsumer(
                comms,
                _module_equations(scenario_builder, "CommunicationModule", "CommunicationModule"),
            ), "CommunicationModule", "CommunicationModule")
        logger.add(comms)

    # ---- Landing / Launch Zone (optional) -------------------
    landingZone = None
    if use_landing_zone:
        landingZoneData = data_from_json("LaunchLandingZoneV1.json")['LaunchLandingZone']
        landingZone = LandingLaunchZone(system, "LZ-Alpha", attributeDict=landingZoneData.raw['attributes'])
        landing_utilities_kw = continuous_power.get("landing_zone_utilities")
        if landing_utilities_kw is not None:
            landingZone.utilitiesPowerRate = float(landing_utilities_kw)
        landing_chilling_kw_per_kg = scenario_config["power"].get("landing_zone_chilling_kw_per_kg")
        if landing_chilling_kw_per_kg is not None:
            landingZone.chillingPowerPerKgLOX = float(landing_chilling_kw_per_kg)
        if _module_power_model(scenario_config, "LaunchLandingZone", "LaunchLandingZone"):
            landingZone.utilitiesPowerRate = 0.0
            landingZone.chillingPowerPerKgLOX = 0.0
        for spike in scenario_config["power"]["spikes"].get("landing_zone", []):
            landingZone.scheduleSpike(spike["time_hr"], spike["energy_kwh"])
        if powerManager:
            register_power_consumer(EquationPowerConsumer(
                landingZone,
                _module_equations(scenario_builder, "LaunchLandingZone", "LaunchLandingZone"),
            ), "LaunchLandingZone", "LaunchLandingZone")
        logger.add(landingZone)

    # ---- Propellant depots selected as LOX destinations -----
    propellant_depots = {}
    depot_instances = _scenario_instances(scenario_builder, "PropellantDepot", 0)
    if depot_instances:
        propellantDepotData = data_from_json("PropellantDepot.json")['PropellantDepot']
        for instance in depot_instances:
            depot = PropellantDepotRuntime(
                system,
                instance["id"],
                propellantDepotData.raw['attributes'],
                _module_equations(
                    scenario_builder,
                    instance["id"],
                    "PropellantDepot",
                ),
            )
            propellant_depots[instance["id"]] = depot
            if powerManager:
                register_power_consumer(depot, instance["id"], "PropellantDepot")
            logger.add(depot)

    # ---- Rovers (regolith always present; LOX optional) -----
    roverData = data_from_json("RoverV1.json")['Rover']

    regolithCargoRovers = []
    for i in range(num_regolith_rovers):
        instance_id = (
            "RegolithRover"
            if num_regolith_rovers == 1
            else f"RegolithRover_{i+1}"
        )
        r = LunarRover(system, name=f"Regolith Cargo Rover {i+1}", roverType="cargo",
                       attributeDict=roverData.raw['attributes'],
                       equations=_module_equations(
                           scenario_builder, instance_id, "RegolithRover"
                       ))
        r.instanceId = instance_id
        r.energyPerKmPerKg = scenario_config["rovers"]["energy_kwh_per_km_per_kg"]
        r.hoursPerKm       = scenario_config["rovers"]["travel_time_hr_per_km"]
        r.maxCapacity      = float(scenario_config["rovers"].get("max_capacity_kg", r.maxCapacity))
        logger.add(r)
        regolithCargoRovers.append(r)

    if rover_load <= 0 or plant_batch <= 0 or plant_input_capacity <= 0:
        raise ValueError("Regolith rover load, plant batch, and plant input capacity must be positive")
    if any(rover_load > rover.maxCapacity for rover in regolithCargoRovers):
        raise ValueError(
            f"Regolith rover load ({rover_load} kg) exceeds rover capacity "
            f"({regolithCargoRovers[0].maxCapacity} kg)"
        )
    if plant_batch > plant_input_capacity:
        raise ValueError(
            f"Plant batch ({plant_batch} kg) exceeds each plant input storage "
            f"capacity ({plant_input_capacity} kg)"
        )
    if rover_load > plant_input_capacity:
        raise ValueError(
            f"Regolith rover load ({rover_load} kg) exceeds each plant input storage "
            f"capacity ({plant_input_capacity} kg)"
        )

    LOXCargoRovers = []
    chargingStation = None
    if use_lox_rover:
        for i in range(num_lox_rovers):
            instance_id = "LOXRover" if num_lox_rovers == 1 else f"LOXRover_{i+1}"
            r = LunarRover(system, name=f"LOX Cargo Rover {i+1}", roverType="cargo",
                           attributeDict=roverData.raw['attributes'],
                           equations=_module_equations(
                               scenario_builder, instance_id, "LOXRover"
                           ))
            r.instanceId = instance_id
            r.energyPerKmPerKg = scenario_config["rovers"]["energy_kwh_per_km_per_kg"]
            r.hoursPerKm       = scenario_config["rovers"]["travel_time_hr_per_km"]
            r.maxCapacity      = float(scenario_config["rovers"].get("max_capacity_kg", r.maxCapacity))
            logger.add(r)
            LOXCargoRovers.append(r)

        # Charging station is only meaningful when there are rovers needing a charge;
        # tie its existence to the LOX rover (the regolith rovers are always present
        # so the station is always built when the LOX rover is, giving it something
        # useful to do for both rover types).
        charging_config = scenario_config["power"]["charging_station"]
        if charging_config.get("enabled_when_lox_rover_active", True):
            chargingStation = RoverChargingStation(
                system,
                "ChargeStation-1",
                chargingPowerRate=charging_config["charging_power_kw"],
                efficiencyFactor=charging_config["efficiency"]
            )
            if powerManager:
                powerManager.registerConsumer(chargingStation)
            logger.add(chargingStation)

    # Any remaining Step 5 module model becomes an explicit grid consumer.
    # This keeps power models functional even when a module has no dedicated
    # Python class in the current ISRU engine.
    if powerManager:
        for model_id, model in scenario_config.get("power", {}).get("module_models", {}).items():
            if model_id in registered_power_model_ids:
                continue
            consumer = StaticPowerConsumer(system, f"{model_id} Power Load")
            powerManager.registerConsumer(PowerModelConsumer(consumer, model))
            logger.add(consumer)
            registered_power_model_ids.add(model_id)

    # ---- Haul distances / thresholds ------------------------
    regolith_haul_distance = scenario_config["routes"]["regolith_distance_km"]
    LOX_haul_distance      = scenario_config["routes"]["lox_distance_km"]
    transport_threshold    = scenario_config["isru"]["lox_transport_threshold_kg"]

    # =========================================================
    # Spawn processes
    # =========================================================

    # Regolith rovers (always active)
    for r in regolithCargoRovers:
        assigned_routes = _resource_routes_for_rover(
            scenario_builder, "Regolith", r.instanceId
        )
        rover_targets = []
        for route in assigned_routes:
            target = next(
                (item for item in plant_targets if item["instance_id"] == route.get("to")),
                None,
            )
            if target is None:
                raise ValueError(
                    f"Regolith route assigned to {r.instanceId} targets unknown plant "
                    f"{route.get('to')!r}"
                )
            routed_target = dict(target)
            if route.get("distance_km") is not None:
                routed_target["distance_km"] = float(route["distance_km"])
            rover_targets.append(routed_target)

        if not assigned_routes and not _has_assigned_resource_routes(
            scenario_builder, "Regolith"
        ):
            rover_targets = plant_targets

        system.process(regolithRoverController(
            system,
            rover_targets,
            rover_load,
            r,
            poll_dt=regolith_dispatch_poll_dt,
        ))

    # ISRU plant controllers + LOX storage energy accounting
    for target in plant_targets:
        p = target["plant"]
        system.process(plantController(system, p, target["buffer"], plant_batch))
        system.process(LOXStorageEnergy(
            system,
            p,
            dt=scenario_config["isru"]["lox_storage_energy_dt_hr"],
            energyCoeff=scenario_config["isru"]["lox_storage_energy_kwh_per_kg_hr"],
        ))

    # LOX delivery to the destination selected in the Step 4 resource route.
    if use_lox_rover and LOXCargoRovers and (landingZone or propellant_depots):
        known_lox_rover_ids = {rover.instanceId for rover in LOXCargoRovers}
        LOXRoverStore = simpy.FilterStore(system, capacity=len(LOXCargoRovers))
        for r in LOXCargoRovers:
            LOXRoverStore.items.append(r)
        for p in plants:
            route = _resource_route_from(scenario_builder, "LOX", p.instanceId)
            assigned_rover_id = (route or {}).get("rover_id")
            if assigned_rover_id and assigned_rover_id not in known_lox_rover_ids:
                raise ValueError(
                    f"LOX route from {p.instanceId} references unknown rover "
                    f"{assigned_rover_id!r}; available rovers: "
                    f"{sorted(known_lox_rover_ids)}"
                )
            destination_id = (route or {}).get("to", "LaunchLandingZone")
            destination_type = _base_instance_type(destination_id)
            if destination_type == "PropellantDepot":
                destination = propellant_depots.get(destination_id)
                if destination is None and len(propellant_depots) == 1:
                    destination = next(iter(propellant_depots.values()))
            else:
                destination = landingZone
            if destination is None:
                raise ValueError(
                    f"No DES destination object exists for LOX route target {destination_id!r}"
                )
            route_distance = LOX_haul_distance
            if route and route.get("distance_km") is not None:
                route_distance = float(route["distance_km"])
            system.process(LOXDeliveryController(
                system, p, LOXRoverStore,
                destination, distance=route_distance,
                transportThreshold=transport_threshold,
                poll_dt=scenario_config["isru"]["lox_delivery_poll_dt_hr"],
                assignedRoverId=assigned_rover_id,
            ))

    # Power management (only when solar system is present)
    if powerManager:
        system.process(powerManager.managePower(dt=scenario_config["power"]["management_dt_hr"]))

    # Experiment ----------------------------------------------
    print("="*70)
    print(experiment)
    print("="*70)
    system.run(until=simDuration)

    # =========================================================
    # Analysis / Results printing
    # =========================================================
    print("\n" + "="*70)
    print("SIMULATION RESULTS")
    print("="*70)

    # ISRU plants
    total_lox_stored     = sum(p.LOXStored           for p in plants)
    total_energy_isru    = sum(p.totalEnergyConsumed  for p in plants)
    total_uptime         = sum(p.processingUptime     for p in plants)
    total_regolith_recv  = sum(p.regolithRecieved     for p in plants)
    total_lox_production = sum(p.totalLOXProduction   for p in plants)

    for p in plants:
        print(f"\n{p.name}:")
        print(f"  LOX Stored: {p.LOXStored:.2f} kg")
        print(f"  Energy Consumed: {p.totalEnergyConsumed:.2f} kWh")
        print(f"  Total Operational Hours: {p.processingUptime:.2f} hours")
        print(f"  Regolith Received: {p.regolithRecieved:.2f} kg")
        print(f"  Total LOX Production: {p.totalLOXProduction:.2f} kg")

    if num_isru_plants > 1:
        print(f"\n[Fleet Totals – {num_isru_plants} ISRU Plants]")
        print(f"  LOX Stored (all plants): {total_lox_stored:.2f} kg")
        print(f"  Energy Consumed (all):   {total_energy_isru:.2f} kWh")
        print(f"  Regolith Received (all): {total_regolith_recv:.2f} kg")
        print(f"  Total LOX Production:    {total_lox_production:.2f} kg")

    if use_solar and solarSystem:
        print(f"\nSolar Power System:")
        print(f"  Total Generated: {solarSystem.totalEnergyGenerated:.2f} kWh")
        print(f"  From Battery: {solarSystem.totalEnergyFromBattery:.2f} kWh")
        print(f"  Battery Charge: {solarSystem.batteryCharge:.2f}/{solarSystem.batteryCapacity:.2f} kWh")

    if powerManager:
        print(f"\nPower Manager Stats")
        print(f"  Energy Generated Time Array: {powerManager.powerGeneratedSeries} kWh")
        print(f"  Total Energy Demand Time Array: {powerManager.totalDemandSeries} kWh")

    if use_habitat and habitat:
        print(f"\n{habitat.name}:")
        print(f"  Energy Consumed: {habitat.totalEnergyConsumed:.2f} kWh")

    if use_comms and comms:
        print(f"\n{comms.name}:")
        print(f"  Energy Consumed: {comms.totalEnergyConsumed:.2f} kWh")

    if use_landing_zone and landingZone:
        print(f"\n{landingZone.name}:")
        print(f"  LOX Stored: {landingZone.loxStored:.2f} kg")
        print(f"  Energy Consumed: {landingZone.totalEnergyConsumed:.2f} kWh")

    for depot in propellant_depots.values():
        print(f"\n{depot.name}:")
        print(f"  LOX Stored: {depot.loxStored:.2f} kg")
        print(f"  Energy Consumed: {depot.totalEnergyConsumed:.2f} kWh")

    for r in regolithCargoRovers:
        print(f"\n{r.name}:")
        print(f"  Total Distance: {r.totalDistanceTraveled:.2f} km")
        print(f"  Energy Consumed: {r.totalEnergyConsumed:.2f} kWh")
        print(f"  Battery Charge: {r.batteryCharge:.2f}/{r.batteryCapacity:.2f} kWh")
        print(f"  Current Load: {r.currentLoad:.2f} kg")

    for r in LOXCargoRovers:
        print(f"\n{r.name}:")
        print(f"  Total Distance: {r.totalDistanceTraveled:.2f} km")
        print(f"  Energy Consumed: {r.totalEnergyConsumed:.2f} kWh")
        print(f"  Battery Charge: {r.batteryCharge:.2f}/{r.batteryCapacity:.2f} kWh")
        print(f"  Current Load: {r.currentLoad:.2f} kg")

    if chargingStation:
        print(f"\n{chargingStation.name}:")
        print(f"  Energy Consumed: {chargingStation.totalEnergyConsumed:.2f} kWh")
        print(f"  Energy Delivered to Rovers: {chargingStation.totalEnergyDelivered:.2f} kWh")

    print("="*70)

    # Output --------------------------------------------------
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.4f} seconds")

    # =========================================================
    # Build results dict — only include sections for active nodes
    # =========================================================
    isru_plant_results = {}
    for target in plant_targets:
        p = target["plant"]
        isru_plant_results[p.name] = {
            "Scenario_Instance":        target["instance_id"],
            "Regolith_Input_Stored_kg": round(target["buffer"].level, 2),
            "Regolith_Route_km":        round(target["distance_km"], 3),
            "Scenario_Equations":       p.scenarioEquations,
            "Equation_Outputs":         p.lastEquationOutputs,
            "LOX_Stored_kg":           round(p.LOXStored, 2),
            "Energy_Consumed_kWh":     round(p.totalEnergyConsumed, 2),
            "Total_Operational_Hours": round(p.processingUptime, 2),
            "Regolith_Received_kg":    round(p.regolithRecieved, 2),
            "Total_LOX_Production_kg": round(p.totalLOXProduction, 2),
        }
    isru_plant_results["Fleet_Totals"] = {
        "Num_Plants":              num_isru_plants,
        "LOX_Stored_kg":           round(total_lox_stored, 2),
        "Energy_Consumed_kWh":     round(total_energy_isru, 2),
        "Total_Operational_Hours": round(total_uptime, 2),
        "Regolith_Received_kg":    round(total_regolith_recv, 2),
        "Total_LOX_Production_kg": round(total_lox_production, 2),
    }

    regolith_rover_results = {}
    for r in regolithCargoRovers:
        regolith_rover_results[r.name] = {
            "Total_Distance_km":    round(r.totalDistanceTraveled, 2),
            "Energy_Consumed_kWh":  round(r.totalEnergyConsumed, 2),
            "Battery_Charge_kWh":   round(r.batteryCharge, 2),
            "Battery_Capacity_kWh": round(r.batteryCapacity, 2),
            "Current_Load_kg":      round(r.currentLoad, 2),
        }
    regolith_rover_results["Fleet_Totals"] = {
        "Num_Rovers":          num_regolith_rovers,
        "Total_Distance_km":   round(sum(r.totalDistanceTraveled for r in regolithCargoRovers), 2),
        "Energy_Consumed_kWh": round(sum(r.totalEnergyConsumed   for r in regolithCargoRovers), 2),
    }

    lox_rover_results = {}
    for r in LOXCargoRovers:
        lox_rover_results[r.name] = {
            "Total_Distance_km":    round(r.totalDistanceTraveled, 2),
            "Energy_Consumed_kWh":  round(r.totalEnergyConsumed, 2),
            "Battery_Charge_kWh":   round(r.batteryCharge, 2),
            "Battery_Capacity_kWh": round(r.batteryCapacity, 2),
            "Current_Load_kg":      round(r.currentLoad, 2),
        }
    if LOXCargoRovers:
        lox_rover_results["Fleet_Totals"] = {
            "Num_Rovers":          len(LOXCargoRovers),
            "Total_Distance_km":   round(sum(r.totalDistanceTraveled for r in LOXCargoRovers), 2),
            "Energy_Consumed_kWh": round(sum(r.totalEnergyConsumed for r in LOXCargoRovers), 2),
        }

    total_lox_delivered = (
        (landingZone.loxStored if landingZone else 0.0)
        + sum(depot.loxStored for depot in propellant_depots.values())
    )
    total_regolith_rover_energy = sum(r.totalEnergyConsumed for r in regolithCargoRovers)
    total_lox_rover_energy = sum(r.totalEnergyConsumed for r in LOXCargoRovers)
    total_system_demand = (
        sum(powerManager.totalDemandSeries)
        if powerManager
        else total_energy_isru + total_regolith_rover_energy + total_lox_rover_energy
    )

    final_results = {
        "Sim_Metrics": {
            "Simulation_Run_Time": round(elapsed_time, 4),
            "Active_Nodes":        sorted(active_nodes),
            "Simulation_Duration_hr": simDuration,
        },
        "Scenario_Config": scenario_config,
        "MoEs": {
            "Total_LOX_Produced_kg": round(total_lox_production, 2),
            "Total_LOX_Delivered_kg": round(total_lox_delivered, 2),
            "Total_LOX_Remaining_at_Plants_kg": round(total_lox_stored, 2),
            "Total_Regolith_Received_kg": round(total_regolith_recv, 2),
            "Total_ISRU_Energy_Consumed_kWh": round(total_energy_isru, 2),
            "Total_Regolith_Rover_Energy_kWh": round(total_regolith_rover_energy, 2),
            "Total_LOX_Rover_Energy_kWh": round(total_lox_rover_energy, 2),
            "Total_System_Demand_kWh": round(total_system_demand, 2),
        },
        "ISRU_Plants": isru_plant_results,
        "Regolith_Cargo_Rovers": regolith_rover_results,
    }
    if LOXCargoRovers:
        final_results["LOX_Cargo_Rovers"] = lox_rover_results

    if use_solar and solarSystem:
        final_results["Solar_Power_System"] = {
            "Total_Generated_kWh":  round(solarSystem.totalEnergyGenerated, 2),
            "From_Battery_kWh":     round(solarSystem.totalEnergyFromBattery, 2),
            "Battery_Charge_kWh":   round(solarSystem.batteryCharge, 2),
            "Battery_Capacity_kWh": round(solarSystem.batteryCapacity, 2),
        }

    if powerManager:
        final_results["Power_Manager"] = {
            "Energy_Generated_Time_Array_kWh": powerManager.powerGeneratedSeries,
            "Total_Demand_Time_Array_kWh":     powerManager.totalDemandSeries,
            "Generation_Equation_Outputs":     powerManager.lastGenerationEquationOutputs,
            "Consumer_Equation_Outputs": {
                consumer.name: consumer.lastEquationOutputs
                for consumer in powerManager.consumers
                if hasattr(consumer, "lastEquationOutputs") and consumer.lastEquationOutputs
            },
        }

    if use_habitat and habitat:
        final_results["Habitat"] = {
            "Name":                habitat.name,
            "Energy_Consumed_kWh": round(habitat.totalEnergyConsumed, 2),
        }

    if use_comms and comms:
        final_results["Communications"] = {
            "Name":                comms.name,
            "Energy_Consumed_kWh": round(comms.totalEnergyConsumed, 2),
        }

    if use_landing_zone and landingZone:
        final_results["Landing_Zone"] = {
            "Name":                landingZone.name,
            "LOX_Stored_kg":       round(landingZone.loxStored, 2),
            "Energy_Consumed_kWh": round(landingZone.totalEnergyConsumed, 2),
        }

    if propellant_depots:
        final_results["Propellant_Depots"] = {
            depot.name: {
                "LOX_Stored_kg": round(depot.loxStored, 2),
                "Energy_Consumed_kWh": round(depot.totalEnergyConsumed, 2),
                "Equation_Outputs": depot.lastEquationOutputs,
            }
            for depot in propellant_depots.values()
        }

    if len(LOXCargoRovers) == 1:
        only_rover = LOXCargoRovers[0]
        final_results["LOX_Cargo_Rover"] = {
            "Name":                 only_rover.name,
            "Total_Distance_km":    round(only_rover.totalDistanceTraveled, 2),
            "Energy_Consumed_kWh":  round(only_rover.totalEnergyConsumed, 2),
            "Battery_Charge_kWh":   round(only_rover.batteryCharge, 2),
            "Battery_Capacity_kWh": round(only_rover.batteryCapacity, 2),
            "Current_Load_kg":      round(only_rover.currentLoad, 2),
        }

    if chargingStation:
        final_results["Charging_Station"] = {
            "Name":                           chargingStation.name,
            "Energy_Consumed_kWh":            round(chargingStation.totalEnergyConsumed, 2),
            "Energy_Delivered_to_Rovers_kWh": round(chargingStation.totalEnergyDelivered, 2),
        }

    # Export to JSON file
    with open('lunar_spaceport_results.json', 'w') as f:
        json.dump(final_results, f, indent=4)

    logger.log()
    logger.saveToJSON()


# -------------------------------------------------
# Example Usage in Main
# -------------------------------------------------
def main():
    start_time = time.perf_counter()
    # Experiment data -----------------------------------------
    experiment = "ISRU Processing Plant with Full Infrastructure"
    roverBatch = 4000          # kg
    roverTravelTime = 5        # hr between deliveries
    simDuration = 60           # hr

    # Model ---------------------------------------------------
    system = simpy.Environment()
    
    # Resources
    regolithBuffer = simpy.Container(system, capacity=20_000)

    #Setup Logger
    logger = LoggingManager(system, time_step=1.0)
    logger.setup()

    # ISRU Plant
    isruPlantData = data_from_json("ISRUV2.json")['ISRUPlant']
    plant = ISRUPlant(system, "ISRU_Plant", isruPlantData.raw['attributes'])
    logger.add(plant)

    # Solar Power System (100 kW output, 500 kWh battery)
    solarPowerSystemData = data_from_json("SolarPowerSystemV1.json")['SolarPowerSystem']
    solarSystem = SolarPowerSystem(system, "Solar_Power_System", solarPowerSystemData.raw['attributes'])
    logger.add(solarSystem)

    # Power Manager
    powerManager = PowerManager(system, solarSystem)
    logger.add(powerManager)

    # Habitation Module (5 kW constant)
    habitationModuleData = data_from_json("HabitationModuleV1.json")['HabitationModule']
    habitat = HabitationModule(system, "Habitat-1", habitationModuleData.raw['attributes'])
    habitat.scheduleSpike(10, 20)  # 20 kWh spike at hour 10
    powerManager.registerConsumer(habitat)
    logger.add(habitat)

    # Communication Module (2 kW constant)
    communicationModuleData = data_from_json("CommunicationModuleV1.json")['CommunicationModule']
    comms = CommunicationModule(system, "CommArray-1", communicationModuleData.raw['attributes'])
    comms.scheduleSpike(15, 10)  # 10 kWh spike at hour 15
    powerManager.registerConsumer(comms)
    logger.add(comms)

    # Landing/Launch Zone (10 kW chilling, 3 kW utilities)
    landingZoneData = data_from_json("LaunchLandingZoneV1.json")['LaunchLandingZone']
    landingZone = LandingLaunchZone(system, "LZ-Alpha", attributeDict=landingZoneData.raw['attributes'])
    landingZone.scheduleSpike(25, 50)  # 50 kWh spike at hour 25
    powerManager.registerConsumer(landingZone)
    logger.add(landingZone)

    # Rover Charging Station
    chargingStation = RoverChargingStation(
        system,
        "ChargeStation-1",
        chargingPowerRate=20,  # kW
        efficiencyFactor=0.85
    )
    powerManager.registerConsumer(chargingStation)
    logger.add(chargingStation)

    roverData = data_from_json("RoverV1.json")['Rover']
    regolithCargoRover = LunarRover(system, name="Regolith Cargo Rover", roverType="cargo", attributeDict=roverData.raw['attributes'])
    LOXCargoRover = LunarRover(system, name="LOX Cargo Rover", roverType="cargo", attributeDict=roverData.raw['attributes'])
    logger.add(regolithCargoRover)
    logger.add(LOXCargoRover)

    # Start processes
    plant_targets = [{
        "instance_id": "ISRUPlant",
        "plant": plant,
        "buffer": regolithBuffer,
        "reserved_inbound_kg": 0.0,
        "distance_km": 1.0,
    }]
    system.process(regolithRoverController(system, plant_targets, roverBatch, regolithCargoRover))
    system.process(plantController(system, plant, regolithBuffer, roverBatch))
    system.process(LOXStorageEnergy(system, plant, dt=1.0))
    LOXRoverStore = simpy.Store(system, capacity=1)
    LOXRoverStore.items.append(LOXCargoRover)
    system.process(LOXDeliveryController(system, plant, LOXRoverStore, landingZone, distance=1, transportThreshold=100))
    system.process(powerManager.managePower(dt=1.0))  # NEW: Power management

    # Experiment ----------------------------------------------
    print("="*70)
    print(experiment)
    print("="*70)
    system.run(until=simDuration)

    # Analysis ------------------------------------------------
    print("\n" + "="*70)
    print("SIMULATION RESULTS")
    print("="*70)
    print(f"\nISRU Plant:")
    print(f"  LOX Stored: {plant.LOXStored:.2f} kg")
    print(f"  Energy Consumed: {plant.totalEnergyConsumed:.2f} kWh")
    print(f"  Total Operational Hours: {plant.processingUptime:.2f} hours")
    print(f"  Regolith Recieved: {plant.regolithRecieved:.2f} kg")
    print(f"  Total LOX Production: {plant.totalLOXProduction:.2f} kg")
    
    print(f"\nSolar Power System:")
    print(f"  Total Generated: {solarSystem.totalEnergyGenerated:.2f} kWh")
    print(f"  From Battery: {solarSystem.totalEnergyFromBattery:.2f} kWh")
    print(f"  Battery Charge: {solarSystem.batteryCharge:.2f}/{solarSystem.batteryCapacity:.2f} kWh")

    print(f"\nPower Manager Stats")
    print(f"  Energy Generated Time Array: {powerManager.powerGeneratedSeries} kWh")
    print(f"  Total Energy Demand Time Array: {powerManager.totalDemandSeries} kWh")
    
    print(f"\n{habitat.name}:")
    print(f"  Energy Consumed: {habitat.totalEnergyConsumed:.2f} kWh")
    
    print(f"\n{comms.name}:")
    print(f"  Energy Consumed: {comms.totalEnergyConsumed:.2f} kWh")
    
    print(f"\n{landingZone.name}:")
    print(f"  LOX Stored: {landingZone.loxStored:.2f} kg")
    print(f"  Energy Consumed: {landingZone.totalEnergyConsumed:.2f} kWh")
    
    print(f"\n{regolithCargoRover.name}:")
    print(f"  Total Distance: {regolithCargoRover.totalDistanceTraveled:.2f} km")
    print(f"  Energy Consumed: {regolithCargoRover.totalEnergyConsumed:.2f} kWh")
    print(f"  Battery Charge: {regolithCargoRover.batteryCharge:.2f}/{regolithCargoRover.batteryCapacity:.2f} kWh")
    print(f"  Current Load: {regolithCargoRover.currentLoad:.2f} kg")

    print(f"\n{LOXCargoRover.name}:")
    print(f"  Total Distance: {LOXCargoRover.totalDistanceTraveled:.2f} km")
    print(f"  Energy Consumed: {LOXCargoRover.totalEnergyConsumed:.2f} kWh")
    print(f"  Battery Charge: {LOXCargoRover.batteryCharge:.2f}/{LOXCargoRover.batteryCapacity:.2f} kWh")
    print(f"  Current Load: {LOXCargoRover.currentLoad:.2f} kg")

    print(f"\n{chargingStation.name}:")
    print(f"  Energy Consumed: {chargingStation.totalEnergyConsumed:.2f} kWh")
    print(f"  Energy Delivered to Rovers: {chargingStation.totalEnergyDelivered:.2f} kWh")
    print("="*70)

    # Output --------------------------------------------------
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.4f} seconds")
    #print(logger.logDict)

    # Create the results dictionary
    final_results = {
        "Sim_Metrics" : {
            "Simulation_Run_Time": round(elapsed_time, 4)
        },
        "ISRU_Plant": {
            "LOX_Stored_kg": round(plant.LOXStored, 2),
            "Energy_Consumed_kWh": round(plant.totalEnergyConsumed, 2),
            "Total_Operational_Hours": round(plant.processingUptime, 2),
            "Regolith_Received_kg": round(plant.regolithRecieved, 2),
            "Total_LOX_Production_kg": round(plant.totalLOXProduction, 2)
        },
        "Solar_Power_System": {
            "Total_Generated_kWh": round(solarSystem.totalEnergyGenerated, 2),
            "From_Battery_kWh": round(solarSystem.totalEnergyFromBattery, 2),
            "Battery_Charge_kWh": round(solarSystem.batteryCharge, 2),
            "Battery_Capacity_kWh": round(solarSystem.batteryCapacity, 2)
        },
        "Power_Manager": {
            "Energy_Generated_Time_Array_kWh": powerManager.powerGeneratedSeries,
            "Total_Demand_Time_Array_kWh": powerManager.totalDemandSeries
        },
        "Habitat": {
            "Name": habitat.name,
            "Energy_Consumed_kWh": round(habitat.totalEnergyConsumed, 2)
        },
        "Communications": {
            "Name": comms.name,
            "Energy_Consumed_kWh": round(comms.totalEnergyConsumed, 2)
        },
        "Landing_Zone": {
            "Name": landingZone.name,
            "LOX_Stored_kg": round(landingZone.loxStored, 2),
            "Energy_Consumed_kWh": round(landingZone.totalEnergyConsumed, 2)
        },
        "Regolith_Cargo_Rover": {
            "Name": regolithCargoRover.name,
            "Total_Distance_km": round(regolithCargoRover.totalDistanceTraveled, 2),
            "Energy_Consumed_kWh": round(regolithCargoRover.totalEnergyConsumed, 2),
            "Battery_Charge_kWh": round(regolithCargoRover.batteryCharge, 2),
            "Battery_Capacity_kWh": round(regolithCargoRover.batteryCapacity, 2),
            "Current_Load_kg": round(regolithCargoRover.currentLoad, 2)
        },
        "LOX_Cargo_Rover": {
            "Name": LOXCargoRover.name,
            "Total_Distance_km": round(LOXCargoRover.totalDistanceTraveled, 2),
            "Energy_Consumed_kWh": round(LOXCargoRover.totalEnergyConsumed, 2),
            "Battery_Charge_kWh": round(LOXCargoRover.batteryCharge, 2),
            "Battery_Capacity_kWh": round(LOXCargoRover.batteryCapacity, 2),
            "Current_Load_kg": round(LOXCargoRover.currentLoad, 2)
        },
        "Charging_Station": {
            "Name": chargingStation.name,
            "Energy_Consumed_kWh": round(chargingStation.totalEnergyConsumed, 2),
            "Energy_Delivered_to_Rovers_kWh": round(chargingStation.totalEnergyDelivered, 2)
        }
    }

    # Export to JSON file
    with open('lunar_spaceport_results.json', 'w') as f:
        json.dump(final_results, f, indent=4)
    
    logger.log()
    logger.saveToJSON()
    
if __name__ == "__main__":
    """ This is a standard block of code used for Python development.
    It means that when this file is run through Python it will run the
    lines contain within the if statement. If however the file is
    imported as a module, then this code is not run. This allows you
    to write your codes in multiple files and import them for easier
    development without having to run a simulation every time a file
    is imported. For example, when we 'import simpy' no simulation is
    run but we get access to the functions and classes contained
    within simpy.
    """
    main()
