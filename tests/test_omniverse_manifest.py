import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "extensions/lsp1.pipeline/lsp1_pipeline/manifest_builder.py"
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
                        }
                    },
                }
            },
            sampler=_FlatTerrainSampler(),
        )

        route = diagnostics["routes"]["regolith_route"]
        self.assertEqual(route["original_waypoints_m"], [[0.0, 0.0], [10.0, 0.0]])
        self.assertEqual(route["terrain_waypoints_m"], [[0.0, 0.0, 0.0], [10.0, 0.0, 10.0]])


if __name__ == "__main__":
    unittest.main()
