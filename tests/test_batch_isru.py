import json
import unittest
from pathlib import Path

from S24.DES_pipeline_version.scenario_runner import check_scenario_validity, run_scenario


REFERENCE_PATH = Path(__file__).resolve().parents[1] / "paper_scitech/COMPASS/reference.json"


class BatchOperationsTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(REFERENCE_PATH.read_text())

    def run_model(self, config=None):
        return run_scenario({"scenario_config": config or self.config})

    def test_preflight_requires_the_assigned_route(self):
        options = {"scenario_config": self.config}
        self.assertEqual(check_scenario_validity(options), [])
        self.config["scenario_builder"]["resource_routes"].pop(0)
        self.assertTrue(check_scenario_validity(options, raiseError=False)[0].startswith("[ERROR]"))

    def test_gas_and_liquid_are_released_at_operation_completion(self):
        self.config["simulation"] = {"duration_hr": 2, "sample_hr": 1 / 60}
        result = self.run_model()
        first_batch = min(event["time_hr"] for event in result["events"]
                          if event["event"] == "batch_completed")
        first_liquid = next(event for event in result["events"]
                            if event["event"] == "liquid_available")
        self.assertAlmostEqual(first_batch, 100 / 60)
        self.assertAlmostEqual(first_liquid["time_hr"] - first_batch, first_liquid["mass_kg"] / 1.30)
        for sample in result["time_series"]:
            if sample["time_hr"] < first_batch:
                self.assertEqual(sum(line["oxygen_kg"] for line in sample["lines"].values()), 0)
                self.assertEqual(sample["liquid_stocks_kg"]["LanderTank"], 0)
        active = None
        for event in result["events"]:
            if event["event"] == "liquefaction_started":
                self.assertIsNone(active)
                active = event
            if event["event"] == "liquid_available":
                self.assertIsNotNone(active)
                self.assertAlmostEqual(event["time_hr"] - active["time_hr"], event["mass_kg"] / 1.30)
                active = None

    def test_calendar_missions_are_serial_and_respect_travel_and_handling(self):
        self.config["simulation"]["duration_hr"] = 120
        result = self.run_model()
        for name in ("RegolithRover_1", "RegolithRover_2"):
            active = None
            started = {}
            seen = set()
            position = "ISRUExcavation"
            for event in (event for event in result["events"] if event["actor"] == name):
                if event["event"] == "phase_start":
                    self.assertIsNone(active)
                    if event["phase"].startswith("drive"):
                        self.assertEqual(event["origin"], position)
                    active = event
                elif event["event"] == "phase_end":
                    self.assertEqual(active["phase"], event["phase"])
                    self.assertAlmostEqual(event["time_hr"] - active["time_hr"], active["duration_hr"])
                    if event["phase"].startswith("drive"):
                        self.assertAlmostEqual(active["duration_hr"], active["distance_km"])
                        position = event["destination"]
                    active = None
                elif event["event"] == "mission_started":
                    started[event["mission"]] = event["time_hr"]
                elif event["event"] == "mission_completed":
                    duration = 20 if event["mission"] == "regolith" else 17
                    self.assertAlmostEqual((event["time_hr"] - started[event["mission"]]) * 60, duration)
                    seen.add(event["mission"])
            self.assertSetEqual(seen, {"regolith", "residue"})
            charges = [event for event in result["events"]
                       if event["actor"] == name and event.get("phase") == "charge"]
            self.assertEqual(len(charges), 2)
            self.assertAlmostEqual(charges[1]["time_hr"] - charges[0]["time_hr"], 10)

    def test_reference_conserves_material_and_energy_and_is_reproducible(self):
        result = self.run_model()
        self.assertEqual(result, self.run_model())
        summary = result["summary"]
        self.assertLess(result["max_event_mass_residual_kg"], 1e-8)
        self.assertGreater(sum(line["completed"] for line in summary["lines"].values()), 0)
        budget = self.config["batch_operations"]["power"]
        energy = summary["energy"]
        self.assertAlmostEqual(energy["electric_available_kwh"], 168 * budget["electric_available_kw"])
        self.assertAlmostEqual(energy["electric_unserved_kwh"], 0)
        self.assertAlmostEqual(energy["electric_available_kwh"],
                               energy["electric_core_kwh"] + energy["electric_charging_kwh"]
                               + energy["electric_curtailed_kwh"])
        self.assertAlmostEqual(energy["thermal_to_reactors_kwh"], 11.1 * sum(
            event["duration_hr"] for event in result["events"] if event["event"] == "batch_started"
        ))
        for rover in summary["vehicles"].values():
            self.assertAlmostEqual(rover["battery_kwh"],
                                   1 + rover["battery_added_kwh"] - rover["traction_and_handling_kwh"])
            self.assertGreaterEqual(rover["battery_kwh"], .2 - 1e-9)

    def test_feed_starvation_is_recoverable_and_laws_can_override_the_defaults(self):
        self.config["simulation"]["duration_hr"] = 12
        for line in self.config["batch_operations"]["lines"]:
            line["initial_feed_kg"] = 0
        self.config["scenario_builder"]["module_equations"]["ISRUPlant"] = (
            "OxygenOut = 0.2 * RegolithIn\nProcessingTime = 0.5"
        )
        result = self.run_model()
        for line in result["summary"]["lines"].values():
            self.assertGreater(line["missed"], 0)
            self.assertGreater(line["completed"], 0)
            self.assertAlmostEqual(line["oxygen_kg"] / line["processed_kg"], .2)

    def test_lox_stays_in_transit_if_the_depot_has_no_room(self):
        self.config["simulation"]["duration_hr"] = 10
        operations = self.config["batch_operations"]
        operations["lines"] = [operations["lines"][0]]
        line = operations["lines"][0]
        operations["depots_kg"] = {"Depot": .3}
        line["lox_rover"] = {
            "id": "Courier", "payload_kg": .2, "dispatch_kg": .2,
            "speed_kph": 1, "poll_hr": .02, "load_hr": .1, "unload_hr": .2,
        }
        self.config["scenario_builder"]["resource_routes"].append({
            "rover_id": "Courier", "flow": "LOX", "distance_km": .5,
            "from": "LanderTank", "to": "Depot",
        })
        result = self.run_model()
        events = result["events"]
        loaded = next(event for event in events
                      if event["actor"] == "Courier" and event["event"] == "phase_start")
        delivered = next(event for event in events
                         if event["actor"] == "Courier" and event["event"] == "material_delivered")
        self.assertAlmostEqual(delivered["time_hr"] - loaded["time_hr"], .8)
        self.assertAlmostEqual(result["summary"]["depots_kg"]["Depot"], .2)
        self.assertAlmostEqual(result["summary"]["mass_in_transit_kg"]["lox"], .2)
        self.assertLess(result["max_event_mass_residual_kg"], 1e-8)


if __name__ == "__main__":
    unittest.main()
