"""Produce publication tables from one run; no simulation or visual interpolation."""
import csv
import json
import re
import sys
from pathlib import Path

def write_rows(path, rows):
    with path.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def main(folder):
    data=json.loads((folder/'des_results.json').read_text())
    result=data['results']
    events=(folder/'events.txt').read_text().splitlines()
    rows=[]
    incoming=[]
    for line in events:
        match=re.match(r'\[([\d.]+) hr\] (.*)',line)
        if not match:
            continue
        hour,msg=match.groups()
        rows.append(dict(time_hr=hour,event=msg))
        delivery=re.search(r'delivered ([\d.]+) kg regolith to (\w+)',msg)
        if delivery:
            incoming.append((float(hour),delivery.group(2),float(delivery.group(1))))
    write_rows(folder/'events.csv',rows)
    times=[]
    bus=result['Power_Manager']
    generated=bus['Energy_Generated_Time_Array_kWh']
    demand=bus['Total_Demand_Time_Array_kWh']
    assert len(demand)==len(generated)==59 and all(g>d for g,d in zip(generated,demand))
    for time,snap in sorted(data['log'].items(), key=lambda pair:float(pair[0])):
        t=int(float(time))
        row=dict(time_hr=t)
        for i in (1,2):
            plant=snap[f'ISRU_Plant_{i}']
            row[f'feed_admitted_{i}_kg']=plant['regolith_recieved']
            row[f'feed_delivered_{i}_kg']=sum(m for h,plant_id,m in incoming if h<=t and plant_id==f'ISRUPlant_{i}')
            row[f'lox_credited_{i}_kg']=plant['total_LOX_production']
            row[f'lox_stock_{i}_kg']=plant['LOX_Stored']
            row[f'plant_{i}_kwh']=plant['total_energy_consumed']
        row['lox_credited_total_kg']=sum(row[f'lox_credited_{i}_kg'] for i in (1,2))
        row['lox_plant_stock_total_kg']=sum(row[f'lox_stock_{i}_kg'] for i in (1,2))
        row['lox_in_transit_kg']=sum(snap[f'LOX Cargo Rover {i}']['current_load'] for i in (1,2))
        row['lox_depot_kg']=snap['PropellantDepot']['LOX_Stored']
        row['lox_landing_zone_kg']=snap['LZ-Alpha']['LOX_Stored']
        residual=row['lox_credited_total_kg']-sum(row[k] for k in ['lox_plant_stock_total_kg','lox_in_transit_kg','lox_depot_kg','lox_landing_zone_kg'])
        assert abs(residual)<1e-7,(t,residual)
        for kind in ['Regolith','LOX']:
            for i in (1,2):
                rover=snap[f'{kind} Cargo Rover {i}']
                row[f'{kind}_rover_{i}_km']=rover['total_distance_traveled']
                row[f'{kind}_rover_{i}_battery_kwh']=rover['battery_charge']
        solar=snap['Solar_Power_System']
        row['solar_battery_kwh']=solar['battery_charge']
        # The logger can precede a scheduled bus tick. Associate cumulative
        # bus demand with the count of completed ticks visible in the snapshot.
        n=round(solar['total_energy_generated']/generated[0])
        row['solar_generated_cum_kwh']=solar['total_energy_generated']
        row['bus_demand_cum_kwh']=sum(demand[:n])
        row['bus_ticks_observed']=n
        times.append(row)
    write_rows(folder/'hourly.csv',times)
    write_rows(folder/'bus.csv',[dict(tick_end_hr=i,generated_kwh=g,bus_demand_kwh=d,unserved_kwh=0) for i,(g,d) in enumerate(zip(generated,demand),1)])
    stats=result['ISRU_Plants']['Fleet_Totals']
    final=times[-1]
    n_batches=round(stats['Regolith_Received_kg']/4000)
    completed=sum('produced ' in r['event'] and 'kg of LOX from' in r['event'] for r in rows)
    lox=final['lox_credited_total_kg']
    plant_kwh=sum(final[f'plant_{i}_kwh'] for i in (1,2))
    unit_process=result['ISRU_Plants']['ISRU_Plant_1']['Equation_Outputs']['EnergyConsumed']
    assert abs(sum(m for _,_,m in incoming)-stats['Regolith_Received_kg']-sum(result['ISRU_Plants'][f'ISRU_Plant_{i}']['Regolith_Input_Stored_kg'] for i in (1,2)))<1e-8
    rovers=sum(s['total_energy_consumed'] for k,s in data['log']['60'].items() if 'Cargo Rover' in k)
    summary=dict(request_id=data['request_id'],regolith_physically_delivered_kg=sum(m for _,_,m in incoming),
        batches_admitted=n_batches,batches_completed=completed,completion_basis_lox_kg=completed*lox/n_batches,
        unit_process_kwh_per_batch=unit_process,process_specific_kwh_per_kg=n_batches*unit_process/lox,
        plant_storage_and_other_kwh=plant_kwh-n_batches*unit_process,
        plant_specific_kwh_per_kg=plant_kwh/lox,bus_specific_kwh_per_kg=sum(demand)/lox,
        traction_separate_kwh=rovers,peak_interval_bus_kwh=max(demand),bus_ticks=len(demand),
        unserved_kwh=0,added_battery_kwh=final['solar_battery_kwh']-times[0]['solar_battery_kwh'],
        inferred_curtailed_kwh=sum(generated)-sum(demand)-(final['solar_battery_kwh']-times[0]['solar_battery_kwh']),
        max_plant_buffers={p:max(float(m) for line in events for m in re.findall(r'to '+p+r' \(input inventory: ([\d.]+) kg',line)) for p in ['ISRUPlant_1','ISRUPlant_2']})
    (folder/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':
    main(Path(sys.argv[1]))
