#!/usr/bin/env python3
r"""DBA5103: three-policy evaluation + one-truck routing feasibility audit.

Works alongside hj_optimization_model.py. Uses the same demand, stock conservation,
failed-return, cost and proportional subscriber/casual service assumptions.

The baseline is a *non-optimized*, supply-balancing heuristic: move integer bikes
from stations above the system's current occupancy ratio to stations below it,
respecting the same 5-nearest-arc and hourly throughput restrictions as Stage 1.

The route checker schedules each fixed arc transfer as a pickup-and-delivery job.
It uses exact precedence/capacity/time-window search for hours with <=max-jobs.
The open route has no depot or initial approach leg. Results are *conditional* on
estimated road times and handling/setup assumptions. They do not validate the
Stage-1 fiction that all delivered bikes are available at the start of the hour.

Run from repository root (Windows CMD, .venv activated):
  python sf_bikeshare\hj_policy_routing.py --self-test
  python sf_bikeshare\hj_policy_routing.py --date 2015-04-06 --hours 24

Requires: numpy, pandas, scipy (the latter required by hj_optimization_model.py).
"""
from __future__ import annotations

import argparse
import heapq
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from hj_optimization_model import read_day, relocation_cost_matrix

TRANSFER_COLUMNS = ['hour','from_station_id','to_station_id','bikes','unit_cost_usd']


def allowed_arcs(ids, distance, max_neighbors):
    n=len(ids)
    k=min(n-1,max(1,int(max_neighbors)))
    return {(int(ids[i]),int(ids[j])) for i in range(n)
            for j in [int(j) for j in np.argsort(distance[i]) if j!=i][:k]}


def clean_transfers(transfers, ids, hours, allowed=None):
    """Validate & aggregate the integer arc movements before applying any policy."""
    if transfers is None or len(transfers)==0:
        return pd.DataFrame(columns=TRANSFER_COLUMNS)
    d=transfers.copy()
    required={'hour','from_station_id','to_station_id','bikes'}
    if not required.issubset(d.columns):
        raise ValueError('Transfer CSV missing columns: '+str(sorted(required-set(d.columns))))
    for col in required:
        d[col]=pd.to_numeric(d[col],errors='raise')
    if d[['hour','from_station_id','to_station_id','bikes']].isna().any().any():
        raise ValueError('Null transfer values')
    for col in ['hour','from_station_id','to_station_id','bikes']:
        if not np.all(np.isclose(d[col],np.round(d[col]),atol=1e-5)):
            raise ValueError(f'{col} must contain integer quantities')
        d[col]=d[col].round().astype(int)
    d=d[d.bikes>0].copy()
    ids_set=set(map(int,ids))
    for rec in d.itertuples(index=False):
        if not (0<=rec.hour<hours):raise ValueError(f'Hour out of range: {rec.hour}')
        if (rec.from_station_id not in ids_set or rec.to_station_id not in ids_set
            or rec.from_station_id==rec.to_station_id):
            raise ValueError(f'Invalid station pair {rec.from_station_id}->{rec.to_station_id}')
        if allowed is not None and (rec.from_station_id,rec.to_station_id) not in allowed:
            raise ValueError(f'Transfer outside restricted arcs {rec.from_station_id}->{rec.to_station_id}')
    d=d.groupby(['hour','from_station_id','to_station_id'],as_index=False).bikes.sum()
    return d.assign(unit_cost_usd=np.nan)[TRANSFER_COLUMNS].sort_values(
        ['hour','from_station_id','to_station_id']).reset_index(drop=True)


def _one_hour_sim(b, caps, demand_sub, demand_cas, returns, jobs, id_to_ix):
    q=b.copy()
    for orig,dest,k in jobs:
        q[id_to_ix[orig]]-=k
        q[id_to_ix[dest]]+=k
    if np.min(q)<-1e-7 or np.max(q-caps)>1e-7:
        raise ValueError('Transfer violates station stock/capacity at start of hour')
    dem=demand_sub+demand_cas
    served=np.minimum(q,dem)
    failed=np.maximum(0,q-served+returns-caps)
    after=q-served+returns-failed
    if np.min(after)<-1e-6 or np.max(after-caps)>1e-6:
        raise AssertionError('Bike conservation inconsistency')
    return q,served,failed,after


def evaluate_policy(name, ids, caps, opening, sub, cas, returns, distance,
                    transfers, *, max_neighbors=5, throughput=15,
                    fixed=60., handling=1., km_cost=.30, avg_load=15.,
                    member_value=.88, casual_value=4.5,
                    failed_return_penalty=.88, unit_costs=None):
    """Exact deterministic evaluator for existing Stage-1 convention, no optimizer."""
    if avg_load<=0:raise ValueError('avg_load must be positive')
    ids=list(map(int,ids));n=len(ids);hours=sub.shape[1]
    costs=relocation_cost_matrix(distance,handling,km_cost,avg_load,unit_costs)
    allowed=allowed_arcs(ids,distance,max_neighbors)
    d=clean_transfers(transfers,ids,hours,allowed)
    id_to_ix={sid:i for i,sid in enumerate(ids)}
    rows=[];b=np.array(opening,dtype=float).copy()
    moved=move_cost=total_value=total_failed=total_served=0.
    for t in range(hours):
        dhr=d[d.hour.eq(t)]
        jobs=[(int(x.from_station_id),int(x.to_station_id),int(x.bikes))
              for x in dhr.itertuples(index=False)]
        if sum(k for _,_,k in jobs)>throughput+1e-6:
            raise ValueError(f'Hour {t}: exceeded {throughput} bike/hour throughput')
        outbound=np.zeros(n)
        for o,_,k in jobs:outbound[id_to_ix[o]]+=k
        if np.any(outbound>b+1e-7):
            raise ValueError(f'Hour {t}: loading more bikes than hour opening stock')
        q,served,failed,after=_one_hour_sim(b,caps,sub[:,t],cas[:,t],returns[:,t],jobs,id_to_ix)
        demand=sub[:,t]+cas[:,t]
        ms=np.divide(sub[:,t],demand,out=np.zeros(n),where=demand>0)
        member=served*ms
        casual=served-member
        vals=member*member_value+casual*casual_value
        for i in range(n):
            rows.append({'station_id':ids[i],'hour':t,'opening_stock':b[i],
                         'post_transfer_stock':q[i], 'pickup_demand':demand[i],
                         'served_pickups':served[i], 'unmet_pickups':demand[i]-served[i],
                         'failed_returns':failed[i], 'return_demand':returns[i,t],
                         'closing_stock':after[i]})
        total_value+=float(vals.sum());total_served+=float(served.sum());total_failed+=float(failed.sum())
        moved+=sum(k for _,_,k in jobs)
        move_cost+=sum(k*costs[id_to_ix[o],id_to_ix[j]]
                       for o,j,k in jobs)
        b=after
    fixedcost=fixed*(1 if moved else 0)
    penalty=total_failed*failed_return_penalty
    d['unit_cost_usd']=[round(float(costs[id_to_ix[int(o)],id_to_ix[int(j)]]),4)
                        for o,j in zip(d.from_station_id,d.to_station_id)]
    summary={'policy':name,'horizon_hours':hours,'demand_pickups':round(float((sub+cas).sum()),5),
             'served_pickups':round(total_served,5),'unmet_pickups':round(float((sub+cas).sum())-total_served,5),
             'attempted_returns':round(float(returns.sum()),5),'failed_returns':round(total_failed,5),
             'bikes_moved':round(moved,5),'transfer_instructions':len(d),
             'trucks_charged':1 if moved else 0, 'trip_value_usd':round(total_value,4),
             'movement_cost_usd':round(move_cost,4),'fixed_cost_usd':round(fixedcost,4),
             'return_failure_penalty_usd':round(penalty,4),
             'model_contribution_usd':round(total_value-move_cost-fixedcost-penalty,4),
             'route_feasibility_checked':False,
             'interpretation':'Same-hour aggregate inventory, fixed estimated returns; provisional cost assumptions'}
    return summary,d,pd.DataFrame(rows)


def equal_occupancy_rule(ids,caps,opening,sub,cas,returns,distance,
                         *,throughput=15,max_neighbors=5,tolerance=.10):
    """Greedy policy towards common occupancy percentage, no MILP and no route information.

    Above/below average station share by >= tolerance is considered unbalanced;
    only move INTEGER bikes; choose the most underfull receiver first and its nearest
    overfull donor among the same allowed arcs as the MILP. No look-ahead.
    """
    ids=list(map(int,ids)); n=len(ids);hours=sub.shape[1]
    allowed=allowed_arcs(ids,distance,max_neighbors)
    pos={sid:i for i,sid in enumerate(ids)}
    b=np.array(opening,dtype=float).copy();rows=[]
    for t in range(hours):
        q=b.copy();left=int(math.floor(throughput+1e-8))
        avg=float(np.sum(q)/np.sum(caps))
        donors={i:max(0,int(np.floor(q[i]-(avg+tolerance)*caps[i]+1e-9))) for i in range(n)}
        recipients={j:max(0,int(np.floor((avg-tolerance)*caps[j]-q[j]+1e-9))) for j in range(n)}
        # Greedy order stable: largest occupancy shortfall first, nearest eligible donor.
        while left>0:
            choices=[]
            for j in range(n):
                if recipients[j]<=0:continue
                for i in range(n):
                    if donors[i]<=0 or (ids[i],ids[j]) not in allowed:continue
                    qty=min(left,donors[i],recipients[j],
                            int(np.floor(q[i]+1e-8)),int(np.floor(caps[j]-q[j]+1e-8)))
                    if qty>0:
                        choices.append((-float(recipients[j]/caps[j]),float(distance[i,j]),-qty,j,i,qty))
            if not choices:break
            choices.sort()
            _,_,_,j,i,qty=choices[0]
            rows.append({'hour':t,'from_station_id':ids[i],'to_station_id':ids[j],
                         'bikes':qty})
            q[i]-=qty;q[j]+=qty;donors[i]-=qty;recipients[j]-=qty;left-=qty
        d_t=[(r['from_station_id'],r['to_station_id'],r['bikes']) for r in rows if r['hour']==t]
        _,_,_,b=_one_hour_sim(b,caps,sub[:,t],cas[:,t],returns[:,t],d_t,pos)
    return clean_transfers(pd.DataFrame(rows) if rows else None,ids,hours,allowed)


@dataclass(frozen=True)
class Job:
    origin: int
    dest: int
    bikes: int


def route_hour_exact(jobs, drive, *, hour, capacity=25,
                     setup_per_stop=2.0, handling_per_bike=1.0,
                     previous_station:Optional[int]=None,previous_abs_finish:Optional[float]=None,
                     max_jobs=8,window_minutes=60.):
    """Earliest-finish exact DP for one truck, unsplittable transfer jobs.

    Driver starts at first pickup for first active hour (open route, no depot).
    Later hours account for repositioning from the previous hour's last stop.
    Returns 'not_certified' if there are too many jobs or no permissible route.
    """
    m=len(jobs);start=hour*60.;deadline=start+window_minutes
    if not m:
        return {'status':'no_moves','events':[], 'finish':previous_abs_finish,
                'end_station':previous_station,'drive_min':0.,'setup_min':0.,'handling_min':0.}
    if m>max_jobs:
        return {'status':'too_many_jobs_for_exact_check','events':[],'job_count':m}
    if any(j.bikes>capacity for j in jobs):
        return {'status':'job_exceeds_truck_capacity','events':[],'job_count':m}
    if any(j.bikes<=0 for j in jobs):raise ValueError('Invalid job amount')
    allmask=(1<<m)-1
    # State: picked/delivered bitmasks and index of most recent action.
    # Each action is (pickup=0/drop=1,job-index), with index 0..2m-1.
    init=(0,0,-1)
    best={init:start};parents={};heap=[(start,init)]
    solved=None
    while heap:
        tm,state=heapq.heappop(heap)
        if tm>best[state]+1e-9:continue
        pick,drop,last=state
        if drop==allmask:
            solved=state;break
        current_load=sum(job.bikes for k,job in enumerate(jobs)
                         if (pick>>k&1) and not(drop>>k&1))
        last_station=(previous_station if last==-1 else
                      (jobs[last//2].origin if last%2==0 else jobs[last//2].dest))
        for k,job in enumerate(jobs):
            for typ in (0,1):
                bit=1<<k
                if typ==0:
                    if pick&bit or current_load+job.bikes>capacity:continue
                    p2,d2=pick|bit,drop
                    station=job.origin
                else:
                    if not(pick&bit) or drop&bit:continue
                    p2,d2=pick,drop|bit
                    station=job.dest
                if last==-1:
                    prior=(start if previous_abs_finish is None else previous_abs_finish)
                    travel=0. if last_station is None else float(drive.loc[last_station,station])
                    arrival=max(start,prior+travel)
                else:
                    travel=float(drive.loc[last_station,station])
                    arrival=tm+travel
                setup=(setup_per_stop if last_station!=station or last==-1 else 0.)
                finish=arrival+setup+handling_per_bike*job.bikes
                if finish>deadline+1e-9:continue
                act=2*k+typ;nextstate=(p2,d2,act)
                if finish+1e-9<best.get(nextstate,math.inf):
                    best[nextstate]=finish
                    parents[nextstate]=(state,travel,setup,job.bikes*handling_per_bike,arrival,finish,station,typ,k)
                    heapq.heappush(heap,(finish,nextstate))
    if solved is None:
        return {'status':'not_certified_within_hour','events':[],'job_count':m}
    events=[];state=solved
    while state!=init:
        previous,travel,setup,handle,arrival,finish,station,typ,k=parents[state]
        events.append({'hour':hour,'job_index':k,'event':'pickup' if typ==0 else 'dropoff',
                       'station_id':station,'bikes':jobs[k].bikes,
                       'travel_minutes_from_previous':round(travel,4),
                       'arrival_minute_abs':round(arrival,4),
                       'finish_minute_abs':round(finish,4),
                       'stop_setup_minutes':round(setup,4),
                       'handling_minutes':round(handle,4)})
        state=previous
    events.reverse()
    return {'status':'timing_capacity_precedence_pass','events':events,
            'finish':best[solved], 'end_station':events[-1]['station_id'],
            'drive_min':sum(x['travel_minutes_from_previous'] for x in events),
            'setup_min':sum(x['stop_setup_minutes'] for x in events),
            'handling_min':sum(x['handling_minutes'] for x in events),
            'job_count':m}


def check_routes(transfers, ids, times, *, hours, truck_capacity=25,
                 stop_setup_minutes=2.,handling_minutes_per_operation=1.,max_jobs=8):
    """Greedy sequence of per-hour exact routes with inter-hour truck continuity.

    A failure of this sequential search is NOT a proof that no other full-day
    route schedule exists: alternate preceding-hour end stations are not searched.
    """
    all_ids=list(map(int,ids));d=clean_transfers(transfers,all_ids,hours)
    rt=times.copy().reindex(index=all_ids,columns=all_ids)
    if rt.isna().any().any():raise ValueError('Missing travel time(s)')
    events=[];hour_rows=[];last_station=None;last_finish=None
    all_certified=True;total_driving=total_setup=total_handling=0.
    chain_broken=False
    for t in range(hours):
        chunk=d[d.hour.eq(t)]
        jobs=[Job(int(x.from_station_id),int(x.to_station_id),int(x.bikes))
              for x in chunk.itertuples(index=False)]
        result=route_hour_exact(jobs,rt,hour=t,capacity=truck_capacity,
            setup_per_stop=stop_setup_minutes,handling_per_bike=handling_minutes_per_operation,
            previous_station=None if chain_broken else last_station,
            previous_abs_finish=None if chain_broken else last_finish,
            max_jobs=max_jobs)
        if result['status']=='not_certified_within_hour':
            # Can a free first-pickup location fit this hour, even ignoring
            # continuity from other hours? If not, the one-hour window fails
            # under the indivisible-jobs assumptions.
            stand=route_hour_exact(jobs,rt,hour=t,capacity=truck_capacity,
                setup_per_stop=stop_setup_minutes,handling_per_bike=handling_minutes_per_operation,
                max_jobs=max_jobs)
            if stand['status']=='timing_capacity_precedence_pass':
                result['status']='not_certified_due_to_chained_route'
            else:
                result['status']='not_certified_even_with_free_start'
        status=result['status']
        if chain_broken and status=='timing_capacity_precedence_pass':
            # This checks the hour in isolation; the preceding failed hour
            # prevents certifying any continuous full-day route.
            status='independent_hour_pass_after_break'
        if status not in ('no_moves','timing_capacity_precedence_pass'):
            all_certified=False
        if result.get('events'):
            events.extend(result['events'])
            total_driving+=result.get('drive_min',0.)
            total_setup+=result.get('setup_min',0.)
            total_handling+=result.get('handling_min',0.)
        if status not in ('no_moves','timing_capacity_precedence_pass'):
            chain_broken=True
        elif not chain_broken:
            last_station=result.get('end_station',last_station)
            last_finish=result.get('finish',last_finish)
        lower_duration=''
        if jobs and status=='not_certified_even_with_free_start':
            # Find the most optimistic minimum duration *without* the hour
            # cutoff, with an unconstrained starting pickup location.
            no_window=route_hour_exact(jobs,rt,hour=t,capacity=truck_capacity,
                setup_per_stop=stop_setup_minutes,
                handling_per_bike=handling_minutes_per_operation,
                max_jobs=max_jobs,window_minutes=10000)
            if no_window['status']=='timing_capacity_precedence_pass':
                lower_duration=round(no_window['finish']-t*60,3)
        hour_rows.append({'hour':t,'jobs':len(jobs),'bikes':int(chunk.bikes.sum()),
                          'status':status,'minimum_route_minutes_free_start':lower_duration,
                          'end_station_if_certified':result.get('end_station','') if status=='timing_capacity_precedence_pass' else '',
                          'finish_minute_abs_if_certified':round(result['finish'],3) if status=='timing_capacity_precedence_pass' else ''})
    summary={'route_status':('conditional_timing_capacity_precedence_pass' if all_certified else
                             'not_certified_for_full_day'),
             'hours_with_transfers':sum(r['jobs']>0 for r in hour_rows),
             'hours_not_certified':sum(r['status'] not in ('no_moves','timing_capacity_precedence_pass') for r in hour_rows),
             'not_certified_hours':[r['hour'] for r in hour_rows if r['status'] not in ('no_moves','timing_capacity_precedence_pass')],
             'hours_failing_even_with_free_start':[r['hour'] for r in hour_rows if r['status']=='not_certified_even_with_free_start'],
             'hours_not_certified_due_to_route_chaining':[r['hour'] for r in hour_rows if r['status']=='not_certified_due_to_chained_route'],
             'hours_independently_possible_but_chain_broken':[r['hour'] for r in hour_rows if r['status']=='independent_hour_pass_after_break'],
             'travel_minutes_in_certified_hours_only':round(total_driving,3),
             'handling_minutes_in_certified_hours_only':round(total_handling,3),
             'setup_minutes_in_certified_hours_only':round(total_setup,3),
             'assumptions':{'single_truck':True,'max_onboard_bikes':truck_capacity,
                            'stop_setup_minutes':stop_setup_minutes,
                            'handling_minutes_per_load_or_unload':handling_minutes_per_operation,
                            'first_location':'free first pickup (no depot)',
                            'route_windows':'all pickup/drop activities completed in assigned clock hour',
                            'interhour_position':'previous certified route end position retained',
                            'route_jobs':'one indivisible pickup-delivery load per transfer row'},
             'limits':'No depot, shift length, driver hours, parking access, station inventory at exact visit time, or customer pickup timing. Sequential hourly route selection not globally optimal; hourly failure with free start is conditional on unsplittable transfer jobs and assumed times; a chain failure alone does not prove infeasibility.'}
    return summary,pd.DataFrame(hour_rows),pd.DataFrame(events)


def _test():
    ids=[1,2,3];caps=np.array([4.,4.,4.]);opening=np.array([4.,0.,0.]);
    sub=np.zeros((3,3));cas=np.zeros((3,3));cas[1,0]=2
    ret=np.zeros((3,3));dist=np.ones((3,3))-np.eye(3)
    move=pd.DataFrame([{'hour':0,'from_station_id':1,'to_station_id':2,'bikes':2}])
    k=dict(throughput=2,fixed=.5,handling=.1,km_cost=0,avg_load=2,max_neighbors=2)
    val,trans,rows=evaluate_policy('test',ids,caps,opening,sub,cas,ret,dist,move,**k)
    assert abs(val['model_contribution_usd']-8.3)<1e-8,val
    assert val['served_pickups']==2.0 and val['bikes_moved']==2
    travel=pd.DataFrame(dist*5,index=ids,columns=ids)
    route,table,events=check_routes(trans,ids,travel,hours=3,truck_capacity=2,
                                  stop_setup_minutes=0,handling_minutes_per_operation=1)
    assert route['hours_not_certified']==0 and list(events.event)==['pickup','dropoff'],route
    impossible,_,_=check_routes(trans,ids,travel,hours=3,truck_capacity=1)
    assert 0 in impossible['not_certified_hours'],impossible
    # Same-hour 2 bikes at B cannot be sourced from returns that occur later.
    rr=np.zeros((3,3));rr[1,0]=2
    empty,_t,_h=evaluate_policy('empty',ids,caps,np.zeros(3),sub,cas,rr,dist,None,**k)
    assert empty['served_pickups']==0 and empty['failed_returns']==0
    print('Self-test PASSED: same-accounting evaluation, conservation, route precedence and capacity.')


def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--date',default='2015-04-06')
    p.add_argument('--hours',type=int,default=24)
    root=Path('output/sf_bikeshare');base=root/'model_inputs_v3'
    p.add_argument('--stations',default=str(base/'station.csv'))
    p.add_argument('--opening',default=str(base/'opening_inventory_daily.csv'))
    p.add_argument('--distances',default=str(base/'station_distances.csv'))
    p.add_argument('--demand',default=str(root/'demand_estimation'/'estimated_demand_station_hour.csv'))
    p.add_argument('--optimized-transfers',default=str(root/'optimization'/'pilot_optimized_transfers.csv'))
    p.add_argument('--optimized-station-hour',default=str(root/'optimization'/'pilot_optimized_station_hour.csv'))
    p.add_argument('--out',default=str(root/'optimization'/'hj_policy_comparison'))
    p.add_argument('--neighbors',type=int,default=5)
    p.add_argument('--throughput',type=float,default=15.)
    p.add_argument('--fixed',type=float,default=60.)
    p.add_argument('--handling',type=float,default=1.)
    p.add_argument('--km-cost',type=float,default=.30)
    p.add_argument('--avg-load',type=float,default=15.)
    p.add_argument('--member-value',type=float,default=.88)
    p.add_argument('--casual-value',type=float,default=4.5)
    p.add_argument('--return-penalty',type=float,default=.88)
    p.add_argument('--occupancy-tolerance',type=float,default=.10)
    p.add_argument('--truck-capacity',type=int,default=25)
    p.add_argument('--stop-setup-minutes',type=float,default=2.)
    p.add_argument('--handling-minutes-per-operation',type=float,default=1.)
    p.add_argument('--max-jobs',type=int,default=8)
    args=p.parse_args()
    if args.self_test:_test();return
    if not 1<=args.hours<=24:raise ValueError('--hours must be 1..24')
    if not Path(args.optimized_transfers).is_file():
        raise FileNotFoundError('Run hj_optimization_model.py first or supply --optimized-transfers')
    ids,caps,opening,sub,cas,ret,dist=read_day(args)
    road=pd.read_csv(args.distances)
    drive=road.pivot(index='from_station_id',columns='to_station_id',values='driving_minutes')
    paths=Path(args.out);paths.parent.mkdir(parents=True,exist_ok=True)
    nearest=allowed_arcs(ids,dist,args.neighbors)
    rule=equal_occupancy_rule(ids,caps,opening,sub,cas,ret,dist,
        throughput=args.throughput,max_neighbors=args.neighbors,tolerance=args.occupancy_tolerance)
    optimized=clean_transfers(pd.read_csv(args.optimized_transfers),ids,args.hours,nearest)
    shared=dict(throughput=args.throughput,max_neighbors=args.neighbors,fixed=args.fixed,
        handling=args.handling,km_cost=args.km_cost,avg_load=args.avg_load,
        member_value=args.member_value,casual_value=args.casual_value,
        failed_return_penalty=args.return_penalty)
    results=[];routes={}
    for policy,tr in [('no_rebalancing',None),('rule_based',rule),('optimized',optimized)]:
        summary,trans,station=evaluate_policy(policy,ids,caps,opening,sub,cas,ret,dist,tr,**shared)
        station.to_csv(str(paths)+f'_{policy}_station_hour.csv',index=False)
        trans.to_csv(str(paths)+f'_{policy}_transfers.csv',index=False)
        if policy!='no_rebalancing':
            route,hours_table,events=check_routes(trans,ids,drive,hours=args.hours,
               truck_capacity=args.truck_capacity,stop_setup_minutes=args.stop_setup_minutes,
               handling_minutes_per_operation=args.handling_minutes_per_operation,
               max_jobs=args.max_jobs)
            routes[policy]=route
            hours_table.to_csv(str(paths)+f'_{policy}_routing_hours.csv',index=False)
            events.to_csv(str(paths)+f'_{policy}_routing_events.csv',index=False)
            summary['route_status']=route['route_status']
            summary['hours_not_certified']=route['hours_not_certified']
        print(policy,json.dumps(summary,indent=2))
        results.append(summary)
        if policy=='optimized' and Path(args.optimized_station_hour).is_file():
            old=pd.read_csv(args.optimized_station_hour)
            if {'station_id','hour','served_pickups','failed_returns','closing_stock'}.issubset(old.columns):
                check=station.merge(old[['station_id','hour','served_pickups','failed_returns','closing_stock']],
                                   on=['station_id','hour'],suffixes=('_replay','_solver'),validate='1:1')
                diffs={col:float(np.max(np.abs(check[f'{col}_replay']-check[f'{col}_solver'])))
                       for col in ['served_pickups','failed_returns','closing_stock']}
                print('Independent Stage 1 replay against solver output (max abs errors):',json.dumps(diffs))
                if any(v>1e-3 for v in diffs.values()):
                    print('WARNING: Replay differs from original solver output; check input versions and parameters.')
    pd.DataFrame(results).to_csv(str(paths)+'_comparison.csv',index=False)
    b=results[0]['model_contribution_usd']
    for result in results[1:]:
        result['increment_vs_no_rebalancing_usd']=round(result['model_contribution_usd']-b,4)
    payload={'date':args.date,'hours':args.hours,'comparison':results,
             'routing':routes,'cost_and_heuristic_parameters':dict(shared,
                        occupancy_tolerance=args.occupancy_tolerance),
             'important':'Routing check is a conditional pickup/delivery time-capacity check. Stage-1 start-of-hour inventory assumption remains unverified. Cost assumptions provisional.'}
    with open(str(paths)+'_summary.json','w',encoding='utf-8') as f:
        json.dump(payload,f,indent=2)
    print('Wrote results with prefix:',paths)
    print('IMPORTANT: no route should be labelled fully verified without station/customer timing and depot/shift assumptions.')

if __name__=='__main__':main()
