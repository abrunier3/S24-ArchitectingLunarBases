"""
Name:       ISRU_DES_Model_V3.py
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
from ISRUPlant import ISRUPlant
from SolarPowerSystem import SolarPowerSystem
from PowerManager import PowerManager
from HabitationModule import HabitationModule
from CommunicationModule import CommunicationModule
from LunarRover import LunarRover
from RoverChargingStation import RoverChargingStation
from LandingLaunchZone import LandingLaunchZone



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

def LOXDeliveryController(system, plant:ISRUPlant, rover: LunarRover, landingZone:LandingLaunchZone, distance, transportThreshold):
    while True:
        yield system.timeout(1)
        if plant.LOXStored > transportThreshold:
            LOXToTransport = plant.LOXStored #kg
            plant.LOXStored = 0
            print(f"[{system.now:.2f} hr] Just emptied LOX stores at the ISRU plant. The following value should read 0: {plant.LOXStored}")
            #Tell rover to load LOX stored
            rover.loadCargo(LOXToTransport)
            #Tell rover to travel roundtrip distance
            yield system.process(rover.travel(distance))
            #Unload rover
            rover.unloadCargo()
            #Have Landing Zone recieve the LOX
            landingZone.receiveLOX(LOXToTransport)
            #print("Transported " + str(LOXToTransport) + " kg of LOX to " + landingZone.name + " which now has " + str(landingZone.loxStored) + " kg of LOX")
            print(f"[{system.now:.2f} hr] Transported {LOXToTransport} kg of LOX to {landingZone.name} which now has {landingZone.loxStored} kg of LOX")
            #print("The ISRU plant now has " + str(plant.LOXStored) + "kg of LOX stored.")

# -------------------------------------------------
# Example Usage in Main
# -------------------------------------------------
def main():
    # Experiment data -----------------------------------------
    experiment = "ISRU Processing Plant with Full Infrastructure"
    roverBatch = 4000          # kg
    roverTravelTime = 5        # hr between deliveries
    simDuration = 60           # hr

    # Model ---------------------------------------------------
    system = simpy.Environment()
    
    # Resources
    regolithBuffer = simpy.Container(system, capacity=20_000)

    # ISRU Plant
    plant = ISRUPlant(system, 1600, 0.1)
    
    # Solar Power System (100 kW output, 500 kWh battery)
    solarSystem = SolarPowerSystem(
        system, 
        powerOutput=100,  # kW
        batteryCapacity=500,  # kWh
        batteryDegradationFactor=1.0,
        powerDegradationFactor=1.0
    )
    
    # Power Manager
    powerManager = PowerManager(system, solarSystem)
    
    # Habitation Module (5 kW constant)
    habitat = HabitationModule(system, "Habitat-1", constantPowerRate=5)
    habitat.scheduleSpike(10, 20)  # 20 kWh spike at hour 10
    powerManager.registerConsumer(habitat)
    
    # Communication Module (2 kW constant)
    comms = CommunicationModule(system, "CommArray-1", constantPowerRate=2)
    comms.scheduleSpike(15, 10)  # 10 kWh spike at hour 15
    powerManager.registerConsumer(comms)
    
    # Landing/Launch Zone (10 kW chilling, 3 kW utilities)
    landingZone = LandingLaunchZone(
        system, 
        "LZ-Alpha",
        loxCapacity=50000,  # kg
        utilitiesPowerRate=3  # kW
    )
    landingZone.scheduleSpike(25, 50)  # 50 kWh spike at hour 25
    powerManager.registerConsumer(landingZone)
    
    # Rover Charging Station
    chargingStation = RoverChargingStation(
        system,
        "ChargeStation-1",
        chargingPowerRate=20,  # kW
        efficiencyFactor=0.85
    )
    powerManager.registerConsumer(chargingStation)
    
    regolithCargoRover = LunarRover(system, name="Regolith Cargo Rover", roverType="cargo", maxCapacity=5000, energyPerKmPerKg=3.4*10**-4, batteryCapacity=100, hoursPerKm=5)
    LOXCargoRover = LunarRover(system, name="LOX Cargo Rover", roverType="cargo", maxCapacity=5000, energyPerKmPerKg=3.4*10**-4, batteryCapacity=100, hoursPerKm=5)

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
    
    print(f"\nSolar Power System:")
    print(f"  Total Generated: {solarSystem.totalEnergyGenerated:.2f} kWh")
    print(f"  From Battery: {solarSystem.totalEnergyFromBattery:.2f} kWh")
    print(f"  Battery Charge: {solarSystem.batteryCharge:.2f}/{solarSystem.batteryCapacity:.2f} kWh")
    
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