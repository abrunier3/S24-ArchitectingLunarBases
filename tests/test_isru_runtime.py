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


if __name__ == "__main__":
    unittest.main()
