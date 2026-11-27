"""Run from the repository root. Outputs must be new and inside the checkout."""
import argparse
import contextlib
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from S24.sysml.main_api import sysml_to_json_transformer
from S24.DES_pipeline_version.ISRU_DES_Model_V5_2_PV import check_scenario_validity, run_scenario

def read(path):
    return json.loads(path.read_text())

def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def relative(path):
    return str(path.relative_to(ROOT))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main(out):
    os.chdir(ROOT)
    out.mkdir(parents=True, exist_ok=False)
    src = ROOT / 'clean_database/json/ISRU_Mission'
    base = ROOT / 'outputs/scenarios/ISRU_Mission/des_results.json'
    system = src / 'ISRU_Mission.json'
    sysml = ROOT / 'clean_database/sysml/ISRU_Mission.sysml'
    run_id = 'B0-' + uuid.uuid4().hex
    stamp = datetime.now(timezone.utc).isoformat()
    hist = read(base)
    cfg = json.loads(hist['inputs']['scenario_config'])
    logic = cfg['scenario_builder']
    types = [n for n in hist['sysml_active_nodes'] if n != 'HabitationModule']
    assert len(types) == 7
    active = [n for n in hist['des_active_nodes'] if n in types]
    slug = 'Lunar_Spaceport_B0'
    cfg['scenario'].update(name='Lunar Spaceport B0', slug=slug, sysml_file=relative(out/'reference.sysml'), json_asset_root=relative(out/'assets'))
    old_line = 'connect LSP1.LOXRover.LOXRover_LOXPortInOut to LSP1.ISRUPlant.ISRU_LOXPortOut'
    new_line = 'connect LSP1.ISRUPlant.ISRU_LOXPortOut to LSP1.LOXRover.LOXRover_LOXPortInOut'
    original = sysml.read_text()
    assert original.count(old_line) == 1
    corrected = original.replace(old_line, new_line)
    (out/'reference.sysml').write_text(corrected)
    parsed = sysml_to_json_transformer(0, corrected, namespace='S24_PIPELINE')
    assert not parsed['metadata']['validation_errors'], parsed['metadata']
    # Freeze the active system export with existing CAD metadata / historical DES properties.
    g = read(system)
    g['parts'] = [p for p in g['parts'] if p['name'] in types]
    for p in g['parts']:
        p.pop('parent',None)
        p['ports'] = [v for v in p.get('ports',[]) if 'habitation' not in json.dumps(v).lower()]
    g['connections'] = [c for c in parsed['connections'] if all(c[k]['part'] in types for k in ['from','to'])]
    assert len(g['connections']) == 8
    write(out/'graph.json',dict(active_nodes=types,connections=g['connections'],request_id=run_id))
    (out/'assets').mkdir()
    for n in types:
        asset=read(src/'assets'/f'{n}.json')
        asset['ports']=[v for v in asset.get('ports',[]) if 'habitation' not in json.dumps(v).lower()]
        write(out/'assets'/f'{n}.json',asset)
    subprocess.run(['node',str(Path(__file__).with_name('routes.js')),base,system,out/'routing.json'],check=True)
    urban=read(out/'routing.json')['urban']
    logic['instances']=urban['scenario_logic']['instances']
    logic['resource_routes']=urban['scenario_logic']['resource_routes']
    for k in ['module_classes','module_equations']:
        logic[k].pop('HabitationModule')
    logic['sysml_interfaces']=[v for v in logic['sysml_interfaces'] if v['to_type'] in types]
    for k in ['continuous_load_kw','spikes']:
        cfg['power'][k].pop('habitation')
    cfg['power']['module_models'].pop('HabitationModule')
    # Replace the geometry-only helper's partial UI state by the complete archived laws and interfaces.
    routing=read(out/'routing.json')
    routing['urban']['scenario_logic']=logic
    write(out/'routing.json',routing)
    u=g['urban_planning']
    u.update(module_instances=urban['modules'],routes=urban['mst_edges'],route_geometry=urban['connections'])
    g['scenario_logic']=logic
    g['metadata'].update(num_parts=len(types),num_connections=len(g['connections']),validation_errors=[],scope='active types; operational routes appended separately')
    for r in logic['resource_routes']:
        geom=u['route_geometry'][r['route_name']]
        length=sum(math.dist(a,b) for a,b in zip(geom['waypoints_m'],geom['waypoints_m'][1:]))/1000
        assert abs(length-r['distance_km']) < 0.00051 and geom['rover_id']==r['rover_id'] and not r['stops']
        assert r['from'] in u['module_instances'] and r['to'] in u['module_instances']
        g['connections'].append(dict(name=r['route_name'],type='OperationalRoute',flow=r['flow'],
            **{'from':{'part':r['from']},'to':{'part':r['to']}},rover_id=r['rover_id'],stops=[],path=geom))
    assert 'HabitationModule' not in json.dumps([types,cfg,g])
    write(out/'system.json',g)
    write(out/'scenario.json',cfg)
    opts=dict(active_nodes=active,sysml_active_nodes=types,sysml_json_path=str(out/'system.json'),
              scenario_config=cfg,scenario_config_path=str(ROOT/'clean_database/des/scenario_config.json'))
    check_scenario_validity(active)
    with tempfile.TemporaryDirectory() as temp, (out/'events.txt').open('w') as log:
        os.chdir(temp)
        try:
            with contextlib.redirect_stdout(log):
                run_scenario(opts)
            results=read(Path('lunar_spaceport_results.json'))
            times=read(Path('lunar_spaceport_log.json'))
        finally:
            os.chdir(ROOT)
    assert len(times)==61 and 'Habitat' not in results
    assert not any('Habitat' in name for snapshot in times.values() for name in snapshot)
    # Paths in saved inputs are portable from the repository root.
    opts.update(sysml_json_path=relative(out/'system.json'),scenario_config_path='clean_database/des/scenario_config.json')
    write(out/'des_results.json',dict(request_id=run_id,executed_at=stamp,status='success',scenario_slug=slug,
        scenario_name='Lunar Spaceport B0',sysml_file=cfg['scenario']['sysml_file'],sysml_active_nodes=types,
        des_active_nodes=active,inputs=opts,results=results,log=times))
    write(out/'resolved.json',results['Scenario_Config'])
    import simpy
    write(out/'provenance.json',dict(request_id=run_id,executed_at=stamp,git=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        python=sys.version,node=subprocess.check_output(['node','--version'],text=True).strip(),simpy=simpy.__version__,
        sources={relative(p):digest(p) for p in [base,system,sysml,ROOT/'ScenarioIndex.html',ROOT/'clean_database/des/scenario_config.json',*[(src/'assets'/f'{t}.json') for t in types]]}))
    print(run_id,results['MoEs'])

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('output',type=Path)
    main(parser.parse_args().output.resolve())
