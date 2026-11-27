def __getattr__(name):
    if name == "run_scenario":
        from .scenario_runner import run_scenario
        return run_scenario
    if name == "check_scenario_validity":
        from .scenario_runner import check_scenario_validity
        return check_scenario_validity
    raise AttributeError(name)
