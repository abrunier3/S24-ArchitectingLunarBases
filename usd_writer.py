from pxr import Usd, UsdGeom, Sdf

def write_usd(model, output_path="output.usd"):
    # Create a new USD stage
    stage = Usd.Stage.CreateNew(output_path)

    # Write each top-level part as a USD prim
    for part in model["parts"]:
        write_part(stage, part, parent_path="/")

    # Save the USD file
    stage.GetRootLayer().Save()
    return output_path


def write_part(stage, part, parent_path):
    name = part["name"]
    prim_path = parent_path + name

    # Create an Xform prim for the part
    prim = UsdGeom.Xform.Define(stage, prim_path)

    # Write attributes (flat key/value)
    for key, value in part["attributes"].items():
        attr = prim.GetPrim().CreateAttribute(key, Sdf.ValueTypeNames.String)
        attr.Set(str(value))

    # Write children (nested parts or attribute groups)
    for child in part["children"]:
        # If it's a nested part
        if child["kind"] == "part":
            write_part(stage, child, prim_path + "/")

        # If it's an attribute group, flatten it
        elif child["kind"] == "attribute_group":
            for key, value in child["attributes"].items():
                attr = prim.GetPrim().CreateAttribute(f"{child['name']}:{key}", Sdf.ValueTypeNames.String)
                attr.Set(str(value))