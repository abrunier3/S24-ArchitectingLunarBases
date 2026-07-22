import unittest

from S24.DES_pipeline_version.LunarRover import LunarRover


class _Environment:
    now = 0.0


class RoverSlopeSpeedTests(unittest.TestCase):
    def test_slope_reduces_speed_and_increases_travel_time(self):
        rover = LunarRover(
            _Environment(),
            "Test rover",
            "cargo",
            {
                "maxCapacity": 4000.0,
                "energyPerKmPerKg": 0.00034,
                "batteryCapacity": 100.0,
                "batteryCharge": 100.0,
                "totalDistanceTraveled": 0.0,
                "totalEnergyConsumed": 0.0,
                "hoursPerKm": 5.0,
            },
        )
        rover.flatSpeedKph = 1.0
        rover.slopeSpeedPenaltyPerDeg = 0.05

        flat = rover.evaluateTransport("Regolith", 4000.0, 1.0, slope_deg=0.0)
        inclined = rover.evaluateTransport("Regolith", 4000.0, 1.0, slope_deg=10.0)

        self.assertEqual(flat["TravelTime"], 1.0)
        self.assertEqual(inclined["TravelTime"], 1.5)
        self.assertEqual(flat["EnergyConsumed"], inclined["EnergyConsumed"])


if __name__ == "__main__":
    unittest.main()
