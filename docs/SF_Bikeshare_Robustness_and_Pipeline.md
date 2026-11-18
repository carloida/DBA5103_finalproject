# SF Bike Share: robustness proposal and remaining pipeline

> Historical planning note. Later on 18 November, Carlo authorized preparation and publication of five additional cases. They are now built in the [separate robustness folder](../output/sf_bikeshare/robustness_testing/README.md). The [current pipeline report](SF_Bikeshare_Project_Pipeline_Report.md) supersedes preparation-status statements below. Policy experiments remain pending; the earlier recommendations are retained for context.

Prepared 18 November 2026. This is a proposed evaluation plan based on Carlo's follow-up message, the supplied project guideline and the course notes. No new region/window is approved, no extra dataset is built and no optimization is run by this note. The uploaded V3 dataset remains unchanged.

## Recommendation

Keep the 34-station SF pilot as the main case. First obtain a working allocation model, consistent inventory simulation and baseline comparison. Then evaluate a later SF period and a small set of demand/cost/resource scenarios. Add one other city only if the core results and report are on track.

Testing another date window is a temporal robustness exercise. Testing another city is a transferability exercise across operating contexts. Both are appropriate OR evaluation activities, but they answer different questions. Changing city and dates together initially would make it harder to tell which change explains a result.

These exercises evaluate the formulation and decision method under other inputs. They do not establish universal model accuracy or prove that the method generalizes beyond this historical bike-share system. Scenario tests also do not, by themselves, turn the formulation into a robust-optimization model; that term requires an uncertainty treatment inside the optimization formulation.

## Support in the course material

| Material | Relevant evidence | Application |
| --- | --- | --- |
| Project guideline, PDF pp. 1-2 | Practical projects should connect assumptions to reality, assess robustness to changed conditions and discuss how better information could improve the model; the hospital-porter example varies demand and capacity | A credible SF case with transparent scenarios is sufficient; a second city is optional |
| Lecture 4, PDF pp. 24-26 | Sensitivity analysis studies changes in resources, prices and incomplete input knowledge | Vary demand, trip value, handling cost and truck resources, then re-solve the integer model |
| Lecture 6, PDF pp. 44-45 | Container repositioning on a time-expanded network | Rebuild station-time inputs for another location/window while preserving the formulation |
| Lecture 6, PDF p. 58 | Repeated network solves across sampled demand realizations evaluate a fixed design | Supports scenario evaluation, while the bike-share application must also enforce the information available when operational decisions are made |
| Project guideline, PDF pp. 3-4 | Evaluation includes model definition, sound methodology and interpretation/limitations | Report feasible service gains, computational performance and the limits of financial/demand assumptions |

Page numbers above are PDF page positions. This note draws on the relevant sections, not an exhaustive review of all textbook material.

## A small experiment set

| Priority | Experiment | What remains fixed | What changes / interpretation |
| --- | --- | --- | --- |
| Core | Main SF evaluation | 34-station cohort, policy definitions, accounting perspective, evaluation protocol | Compare no redistribution, a simple resource-matched rule and optimized allocation |
| High | Later SF calendar window | Same cohort, formulation, estimator recipe and policy settings | New dated observations and initial stocks; tests performance over time |
| High | Demand scenarios | Same network and common conditions for each competing policy | For example 0.8/1.0/1.2 times demand as explicitly assumed stress factors; keep OD/returns/bike conservation consistent |
| High | Cost/resource scenarios | Same demand instance and comparison rules | Low/base/high trip value and cost, or alternative truck resources; these are scenario choices, not measured operator inputs |
| Optional | One other city, preferably the same evaluation dates initially | Same formulation, cleaning/estimation recipe and policy definitions | New station set, demand, inventory, docks, travel matrix and boundary flows; tests transferability |
| Optional | Another city in another date window | Protocol chosen before policy results | Combined context change; interpret after the separate temporal/location checks |

San Jose is a possible second-city candidate because the existing station table lists 16 stations there. Its eligibility, activity, status coverage, dates and boundary flows must be audited before selecting the final cohort. It is not yet an approved or prepared second case. No new trip-data provider is needed merely to test this extension: the full original Bay Area database is already available locally.

Use a limited scenario grid rather than every combination. Numerical factors above are suggested experiments and need team agreement.

## Implementation protocol

1. **Agree on the main objective and rules.** Decide whether rider values are explicitly allocated service-value scenarios or defensible incremental cash contributions. Confirm operating horizon, within-hour order, transfer/customer travel times, effective capacity, external-flow failures, activation periods, depot and end conditions.
2. **Separate estimation, tuning and evaluation.** V3 retains 9 February-5 April for training and 6-19 April for exploratory validation. A previously proposed later evaluation candidate is 20 April-3 May 2015, subject to coverage and team agreement. Earlier full EDA has examined later data, so do not describe this as a completely untouched or sealed holdout. Fix the evaluation protocol before inspecting policy gains.
3. **Estimate inputs without future leakage.** Fu Yan applies the agreed demand estimator using only observations preceding each decision. A rolling implementation may update estimates using newly available past data, under a rule selected in advance. Re-estimating local demand with the same recipe is different from retuning the method to make a test result look favorable.
4. **Build a reusable instance loader.** Treat city/cohort, start/end dates and parameter scenarios as inputs. Supply the same V3 table meanings and metric units for each case. The current enrichment script hard-codes the SF pilot; a city/date-parameterized builder is future implementation work, not a capability already completed.
5. **Rebuild context-specific inputs.** For a new city/window, re-extract rider-split endpoints, exposure, opening inventories, capacity diagnostics, OD/return lags, horizon transit and boundary flows. A new city also needs a new road matrix and a specified depot/vehicle scenario. Review whether SF cost proxies are applicable; retain common cost assumptions only as an explicitly controlled scenario.
6. **Run every policy on each instance.** Start from the same bikes/docks and in-transit state, expose policies to the same request scenarios and enforce the same resources and feasible operating rules within that comparison. Re-optimize the new instance; do not copy an SF transfer schedule to different station IDs. If Stage 2 cannot execute the allocation, revise/re-evaluate it or report the failure.
7. **Respect the information timeline.** A policy must choose moves from forecasts and information available at that time, then face subsequent requests. Optimizing against the complete realized day gives a perfect-information benchmark unless that information is explicitly assumed available. Re-solving across assumed known scenarios is useful sensitivity analysis, but is not by itself evidence of deployable performance under unknown future demand.
8. **Evaluate simulated service consistently.** Additional accepted internal trips must generate later arrivals or remain in transit. Historical returns cannot simply be replayed unchanged after different pickups are rejected. Historical inventory paths already include real operations and are not the no-redistribution baseline. Return failures must be handled without double-counting lost journeys.
9. **Compare paired results and document failures.** Calculate policy differences for the same day/scenario. If practical, summarize variation across days or whole-day/week resamples; avoid treating every station-hour as independent. Include infeasibility, solver status, time limits and optimality gaps instead of discarding difficult runs.

## Result table to populate after implementation

| Measure | Why it matters |
| --- | --- |
| Additional served trips versus no redistribution | Main service effect under the stated demand model |
| Unmet requests and service rate | Service quality, conditional on estimated/scenario demand |
| Bikes moved, road km and operating/handling hours | Resources used and operating explanation |
| Estimated redistribution cost and cost per additional trip served | Efficiency; the ratio is unavailable when extra served trips are zero and needs care when the change is negative |
| Modeled incremental contribution, with the rider-value scenario named | Conditional economic interpretation, not measured operator profit |
| Executable-route share / route failures | Whether aggregate allocation can be implemented |
| Solve time, termination status and optimality gap | Computational performance and limits |

Compare policies within each location/window first. Across cities, report service percentages, per-day effects and resource-normalized outcomes alongside totals. Raw objective values differ with station count, demand and resource scale, so a larger raw objective does not establish a better method. Label estimated attempted demand separately from observed completed trips.

## Whole project pipeline and ownership

| Step | Deliverable / dependency | Lead | Paper section |
| --- | --- | --- | --- |
| 1. Scope, source audit and V3 data | Completed observed-data package; review flags and finish focused EDA | Carlo | 3; motivation evidence for 1 |
| 2. Demand estimation | Matched exposure, pooled estimates, fallback rules, validation and uncertainty | Fu Yan with Carlo | 3; assumptions in 7 |
| 3. Economic/vehicle inputs | Sources, units, price year, scenario ranges and value interpretation | Jason with Fu Yan/Joohee | 1-2; input table referenced in 4 and 7 |
| 4. Mathematical formulation | Variables, objective, inventory/conservation, docks, activation, timing and boundary constraints | Joohee | 4 |
| 5. Small working implementation | Sanity cases, conservation/feasibility checks, solver setup, then daily/rolling SF instances | Hong Jin with Joohee | 5; code appendix |
| 6. Main baseline comparison | No moves, simple rule and optimized allocation under common information and conditions | Hong Jin | 6 |
| 7. Routing extension | Executable route checks and estimated Stage 1 versus Stage 2 cost comparison | Hong Jin/Joohee | 5 and 7 |
| 8. Sensitivity and later-SF evaluation | Changes in costs/resources/demand, paired evaluation and failure reporting | Hong Jin; Joohee and Fu Yan interpret | 6-7 |
| 9. Optional second-city experiment | Additional audited instance using the same method; proceed only after the main results work | Carlo prepares inputs; Fu Yan estimates; Joohee/Hong Jin run and interpret | 7 |
| 10. Conclusions, assembly and final edit | Findings tied to evidence, limitations, consistent notation/units, citations and code appendix | Carlo/Hong Jin conclusions; Carlo final edit; each owner supplies their section | 8 and whole paper |

The introduction and literature work can proceed now. Demand estimation, parameter research and formulation can proceed in parallel using the V3 schema. Hong Jin can begin with small illustrative inputs before every parameter is final, provided those runs are not presented as empirical results. Final evaluation requires consistent agreed inputs and rules.

The supplied ownership outline fits the guideline. Its roughly 10-13 narrative pages are a planning estimate; the guideline's 8-14 pages are guidance, not a strict limit. Keep one clear operational question. A second city should strengthen the evidence rather than delay the core case or crowd out explanation of the model.

## What Carlo should do next

- Share the robustness idea as a proposal, retaining SF as the main agreed case.
- Finish the observed-data section and explain capacity, DST and long-trip flags. Do not silently resolve model assumptions through data cleaning.
- Coordinate V3 inputs with Fu Yan/Joohee/Hong Jin; prepare additional windows only after the experiment protocol is agreed.
- Give priority to a later SF period and a small scenario grid. Prepare another city only after the main model and evaluation are working.
- Collect each owner's results and methods for the final consistency edit; do not take over all modeling workstreams.

Supporting local materials: [project guideline](../Project_Guideline.pdf), [Lecture 4](../Lecture4%20DualitySensitivity.pdf), [Lecture 6](../Lecture6%20Network.pdf), [V3 guide](../output/sf_bikeshare/model_inputs_v3/README.md), [current status](PROJECT_STATUS.md), and [cost-formula proposal](SF_Bikeshare_Cost_Formula_Revision.md). Course PDFs stay local and are not part of the GitHub handoff.
