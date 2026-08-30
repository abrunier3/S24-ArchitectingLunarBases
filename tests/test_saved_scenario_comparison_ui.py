import unittest
from pathlib import Path


class SavedScenarioComparisonUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (Path(__file__).resolve().parents[1] / "ScenarioIndex.html").read_text()

    def test_comparison_loads_persisted_des_outputs(self):
        self.assertIn("async function loadScenarioComparisonResults", self.html)
        self.assertIn("outputs/scenarios/${slug}/des_results.json", self.html)
        self.assertIn("await fetchRepositoryScenarios();", self.html)
        self.assertIn("savedScenarioComparisonSnapshots", self.html)

    def test_comparison_offers_only_the_two_views(self):
        self.assertIn("setSavedScenarioComparisonMode('moes')", self.html)
        self.assertIn("setSavedScenarioComparisonMode('history')", self.html)
        self.assertNotIn("toggleSavedScenarioComparisonSelection", self.html)
        self.assertNotIn("savedScenarioComparisonBaseline", self.html)
        self.assertNotIn("setSavedScenarioComparisonMetric", self.html)

    def test_comparison_supports_final_moes_and_time_histories(self):
        self.assertIn("renderScenarioComparisonMoes", self.html)
        self.assertIn("renderScenarioComparisonHistory", self.html)
        self.assertIn("Total_LOX_Produced_kg", self.html)
        self.assertIn("Total_LOX_Delivered_kg", self.html)
        self.assertIn("Primary resource output", self.html)
        self.assertIn("Regolith received", self.html)
        self.assertIn("Energy consumed", self.html)
        self.assertIn("grid-template-columns:repeat(auto-fit,minmax(300px,1fr))", self.html)
        self.assertIn("Object.entries(log)", self.html)


if __name__ == "__main__":
    unittest.main()
