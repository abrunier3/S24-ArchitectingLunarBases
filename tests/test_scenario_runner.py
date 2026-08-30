import unittest

from S24.DES_pipeline_version.scenario_runner import (
    _engine_mode,
    check_scenario_validity,
)


class ScenarioRunnerTests(unittest.TestCase):
    def test_inline_engine_mode_selects_generic(self):
        options = {"scenario_config": {"engine": {"mode": "generic"}}}
        self.assertEqual(_engine_mode(options), "generic")

    def test_default_engine_keeps_legacy_isru_validation(self):
        options = {
            "active_nodes": [
                "ISRUPlant",
                "RegolithRover",
                "LOXRover",
                "SolarPowerSystem",
                "LaunchLandingZone",
            ]
        }
        messages = check_scenario_validity(options, raiseError=False)
        self.assertFalse([message for message in messages if message.startswith("[ERROR]")])


if __name__ == "__main__":
    unittest.main()
