"""Map timed batch results onto the ECLIPSE DES result and telemetry envelopes."""

import json
from pathlib import Path

from S24.DES_pipeline_version.scenario_config import load_scenario_config


def collect_result_fields(options, execution):
    """Use in-memory results for timed batches and the established files otherwise."""
    if execution is None or "max_event_mass_residual_kg" not in execution:
        return {
            "results": json.loads(Path("lunar_spaceport_results.json").read_text()),
            "log": json.loads(Path("lunar_spaceport_log.json").read_text()),
        }

    config = load_scenario_config(options)
    specs = {line["plant_id"]: line for line in config["batch_operations"]["lines"]}
    outputs = {spec["id"]: spec["output_id"] for spec in config["batch_operations"]["liquefiers"]}
    rover_specs = {
        line[key]["id"]: line[key] for line in specs.values()
        for key in ("regolith_rover", "lox_rover") if key in line
    }
    operation_events = [
        event for event in execution["events"]
        if event["event"] not in {"liquefaction_started", "liquid_available"}
    ]
    deliveries = [event for event in operation_events if event["event"] == "material_delivered"]
    delivery_index = 0
    feed_delivered = dict.fromkeys(specs, 0.0)
    totals = {}
    log = {}
    previous_power = (0, 0)

    for snapshot in execution["time_series"]:
        time = snapshot["time_hr"]
        while delivery_index < len(deliveries) and deliveries[delivery_index]["time_hr"] <= time:
            delivery = deliveries[delivery_index]
            if delivery["resource"] == "Regolith":
                feed_delivered[delivery["destination"]] += delivery["mass_kg"]
            delivery_index += 1
        plants = {}
        for plant, line in snapshot["lines"].items():
            spec = specs[plant]
            liquid_output = outputs[spec["liquefier_id"]]
            plants[plant] = {
                "Name": plant,
                "processingRate": spec["batch_kg"] / spec["processing_hr"],
                "LOX_Stored": snapshot["liquid_stocks_kg"].get(plant, 0),
                "total_LOX_production": line["liquid_kg"],
                "regolith_recieved": feed_delivered[plant],
                "Feed_kg": line["feed_kg"],
                "Oxygen_Extracted_kg": line["oxygen_kg"],
                "Liquid_Output_ID": liquid_output,
                "Processing": line["solid_in_process_kg"] > 0,
                "Completed_Batches": line["completed"],
                "Missed_Batches": line["missed"],
            }
        # When the liquid output is a common tank, identify it as a separate stock.
        stocks = {name: {"Name": name, "LOX_Stored": mass}
                  for name, mass in {**snapshot["liquid_stocks_kg"], **snapshot["depots_kg"]}.items()
                  if name not in plants}
        vehicles = {
            name: {
                "Name": name, "rover_type": "cargo", "current_load": vehicle["cargo_kg"],
                "battery_charge": vehicle["battery_kwh"],
                "battery_capacity": rover_specs[name].get("battery_kwh", 0),
                "total_distance_traveled": vehicle["completed_distance_km"],
                "Operation": vehicle["phase"],
                "Cargo_Resource": vehicle["cargo_resource"],
            }
            for name, vehicle in snapshot["vehicles"].items()
        }
        energy = snapshot["energy"]
        generated = energy["electric_available_kwh"]
        demand = energy["electric_core_kwh"] + energy["electric_charging_kwh"]
        totals = {
            "Total_LOX_Produced_kg": sum(plant["total_LOX_production"] for plant in plants.values()),
            "Total_LOX_Delivered_kg": snapshot["delivered_lox_kg"],
            "Total_Regolith_Received_kg": sum(feed_delivered.values()),
            "Total_System_Demand_kWh": demand,
            "Plant_LOX_kg": sum(plant["LOX_Stored"] for plant in plants.values()),
            "Common_Tank_LOX_kg": sum(mass for key, mass in snapshot["liquid_stocks_kg"].items()
                                      if key not in plants),
            "In_Transit_LOX_kg": snapshot["mass_in_transit_kg"]["lox"],
            "Thermal_To_Reactors_kWh": energy["thermal_to_reactors_kwh"],
            "Electric_Unserved_kWh": energy["electric_unserved_kwh"],
        }
        log[str(time)] = {
            **plants, **vehicles, **stocks,
            "Power_Manager": {"current_energy_production": generated - previous_power[0],
                              "current_energy_demand": demand - previous_power[1],
                              "total_energy_consumed": demand},
            "Batch_Operations": totals,
        }
        previous_power = generated, demand

    first_delivery = next((event["time_hr"] for event in deliveries if event["resource"] == "LOX"), None)
    return {
        "results": {
            "Engine": "BatchISRU",
            "Sim_Metrics": {"Simulation_Duration_hr": execution["summary"]["time_hr"],
                            "Active_Nodes": options.get("active_nodes", [])},
            "Scenario_Config": config,
            "MoEs": totals,
            "Batch_Operations": execution["summary"],
            "First_LOX_Delivery_hr": first_delivery,
            "Max_Mass_Residual_kg": execution["max_event_mass_residual_kg"],
        },
        "log": log,
        "operation_events": operation_events,
    }
