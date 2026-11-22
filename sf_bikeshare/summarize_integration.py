"""Summarize executed integration checks; does not rerun or fabricate model results."""
import argparse
import hashlib
import json
from pathlib import Path
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def markdown(frame):
    names=list(frame.columns)
    rows=['| '+' | '.join(names)+' |','| '+' | '.join(['---']*len(names))+' |']
    for row in frame.itertuples(index=False,name=None):
        cells=[]
        for x in row:
            if pd.isna(x):cells.append('not available')
            elif isinstance(x,(float,np.floating)):
                cells.append(f'{x:.3g}' if 0<abs(x)<.001 else f'{x:.3f}')
            else:cells.append(str(x).replace('|','/'))
        rows.append('| '+' | '.join(cells)+' |')
    return '\n'.join(rows)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output-dir',
        default=str(ROOT/'output/sf_bikeshare/integration_review_2026-11-22'));args=ap.parse_args()
    out=Path(args.output_dir)
    manifest=json.loads((out/'run_manifest.json').read_text())
    s=pd.read_csv(out/'daily_policy_comparison.csv')
    r=pd.read_csv(out/'conditional_route_comparison.csv')
    config=json.loads((out/'cost_configuration.json').read_text())
    c,k=config['configuration'],config['derived']
    base=s[s.policy.eq('no_rebalancing')].set_index(['case','date'])
    rows=[]
    for x in s.itertuples():
        b=base.loc[(x.case,x.date)]
        gross=(x.trip_value_usd-b.trip_value_usd)-(x.return_failure_penalty_usd-b.return_failure_penalty_usd)
        n=x.bikes_moved
        rows.append(dict(case=x.case,date=x.date,policy=x.policy,bikes_moved=n,
            gross_allocated_service_gain_usd=gross,
            break_even_total_cost_usd_per_bike=gross/n if n else None,
            break_even_variable_cost_usd_per_bike=(gross-x.fixed_cost_usd)/n if n else None,
            stage1_cost_usd_per_bike=(x.movement_cost_usd+x.fixed_cost_usd)/n if n else None))
    pd.DataFrame(rows).to_csv(out/'break_even_costs.csv',index=False,lineterminator='\n')
    for ix,x in r.iterrows():
        b=base.loc[(x['case'],x['date'])]
        policy=s[s.case.eq(x['case'])&s.date.eq(x['date'])&s.policy.eq(x['policy'])].iloc[0]
        if pd.isna(x.get('stage2_cost_usd')):continue
        r.loc[ix,'stage1_additional_contribution_on_priced_days_usd']=policy.additional_contribution_usd
        active_cost=(0. if policy.bikes_moved==0 else c['fixed_usd_per_van_day']+
            k['loaded_wage_usd_per_hour']*x.active_hours+k['vehicle_usd_per_km']*x.route_distance_km+
            c['additional_direct_fees_usd'])
        r.loc[ix,'stage2_active_time_only_cost_usd']=active_cost
        r.loc[ix,'stage2_paid_cost_usd_per_bike']=(None if policy.bikes_moved==0 else x.stage2_cost_usd/policy.bikes_moved)
        r.loc[ix,'stage2_active_cost_usd_per_bike']=(None if policy.bikes_moved==0 else active_cost/policy.bikes_moved)
        r.loc[ix,'additional_contribution_paid_span_usd']=(
            x.conditional_route_repriced_contribution_usd-b.model_contribution_usd)
        r.loc[ix,'additional_contribution_active_time_only_usd']=(
            policy.trip_value_usd-policy.return_failure_penalty_usd-active_cost-b.model_contribution_usd)
    r.to_csv(out/'route_cost_sensitivity.csv',index=False,lineterminator='\n')
    aggregation=s.groupby(['case','policy']).agg(days=('date','size'),served_pickups=('served_pickups','sum'),
        unmet_pickups=('unmet_pickups','sum'),failed_returns=('failed_returns','sum'),
        bikes_moved=('bikes_moved','sum'),additional_contribution_usd=('additional_contribution_usd','sum'),
        additional_served_pickups=('additional_served_pickups','sum')).reset_index()
    aggregation.to_csv(out/'aggregate_policy_comparison.csv',index=False,lineterminator='\n')
    opt=s[s.policy.eq('optimized')]
    route_summary=r.groupby(['case','policy']).agg(days=('date','size'),
        conditionally_priced_days=('stage2_cost_usd','count'),
        stage1_additional_contribution_on_priced_days_usd=('stage1_additional_contribution_on_priced_days_usd',lambda x:x.sum(min_count=1)),
        paid_span_route_cost_usd=('stage2_cost_usd',lambda x:x.sum(min_count=1)),
        productive_time_route_cost_usd=('stage2_active_time_only_cost_usd',lambda x:x.sum(min_count=1)),
        paid_span_additional_contribution_usd=('additional_contribution_paid_span_usd',lambda x:x.sum(min_count=1)),
        productive_time_additional_contribution_usd=('additional_contribution_active_time_only_usd',lambda x:x.sum(min_count=1))).reset_index()
    route_summary.to_csv(out/'aggregate_route_comparison.csv',index=False,lineterminator='\n')
    reproduction=pd.read_csv(out/'artifact_reconciliation.csv')
    sensitivity=pd.read_csv(out/'additional_sensitivity.csv')
    text='''# Temporary integration review and executed results

This is the isolated integration branch, not a merge into main. It combines Fu Yan PR #2 and Hong Jin PR #1 source, the updated cost inputs and the existing observed data. See [methods, formulas and reproduction](INTEGRATION_METHODS_2026-11-22.md).

**Main finding:** demand reproduction is resolved, but the positive Stage 1 gains do not survive the tested Stage 2 route repricing assumptions on the conditionally priced subset. Cost/route-aware model refinement remains material; this branch does not establish profitable dispatches.

## Decision from the demand comparison

The latest PR closes the missing-core and validation handoff. Its hybrid is the same numerical case as the previous v2 file; its historical case matches Carlo's trial within floating-point rounding. These are three artifact versions but two distinct demand scenarios:

'''
    text+=markdown(reproduction)
    text+='''

Both published validation tables reproduce. Historical-only still has lower MAE/RMSE in all four pickup/return/rider categories at one and three hours; short pre-outage results are mixed and the hybrid has less negative bias. The latest code is more complete and reproducible, not a newly superior statistical estimator. Use its historical option as the supported base producer and its hybrid option as sensitivity, subject to the team's final review. No third identical optimization case is needed.

## Integrated pipeline results

'''
    text+=f"The pipeline evaluated {len(manifest['dates'])} previously explored validation dates, two demand cases and three policies: **{len(s)} policy evaluations**. These are retrospective perfect-information benchmarks, not a new sealed test or all five robustness datasets.\n\n"
    text+=markdown(aggregation)
    text+='\n\nAdditional contribution uses allocated trip values, not cash receipts. Both policies and the optimizer use the same pair-specific cost matrix, including driving labour. Solver summaries retain statuses and gaps; the largest optimized relative gap was '+f"{opt.mip_gap.max():.2%}"+'. Feasible-incumbent gains must not be called exact optimal gains.\n'
    text+='''

## Conditional routes and cost uncertainty

Only full-day conditional timing/capacity/precedence passes receive route costs. Uncertified routes have missing costs, not fictitious full-day totals. The table sums only priced days; use the priced-day count before making any cross-policy comparison.

'''
    text+=markdown(route_summary)
    text+='''

Paid-span costing charges labour between the first assigned hour and last completion, including waiting. Productive-time-only costing is a separate opportunity/incremental-cost assumption. Large differences reveal that average-load Stage 1 costs omit idle-span and stop effects. Stage 1 and Stage 2 costs are alternative estimates of the same operation and are not added.

A long paid span does not certify a single person's shift. Driver schedules, overtime, breaks, depots, true station inventory at visit times and intra-hour customer timing are not modelled. Conditional routes therefore do not establish an implementable or profitable dispatch. Route search minimizes hourly completion time for fixed jobs, not joint global monetary cost.

## Added objective and terminal-stock checks

'''
    cols=[x for x in ['case','date','scenario','solver_status','solver_gap','served_pickups','failed_returns','bikes_moved','redistribution_budget_usd','model_contribution_usd'] if x in sensitivity]
    text+=markdown(sensitivity[cols])
    text+='''

These scenarios run on the first selected date only. Equal-service minimizes unserved pickups plus failed returns, using equal request weights under an illustrative USD120 Stage 1 redistribution budget. Its financial contribution is reported separately, not used as its optimization objective. The terminal scenario requires every station's closing expected stock to be at least its observed opening stock. Infeasibility, if reported, is an outcome rather than a missing-data substitute.

The break-even table reports the maximum total redistribution cost per moved bike supported by incremental allocated service value net of return penalties. A second column removes fixed activation first to show the variable-cost threshold. Zero-move cases have no per-bike threshold.

## What was corrected

- PR #2 is the active producer; the earlier own-hour report/code is not the base demand input.
- Rental mileage is USD0.086992/km; the pasted USD0.0087 entry was a decimal error.
- Handling is USD0.985667 per bike, not per hour.
- Pair-specific driving labour is included, using road minutes instead of an invented speed.
- The daily vehicle fee is charged once; hourly vehicle rental and owner maintenance are not added again.
- Optimizer/evaluator pricing agree, and route handling is priced once through paid labour time.
- Source CSV line endings are stable across operating systems.
- Historical data and main are unchanged. PR #1's stale generated outputs were not imported.

## Course alignment and remaining work

Lecture 6 supplies flow/capacity structure; Lecture 7 supports mixed integer/continuous decisions and motivates routing; Lecture 8 supports the state-based route search; Lecture 4 supports re-solving uncertain-input scenarios. These lessons do not prove a particular demand estimator is true or make the conditional route check a classic TSP solution.

Before the final submission: confirm scope/cost/crew-time assumptions, reconcile report sections with the actual formulation, decide route-aware repair or state routing limitations, complete the selected sensitivity/robustness runs, and perform the final report edit. The five observed robustness packages are prepared but were not all optimized here. Their demand windows and missing-opening rules need separate handling. No external Google Doc was edited.

## Review files

- [Artifact reconciliation](../output/sf_bikeshare/integration_review_2026-11-22/artifact_reconciliation.csv)
- [Matched validation](../output/sf_bikeshare/integration_review_2026-11-22/matched_validation.csv)
- [Daily policy results](../output/sf_bikeshare/integration_review_2026-11-22/daily_policy_comparison.csv)
- [Conditional route costs](../output/sf_bikeshare/integration_review_2026-11-22/route_cost_sensitivity.csv)
- [Break-even costs](../output/sf_bikeshare/integration_review_2026-11-22/break_even_costs.csv)
- [Exact configuration and sources](../sf_bikeshare/integration_cost_config.json)
- [Run manifest](../output/sf_bikeshare/integration_review_2026-11-22/run_manifest.json)
'''
    (ROOT/'docs/INTEGRATION_REVIEW_2026-11-22.md').write_bytes(text.encode('utf-8'))
    evidence=dict(status='TEMPORARY_INTEGRATION_RESULTS',files={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in out.iterdir() if p.is_file() and p.name!='evidence_manifest.json'})
    (out/'evidence_manifest.json').write_bytes((json.dumps(evidence,indent=2)+'\n').encode())
    print(aggregation.to_string(index=False))
    print(route_summary.to_string(index=False))


if __name__=='__main__':main()
