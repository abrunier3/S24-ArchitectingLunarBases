import simpy

# -------------------------------------------------
# Lunar Rover (Requirement 5)
# -------------------------------------------------

class LunarRover:
    """
    Lunar rover with cargo/crew capacity and energy consumption.
    """
    def __init__(self, system, name, roverType, attributeDict):
        """
        Args:
            system: SimPy environment
            name: Rover identifier
            roverType: 'crew' or 'cargo'
            maxCapacity: Maximum cargo capacity (kg)
            energyPerKmPerKg: Energy consumption per km traveled (kWh/km)
            batteryCapacity: Rover battery capacity (kWh)
        """
        self.system = system
        self.name = name
        self.type = roverType
        self.maxCapacity = attributeDict["maxCapacity"]
        self.currentLoad = 0
        self.energyPerKmPerKg = attributeDict["energyPerKmPerKg"]
        self.batteryCapacity = attributeDict["batteryCapacity"]
        #self.batteryCharge = self.batteryCapacity  # Start fully charged
        self.batteryCharge = attributeDict["batteryCharge"]
        self.totalDistanceTraveled = attributeDict["totalDistanceTraveled"]
        self.totalEnergyConsumed = attributeDict["totalEnergyConsumed"]
        self.hoursPerKm = attributeDict["hoursPerKm"]
        
    def travel(self, distance):
        """
        Travel a given distance (km).
        Returns energy consumed.
        """
        energyNeeded = distance * self.energyPerKmPerKg * self.currentLoad
        
        if energyNeeded > self.batteryCharge:
            raise RuntimeError(
                f"[{self.system.now:.2f} hr] {self.name}: Insufficient battery! "
                f"Needed {energyNeeded:.2f} kWh, have {self.batteryCharge:.2f} kWh"
            )
        
        self.batteryCharge -= energyNeeded
        self.totalDistanceTraveled += distance
        self.totalEnergyConsumed += energyNeeded
        print("The total energy consumed by " + self.name + " is " + str(self.totalEnergyConsumed) + " kWh.")
        yield self.system.timeout(distance*self.hoursPerKm)
        return energyNeeded
    
    def loadCargo(self, mass):
        """Load cargo onto rover"""
        if self.currentLoad + mass > self.maxCapacity:
            raise ValueError(f"{self.name}: Cannot load {mass} kg, exceeds capacity")
        self.currentLoad += mass
        
    def unloadCargo(self):
        """Unload all cargo from rover"""
        cargo = self.currentLoad
        self.currentLoad = 0
        return cargo

    def getLoggingAttributes(self):
        attr = {
            "Name": self.name,
            "rover_type":self.type,
            "max_capacity": self.maxCapacity,
            "current_load":self.currentLoad,
            "energy_per_km_per_kg": self.energyPerKmPerKg,
            "battery_capacity": self.batteryCapacity,
            "battery_charge": self.batteryCharge,
            "total_distance_traveled": self.totalDistanceTraveled,
            "total_energy_consumed": self.totalEnergyConsumed,
            "hours_per_km": self.hoursPerKm
        }
        return attr

# class LunarRover:
#     """
#     Lunar rover with cargo/crew capacity and energy consumption.
#     """
#     def __init__(self, system, name, roverType, maxCapacity, energyPerKmPerKg, batteryCapacity, hoursPerKm):
#         """
#         Args:
#             system: SimPy environment
#             name: Rover identifier
#             roverType: 'crew' or 'cargo'
#             maxCapacity: Maximum cargo capacity (kg)
#             energyPerKmPerKg: Energy consumption per km traveled (kWh/km)
#             batteryCapacity: Rover battery capacity (kWh)
#         """
#         self.system = system
#         self.name = name
#         self.type = roverType
#         self.maxCapacity = maxCapacity
#         self.currentLoad = 0
#         self.energyPerKmPerKg = energyPerKmPerKg
#         self.batteryCapacity = batteryCapacity
#         self.batteryCharge = batteryCapacity  # Start fully charged
#         self.totalDistanceTraveled = 0
#         self.totalEnergyConsumed = 0
#         self.hoursPerKm = hoursPerKm
        
#     def travel(self, distance):
#         """
#         Travel a given distance (km).
#         Returns energy consumed.
#         """
#         energyNeeded = distance * self.energyPerKmPerKg * self.currentLoad
        
#         if energyNeeded > self.batteryCharge:
#             raise RuntimeError(
#                 f"[{self.system.now:.2f} hr] {self.name}: Insufficient battery! "
#                 f"Needed {energyNeeded:.2f} kWh, have {self.batteryCharge:.2f} kWh"
#             )
        
#         self.batteryCharge -= energyNeeded
#         self.totalDistanceTraveled += distance
#         self.totalEnergyConsumed += energyNeeded
#         print("The total energy consumed by " + self.name + " is " + str(self.totalEnergyConsumed) + " kWh.")
#         yield self.system.timeout(distance*self.hoursPerKm)
#         return energyNeeded
    
#     def loadCargo(self, mass):
#         """Load cargo onto rover"""
#         if self.currentLoad + mass > self.maxCapacity:
#             raise ValueError(f"{self.name}: Cannot load {mass} kg, exceeds capacity")
#         self.currentLoad += mass
        
#     def unloadCargo(self):
#         """Unload all cargo from rover"""
#         cargo = self.currentLoad
#         self.currentLoad = 0
#         return cargo
