# Temporary integration review and executed results

> **Dated experiment:** the original temporary-branch status below records when these checks were run. The complete project pipeline is now published with historical base and hybrid sensitivity. This updated-cost experiment remains separate from Joohee's unchanged report-cost results. See the [current pipeline](SF_Bikeshare_Project_Pipeline_Report.md).

This is the isolated integration branch, not a merge into main. It combines Fu Yan PR #2 and Hong Jin PR #1 source, the updated cost inputs and the existing observed data. See [methods, formulas and reproduction](INTEGRATION_METHODS_2026-11-22.md).

**Main finding:** demand reproduction is resolved, but the positive Stage 1 gains do not survive the tested Stage 2 route repricing assumptions on the conditionally priced subset. Cost/route-aware model refinement remains material; this branch does not establish profitable dispatches.

## Decision from the demand comparison

The latest PR closes the missing-core and validation handoff. Its hybrid is the same numerical case as the previous v2 file; its historical case matches Carlo's trial within floating-point rounding. These are three artifact versions but two distinct demand scenarios:

| artifact | latest_producer | rows | maximum_numeric_difference | canonical_lf_byte_identical | interpretation |
| --- | --- | --- | --- | --- | --- |
| historical_demand_station_hour.csv | historical | 57120 | 5.33e-15 | False | Same demand case; producer/validation handoff updated |
| estimated_demand_station_hour_hybrid.csv | hybrid | 57120 | 0.000 | True | Same demand case; producer/validation handoff updated |

Both published validation tables reproduce. Historical-only still has lower MAE/RMSE in all four pickup/return/rider categories at one and three hours; short pre-outage results are mixed and the hybrid has less negative bias. The latest code is more complete and reproducible, not a newly superior statistical estimator. Use its historical option as the supported base producer and its hybrid option as sensitivity, subject to the team's final review. No third identical optimization case is needed.

## Integrated pipeline results

The pipeline evaluated 14 previously explored validation dates, two demand cases and three policies: **84 policy evaluations**. These are retrospective perfect-information benchmarks, not a new sealed test or all five robustness datasets.

| case | policy | days | served_pickups | unmet_pickups | failed_returns | bikes_moved | additional_contribution_usd | additional_served_pickups |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| historical | no_rebalancing | 14 | 11636.705 | 1647.279 | 1336.482 | 0.000 | 0.000 | 0.000 |
| historical | optimized | 14 | 12377.308 | 906.676 | 668.519 | 756.000 | 176.397 | 740.603 |
| historical | rule_based | 14 | 12096.676 | 1187.309 | 1049.835 | 1736.000 | -1820.632 | 459.971 |
| hybrid | no_rebalancing | 14 | 11697.784 | 2013.032 | 1435.315 | 0.000 | 0.000 | 0.000 |
| hybrid | optimized | 14 | 12555.509 | 1155.307 | 692.306 | 883.000 | 316.086 | 857.725 |
| hybrid | rule_based | 14 | 12197.277 | 1513.540 | 1139.326 | 1772.000 | -1810.358 | 499.493 |

Additional contribution uses allocated trip values, not cash receipts. Both policies and the optimizer use the same pair-specific cost matrix, including driving labour. Solver summaries retain statuses and gaps; the largest optimized relative gap was 2.48%. Feasible-incumbent gains must not be called exact optimal gains.


## Conditional routes and cost uncertainty

Joohee's exact original report plans were subsequently supplied and [independently verified](../output/sf_bikeshare/optimization_14days_2026-11-22/EXACT_PLAN_AUDIT_README.md). Those exact plans pass all 133 active hours at one-minute setup and yield -USD878.71/-USD4,191.83 in route-cost scenarios. The earlier re-solve results below remain distinct.

These checks apply to Carlo's separate re-solved allocations, not the exact plans behind Joohee's USD202.32 report result. See the [schedule differences and downloadable route evidence](ROUTING_EVIDENCE_RECTIFICATION_2026-11-22.md). Historical optimized passes are 13/14 calendar days, including five no-move days (8/9 active days); the rule passes 3/14. Equal daily bike totals alone cannot verify exact report-plan identity.

Only full-day conditional timing/capacity/precedence passes receive route costs. Uncertified routes have missing costs, not fictitious full-day totals. The table sums only priced days; use the priced-day count before making any cross-policy comparison.

| case | policy | days | conditionally_priced_days | stage1_additional_contribution_on_priced_days_usd | paid_span_route_cost_usd | productive_time_route_cost_usd | paid_span_additional_contribution_usd | productive_time_additional_contribution_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| historical | optimized | 14 | 13 | 135.187 | 5083.192 | 2004.178 | -3782.262 | -703.248 |
| historical | rule_based | 14 | 3 | -295.155 | 2302.191 | 752.149 | -2257.504 | -707.462 |
| hybrid | optimized | 14 | 13 | 262.738 | 4997.118 | 2285.899 | -3453.556 | -742.337 |
| hybrid | rule_based | 14 | 3 | -280.961 | 2286.715 | 734.445 | -2228.985 | -676.715 |

Paid-span costing charges labour between the first assigned hour and last completion, including waiting. Productive-time-only costing includes driving, handling and setup and is a separate opportunity/incremental-cost assumption. These are proxy cost scenarios, not observed expenses or certified worker shifts. Large differences reveal that average-load Stage 1 costs omit idle-span and stop effects. Stage 1 and Stage 2 costs are alternative estimates of the same operation and are not added.

A long paid span does not certify a single person's shift. Driver schedules, overtime, breaks, depots, true station inventory at visit times and intra-hour customer timing are not modelled. Conditional routes therefore do not establish an implementable or profitable dispatch. Route search minimizes hourly completion time for fixed jobs, not joint global monetary cost.

## Added objective and terminal-stock checks

| case | date | scenario | solver_status | solver_gap | served_pickups | failed_returns | bikes_moved | redistribution_budget_usd | model_contribution_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| historical | 2015-04-06 | equal_service_budget | 0 | 0.001 | 1055.312 | 97.921 | 57.000 | 120.000 | 981.386 |
| historical | 2015-04-06 | terminal_stock | 0 | 0.008 | 1060.358 | 55.796 | 172.000 | not available | 914.859 |
| hybrid | 2015-04-06 | equal_service_budget | 0 | 0.000804 | 1066.727 | 105.922 | 57.000 | 120.000 | 985.313 |
| hybrid | 2015-04-06 | terminal_stock | 0 | 0.005 | 1083.118 | 58.805 | 186.000 | not available | 920.909 |

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
