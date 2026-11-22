# Temporary demand cost and model integration

> **Dated experiment:** the original temporary-branch status below records when these checks were run. The complete project pipeline is now published with historical base and hybrid sensitivity. This updated-cost experiment remains separate from Joohee's unchanged report-cost results. See the [current pipeline](SF_Bikeshare_Project_Pipeline_Report.md).

This branch integrates the latest Fu Yan demand producer from PR #2 with the model/evaluator source from PR #1. Main and the upstream PRs remain unmerged. The original PR #1 generated demand, duplicate nested CSV and old result tables were not imported as current results.

The active pipeline is:

1. Frozen V3 observations and the minute supplement.
2. Fu Yan's complete producer for historical and hybrid demand, rates, episodes and corrected validation.
3. One documented cost configuration with metric pair-specific handling, vehicle travel and driving-labour costs.
4. The same no-rebalancing, equal-occupancy and mixed-integer policies evaluated on each demand case.
5. Conditional pickup/delivery route checks and separate route-cost repricing.
6. Paired demand-method comparisons, solver-status reporting, break-even costs and explicit limitations.

See the [executed review](INTEGRATION_REVIEW_2026-11-22.md) for measured results and remaining work. Earlier case reports are dated audit snapshots; their missing-core findings are resolved by the PR #2 source present on this branch.

## Source versions and demand cases

- Main starting point: 64fe8cd9fa5aa5beac6b1a4a66339bd3acda08ed.
- Fu Yan PR #2 source: 169043a843d4f67cf9ca3381d0d37be5a633c822.
- Hong Jin PR #1 source: 244dda807805acbd28b33c56292e6eecb1de936a.

The historical output previously constructed by Carlo and the new producer's historical output agree within floating-point rounding. The earlier Fu Yan v2 hybrid and latest producer's hybrid agree numerically and byte-for-byte after canonical LF line endings. Consequently, the three artifact versions requested for comparison represent **two distinct demand cases**, not three new estimators.

PR #2 supplies the previously missing core and reproduces both published matched-validation tables. Its pooled/unresolved fallback tests pass. For cross-platform output hashing this branch explicitly writes LF CSV record endings. Validation also scores only the paired finite target subset when future cases have unsupported rates, and reports missing errors when no shared target remains. These edge-case changes preserve all main-case metrics.

The original own-hour method in PR #1 is retained as legacy source for attribution, not the active input producer. Neither it nor the old unlimited 15-minute predecessor method is silently substituted into the current pipeline.

## Updated redistribution cost

The configuration is in [integration_cost_config.json](../sf_bikeshare/integration_cost_config.json). Source observations, price proxies and operating assumptions remain distinguishable.

| Input | Adopted value | Interpretation |
| --- | ---: | --- |
| Rental | USD60/van-day | 2015 Enterprise Florida-contract proxy, not SF operator expenditure |
| Rental mileage | 0.14/1.609344 = USD0.086992/km | Corrects the pasted summary's USD0.0087/km decimal error |
| Fuel price | USD0.882/litre | Rounded March 2015 California common-price scenario |
| Fuel use | 16.8 litres/100 km | Specified Ford wagon proxy, not verified rental-van duty cycle |
| Vehicle cost | USD0.235168/km | Rental mileage plus fuel; no extra owner-maintenance allowance |
| Base wage | USD19.35/hour | BLS May 2016 SF occupational mean, a year-mismatched local proxy |
| Benefits ratio | 27.55/18.03, about 1.528 | BLS March 2015 national occupation-group proxy |
| Loaded wage | USD29.57/hour | Adopted rounded rate |
| Load/unload | One minute each | Two operations per moved bicycle; scenario, not observed SF timing |
| Handling | USD0.985667/bike | Corrects the pasted calculation's USD/hour label |
| Average load / throughput | 15 bikes / 15 bikes per truck-hour | Separate analytical assumptions |
| Onboard route capacity | 25 bikes | Separate unverified operating assumption |
| Setup | One minute per stop | Illustrative setting; not a measured parking time |

For stations $i,j$, road distance $d_{ij}$ in km and travel time $\tau_{ij}$ in minutes:

$$
h=W(t_{\rm load}+t_{\rm unload})/60,
\qquad
c_{ij}=h+\frac{k_{\rm vehicle}d_{ij}+W\tau_{ij}/60}{\bar L}.
$$

Stage 1 uses:

$$
C_1=60y+\sum_{i,j,t}c_{ij}x_{ijt}.
$$

The optimizer and separate policy evaluator both receive the same pair-cost matrix. The previous pilot coefficient USD0.30/km is not treated as a completed calibration of travel labour. No invented average speed is needed because the existing directed matrix supplies travel minutes.

For a complete conditional one-truck route:

$$
C_2=60y+29.57H+0.235168D+A.
$$

Handling labour is already inside $H$, so the per-bike handling term is not added again. Stage 1 and Stage 2 describe the same operation; compare them rather than summing them. The fixed rental is charged once per activated day, without a second hourly vehicle-rent charge.

The primary route labour basis is the span from the first assigned hour's start to the last completion, including gaps. Productive-activity-only labour is also reported as an alternative accounting assumption. A long paid span is not evidence that one worker can drive that entire span: crew rosters, shift limits, overtime and breaks are not modelled. Fees $A$ are excluded from the base; this does not verify that parking, tolls or insurance charges are absent.

If the full conditional route cannot be certified, full-route cost and the cost gap are left missing. Partial-hour distances are not presented as a complete route.

## Mathematical model and lecture alignment

The active model remains a time-expanded, restricted-neighbour MILP. Relocation quantities and truck activation are integer; inventory, served requests and failed returns are continuous expected quantities. Each station-hour serves the minimum of post-transfer inventory and pickup demand. Its rider composition is allocated proportionally; it is not an event-level first-come-first-served simulation.

The base graph has five nearest destinations per origin, not every station pair. Transfers occur at hour start, pickups before fixed returns. Daily midnight stock is observed; each day is independent. No end-stock target is imposed in the base.

The integration adds:

- One consistent pair-cost matrix across optimizer/evaluator.
- A nonempty-use link for truck activation.
- An optional end stock at least opening-stock condition.
- An optional equal-service objective: minimize unserved pickups plus failed returns under an explicit Stage 1 redistribution-cost budget. The illustrative budget is USD120/day, not a confirmed team resource limit.

The service objective omits a constant total pickup-demand term when solved, which does not change the minimizer. It gives member/casual requests equal service weight; its reported financial metrics are still calculated separately using the same allocated trip values.

Course connections:

| Notes | Connection and boundary |
| --- | --- |
| Lecture 6 Network, pp. 17-18 | Inventory conservation, flow/capacity constraints and costed directed arcs |
| Lecture 7 IP, p. 4 | Mixed integer/continuous variables; fractional expected demand does not require rounding |
| Lecture 7 IP, p. 22 | Routing extension relates to TSP, but this is an open pickup/delivery problem with capacity and precedence |
| Lecture 8 DP, pp. 14, 27-28 | State/transition/value ideas support the fixed-job route search |
| Lecture 4 Duality and Sensitivity, pp. 25-26 | Re-solve under uncertain inputs; LP allowable ranges do not replace MIP scenario analysis |

Stage 2 searches earliest-finish fixed-job routes within each hour, then carries the end position forward. It is not a joint minimum-cost route/allocation optimizer. Failure of sequential chaining alone does not prove that every alternative day route is infeasible.

## Report reconciliation

The latest pasted Section 3.4, which uses historical as base and hybrid as sensitivity, matches PR #2. The earlier own-hour draft and its 58,614/7,292 pickup totals are superseded and must not be merged into the final method/results.

Correct these statements during the report merge:

1. Historical rates are piecewise constant by clock hour, not necessarily constant over an entire long episode.
2. The opening rule selects the latest preceding snapshot and then checks validity/freshness; it does not skip a bad latest snapshot to find an older valid one.
3. A small percentage of adjusted hours does not mathematically bound missed-demand magnitude or policy impact.
4. The dashboard's 63,751 trips are a separate descriptive scope, not the 34-station pickup total of 62,243.
5. Trip values are allocations, not additional subscription/pass cash receipts.
6. Both validation and policy evaluation dates have already been explored; do not call them a new sealed test.
7. Modelled positive contribution under Stage 1 is not proof of a feasible, profitable dispatch after route costs.

The branch does not edit Google Docs. These notes are for the team's manual final merge.

## Reproduction

From a fresh environment in this branch:

    python -m pip install -r requirements-integration.txt
    python sf_bikeshare/test_demand_estimation.py --hourly output/sf_bikeshare/model_inputs_v3/station_hour_observed.csv.gz --minute-dir output/sf_bikeshare/demand_estimation_inputs_v3
    python sf_bikeshare/test_integration.py
    python sf_bikeshare/run_integrated_pipeline.py --build-demand --extra-sensitivity
    python sf_bikeshare/summarize_integration.py

Use --dates followed by ISO dates for a smaller pilot, --time-limit to set the per-MILP cap, or --skip-routing for a Stage 1-only diagnostic. Generated full demand/target/detail tables live under ignored tmp; compact results and manifests are under the integration-review output folder.

The source demand module currently targets the main February-April window. The five prepared robustness packages require case-specific scope/availability inputs and support/opening-stock rules before they can be claimed as completed experiments. No results for those cases are fabricated.

## References

- [Enterprise 2015 price sheet](https://www.fa.ufl.edu/wp-content/uploads/2019/04/Enterprise-National-Pricing-and-Age-Information.pdf), truck-rental page: adopted rate is a contract/year proxy with insurance exclusions and a date after the study window.
- [BLS May 2016 SF occupation table](https://www.bls.gov/oes/2016/may/oes_41884.htm), occupation 53-3033; [BLS March 2015 compensation release](https://www.bls.gov/news.release/archives/ecec_06102015.htm), Table 6.
- [EIA California gasoline history](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=M&n=PET&s=EMM_EPMR_PTE_SCA_DPG); [Ford 2015 Transit brochure](https://cdn.dealereprocess.org/cdn/brochures/ford/2015-transit.pdf).
- [Pal and Zhang (2017)](https://doi.org/10.1016/j.trc.2017.03.016), experimental handling assumptions.
- [PR #2](https://github.com/carloida/DBA5103_finalproject/pull/2), [PR #1](https://github.com/carloida/DBA5103_finalproject/pull/1), and the local course notes identified above.

Course PDFs are referenced but not distributed. The statistical estimator and scenario parameters remain project adaptations, not verified Bay Area Bike Share operating rules.
