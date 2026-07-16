import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRESET_PATH = ROOT / "clean_database/scenarios/presets/ISRU.json"
INDEX_PATH = ROOT / "ScenarioIndex.html"


class IsruPresetTests(unittest.TestCase):
    def test_isru_preset_is_complete_and_loaded_by_the_ui(self):
        preset = json.loads(PRESET_PATH.read_text())
        html = INDEX_PATH.read_text()

        self.assertEqual(preset["mode"], "isru")
        self.assertEqual(
            set(preset["active_nodes"]),
            {
                "HabitationModule",
                "ISRUPlant",
                "LaunchLandingZone",
                "PropellantDepot",
                "LOXRover",
                "SolarPowerSystem",
                "RegolithRover",
                "ISRUExcavation",
            },
        )
        self.assertEqual(
            set(preset["scenario_logic"]["moduleEquations"]),
            set(preset["active_nodes"]),
        )
        self.assertEqual(
            preset["scenario_logic"]["roverCounts"],
            {"regolith": 1, "lox": 1},
        )
        self.assertEqual(
            preset["scenario_logic"]["roverPayloadsKg"],
            {"regolith": 4000, "lox": 4000},
        )

        required_controls = {
            "desRoverCount",
            "desLoxRoverCount",
            "desPlantCount",
            "desRoverEnergy",
            "desRoverTravel",
            "desProcessRate",
            "desLoxThresh",
            "desSimDuration",
            "desPlantBatch",
            "desPlantInputCapacity",
            "desLoxPollDt",
            "desLoxStorageCoeff",
            "desPowerDt",
            "desSolarPowerOutput",
            "desSolarBatteryCapacity",
            "desSolarInitialCharge",
        }
        self.assertTrue(required_controls.issubset(preset["des_form"]))
        for control_id in required_controls:
            self.assertIn(f'id="{control_id}"', html)

        self.assertIn(
            "clean_database/scenarios/presets/ISRU.json",
            html,
        )
        self.assertIn("await loadScenarioPreset(ISRU_PRESET_PATH", html)
        self.assertEqual(
            preset["power_models"]["LaunchLandingZone"]["equation"],
            "PowerIn = 3 + LOXStored * 0.31",
        )
        self.assertEqual(
            preset["power_models"]["HabitationModule"]["spike_energy_kwh"],
            20,
        )


if __name__ == "__main__":
    unittest.main()
