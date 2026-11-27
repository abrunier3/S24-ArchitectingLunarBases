import importlib.util
import json
from pathlib import Path
import unittest

from S24.DES_pipeline_version.batch_results import collect_result_fields
from S24.DES_pipeline_version.scenario_runner import run_scenario


ROOT = Path(__file__).resolve().parents[1]
module_path = ROOT / "extensions/lsp1.pipeline/lsp1_pipeline/manifest_builder.py"
spec = importlib.util.spec_from_file_location("batch_test_manifest_builder", module_path)
manifest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest)


class BatchIntegrationTests(unittest.TestCase):
    def test_workflow_output_uses_native_lot_and_route_times(self):
        config = json.loads((ROOT / "paper_scitech/COMPASS/reference.json").read_text())
        config["simulation"]["duration_hr"] = 6
        options = {"scenario_config": config}
        result = run_scenario(options)
        fields = collect_result_fields(options, result)
        self.assertEqual(fields["results"]["Engine"], "BatchISRU")
        summary = fields["results"]["MoEs"]
        tank = result["summary"]["liquid_stocks_kg"]["LanderTank"]
        self.assertAlmostEqual(summary["Total_LOX_Produced_kg"], tank)
        self.assertAlmostEqual(summary["Common_Tank_LOX_kg"], tank)
        self.assertEqual(summary["Total_LOX_Delivered_kg"], 0)
        self.assertEqual(fields["log"]["6.0"]["LanderTank"]["LOX_Stored"], tank)

        for route in fields["results"]["Scenario_Config"]["scenario_builder"]["resource_routes"]:
            route["route_name"] = route["id"]
        movements, plants, warnings = manifest._timed_operations(
            fields, {"RegolithRover_1_Regolith", "RegolithRover_2_Regolith"}
        )
        self.assertTrue(warnings)
        self.assertEqual(len(movements), 6)
        self.assertEqual(len(plants["ISRUPlant_1"]), 4)
        self.assertAlmostEqual(movements[0]["start_time"], .05)
        self.assertAlmostEqual(movements[0]["end_time"], .15)
        self.assertAlmostEqual(plants["ISRUPlant_1"][0]["end_time"], 100 / 60)
        self.assertTrue(any(movement["reverse"] for movement in movements))
        self.assertTrue(all("Regolith" in movement["route_name"] for movement in movements))
