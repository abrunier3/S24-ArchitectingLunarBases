"""Build the standard ECLIPSE visualization from this run's active system and DES."""
import hashlib
import json
import math
import sys
from pathlib import Path

from pxr import Usd, UsdGeom, UsdUtils
root = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(root),str(root/'extensions/lsp1.pipeline')]
from S24.usd.model_submission import build_submission_manifest
from S24.usd import build_usd_scene_from_manifest
from S24.usd.waypoints import write_connections_usda
from lsp1_pipeline.manifest_builder import build_manifest, write_manifest

def main(folder):
    folder=folder.resolve()
    dest=folder/'omniverse'
    dest.mkdir(exist_ok=True)
    system=folder/'system.json'
    results=folder/'des_results.json'
    g=json.loads(system.read_text())
    des=json.loads(results.read_text())
    assets=root/'clean_database/json/ISRU_Mission/assets'
    parts={p['name']:p for p in g['parts']}
    model=build_submission_manifest(asset_paths=[assets/f'{name}.json' for name in parts],verbose=0)
    for p in model['parts']:
        assert p['cad_found'] and '/ISRU_Mission/' in p['cad_path'],p['name']
        tr=parts[p['name']]['transform']
        p.update({k:v for k,v in tr.items() if k in ('position_m','rotation_deg','scale')})
    scene=dest/'scene.usda'
    paths=dest/'waypoints.usda'
    terrain=root/'clean_database/scenes/Lunar_surface_v4.usdc'
    build_usd_scene_from_manifest(model,output_path=str(scene),verbose=0)
    write_connections_usda(json_path=str(system),output_usda_path=str(paths),curve_width=4.0,
                           write_waypoints=True,marker_radius=10.0,verbose=0)
    manifest=build_manifest(system_json_path=system,waypoints_usd_path=paths,des_json_path=results,
        scene_usd_path=scene,terrain_usd_path=terrain,output_path=dest/'manifest.json',scenario_slug=des['scenario_slug'])
    manifest['scenario']['request_id']=des['request_id']
    write_manifest(manifest,dest/'manifest.json')
    stage=Usd.Stage.Open(str(scene))
    waypoint_stage=Usd.Stage.Open(str(paths))
    assert all(stage.GetPrimAtPath('/World/'+t) for t in parts)
    assert not stage.GetPrimAtPath('/World/HabitationModule')
    assert waypoint_stage.GetPrimAtPath(manifest['waypoint_root'])
    layers,assets_used,unresolved=UsdUtils.ComputeAllDependencies(str(scene))
    assert all('.jpg' in str(asset).lower() for asset in unresolved),unresolved
    for name in parts:
        assert any(prim.IsA(UsdGeom.Mesh) for prim in Usd.PrimRange(stage.GetPrimAtPath('/World/'+name))), name
    diag=manifest['terrain_projection']['routes']['routes']
    routes={}
    for r in g['scenario_logic']['resource_routes']:
        path=diag[r['route_name']]
        points=path['sampled_waypoints_m']
        routes[r['rover_id']]=dict(plan_km=r['distance_km'],projected_length_km=(
            sum(math.dist(a,b) for a,b in zip(points,points[1:]))/1000 if path['out_of_bounds_count']==0 else None),
            projected_max_slope_deg=path['max_slope_deg'],sample_count=path['sample_count'],missing=path['out_of_bounds_count'],
            mesh_status=path['status'])
    checks=dict(request_id=des['request_id'],openusd=Usd.GetVersion(),routes=routes,
                unresolved_material_textures=[str(x).replace(str(root)+'/','') for x in unresolved],source_prims=list(parts),actor_movements={a['id']:len(a['movements']) for a in manifest['actors']},
                dependencies={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [terrain,*[Path(l.realPath) for l in layers if l.realPath and Path(l.realPath)!=scene]]})
    (dest/'checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(routes,indent=2),checks['actor_movements'])

if __name__=='__main__':
    main(Path(sys.argv[1]))
