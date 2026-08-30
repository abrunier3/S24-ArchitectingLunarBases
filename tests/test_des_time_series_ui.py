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

    def test_des_runs_are_correlated_and_stale_results_are_cleared(self):
        html = INDEX_PATH.read_text()

        self.assertIn("function resetDesResultsForRun", html)
        self.assertIn("request_id: requestId", html)
        self.assertIn("data.request_id !== requestId", html)
        self.assertIn("Ignoring stale results", html)

        workflow = (ROOT / ".github" / "workflows" / "run_des.yml").read_text()
        self.assertIn("request_id:", workflow)
        self.assertIn('result["request_id"] = request_id', workflow)

    def test_structured_config_reads_visible_des_controls(self):
        html = INDEX_PATH.read_text()

        self.assertIn("const sliderValues = getDesSliderValues();", html)
        self.assertIn("Number(sliderValues.Num_Regolith_Rovers", html)
        self.assertIn("Number(sliderValues.Num_LOX_Rovers", html)
        self.assertIn(
            "energy_kwh_per_km_per_kg: ignorePower ? 0 : Number(sliderValues.Rover_Energy_Consumption)",
            html,
        )
        self.assertIn("flat_speed_kph: Number(sliderValues.Rover_Flat_Speed)", html)
        self.assertIn("slope_speed_penalty_per_deg: Number(sliderValues.Rover_Slope_Speed_Penalty)", html)
        self.assertIn("processing_rate_kg_hr: Number(sliderValues.ISRU_Plant_Processing_Rate)", html)
        self.assertIn("dispatch_poll_dt_hr: getNumberInputValue('desRegolithPollDt', 0.1)", html)
        self.assertIn("lox_storage_energy_dt_hr: getNumberInputValue('desLoxStorageDt', 1)", html)


if __name__ == "__main__":
    unittest.main()
