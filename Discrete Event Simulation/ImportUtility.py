import sys
from pathlib import Path

# Add the parent directory to the path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

# Standard library
import os
from pathlib import Path

# S24 pipeline
from S24.sysml import sysml_to_json, write_json
from S24.jsonio.vetting import VettingProc

print("Hello World!")

#NOTE: SYSML File must be conatined under database/sysml/ and the sysml_filename must only be the name of the sysml file (i.e. "ISRUPlantModelV2.sysml")
def generate_json_from_sysml(sysml_filename, json_filename):
    ROOT = Path.cwd().parent

    DATA_SYSML = ROOT / "S24-ArchitectingLunarBases" / "database" / "sysml"
    DATA_JSON  = ROOT / "S24-ArchitectingLunarBases" / "database" / "json"

    #SYSML_FILE = DATA_SYSML / "ISRUPlantModelV2.sysml"
    SYSML_FILE = DATA_SYSML / sysml_filename
    JSON_FILE  = DATA_JSON  / json_filename

    SYSML_FILE_PATH = Path(SYSML_FILE)

    with open(SYSML_FILE_PATH, "r", encoding="utf-8") as f:
        sysml_text = f.read()

    #print(sysml_text[:500], "...")

    parts_json = sysml_to_json(
        sysml_text,
        namespace="lunarspaceport1"
    )
    write_json(parts_json, JSON_FILE)
    vetting = VettingProc(source=str(JSON_FILE))
    vetted_parts = vetting.by_name
    
    #print(list(vetted_parts.keys()))
    #print(vetted_parts['ISRUPlant'])

    return vetted_parts

#NOTE: JSON File must be conatined under database/json/ and the json_filename must only be the name of the json file (i.e. "ISRU.json")
def data_from_json(json_filename):
    ROOT = Path.cwd().parent

    DATA_JSON  = ROOT / "S24-ArchitectingLunarBases" / "database" / "json"
    JSON_FILE  = DATA_JSON  / json_filename

    vetting = VettingProc(source=str(JSON_FILE))
    vetted_parts = vetting.by_name
    
    #print(list(vetted_parts.keys()))
    #print(vetted_parts['ISRUPlant'])

    return vetted_parts


isruPlant = data_from_json("ISRUV2.json")['ISRUPlant']
print(isruPlant.raw['attributes']["processingRate"])

#generate_json_from_sysml("ISRUPlantModelV3.sysml", "ISRUV2.json")