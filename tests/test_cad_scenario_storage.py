import unittest
from pathlib import Path

from S24.cad.paths import scenario_slug_from_cad_path
from S24.sysml.cad_metadata_updater import _cad_path_candidates


class CadScenarioStorageTests(unittest.TestCase):
    def test_converter_extracts_scenario_from_scoped_cad_path(self):
        path = "clean_database/cad_models/ISRU_petit/LOXRover/LOXRover.step"
        self.assertEqual(scenario_slug_from_cad_path(path), "ISRU_petit")

    def test_converter_keeps_legacy_cad_in_default_scenario(self):
        path = "clean_database/cad_models/LOXRover/LOXRover.step"
        self.assertEqual(scenario_slug_from_cad_path(path), "ECLIPSE_Project")

    def test_asset_geometry_ref_precedes_legacy_cad_folder(self):
        repo_root = Path.cwd()
        candidates = _cad_path_candidates(
            module_name="LOXRover",
            preview_meta={"usd_path": "clean_database/cad_models/Other/LOXRover/LOXRover.usdc"},
            metadata={"geometryRef": "clean_database/cad_models/Current/LOXRover/LOXRover.usdc"},
            repo_root=repo_root,
        )
        self.assertEqual(
            candidates[:2],
            [
                "clean_database/cad_models/Current/LOXRover/LOXRover.usdc",
                "clean_database/cad_models/Other/LOXRover/LOXRover.usdc",
            ],
        )

    def test_step_three_reuses_a_copied_scenario_scoped_cad(self):
        html = (Path(__file__).resolve().parents[1] / "ScenarioIndex.html").read_text()

        self.assertIn("function refreshCadReuseOptions", html)
        self.assertIn("function loadCadFromScenario", html)
        self.assertIn("clean_database/cad_models/${scenarioSlug}/${moduleName}", html)
        self.assertIn("This scenario now owns its copy", html)
        self.assertIn("cadImportedFromScenario", html)

    def test_new_rover_controls_are_not_sent_as_undeclared_workflow_inputs(self):
        html = (Path(__file__).resolve().parents[1] / "ScenarioIndex.html").read_text()

        self.assertIn("function getDesWorkflowSliderInputs", html)
        self.assertIn("...workflowSliderInputs", html)
        self.assertIn("Rover_Travel_Time: String(1 / flatSpeedKph)", html)


if __name__ == "__main__":
    unittest.main()
