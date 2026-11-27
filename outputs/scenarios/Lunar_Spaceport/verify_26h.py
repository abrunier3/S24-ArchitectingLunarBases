"""Run in NVIDIA Kit's Script Editor after loading the supplied scenario."""
import gc
import json
import math
from pathlib import Path

import omni.kit.app
import omni.usd
from pxr import Usd, UsdGeom

def verify_loaded_lunar_spaceport():
    candidates = [obj for obj in gc.get_objects()
                  if type(obj).__name__ == 'LSP1PipelineExtension'
                  and getattr(obj, 'is_loaded', False)]
    if len(candidates) != 1:
        raise RuntimeError('Select Lunar Spaceport case study in LSP1 Mission Playback first.')
    ext = candidates[0]
    folder = Path(ext.manifest_path).resolve().parents[1]
    expected = json.loads((folder / 'expected_at_26h.json').read_text())
    actual_id = ext.manifest['scenario']['request_id']
    if expected['request_id'] != actual_id or actual_id != ext.des_data['request_id']:
        raise RuntimeError('Loaded scenario and DES request IDs differ from the reference.')
    ext._pause()
    ext._seek_to_des_time(26.0)
    stage = omni.usd.get_context().get_stage()
    cache = UsdGeom.XformCache(Usd.TimeCode.Default())
    observed = {}
    for actor, row in expected['actors'].items():
        prim = stage.GetPrimAtPath(row['prim'])
        if not prim or not prim.IsValid():
            raise RuntimeError('Missing actor in the active stage: ' + actor)
        position = list(cache.GetLocalToWorldTransform(prim).ExtractTranslation())
        observed[actor] = {'world_position_m': position,
                           'position_error_m': math.dist(position,row['position_local_m']),
                           'route':ext.actor_motion_state.get(actor,{}).get('route_name')}
    snap = ext._get_snapshot(26.0)
    report = {'request_id':actual_id,'kit_build':str(omni.kit.app.get_app().get_build_version()),
              'time_h':ext.current_des_time,'time_label':ext.time_label.text,
              'stage':stage.GetRootLayer().identifier,'actors':observed,
              'dashboard':{k:v.text for k,v in ext.mission_labels.items()},
              'displayed_plants':{k:v.text for k,v in ext.plant_labels.items()},
              'depot_snapshot_kg':snap['PropellantDepot']['LOX_Stored'],
              'lox_in_transit_snapshot_kg':snap['Batch_Operations']['In_Transit_LOX_kg']}
    report['pose_and_route_check'] = all(v['position_error_m'] < .1 and v['route'] == expected['actors'][k]['route'] for k,v in observed.items())
    report['des_inventory_check'] = abs(report['depot_snapshot_kg']-expected['depot_kg']) < 1e-6 and abs(report['lox_in_transit_snapshot_kg']-expected['in_transit_kg']) < 1e-6
    output = folder / 'observed_in_kit_26h.json'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print('Kit observations saved to',output,report['pose_and_route_check'],report['des_inventory_check'])
verify_loaded_lunar_spaceport()
