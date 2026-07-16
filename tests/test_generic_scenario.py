import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from S24.DES_pipeline_version.generic_scenario import (
    compile_scenario,
    run_generic_scenario,
    validate_generic_scenario,
)


class GenericScenarioTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.assets = self.root / "assets"
        self.assets.mkdir()
        self._write_asset("WaterExtractor", {"productionRate": 10.0})
        self._write_asset(
            "WaterProcessor",
            {"conversionEfficiency": 0.8, "processingRate": 10.0},
        )
        self._write_asset("WaterTank", {})
        self._write_asset("SolarArray", {"powerOutput": 100.0})
        self._write_asset(
            "WaterRover",
            {"hoursPerKm": 1.0, "energyPerKmPerKg": 0.01},
        )
        self._write_asset(
            "ProductRover",
            {"hoursPerKm": 1.0, "energyPerKmPerKg": 0.01},
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_asset(self, name, attributes):
        with (self.assets / f"{name}.json").open("w") as handle:
            json.dump({"name": name, "attributes": attributes, "ports": []}, handle)

    def _options(self):
        module_equations = {
            "WaterExtractor": (
                "WaterOut = min(RequestedWater, productionRate)\n"
                "ProcessingTime = WaterOut / productionRate\n"
                "EnergyConsumed = WaterOut * 0.1\n"
                "PowerIn = 1"
            ),
            "WaterProcessor": (
                "ProductOut = WaterIn * conversionEfficiency\n"
                "ProcessingTime = WaterIn / processingRate\n"
                "EnergyConsumed = WaterIn * 0.2\n"
                "PowerIn = 2"
            ),
            "WaterTank": "ProductStored = ProductStored + ProductIn\nPowerIn = 0",
            "SolarArray": "PowerOut = powerOutput",
            "WaterRover": (
                "WaterOut = min(WaterIn, RoverCapacity)\n"
                "TravelTime = Distance * hoursPerKm\n"
                "EnergyConsumed = Distance * CargoMass * energyPerKmPerKg"
            ),
            "ProductRover": (
                "ProductOut = min(ProductIn, RoverCapacity)\n"
                "TravelTime = Distance * hoursPerKm\n"
                "EnergyConsumed = Distance * CargoMass * energyPerKmPerKg"
            ),
        }
        scenario = {
            "engine": {"mode": "generic", "schema_version": 1},
            "simulation": {"duration_hr": 8.0},
            "rovers": {
                "max_capacity_kg": 10.0,
                "travel_time_hr_per_km": 1.0,
                "energy_kwh_per_km_per_kg": 0.01,
            },
            "power": {"management_dt_hr": 0.25, "module_models": {}},
            "scenario_builder": {
                "instances": [
                    {"id": "WaterExtractor", "type": "WaterExtractor", "placed": True},
                    {"id": "WaterProcessor", "type": "WaterProcessor", "placed": True},
                    {"id": "WaterTank", "type": "WaterTank", "placed": True},
                    {"id": "SolarArray", "type": "SolarArray", "placed": True},
                ],
                "resource_routes": [
                    {
                        "id": "raw_water_route",
                        "flow": "Water",
                        "unit": "kg",
                        "rover_type": "WaterRover",
                        "rover_id": "WaterRover",
                        "from": "WaterExtractor",
                        "to": "WaterProcessor",
                        "distance_km": 0.1,
                    },
                    {
                        "id": "product_route",
                        "flow": "Product",
                        "unit": "kg",
                        "rover_type": "ProductRover",
                        "rover_id": "ProductRover",
                        "from": "WaterProcessor",
                        "to": "WaterTank",
                        "distance_km": 0.1,
                    },
                ],
                "sysml_interfaces": [
                    {
                        "flow": "Power",
                        "from_instances": ["SolarArray"],
                        "to_instances": [
                            "WaterExtractor",
                            "WaterProcessor",
                            "WaterTank",
                        ],
                    }
                ],
                "module_equations": module_equations,
            },
        }
        return {
            "active_nodes": [
                "WaterExtractor",
                "WaterProcessor",
                "WaterTank",
                "SolarArray",
                "WaterRover",
                "ProductRover",
            ],
            "scenario_config": scenario,
        }

    def test_non_isru_scenario_compiles_and_runs(self):
        options = self._options()
        messages = validate_generic_scenario(
            options, raise_error=False, asset_root=self.assets
        )
        self.assertFalse([message for message in messages if message.startswith("[ERROR]")])

        result = run_generic_scenario(
            options,
            asset_root=self.assets,
            results_path=self.root / "results.json",
            log_path=self.root / "log.json",
        )

        self.assertEqual(result["Engine"], "GenericScenario")
        self.assertGreater(
            result["Resource_Flows"]["Product"]["Delivered_To_Terminal"], 0
        )
        self.assertGreater(result["Modules"]["WaterProcessor"]["Cycles"], 0)
        self.assertGreater(result["MoEs"]["Total_Transport_Distance_km"], 0)
        self.assertEqual(result["Power"]["Unserved_Energy_kWh"], 0)

    def test_power_supply_and_payloads_are_overridden_by_scenario_config(self):
        options = self._options()
        config = options["scenario_config"]
        config["power"]["supply"] = {
            "power_output_kw": 240.0,
            "battery_capacity_kwh": 900.0,
            "initial_battery_charge_kwh": 450.0,
        }
        config["rovers"]["capacity_by_flow_kg"] = {
            "water": 25.0,
            "product": 7.5,
        }

        blueprint = compile_scenario(options, asset_root=self.assets)
        solar = blueprint.modules["SolarArray"].attributes

        self.assertEqual(solar["powerOutput"], 240.0)
        self.assertEqual(solar["batteryCapacity"], 900.0)
        self.assertEqual(solar["batteryCharge"], 450.0)
        self.assertEqual(blueprint.rover_capacity_by_flow_kg["Water"], 25.0)
        self.assertEqual(blueprint.rover_capacity_by_flow_kg["Product"], 7.5)

    def test_unknown_equation_variable_is_rejected_before_run(self):
        options = self._options()
        scenario = options["scenario_config"]
        scenario["scenario_builder"]["module_equations"]["WaterProcessor"] = (
            "ProductOut = WaterIn * missingEfficiency\n"
            "ProcessingTime = WaterIn / processingRate"
        )
        messages = validate_generic_scenario(
            options, raise_error=False, asset_root=self.assets
        )
        self.assertTrue(any("missingEfficiency" in message for message in messages))

    def test_incompatible_units_are_rejected(self):
        options = self._options()
        duplicate = deepcopy(
            options["scenario_config"]["scenario_builder"]["resource_routes"][0]
        )
        duplicate.update({
            "id": "water_unit_conflict",
            "from": "WaterExtractor",
            "to": "WaterTank",
            "unit": "lb",
        })
        options["scenario_config"]["scenario_builder"]["resource_routes"].append(
            duplicate
        )
        messages = validate_generic_scenario(
            options, raise_error=False, asset_root=self.assets
        )
        self.assertTrue(any("incompatible route units" in message for message in messages))

    def test_power_consumer_without_interface_is_rejected(self):
        options = self._options()
        options["scenario_config"]["scenario_builder"]["sysml_interfaces"] = []
        messages = validate_generic_scenario(
            options, raise_error=False, asset_root=self.assets
        )
        self.assertTrue(any("consumes power" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
