"""Replay/recheck SAVED Carlo re-solved plans, never Joohee's missing exact plans.

No allocation MILP is solved. Default verifies the published evidence; --write-audit
creates the comparison, route summary and manifest after all checks pass.
"""
import argparse
import hashlib
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
from hj_optimization_model import read_day
from hj_policy_routing import evaluate_policy,check_routes
from integration_costs import coefficients,unit_cost_matrix,route_cost

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'output/sf_bikeshare'
OUT=DATA/'routing_evidence_2026-11-22'


def read_frame(path):
    try:return pd.read_csv(path)
    except pd.errors.EmptyDataError:return pd.DataFrame()


def compare_frames(a,b):
    if a.empty and b.empty:return
    # Compare CSV semantics: empty presentation cells round-trip as missing.
    a=pd.read_csv(StringIO(a.to_csv(index=False)))
    b=pd.read_csv(StringIO(b.to_csv(index=False)))
    pd.testing.assert_frame_equal(a,b,check_dtype=False,atol=1e-4,rtol=1e-7)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--write-audit',action='store_true')
    args=ap.parse_args()
    source=pd.read_csv(OUT/'source_daily_policy_comparison.csv')
    original_routes=pd.read_csv(OUT/'source_conditional_route_comparison.csv')
    configuration=json.loads((OUT/'source_cost_configuration.json').read_text())
    c,k=configuration['configuration'],configuration['derived']
    prior=json.loads((OUT/'source_run_manifest.json').read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    for name,value in prior['observed_inputs_sha256'].items():assert sha(ROOT/name)==value,name
    comparisons=[];checks=[]
    roads=pd.read_csv(DATA/'model_inputs_v3/station_distances.csv')
    travel=roads.pivot(index='from_station_id',columns='to_station_id',values='driving_minutes')
    distances=roads.pivot(index='from_station_id',columns='to_station_id',values='road_distance_km')
    report_files={'historical':'historical_demand_station_hour.csv',
                  'hybrid':'estimated_demand_station_hour_hybrid.csv'}
    for case in ['historical','hybrid']:
        report=pd.read_csv(DATA/f'optimization_14days_2026-11-22/{case}_daily_policy_comparison.csv')
        for date in prior['dates']:
            print('CHECK',case,date,flush=True)
            v3=DATA/'model_inputs_v3'
            reader=SimpleNamespace(stations=v3/'station.csv',opening=v3/'opening_inventory_daily.csv',
                distances=v3/'station_distances.csv',date=date,hours=24,
                demand=DATA/'demand_estimation_cases_2026-11-22'/report_files[case])
            ids,caps,opening,sub,cas,returns,distance=read_day(reader)
            matrix=unit_cost_matrix(distance,travel.reindex(index=ids,columns=ids).to_numpy(),c)
            baseline=source[source['case'].eq(case)&source.date.eq(date)&source.policy.eq('no_rebalancing')].iloc[0]
            for policy in ['optimized','rule_based']:
                folder=OUT/case/date
                transfers=read_frame(folder/f'{policy}_transfers.csv')
                summary,_,_=evaluate_policy(policy,ids,caps,opening,sub,cas,returns,distance,transfers,
                    throughput=c['throughput_bikes_per_truck_hour'],max_neighbors=c['nearest_destinations'],
                    fixed=c['fixed_usd_per_van_day'],handling=k['handling_usd_per_bike'],
                    km_cost=k['vehicle_usd_per_km'],avg_load=c['average_load_bikes'],
                    member_value=c['member_allocated_value_usd'],casual_value=c['casual_allocated_value_usd'],
                    failed_return_penalty=c['failed_return_penalty_usd'],unit_costs=matrix)
                old=source[source['case'].eq(case)&source.date.eq(date)&source.policy.eq(policy)].iloc[0]
                for field in ['served_pickups','failed_returns','bikes_moved','trip_value_usd',
                              'movement_cost_usd','fixed_cost_usd','model_contribution_usd']:
                    assert abs(summary[field]-old[field])<.002,(case,date,policy,field)
                route,hours,events=check_routes(transfers,ids,travel,hours=24,
                    truck_capacity=c['truck_capacity_bikes'],stop_setup_minutes=c['stop_setup_minutes'],
                    handling_minutes_per_operation=c['load_minutes_per_bike'])
                compare_frames(hours,read_frame(folder/f'{policy}_route_hours.csv'))
                compare_frames(events,read_frame(folder/f'{policy}_route_events.csv'))
                old_route=original_routes[original_routes['case'].eq(case)&original_routes.date.eq(date)
                    &original_routes.policy.eq(policy)].iloc[0]
                assert route['route_status']==old_route.route_status
                stage1=summary['movement_cost_usd']+summary['fixed_cost_usd']
                priced=route_cost(route,events,distances,c,stage1)
                active_cost=paid_gain=active_gain=None
                if priced['stage2_cost_usd'] is not None:
                    assert abs(priced['stage2_cost_usd']-old_route.stage2_cost_usd)<.002
                    active_cost=(0. if summary['bikes_moved']==0 else c['fixed_usd_per_van_day']+
                        k['loaded_wage_usd_per_hour']*priced['active_hours']+
                        k['vehicle_usd_per_km']*priced['route_distance_km']+c['additional_direct_fees_usd'])
                    gross=summary['trip_value_usd']-summary['return_failure_penalty_usd']-baseline.model_contribution_usd
                    paid_gain=gross-priced['stage2_cost_usd'];active_gain=gross-active_cost
                reported=report[report.date.eq(date)&report.policy.eq(policy)].iloc[0]
                comparisons.append(dict(case=case,date=date,policy=policy,
                    report_bikes_moved=reported.bikes_moved,resolved_bikes_moved=summary['bikes_moved'],
                    bike_totals_match=bool(abs(reported.bikes_moved-summary['bikes_moved'])<1e-5),
                    exact_report_plan_verified=False,
                    scope='Daily totals comparison only; exact report transfer rows unavailable'))
                checks.append(dict(case=case,date=date,policy=policy,bikes_moved=summary['bikes_moved'],
                    active_day=summary['bikes_moved']>0,route_status=route['route_status'],
                    hours_not_certified=route['hours_not_certified'],exact_report_plan_verified=False,
                    stage1_additional_contribution_usd=summary['model_contribution_usd']-baseline.model_contribution_usd,
                    productive_activity_route_cost_usd=active_cost,
                    paid_span_additional_contribution_usd=paid_gain,
                    productive_activity_additional_contribution_usd=active_gain,**priced))
    a,b=pd.DataFrame(comparisons),pd.DataFrame(checks)
    assert len(a)==len(b)==56
    historical=a[a['case'].eq('historical')&a.policy.eq('optimized')]
    assert historical[~historical.bike_totals_match].date.tolist()==[
        '2015-04-06','2015-04-08','2015-04-15','2015-04-16','2015-04-17']
    assert a[a['case'].eq('historical')&a.policy.eq('rule_based')].bike_totals_match.all()
    rows=[]
    for (case,policy),g in b.groupby(['case','policy']):
        passed=g.route_status.eq('conditional_timing_capacity_precedence_pass')
        p=g[passed]
        rows.append(dict(case=case,policy=policy,calendar_days=len(g),
            active_days=int(g.active_day.sum()),no_move_days=int((~g.active_day).sum()),
            conditional_pass_days=int(passed.sum()),active_conditional_pass_days=int((passed&g.active_day).sum()),
            unverified_days=int((~passed).sum()),
            stage1_gain_same_priced_days_usd=p.stage1_additional_contribution_usd.sum(),
            productive_activity_gain_usd=p.productive_activity_additional_contribution_usd.sum(),
            paid_span_gain_usd=p.paid_span_additional_contribution_usd.sum()))
    aggregate=pd.DataFrame(rows)
    original=pd.read_csv(DATA/'integration_review_2026-11-22/aggregate_route_comparison.csv')
    for row in aggregate.itertuples(index=False):
        old=original[original['case'].eq(row.case)&original.policy.eq(row.policy)].iloc[0]
        assert row.conditional_pass_days==old.conditionally_priced_days
        assert abs(row.productive_activity_gain_usd-old.productive_time_additional_contribution_usd)<.002
        assert abs(row.paid_span_gain_usd-old.paid_span_additional_contribution_usd)<.002
    outputs={'schedule_comparison.csv':a,'route_day_summary.csv':b,'aggregate_recheck.csv':aggregate}
    if args.write_audit:
        for name,frame in outputs.items():frame.to_csv(OUT/name,index=False,lineterminator='\n')
        manifest=dict(status='SAVED_RESOLVED_PLANS_REPLAYED_AND_ROUTE_RECHECKED_NOT_REPORT_CERTIFICATES',
            allocation_resolves_executed=0,exact_report_plans_verified=0,route_days_rechecked=56,
            saved_detail_files=168,checker_sha256=sha(Path(__file__)),
            source_run='integration_review_2026-11-22; saved transfers and routes, unchanged allocation decisions',
            cost_caveat='Proxy route costs; active time includes travel, loading/unloading and setup; paid span includes gaps, not a certified shift.',
            files={p.relative_to(OUT).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p))
                for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json'})
        (OUT/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    else:
        for name,frame in outputs.items():compare_frames(frame,pd.read_csv(OUT/name))
        manifest=json.loads((OUT/'manifest.json').read_text())
        for name,info in manifest['files'].items():assert sha(OUT/name)==info['sha256'],name
    print(aggregate.to_string(index=False))
    print('PASS saved-plan replay and route recheck. No MILP allocation re-solved; no exact Joohee report plan certified.')


if __name__=='__main__':main()
