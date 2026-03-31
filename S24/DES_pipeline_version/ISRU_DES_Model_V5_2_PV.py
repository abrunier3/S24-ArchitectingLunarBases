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
from S24.DES_pipeline_version.PowerManager import PowerManager
from S24.DES_pipeline_version.HabitationModule import HabitationModule
from S24.DES_pipeline_version.CommunicationModule import CommunicationModule
from S24.DES_pipeline_version.LunarRover import LunarRover
from S24.DES_pipeline_version.RoverChargingStation import RoverChargingStation
from S24.DES_pipeline_version.LandingLaunchZone import LandingLaunchZone
from S24.DES_pipeline_version.ImportUtility import data_from_json
from S24.DES_pipeline_version.LoggingManager import LoggingManager
import json
import time


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

def regolithRoverController(system, regolithBuffer, batchSize, distance, rover: LunarRover):
    """Continuously delivers regolith to the plant"""
    while True:
        rover.loadCargo(batchSize)
        yield system.process(rover.travel(distance))
        rover.unloadCargo()
        yield regolithBuffer.put(batchSize)
        print(f"[{system.now:.2f} hr] Rover delivered {batchSize} kg regolith")

# -------------------------------------------------
# Plant Controller
# -------------------------------------------------
def plantController(system, plant, regolithBuffer, batchSize):
    """Waits for regolith, then processes it"""
    while True:
        yield regolithBuffer.get(batchSize)
        yield system.process(plant.processRegolith(system, batchSize))


# -------------------------------------------------
# LOX Storage Energy
# -------------------------------------------------
def LOXStorageEnergy(system, plant, dt=1.0):
    """
    Continuously accounts for LOX storage energy.
    dt = accounting time step (hours)
    """
    while True:
        yield system.timeout(dt)

        storageEnergy = 0.31 * plant.LOXStored * dt
        plant.totalEnergyConsumed += storageEnergy

def LOXDeliveryController(system, plant: ISRUPlant, roverResource: simpy.Resource,
                          rover: LunarRover, landingZone: LandingLaunchZone,
                          distance, transportThreshold):
    """
    Per-plant LOX delivery controller (first-come-first-served).

    Each plant runs its own instance of this process.  When a plant's LOX
    reaches the transport threshold it joins the queue for the shared
    roverResource (a SimPy Resource with capacity=1).  Whichever plant
    acquires the resource first gets the rover; the others wait in the
    SimPy queue and are served in arrival order once the rover returns.

    MODIFICATION: Previously a single controller managed one plant directly.
    Now each plant has its own controller process that competes for the
    shared rover via roverResource.  The rover itself (LunarRover) is still
    the same single object — the Resource is just the mutex that ensures
    only one plant uses it at a time.
    """
    while True:
        # Poll every hour until this plant's LOX hits the threshold
        yield system.timeout(1)
        if plant.LOXStored >= transportThreshold:
            print(f"[{system.now:.2f} hr] {plant.name} reached threshold "
                  f"({plant.LOXStored:.2f} kg LOX). Queuing for LOX rover.")

            # Request the shared rover — blocks if another plant is using it.
            # LOX is NOT zeroed out here; the plant keeps accumulating while
            # waiting in the queue.
            with roverResource.request() as req:
                yield req  # wait in FCFS queue until rover is free

                # Rover has arrived — snapshot and clear LOX now, picking up
                # everything the plant has produced up to this moment.
                LOXToTransport = plant.LOXStored
                plant.LOXStored = 0
                print(f"[{system.now:.2f} hr] {plant.name} acquired LOX rover, "
                      f"beginning delivery of {LOXToTransport:.2f} kg.")
                # Load, travel, unload
                rover.loadCargo(LOXToTransport)
                yield system.process(rover.travel(distance))
                rover.unloadCargo()
                landingZone.receiveLOX(LOXToTransport)
                print(f"[{system.now:.2f} hr] {plant.name} delivered "
                      f"{LOXToTransport:.2f} kg LOX to {landingZone.name} "
                      f"(total there: {landingZone.loxStored:.2f} kg). "
                      f"Rover released.")

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
    roverBatch = 4000          # kg
    simDuration = 60           # hr

    num_regolith_rovers = optionsDict.get("Num_Regolith_Rovers", 1)
    num_isru_plants     = optionsDict.get("Num_ISRU_Plants", 1)

    # Model ---------------------------------------------------
    system = simpy.Environment()

    regolithBuffer = simpy.Container(system, capacity=20_000 * num_regolith_rovers)

    logger = LoggingManager(system, time_step=1.0)
    logger.setup()

    # ---- ISRU Plants (always present — enforced above) ------
    isruPlantData = data_from_json("ISRUV2.json")['ISRUPlant']
    plants = []
    for i in range(num_isru_plants):
        p = ISRUPlant(system, f"ISRU_Plant_{i+1}", isruPlantData.raw['attributes'])
        p.processingRate = optionsDict["ISRU_Plant_Processing_Rate"]
        logger.add(p)
        plants.append(p)

    # ---- Solar Power System (optional) ----------------------
    solarSystem  = None
    powerManager = None
    if use_solar:
        solarPowerSystemData = data_from_json("SolarPowerSystemV1.json")['SolarPowerSystem']
        solarSystem = SolarPowerSystem(system, "Solar_Power_System", solarPowerSystemData.raw['attributes'])
        logger.add(solarSystem)
        powerManager = PowerManager(system, solarSystem)
        logger.add(powerManager)
        # Register ISRU plants with power manager
        for p in plants:
            powerManager.registerConsumer(p)

    # ---- Habitation Module (optional) -----------------------
    habitat = None
    if use_habitat:
        habitationModuleData = data_from_json("HabitationModuleV1.json")['HabitationModule']
        habitat = HabitationModule(system, "Habitat-1", habitationModuleData.raw['attributes'])
        habitat.scheduleSpike(10, 20)  # 20 kWh spike at hour 10
        if powerManager:
            powerManager.registerConsumer(habitat)
        logger.add(habitat)

    # ---- Communication Module (optional) --------------------
    comms = None
    if use_comms:
        communicationModuleData = data_from_json("CommunicationModuleV1.json")['CommunicationModule']
        comms = CommunicationModule(system, "CommArray-1", communicationModuleData.raw['attributes'])
        comms.scheduleSpike(15, 10)  # 10 kWh spike at hour 15
        if powerManager:
            powerManager.registerConsumer(comms)
        logger.add(comms)

    # ---- Landing / Launch Zone (optional) -------------------
    landingZone = None
    if use_landing_zone:
        landingZoneData = data_from_json("LaunchLandingZoneV1.json")['LaunchLandingZone']
        landingZone = LandingLaunchZone(system, "LZ-Alpha", attributeDict=landingZoneData.raw['attributes'])
        landingZone.scheduleSpike(25, 50)  # 50 kWh spike at hour 25
        if powerManager:
            powerManager.registerConsumer(landingZone)
        logger.add(landingZone)

    # ---- Rovers (regolith always present; LOX optional) -----
    roverData = data_from_json("RoverV1.json")['Rover']

    regolithCargoRovers = []
    for i in range(num_regolith_rovers):
        r = LunarRover(system, name=f"Regolith Cargo Rover {i+1}", roverType="cargo",
                       attributeDict=roverData.raw['attributes'])
        r.energyPerKmPerKg = optionsDict["Rover_Energy_Consumption"]
        r.hoursPerKm       = optionsDict["Rover_Travel_Time"]
        logger.add(r)
        regolithCargoRovers.append(r)

    LOXCargoRover = None
    chargingStation = None
    if use_lox_rover:
        LOXCargoRover = LunarRover(system, name="LOX Cargo Rover", roverType="cargo",
                                   attributeDict=roverData.raw['attributes'])
        LOXCargoRover.energyPerKmPerKg = optionsDict["Rover_Energy_Consumption"]
        LOXCargoRover.hoursPerKm       = optionsDict["Rover_Travel_Time"]
        logger.add(LOXCargoRover)

        # Charging station is only meaningful when there are rovers needing a charge;
        # tie its existence to the LOX rover (the regolith rovers are always present
        # so the station is always built when the LOX rover is, giving it something
        # useful to do for both rover types).
        chargingStation = RoverChargingStation(
            system,
            "ChargeStation-1",
            chargingPowerRate=20,   # kW
            efficiencyFactor=0.85
        )
        if powerManager:
            powerManager.registerConsumer(chargingStation)
        logger.add(chargingStation)

    # ---- Haul distances / thresholds ------------------------
    regolith_haul_distance = optionsDict["Regolith_Haul_Distance"]
    LOX_haul_distance      = optionsDict.get("LOX_Haul_Distance", 1)
    transport_threshold    = optionsDict.get("LOX_Transport_Threshold", 100)

    # =========================================================
    # Spawn processes
    # =========================================================

    # Regolith rovers (always active)
    for r in regolithCargoRovers:
        system.process(regolithRoverController(system, regolithBuffer, roverBatch,
                                               regolith_haul_distance, r))

    # ISRU plant controllers + LOX storage energy accounting
    for p in plants:
        system.process(plantController(system, p, regolithBuffer, roverBatch))
        system.process(LOXStorageEnergy(system, p, dt=1.0))

    # LOX delivery: only when both the rover AND a landing zone destination exist
    if use_lox_rover and use_landing_zone and LOXCargoRover and landingZone:
        LOXRoverResource = simpy.Resource(system, capacity=1)
        for p in plants:
            system.process(LOXDeliveryController(
                system, p, LOXRoverResource, LOXCargoRover,
                landingZone, distance=LOX_haul_distance,
                transportThreshold=transport_threshold
            ))

    # Power management (only when solar system is present)
    if powerManager:
        system.process(powerManager.managePower(dt=1.0))

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

    for r in regolithCargoRovers:
        print(f"\n{r.name}:")
        print(f"  Total Distance: {r.totalDistanceTraveled:.2f} km")
        print(f"  Energy Consumed: {r.totalEnergyConsumed:.2f} kWh")
        print(f"  Battery Charge: {r.batteryCharge:.2f}/{r.batteryCapacity:.2f} kWh")
        print(f"  Current Load: {r.currentLoad:.2f} kg")

    if use_lox_rover and LOXCargoRover:
        print(f"\n{LOXCargoRover.name}:")
        print(f"  Total Distance: {LOXCargoRover.totalDistanceTraveled:.2f} km")
        print(f"  Energy Consumed: {LOXCargoRover.totalEnergyConsumed:.2f} kWh")
        print(f"  Battery Charge: {LOXCargoRover.batteryCharge:.2f}/{LOXCargoRover.batteryCapacity:.2f} kWh")
        print(f"  Current Load: {LOXCargoRover.currentLoad:.2f} kg")

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
    for p in plants:
        isru_plant_results[p.name] = {
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

    final_results = {
        "Sim_Metrics": {
            "Simulation_Run_Time": round(elapsed_time, 4),
            "Active_Nodes":        sorted(active_nodes),
        },
        "ISRU_Plants": isru_plant_results,
        "Regolith_Cargo_Rovers": regolith_rover_results,
    }

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

    if use_lox_rover and LOXCargoRover:
        final_results["LOX_Cargo_Rover"] = {
            "Name":                 LOXCargoRover.name,
            "Total_Distance_km":    round(LOXCargoRover.totalDistanceTraveled, 2),
            "Energy_Consumed_kWh":  round(LOXCargoRover.totalEnergyConsumed, 2),
            "Battery_Charge_kWh":   round(LOXCargoRover.batteryCharge, 2),
            "Battery_Capacity_kWh": round(LOXCargoRover.batteryCapacity, 2),
            "Current_Load_kg":      round(LOXCargoRover.currentLoad, 2),
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
    system.process(regolithRoverController(system, regolithBuffer, roverBatch, 1, regolithCargoRover))
    system.process(plantController(system, plant, regolithBuffer, roverBatch))
    system.process(LOXStorageEnergy(system, plant, dt=1.0))
    system.process(LOXDeliveryController(system, plant, LOXCargoRover, landingZone, distance=1, transportThreshold=100))
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