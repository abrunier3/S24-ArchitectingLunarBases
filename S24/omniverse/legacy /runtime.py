from omni.isaac.kit import SimulationApp

def start_omniverse(headless=False):
    config = {
        "headless": headless,
        "renderer": "RayTracedLighting"
    }
    return SimulationApp(config)