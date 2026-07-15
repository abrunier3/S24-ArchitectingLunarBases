import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "ScenarioIndex.html"


class DesTimeSeriesUiTests(unittest.TestCase):
    def test_results_panel_contains_time_history_charts(self):
        html = INDEX_PATH.read_text()

        self.assertIn('id="desTimeSeriesSection"', html)
        self.assertIn('id="desTimeSeriesWrap"', html)
        self.assertIn("function renderDesTimeSeries", html)
        self.assertIn("ISRU material flow", html)
        self.assertIn("Power balance", html)
        self.assertIn("Cumulative energy", html)
        self.assertIn("Rover battery state", html)
        self.assertIn("Rover transport activity", html)


if __name__ == "__main__":
    unittest.main()
