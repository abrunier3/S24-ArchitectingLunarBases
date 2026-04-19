import simpy

# -------------------------------------------------
# Solar Panel / Power Generation System
# -------------------------------------------------

class SolarPowerSystem:
    """
    Solar panel system with battery storage and degradation capabilities.
    Manages power generation, battery charging, and power distribution.
    """
    def __init__(self, system, name, attributeDict):
        """
        Args:
            system: SimPy environment
            powerOutput: Power generation rate (kW)
            batteryCapacity: Maximum battery capacity (kWh)
            batteryDegradationFactor: Factor to degrade battery capacity over time (0-1)
            powerDegradationFactor: Factor to degrade power output over time (0-1)
        """
        self.name = name
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

    def getLoggingAttributes(self):
        attr = {
            "Name": self.name,
            "power_degradation_factor": self.powerDegradationFactor,
            "current_power_output": self.currentPowerOutput,
            "battery_degradation_factor": self.batteryDegradationFactor,
            "battery_capacity": self.batteryCapacity,
            "battery_charge": self.batteryCharge,
            "total_energy_generated": self.totalEnergyGenerated,
            "total_energy_from_battery": self.totalEnergyFromBattery
        }
        return attr






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



#-----------------------------------------------------------------------------------------------------------------------------------------
# re-written


# import simpy
# from typing import Any, Dict


# class SolarPowerSystem:
#     """
#     Discrete-event simulation model of a solar power generation system with
#     battery storage and degradation effects.

#     The system models:
#     - solar power generation
#     - battery charging and discharging
#     - degradation of generation capacity and storage capacity
#     - cumulative energy production and battery usage

#     All parameters are initialized from an attribute dictionary.
#     """

#     def __init__(
#         self,
#         system: simpy.Environment,
#         name: str,
#         attribute_dict: Dict[str, Any],
#     ) -> None:
#         self.system = system
#         self.name = name

#         # Power generation
#         self.nominal_power_output = attribute_dict["powerOutput"]              # kW
#         self.power_degradation_factor = attribute_dict["powerDegradationFactor"]
#         self.current_power_output = (
#             self.nominal_power_output * self.power_degradation_factor
#         )

#         # Battery
#         self.battery_degradation_factor = attribute_dict["batteryDegradationFactor"]
#         self.battery_capacity = (
#             attribute_dict["batteryCapacity"] * self.battery_degradation_factor
#         )                                                                      # kWh
#         self.battery_charge = attribute_dict["batteryCharge"]                 # kWh

#         # Energy accounting
#         self.total_energy_generated = attribute_dict["totalEnergyGenerated"]  # kWh
#         self.total_energy_from_battery = attribute_dict["totalEnergyFromBattery"]  # kWh

#     def generate_power(self, duration: float) -> float:
#         """
#         Generate electrical energy over a time interval.

#         Parameters
#         ----------
#         duration : float
#             Time duration [hr].

#         Returns
#         -------
#         float
#             Energy generated [kWh].
#         """
#         energy_generated = self.current_power_output * duration
#         self.total_energy_generated += energy_generated
#         return energy_generated

#     def charge_battery(self, energy: float) -> float:
#         """
#         Charge the battery with available energy.

#         Parameters
#         ----------
#         energy : float
#             Available energy [kWh].

#         Returns
#         -------
#         float
#             Energy successfully stored [kWh].
#         """
#         space_available = self.battery_capacity - self.battery_charge
#         energy_stored = min(energy, space_available)

#         self.battery_charge += energy_stored
#         return energy_stored

#     def discharge_battery(self, energy: float) -> float:
#         """
#         Discharge energy from the battery.

#         Parameters
#         ----------
#         energy : float
#             Requested energy [kWh].

#         Returns
#         -------
#         float
#             Energy delivered [kWh].

#         Raises
#         ------
#         RuntimeError
#             If the battery cannot meet the demand.
#         """
#         energy_available = min(energy, self.battery_charge)

#         self.battery_charge -= energy_available
#         self.total_energy_from_battery += energy_available

#         if energy_available < energy:
#             deficit = energy - energy_available
#             raise RuntimeError(
#                 f"[{self.system.now:.2f} hr] POWER FAILURE: "
#                 f"Required {energy:.2f} kWh, available {energy_available:.2f} kWh. "
#                 f"Deficit: {deficit:.2f} kWh."
#             )

#         return energy_available

#     def degrade_power(self, factor: float) -> None:
#         """
#         Apply degradation to power generation.

#         Parameters
#         ----------
#         factor : float
#             Multiplicative degradation factor (0–1).
#         """
#         self.power_degradation_factor *= factor
#         self.current_power_output = (
#             self.nominal_power_output * self.power_degradation_factor
#         )

#     def degrade_battery(self, factor: float) -> None:
#         """
#         Apply degradation to battery capacity.

#         Parameters
#         ----------
#         factor : float
#             Multiplicative degradation factor (0–1).
#         """
#         old_capacity = self.battery_capacity

#         self.battery_degradation_factor *= factor
#         self.battery_capacity *= factor

#         if old_capacity > 0:
#             self.battery_charge = (
#                 self.battery_charge / old_capacity
#             ) * self.battery_capacity

#     def get_logging_attributes(self) -> Dict[str, Any]:
#         """
#         Return current system state for logging.
#         """
#         return {
#             "name": self.name,
#             "nominal_power_output": self.nominal_power_output,
#             "current_power_output": self.current_power_output,
#             "power_degradation_factor": self.power_degradation_factor,
#             "battery_capacity": self.battery_capacity,
#             "battery_charge": self.battery_charge,
#             "battery_degradation_factor": self.battery_degradation_factor,
#             "total_energy_generated": self.total_energy_generated,
#             "total_energy_from_battery": self.total_energy_from_battery,
#         }