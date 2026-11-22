"""Integration invariants: money units, pair costs, service budget, stock and routing."""
import copy
from pathlib import Path
import numpy as np
import pandas as pd
from integration_costs import load_config,coefficients,unit_cost_matrix,route_cost
from hj_optimization_model import solve_allocation
from hj_policy_routing import evaluate_policy,check_routes


def run():
    c=load_config(Path(__file__).with_name('integration_cost_config.json'))
    k=coefficients(c)
    assert np.isclose(k['rental_mileage_usd_per_km'],.14/1.609344)
    assert np.isclose(k['handling_usd_per_bike'],29.57*2/60)
    ids=[1,2];caps=np.array([4.,4.]);opening=np.array([2.,0.])
    distance=np.array([[0.,3.],[3.,0.]])
    minutes=np.array([[0.,6.],[6.,0.]])
    matrix=unit_cost_matrix(distance,minutes,c)
    assert np.isclose(matrix[0,1],29.57*2/60+((.14/1.609344+.882*.168)*3+29.57*.1)/15)
    sub=np.zeros((2,1));cas=sub.copy();cas[1,0]=2;returns=sub.copy()
    unit=np.array([[0.,.25],[.25,0.]])
    args=dict(fixed=.5,handling=99.,km_cost=99.,avg_load=2,throughput=2,max_neighbors=1,
              unit_costs=unit,time_limit=5.)
    result=solve_allocation(ids,caps,opening,sub,cas,returns,distance,**args)
    assert result.summary['solver_status']==0,result.summary
    assert np.isclose(result.summary['model_contribution_usd'],8.)
    evaluated,jobs,states=evaluate_policy('test',ids,caps,opening,sub,cas,returns,distance,
        result.transfers,**{x:v for x,v in args.items() if x!='time_limit'})
    assert np.isclose(evaluated['model_contribution_usd'],8.)
    no=solve_allocation(ids,caps,opening,sub,cas,returns,distance,
        objective_mode='min_failed_requests',redistribution_budget=0.,**args)
    assert no.summary['bikes_moved']==0 and no.summary['served_pickups']==0
    yes=solve_allocation(ids,caps,opening,sub,cas,returns,distance,
        objective_mode='min_failed_requests',redistribution_budget=1.,**args)
    assert yes.summary['served_pickups']==2
    assert yes.summary['movement_cost_usd']+yes.summary['fixed_cost_usd']<=1.+1e-7
    terminal=solve_allocation(ids,caps,opening,sub,cas,returns,distance,
        end_stock_at_least_opening=True,**args)
    assert terminal.summary['served_pickups']==0
    assert (terminal.station_hour.closing_stock.to_numpy()>=opening-1e-7).all()
    times=pd.DataFrame(minutes,index=ids,columns=ids)
    dframe=pd.DataFrame(distance,index=ids,columns=ids)
    job=pd.DataFrame([dict(hour=0,from_station_id=1,to_station_id=2,bikes=1)])
    rs,_,ev=check_routes(job,ids,times,hours=1,truck_capacity=2,
        stop_setup_minutes=0,handling_minutes_per_operation=1)
    c=copy.deepcopy(c);c['stop_setup_minutes']=0
    route=route_cost(rs,ev,dframe,c,stage1_cost=61.)
    assert np.isclose(route['route_distance_km'],3.)
    assert np.isclose(route['paid_hours'],8/60)
    assert np.isclose(route['stage2_cost_usd'],60+29.57*8/60+k['vehicle_usd_per_km']*3)
    bad,_,events=check_routes(pd.DataFrame([dict(hour=0,from_station_id=1,to_station_id=2,bikes=3)]),
        ids,times,hours=1,truck_capacity=2,stop_setup_minutes=0,handling_minutes_per_operation=1)
    assert route_cost(bad,events,dframe,c,stage1_cost=61.)['stage2_cost_usd'] is None
    print('PASS integration: unit conversions, driving-labor matrix, evaluator equality, budget objective, terminal condition and conditional route costing')


if __name__=='__main__':run()
