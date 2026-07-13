def __getattr__(name):
    if name == "run_scenario":
        from .ISRU_DES_Model_V5_2_PV import run_scenario
        return run_scenario
    raise AttributeError(name)
