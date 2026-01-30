import simpy

# -------------------------------------------------
# Landing and Launch Zone
# -------------------------------------------------
class LandingLaunchZone:
    """
    Landing and launch facility with LOX storage and power consumption.
    """
    def __init__(self, system, name, loxCapacity, utilitiesPowerRate):
        """
        Args:
            system: SimPy environment
            name: Facility identifier
            loxCapacity: Maximum LOX storage capacity (kg)
            utilitiesPowerRate: Power for utilities/lighting (kW)
        """
        self.system = system
        self.name = name
        self.loxCapacity = loxCapacity
        self.loxStored = 0
        self.utilitiesPowerRate = utilitiesPowerRate
        self.totalEnergyConsumed = 0
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
        basePower = 0.31*self.loxStored + self.utilitiesPowerRate
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