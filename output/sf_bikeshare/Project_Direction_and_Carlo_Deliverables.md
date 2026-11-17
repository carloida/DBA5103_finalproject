# Project direction and Carlo's handoff

Prepared 17 November 2026. This brief reconciles the supplied updated allocation, the 16 November minutes, the existing local SF EDA, the course guideline, lectures and reference books. Recommendations below are proposals for the team, not decisions recorded in the minutes.

## 1. Recommended objective and scope

Use San Francisco as a pilot and ask: **When does moving bikes generate enough additional trip contribution to cover its operational cost?** Compare optimized transfers, a simple rule and no transfers under the same starting inventory, demand scenarios, timing and resource limits.

For policy p versus no-rebalancing policy 0:

`Incremental operating contribution = sum[r_k * (served_trips_p,k - served_trips_0,k)] - (rebalancing_cost_p - rebalancing_cost_0)`

Here r_k is the assumed incremental contribution of an additional served trip in rider class k, after any trip-related variable expenses included in the analysis. If those expenses are excluded, label the quantity incremental fare revenue minus rebalancing cost instead. Neither quantity establishes total system profit. Exclude bicycle/dock capex as agreed. Annual membership fees cannot simply be allocated as marginal cash receipts for each extra subscriber ride; any retention/service value needs a separate assumption.

If contribution estimates remain weak, make **minimizing unmet pickup requests subject to a rebalancing budget** the main operational result and show financial outcomes as scenarios. Return failures can be a second service measure, with care not to count the same failed journey twice.

Recommended core: an hourly inventory/transfer model with capacity limits and explicit transfer lead times. Add integer truck activation if required by the cost model. A detailed multi-stop route can be a small extension after the inventory model works. A global limit on bikes moved per hour is a throughput approximation, not proof that a truck route is physically feasible.

The historical status file reflects operations already taking place. Its observed inventory is not the inventory path of a no-rebalancing baseline. Initialize a common state, then simulate each policy using the same request scenarios; do not reset inventories from historical snapshots every hour.

## 2. Can we use a smaller subset?

**Yes. Use complete station histories over contiguous calendar windows, and retain every minute within the selected interval when estimating exposure.** A random sample of status rows or the first N rows can distort stockout durations, coverage and weekday/peak patterns. Longer history is useful only if it improves demand estimation, weather coverage or stability. It does not automatically improve the final decision.

The existing database already contains the full audit and an hourly panel, so there is no need to reread the approximately 2 GB source CSV for routine modeling. Query the cached panel; requery selected raw intervals only for finer time bins, opening snapshots or additional status diagnostics.

I ran a new exploratory assessment with the 34 SF stations installed by 29 August 2013. For each of three validation starts (2 February, 2 March and 6 April 2015), I used the preceding 1, 2, 4 or 8 complete weeks to predict the next 14 days. Forecasts are mean **completed** departures/arrivals by station, weekday/weekend and hour; weather is not fitted. Every window is evaluated on the same subsequent days within its comparison.

| Training history | Station-hour rows per window | Mean departure MAE | Mean arrival MAE | Mean peak departure MAE |
| --- | ---: | ---: | ---: | ---: |
| 1 week | 5,712 | 0.7048 | 0.6847 | 1.2689 |
| 2 weeks | 11,424 | 0.6864 | 0.6686 | 1.2293 |
| 4 weeks | 22,848 | 0.6727 | 0.6598 | 1.2024 |
| 8 weeks | 45,696 | 0.6754 | 0.6666 | 1.2347 |

MAE units: completed trips per station-hour; peak hours are 07:00-09:59 and 16:00-18:59. These are equally weighted means over three validation windows. The roughly 0.4% difference in overall departure MAE between four and eight weeks is small and has no uncertainty interval. Eight weeks improves that metric in two of the three individual comparisons, while the December/holiday history hurts the first comparison. These results favor **four weeks as a provisional simple forecasting base and eight weeks as a sensitivity case**. They do not prove equivalent latent-demand estimates or optimization outcomes.

An observed-data candidate is exported at [subset_assessment/candidate_observed_station_hours.parquet](subset_assessment/candidate_observed_station_hours.parquet): **57,120 rows, about 0.25 MB**, including eight weeks of training (9 February-5 April 2015) and two weeks of exploratory validation (6-19 April). The four-week base is the training portion from 9 March onward. Filter by the supplied split; fitting on the validation rows would leak information.

The eight-week candidate training period has **five measurable-rain days**, versus four in its last four weeks. That is limited support for station-specific rain profiles. Use more historical rain days for a pooled rain scenario, or label rain multipliers as assumptions. A period from 20 April-3 May is suggested for subsequent policy evaluation; this script does not read it, but earlier full EDA may already have examined those dates, so it is not a globally sealed holdout.

The panel retains pickups and returns involving stations outside the cohort. Model these boundary flows explicitly, or expand the station set; keeping only trips with both endpoints inside changes the question. A smaller 10-15 station route example is acceptable if chosen on training-period geography, activity, coverage and complementary flows, with its boundary assumptions disclosed. All 34 stations are already small enough for the core hourly model.

## 3. Sensitivity and validation work

Subset validation and model sensitivity answer different questions. Use both.

| Question | Proposed comparisons | Owner / reported evidence |
| --- | --- | --- |
| Is a short history adequate? | 1, 2, 4, 8 weeks on common later days | Carlo: existing new MAE table; add priority-rank stability and demand-estimate uncertainty with Fu Yan |
| Does aggregation conceal stockouts? | 60-minute base versus 30-minute slots | Carlo: reaggregate bounded raw intervals for the selected dates; compare exposure, peak flows and row counts |
| Do cleaning choices drive the finding? | Daily coverage screens 75%, 90%, 95%; gap limits 60, 90, 120 seconds | Carlo: report retained time, exposure and affected stations; existing full-data sensitivity tables provide a starting point |
| Is corrected demand plausible? | Observed-count lower bound versus pooled exposure-adjusted estimates; alternative censoring/substitution assumptions | Fu Yan with Carlo: errors under artificial censoring, uncertainty and zero-exposure flags |
| When does rebalancing pay? | Low/base/high sourced contribution and cost; sweep cost until best policy has no positive gain over no moves | Hong Jin with Jason/Carlo: incremental contribution, served requests and movements |
| What resources matter? | Truck capacity 20/30/40 as explicitly assumed scenarios; budgets 0.5/1/1.5 times base; loading/travel time low/base/high | Hong Jin/Joohee: service-cost curves, feasible operations and solve times |
| Does the conclusion transfer? | Weekday/weekend, dry/rain, demand 0.8/1/1.2 times base; paired whole-day or week resampling | Team: policy gains on common scenarios, uncertainty and failures |

The proposed numerical scenario levels are experimental choices, not verified SF operating parameters. Change one factor at a time initially, then test a small adverse combination. Select the plan using training information and evaluate the same fixed plan on later scenarios; reoptimizing after seeing every scenario gives a perfect-information benchmark unless the model explicitly permits that recourse.

For mixed-integer models, re-solve each scenario. LP shadow prices and allowable ranges describe the continuous model locally; they do not directly value an additional truck in the integer model. If reporting LP-relaxation duals, label them and confirm integer resource effects with discrete scenario solves.

## 4. Your deliverables

| Deliverable | Current status and remaining action | Recipient |
| --- | --- | --- |
| 1. Scope and subset note | New assessment supplied; team still needs to freeze region, stations, dates, 30/60-minute slots and evaluation split | Everyone, before coding |
| 2. Reproducible EDA | Existing executed notebook, Python script, charts and report available; select only figures that motivate redistribution | Report/team |
| 3. Data quality and cleaning record | Existing key, coverage, capacity and gap audits available; repeat checks for the chosen subset and explain exclusions | Fu Yan/Joohee |
| 4. Compact observed station-slot panel | Candidate Parquet supplied; contains observed counts/exposure/weather, not estimated true demand | Fu Yan |
| 5. Model input handoff | Still needed after scope freeze: reviewed capacities, valid opening inventories with snapshot age, OD flows/travel lags, boundary flows and units | Joohee/Hong Jin |
| 6. Subset and cleaning sensitivity summary | History-window forecast comparison supplied; priority stability, 30-minute comparison and selected-subset cleaning sensitivity remain | Fu Yan/report |
| 7. Cost assumption register | Coordinate Carlo's earlier cost-research action with Jason's newer parameter role; record sources, dates, units, ranges and assumptions | Jason/Joohee/Hong Jin |
| 8. Data section and appendix | Adapt the full EDA into a concise data/scope/limitations section; include code and dictionary in appendix | Shared report |
| 9. GitHub handoff | Publish the agreed SF code, small derived files, manifest and run instructions; raw CSV/database stay outside ordinary Git. No upload performed here | Team |
| 10. Final consistency edit | Check data/model agreement, scenario labels, results, citations, notation and appendix; conclusion/recommendations jointly with Hong Jin | Final report |

Under the newer allocation, Fu Yan owns demand estimation, Joohee owns the formulation, Hong Jin owns optimization/results and Jason leads costs/literature. Carlo supplies their inputs and coordinates the final data story; taking over every workstream is unnecessary. The minutes' 17 November data target and 18 November demand/model target make the data handoff the immediate priority. Keep the 21 November consolidation target because the supplied brief says submission is 22 November and Carlo travels that evening.

Suggested input tables after scope agreement:

- `station`: station_id, name, coordinates, reviewed_capacity, capacity_basis.
- `station_slot_observed`: station_id, slot_start, slot_minutes, observed_pickups, observed_returns, observed_seconds, empty_seconds, full_seconds, coverage, calendar/weather flags, quality flags, split.
- `opening_inventory`: scenario/date, station_id, bikes, docks_available, source_snapshot_time, snapshot_age, validity_flag. Hourly mean inventory is not a substitute.
- `customer_od`: origin, destination, departure_slot, travel_lag, observed_count, boundary_flag. Preserve trips entering before the horizon and arriving within it where relevant.
- Fu Yan's later `demand`: station_id, slot, day_type, scenario, pickup_demand, return_demand, exposure, estimation_method, uncertainty/quality flag. Do not relabel the observed panel as this table.
- `cost_parameters`: parameter, value, unit, low/base/high, price_year, currency, source_url, assumption_flag, marginal_or_fixed.

## 5. Corrections needed before using the meeting's suggested formulas

**Demand:** An available-time estimator is a reasonable transparent starting assumption, but numerator and exposure must cover the same valid intervals. Pool comparable station/hour/day-type observations before dividing. For a fully observed slot, a rate estimated during nonempty time can be projected to the slot duration. With missing status, distinguish extrapolation over observed empty time from extrapolation over unobserved time. Zero exposure is unidentifiable from that slot, not zero demand; use a documented pooled fallback or flag it. Tiny denominators need pooling/regularization and sensitivity checks. Artificially censor known available periods to check recovery. Constant arrival intensity during available and empty periods and no station substitution are assumptions.

**Bike conservation:** If additional pickups are served, their bikes must later arrive somewhere or remain in transit. Replaying fixed historical return totals while changing served rentals can create or destroy bikes in a closed system. Link accepted OD trips and travel lags, including horizon boundary inventory, or explicitly use an open-system approximation. End-of-hour inventory bounds alone can hide temporary stockouts within the hour; document event order or use finer simulation.

**Cost:** Fu Yan's cost structure is useful, but its dollar inputs remain unverified in the supplied brief. Historical 2013-2015 trips combined with 2026 prices define a hypothetical scenario unless prices are harmonized. For a multi-stop tour use, for example:

`route_cost = fixed_dispatch + (driver_hourly + truck_hourly) * (drive_hours + stop_hours + handling_hours) + mileage_cost * route_miles`.

Define whether handling time means both loading and unloading. Count its driver wages once. If the truck incurs an hourly opportunity/rental cost during handling, include that time too. If handling is already in total tour time, do not add its labor again per bike. Charge dispatch only when dispatched, and avoid adding depot-return costs independently for every station pair in a multi-stop tour. `ceil(total_moved / truck_capacity)` is not a general tour-count formula: a truck can unload and reload along one tour. Enforce its onboard load after each visit.

**Routing:** A plain TSP chooses visit order. Rebalancing also needs amounts picked up/delivered, station bounds, onboard capacity, timing and depot rules. These make it a capacitated pickup/delivery rebalancing problem. Keep a route example as an extension if those data and constraints are available, rather than claiming that a TSP alone solves redistribution. The published [single-vehicle static rebalancing formulation](https://www.sciencedirect.com/science/article/pii/S0377221715002659) explicitly combines station sequence with quantities collected/delivered.

## 6. Where this comes from in your materials

Page references below are PDF page positions unless a printed page is explicitly specified. These are selective relevant readings, not claims that the entire books were reviewed in depth.

| Local material | Relevant part | Application |
| --- | --- | --- |
| Project guideline (local course PDF; not redistributed) | pp. 1-2 and 3-4 | Practical assumptions, robustness, model/method, interpretation and appendix code. 8-14 narrative pages is guidance; there is no strict page limit. |
| Lecture 6 (local course PDF; not redistributed) | pp. 17-23; 44-45; 58 | Flow conservation and capacities; container repositioning across time is the closest teaching analogy; repeated scenario evaluation. |
| Lecture 4 (local course PDF; not redistributed) | pp. 24-41 | What-if effects on optimal value and local LP sensitivity. |
| Lecture 7 (local course PDF; not redistributed) | pp. 16-20; 22-50; 63-79 | Linking binary activation and flows, TSP/precedence, LP relaxation and branch-and-bound. |
| Bradley, Hax and Magnanti (local course PDF; not redistributed) | Chapters 3, 8 and 9; PDF pp. 76, 227, 272 start these chapters | Sensitivity, network models, integer decisions. |
| Bertsimas and Tsitsiklis (local course PDF; not redistributed) | Chapter 5, especially 5.1; PDF p. 219 / printed p. 202 | Dependence on costs/resources and the limits of local LP sensitivity. This supplied excerpt contains only the first five chapters; its contents list later chapters that are not available in full. |
| Hillier and Lieberman (local course PDF; not redistributed) | Sections 6.6-6.7, 9.6, 12.3; fixed charge at PDF p. 614 / printed p. 589 | Sensitivity, minimum-cost flow and a fixed dispatch cost linked to a binary decision. |

External methodological support: [Liu and Pelechrinis (2021), Excess demand prediction for bike sharing systems](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0252894). It explains why observed trips omit excess demand and develops an availability-based method. It does not validate the meeting's simple exposure-ratio estimator, and that published method has not been implemented here.

## 7. Reproduce and interpret the new outputs

Script: [assess_subset_windows.py](../../sf_bikeshare/assess_subset_windows.py). Outputs: [individual windows](subset_assessment/window_comparison.csv), [mean validation metrics](subset_assessment/mean_validation_metrics.csv), [station list](subset_assessment/candidate_stations.csv), [manifest](subset_assessment/assessment_manifest.json).

The script opens the existing DuckDB database read-only, checks station-hour uniqueness, complete calendar grids and forecast coverage, and writes only new subset-assessment files. It does not reestimate demand, fit an optimizer, compute profit, change the existing inferential PDF or upload to GitHub. The project's existing virtual environment currently points to a missing Python installation; this assessment was executed using the bundled Python 3.12 runtime with the project's installed DuckDB package. Recreate the virtual environment from the existing requirements for normal team reproduction.
