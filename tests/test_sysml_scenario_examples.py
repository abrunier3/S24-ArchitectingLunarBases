import json
import tempfile
import unittest
from pathlib import Path

from S24.DES_pipeline_version.generic_scenario import run_generic_scenario
from S24.sysml.main_api import sysml_to_json_transformer


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = (
    "Water_Transfer_Test",
    "Ice_Processing_Test",
    "Cargo_Relay_Test",
)
EXPECTED_FLOWS = {
    "Water_Transfer_Test": {"Water", "Power"},
    "Ice_Processing_Test": {"Ice", "Water", "Power"},
    "Cargo_Relay_Test": {"Cargo"},
}


class SysmlScenarioExampleTests(unittest.TestCase):
    def _build_options(self, scenario_name, asset_root):
        snapshot_path = ROOT / "clean_database/scenarios" / f"{scenario_name}.json"
        snapshot = json.loads(snapshot_path.read_text())
        self.assertEqual(snapshot_path.stem, snapshot["scenario_slug"])
        self.assertEqual(Path(snapshot["sysml_file"]).stem, snapshot["scenario_slug"])
        logic = snapshot["scenario_logic"]
        routes = []
        for route in logic["resourceRoutes"]:
            routes.append({
                "id": route["id"],
                "flow": route["flow"],
                "unit": "kg",
                "rover_type": route["rover_type"],
                "rover_id": route["rover_id"],
                "from": route["from"],
                "to": route["to"],
                "stops": route.get("stops", []),
                "distance_km": route["distance_km"],
            })

        sysml_path = ROOT / snapshot["sysml_file"]
        parsed = sysml_to_json_transformer(0, sysml_path.read_text())
        power_links = []
        for connection in parsed["connections"]:
            if connection["flow"] != "Power":
                continue
            power_links.append({
                "flow": "Power",
                "from_instances": [connection["from"]["part"]],
                "to_instances": [connection["to"]["part"]],
            })

        for part in parsed["parts"]:
            (asset_root / f"{part['name']}.json").write_text(json.dumps(part))

        duration = float(snapshot["des_form"]["desSimDuration"])
        capacity = float(snapshot["des_form"]["desRoverCapacity"])
        return {
            "active_nodes": snapshot["active_nodes"],
            "scenario_config": {
                "engine": {"mode": "generic", "schema_version": 1},
                "scenario": {"json_asset_root": str(asset_root)},
                "simulation": {"duration_hr": duration},
                "rovers": {
                    "max_capacity_kg": capacity,
                    "travel_time_hr_per_km": float(snapshot["des_form"]["desRoverTravel"]),
                    "energy_kwh_per_km_per_kg": float(snapshot["des_form"]["desRoverEnergy"]),
                },
                "power": {"management_dt_hr": 0.25, "module_models": {}},
                "scenario_builder": {
                    "instances": [
                        {"id": module_id, "type": module_id, "placed": True}
                        for module_id in snapshot["placements"]
                    ],
                    "resource_routes": routes,
                    "sysml_interfaces": power_links,
                    "module_equations": logic["moduleEquations"],
                },
            },
        }, parsed

    def test_example_sysml_models_parse_and_run(self):
        for scenario_name in EXAMPLES:
            with self.subTest(scenario=scenario_name), tempfile.TemporaryDirectory() as tmp:
                temp_root = Path(tmp)
                asset_root = temp_root / "assets"
                asset_root.mkdir()
                options, parsed = self._build_options(scenario_name, asset_root)

                self.assertFalse(parsed["metadata"]["validation_errors"])
                self.assertTrue(all(connection["flow"] for connection in parsed["connections"]))
                self.assertEqual(
                    {connection["flow"] for connection in parsed["connections"]},
                    EXPECTED_FLOWS[scenario_name],
                )

                result = run_generic_scenario(
                    options,
                    asset_root=asset_root,
                    results_path=temp_root / "results.json",
                    log_path=temp_root / "log.json",
                )
                self.assertEqual(result["Engine"], "GenericScenario")
                self.assertGreater(
                    result["MoEs"]["Total_Resource_Delivered_To_Terminals"], 0
                )


if __name__ == "__main__":
    unittest.main()
