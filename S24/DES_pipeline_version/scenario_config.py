import copy
import json
from pathlib import Path


DEFAULT_SCENARIO_CONFIG = {
    "simulation": {
        "duration_hr": 60.0,
    },
    "regolith": {
        "batch_kg": 4000.0,
        "buffer_capacity_per_rover_kg": 20000.0,
    },
    "isru": {
        "plant_count": 1,
        "processing_rate_kg_hr": 1600.0,
        "lox_transport_threshold_kg": 100.0,
        "lox_delivery_poll_dt_hr": 1.0,
        "lox_storage_energy_kwh_per_kg_hr": 0.31,
        "lox_storage_energy_dt_hr": 1.0,
    },
    "rovers": {
        "regolith": {
            "count": 1,
        },
        "lox": {
            "count": 1,
        },
        "energy_kwh_per_km_per_kg": 0.00034,
        "travel_time_hr_per_km": 5.0,
    },
    "routes": {
        "use_sysml_distances": True,
        "regolith_distance_km": 1.0,
        "lox_distance_km": 1.0,
        "distance_source": "defaults",
    },
    "power": {
        "management_dt_hr": 1.0,
        "spikes": {
            "habitation": [
                {"time_hr": 10.0, "energy_kwh": 20.0}
            ],
            "communications": [
                {"time_hr": 15.0, "energy_kwh": 10.0}
            ],
            "landing_zone": [
                {"time_hr": 25.0, "energy_kwh": 50.0}
            ],
        },
        "charging_station": {
            "enabled_when_lox_rover_active": True,
            "charging_power_kw": 20.0,
            "efficiency": 0.85,
        },
    },
}


DEFAULT_CONFIG_PATH = Path("clean_database/des/scenario_config.json")
DEFAULT_SYSML_JSON_PATH = Path("clean_database/json/ECLIPSE_Project/ECLIPSE_Project.json")


def _deep_merge(base, override):
    merged = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _as_float(value, fallback):
    if value is None or value == "":
        return fallback
    return float(value)


def _as_int(value, fallback):
    if value is None or value == "":
        return fallback
    return int(float(value))


def _load_json_file(path):
    path = Path(path)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _parse_inline_config(value):
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return json.loads(value)
    raise TypeError("scenario_config must be a dict or JSON string")


def _apply_legacy_options(config, options):
    config = copy.deepcopy(config)

    config["rovers"]["regolith"]["count"] = _as_int(
        options.get("Num_Regolith_Rovers"),
        config["rovers"]["regolith"]["count"],
    )
    config["rovers"]["lox"]["count"] = _as_int(
        options.get("Num_LOX_Rovers"),
        config["rovers"]["lox"]["count"],
    )
    config["isru"]["plant_count"] = _as_int(
        options.get("Num_ISRU_Plants"),
        config["isru"]["plant_count"],
    )
    config["routes"]["regolith_distance_km"] = _as_float(
        options.get("Regolith_Haul_Distance"),
        config["routes"]["regolith_distance_km"],
    )
    config["routes"]["lox_distance_km"] = _as_float(
        options.get("LOX_Haul_Distance"),
        config["routes"]["lox_distance_km"],
    )
    config["rovers"]["energy_kwh_per_km_per_kg"] = _as_float(
        options.get("Rover_Energy_Consumption"),
        config["rovers"]["energy_kwh_per_km_per_kg"],
    )
    config["rovers"]["travel_time_hr_per_km"] = _as_float(
        options.get("Rover_Travel_Time"),
        config["rovers"]["travel_time_hr_per_km"],
    )
    config["isru"]["processing_rate_kg_hr"] = _as_float(
        options.get("ISRU_Plant_Processing_Rate"),
        config["isru"]["processing_rate_kg_hr"],
    )
    config["isru"]["lox_transport_threshold_kg"] = _as_float(
        options.get("LOX_Transport_Threshold"),
        config["isru"]["lox_transport_threshold_kg"],
    )
    config["simulation"]["duration_hr"] = _as_float(
        options.get("Simulation_Duration_hr"),
        config["simulation"]["duration_hr"],
    )

    if "Use_SysML_Route_Distances" in options:
        raw = str(options["Use_SysML_Route_Distances"]).strip().lower()
        config["routes"]["use_sysml_distances"] = raw not in {"0", "false", "no"}

    return config


def _extract_sysml_route_distances(sysml_path=DEFAULT_SYSML_JSON_PATH):
    sysml_path = Path(sysml_path)
    if not sysml_path.exists():
        return {}

    with sysml_path.open() as f:
        sysml = json.load(f)

    regolith_distances = []
    lox_distances = []
    for connection in sysml.get("connections", []):
        flow = str(connection.get("flow") or "").lower()
        path = connection.get("path") or {}
        distance = path.get("distance_km", connection.get("distance_km"))
        if distance is None:
            continue
        try:
            distance = float(distance)
        except (TypeError, ValueError):
            continue

        if flow == "regolith":
            regolith_distances.append(distance)
        elif flow == "lox":
            lox_distances.append(distance)

    route_distances = {}
    if regolith_distances:
        route_distances["regolith_distance_km"] = max(regolith_distances)
    if lox_distances:
        route_distances["lox_distance_km"] = max(lox_distances)
    if route_distances:
        route_distances["distance_source"] = str(sysml_path)
    return route_distances


def load_scenario_config(options=None):
    options = options or {}
    config = copy.deepcopy(DEFAULT_SCENARIO_CONFIG)

    config_path = options.get("scenario_config_path") or options.get("Scenario_Config_Path")
    if config_path:
        config = _deep_merge(config, _load_json_file(config_path))
    else:
        config = _deep_merge(config, _load_json_file(DEFAULT_CONFIG_PATH))

    inline_config = options.get("scenario_config") or options.get("Scenario_Config")
    config = _deep_merge(config, _parse_inline_config(inline_config))
    config = _apply_legacy_options(config, options)

    if config.get("routes", {}).get("use_sysml_distances", True):
        sysml_path = options.get("sysml_json_path") or options.get("SysML_JSON_Path") or DEFAULT_SYSML_JSON_PATH
        sysml_routes = _extract_sysml_route_distances(sysml_path)
        if sysml_routes:
            config["routes"].update(sysml_routes)

    return config
