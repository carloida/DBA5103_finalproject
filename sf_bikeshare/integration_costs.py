"""Common metric cost accounting for Stage 1 and conditional route repricing."""
import json
from pathlib import Path
import numpy as np


def load_config(path):
    config=json.loads(Path(path).read_text(encoding='utf-8'))
    if config['currency']!='USD':
        raise ValueError('This scenario uses USD')
    if config['max_trucks']!=1:
        raise ValueError('The integrated evaluator/routing currently supports exactly one available truck')
    for name in ['average_load_bikes','adopted_loaded_wage_usd_per_hour']:
        if config[name]<=0:raise ValueError(name+' must be positive')
    return config


def coefficients(config):
    wage=float(config['adopted_loaded_wage_usd_per_hour'])
    mileage=config['rental_mileage_usd_per_mile_source']/config['kilometres_per_mile']
    fuel=config['fuel_usd_per_litre']*config['fuel_litres_per_100km']/100
    handling=wage*(config['load_minutes_per_bike']+config['unload_minutes_per_bike'])/60
    return dict(loaded_wage_usd_per_hour=wage,rental_mileage_usd_per_km=mileage,
                fuel_usd_per_km=fuel,vehicle_usd_per_km=mileage+fuel,
                handling_usd_per_bike=handling)


def unit_cost_matrix(distance_km,driving_minutes,config):
    d,t=np.asarray(distance_km,dtype=float),np.asarray(driving_minutes,dtype=float)
    if d.shape!=t.shape or not np.isfinite(d).all() or not np.isfinite(t).all() or (d<0).any() or (t<0).any():
        raise ValueError('Finite nonnegative distance/time matrices with common shape required')
    c=coefficients(config)
    return c['handling_usd_per_bike']+(c['vehicle_usd_per_km']*d+
                c['loaded_wage_usd_per_hour']*t/60)/config['average_load_bikes']


def route_cost(route_summary,events,distances,config,stage1_cost):
    """Price only a complete conditional route; incomplete hours never create a full-route cost."""
    if route_summary['route_status']!='conditional_timing_capacity_precedence_pass':
        return dict(stage2_cost_usd=None,stage2_minus_stage1_usd=None,
                    cost_status='not_priced_incomplete_conditional_route')
    if events.empty:
        return dict(stage2_cost_usd=0.,stage2_minus_stage1_usd=-float(stage1_cost),
                    route_distance_km=0.,paid_hours=0.,active_hours=0.,cost_status='no_moves')
    records=events.sort_values(['hour','arrival_minute_abs'],kind='stable')
    stations=records.station_id.astype(int).tolist()
    distance=sum(float(distances.loc[a,b]) for a,b in zip(stations,stations[1:]))
    active=(records.travel_minutes_from_previous.sum()+records.stop_setup_minutes.sum()+records.handling_minutes.sum())/60
    span=(records.finish_minute_abs.max()-records.hour.min()*60)/60
    if config['paid_time_basis'] not in ('span','active'):
        raise ValueError('Unknown paid time basis')
    paid=span if config['paid_time_basis']=='span' else active
    c=coefficients(config)
    cost=(config['fixed_usd_per_van_day']+c['loaded_wage_usd_per_hour']*paid+
          c['vehicle_usd_per_km']*distance+config['additional_direct_fees_usd'])
    return dict(stage2_cost_usd=float(cost),stage2_minus_stage1_usd=float(cost-stage1_cost),
                route_distance_km=distance,paid_hours=float(paid),active_hours=float(active),
                wait_hours_in_span=float(max(0,span-active)),cost_status='conditional_route_priced')
