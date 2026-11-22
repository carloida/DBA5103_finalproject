#!/usr/bin/env python3
r"""DBA5103 Stage-1 bike-allocation MILP, with a 3x3 regression test.

This is a prototype of the *allocation* model in Joo Hee's report §4, not a
truck-routing solver. Inputs and costs are scenario assumptions, not observed
operator financials. An optimization on retrospectively adjusted demand is a
perfect-information benchmark, not a live forecast.

Windows CMD examples (run from repository root with .venv active):

  python sf_bikeshare\hj_optimization_model.py --self-test
  python sf_bikeshare\hj_optimization_model.py --date 2015-04-06 --hours 3 --demand output\sf_bikeshare\demand_estimation\estimated_demand_station_hour.csv

To run all 24 hours, use --hours 24. Start with a modest time limit and examine
solver status/gap; a feasible incumbent is NOT necessarily proven optimal.
The default --neighbors 5 restricts each origin to the five nearest destinations;
use --neighbors 33 for the unrestricted graph (much slower).

Dependencies: numpy, pandas, scipy (SciPy >= 1.9 for milp).
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import milp, Bounds, LinearConstraint
from scipy.sparse import coo_matrix


@dataclass
class Result:
    summary: dict
    transfers: pd.DataFrame
    station_hour: pd.DataFrame


def relocation_cost_matrix(distance, handling, km_cost, avg_load, unit_costs=None):
    """USD per relocated bike; optional pair costs include time-based driving labor."""
    if avg_load <= 0:
        raise ValueError('avg_load must be positive')
    costs=(handling+km_cost*np.asarray(distance,dtype=float)/avg_load
           if unit_costs is None else np.asarray(unit_costs,dtype=float))
    if costs.shape != np.asarray(distance).shape or not np.isfinite(costs).all() or (costs<0).any():
        raise ValueError('Unit cost matrix must match distances and be finite/nonnegative')
    return costs


def solve_allocation(station_ids, caps, opening, pickups_sub, pickups_cas,
                     returns, distance, *, fixed=60.0, handling=1.0,
                     km_cost=.30, avg_load=15.0, throughput=15.0,
                     max_trucks=1, member_value=.88, casual_value=4.5,
                     failed_return_penalty=.88, time_limit=30.0,
                     no_rebalancing=False, max_neighbors=5, unit_costs=None,
                     end_stock_at_least_opening=False, objective_mode='contribution',
                     redistribution_budget=None) -> Result:
    """Solve one daily/partial-day horizon. Arrays: station x hour, USD/km inputs.

    b and served quantities are continuous because estimated demand is fractional.
    x and trucks are integer. Aggregate service uses proportional rider splitting and the exact
    min(available post-transfer stock, total pickup demand) linearization.
    Returns enter AFTER customer pickups in the hour; their failure is also
    linearized exactly, rather than left to the financial objective to decide.
    """
    ids = list(map(int, station_ids))
    n, hours = pickups_sub.shape
    assert len(ids) == n and pickups_cas.shape == returns.shape == (n, hours)
    assert len(caps) == len(opening) == n and distance.shape == (n,n)
    if avg_load <= 0 or throughput < 0 or max_trucks < 0: raise ValueError('Invalid vehicle parameters')
    for a in (caps, opening, pickups_sub, pickups_cas, returns, distance):
        if not np.all(np.isfinite(a)) or np.any(a < 0): raise ValueError('Inputs must be finite and nonnegative')
    if np.any(opening > caps + 1e-8): raise ValueError('Opening bikes exceed station capacity')
    d = pickups_sub + pickups_cas
    costs=relocation_cost_matrix(distance,handling,km_cost,avg_load,unit_costs)
    if objective_mode not in ('contribution','min_failed_requests'):
        raise ValueError('Unknown objective')
    if objective_mode=='min_failed_requests' and redistribution_budget is None:
        raise ValueError('Service objective requires an explicit redistribution budget')
    if redistribution_budget is not None and redistribution_budget<0:
        raise ValueError('Budget must be nonnegative')
    # Restrict each origin to nearby destinations to make the full-day MILP
    # tractable for a group project. This is NOT the unrestricted 34x33 graph.
    k = min(n-1, max(1,int(max_neighbors)))
    arcs = []
    for i in range(n):
        nearest = [int(j) for j in np.argsort(distance[i]) if j != i][:k]
        arcs.extend((i, j) for j in nearest)
    arcs_by_i = {i:[j for a,j in arcs if a==i] for i in range(n)}
    inbound_by_j = {j:[i for i,b in arcs if b==j] for j in range(n)}

    # Index variables, bounds, objective (minimize negative contribution + costs).
    ix, lower, upper, integral, objective = {}, [], [], [], []
    def var(key, lb=0, ub=np.inf, integer=0, cost=0.0):
        idx = len(lower);ix[key] = idx
        lower.append(float(lb));upper.append(float(ub))
        integral.append(integer);objective.append(float(cost))
        return idx
    for t in range(hours):
        for i,j in arcs:
            cost = costs[i,j] if objective_mode=='contribution' else 0.
            var(('x',i,j,t),ub=0 if no_rebalancing else throughput*max_trucks,
                integer=1,cost=cost)
    for t in range(hours+1):
        for i in range(n):
            var(('b',i,t),lb=opening[i] if t==0 or (t==hours and end_stock_at_least_opening) else 0,
                ub=opening[i] if t==0 else caps[i])
    for t in range(hours):
        for i in range(n):
            value_per_served = (member_value*pickups_sub[i,t] + casual_value*pickups_cas[i,t]) / d[i,t] if d[i,t]>0 else 0
            var(('q',i,t),ub=caps[i])     # Stock after morning redistribution
            var(('s',i,t),ub=d[i,t],cost=-value_per_served if objective_mode=='contribution' else -1.)
            var(('o',i,t),ub=returns[i,t],cost=failed_return_penalty if objective_mode=='contribution' else 1.)
            var(('z',i,t),ub=1,integer=1) # pickup stockout indicator
            var(('v',i,t),ub=1,integer=1) # return overflow indicator
    var(('y',),ub=0 if no_rebalancing else max_trucks,integer=1,cost=fixed if objective_mode=='contribution' else 0.)

    rows,cols,vals,lbs,ubs = [],[],[],[],[]
    def constraint(coef, lb=-np.inf, ub=np.inf):
        row = len(lbs)
        for k, v in coef.items():
            if abs(v)>1e-12:
                rows.append(row);cols.append(ix[k]);vals.append(float(v))
        lbs.append(float(lb));ubs.append(float(ub))

    # Every activated truck must be used; essential for the service-only objective.
    constraint({('y',):1,**{('x',i,j,t):-1 for t in range(hours) for i,j in arcs}},ub=0)
    if redistribution_budget is not None:
        constraint({('y',):fixed,**{('x',i,j,t):float(costs[i,j])
                   for t in range(hours) for i,j in arcs}},ub=redistribution_budget)

    for t in range(hours):
        throughput_row={('y',):-throughput}
        for i,j in arcs:
            throughput_row[('x',i,j,t)] = 1
        constraint(throughput_row,ub=0)
        for i in range(n):
            inbound={('x',j,i,t):1 for j in inbound_by_j[i]}
            outbound={('x',i,j,t):-1 for j in arcs_by_i[i]}
            # Post-transfer inventory = initial + arrivals of trucks - departures of trucks.
            coef={('q',i,t):1,('b',i,t):-1}
            coef.update({k:-v for k,v in inbound.items()})
            coef.update({k:-v for k,v in outbound.items()})
            constraint(coef,lb=0,ub=0)
            # Cannot load more bikes than available at the start of the hour.
            constraint({('b',i,t):-1,**{('x',i,j,t):1 for j in arcs_by_i[i]}},ub=0)
            # Work-conserving aggregate service, proportional by class; not event-level FCFS.
            # s<=q; s<=D is already encoded in the variable upper bound.
            constraint({('s',i,t):1,('q',i,t):-1},ub=0)
            m=float(caps[i]+d[i,t]+1)
            # s >= D - M*z
            constraint({('s',i,t):1,('z',i,t):m},lb=d[i,t])
            # s >= q - M*(1-z)
            constraint({('s',i,t):1,('q',i,t):-1,('z',i,t):-m},lb=-m)
            # Rejected returns = max(0, A + post-pickup stock - K).
            # B_next = post-pickup stock + attempted returns - rejected returns.
            constraint({('b',i,t+1):1,('q',i,t):-1,('s',i,t):1,('o',i,t):1},lb=returns[i,t],ub=returns[i,t])
            constraint({('o',i,t):1,('q',i,t):-1,('s',i,t):1},lb=returns[i,t]-caps[i])
            mo=float(caps[i]+returns[i,t]+1)
            constraint({('o',i,t):1,('q',i,t):-1,('s',i,t):1,('v',i,t):mo},
                       ub=returns[i,t]-caps[i]+mo)
            constraint({('o',i,t):1,('v',i,t):-mo},ub=0)

    A=coo_matrix((vals,(rows,cols)),shape=(len(lbs),len(lower))).tocsr()
    begun=time.perf_counter()
    res=milp(c=np.array(objective),integrality=np.array(integral),
             bounds=Bounds(lower,upper),
             constraints=LinearConstraint(A,lbs,ubs),
             options={'time_limit':float(time_limit),'mip_rel_gap':0.01})
    elapsed=time.perf_counter()-begun
    info={'solver_status':int(res.status),'solver_message':str(res.message),
          'seconds':round(elapsed,3),'n_variables':len(lower),'n_constraints':len(lbs),'allowed_directed_arcs':len(arcs),'neighbors_per_origin':k,
          'solver_gap':float(res.mip_gap) if getattr(res,'mip_gap',None) is not None else None}
    if res.x is None:
        return Result(info,pd.DataFrame(),pd.DataFrame())
    X=res.x
    total_moves,move_cost,records=0.0,0.0,[]
    for t in range(hours):
        for i,j in arcs:
                value=X[ix['x',i,j,t]]
                if value>1e-5:
                    cost=costs[i,j]
                    records.append({'hour':t,'from_station_id':ids[i],'to_station_id':ids[j],
                                    'bikes':round(float(value),5),'unit_cost_usd':round(float(cost),4)})
                    total_moves += value;move_cost += value*cost
    values=[]
    total_served=total_failed=total_demand=total_ret=total_value=0.0
    for t in range(hours):
        for i in range(n):
            served=max(0.0,float(X[ix['s',i,t]]))
            unmet=max(0.0,float(d[i,t])-served)
            failed=max(0.0,float(X[ix['o',i,t]]))
            member=served*pickups_sub[i,t]/d[i,t] if d[i,t]>0 else 0
            casual=served-member
            value=member*member_value+casual*casual_value
            total_value += value;total_demand += d[i,t];total_served +=served
            total_failed+=failed;total_ret+=returns[i,t]
            values.append({'station_id':ids[i],'hour':t,'opening_stock':float(X[ix['b',i,t]]),
                           'post_transfer_stock':float(X[ix['q',i,t]]),'pickup_demand':float(d[i,t]),
                           'served_pickups':served,'unmet_pickups':unmet,'failed_returns':failed,
                           'return_demand':float(returns[i,t]),
                           'closing_stock':float(X[ix['b',i,t+1]])})
    trucks=float(X[ix[('y',)]]);fixed_cost=fixed*trucks
    info.update({'objective_mode':objective_mode,'redistribution_budget_usd':redistribution_budget,
                 'unit_cost_matrix_override':unit_costs is not None,
                 'end_stock_at_least_opening':end_stock_at_least_opening,
                 'trucks_used':trucks,'bikes_moved':round(total_moves,5),
                 'demand_pickups':round(total_demand,5),'served_pickups':round(total_served,5),
                 'unmet_pickups':round(total_demand-total_served,5),
                 'attempted_returns':round(total_ret,5),'failed_returns':round(total_failed,5),
                 'trip_value_usd':round(total_value,4),'movement_cost_usd':round(move_cost,4),
                 'fixed_cost_usd':round(fixed_cost,4),
                 'return_failure_penalty_usd':round(total_failed*failed_return_penalty,4),
                 'model_contribution_usd':round(total_value-move_cost-fixed_cost-total_failed*failed_return_penalty,4),
                 'routing_verified':False,'model_description':'restricted-neighbor Stage 1 MILP, no vehicle routing'})
    return Result(info,pd.DataFrame(records),pd.DataFrame(values))


def read_day(args):
    stations=pd.read_csv(args.stations).sort_values('station_id')
    ids=stations.station_id.astype(int).tolist()
    n=len(ids); cap=stations.dock_count.to_numpy(dtype=float)
    opening=pd.read_csv(args.opening)
    opening['service_date']=pd.to_datetime(opening.service_date).dt.strftime('%Y-%m-%d')
    init=opening[opening.service_date.eq(args.date)].set_index('station_id').reindex(ids)
    if init.opening_bikes.isna().any(): raise ValueError('Missing opening stocks for some stations on date '+args.date)
    first=init.opening_bikes.to_numpy(dtype=float)
    demand=pd.read_csv(args.demand)
    demand['service_date']=pd.to_datetime(demand.service_date).dt.strftime('%Y-%m-%d')
    day=demand[demand.service_date.eq(args.date)].copy()
    if len(day)!=n*24:raise ValueError(f'Expected {n*24} rows in daily demand, got {len(day)}')
    day=day[day.hour.lt(args.hours)].set_index(['station_id','hour'])
    grid=pd.MultiIndex.from_product([ids,range(args.hours)],names=['station_id','hour'])
    day=day.reindex(grid)
    fields=['estimated_subscriber_pickups','estimated_customer_pickups',
            'estimated_total_returns']
    if day[fields].isna().any().any(): raise ValueError('Missing demand values for some station-hours')
    shape=(n,args.hours)
    sub=day[fields[0]].to_numpy(dtype=float).reshape(shape)
    cas=day[fields[1]].to_numpy(dtype=float).reshape(shape)
    ret=day[fields[2]].to_numpy(dtype=float).reshape(shape)
    distances=pd.read_csv(args.distances)
    road=distances.pivot(index='from_station_id',columns='to_station_id',values='road_distance_km').reindex(index=ids,columns=ids)
    if road.isna().any().any():raise ValueError('Missing road distances')
    return ids,cap,first,sub,cas,ret,road.to_numpy(dtype=float)


def test():
    # Exactly two initial bikes at A, two requests at B in hour 0; no returns.
    # Other stations and hours have no demand. One truck can carry 2 per hour.
    ids=[1,2,3];cap=np.array([3.,3.,3.]);opening=np.array([2.,0.,0.])
    sub=np.zeros((3,3));cas=np.zeros((3,3));cas[1,0]=2
    returns=np.zeros((3,3));distance=np.ones((3,3))-np.eye(3)
    args=dict(fixed=0.5,handling=.1,km_cost=0,avg_load=2,throughput=2,
              max_trucks=1,casual_value=4.5,time_limit=10)
    base=solve_allocation(ids,cap,opening,sub,cas,returns,distance,**args,no_rebalancing=True)
    opt=solve_allocation(ids,cap,opening,sub,cas,returns,distance,**args)
    assert base.summary['solver_status']==0 and opt.summary['solver_status']==0, (base.summary,opt.summary)
    assert abs(base.summary['served_pickups'])<1e-7
    assert abs(opt.summary['served_pickups']-2)<1e-7, opt.summary
    assert abs(opt.summary['bikes_moved']-2)<1e-7, opt.summary
    assert abs(opt.summary['model_contribution_usd']-8.3)<1e-5, opt.summary
    assert opt.summary['failed_returns']==0
    # Independent corner cases: returns should not satisfy earlier same-hour
    # rentals, and full docks must reject the minimum physically required returns.
    cs=np.zeros((3,3)); cs[1,0]=1
    rr=np.zeros((3,3)); rr[1,0]=1
    no_stock=solve_allocation(ids,cap,np.zeros(3),sub,cs,rr,distance,
                              **{**args,'fixed':100},no_rebalancing=True)
    assert no_stock.summary['served_pickups']==0, no_stock.summary
    assert no_stock.summary['failed_returns']==0, no_stock.summary
    overflow=solve_allocation(ids,np.array([2.,2.,2.]),np.array([2.,0.,0.]),
                              np.zeros((3,3)),np.zeros((3,3)),
                              np.array([[2.,0.,0.],[0.,0.,0.],[0.,0.,0.]]),
                              distance,**args,no_rebalancing=True)
    assert overflow.summary['failed_returns']==2, overflow.summary
    print('3x3 mathematical regression, same-hour ordering, and overflow tests PASSED')
    print(json.dumps({'baseline':base.summary,'optimized':opt.summary},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--date',default='2015-04-06')
    p.add_argument('--hours',type=int,default=3)
    root=Path('output/sf_bikeshare')
    inputs=root/'model_inputs_v3'
    p.add_argument('--stations',default=str(inputs/'station.csv'))
    p.add_argument('--opening',default=str(inputs/'opening_inventory_daily.csv'))
    p.add_argument('--distances',default=str(inputs/'station_distances.csv'))
    p.add_argument('--demand',default=str(root/'demand_estimation'/'estimated_demand_station_hour.csv'))
    p.add_argument('--out',default=str(root/'optimization'/'pilot'))
    p.add_argument('--fixed',type=float,default=60.0)
    p.add_argument('--handling',type=float,default=1.0)
    p.add_argument('--km-cost',type=float,default=.30)
    p.add_argument('--avg-load',type=float,default=15.0)
    p.add_argument('--throughput',type=float,default=15.0)
    p.add_argument('--time-limit',type=float,default=25.0)
    p.add_argument('--neighbors',type=int,default=5,help='Allowed nearest destinations per source')
    args=p.parse_args()
    if args.self_test: test();return
    if not 1<=args.hours<=24: raise ValueError('--hours must be 1..24')
    ids,caps,opening,sub,cas,ret,road=read_day(args)
    kw=dict(fixed=args.fixed,handling=args.handling,km_cost=args.km_cost,
            avg_load=args.avg_load,throughput=args.throughput,time_limit=args.time_limit,max_neighbors=args.neighbors)
    output={}
    prefix=Path(args.out);prefix.parent.mkdir(parents=True,exist_ok=True)
    for policy,zero in [('no_rebalancing',True),('optimized',False)]:
        result=solve_allocation(ids,caps,opening,sub,cas,ret,road,**kw,no_rebalancing=zero)
        print(policy,json.dumps(result.summary,indent=2))
        output[policy]=result.summary
        if not result.station_hour.empty:
            result.station_hour.to_csv(str(prefix)+f'_{policy}_station_hour.csv',index=False)
            result.transfers.to_csv(str(prefix)+f'_{policy}_transfers.csv',index=False)
    with open(str(prefix)+'_summary.json','w',encoding='utf-8') as f:
        json.dump({'date':args.date,'hours':args.hours,'status':'STAGE1_ONLY_COST_PARAMETERS_PROVISIONAL',
                   'assumptions':kw,'policies':output},f,indent=2)
    if all(k in output and 'model_contribution_usd' in output[k] for k in ('no_rebalancing','optimized')):
        print('Additional modeled contribution (USD):',round(output['optimized']['model_contribution_usd']-output['no_rebalancing']['model_contribution_usd'],4))
    print('IMPORTANT: Stage 2 truck routing is not yet validated; cost rates are illustrative/provisional.')


if __name__=='__main__':main()
