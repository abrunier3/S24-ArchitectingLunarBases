import unittest

from S24.DES_pipeline_version.PowerManager import PowerModelConsumer


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


if __name__ == "__main__":
    unittest.main()
