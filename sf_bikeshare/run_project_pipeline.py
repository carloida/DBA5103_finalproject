"""Verify the agreed project handoff; rebuild demand/model runs only with explicit flags.

This entry point uses the report's USD60/day, USD1/bike, USD0.30/km scenario.
The separately labelled updated-cost extension is run_integrated_pipeline.py.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'output/sf_bikeshare'
CASES={'historical':'historical_demand_station_hour.csv',
       'hybrid':'estimated_demand_station_hour_hybrid.csv'}
DATES=pd.date_range('2015-04-06','2015-04-19').strftime('%Y-%m-%d').tolist()


def verify():
    handoff=json.loads((ROOT/'docs/JOOHEE_HANDOFF_MANIFEST_2026-11-22.json').read_text())
    for f in handoff['files']:
        assert hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
    outputs={}
    for case,name in CASES.items():
        d=pd.read_csv(DATA/'demand_estimation_cases_2026-11-22'/name)
        assert d.shape==(57120,31) and not d.duplicated(['station_id','service_date','hour']).any()
        for side in ['pickups','returns']:
            for rider in ['subscriber','customer']:
                a=d[f'estimated_{rider}_{side}'];b=d[f'observed_{rider}_{side}']
                assert np.isfinite(a).all() and a.ge(b-1e-10).all()
        outputs[case]=d
    for case in ['historical','hybrid','observed']:
        s=pd.read_csv(DATA/f'optimization_14days_2026-11-22/{case}_daily_policy_comparison.csv')
        assert len(s)==42 and not s.duplicated(['date','policy']).any()
        assert sorted(s.date.unique())==DATES and s.groupby('date').size().eq(3).all()
        source=outputs.get(case,outputs['historical']).copy()
        source['service_date']=pd.to_datetime(source.service_date).dt.strftime('%Y-%m-%d')
        prefix='observed' if case=='observed' else 'estimated'
        source['pickup_total']=source[f'{prefix}_subscriber_pickups']+source[f'{prefix}_customer_pickups']
        source['return_total']=source[f'{prefix}_subscriber_returns']+source[f'{prefix}_customer_returns']
        expected=source.groupby('service_date')[['pickup_total','return_total']].sum()
        assert np.allclose(s.demand_pickups,s.date.map(expected.pickup_total),atol=.001,rtol=0)
        assert np.allclose(s.attempted_returns,s.date.map(expected.return_total),atol=.001,rtol=0)
        assert np.allclose(s.trip_value_usd-s.movement_cost_usd-s.fixed_cost_usd-s.return_failure_penalty_usd,
                           s.model_contribution_usd,atol=.001,rtol=0)
        opt=s[s.policy.eq('optimized')]
        assert opt.solver_status.eq(0).all() and opt.solver_gap.le(.01).all()
        assert opt.replay_max_error.lt(1e-4).all()
    for name,variable in [('hj_multiday_sensitivity.py','BASE_COST'),('jh_run_experiments.py','COST')]:
        tree=ast.parse((ROOT/'sf_bikeshare'/name).read_bytes())
        node=next(n.value for n in tree.body if isinstance(n,ast.Assign)
                  and any(isinstance(t,ast.Name) and t.id==variable for t in n.targets))
        assert isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='dict'
        values={k.arg:ast.literal_eval(k.value) for k in node.keywords}
        assert values==dict(fixed=60.,handling=1.,km_cost=.30,avg_load=15.)
    print('PASS: frozen supplied file hashes, both demand contracts, three 14-day result sets, '
          'demand totals, contribution accounting, recorded solver/replay diagnostics and report cost constants')
    print('Historical is base; hybrid is sensitivity; observed counts are a lower-demand comparison. '
          'This verifies supplied records; it does not independently reproduce their optimization or certify routes.')


def run(script,*args):
    subprocess.run([sys.executable,'-B',str(ROOT/'sf_bikeshare'/script),*map(str,args)],cwd=ROOT,check=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build-demand',action='store_true')
    ap.add_argument('--run-models',action='store_true')
    ap.add_argument('--run-extra-experiments',action='store_true',help='Rerun penalty and budget experiments only')
    ap.add_argument('--output-dir',default=str(ROOT/'tmp/project_pipeline_rebuild'))
    ap.add_argument('--dates',nargs='+',default=DATES)
    ap.add_argument('--time-limit',type=float,default=30.)
    args=ap.parse_args()
    verify()
    if not any([args.build_demand,args.run_models,args.run_extra_experiments]):return
    out=Path(args.output_dir).resolve()
    if out==ROOT or DATA.resolve()==out or DATA.resolve() in out.parents:
        raise ValueError('Rebuilds must use a separate output directory outside the published output tree')
    if out.exists() and any(out.iterdir()):raise ValueError('Choose a new/empty output directory')
    out.mkdir(parents=True,exist_ok=True)
    paths={case:DATA/'demand_estimation_cases_2026-11-22'/name for case,name in CASES.items()}
    if args.build_demand:
        for case in CASES:
            dest=out/'demand'/case
            run('build_demand_minute.py','--case',case,'--hourly',DATA/'model_inputs_v3/station_hour_observed.csv.gz',
                '--minute-dir',DATA/'demand_estimation_inputs_v3','--output-dir',dest)
            paths[case]=dest/f'estimated_demand_station_hour_{case}.csv'
            pd.testing.assert_frame_equal(pd.read_csv(paths[case]),
                pd.read_csv(DATA/'demand_estimation_cases_2026-11-22'/CASES[case]),rtol=1e-12,atol=1e-12)
    if args.run_models:
        observed=pd.read_csv(paths['historical'])
        for side in ['pickups','returns']:
            for rider in ['subscriber','customer']:
                observed[f'estimated_{rider}_{side}']=observed[f'observed_{rider}_{side}']
                observed[f'missed_{rider}_{side}']=0.
                observed[f'method_{rider}_{side}']='observed_only_lower_bound'
            observed[f'estimated_total_{side}']=observed[f'estimated_subscriber_{side}']+observed[f'estimated_customer_{side}']
        paths['observed']=out/'observed_station_hour.csv'
        observed.to_csv(paths['observed'],index=False,lineterminator='\n')
        for case,path in paths.items():
            run('hj_multiday_sensitivity.py','--dates',*args.dates,'--time-limit',args.time_limit,
                '--demand',path,'--out',out/'models'/case)
    if args.run_extra_experiments:
        (out/'extra').mkdir(exist_ok=True)
        for label,filename in [('penalty','penalty_sensitivity.csv'),('losttrip','lost_trip_budget.csv')]:
            run('jh_run_experiments.py',label,paths['historical'],out/'extra'/filename)
        print('Extra runners use their documented 14 dates and 30-second limit; diversion was not rerun.')
    print('New artifacts:',out,'; published results were not overwritten.')


if __name__=='__main__':main()
