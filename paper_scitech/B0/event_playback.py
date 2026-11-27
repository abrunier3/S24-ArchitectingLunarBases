"""Supplement the standard manifest using console events from the same B0 run."""
import csv
import json
import re
import sys
from pathlib import Path

def main(run):
    dest=run/'omniverse'
    m=json.loads((dest/'manifest.json').read_text())
    d=json.loads((run/'des_results.json').read_text())
    config=d['results']['Scenario_Config']
    assert d['request_id']==m['scenario']['request_id']
    routes={r['rover_id']:r for r in config['scenario_builder']['resource_routes']}
    events=list(csv.DictReader((run/'events.csv').open()))
    for actor in m['actors']:
        name=actor['id']
        route=routes[name.replace(' Cargo Rover ','Rover_')]
        assert 'TravelTime = Distance * hoursPerKm' in config['scenario_builder']['module_equations'][route['rover_type']]
        duration=route['distance_km']*config['rovers']['travel_time_hr_per_km']
        moves=[]
        def leg(start,end,reverse,source):
            assert end>start and (not moves or start>=moves[-1]['end_time']-0.011)
            moves.append(dict(route_name=route['route_name'],from_module=route['to' if reverse else 'from'],
                        to_module=route['from' if reverse else 'to'],reverse=reverse,
                        start_time=round(max(0,start),4),end_time=round(end,4),source=source))
        last_load=None
        for row in events:
            t,msg=float(row['time_hr']),row['event']
            if name not in msg:
                continue
            if 'acquired '+name in msg:
                last_load=t
            elif (name+' delivered ' in msg and 'kg regolith to' in msg) or ('kg LOX to' in msg and name+' beginning' in msg):
                start=last_load if last_load is not None else t-duration
                assert abs(t-start-duration)<0.011
                leg(start,t,False,'DES delivery; departure logged for LOX, inferred from active travel law for regolith')
                leg(t,t+duration,True,'DES unloading followed by empty return; arrival extrapolated if outside horizon')
                last_load=None
            elif name+' returned empty' in msg:
                assert moves[-1]['reverse'] and abs(moves[-1]['end_time']-t)<0.011
                moves[-1].update(end_time=t,source='DES unloading and empty return events')
        total=d['log']['60'][name]['total_distance_traveled']
        assert abs(len(moves)*route['distance_km']-total)<1e-7
        actor['movements']=moves
        actor.update({k:moves[0][k] for k in ['start_time','end_time','from_module','to_module','route_name']})
    m['generated_from']['B0_event_stream']='../events.csv'
    m['playback']['timing_basis']='B0 offline event reconciliation; event timestamps printed to 0.01 h'
    (dest/'manifest_events.json').write_text(json.dumps(m,separators=(',',':'))+'\n')
    print({a['id']:len(a['movements']) for a in m['actors']})

if __name__=='__main__':
    main(Path(sys.argv[1]))
