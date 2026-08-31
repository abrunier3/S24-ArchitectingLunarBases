import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "extensions/lsp1.pipeline/lsp1_pipeline/manifest_builder.py"
EXTENSION_PATH = ROOT / "extensions/lsp1.pipeline/lsp1_pipeline/extension.py"
SPEC = importlib.util.spec_from_file_location("manifest_builder", MODULE_PATH)
manifest_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest_builder)


class _FlatTerrainSampler:
    def sample_height(self, x, y):
        return x + y


class OmniverseManifestTests(unittest.TestCase):
    def test_route_diagnostics_include_terrain_projected_original_waypoints(self):
        diagnostics = manifest_builder._build_terrain_route_diagnostics(
            system_json={
                "urban_planning": {
                    "routes": [{"key": "regolith_route", "flow": "Regolith"}],
                    "route_geometry": {
                        "regolith_route": {
                            "flow": "Regolith",
                            "waypoints_m": [[0, 0], [10, 0]],
                        },
                        "ISRUPlantToPropellantDepot_LOX": {
                            "flow": "LOX",
                            "waypoints_m": [[10, 0], [20, 0]],
                        }
                    },
                }
            },
            sampler=_FlatTerrainSampler(),
        )

        route = diagnostics["routes"]["regolith_route"]
        self.assertEqual(route["original_waypoints_m"], [[0.0, 0.0], [10.0, 0.0]])
        self.assertEqual(route["terrain_waypoints_m"], [[0.0, 0.0, 0.0], [10.0, 0.0, 10.0]])
        self.assertTrue(route["visible_in_scene"])
        self.assertFalse(
            diagnostics["routes"]["ISRUPlantToPropellantDepot_LOX"]["visible_in_scene"]
        )

    def test_overview_camera_uses_a_non_parallel_up_axis_and_follow_respects_selection(self):
        extension_source = EXTENSION_PATH.read_text()

        self.assertIn("up=(0.0, 1.0, 0.0)", extension_source)
        self.assertIn("Gf.Vec3d(*up)", extension_source)
        self.assertIn("if selected in active:", extension_source)
        self.assertIn("if start_time <= des_time < end_time:", extension_source)

    def test_fixed_modules_receive_a_terrain_foundation_but_rovers_do_not(self):
        terrain_plane = {"max_clearance_m": 3.054}
        footprint = {"size_m": {"length": 43.301, "width": 50.0}}
        fixed = manifest_builder._module_terrain_foundation(
            part={"dimensions": {"size_m": footprint["size_m"]}},
            source_name="LaunchLandingZone",
            footprint=footprint,
            terrain_plane=terrain_plane,
        )
        rover = manifest_builder._module_terrain_foundation(
            part={"dimensions": {"size_m": {"length": 5.0, "width": 3.0}}},
            source_name="RegolithRover",
            footprint=None,
            terrain_plane=terrain_plane,
        )
        extension_source = EXTENSION_PATH.read_text()

        self.assertTrue(fixed["required"])
        self.assertEqual(fixed["terrain_gap_m"], 3.054)
        self.assertEqual(fixed["size_m"]["height"], 3.304)
        self.assertFalse(rover["required"])
        self.assertIn("def _ensure_module_terrain_foundations", extension_source)
        self.assertIn('f"{prim_path}/TerrainFoundation"', extension_source)


if __name__ == "__main__":
    unittest.main()
