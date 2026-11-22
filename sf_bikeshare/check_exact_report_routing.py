"""Replay Joohee's exact historical report plans and validate supplied route certificates.

No allocation re-solve or route re-search. Default verifies published audit files;
--write-audit writes independent replay, route-cost and provenance outputs.
"""
import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
from hj_optimization_model import read_day
from hj_policy_routing import evaluate_policy,clean_transfers
from integration_costs import load_config,route_cost

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'output/sf_bikeshare'
OUT=DATA/'optimization_14days_2026-11-22'
DETAIL=OUT/'route_audit_historical'
PASS='timing_capacity_precedence_pass'


def read_events(path):
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def validate_certificate(transfers,hours,events,drive,setup):
    assert hours.hour.tolist()==list(range(24))
    previous_station=None;previous_finish=None;chain_broken=False
    for h in hours.itertuples(index=False):
        jobs=transfers[transfers.hour.eq(h.hour)].reset_index(drop=True)
        assert h.jobs==len(jobs) and h.bikes==jobs.bikes.sum()
        ev=events[events.hour.eq(h.hour)] if not events.empty else pd.DataFrame()
        if jobs.empty:
            assert h.status=='no_moves' and ev.empty
            continue
        if h.status not in (PASS,'independent_hour_pass_after_break'):
            assert ev.empty
            chain_broken=True
            continue
        assert len(ev)==2*len(jobs)
        local_station=None if chain_broken else previous_station
        local_finish=None if chain_broken else previous_finish
        picked=set();dropped=set();load=0
        for index,e in enumerate(ev.itertuples(index=False)):
            job=jobs.iloc[int(e.job_index)]
            assert e.bikes==job.bikes
            if e.event=='pickup':
                assert e.job_index not in picked and e.station_id==job.from_station_id
                picked.add(e.job_index);load+=e.bikes
            else:
                assert e.event=='dropoff' and e.job_index in picked and e.job_index not in dropped
                assert e.station_id==job.to_station_id
                dropped.add(e.job_index);load-=e.bikes
            assert -1e-8<=load<=25+1e-8
            travel=0. if local_station is None else float(drive.loc[int(local_station),int(e.station_id)])
            expected_arrival=max(h.hour*60,(h.hour*60 if local_finish is None else local_finish)+travel)
            expected_setup=setup if index==0 or local_station!=e.station_id else 0.
            assert abs(e.travel_minutes_from_previous-travel)<.002
            assert abs(e.arrival_minute_abs-expected_arrival)<.002
            assert abs(e.stop_setup_minutes-expected_setup)<.002
            assert abs(e.handling_minutes-e.bikes)<.002
            assert abs(e.finish_minute_abs-(e.arrival_minute_abs+expected_setup+e.bikes))<.002
            assert e.finish_minute_abs<=60*(h.hour+1)+.002
            local_station=e.station_id;local_finish=e.finish_minute_abs
        assert load==0 and picked==dropped==set(range(len(jobs)))
        if not chain_broken:
            previous_station=local_station;previous_finish=local_finish
    return dict(hours_with_transfers=int(hours.jobs.gt(0).sum()),
                uncertified_hours=int((~hours.status.isin(['no_moves',PASS])).sum()))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--write-audit',action='store_true');args=ap.parse_args()
    prepared=ROOT/'tmp/final_report_v2_review/source_manifest.json'
    source=(json.loads(prepared.read_text()) if args.write_audit and prepared.exists() else
            json.loads((OUT/'exact_plan_audit_manifest.json').read_text())['source'])
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(OUT/source['archive'])==source['archive_sha256']
    for name,value in source['files'].items():assert sha(ROOT/name)==value,name
    summary=pd.read_csv(OUT/'historical_daily_policy_comparison.csv')
    route_summary=pd.read_csv(OUT/'routing_sensitivity.csv')
    v3=DATA/'model_inputs_v3'
    roads=pd.read_csv(v3/'station_distances.csv')
    drive=roads.pivot(index='from_station_id',columns='to_station_id',values='driving_minutes')
    distances=roads.pivot(index='from_station_id',columns='to_station_id',values='road_distance_km')
    config=load_config(ROOT/'sf_bikeshare/integration_cost_config.json')
    assert config['fixed_usd_per_van_day']==60. and config['adopted_loaded_wage_usd_per_hour']==29.57
    assert config['fuel_usd_per_litre']==.882 and config['fuel_litres_per_100km']==16.8
    assert config['paid_time_basis']=='span' and config['additional_direct_fees_usd']==0.
    replay=[];routes=[]
    for date in sorted(summary.date.unique()):
        print('EXACT CHECK',date,flush=True)
        reader=SimpleNamespace(stations=v3/'station.csv',opening=v3/'opening_inventory_daily.csv',distances=v3/'station_distances.csv',
            demand=DATA/'demand_estimation_cases_2026-11-22/historical_demand_station_hour.csv.gz',date=date,hours=24)
        ids,caps,opening,sub,cas,returns,distance=read_day(reader)
        baseline=summary[summary.date.eq(date)&summary.policy.eq('no_rebalancing')].iloc[0]
        for policy in ['no_rebalancing','rule_based','optimized']:
            transfers=clean_transfers(pd.read_csv(DETAIL/f'{date}_{policy}_transfers.csv'),ids,24)
            evaluated,_,states=evaluate_policy(policy,ids,caps,opening,sub,cas,returns,distance,transfers,
                fixed=60.,handling=1.,km_cost=.30,avg_load=15.,throughput=15,max_neighbors=5,
                member_value=.88,casual_value=4.5,failed_return_penalty=.88)
            reported=summary[summary.date.eq(date)&summary.policy.eq(policy)].iloc[0]
            for field in ['bikes_moved','served_pickups','failed_returns','movement_cost_usd','fixed_cost_usd','trip_value_usd','model_contribution_usd']:
                assert abs(evaluated[field]-reported[field])<.001,(date,policy,field)
            original=pd.read_csv(DETAIL/f'{date}_{policy}_station_hour.csv')
            pd.testing.assert_frame_equal(states,original,check_dtype=False,atol=1e-5,rtol=1e-9)
            error=float(np.nanmax(np.abs(states.select_dtypes('number').to_numpy()-original.select_dtypes('number').to_numpy())))
            replay.append(dict(date=date,**evaluated,replay_max_error=error,reported_plan_replay_pass=True))
            if policy=='no_rebalancing':continue
            for setup in [1.,2.]:
                prefix=f'{date}_{policy}_setup{setup:.1f}'.replace('.', 'p')
                hours=pd.read_csv(DETAIL/f'{prefix}_routing_hours.csv')
                events=read_events(DETAIL/f'{prefix}_routing_events.csv')
                certificate=validate_certificate(transfers,hours,events,drive,setup)
                record=route_summary[route_summary.date.eq(date)&route_summary.policy.eq(policy)&route_summary.stop_setup_minutes.eq(setup)].iloc[0]
                assert certificate['hours_with_transfers']==record.hours_with_transfers
                assert certificate['uncertified_hours']==record.hours_not_certified
                passed=certificate['uncertified_hours']==0
                assert passed==(record.route_status=='conditional_timing_capacity_precedence_pass')
                stage1=evaluated['movement_cost_usd']+evaluated['fixed_cost_usd']
                priced=route_cost(dict(route_status=record.route_status),events,distances,config,stage1)
                active_cost=paid_gain=active_gain=None
                if passed:
                    active_cost=0. if events.empty else 60.+29.57*priced['active_hours']+(.14/1.609344+.882*.168)*priced['route_distance_km']
                    gross=evaluated['trip_value_usd']-evaluated['return_failure_penalty_usd']-baseline.model_contribution_usd
                    paid_gain=gross-priced['stage2_cost_usd'];active_gain=gross-active_cost
                routes.append(dict(date=date,policy=policy,stop_setup_minutes=setup,reported_plan_replay_pass=True,
                    bikes_moved=evaluated['bikes_moved'],transfer_instructions=len(transfers),**certificate,
                    route_status=record.route_status,productive_activity_cost_usd=active_cost,
                    productive_activity_increment_usd=active_gain,paid_span_increment_usd=paid_gain,**priced))
    a,b=pd.DataFrame(replay),pd.DataFrame(routes)
    op=b[b.policy.eq('optimized')&b.stop_setup_minutes.eq(1.)]
    assert len(a)==42 and len(b)==56
    assert op.hours_with_transfers.sum()==133 and op.uncertified_hours.sum()==0 and op.bikes_moved.sum()==766
    slow=b[b.policy.eq('optimized')&b.stop_setup_minutes.eq(2.)]
    assert slow.uncertified_hours.sum()==29 and slow.uncertified_hours.gt(0).sum()==3
    rule1=b[b.policy.eq('rule_based')&b.stop_setup_minutes.eq(1.)]
    rule2=b[b.policy.eq('rule_based')&b.stop_setup_minutes.eq(2.)]
    assert rule1.uncertified_hours.eq(0).sum()==3 and rule2.uncertified_hours.eq(0).sum()==1
    assert rule1.hours_with_transfers.sum()==249 and rule1.uncertified_hours.sum()==179
    stats=dict(replayed_policy_days=42,checked_route_cases=56,optimized_bikes=766,
        optimized_active_days=int(op.bikes_moved.gt(0).sum()),optimized_active_hours=133,
        setup1_optimized_uncertified_hours=0,setup2_optimized_uncertified_hours=29,
        setup2_optimized_uncertified_days=3,transfer_instructions=int(op.transfer_instructions.sum()),
        setup1_rule_pass_days=3,setup2_rule_pass_days=1,rule_active_hours=249,
        setup1_rule_uncertified_hours=179,
        bikes_per_transfer_instruction=float(766/op.transfer_instructions.sum()),
        optimized_productive_activity_cost_usd=float(op.productive_activity_cost_usd.sum()),
        optimized_productive_activity_increment_usd=float(op.productive_activity_increment_usd.sum()),
        optimized_paid_span_cost_usd=float(op.stage2_cost_usd.sum()),
        optimized_paid_span_increment_usd=float(op.paid_span_increment_usd.sum()))
    if args.write_audit:
        a.to_csv(OUT/'exact_plan_replay_checks.csv',index=False,lineterminator='\n')
        b.to_csv(OUT/'exact_plan_route_costs.csv',index=False,lineterminator='\n')
        manifest=dict(status='EXACT_REPORT_FIXED_PLANS_REPLAYED_AND_SUPPLIED_CERTIFICATES_CHECKED',source=source,
            checks=stats,allocation_resolves_executed=0,conditional_only=True,checker_sha256=sha(Path(__file__)),
            input_files={p.relative_to(ROOT).as_posix():sha(p) for p in [
                v3/'station.csv',v3/'opening_inventory_daily.csv',v3/'station_distances.csv',
                DATA/'demand_estimation_cases_2026-11-22/historical_demand_station_hour.csv.gz',
                OUT/'historical_daily_policy_comparison.csv',ROOT/'sf_bikeshare/integration_cost_config.json']},
            cost_scope='Proxy vehicle/wage costs; original hourly service held fixed; no depot/shift/customer-timing certificate',
            derived_files={n:sha(OUT/n) for n in ['exact_plan_replay_checks.csv','exact_plan_route_costs.csv']})
        (OUT/'exact_plan_audit_manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    else:
        manifest=json.loads((OUT/'exact_plan_audit_manifest.json').read_text())
        assert manifest['checker_sha256']==sha(Path(__file__))
        for name,value in manifest['input_files'].items():assert sha(ROOT/name)==value,name
        for name,value in manifest['derived_files'].items():assert sha(OUT/name)==value,name
        for key,value in stats.items():assert np.isclose(value,manifest['checks'][key]),key
    print(json.dumps(stats,indent=2))
    print('PASS exact report replay and conditional certificate checks; no allocation re-solve')


if __name__=='__main__':main()
