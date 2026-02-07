import simpy

# -------------------------------------------------
# Solar Panel / Power Generation System
# -------------------------------------------------

class SolarPowerSystem:
    """
    Solar panel system with battery storage and degradation capabilities.
    Manages power generation, battery charging, and power distribution.
    """
    def __init__(self, system, attributeDict):
        """
        Args:
            system: SimPy environment
            powerOutput: Power generation rate (kW)
            batteryCapacity: Maximum battery capacity (kWh)
            batteryDegradationFactor: Factor to degrade battery capacity over time (0-1)
            powerDegradationFactor: Factor to degrade power output over time (0-1)
        """
        self.system = system
        self.nominalPowerOutput = attributeDict["powerOutput"]  # kW
        self.powerDegradationFactor = attributeDict["powerDegradationFactor"]
        self.currentPowerOutput = self.nominalPowerOutput * self.powerDegradationFactor  # kW
        
        self.batteryDegradationFactor = attributeDict["batteryDegradationFactor"]
        self.batteryCapacity = attributeDict["batteryCapacity"] * self.batteryDegradationFactor  # kWh
        self.batteryCharge = attributeDict["batteryCharge"]
        #self.batteryCharge = self.batteryCapacity * self.batteryDegradationFactor  # Start fully charged
        
        self.totalEnergyGenerated = attributeDict["totalEnergyGenerated"] # kWh
        self.totalEnergyFromBattery = attributeDict["totalEnergyFromBattery"]  # kWh
        
    def generatePower(self, duration):
        """Generate power over a given duration (hours)"""
        energyGenerated = self.currentPowerOutput * duration
        self.totalEnergyGenerated += energyGenerated
        return energyGenerated
    
    def chargeBattery(self, energy):
        """
        Charge battery with excess energy.
        Returns amount of energy actually stored (remainder is wasted).
        """
        spaceAvailable = self.batteryCapacity - self.batteryCharge
        energyStored = min(energy, spaceAvailable)
        self.batteryCharge += energyStored
        return energyStored
    
    def dischargeBattery(self, energy):
        """
        Discharge energy from battery.
        Returns amount of energy actually discharged.
        Raises RuntimeError if insufficient energy and battery depleted.
        """
        energyAvailable = min(energy, self.batteryCharge)
        self.batteryCharge -= energyAvailable
        self.totalEnergyFromBattery += energyAvailable
        
        if energyAvailable < energy:
            deficit = energy - energyAvailable
            raise RuntimeError(
                f"[{self.system.now:.2f} hr] POWER FAILURE: Insufficient power! "
                f"Needed {energy:.2f} kWh, but only {energyAvailable:.2f} kWh available. "
                f"Deficit: {deficit:.2f} kWh. Battery depleted."
            )
        
        return energyAvailable
    
    def degradePower(self, factor):
        """Apply degradation factor to power output"""
        self.powerDegradationFactor *= factor
        self.currentPowerOutput = self.nominalPowerOutput * self.powerDegradationFactor
        
    def degradeBattery(self, factor):
        """Apply degradation factor to battery capacity"""
        self.batteryDegradationFactor *= factor
        oldCapacity = self.batteryCapacity
        self.batteryCapacity = self.nominalPowerOutput * self.batteryDegradationFactor
        # Adjust current charge proportionally
        if oldCapacity > 0:
            self.batteryCharge = (self.batteryCharge / oldCapacity) * self.batteryCapacity









# class SolarPowerSystem:
#     """
#     Solar panel system with battery storage and degradation capabilities.
#     Manages power generation, battery charging, and power distribution.
#     """
#     def __init__(self, system, powerOutput, batteryCapacity=0, batteryDegradationFactor=1.0, powerDegradationFactor=1.0):
#         """
#         Args:
#             system: SimPy environment
#             powerOutput: Power generation rate (kW)
#             batteryCapacity: Maximum battery capacity (kWh)
#             batteryDegradationFactor: Factor to degrade battery capacity over time (0-1)
#             powerDegradationFactor: Factor to degrade power output over time (0-1)
#         """
#         self.system = system
#         self.nominalPowerOutput = powerOutput  # kW
#         self.currentPowerOutput = powerOutput * powerDegradationFactor  # kW
#         self.powerDegradationFactor = powerDegradationFactor
        
#         self.batteryCapacity = batteryCapacity * batteryDegradationFactor  # kWh
#         self.batteryDegradationFactor = batteryDegradationFactor
#         self.batteryCharge = batteryCapacity * batteryDegradationFactor  # Start fully charged
        
#         self.totalEnergyGenerated = 0  # kWh
#         self.totalEnergyFromBattery = 0  # kWh
        
#     def generatePower(self, duration):
#         """Generate power over a given duration (hours)"""
#         energyGenerated = self.currentPowerOutput * duration
#         self.totalEnergyGenerated += energyGenerated
#         return energyGenerated
    
#     def chargeBattery(self, energy):
#         """
#         Charge battery with excess energy.
#         Returns amount of energy actually stored (remainder is wasted).
#         """
#         spaceAvailable = self.batteryCapacity - self.batteryCharge
#         energyStored = min(energy, spaceAvailable)
#         self.batteryCharge += energyStored
#         return energyStored
    
#     def dischargeBattery(self, energy):
#         """
#         Discharge energy from battery.
#         Returns amount of energy actually discharged.
#         Raises RuntimeError if insufficient energy and battery depleted.
#         """
#         energyAvailable = min(energy, self.batteryCharge)
#         self.batteryCharge -= energyAvailable
#         self.totalEnergyFromBattery += energyAvailable
        
#         if energyAvailable < energy:
#             deficit = energy - energyAvailable
#             raise RuntimeError(
#                 f"[{self.system.now:.2f} hr] POWER FAILURE: Insufficient power! "
#                 f"Needed {energy:.2f} kWh, but only {energyAvailable:.2f} kWh available. "
#                 f"Deficit: {deficit:.2f} kWh. Battery depleted."
#             )
        
#         return energyAvailable
    
#     def degradePower(self, factor):
#         """Apply degradation factor to power output"""
#         self.powerDegradationFactor *= factor
#         self.currentPowerOutput = self.nominalPowerOutput * self.powerDegradationFactor
        
#     def degradeBattery(self, factor):
#         """Apply degradation factor to battery capacity"""
#         self.batteryDegradationFactor *= factor
#         oldCapacity = self.batteryCapacity
#         self.batteryCapacity = self.nominalPowerOutput * self.batteryDegradationFactor
#         # Adjust current charge proportionally
#         if oldCapacity > 0:
#             self.batteryCharge = (self.batteryCharge / oldCapacity) * self.batteryCapacity
