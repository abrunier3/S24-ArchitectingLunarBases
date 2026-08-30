import simpy

from S24.DES_pipeline_version.scenario_equations import evaluate_equations


def _numeric_state(component):
    return {
        key: value for key, value in vars(component).items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def _numeric_state_chain(component):
    state = {}
    current = component
    visited = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        state.update(_numeric_state(current))
        current = getattr(current, "consumer", None)
    return state


def _add_total_energy(component, energy):
    current = component
    visited = set()
    while current is not None and id(current) not in visited:
        visited.add(id(current))
        if hasattr(current, "totalEnergyConsumed"):
            current.totalEnergyConsumed += energy
            return
        current = getattr(current, "consumer", None)


class StaticPowerConsumer:
    """Power consumer used for modules without a dedicated Python process."""

    def __init__(self, system, name):
        self.system = system
        self.name = name
        self.totalEnergyConsumed = 0.0

    def getCurrentPowerDemand(self, dt):
        return 0.0

    def getLoggingAttributes(self):
        return {
            "Name": self.name,
            "Energy_Consumed_kWh": round(self.totalEnergyConsumed, 6),
        }


class PowerModelConsumer:
    """Add a user-defined continuous power model to an event-driven consumer."""

    def __init__(self, consumer, model):
        self.consumer = consumer
        self.model = dict(model or {})
        self.name = consumer.name
        self.lastEquationOutputs = {}
        self.latestBackgroundDemand = 0.0
        self.spikeDelivered = False

    def _profile_power(self, time_hr):
        points = sorted(
            (
                (float(point.get("time_hr", 0.0)), float(point.get("power_kw", 0.0)))
                for point in self.model.get("points", [])
            ),
            key=lambda item: item[0],
        )
        if not points:
            return float(self.model.get("average_kw", 0.0))
        if time_hr <= points[0][0]:
            return points[0][1]
        if time_hr >= points[-1][0]:
            return points[-1][1]
        for left, right in zip(points, points[1:]):
            if left[0] <= time_hr <= right[0]:
                width = right[0] - left[0]
                fraction = 0.0 if width <= 0 else (time_hr - left[0]) / width
                return left[1] + fraction * (right[1] - left[1])
        return points[-1][1]

    def _background_energy(self, dt):
        mode = str(self.model.get("mode", "average")).lower()
        system = getattr(self.consumer, "system", None)
        if system is None and hasattr(self.consumer, "consumer"):
            system = getattr(self.consumer.consumer, "system", None)
        simulation_time = float(getattr(system, "now", 0.0))

        if mode == "equation":
            context = _numeric_state_chain(self.consumer)
            context["LOXStored"] = float(
                context.get("LOXStored", context.get("loxStored", 0.0))
            )
            context.update({
                "SimulationTime": simulation_time,
                "dt": float(dt),
                "PowerIn": 0.0,
                "EnergyConsumed": 0.0,
            })
            outputs = evaluate_equations(
                self.model.get("equation", ""),
                context,
                effect_outputs={"PowerIn", "EnergyConsumed"},
            )
            self.lastEquationOutputs = outputs
            if "EnergyConsumed" in outputs:
                return outputs["EnergyConsumed"]
            return outputs.get("PowerIn", 0.0) * dt

        if mode == "profile":
            return self._profile_power(simulation_time) * dt
        return float(self.model.get("average_kw", 0.0)) * dt

    def _spike_energy(self):
        energy = float(self.model.get("spike_energy_kwh", 0.0) or 0.0)
        trigger_time = float(self.model.get("spike_time_hr", 0.0) or 0.0)
        system = getattr(self.consumer, "system", None)
        if system is None and hasattr(self.consumer, "consumer"):
            system = getattr(self.consumer.consumer, "system", None)
        simulation_time = float(getattr(system, "now", 0.0))
        if energy > 0 and not self.spikeDelivered and simulation_time >= trigger_time:
            self.spikeDelivered = True
            return energy
        return 0.0

    def getCurrentPowerDemand(self, dt):
        event_demand = self.consumer.getCurrentPowerDemand(dt)
        background_demand = self._background_energy(dt) + self._spike_energy()
        if background_demand < 0:
            raise RuntimeError(f"{self.name}: background power demand cannot be negative")
        self.latestBackgroundDemand = background_demand
        _add_total_energy(self.consumer, background_demand)
        return event_demand + background_demand


class EquationPowerConsumer:
    """Apply user equations to an existing consumer's power demand."""

    def __init__(self, consumer, equations):
        self.consumer = consumer
        self.equations = equations or ""
        self.name = consumer.name
        self.lastEquationOutputs = {}

    def getCurrentPowerDemand(self, dt):
        before_total = getattr(self.consumer, "totalEnergyConsumed", None)
        baseline_energy = self.consumer.getCurrentPowerDemand(dt)
        context = _numeric_state(self.consumer)
        context["chillingPowerPerKgLox"] = float(
            context.get(
                "chillingPowerPerKgLox",
                context.get("chillingPowerPerKgLOX", 0.0),
            )
        )
        context.update({
            "SimulationTime": float(self.consumer.system.now),
            "dt": float(dt),
            "PowerIn": baseline_energy / dt if dt else 0.0,
            "EnergyConsumed": baseline_energy,
            "LOXStored": float(getattr(self.consumer, "loxStored", 0.0)),
        })
        outputs = evaluate_equations(
            self.equations,
            context,
            effect_outputs={"PowerIn", "EnergyConsumed"},
        )
        self.lastEquationOutputs = outputs
        if "EnergyConsumed" in outputs:
            demand = outputs["EnergyConsumed"]
        elif "PowerIn" in outputs:
            demand = outputs["PowerIn"] * dt
        else:
            demand = baseline_energy
        if demand < 0:
            raise RuntimeError(f"{self.name}: power demand cannot be negative")
        if before_total is not None:
            self.consumer.totalEnergyConsumed += demand - baseline_energy
        return demand

# -------------------------------------------------
# Power Manager (handles distribution)
# -------------------------------------------------
class PowerManager:
    """
    Manages power distribution from power system to all consumers.
    Tracks all power demands and manages battery charging/discharging.
    """
    def __init__(self, system, solarSystem, generationEquations=None):
        self.system = system
        self.solarSystem = solarSystem
        self.consumers = []  # List of power consumers
        self.powerGeneratedSeries = [] #Create an array to track how much power is generated at each time step
        self.totalDemandSeries = [] #Create an array to track how much power demand exists at each time step
        self.generationEquations = generationEquations or ""
        self.lastGenerationEquationOutputs = {}
        
        #These are simply variables that stores the latest demand and production numbers so that the logger can access them
        #Should not be used externally
        self.latestEnergyDemand = 0
        self.latestEnergyProduction = 0

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
            generation_context = _numeric_state(self.solarSystem)
            generation_context.update({
                "SimulationTime": float(self.system.now),
                "dt": float(dt),
                "powerOutput": float(self.solarSystem.currentPowerOutput),
                "PowerOut": energyGenerated / dt if dt else 0.0,
                "EnergyGenerated": energyGenerated,
            })
            generation_outputs = evaluate_equations(
                self.generationEquations,
                generation_context,
                effect_outputs={"PowerOut", "EnergyGenerated"},
            )
            self.lastGenerationEquationOutputs = generation_outputs
            if "EnergyGenerated" in generation_outputs:
                adjusted_generation = generation_outputs["EnergyGenerated"]
            elif "PowerOut" in generation_outputs:
                adjusted_generation = generation_outputs["PowerOut"] * dt
            else:
                adjusted_generation = energyGenerated
            if adjusted_generation < 0:
                raise RuntimeError("Solar_Power_System: generated energy cannot be negative")
            self.solarSystem.totalEnergyGenerated += adjusted_generation - energyGenerated
            energyGenerated = adjusted_generation
            
            # Calculate total demand
            totalDemand = 0
            for consumer in self.consumers:
                if hasattr(consumer, 'getCurrentPowerDemand'):
                    totalDemand += consumer.getCurrentPowerDemand(dt)
            
            # Manage power balance
            energyBalance = energyGenerated - totalDemand
            
            #Updated tracking variables
            self.latestEnergyDemand = totalDemand
            self.latestEnergyProduction = energyGenerated

            #Update internal tracking arrays
            self.powerGeneratedSeries.append(energyGenerated)
            self.totalDemandSeries.append(totalDemand)

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

    def getLoggingAttributes(self):
        attr = {
            "Name": "Power_Manager",
            "current_energy_demand":self.latestEnergyDemand,
            "current_energy_production": self.latestEnergyProduction,
            "generation_equation_outputs": self.lastGenerationEquationOutputs,
            "consumer_equation_outputs": {
                consumer.name: consumer.lastEquationOutputs
                for consumer in self.consumers
                if hasattr(consumer, "lastEquationOutputs") and consumer.lastEquationOutputs
            },
        }
        return attr
