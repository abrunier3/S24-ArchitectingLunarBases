"""Select the validated ISRU engine or the generic scenario compiler."""

from S24.DES_pipeline_version.scenario_config import load_scenario_config


def _engine_mode(options):
    config = load_scenario_config(options)
    return str(config.get("engine", {}).get("mode", "isru")).strip().lower()


def check_scenario_validity(options, raiseError=True):
    if _engine_mode(options) == "generic":
        from S24.DES_pipeline_version.generic_scenario import validate_generic_scenario

        return validate_generic_scenario(options, raise_error=raiseError)

    from S24.DES_pipeline_version.ISRU_DES_Model_V5_2_PV import (
        check_scenario_validity as check_isru_scenario,
    )

    return check_isru_scenario(options.get("active_nodes", []), raiseError=raiseError)


def run_scenario(options):
    if _engine_mode(options) == "generic":
        from S24.DES_pipeline_version.generic_scenario import run_generic_scenario

        return run_generic_scenario(options)

    from S24.DES_pipeline_version.ISRU_DES_Model_V5_2_PV import (
        run_scenario as run_isru_scenario,
    )

    return run_isru_scenario(options)
