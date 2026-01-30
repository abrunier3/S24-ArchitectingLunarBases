import simpy

# -------------------------------------------------
# Communication Module
# -------------------------------------------------
class CommunicationModule:
    """
    Communication module with constant and spike power consumption.
    """
    def __init__(self, system, name, constantPowerRate):
        """
        Args:
            system: SimPy environment
            name: Module identifier
            constantPowerRate: Constant power consumption (kW)
        """
        self.system = system
        self.name = name
        self.constantPowerRate = constantPowerRate  # kW
        self.totalEnergyConsumed = 0  # kWh
        self.spikeEvents = []  # List of (time, energy) tuples
        
    def setConstantPowerRate(self, rate):
        """Change the constant power consumption rate"""
        self.constantPowerRate = rate
        
    def scheduleSpike(self, time, energy):
        """Schedule a one-time power spike event"""
        self.spikeEvents.append((time, energy))
        
    def getCurrentPowerDemand(self, dt):
        """Calculate current power demand for time period dt (hours)"""
        demand = self.constantPowerRate * dt
        
        # Check for spike events in current time window
        currentTime = self.system.now
        spikesToRemove = []
        for i, (spikeTime, spikeEnergy) in enumerate(self.spikeEvents):
            if abs(currentTime - spikeTime) < dt/2:  # Spike occurs in this timestep
                demand += spikeEnergy
                spikesToRemove.append(i)
                print(f"[{currentTime:.2f} hr] {self.name}: Power spike of {spikeEnergy:.2f} kWh")
        
        # Remove processed spikes
        for i in reversed(spikesToRemove):
            self.spikeEvents.pop(i)
        
        self.totalEnergyConsumed += demand
        return demand