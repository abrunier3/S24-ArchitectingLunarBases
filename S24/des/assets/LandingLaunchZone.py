import simpy

# -------------------------------------------------
# Landing and Launch Zone
# -------------------------------------------------
class LandingLaunchZone:
    """
    Landing and launch facility with LOX storage and power consumption.
    """
    def __init__(self, system, name, attributeDict):
        """
        Args:
            system: SimPy environment
            name: Facility identifier
            loxCapacity: Maximum LOX storage capacity (kg)
            utilitiesPowerRate: Power for utilities/lighting (kW)
        """
        self.system = system
        self.name = name
        self.loxCapacity = attributeDict["loxCapacity"]
        self.loxStored = attributeDict["loxStored"]
        self.utilitiesPowerRate = attributeDict["utilitiesPowerRate"]
        self.totalEnergyConsumed = attributeDict["totalEnergyConsumed"]
        self.chillingPowerPerKgLOX = attributeDict["chillingPowerPerKgLox"] #kW / kg LOX
        self.spikeEvents = []  # List of (time, energy) tuples

    def receiveLOX(self, amount):
        """Receive LOX delivery from rover"""
        if self.loxStored + amount > self.loxCapacity:
            raise ValueError(
                f"{self.name}: Cannot store {amount} kg LOX, exceeds capacity. "
                f"Current: {self.loxStored} kg, Capacity: {self.loxCapacity} kg"
            )
        self.loxStored += amount
        print(f"[{self.system.now:.2f} hr] {self.name}: Received {amount:.2f} kg LOX "
              f"(Total stored: {self.loxStored:.2f} kg)")
        
    def consumeLOX(self, amount):
        """Consume LOX (e.g., for launch)"""
        if amount > self.loxStored:
            raise ValueError(f"{self.name}: Insufficient LOX stored")
        self.loxStored -= amount
        return amount
    
    def scheduleSpike(self, time, energy):
        """Schedule a one-time power spike event"""
        self.spikeEvents.append((time, energy))
        
    def getCurrentPowerDemand(self, dt):
        """Calculate current power demand for time period dt (hours)"""
        # Base demand: chilling + utilities
        basePower = self.chillingPowerPerKgLOX*self.loxStored + self.utilitiesPowerRate
        demand = basePower * dt
        
        # Check for spike events
        currentTime = self.system.now
        spikesToRemove = []
        for i, (spikeTime, spikeEnergy) in enumerate(self.spikeEvents):
            if abs(currentTime - spikeTime) < dt/2:
                demand += spikeEnergy
                spikesToRemove.append(i)
                print(f"[{currentTime:.2f} hr] {self.name}: Power spike of {spikeEnergy:.2f} kWh")
        
        for i in reversed(spikesToRemove):
            self.spikeEvents.pop(i)
        
        self.totalEnergyConsumed += demand
        return demand
    
    def getLoggingAttributes(self):
        attr = {
            "Name": self.name,
            "LOX_Capacity":self.loxCapacity,
            "LOX_Stored": self.loxStored,
            "utilities_power_rate":self.utilitiesPowerRate,
            "Energy_Consumed_kWh": self.totalEnergyConsumed,
            "chilling_power_per_kg_LOX": self.chillingPowerPerKgLOX,
            "Spike_Events_Array": self.spikeEvents
        }
        return attr


# class LandingLaunchZone:
#     """
#     Landing and launch facility with LOX storage and power consumption.
#     """
#     def __init__(self, system, name, loxCapacity, utilitiesPowerRate):
#         """
#         Args:
#             system: SimPy environment
#             name: Facility identifier
#             loxCapacity: Maximum LOX storage capacity (kg)
#             utilitiesPowerRate: Power for utilities/lighting (kW)
#         """
#         self.system = system
#         self.name = name
#         self.loxCapacity = loxCapacity
#         self.loxStored = 0
#         self.utilitiesPowerRate = utilitiesPowerRate
#         self.totalEnergyConsumed = 0
#         self.spikeEvents = []  # List of (time, energy) tuples

#     def receiveLOX(self, amount):
#         """Receive LOX delivery from rover"""
#         if self.loxStored + amount > self.loxCapacity:
#             raise ValueError(
#                 f"{self.name}: Cannot store {amount} kg LOX, exceeds capacity. "
#                 f"Current: {self.loxStored} kg, Capacity: {self.loxCapacity} kg"
#             )
#         self.loxStored += amount
#         print(f"[{self.system.now:.2f} hr] {self.name}: Received {amount:.2f} kg LOX "
#               f"(Total stored: {self.loxStored:.2f} kg)")
        
#     def consumeLOX(self, amount):
#         """Consume LOX (e.g., for launch)"""
#         if amount > self.loxStored:
#             raise ValueError(f"{self.name}: Insufficient LOX stored")
#         self.loxStored -= amount
#         return amount
    
#     def scheduleSpike(self, time, energy):
#         """Schedule a one-time power spike event"""
#         self.spikeEvents.append((time, energy))
        
#     def getCurrentPowerDemand(self, dt):
#         """Calculate current power demand for time period dt (hours)"""
#         # Base demand: chilling + utilities
#         basePower = 0.31*self.loxStored + self.utilitiesPowerRate
#         demand = basePower * dt
        
#         # Check for spike events
#         currentTime = self.system.now
#         spikesToRemove = []
#         for i, (spikeTime, spikeEnergy) in enumerate(self.spikeEvents):
#             if abs(currentTime - spikeTime) < dt/2:
#                 demand += spikeEnergy
#                 spikesToRemove.append(i)
#                 print(f"[{currentTime:.2f} hr] {self.name}: Power spike of {spikeEnergy:.2f} kWh")
        
#         for i in reversed(spikesToRemove):
#             self.spikeEvents.pop(i)
        
#         self.totalEnergyConsumed += demand
#         return demand

#-----------------------------------------------------------------------------------------------------------------------------------------
# re-written

# import simpy
# from typing import Any, Dict, List, Tuple


# class LandingLaunchZone:
#     """
#     Discrete-event simulation model of a lunar landing and launch facility.

#     The facility is responsible for:
#     - storing liquid oxygen (LOX)
#     - consuming LOX for operations (e.g., launches)
#     - consuming electrical power for utilities and cryogenic storage
#     - handling transient power demand spikes

#     The model tracks:
#     - LOX inventory levels
#     - cumulative energy consumption
#     - scheduled transient energy events
#     """

#     def __init__(
#         self,
#         system: simpy.Environment,
#         name: str,
#         attribute_dict: Dict[str, Any],
#     ) -> None:
#         self.system = system
#         self.name = name

#         self.lox_capacity = attribute_dict["loxCapacity"]                 # kg
#         self.lox_stored = attribute_dict["loxStored"]                     # kg

#         self.utilities_power_rate = attribute_dict["utilitiesPowerRate"]  # kW
#         self.chilling_power_per_kg = attribute_dict["chillingPowerPerKgLox"]  # kW/kg

#         self.total_energy_consumed = attribute_dict["totalEnergyConsumed"]  # kWh

#         self.spike_events: List[Tuple[float, float]] = []

#     def receive_lox(self, amount: float) -> None:
#         """
#         Receive a delivered quantity of LOX.

#         Parameters
#         ----------
#         amount : float
#             Amount of LOX delivered [kg].
#         """
#         if self.lox_stored + amount > self.lox_capacity:
#             raise ValueError(
#                 f"{self.name}: Cannot store {amount:.2f} kg LOX. "
#                 f"Capacity exceeded (current: {self.lox_stored:.2f}, "
#                 f"capacity: {self.lox_capacity:.2f})."
#             )

#         self.lox_stored += amount

#         print(
#             f"[{self.system.now:.2f} hr] {self.name}: Received "
#             f"{amount:.2f} kg LOX (total: {self.lox_stored:.2f} kg)"
#         )

#     def consume_lox(self, amount: float) -> float:
#         """
#         Consume LOX from storage.

#         Parameters
#         ----------
#         amount : float
#             Amount of LOX to consume [kg].

#         Returns
#         -------
#         float
#             The amount of LOX consumed.
#         """
#         if amount > self.lox_stored:
#             raise ValueError(f"{self.name}: Insufficient LOX available.")

#         self.lox_stored -= amount
#         return amount

#     def schedule_spike(self, time: float, energy: float) -> None:
#         """
#         Schedule a one-time power demand spike.

#         Parameters
#         ----------
#         time : float
#             Simulation time at which the spike occurs [hr].
#         energy : float
#             Energy demand of the spike [kWh].
#         """
#         self.spike_events.append((time, energy))

#     def get_current_power_demand(self, dt: float) -> float:
#         """
#         Compute power demand over a time interval.

#         Parameters
#         ----------
#         dt : float
#             Time interval [hr].

#         Returns
#         -------
#         float
#             Energy demand over the interval [kWh].
#         """
#         # Base demand: chilling + utilities
#         base_power = (
#             self.chilling_power_per_kg * self.lox_stored
#             + self.utilities_power_rate
#         )

#         demand = base_power * dt

#         current_time = self.system.now
#         spikes_to_remove: List[int] = []

#         for i, (spike_time, spike_energy) in enumerate(self.spike_events):
#             if abs(current_time - spike_time) < dt / 2:
#                 demand += spike_energy
#                 spikes_to_remove.append(i)

#                 print(
#                     f"[{current_time:.2f} hr] {self.name}: "
#                     f"Power spike of {spike_energy:.2f} kWh"
#                 )

#         for i in reversed(spikes_to_remove):
#             self.spike_events.pop(i)

#         self.total_energy_consumed += demand
#         return demand

#     def get_logging_attributes(self) -> Dict[str, Any]:
#         """
#         Return current facility state for logging.
#         """
#         return {
#             "name": self.name,
#             "lox_capacity": self.lox_capacity,
#             "lox_stored": self.lox_stored,
#             "utilities_power_rate": self.utilities_power_rate,
#             "chilling_power_per_kg": self.chilling_power_per_kg,
#             "total_energy_consumed": self.total_energy_consumed,
#             "spike_events": self.spike_events,
#         }