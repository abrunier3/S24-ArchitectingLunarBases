import simpy

# -------------------------------------------------
# Power Manager (handles distribution)
# -------------------------------------------------
class PowerManager:
    """
    Manages power distribution from power system to all consumers.
    Tracks all power demands and manages battery charging/discharging.
    """
    def __init__(self, system, solarSystem):
        self.system = system
        self.solarSystem = solarSystem
        self.consumers = []  # List of power consumers
        
    def registerConsumer(self, consumer):
        """Register a power consumer"""
        self.consumers.append(consumer)
        
    def managePower(self, dt=1.0):
        """
        Continuously manage power generation and distribution.
        dt = time step (hours)
        """
        while True:
            yield self.system.timeout(dt)
            
            # Generate power from solar panels
            energyGenerated = self.solarSystem.generatePower(dt)
            
            # Calculate total demand
            totalDemand = 0
            for consumer in self.consumers:
                if hasattr(consumer, 'getCurrentPowerDemand'):
                    totalDemand += consumer.getCurrentPowerDemand(dt)
            
            # Manage power balance
            energyBalance = energyGenerated - totalDemand
            
            if energyBalance > 0:
                # Excess power - charge battery
                stored = self.solarSystem.chargeBattery(energyBalance)
                if stored < energyBalance:
                    wasted = energyBalance - stored
                    # print(f"[{self.system.now:.2f} hr] Wasted {wasted:.2f} kWh (battery full)")
            elif energyBalance < 0:
                # Deficit - discharge battery
                needed = abs(energyBalance)
                try:
                    self.solarSystem.dischargeBattery(needed)
                except RuntimeError as e:
                    print(str(e))
                    raise
