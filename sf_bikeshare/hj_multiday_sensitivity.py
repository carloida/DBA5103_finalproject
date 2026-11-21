#!/usr/bin/env python3
r"""DBA5103 multi-day policies, cost sensitivity, throughput and routing audit.

Uses the existing hj_optimization_model.py and hj_policy_routing.py, with the
same input data and assumptions. Outputs CSV/JSON and a draft findings memo.
All results are Stage-1 retrospective scenarios, not realized operator profit.

Windows CMD, from repository root, activated venv:
  python sf_bikeshare\hj_multiday_sensitivity.py --self-test
  python sf_bikeshare\hj_multiday_sensitivity.py
  python sf_bikeshare\hj_multiday_sensitivity.py --dates 2015-04-06 2015-04-11 --time-limit 30

The four default dates are illustrative, NOT a clean holdout or a representative
statistical sample. Optional re-optimization experiments apply to the first date only.
The default run includes multi-day fixed-schedule cost sensitivity and routing
checks. Add --run-throughput-reoptimization to reoptimize 10/20 bikes/hour;
--run-cost-reoptimization may be computationally expensive.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from hj_optimization_model import read_day, solve_allocation
from hj_policy_routing import equal_occupancy_rule, evaluate_policy, check_routes

BASE_COST = dict(fixed=60.0, handling=1.0, km_cost=0.30, avg_load=15.0)
BASE_OTHER = dict(member_value=0.88, casual_value=4.50, failed_return_penalty=0.88)
COST_SCENARIOS = {
    'low': dict(fixed=30.0, handling=0.50, km_cost=0.20, avg_load=15.0),
    'base': BASE_COST,
    'high': dict(fixed=90.0, handling=1.50, km_cost=0.40, avg_load=15.0),
}
DEFAULT_DATES = ['2015-04-06','2015-04-10','2015-04-11','2015-04-15']


def write_csv(frame:pd.DataFrame, path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    frame.to_csv(path,index=False)


def load_day(date,args):
    reader=SimpleNamespace(stations=args.stations,opening=args.opening,
        demand=args.demand,distances=args.distances,date=date,hours=24)
    return read_day(reader)


def evaluate_three(date,arrays,args,out, *, save_detail=True):
    ids,caps,opening,sub,cas,returns,distance=arrays
    no=None
    rule=equal_occupancy_rule(ids,caps,opening,sub,cas,returns,distance,
                               throughput=args.throughput,max_neighbors=args.neighbors,
                               tolerance=args.occupancy_tolerance)
    kwargs=dict(**BASE_COST, **BASE_OTHER,throughput=args.throughput,max_neighbors=args.neighbors)
    opt=solve_allocation(ids,caps,opening,sub,cas,returns,distance,
                          fixed=BASE_COST['fixed'],handling=BASE_COST['handling'],
                          km_cost=BASE_COST['km_cost'],avg_load=BASE_COST['avg_load'],
                          throughput=args.throughput,max_neighbors=args.neighbors,
                          max_trucks=1,time_limit=args.time_limit,
                          member_value=BASE_OTHER['member_value'],
                          casual_value=BASE_OTHER['casual_value'],
                          failed_return_penalty=BASE_OTHER['failed_return_penalty'])
    if opt.station_hour.empty:
        raise RuntimeError(f'No solver incumbent for {date}: {opt.summary}')
    raw={'no_rebalancing':no,'rule_based':rule,'optimized':opt.transfers}
    results={}
    for pol,transfers in raw.items():
        summary,tr,stock=evaluate_policy(pol,ids,caps,opening,sub,cas,returns,distance,
                                         transfers,**kwargs)
        summary.update(date=date,solver_gap=opt.summary.get('solver_gap') if pol=='optimized' else None,
                        solver_status=opt.summary.get('solver_status') if pol=='optimized' else None,
                        optimization_seconds=opt.summary.get('seconds') if pol=='optimized' else None)
        results[pol]=(summary,tr,stock)
        if save_detail:
            prefix=out/f'{date}_{pol}'
            write_csv(tr,prefix.with_name(prefix.name+'_transfers.csv'))
            write_csv(stock,prefix.with_name(prefix.name+'_station_hour.csv'))
    replay=results['optimized'][2].merge(
        opt.station_hour[['station_id','hour','served_pickups','closing_stock','failed_returns']],
        on=['station_id','hour'],suffixes=('_replay','_solver'),validate='one_to_one')
    err=max(float(np.max(np.abs(replay[k+'_replay']-replay[k+'_solver'])))
            for k in ('served_pickups','closing_stock','failed_returns'))
    if err>1e-3:raise AssertionError(f'Independent replay differs from solver by {err} on {date}')
    return results,arrays,opt.summary,err


def calculate_break_even(base,opt, km_cost=0.30, avg_load=15.0, handling=1., penalty=.88):
    """Break-even for an UNCHANGED Stage-1 transfer schedule (not reoptimized)."""
    move=float(opt['bikes_moved'])
    if move<=0:return {'activation_cost_break_even_usd':None,
                         'handling_break_even_usd_per_bike':None,
                         'interpretation':'No truck activated in this solution'}
    benefit=(float(opt['trip_value_usd'])-float(base['trip_value_usd'])
              +penalty*(float(base['failed_returns'])-float(opt['failed_returns'])))
    distance_component=float(opt['movement_cost_usd'])-handling*move
    be_fixed=benefit-float(opt['movement_cost_usd'])
    be_handling=(benefit-float(opt['fixed_cost_usd'])-distance_component)/move
    return {'gross_incremental_benefit_usd':round(benefit,5),
            'activation_cost_break_even_usd':round(be_fixed,5),
            'handling_break_even_usd_per_bike':round(be_handling,5),
            'variable_distance_component_usd':round(distance_component,5),
            'interpretation':'Fixed Stage-1 allocation only; reoptimization can change this threshold'}


def routing_check(date, policies, ids, drive, out, args):
    records=[]
    for setup in args.setup_minutes:
        for pol in ('rule_based','optimized'):
            summary,transfers,_=policies[pol]
            route,hours,events=check_routes(transfers,ids,drive,hours=24,
                      truck_capacity=args.truck_capacity,
                      stop_setup_minutes=setup,
                      handling_minutes_per_operation=args.handling_minutes,
                      max_jobs=args.max_jobs)
            records.append({'date':date,'policy':pol,'stop_setup_minutes':setup,
                'route_status':route['route_status'],
                'hours_with_transfers':route['hours_with_transfers'],
                'hours_not_certified':route['hours_not_certified'],
                'uncertified_hours':','.join(map(str,route['not_certified_hours'])),
                'conditional_only':True})
            prefix=out/f'{date}_{pol}_setup{str(setup).replace(".","p")}'
            write_csv(hours,prefix.with_name(prefix.name+'_routing_hours.csv'))
            if not events.empty:
                write_csv(events,prefix.with_name(prefix.name+'_routing_events.csv'))
    return records


def reprice_fixed_transfers(date, pol, arrays, transfers, scenario, parameters, args):
    ids,caps,opening,sub,cas,returns,distance=arrays
    kwargs=dict(**parameters, **BASE_OTHER,throughput=args.throughput,max_neighbors=args.neighbors)
    result,_,_=evaluate_policy(pol,ids,caps,opening,sub,cas,returns,distance,transfers,**kwargs)
    return {'date':date,'policy':pol,'scenario':scenario,'analysis':'fixed_schedule_repricing',
            **{k:float(parameters[k]) for k in BASE_COST},
            'contribution_usd':result['model_contribution_usd'],
            'bikes_moved':result['bikes_moved'],
            'served_pickups':result['served_pickups'],
            'failed_returns':result['failed_returns']}


def reoptimize_one_day(date, arrays, args):
    ids,caps,opening,sub,cas,returns,distance=arrays
    cases=[]
    jobs=[]
    if args.run_cost_reoptimization:
        jobs.extend([('cost_low',COST_SCENARIOS['low'],args.throughput),('cost_high',COST_SCENARIOS['high'],args.throughput)])
    if args.run_throughput_reoptimization:
        jobs.extend([('throughput_low',BASE_COST,10.0),('throughput_high',BASE_COST,20.0)])
    for name,pars,tp in jobs:
        # The base case is already solved in the multi-day comparison.
        ans=solve_allocation(ids,caps,opening,sub,cas,returns,distance,
                      **pars,**BASE_OTHER,throughput=tp,max_neighbors=args.neighbors,
                      max_trucks=1,time_limit=args.time_limit)
        record={'date':date,'scenario':name,'throughput':tp,
                **{k:float(v) for k,v in pars.items()},
                'status':ans.summary.get('solver_status'),
                'gap':ans.summary.get('solver_gap'),
                'seconds':ans.summary.get('seconds'),
                'bikes_moved':ans.summary.get('bikes_moved'),
                'served_pickups':ans.summary.get('served_pickups'),
                'failed_returns':ans.summary.get('failed_returns'),
                'contribution_usd':ans.summary.get('model_contribution_usd')}
        cases.append(record)
        print(f"  re-optimization {name}: status={record['status']} gap={record['gap']} moved={record['bikes_moved']} contribution={record['contribution_usd']}",flush=True)
    return cases


def summary_memo(daily, cost, reopt, routing, bes, args):
    d=daily.copy()
    p=d.pivot(index='date',columns='policy',values='model_contribution_usd')
    m=d.pivot(index='date',columns='policy',values='unmet_pickups')
    v=(p['optimized']-p['no_rebalancing'])
    rel=(1-m['optimized']/m['no_rebalancing']).replace([np.inf,-np.inf],np.nan)
    rows=['# DBA5103: Draft Section 6 and Section 7 results (exploratory)', '',
          '> **Status:** computational Stage 1 scenarios, not actual financial performance. All numerical results use provisional costs and retrospective estimated demand; routes are not fully certified.', '',
          '## Section 6 — Results and comparison', '',
          f"The analysis evaluated {len(p)} selected days ({', '.join(p.index)}), each with 34 stations and 24 hourly periods. The same midnight inventory, estimated pickup and return demand, station capacities and provisional cost assumptions were applied to the no-rebalancing, equal-occupancy heuristic and optimized policies. The latter solves a mixed-integer program with the five-nearest-destination restriction per origin and a one-truck, {args.throughput:g}-bike/hour throughput constraint.", '',
          f"Across the selected days, the optimized Stage 1 solution improved modeled contribution relative to the no-rebalancing counterfactual by ${v.sum():,.2f} in total, or ${v.mean():,.2f} per day (range ${v.min():,.2f} to ${v.max():,.2f}). The unweighted mean reduction in estimated unmet pickups was {100*rel.mean():.1f}% across days. This is a descriptive calculation on selected dates, not a population estimate or out-of-sample policy performance claim.", '',
          'Daily modeled contribution (USD):', '',
          '| Date | No rebalancing | Equal-occupancy rule | Optimized | Increment vs no rebalance |',
          '|---|---:|---:|---:|---:|']
    for date in p.index:
        rows.append(f"| {date} | ${p.loc[date,'no_rebalancing']:,.2f} | ${p.loc[date,'rule_based']:,.2f} | ${p.loc[date,'optimized']:,.2f} | ${v.loc[date]:+,.2f} |")
    rows += ['', 'The equal-occupancy policy is a simple heuristic that moves whole bikes toward a common dock-occupancy fraction. It is not optimized for marginal demand or economic contribution. It is evaluated through the same station-hour stock and trip-service equations as the optimization, without assuming historic inventory is a no-rebalancing trajectory.', '',
             '## Section 7 — Sensitivity, routing and limitations', '',
             'For a **fixed optimized transfer schedule**, the break-even fixed truck activation cost is the extra allocated trip value plus the avoided return-failure penalty, less variable transfer costs. It is a schedule-specific accounting threshold and does not establish a global break-even tariff or cash profit.', '',
             '| Date | Fixed schedule: break-even daily truck charge | Break-even handling USD/bike |',
             '|---|---:|---:|']
    for z in bes:
        rows.append(f"| {z['date']} | ${z['activation_cost_break_even_usd']:,.2f} | ${z['handling_break_even_usd_per_bike']:,.3f} |" if pd.notna(z['activation_cost_break_even_usd']) else f"| {z['date']} | n/a | n/a |")
    if not routing.empty:
        c=routing[(routing.policy=='optimized')].pivot(index='date',columns='stop_setup_minutes',values='hours_not_certified')
        rows += ['', 'Conditional routing audit: hourly checks enforce transfer precedence, onboard capacity, estimated travel time and handling/setup assumptions, with an open initial location and sequential hour chaining. Uncertified hours do not necessarily prove a full-day route impossible.', '',
                 '| Date | '+ ' | '.join(f'{z:g} min setup: uncertified hours' for z in c.columns)+' |',
                 '|---|'+'---:|'*len(c.columns)]
        for date in c.index:
            rows.append('| '+date+' | '+' | '.join(str(int(c.loc[date,z])) for z in c.columns)+' |')
    if not reopt.empty:
        labels=', '.join(reopt['scenario'].astype(str).tolist())
        rows += ['', f"On {args.dates[0]}, the following sensitivity cases were **reoptimized**: {labels}. Their solver statuses and MIP gaps are in `reoptimization_sensitivity.csv`. Other cost scenarios shown here reprice the fixed original schedules only."]
    rows += ['', '### Interpretation and limitations', '',
         '1. The retrospective own-hour availability adjustment uses observed arrivals from within the hour; it is **not** a prospective forecast. The two April validation weeks were already examined during method development and are not a sealed holdout.',
         '2. Estimated pickups and returns are fractional expected counts; the model uses proportional service by rider type. Returns are treated as fixed even when the policy blocks departures, so counterfactual network conservation is approximate.',
         '3. Stage 1 permits only each station’s five nearest destination arcs and assumes transfers arrive at the start of their assigned hour. Thus its MIP gap does not measure the gap to the unrestricted fleet-routing problem.',
         '4. The Stage 2 check does not enforce the exact minute of customer pickups, depot or daily shift/depot costs. Passing it is a **conditional** result, not full operational certification; no route-adjusted profit was estimated.',
         '5. Monetary quantities are allocated rider-pass values and scenario cost proxies, not observed marginal revenue or actual redistribution expenditure. The sensitivity ranges are illustrative rather than statistically calibrated.', '',
         '### Required before final report', '',
         'Confirm cost parameters and cite their sources; verify each solver status and gap; choose how to handle failed returns and in-transit rides; report routing failures explicitly; use any untouched held-out date set only after generating demand estimates without look-ahead.', '']
    return '\n'.join(rows)


def main():
    root=Path('output/sf_bikeshare')
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--dates',nargs='+',default=DEFAULT_DATES)
    p.add_argument('--time-limit',type=float,default=35.)
    p.add_argument('--throughput',type=float,default=15.)
    p.add_argument('--neighbors',type=int,default=5)
    p.add_argument('--occupancy-tolerance',type=float,default=0.10)
    p.add_argument('--truck-capacity',type=int,default=25)
    p.add_argument('--handling-minutes',type=float,default=1.0)
    p.add_argument('--setup-minutes',nargs='+',type=float,default=[2.0,1.0])
    p.add_argument('--max-jobs',type=int,default=8)
    p.add_argument('--run-throughput-reoptimization',action='store_true',help='Reoptimize 10 and 20 bikes/hour on the first date (base 15 already included)')
    p.add_argument('--run-cost-reoptimization',action='store_true',help='Reoptimize low/high cost assumptions on first date; these MILPs may solve slowly')
    p.add_argument('--skip-routes',action='store_true')
    base=root/'model_inputs_v3'
    p.add_argument('--stations',default=str(base/'station.csv'))
    p.add_argument('--opening',default=str(base/'opening_inventory_daily.csv'))
    p.add_argument('--distances',default=str(base/'station_distances.csv'))
    p.add_argument('--demand',default=str(root/'demand_estimation/estimated_demand_station_hour.csv'))
    p.add_argument('--out',default=str(root/'optimization/multiday'))
    args=p.parse_args()
    if args.self_test:
        x=dict(trip_value_usd=12.,failed_returns=1.,movement_cost_usd=3.,bikes_moved=2.,fixed_cost_usd=6.)
        b=dict(trip_value_usd=8.,failed_returns=3.)
        be=calculate_break_even(b,x,handling=1,penalty=.88)
        assert abs(be['activation_cost_break_even_usd']-2.76)<1e-9,be
        assert abs(be['handling_break_even_usd_per_bike']+0.62)<1e-9,be
        print('Self-test PASSED: frozen-schedule break-even arithmetic')
        return
    if not all(Path(z).exists() for z in [args.stations,args.opening,args.distances,args.demand]):
        raise FileNotFoundError('A data input is missing: run from the Git repository root, check --stations --opening --distances --demand')
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    distances=pd.read_csv(args.distances)
    driving=distances.pivot(index='from_station_id',columns='to_station_id',values='driving_minutes')
    daily=[];break_even=[];fixed_cost=[];route_all=[];reopt=[]
    first_arrays=None
    for date in args.dates:
        print(f'Running {date} ...',flush=True)
        arrays=load_day(date,args)
        cases,_,solver,replay_err=evaluate_three(date,arrays,args,out)
        base=cases['no_rebalancing'][0];op=cases['optimized'][0]
        for policy in ('no_rebalancing','rule_based','optimized'):
            s=dict(cases[policy][0]);s['replay_max_error']=replay_err if policy=='optimized' else None
            s['increment_vs_baseline_usd']=round(s['model_contribution_usd']-base['model_contribution_usd'],4)
            s['unmet_pickup_reduction_pct']=round(100*(1-s['unmet_pickups']/base['unmet_pickups']),3) if base['unmet_pickups']>0 else None
            daily.append(s)
        be=calculate_break_even(base,op);be['date']=date;break_even.append(be)
        for scenario,params in COST_SCENARIOS.items():
            for policy in ('no_rebalancing','rule_based','optimized'):
                fixed_cost.append(reprice_fixed_transfers(date,policy,arrays,
                                    cases[policy][1],scenario,params,args))
        if not args.skip_routes:
            route_all.extend(routing_check(date,cases,arrays[0],driving,out,args))
        print(f"  optimized {op['bikes_moved']} bikes, model Δ ${op['model_contribution_usd']-base['model_contribution_usd']:+.2f}, gap {solver.get('solver_gap')}, replay max-error {replay_err:.2g}",flush=True)
        if first_arrays is None:first_arrays=arrays
    write_csv(pd.DataFrame(daily),out/'daily_policy_comparison.csv')
    write_csv(pd.DataFrame(break_even),out/'break_even_fixed_schedule.csv')
    cost=pd.DataFrame(fixed_cost);write_csv(cost,out/'fixed_schedule_cost_sensitivity.csv')
    routing=pd.DataFrame(route_all)
    if not routing.empty:write_csv(routing,out/'routing_sensitivity.csv')
    if args.run_throughput_reoptimization or args.run_cost_reoptimization:
        print(f'Running requested reoptimization scenarios for {args.dates[0]} ...',flush=True)
        reopt=reoptimize_one_day(args.dates[0],first_arrays,args)
    repro=pd.DataFrame(reopt)
    if not repro.empty:write_csv(repro,out/'reoptimization_sensitivity.csv')
    memo=summary_memo(pd.DataFrame(daily),cost,repro,routing,break_even,args)
    (out/'draft_sections_6_7.md').write_text(memo,encoding='utf-8')
    summary={'dates':args.dates,'cost_scenarios':COST_SCENARIOS,'base_values':BASE_OTHER,
             'neighbors':args.neighbors,'throughput':args.throughput,'time_limit':args.time_limit,
             'stage1_only':True,'sequential_conditional_routing_only':True,
             'not_untouched_holdout':True,
             'sources':'Joo Hee §3.4 and §4; Carlo V3 inputs; earlier hj_optimization_model and hj_policy_routing scripts'}
    (out/'experiment_manifest.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print('Saved report-ready exploratory CSVs and draft to',out.resolve(),flush=True)

if __name__=='__main__':main()
