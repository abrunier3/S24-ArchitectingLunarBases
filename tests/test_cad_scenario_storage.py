import unittest
from pathlib import Path

from S24.cad.paths import scenario_slug_from_cad_path
from S24.sysml.cad_metadata_updater import _cad_path_candidates


class CadScenarioStorageTests(unittest.TestCase):
    def test_converter_extracts_scenario_from_scoped_cad_path(self):
        path = "clean_database/cad_models/ISRU_Missionjjj/LOXRover/LOXRover.step"
        self.assertEqual(scenario_slug_from_cad_path(path), "ISRU_Missionjjj")

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
        self.assertIn("function getCadCatalogGroups", html)
        self.assertIn("clean_database/cad_models/${scenarioSlug}/${moduleName}", html)
        self.assertIn("CAD library: clean_database/cad_models", html)
        self.assertIn("This scenario now owns its CAD and preview", html)
        self.assertIn("cadImportedFromScenario", html)

    def test_step_three_remembers_catalog_choices_and_can_publish_one_cad(self):
        html = (Path(__file__).resolve().parents[1] / "ScenarioIndex.html").read_text()

        self.assertIn("function rememberCadReuseSelection", html)
        self.assertIn("pendingCadCatalogPath", html)
        self.assertIn("option.value = candidate.cadPath", html)
        self.assertIn("function publishCurrentCad", html)
        self.assertIn("Upload &amp; Publish this CAD", html)

    def test_new_rover_controls_are_not_sent_as_undeclared_workflow_inputs(self):
        html = (Path(__file__).resolve().parents[1] / "ScenarioIndex.html").read_text()

        self.assertIn("function getDesWorkflowSliderInputs", html)
        self.assertIn("...workflowSliderInputs", html)
        self.assertIn("Rover_Travel_Time: String(1 / flatSpeedKph)", html)

    def test_new_isru_scenario_seeds_its_reference_cads(self):
        html = (Path(__file__).resolve().parents[1] / "ScenarioIndex.html").read_text()

        self.assertIn("const ISRU_REFERENCE_CAD_PATHS", html)
        self.assertIn("async function seedIsruReferenceCad", html)
        self.assertIn("await seedIsruReferenceCad({slug, preset});", html)
        self.assertIn("clean_database/cad_models/${slug}/${moduleName}/${fileName}", html)

    def test_step_axis_override_survives_reselecting_a_module(self):
        html = (Path(__file__).resolve().parents[1] / "ScenarioIndex.html").read_text()

        self.assertIn("cadSourceUpAxisOverride: true", html)
        self.assertIn("!existing.cadSourceUpAxisOverride", html)
        self.assertIn("cadSourceUpAxisOverride: Boolean(saved.cadSourceUpAxisOverride)", html)

    def test_usd_stage_axis_overrides_stale_scenario_axis_metadata(self):
        html = (Path(__file__).resolve().parents[1] / "ScenarioIndex.html").read_text()
        scene_builder = (
            Path(__file__).resolve().parents[1] / "S24/usd/scene_builder.py"
        ).read_text()

        self.assertIn("const sourceUpAxis = isSourceAxisCadMeta(data)", html)
        self.assertIn("authored_up_axis=up_axis", scene_builder)
        self.assertIn("A USD's stage metadata is authoritative.", scene_builder)
        self.assertIn("def _stage_has_authored_orientation", scene_builder)
        self.assertIn("has_authored_orientation", scene_builder)

    def test_source_axis_choice_rebuilds_raw_cad_and_is_not_reapplied_in_scene(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "ScenarioIndex.html").read_text()
        workflow = (root / ".github/workflows/convert_cad.yml").read_text()
        converter = (root / "S24/cad/convert_workflow.py").read_text()
        scene_builder = (root / "S24/usd/scene_builder.py").read_text()
        submission = (root / "S24/usd/model_submission.py").read_text()

        self.assertIn("async function setCadSourceUpAxis", html)
        self.assertIn("function getCadFileForSave", html)
        self.assertIn("cached.cadSourceFile || metadata.cadSourceFile", html)
        self.assertIn("data.source_cad_path || data.source_metadata?.source_file", html)
        self.assertIn("data.source_metadata?.file_name", html)
        self.assertIn("part.metadata?.cadSourceFile", html)
        self.assertIn("function getRawCadAxisSource", html)
        self.assertIn("Copying the raw CAD into this scenario", html)
        self.assertIn("Reorienting ${moduleName} as ${normalized}-up", html)
        self.assertIn("Rebuilding USD as ${normalized}-up", html)
        self.assertIn("data-cad-axis-status=\"${moduleName}\"", html)
        self.assertIn("source_up_axis: normalizeUpAxis(sourceUpAxis, 'Z')", html)
        self.assertIn("source_up_axis:", workflow)
        self.assertIn('"source_up_axis": _normalise_up_axis', converter)
        self.assertIn("def _is_baked_cad_conversion", scene_builder)
        self.assertIn("if orientation_is_baked:", scene_builder)
        self.assertIn("_source_front_yaw(metadata, authored_up_axis=up_axis)", scene_builder)
        self.assertIn("Preserve a USD's authored upright orientation", scene_builder)
        self.assertIn("def _find_scenario_cad_file", submission)

    def test_front_axis_is_persisted_before_des_and_cannot_match_up_axis(self):
        html = (Path(__file__).resolve().parents[1] / "ScenarioIndex.html").read_text()

        self.assertIn("function isCompatibleCadFrontAxis", html)
        self.assertIn("function getCadDetectedUpAxis", html)
        self.assertIn("cadAxisBase(axis) !== getCadDetectedUpAxis(moduleName)", html)
        self.assertIn("const cadAxisSavePromises = new Map()", html)
        self.assertIn("async function waitForCadAxisSaves", html)
        self.assertIn("await waitForCadAxisSaves()", html)
        self.assertIn("Omniverse placement yaw", html)

    def test_preview_uses_generated_usd_axes_not_raw_cad_axes(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "ScenarioIndex.html").read_text()
        scene_builder = (root / "S24/usd/scene_builder.py").read_text()

        self.assertIn("USD up: ${detectedUpAxis} (detected)", html)
        self.assertIn("Raw CAD up (rebuild)", html)
        self.assertIn("USD front", html)
        self.assertIn("const selectedUp = getCadDetectedUpAxis(moduleName)", html)
        self.assertIn("authored_up_axis or metadata.get(\"cadSourceUpAxis\")", scene_builder)

    def test_glb_preview_converts_generated_z_up_usd_to_y_up(self):
        converter = (
            Path(__file__).resolve().parents[1] / "S24/cad/convert_workflow.py"
        ).read_text()

        self.assertIn('if str(up_axis).upper() == "Z"', converter)
        self.assertIn("GLB viewers are Y-up", converter)


if __name__ == "__main__":
    unittest.main()
