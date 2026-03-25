"""
Name:       ISRU_DES_Model_V4_PV.py
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
# Run Scenario
# -------------------------------------------------
def run_scenario(optionsDict):
    start_time = time.perf_counter()
    # Experiment data -----------------------------------------
    experiment = "ISRU Processing Plant with Full Infrastructure"
    roverBatch = 4000          # kg
    roverTravelTime = 5        # hr between deliveries
    simDuration = 60           # hr

    # =========================================================
    # MODIFICATION 1: Read fleet/plant counts from optionsDict.
    # These default to 1 to preserve original single-unit behavior
    # if the keys are not provided.
    # =========================================================
    num_regolith_rovers = optionsDict.get("Num_Regolith_Rovers", 1)  # NEW
    num_isru_plants     = optionsDict.get("Num_ISRU_Plants", 1)      # NEW

    # Model ---------------------------------------------------
    system = simpy.Environment()
    
    # Resources
    # =========================================================
    # MODIFICATION 2: Scale the regolithBuffer capacity with the
    # number of rovers so the buffer never becomes the bottleneck
    # when more rovers are hauling in parallel.
    # =========================================================
    regolithBuffer = simpy.Container(system, capacity=20_000 * num_regolith_rovers)  # MODIFIED

    #Setup Logger
    logger = LoggingManager(system, time_step=1.0)
    logger.setup()
    
    # =========================================================
    # MODIFICATION 3: Build a LIST of ISRU plants instead of a
    # single plant.  Every plant is an identical parallel
    # processing unit sharing the same regolithBuffer and
    # LOX storage (accumulated across all plants for delivery).
    # Each plant is registered with the power manager and logger
    # individually so that per-unit metrics are preserved.
    # =========================================================
    isruPlantData = data_from_json("ISRUV2.json")['ISRUPlant']
    plants = []  # NEW – list replaces single `plant` variable
    for i in range(num_isru_plants):
        p = ISRUPlant(system, f"ISRU_Plant_{i+1}", isruPlantData.raw['attributes'])
        # Override Processing Rate with value from sliders
        p.processingRate = optionsDict["ISRU_Plant_Processing_Rate"]
        logger.add(p)
        plants.append(p)

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

    # =========================================================
    # MODIFICATION 4: Build a LIST of regolith rovers instead of
    # a single rover.  All rovers are identical and travel the
    # same route independently, contributing parallel haul
    # capacity by each depositing roverBatch kg per trip into
    # the shared regolithBuffer.
    # =========================================================
    regolithCargoRovers = []  # NEW – list replaces single variable
    for i in range(num_regolith_rovers):
        r = LunarRover(system, name=f"Regolith Cargo Rover {i+1}", roverType="cargo", attributeDict=roverData.raw['attributes'])
        # Override Energy Consumption and travel time from sliders
        r.energyPerKmPerKg = optionsDict["Rover_Energy_Consumption"]
        r.hoursPerKm       = optionsDict["Rover_Travel_Time"]
        logger.add(r)
        regolithCargoRovers.append(r)

    # LOX Cargo Rover – single rover; unchanged
    LOXCargoRover = LunarRover(system, name="LOX Cargo Rover", roverType="cargo", attributeDict=roverData.raw['attributes'])
    LOXCargoRover.energyPerKmPerKg = optionsDict["Rover_Energy_Consumption"]
    LOXCargoRover.hoursPerKm       = optionsDict["Rover_Travel_Time"]
    logger.add(LOXCargoRover)

    # Start processes
    regolith_haul_distance = optionsDict["Regolith_Haul_Distance"] # km, round trip distance for hauling regolith from source to plant
    LOX_haul_distance      = optionsDict["LOX_Haul_Distance"]      # km, round trip distance for hauling LOX from plant to landing zone
    transport_threshold    = optionsDict["LOX_Transport_Threshold"] # kg, how much LOX needs to be stored before it is transported to the landing zone

    # =========================================================
    # MODIFICATION 5: Spawn one regolithRoverController process
    # per rover.  Each rover runs its own continuous loop,
    # depositing into the shared regolithBuffer independently,
    # giving the fleet combined (parallel) haul capacity.
    # =========================================================
    for r in regolithCargoRovers:  # NEW loop
        system.process(regolithRoverController(system, regolithBuffer, roverBatch, regolith_haul_distance, r))

    # =========================================================
    # MODIFICATION 6: Spawn one plantController process per ISRU
    # plant.  All plants compete for batches from the same
    # regolithBuffer (SimPy Container .get() is atomic), so they
    # act as parallel processing units without double-consuming.
    # Also spawn a LOXStorageEnergy accounting process per plant.
    # =========================================================
    for p in plants:  # NEW loop
        system.process(plantController(system, p, regolithBuffer, roverBatch))
        system.process(LOXStorageEnergy(system, p, dt=1.0))

    # =========================================================
    # MODIFICATION 7: Create a SimPy Resource (capacity=1) that
    # acts as a mutex for the single LOX cargo rover.  One
    # LOXDeliveryController process is spawned per plant; each
    # independently monitors its own LOX level and joins the
    # FCFS queue for the rover when its threshold is reached.
    # =========================================================
    LOXRoverResource = simpy.Resource(system, capacity=1)  # NEW - shared rover mutex
    for p in plants:  # NEW - one controller per plant
        system.process(LOXDeliveryController(
            system, p, LOXRoverResource, LOXCargoRover,
            landingZone, distance=LOX_haul_distance,
            transportThreshold=transport_threshold
        ))

    system.process(powerManager.managePower(dt=1.0))  # Power management

    # Experiment ----------------------------------------------
    print("="*70)
    print(experiment)
    print("="*70)
    system.run(until=simDuration)

    # Analysis ------------------------------------------------
    print("\n" + "="*70)
    print("SIMULATION RESULTS")
    print("="*70)

    # =========================================================
    # MODIFICATION 8: Print per-plant results for every ISRU
    # plant in the fleet, then print fleet-level aggregates.
    # =========================================================
    total_lox_stored      = sum(p.LOXStored              for p in plants)
    total_energy_isru     = sum(p.totalEnergyConsumed    for p in plants)
    total_uptime          = sum(p.processingUptime       for p in plants)
    total_regolith_recv   = sum(p.regolithRecieved       for p in plants)
    total_lox_production  = sum(p.totalLOXProduction     for p in plants)

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

    # =========================================================
    # MODIFICATION 9: Print per-rover results for every regolith
    # rover in the fleet.
    # =========================================================
    for r in regolithCargoRovers:
        print(f"\n{r.name}:")
        print(f"  Total Distance: {r.totalDistanceTraveled:.2f} km")
        print(f"  Energy Consumed: {r.totalEnergyConsumed:.2f} kWh")
        print(f"  Battery Charge: {r.batteryCharge:.2f}/{r.batteryCapacity:.2f} kWh")
        print(f"  Current Load: {r.currentLoad:.2f} kg")

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

    # =========================================================
    # MODIFICATION 10: Build per-plant and per-rover entries in
    # the results dict dynamically, plus fleet-level aggregates.
    # =========================================================
    isru_plant_results = {}
    for p in plants:
        isru_plant_results[p.name] = {
            "LOX_Stored_kg":            round(p.LOXStored, 2),
            "Energy_Consumed_kWh":      round(p.totalEnergyConsumed, 2),
            "Total_Operational_Hours":  round(p.processingUptime, 2),
            "Regolith_Received_kg":     round(p.regolithRecieved, 2),
            "Total_LOX_Production_kg":  round(p.totalLOXProduction, 2),
        }
    isru_plant_results["Fleet_Totals"] = {
        "Num_Plants":                   num_isru_plants,
        "LOX_Stored_kg":                round(total_lox_stored, 2),
        "Energy_Consumed_kWh":          round(total_energy_isru, 2),
        "Total_Operational_Hours":      round(total_uptime, 2),
        "Regolith_Received_kg":         round(total_regolith_recv, 2),
        "Total_LOX_Production_kg":      round(total_lox_production, 2),
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
        "Num_Rovers":           num_regolith_rovers,
        "Total_Distance_km":    round(sum(r.totalDistanceTraveled for r in regolithCargoRovers), 2),
        "Energy_Consumed_kWh":  round(sum(r.totalEnergyConsumed   for r in regolithCargoRovers), 2),
    }

    final_results = {
        "Sim_Metrics": {
            "Simulation_Run_Time": round(elapsed_time, 4)
        },
        # Per-plant dict + fleet totals (MODIFIED)
        "ISRU_Plants": isru_plant_results,
        "Solar_Power_System": {
            "Total_Generated_kWh": round(solarSystem.totalEnergyGenerated, 2),
            "From_Battery_kWh":    round(solarSystem.totalEnergyFromBattery, 2),
            "Battery_Charge_kWh":  round(solarSystem.batteryCharge, 2),
            "Battery_Capacity_kWh":round(solarSystem.batteryCapacity, 2)
        },
        "Power_Manager": {
            "Energy_Generated_Time_Array_kWh": powerManager.powerGeneratedSeries,
            "Total_Demand_Time_Array_kWh":     powerManager.totalDemandSeries
        },
        "Habitat": {
            "Name":                habitat.name,
            "Energy_Consumed_kWh": round(habitat.totalEnergyConsumed, 2)
        },
        "Communications": {
            "Name":                comms.name,
            "Energy_Consumed_kWh": round(comms.totalEnergyConsumed, 2)
        },
        "Landing_Zone": {
            "Name":                landingZone.name,
            "LOX_Stored_kg":       round(landingZone.loxStored, 2),
            "Energy_Consumed_kWh": round(landingZone.totalEnergyConsumed, 2)
        },
        # Per-rover dict + fleet totals (MODIFIED)
        "Regolith_Cargo_Rovers": regolith_rover_results,
        "LOX_Cargo_Rover": {
            "Name":                 LOXCargoRover.name,
            "Total_Distance_km":    round(LOXCargoRover.totalDistanceTraveled, 2),
            "Energy_Consumed_kWh":  round(LOXCargoRover.totalEnergyConsumed, 2),
            "Battery_Charge_kWh":   round(LOXCargoRover.batteryCharge, 2),
            "Battery_Capacity_kWh": round(LOXCargoRover.batteryCapacity, 2),
            "Current_Load_kg":      round(LOXCargoRover.currentLoad, 2)
        },
        "Charging_Station": {
            "Name":                          chargingStation.name,
            "Energy_Consumed_kWh":           round(chargingStation.totalEnergyConsumed, 2),
            "Energy_Delivered_to_Rovers_kWh":round(chargingStation.totalEnergyDelivered, 2)
        }
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