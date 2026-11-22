# End-to-end pipeline review

## Assessment

The pipeline is cohesive for a retrospective operations-research study: audited observations feed attempted-demand estimates, economic assumptions feed a daily mixed-integer allocation model, and common accounting evaluates service and conditional contribution. Historical is the agreed base; hybrid and observed counts provide separate comparisons. The code/input handoff is ready and approved for main publication. Financial conclusions, operational feasibility and some report wording still require qualifications.

This review inspects source, published inputs and supplied results. The default project verification passed again. No optimization, demand-estimation or diversion experiment was rerun for this review. Google Docs were not edited. The reviewed pipeline was subsequently approved for publication on main.

## Alignment by stage

| Stage | Alignment with the objective | Assessment |
| --- | --- | --- |
| Observations and features | Same stations, dates, keys, dock capacities, midnight stocks, rider counts and metric distances feed the model | Consistent; DST, missing exposure and static-capacity interpretation stay explicit |
| Demand estimation | Historical training rates correct censored observations; served events are subtracted once; hourly outputs match model columns | Consistent. Hidden available windows test reconstruction, not actual unmet-demand truth |
| Economic inputs | Jason's trip allocations and cost assumptions determine value and redistribution cost | Consistent as an assumed contribution scenario; report cost and updated-cost extension must stay separate |
| Allocation MILP | Chooses integer moves/truck use under stock, capacity and hourly throughput constraints | Consistent with the stated daily aggregate model; fixed returns and within-hour order limit physical interpretation |
| Policy evaluation | No moves, occupancy rule and allocation solution use common demand, initial stock, capacity and cost accounting | Accounting is consistent; the policies have different information/look-ahead |
| Routing | Fixed transfers are checked for pickup/delivery precedence, onboard load and estimated timing | Appropriate extension; it does not repair Stage 1 customer timing or certify the supplied report's exact schedules |
| Sensitivity and writing | Demand cases, penalty/budget experiments and cost checks test selected assumptions | Completed scopes are identifiable. Additional city/time packages remain prepared inputs, not completed tests |

## Gaps and required actions

| Priority | Gap and consequence | Owner / action |
| --- | --- | --- |
| High: economics | The report uses USD0.30/km as an approximate travel coefficient, without explicit full driving-time labour or paid-span treatment. The separate route-repricing experiment reverses the positive Stage 1 gains under its tested assumptions. | Jason + Joohee: retain the report coefficients only as a clearly labelled approximation, discuss the extension and avoid claiming cash profit or economically justified real dispatches. A stronger operational claim requires consistent costs and suitable schedules. |
| High: route evidence | The supplied 14-day tables mark routing unchecked. Exact transfer/state/route files supporting the draft's claimed pass counts were not supplied. | Hong Jin + Joohee: provide the existing exact schedules and audit outputs/settings if available. Do not rerun all experiments merely for an upload. Without the files, remove or qualify executability/pass-count claims. |
| High: comparison interpretation | The optimizer uses the full day's estimated demand; the occupancy rule uses current stock and no look-ahead. Their gain difference combines information/planning with the allocation method. | Joohee + Hong Jin + Carlo: describe an informed retrospective benchmark versus a stock-balancing rule. For a future deployment comparison, evaluate forecast-based policies with matched information. |
| High: report accuracy | At penalty USD0.50, the supplied returned allocation is USD24.79 worse than no rebalancing. Solver gaps refer to the full objective, so a small incremental gain is not necessarily certified. | Hong Jin + Joohee + Carlo: correct the row; distinguish feasible incumbents from exact optima. In a future dispatcher choose the better evaluated feasible candidate, including no rebalancing. Do not alter the supplied snapshots silently. |
| Model boundary | Returns stay fixed when pickups are lost, diverted returns may already be counted nearby, and each day restarts from historical midnight stock without an end target. This is not a continuously simulated ten-week policy. | Joohee + Fu Yan: explain independent daily scenarios and approximate flow consistency. Link accepted departures to returns, diversion and terminal states only in a separately validated extension. |
| Claim strength | Proportional aggregate rider service is not FCFS; the 86% neighbour-return ratio does not identify 86% of individual riders; pre-outage underprediction does not establish conservative outage benefits. | Carlo + section owners: apply the [report reconciliation](REPORT_RECONCILIATION_2026-11-22.md). The small weighted cost term in the service objective is also not a strict lexicographic tie-break. |
| Scope and generalization | Five additional city/time subsets, lower-capacity scenarios and some terminal/rider-value variations are not completed report experiments. The evaluation dates were already examined. | Team: state completed versus proposed checks accurately; report extra runs only if required by the agreed scope. No new data collection is needed to finalize the current retrospective study. |

## What is ready

**Routing correction:** [saved re-solved route evidence is now downloadable](ROUTING_EVIDENCE_RECTIFICATION_2026-11-22.md), with replay/recheck results and daily plan-total differences. This closes access to Carlo's evidence, not the missing exact Joohee schedule handoff. Report-ready conditional wording and cost/active-day qualifications are included there.

The observed inputs, two estimated-demand outputs, complete producer, model/policy source, supplied result tables, supporting reports and verification command are available together. Jason's research contribution is represented in the economics and Section 1–2 ownership; he does not need a separate script. Demand is reconciled across the team; it does not need to be reopened for the above reporting/model limitations.

The next step is a focused consistency edit and collection of existing route evidence, followed by the team's final scope/cost sign-off. No blanket experiment rerun is recommended by this review. A stronger feasibility/profit/generalization claim would require further modelling or evidence rather than a wording change alone.

- [Complete pipeline and process owners](SF_Bikeshare_Project_Pipeline_Report.md)
- [Code/result handoff and provenance](JOOHEE_HANDOFF_2026-11-22.md)
- [Report corrections](REPORT_RECONCILIATION_2026-11-22.md)
- [Separate updated-cost experiment and limits](INTEGRATION_REVIEW_2026-11-22.md)
- [Downloadable 14-day results](../output/sf_bikeshare/optimization_14days_2026-11-22/README.md)
- [Penalty, budget and diversion results](../output/sf_bikeshare/extra_experiments_2026-11-22/README.md)

Publication status: Carlo explicitly approved the reviewed pipeline for `main` as the team's main reference. The reviewed PR #1/#2 heads are included as merge ancestors, with superseded generated outputs excluded as described in the [release provenance](PIPELINE_RELEASE_2026-11-22.md). This publication retains the open modelling/report gaps above; it does not certify operational profit or exact route feasibility.
