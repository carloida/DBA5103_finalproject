# Bike Share Project Pipeline and Robustness Plan

Prepared by Carlo | 18 November 2026

## Project pipeline and current status

We can formally begin report writing now. The observed-data scope and a reproducible data handoff are available. We should write the background, literature, data preparation and planned methodology while the team finalizes demand, operating assumptions and formulation. Results and financial conclusions must follow actual model runs.

### Purpose and operational question

Our main case remains 34 San Francisco stations over 9 February-19 April 2015, at hourly resolution. We ask where, when and how many bikes to redistribute to improve modeled service relative to no redistribution, within inventory, dock, timing and vehicle limits. Economic contribution is conditional on an explicitly agreed trip-value interpretation; allocated membership revenue is not automatically marginal cash revenue.

### Working sequence and responsibility

| Step | Work and output | Lead |
| --- | --- | --- |
| 1 | Prepare and audit observations. Main V3 plus five robustness cases; quality flags and metric units. | Carlo |
| 2 | Estimate attempted demand. Pool matched counts/exposure; validate fallbacks and uncertainty. | Fu Yan with Carlo |
| 3 | Agree parameters and assumptions. Trip-value interpretation, vehicle inputs, costs and operating rules. | Jason with Joo Hee |
| 4 | Define the allocation model. Inventory, bike conservation, dock bounds, transfer time and activation. | Joo Hee |
| 5 | Implement and compare policies. Start small, then compare no moves, a rule and optimized allocation. | Hong Jin with Joo Hee |
| 6 | Check routes and estimated costs. Onboard load, handling/travel time, depot rules and cost reconciliation. | Hong Jin with Joo Hee |
| 7 | Evaluate robustness. Repeat the same method across cities/periods and selected scenarios. | Team |
| 8 | Interpret and finalize the paper. Explain service/cost trade-offs, failures, limitations and recommendations. | Carlo and section owners |

Demand estimation, parameter research and formulation (steps 2-4) can progress together using the fixed data schema. Hong Jin can begin small sanity instances before all empirical inputs are final. Do not present illustrative runs as observed performance.

## Robustness design and separate datasets

Five additional subsets have been prepared in a separate robustness_testing folder. With the unchanged main V3 case, they form two cities by three non-overlapping calendar windows. Every case is ten weeks long: eight weeks for estimation and two labeled validation for retrospective evaluation. Earlier EDA has examined the broader source, so these are not sealed holdouts.

| Case | City | Inclusive dates | Rows |
| --- | --- | --- | --- |
| D0 main | SF | 9 Feb-19 Apr 2015 | 57,120 |
| R1 | San Jose | 9 Feb-19 Apr 2015 | 26,880 |
| R2 | SF | 2 Jun-10 Aug 2014 | 57,120 |
| R3 | San Jose | 2 Jun-10 Aug 2014 | 26,880 |
| R4 | SF | 20 Apr-28 Jun 2015 | 57,120 |
| R5 | San Jose | 20 Apr-28 Jun 2015 | 26,880 |

### What is held consistent

All five additions match the 51-column V3 hourly schema and all 21 core table schemas, including names, order and SQL types. Their station, day, OD, boundary, transit and distance tables retain the same meanings. Physical units are metric and currency is USD. SF has 34 stations and San Jose 16; natural row counts differ without changing duration or inventing observations.

### Build evidence and remaining data rules

Each added case passed 65 checks and 18 export row-count readbacks: 325 checks and 90 readbacks overall. The original database was read-only and V3 was preserved. Current San Jose road estimates were fetched once and cached; the SF road cache was reused. These are driving proxies, not historical truck logs.

Each additional SF window has four unusable midnight stocks, retained as NULL with flags; one affects the later window's evaluation period. San Jose midnight stocks are fresh throughout. Agree the same initialization fallback or complete-day exclusion rule before policy results are inspected. Capacity and long-trip diagnostics remain visible.

### What the design can establish

Compare location effects within common dates and period effects within each city. The cases share dates, stations and source history, so they are dependent. Six cases is our practical design choice, not a universal minimum or proof of general validity. Demand intensity differs substantially across cities; little benefit from rebalancing can be a valid result.

## Model construction and fair evaluation

### Stage 1 allocation

Joo Hee defines an integer model on station-time nodes. It chooses relocations while conserving bikes, bounding station stock and docks, linking accepted customer trips to later arrivals/in-transit stock, respecting transfer timing and activating truck resources. Opening stock is a dated initial condition, not an hourly reset to the historical inventory path.

The proposed allocation cost is activation plus bikes moved times handling and allocated distance cost: C1 = sum(F z) + sum[(h + k d / average_load) x]. Here h is USD per relocated bike including load/unload, k is variable USD per truck-km, and d is km. Average load is positive and distinct from onboard capacity and hourly throughput. The activation billing period must be defined.

### Stage 2 route checks

Route the proposed movements and verify visit feasibility, onboard load, handling/setup/travel time, depot legs and end conditions. Evaluate C2 = F z + (W + V) H + P G + M D + A for consistent activated vehicle periods. Fuel litres may be approximated by G = D q / 100 with q in litres/100 km. Include each cost once; compare C2 with C1 rather than adding both as separate expenses.

An infeasible route requires revised movements and reevaluation, or an explicit failure report. A TSP visit order alone is insufficient. Both costs remain estimates, and sequential optimization does not establish joint global optimality.

### Common comparison protocol

Evaluate no redistribution, a resource-matched rule and optimized allocation on the same city-day starting stocks, in-transit bikes, request scenarios and operating limits. Moves use forecasts and information available before requests occur. Solving with the full realized future is a perfect-information benchmark, not normal operational performance. Unavailable external pickups/returns need explicit rules.

Up to 14 evaluation city-days per case gives 84 city-days and 252 policy-day evaluations for three policies before exclusions, cost/demand scenarios or stochastic replications. Use paired policy differences and preserve day/week dependence. If simulations or heuristics are stochastic, choose repetitions from a variability pilot and use common scenarios/seeds where appropriate.

After the base comparisons, test agreed low/base/high costs and rider values, demand stress factors and truck/handling resources. These are explicit scenario choices. Start with a small experiment budget and selected adverse combinations rather than every possible factor combination.

### Results to report

Report additional served trips, unmet estimated requests, bikes moved, km and operating hours, estimated redistribution cost, conditional contribution, executable-route share, solve time, solver status and gaps. Normalize across city sizes and report failures. Neither stockouts nor observed trips alone measure attempted demand, and allocated fares do not establish actual profit.

## Report writing and completion gates

Yes, start formal writing now. A finished data handoff is a foundation for the paper; it does not require waiting for every experiment. Keep factual completed work separate from the methodology proposed and results still pending. There is no basis to promise that no further correction will ever be needed, but the main observed-data package can serve as the reference release.

| Paper section | Owner | Write now or finalize later |
| --- | --- | --- |
| 1 Introduction | Jason | Write the problem, motivation and observed evidence now. |
| 2 Literature | Jason | Write now; connect references to the actual model. |
| 3 Data and demand | Carlo + Fu Yan | Data/scope/QA now; complete demand method and validation after fitting. |
| 4 Formulation | Joo Hee | Draft now; finalize after inventory, timing, boundary and vehicle rules agree. |
| 5 Solution method | Joo Hee + Hong Jin | Outline now; report the solver, size, runtime and gaps actually used. |
| 6 Results | Hong Jin | Finalize only from reproducible baseline and optimization runs. |
| 7 Robustness and limits | Joo Hee + Hong Jin + Fu Yan | Write the protocol/known limits now; add measured robustness outcomes later. |
| 8 Conclusion | Carlo + Hong Jin | Finalize recommendations after results and sensitivity are available. |
| Appendix and edit | All code owners; Carlo edits | Maintain data/model code, input register, citations and consistent notation. |

### Decisions needed before empirical claims

Fu Yan must validate the demand estimator and zero-exposure fallback. Jason/Joo Hee must agree the trip-value interpretation and numerical vehicle/cost scenarios. Joo Hee/Hong Jin must agree within-hour order, lead times, effective capacity, external-flow failures, depot/starting load, activation periods and terminal conditions. Case gasoline values are unselected; historical tariff/allocation tables remain benchmarks requiring date and geography review.

The provided 10-13-page team outline fits the guideline's indicative 8-14 narrative pages; depth and clarity matter more than length. This brief is a coordination report, not the finished term paper. Shared Google Docs remain untouched; Carlo will relay the material manually.

### Evidence and reproducibility

Course basis: project guideline pp. 1-4; Lecture 4 pp. 24-26 (sensitivity); Lecture 6 pp. 44-45 and 58 (time-expanded repositioning and scenario evaluation); Lecture 7 fixed-charge and routing constraints. Page references are PDF positions.

[Optimization benchmarking guidance](https://arxiv.org/html/2007.03488v2)

[Good Laboratory Practice for Optimization Research](https://www.graham-kendall.com/papers/ketal2016.pdf)

[Chronological forecasting evaluation](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation)

[GitHub data and scripts](https://github.com/carloida/DBA5103_finalproject)
