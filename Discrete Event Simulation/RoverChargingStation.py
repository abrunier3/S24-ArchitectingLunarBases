import simpy

# -------------------------------------------------
# Rover Charging Station
# -------------------------------------------------
class RoverChargingStation:
    """
    Charging station for lunar rovers with configurable efficiency.
    """
    def __init__(self, system, name, chargingPowerRate, efficiencyFactor=0.9):
        """
        Args:
            system: SimPy environment
            name: Station identifier
            chargingPowerRate: Power consumption/charging rate (kW)
            efficiencyFactor: Charging efficiency (0-1), accounts for losses
        """
        self.system = system
        self.name = name
        self.chargingPowerRate = chargingPowerRate  # kW
        self.efficiencyFactor = efficiencyFactor
        self.totalEnergyConsumed = 0
        self.totalEnergyDelivered = 0
        self.resource = simpy.Resource(system, capacity=1)  # One rover at a time per station
        
    def chargeRover(self, rover):
        """
        Charge a rover to full capacity.
        Returns a SimPy process.
        """
        with self.resource.request() as req:
            yield req
            
            energyNeeded = rover.batteryCapacity - rover.batteryCharge
            energyDelivered = energyNeeded
            energyConsumed = energyNeeded / self.efficiencyFactor  # Account for losses
            
            chargingTime = energyConsumed / self.chargingPowerRate  # hours
            
            print(f"[{self.system.now:.2f} hr] {self.name}: Charging {rover.name} "
                  f"({energyNeeded:.2f} kWh needed, {chargingTime:.2f} hr)")
            
            yield self.system.timeout(chargingTime)
            
            rover.batteryCharge = rover.batteryCapacity
            self.totalEnergyConsumed += energyConsumed
            self.totalEnergyDelivered += energyDelivered
            
            print(f"[{self.system.now:.2f} hr] {self.name}: {rover.name} fully charged")
    
    def getCurrentPowerDemand(self, dt):
        """Calculate current power demand"""
        # Check if station is in use
        if self.resource.count > 0:
            demand = self.chargingPowerRate * dt
            return demand
        return 0