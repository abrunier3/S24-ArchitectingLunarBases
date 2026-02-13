# Step 7: Load USD stage inside Omniverse Kit

import omni.usd
from pxr import Usd

USD_PATH  = "/workspace/notebooks/database/scenes/assembly.usda"

ctx = omni.usd.get_context()
ctx.open_stage(USD_PATH)

stage = ctx.get_stage()
print("Stage loaded:", stage)
