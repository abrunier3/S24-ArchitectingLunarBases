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
        self.assertEqual(
            preset["scenario_logic"]["moduleClassOverrides"],
            {"LOXRover": "Transporter", "RegolithRover": "Transporter"},
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

    def test_isru_graph_classification_uses_raw_connections_and_port_directions(self):
        html = INDEX_PATH.read_text()

        self.assertIn(
            "const graphData = window._currentGraphData || window._lastGraphData",
            html,
        )
        self.assertIn("function resolveConnectionPort(value, ownerName)", html)
        self.assertIn(
            "connectionPortSourceScore(toPort) > connectionPortSourceScore(fromPort)",
            html,
        )
        self.assertIn("function getModulePortFlowDirections(moduleId)", html)
        self.assertIn("function isAssignedScenarioTransporter(moduleId)", html)
        self.assertNotIn("function getModuleAttributeMap(moduleId)", html)
        self.assertNotIn("function hasStorageAttributes(moduleId)", html)
        self.assertNotIn("function hasTransporterAttributes(moduleId)", html)
        self.assertNotIn("function hasPowerGenerationAttributes(moduleId)", html)


if __name__ == "__main__":
    unittest.main()
