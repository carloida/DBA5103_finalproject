"""Temporary integrated demand -> allocation -> conditional routing -> cost evaluation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd
import scipy
from integration_costs import load_config,coefficients,unit_cost_matrix,route_cost
from hj_optimization_model import read_day,solve_allocation
from hj_policy_routing import equal_occupancy_rule,evaluate_policy,check_routes

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(frame,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    frame.to_csv(path,index=False,lineterminator='\n')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',default=str(ROOT/'sf_bikeshare/integration_cost_config.json'))
    ap.add_argument('--output-dir',default=str(ROOT/'output/sf_bikeshare/integration_review_2026-11-22'))
    ap.add_argument('--demand-root',default=str(ROOT/'tmp/generated_demand'))
    ap.add_argument('--build-demand',action='store_true')
    ap.add_argument('--dates',nargs='+',default=None)
    ap.add_argument('--time-limit',type=float,default=15.)
    ap.add_argument('--skip-routing',action='store_true')
    ap.add_argument('--extra-sensitivity',action='store_true')
    args=ap.parse_args()
    c=load_config(args.config);out=Path(args.output_dir);out.mkdir(parents=True,exist_ok=True)
    if 'model_inputs_v3' in out.resolve().parts:raise ValueError('Frozen V3 output target forbidden')
    demand_root=Path(args.demand_root)
    v3=ROOT/'output/sf_bikeshare/model_inputs_v3'
    minute=ROOT/'output/sf_bikeshare/demand_estimation_inputs_v3'
    inputs=[v3/'station_hour_observed.csv.gz',v3/'station.csv',v3/'opening_inventory_daily.csv',
            v3/'station_distances.csv',minute/'status.csv.gz',minute/'trip_events.csv.gz']
    before={p.relative_to(ROOT).as_posix():digest(p) for p in inputs}
    if args.build_demand:
        for case in ['historical','hybrid']:
            subprocess.run([sys.executable,'-B',str(ROOT/'sf_bikeshare/build_demand_minute.py'),
                '--case',case,'--hourly',str(inputs[0]),'--minute-dir',str(minute),
                '--output-dir',str(demand_root/case)],cwd=ROOT,check=True)
    reproduction=[]
    snapshots=ROOT/'output/sf_bikeshare/demand_estimation_cases_2026-11-22'
    for case,published in [('historical','historical_demand_station_hour.csv'),
                           ('hybrid','estimated_demand_station_hour_hybrid.csv')]:
        actual=demand_root/case/f'estimated_demand_station_hour_{case}.csv'
        a,b=pd.read_csv(actual),pd.read_csv(snapshots/published)
        pd.testing.assert_frame_equal(a,b,rtol=1e-12,atol=1e-12)
        numeric=a.select_dtypes('number').columns
        reproduction.append(dict(artifact=published,latest_producer=case,rows=len(a),
            maximum_numeric_difference=float(np.nanmax(abs(a[numeric]-b[numeric]))),
            canonical_lf_byte_identical=actual.read_bytes().replace(b'\r\n',b'\n')==
               (snapshots/published).read_bytes().replace(b'\r\n',b'\n'),
            interpretation='Same demand case; producer/validation handoff updated'))
    write_csv(pd.DataFrame(reproduction),out/'artifact_reconciliation.csv')
    for name in ['matched_validation.csv','validation_by_origin_group.csv']:
        a=pd.read_csv(demand_root/'historical'/name)
        b=pd.read_csv(ROOT/'output/sf_bikeshare/demand_case_comparison_2026-11-22'/name)
        keys=['group','test','side','rider','method'] if 'group' in a else ['test','side','rider']
        pd.testing.assert_frame_equal(a.sort_values(keys).reset_index(drop=True),
             b.sort_values(keys).reset_index(drop=True),rtol=1e-10,atol=1e-10,check_dtype=False)
        write_csv(a,out/name)
    coeff=coefficients(c)
    (out/'cost_configuration.json').write_bytes((json.dumps(dict(configuration=c,derived=coeff),indent=2)+'\n').encode())
    roads=pd.read_csv(v3/'station_distances.csv')
    travel=roads.pivot(index='from_station_id',columns='to_station_id',values='driving_minutes')
    distance_frame=roads.pivot(index='from_station_id',columns='to_station_id',values='road_distance_km')
    dates=args.dates or pd.date_range('2015-04-06','2015-04-19').strftime('%Y-%m-%d').tolist()
    records=[];routes=[];sensitivity=[];solver_records=[]
    for case in ['historical','hybrid']:
        for date in dates:
            print('MODEL',case,date,flush=True)
            reader=SimpleNamespace(stations=str(v3/'station.csv'),opening=str(v3/'opening_inventory_daily.csv'),
                distances=str(v3/'station_distances.csv'),
                demand=str(demand_root/case/f'estimated_demand_station_hour_{case}.csv'),date=date,hours=24)
            ids,caps,opening,sub,cas,returns,distance=read_day(reader)
            costs=unit_cost_matrix(distance,travel.reindex(index=ids,columns=ids).to_numpy(),c)
            if case=='historical' and date==dates[0]:
                pairs=roads[['from_station_id','to_station_id','road_distance_km','driving_minutes']].copy()
                costframe=pd.DataFrame(costs,index=ids,columns=ids)
                pairs['unit_cost_usd_per_bike']=[costframe.loc[i,j] for i,j in zip(pairs.from_station_id,pairs.to_station_id)]
                write_csv(pairs,out/'station_pair_costs.csv')
            kwargs=dict(fixed=c['fixed_usd_per_van_day'],handling=coeff['handling_usd_per_bike'],
                km_cost=coeff['vehicle_usd_per_km'],avg_load=c['average_load_bikes'],
                throughput=c['throughput_bikes_per_truck_hour'],max_neighbors=c['nearest_destinations'],
                member_value=c['member_allocated_value_usd'],casual_value=c['casual_allocated_value_usd'],
                failed_return_penalty=c['failed_return_penalty_usd'],unit_costs=costs)
            opt=solve_allocation(ids,caps,opening,sub,cas,returns,distance,max_trucks=c['max_trucks'],
                time_limit=args.time_limit,**kwargs)
            if opt.station_hour.empty:raise RuntimeError((case,date,opt.summary))
            rule=equal_occupancy_rule(ids,caps,opening,sub,cas,returns,distance,
                throughput=c['throughput_bikes_per_truck_hour'],max_neighbors=c['nearest_destinations'])
            summaries={}
            for name,jobs in [('no_rebalancing',None),('rule_based',rule),('optimized',opt.transfers)]:
                summary,tr,states=evaluate_policy(name,ids,caps,opening,sub,cas,returns,distance,jobs,**kwargs)
                if name=='optimized':
                    assert abs(summary['model_contribution_usd']-opt.summary['model_contribution_usd'])<.001
                    summary.update(solver_status=opt.summary['solver_status'],mip_gap=opt.summary['solver_gap'],
                                   solve_seconds=opt.summary['seconds'])
                summary.update(case=case,date=date,cost_scenario='updated_historical_proxies_with_driving_labor')
                summaries[name]=summary
                details=ROOT/'tmp/integrated_details'/case/date
                write_csv(tr,details/(name+'_transfers.csv'));write_csv(states,details/(name+'_station_hour.csv'))
                if name!='no_rebalancing' and not args.skip_routing:
                    rs,hours,events=check_routes(tr,ids,travel,hours=24,truck_capacity=c['truck_capacity_bikes'],
                        stop_setup_minutes=c['stop_setup_minutes'],
                        handling_minutes_per_operation=c['load_minutes_per_bike'])
                    if c['load_minutes_per_bike']!=c['unload_minutes_per_bike']:
                        raise ValueError('Current route checker requires equal load/unload operation time')
                    stage1=summary['movement_cost_usd']+summary['fixed_cost_usd']
                    priced=route_cost(rs,events,distance_frame,c,stage1)
                    row=dict(case=case,date=date,policy=name,route_status=rs['route_status'],
                        hours_not_certified=rs['hours_not_certified'],stage1_cost_usd=stage1,**priced)
                    row['conditional_route_repriced_contribution_usd']=(None if priced['stage2_cost_usd'] is None else
                        summary['trip_value_usd']-summary['return_failure_penalty_usd']-priced['stage2_cost_usd'])
                    routes.append(row)
                    write_csv(hours,details/(name+'_route_hours.csv'));write_csv(events,details/(name+'_route_events.csv'))
            base=summaries['no_rebalancing']
            for row in summaries.values():
                row['additional_contribution_usd']=row['model_contribution_usd']-base['model_contribution_usd']
                row['additional_served_pickups']=row['served_pickups']-base['served_pickups']
                records.append(row)
            solver_records.append(dict(case=case,date=date,summary=opt.summary))
            write_csv(pd.DataFrame(records),out/'daily_policy_comparison.csv')
            if routes:write_csv(pd.DataFrame(routes),out/'conditional_route_comparison.csv')
            print('DONE',case,date,'gain',summaries['optimized']['additional_contribution_usd'],
                  'gap',opt.summary['solver_gap'],flush=True)
            if args.extra_sensitivity and date==dates[0]:
                specs=[('equal_service_budget',dict(objective_mode='min_failed_requests',
                        redistribution_budget=c['service_budget_usd'])),
                       ('terminal_stock',dict(end_stock_at_least_opening=True))]
                for label,extra in specs:
                    r=solve_allocation(ids,caps,opening,sub,cas,returns,distance,
                        max_trucks=c['max_trucks'],time_limit=args.time_limit,**kwargs,**extra)
                    sensitivity.append(dict(case=case,date=date,scenario=label,**r.summary))
                write_csv(pd.DataFrame(sensitivity),out/'additional_sensitivity.csv')
    assert all(digest(ROOT/name)==value for name,value in before.items())
    manifest=dict(status='TEMPORARY_INTEGRATION_NOT_MAIN_MERGE',dates=dates,observed_inputs_sha256=before,
        observed_inputs_unchanged=True,software=dict(python=sys.version,numpy=np.__version__,
            pandas=pd.__version__,scipy=scipy.__version__),solver_time_limit_seconds=args.time_limit,
        raw_pr2_head='169043a843d4f67cf9ca3381d0d37be5a633c822',
        raw_pr1_head='244dda807805acbd28b33c56292e6eecb1de936a',
        model_cases=2,artifact_versions_compared=3,policy_evaluations=len(records),
        extra_sensitivity=sensitivity,solver_runs=solver_records,
        code_sha256={p.name:digest(p) for p in (ROOT/'sf_bikeshare').glob('*.py')},
        caveats=['Previously explored validation dates, not sealed-test claims.',
                 'Routes conditional; unknown fees excluded; all five robustness cases not evaluated.',
                 'Original main and upstream PRs remain unmerged.'])
    (out/'run_manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    print('COMPLETE',len(records),'policy evaluations; frozen observed inputs unchanged',flush=True)


if __name__=='__main__':main()
