import unittest

import simpy

from S24.DES_pipeline_version.PowerManager import PowerManager, PowerModelConsumer


class _System:
    now = 0.0


class _Consumer:
    def __init__(self):
        self.system = _System()
        self.name = "TestConsumer"
        self.totalEnergyConsumed = 0.0
        self.loxStored = 10.0

    def getCurrentPowerDemand(self, dt):
        return 0.0


class PowerModelTests(unittest.TestCase):
    def test_one_time_spike_is_delivered_once(self):
        consumer = _Consumer()
        model = PowerModelConsumer(consumer, {
            "mode": "average",
            "average_kw": 2.0,
            "spike_energy_kwh": 10.0,
            "spike_time_hr": 3.0,
        })

        consumer.system.now = 2.0
        self.assertEqual(model.getCurrentPowerDemand(1.0), 2.0)
        consumer.system.now = 3.0
        self.assertEqual(model.getCurrentPowerDemand(1.0), 12.0)
        consumer.system.now = 4.0
        self.assertEqual(model.getCurrentPowerDemand(1.0), 2.0)

    def test_equation_can_use_canonical_lox_stored_name(self):
        consumer = _Consumer()
        model = PowerModelConsumer(consumer, {
            "mode": "equation",
            "equation": "PowerIn = 3 + LOXStored * 0.31",
        })

        self.assertAlmostEqual(model.getCurrentPowerDemand(1.0), 6.1)

    def test_generation_equation_can_use_sysml_power_output_name(self):
        class Solar:
            def __init__(self, system):
                self.system = system
                self.currentPowerOutput = 100.0
                self.totalEnergyGenerated = 0.0
                self.batteryCharge = 0.0

            def generatePower(self, duration):
                energy = self.currentPowerOutput * duration
                self.totalEnergyGenerated += energy
                return energy

            def chargeBattery(self, energy):
                self.batteryCharge += energy
                return energy

            def dischargeBattery(self, energy):
                raise AssertionError("Battery discharge should not be required")

        system = simpy.Environment()
        solar = Solar(system)
        manager = PowerManager(
            system,
            solar,
            generationEquations="PowerOut = powerOutput",
        )
        system.process(manager.managePower(dt=1.0))
        system.run(until=1.1)

        self.assertEqual(manager.latestEnergyProduction, 100.0)


if __name__ == "__main__":
    unittest.main()
