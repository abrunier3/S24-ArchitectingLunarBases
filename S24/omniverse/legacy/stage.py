from pxr import Usd
import omni.usd

def load_stage(usd_path: str):
    ctx = omni.usd.get_context()
    ctx.open_stage(usd_path)
    return ctx.get_stage()
