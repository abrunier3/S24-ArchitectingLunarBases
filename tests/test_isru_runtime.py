import json
import os
import tempfile
import unittest
from pathlib import Path

import simpy

from S24.DES_pipeline_version.ISRU_DES_Model_V5_2_PV import (
    _resource_routes_for_rover,
    run_scenario,
)
from S24.DES_pipeline_version.ISRUPlant import ISRUPlant
from S24.DES_pipeline_version.ImportUtility import data_from_json
from S24.DES_pipeline_version.scenario_equations import evaluate_equations


class IsruRuntimeTests(unittest.TestCase):
    def test_plant_uses_explicit_conversion_efficiency(self):
        root = Path(__file__).resolve().parents[1]
        attributes = json.loads(
            (root / "clean_database/json/ECLIPSE_Project/assets/ISRUPlant.json").read_text()
        )["attributes"]
        attributes["excavationEnergyCoeff"] = 0.0
        attributes["conversionEfficiency"] = 0.01
        system = simpy.Environment()
        plant = ISRUPlant(system, "plant", attributes)

        system.process(plant.processRegolith(system, 4000.0))
        system.run()

        self.assertEqual(plant.totalLOXProduction, 40.0)

    def test_detailed_isru_equation_matches_the_named_process_parameters(self):
        root = Path(__file__).resolve().parents[1]
        attributes = json.loads(
            (root / "clean_database/json/ECLIPSE_Project/assets/ISRUPlant.json").read_text()
        )["attributes"]
        equations = json.loads(
            (root / "clean_database/scenarios/presets/ISRU.json").read_text()
        )["scenario_logic"]["moduleEquations"]["ISRUPlant"]
        regolith_mass = 4000.0
        expected = evaluate_equations(
            equations,
            {**attributes, "RegolithIn": regolith_mass, "transportDist": 1.0},
            effect_outputs={"LOXOut", "ProcessingTime", "EnergyConsumed", "PowerIn"},
        )

        system = simpy.Environment()
        plant = ISRUPlant(system, "plant", attributes)
        system.process(plant.processRegolith(system, regolith_mass))
        system.run()

        self.assertAlmostEqual(plant.totalLOXProduction, expected["LOXOut"])
        self.assertAlmostEqual(plant.totalEnergyConsumed, expected["EnergyConsumed"])

    def test_scenario_asset_root_is_used_for_runtime_assets(self):
        root = Path(__file__).resolve().parents[1]
        asset = data_from_json(
            "ISRUV2.json",
            asset_root="clean_database/json/ISRU_Missionjjj/assets",
        )["ISRUPlant"]

        expected = json.loads(
            (root / "clean_database/json/ISRU_Missionjjj/assets/ISRUPlant.json").read_text()
        )["attributes"]
        self.assertEqual(asset.raw["attributes"], expected)

    def test_base_rover_route_applies_to_every_fleet_instance(self):
        builder = {
            "resource_routes": [
                {
                    "flow": "Regolith",
                    "rover_id": "RegolithRover",
                    "from": "ISRUExcavation",
                    "to": "ISRUPlant",
                }
            ]
        }

        self.assertEqual(
            len(_resource_routes_for_rover(builder, "Regolith", "RegolithRover_1")),
            1,
        )
        self.assertEqual(
            len(_resource_routes_for_rover(builder, "Regolith", "RegolithRover_3")),
            1,
        )

    def test_neutral_source_power_boundary_runs_in_isru_controller(self):
        options = {
            "active_nodes": ["ISRUPlant", "RegolithRover"],
            "scenario_config": {
                "simulation": {"duration_hr": 0.01},
                "scenario_builder": {
                    "module_equations": {
                        "ISRUExcavation": (
                            "RegolithOut = RequestedRegolith\n"
                            "EnergyConsumed = 0\n"
                            "PowerOut = 0"
                        )
                    }
                },
            },
        }

        previous_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                run_scenario(options)
                results_written = Path("lunar_spaceport_results.json").exists()
        finally:
            os.chdir(previous_cwd)

        self.assertTrue(results_written)

    def test_energy_unconstrained_mode_skips_power_manager_and_rover_battery_limits(self):
        options = {
            "active_nodes": ["ISRUPlant", "RegolithRover", "SolarPowerSystem"],
            "scenario_config": {
                "simulation": {"duration_hr": 0.01},
                "rovers": {"energy_kwh_per_km_per_kg": 100.0},
                "power": {"ignore_power": True},
            },
        }

        previous_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                run_scenario(options)
                results = json.loads(Path("lunar_spaceport_results.json").read_text())
        finally:
            os.chdir(previous_cwd)

        self.assertNotIn("Solar_Power_System", results)
        self.assertNotIn("Power_Manager", results)

    def test_legacy_charging_station_config_is_ignored(self):
        options = {
            "active_nodes": [
                "ISRUPlant",
                "RegolithRover",
                "LOXRover",
                "LaunchLandingZone",
            ],
            "scenario_config": {
                "simulation": {"duration_hr": 0.01},
                "power": {
                    "charging_station": {
                        "enabled_when_lox_rover_active": True,
                        "charging_power_kw": 999.0,
                        "efficiency": 0.01,
                    }
                },
            },
        }

        previous_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                run_scenario(options)
                results = json.loads(Path("lunar_spaceport_results.json").read_text())
        finally:
            os.chdir(previous_cwd)

        self.assertNotIn("Charging_Station", results)

    def test_reference_preset_equations_run_with_all_isru_systems(self):
        root = Path(__file__).resolve().parents[1]
        preset = json.loads(
            (root / "clean_database/scenarios/presets/ISRU.json").read_text()
        )
        options = {
            "active_nodes": [
                "HabitationModule",
                "ISRUPlant",
                "LaunchLandingZone",
                "LOXRover",
                "SolarPowerSystem",
                "RegolithRover",
            ],
            "scenario_config": {
                "simulation": {"duration_hr": 60.0},
                "routes": {
                    "use_sysml_distances": False,
                    "regolith_distance_km": 2.39,
                    "lox_distance_km": 1.9,
                },
                "power": {
                    "continuous_load_kw": {
                        "habitation": None,
                        "communications": None,
                        "landing_zone_utilities": None,
                    },
                    "landing_zone_chilling_kw_per_kg": None,
                    "spikes": {
                        "habitation": [],
                        "communications": [],
                        "landing_zone": [],
                    },
                    "module_models": preset["power_models"],
                },
                "scenario_builder": {
                    "module_equations": preset["scenario_logic"]["moduleEquations"],
                },
            },
        }

        previous_cwd = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                run_scenario(options)
                results_written = Path("lunar_spaceport_results.json").exists()
                log = json.loads(Path("lunar_spaceport_log.json").read_text())
        finally:
            os.chdir(previous_cwd)

        self.assertTrue(results_written)
        self.assertEqual(max(map(float, log)), 60.0)


if __name__ == "__main__":
    unittest.main()
