import json
import os
import tempfile
import unittest
from pathlib import Path

from S24.DES_pipeline_version.ISRU_DES_Model_V5_2_PV import run_scenario


class IsruRuntimeTests(unittest.TestCase):
    def test_neutral_source_power_boundary_runs_in_isru_controller(self):
        options = {
            "active_nodes": ["ISRUPlant", "RegolithRover"],
            "scenario_config": {
                "simulation": {"duration_hr": 0.01},
                "scenario_builder": {
                    "module_equations": {
                        "ISRUExcavation": (
                            "RegolithOut = RequestedRegolith\n"
                            "EnergyConsumed = 0\n"
                            "PowerOut = 0"
                        )
                    }
                },
            },
        }

        previous_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                run_scenario(options)
                results_written = Path("lunar_spaceport_results.json").exists()
        finally:
            os.chdir(previous_cwd)

        self.assertTrue(results_written)

    def test_reference_preset_equations_run_with_all_isru_systems(self):
        root = Path(__file__).resolve().parents[1]
        preset = json.loads(
            (root / "clean_database/scenarios/presets/ISRU.json").read_text()
        )
        options = {
            "active_nodes": [
                "HabitationModule",
                "ISRUPlant",
                "LaunchLandingZone",
                "LOXRover",
                "SolarPowerSystem",
                "RegolithRover",
            ],
            "scenario_config": {
                "simulation": {"duration_hr": 60.0},
                "routes": {
                    "use_sysml_distances": False,
                    "regolith_distance_km": 2.39,
                    "lox_distance_km": 1.9,
                },
                "power": {
                    "continuous_load_kw": {
                        "habitation": None,
                        "communications": None,
                        "landing_zone_utilities": None,
                    },
                    "landing_zone_chilling_kw_per_kg": None,
                    "spikes": {
                        "habitation": [],
                        "communications": [],
                        "landing_zone": [],
                    },
                    "module_models": preset["power_models"],
                },
                "scenario_builder": {
                    "module_equations": preset["scenario_logic"]["moduleEquations"],
                },
            },
        }

        previous_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                run_scenario(options)
                results_written = Path("lunar_spaceport_results.json").exists()
                log = json.loads(Path("lunar_spaceport_log.json").read_text())
        finally:
            os.chdir(previous_cwd)

        self.assertTrue(results_written)
        self.assertEqual(max(map(float, log)), 60.0)


if __name__ == "__main__":
    unittest.main()
