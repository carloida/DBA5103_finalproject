> Supporting technical notes only. The shorter [Section 3 draft](../SF_Bikeshare_Consolidated_Data_Preparation_Report.md) is Carlo's paper contribution. These notes retain broader team context and are outside its shared two-page allowance.

# SF Bay Area Bike Share: data preparation, feature engineering and model-input report

**Prepared by Carlo | Updated 19 November 2026 | Consolidated report for team review**

This report supersedes the current-status statements in the 17 November initial report and consolidates the 18 November V3 changelog, the separate robustness packages and Jason's updated inputs. The earlier reports remain a preparation history. This is the observed-data handoff and proposed modeling plan, not a completed optimization study.

## 1. Objective and current position

The project investigates where, when and how many bikes to redistribute to improve service and modeled economic contribution, subject to bike conservation, station inventory, docking, transfer-time and truck-resource limits. Performance will be compared with no redistribution and a simple rule under common conditions. Bicycle and dock purchases are outside the operational scope.

Joohee has approved the main scope: **34 San Francisco stations, 9 February-19 April 2015 inclusive, hourly resolution**. Main V3 contains **57,120 station-hours and 51 hourly columns**, with related inputs organized into **21 core database tables**. Five additional cases have been prepared separately for **robustness testing and evaluation only**. Their observed-data preparation is complete; demand estimation, final operating parameters, formulation, executable routes and policy results remain pending.

Jason's baseline values of USD 0.88 per Subscriber trip and USD 4.50 per Customer trip can be evaluated as allocated-revenue scenarios. They are not observed per-trip payments or established incremental cash receipts. Accordingly, the economic objective is described as **net modeled contribution under stated value assumptions**, rather than verified accounting profit.

The original source database and V2 file are preserved. Scoped V3 and robustness exports are already published on [GitHub](https://github.com/carloida/DBA5103_finalproject). No Google Doc has been edited; Carlo will relay this report manually. This update changes the documentation, not the frozen data exports or their parameter values.

## 2. Sources, scope and dataset progression

The supplied files associated with [Ben Hamner's SF Bay Area Bike Share dataset](https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share) contain trips, stations, historical bike/dock status and weather. Trip starts cover 29 August 2013-31 August 2015. The full audited source contains 669,959 completed trips, 70 stations across five cities, 71,984,434 status snapshots and 3,665 weather location-days.

The source lists 35 SF stations. The main pilot retains the 34 installed by 29 August 2013, giving a fixed station cohort throughout the selected dates. The period is represented as `[2015-02-09, 2015-04-20)`, so the whole of 19 April is included. The recorded local-clock grid has 34 x 70 x 24 = 57,120 rows; it does not resolve daylight-saving timestamp ambiguity.

| Iteration | Scope and change | Status and purpose |
| --- | --- | --- |
| V1: full source and audited database | All five cities; typed and linked trip, station, status and weather records | Preserved locally; source audit and broader descriptive context |
| V2: observed SF pilot | 34 stations, ten weeks, 21 columns; hourly flows, availability and weather; eight training weeks and two exploratory validation weeks | Original Parquet preserved; 57,120 rows |
| V3: enriched main inputs | Same cohort/dates; 51 hourly columns plus station, opening-stock, OD, boundary, transit, distance and parameter tables | Published; 21 core tables, 43 build checks and 18 export row-count readbacks passed |
| V3 robustness branch | Five separate ten-week cases using the same hourly features and core table schemas | Published separately; 194,880 additional station-hours; experiments pending |
| V4: demand and agreed parameters | Training-derived attempted-demand estimates/scenarios and agreed financial/vehicle/operating values | Planned; Fu Yan, Jason, Joohee and team decisions |
| V5: policy and route results | Baselines, optimized moves, executable-route checks and sensitivity results | Planned; these will be model outputs, not new historical observations |

These are analytical iteration labels, not Git tags. The robustness branch does not replace the main case or constitute completed V4/V5 work.

The main pilot represents 4.72% of the full 1,209,456-row hourly panel. Its 63,974 distinct endpoint-relevant journeys represent 9.55% of the full trip count: a journey qualifies when at least one selected-station endpoint occurs within the window. Pickups and returns must not be added to count unique journeys. V3 also retains one flagged December-to-June horizon-spanning journey for transit review, giving 63,975 local journey records without changing the hourly endpoint totals.

The 247,473-byte V2 Parquet is about 0.247 MB versus 2,070.35 MB for the four raw CSVs. Its approximately 99.988% storage reduction combines narrower scope, hourly aggregation, omitted individual-record detail and compression. This comparison describes the original V2 panel, not the storage size of the complete V3 package or the proportion of source observations used.

## 3. Ingestion and feature engineering

### 3.1 Common processing rules

Station IDs and timestamps link the source tables. Pickups use trip start times and returns use trip end times. A dense station-hour grid retains hours with zero recorded trip events. No recorded event means a zero completed-trip count; missing availability is not converted to zero bikes, zero demand or zero exposure fractions.

Source timestamps are analyzed as recorded local clock time, without conversion to Singapore time. DST flags preserve known ambiguity; they do not constitute a timezone repair. Weather is joined by a documented city-to-weather-ZIP mapping and date, not by rider ZIP code. It is a city-level proxy rather than a station weather measurement.

For status exposure, a state is valid when bikes and free docks are nonnegative, nonmissing and have a positive combined total. The both-zero state is excluded from valid exposure. A preceding state is carried only to the next observation when the gap is positive and at most 90 seconds. Eligible intervals are split at hour boundaries. Longer gaps remain unknown; capacity discrepancies are flagged rather than automatically removed.

### 3.2 What the 51 hourly columns contain

Not all 51 columns are new features or external inputs. Many are inherited observations/aggregations; V3 adds diagnostics and class-specific transformations and replaces three original weather-unit columns with metric equivalents. The change from 21 to 51 is a **net increase of 30 columns**. Opening stocks, road matrices and parameter registers are separate tables, not 51 additional hourly fields.

| Feature family | Columns | Engineering and interpretation |
| --- | ---: | --- |
| Station/time/split identifiers | 9 | Station, city, local hour, date, hour-of-day, ISO weekday, day type, training/validation split and DST-date flag |
| Total completed flows and net flow | 3 | Departures, arrivals and departures minus arrivals; net flow indicates pressure, not the required truck movement |
| Rider-specific event counts | 14 | Subscriber and Customer pickups/returns, each counted over all events, valid exposure and matching available exposure; two unknown-rider event counts |
| Internal/boundary endpoint counts | 4 | Internal pickups/returns and pickups/returns involving a station outside the selected cohort |
| Availability exposure and ratios | 10 | Valid, empty, full, low-bike and low-dock seconds; coverage; bike/dock available seconds; empty/full exposure fractions |
| Time-weighted availability means | 2 | Mean bikes and mean effective bikes-plus-free-docks over valid observed intervals |
| Quality diagnostics | 4 | Capacity-mismatch seconds, snapshot-tied event count, missing-exposure flag and capacity-mismatch flag |
| Weather/proxy fields | 5 | Weather ZIP, trace-precipitation flag, temperature in Celsius, wind in km/h and precipitation in mm |
| **Total** | **51** | Exact field names and SQL types appear in the [V3 data dictionary](https://github.com/carloida/DBA5103_finalproject/blob/main/output/sf_bikeshare/model_inputs_v3/data_dictionary.csv) |

For each hour, let `O` be valid observed seconds, `E` empty seconds, `U` full seconds, `P` completed pickups and `R` completed returns. The implemented transformations are:

```text
net_outflow = P - R
status_coverage_fraction = O / 3600
bike_available_seconds = O - E
dock_available_seconds = O - U
empty_exposure_fraction = E / O, when O > 0
full_exposure_fraction = U / O, when O > 0
```

Ratios with no valid denominator remain NULL. Low-bike and low-dock seconds use thresholds of at most two bikes or free docks, respectively; these include empty/full time and must not be added to it as disjoint categories. An overall empty/full percentage is `sum(E or U) / sum(O)`, rather than an unweighted average of hourly percentages.

For valid interval pieces `k`, with duration `w_k` seconds, bike count `b_k` and free-dock count `f_k`:

```text
mean_bikes_available = sum(w_k * b_k) / sum(w_k)
mean_effective_capacity = sum[w_k * (b_k + f_k)] / sum(w_k)
```

These are time-weighted means, not opening inventories. A status total is an effective-availability diagnostic and does not establish that physical dock capacity changed.

### 3.3 Rider splits and matched exposure

Subscriber/Customer flows are transformations of existing rider labels, not externally obtained demand. For each class, V3 distinguishes all recorded endpoint events from events falling within eligible status intervals. Pickup-available counts additionally require a bike to be available; return-available counts require a free dock. Snapshot-time ties are flagged because minute-rounded timestamps do not establish event ordering.

The main cohort has **55,179 Subscriber and 7,064 Customer pickups**, and **55,234 Subscriber and 7,092 Customer returns**. These count completed events, not all attempted requests. There are 1,647 external-cohort pickups and 1,729 external-cohort returns. Such boundary flows are included in the totals, not additional events to add again.

### 3.4 Separate inventory, capacity, OD and distance inputs

| Input | Engineering completed | Modeling interpretation |
| --- | --- | --- |
| Opening inventory | Latest snapshot at or before each hour/midnight; valid only when the latest state is valid and at most 90 seconds old; source time and age retained | No future lookup, fallback imputation or substitution of hourly means; hourly opening diagnostics do not authorize hourly historical stock resets |
| Dock capacity | Listed dock count retained; modal/minimum/maximum status totals and discrepancies audited | Joohee/Carlo still choose the physical/effective capacity rule; no invented capacity overrides |
| OD and boundary flows | Journeys grouped by origin, destination, rider class, departure/arrival hour and temporal flags | Preserves timing and outside-cohort movements; aggregate boundary counts reconcile with hourly events |
| In-transit and exact-boundary records | Trips strictly spanning day boundaries separated from events exactly at a boundary | Supports initialization and agreed event order; accepted internal rentals must generate their later returns |
| Great-circle distance | Haversine calculation from original station coordinates using Earth radius 6,371.0088 km | Derived straight-line geographic distance, not a truck route |
| Directed road distance/time | Current OSRM driving matrix, with coordinate order, access time and snapping diagnostics | SF: 34 x 34 = 1,156 pairs; San Jose: 16 x 16 = 256 pairs, including same-station pairs |

OSRM provides distances along its fastest modeled routes, not necessarily shortest-distance routes. Working fields convert metres to km and seconds to minutes. These are current default-driving proxies, not observed 2014/2015 congestion, certified truck access, depot legs or executable multi-stop routes. [OSRM Table service documentation](https://project-osrm.org/docs/v5.24.0/api/#table-service).

### 3.5 External evidence, team assumptions and units

Coordinates, dock counts, rider labels, trips, status and weather originate in the supplied source. New external integration comprises current OSRM estimates and historical tariff evidence. Previously sourced EIA California gasoline benchmarks were carried into main V3. Assumed trips per pass are Jason's team scenarios, not externally measured rider behavior. Historical billing transactions and truck operating logs remain unavailable.

All V3 and robustness working physical units are metric; currency is USD. The exact conversions are:

```text
temperature_C = (temperature_F - 32) * 5 / 9
wind_km_per_hour = wind_miles_per_hour * 1.609344
precipitation_mm = precipitation_inches * 25.4
road_distance_km = road_distance_metres / 1000
driving_minutes = driving_seconds / 60
fuel_price_USD_per_litre = fuel_price_USD_per_US_gallon / 3.785411784
```

Missing weather values remain missing and the trace-precipitation flag is retained. Original source units remain in provenance notes and V1/V2; they are not the working model units. No normalization or standardization has been applied.

## 4. Validation and existing descriptive findings

Main V3 passed **43 build/reconciliation checks and 18 exported-table row-count readbacks**. The five robustness cases passed **65 checks and 18 readbacks each**, totaling **325 checks and 90 readbacks** for the additions. Portable validation also verified export hashes, schemas, splits, row counts, rider totals and missing-stock handling. These establish consistency of prepared inputs, not accuracy of attempted-demand estimates or optimization results.

Material main-case findings are:

- All 2,380 midnight opening stocks are fresh within 90 seconds. There are 67 midnight effective/static-capacity mismatches. All 34 stations have some status-capacity discrepancy; their modal and maximum valid totals equal listed docks.
- The 34 stale hourly openings occur at 03:00 on 8 March 2015 around DST. They remain NULL/flagged. The nominal recorded-hour grid should not be interpreted as a repaired elapsed-time timeline.
- Thirteen of the 63,974 endpoint-relevant journeys exceed 24 hours. Including the supplemental horizon-spanning record gives 14 long journeys in V3. These are flags, not confirmed continuous bike use or chargeable bills.
- The main training split is 9 February-5 April: 45,696 rows. The exploratory validation split is 6-19 April: 11,424 rows. These dates have already been examined and are not a sealed final holdout.

Earlier descriptive checks compared the same 34 stations with the other 94 complete weeks in a 104-week calendar. Their findings remain relevant because V3 preserved the V2 flow/exposure totals:

| Measure | Other 94 weeks | Main ten weeks |
| --- | ---: | ---: |
| Average weekday pickups/day | 984.83 | 1,115.58 |
| Average weekend pickups/day | 343.98 | 323.20 |
| Valid observed time empty | 1.1605% | 1.8529% |
| Valid observed time full | 0.7244% | 0.8562% |
| Days flagged by the daily IQR screen | 46 of 658 | 1 of 70 |

Weekday peaks occur around 08:00 and 17:00, and correlation of the two normalized 24-hour weekday profiles is 0.9965. Only six stations overlap in the top-ten empty/full-pressure lists. Similar hourly shapes therefore do not establish equivalent station priorities or performance across seasons.

The daily screening rule flags values below `Q1 - 1.5*(Q3-Q1)` or above `Q3 + 1.5*(Q3-Q1)`, using separate reference weekday/weekend distributions. All flagged days were retained. It is a descriptive screen, not an error classification or optimization validation.

An earlier completed-trip forecast exercise across three validation starts found mean departure errors of approximately 0.673 and 0.675 trips per station-hour using four and eight training weeks. This does not establish equivalent attempted-demand estimates or policy results. The main eight training weeks have only five measurable-rain days, limiting detailed station-specific rain estimates. [Existing pattern audit](https://github.com/carloida/DBA5103_finalproject/blob/main/output/sf_bikeshare/subset_assessment/Pattern_Check_Findings.md).

## 5. Jason's updated pricing and ridership inputs

### 5.1 Historical evidence and allocation scenarios

Official historical evidence supports annual membership at USD 88 and 24-hour access at USD 9. The SFMTA November 2015 release also lists a USD 22 three-day pass; it is dated **25 November**, not December, and postdates the pilot. The October 2013 SFMTA board supplies the included-duration/surcharge benchmark. Exact unchanged fee applicability and complete billing terms for every study window still require review. [SFMTA 2015 release](https://www.sfmta.com/press-releases/2015-holiday-shopping-season-ready-be-unwrapped), [SFMTA 2013 board, PDF page 4](https://www.sfmta.com/sites/default/files/projects/10.16.2013%20Bike%20Share%20Open%20House%20Boards.pdf).

Jason's six scenarios are already in V3 and retained as reference scenarios in the robustness packages:

| Source rider label | Low allocation, USD/trip | Base | High |
| --- | ---: | ---: | ---: |
| Subscriber | 88/150 = 0.5866667 | 88/100 = 0.88 | 88/50 = 1.76 |
| Customer | 9/4 = 2.25 | 9/2 = 4.50 | 9/1 = 9.00 |

Calculations retain full precision; rounding is for display. The rule is `allocated value per trip = assumed pass price / assumed trips per pass`. The annual and daily allocation periods differ. Rider labels do not identify actual annual/trial membership or daily/three-day purchases, and pass transactions, discounts and refunds are absent. These are assumed allocations, not measured willingness to pay, societal value, marginal revenue or actual operating contribution after all variable costs.

### 5.2 Corrected arithmetic and unresolved dashboard scope

Jason reports 56,803 member trips and 6,948 casual trips from the [SFMTA dashboard](https://transtat-public.sfmta.com/t/public/views/BayAreaBikeShare/Overview?%3Aembed=y). The interactive filters could not be independently verified in this review. His reported total is 63,751, with mean duration 12 minutes 20 seconds and median eight minutes. These remain **externally reported, scope-unreconciled statistics**, not V3 cohort summaries.

The corrected allocation arithmetic for his reported population is:

```text
member allocation = 56,803 * 0.88 = USD 49,986.64
casual allocation = 6,948 * 4.50 = USD 31,266.00
total allocation = USD 81,252.64
weighted allocation = 81,252.64 / 63,751 = USD 1.2745312 per trip
```

The proposed denominator of 53,751 and total of USD 81,253.64 are errors. Approximately USD 1.27/trip is correct only with the corrected total and denominator.

| Population/measure | Subscriber/member | Customer/casual | Total |
| --- | ---: | ---: | ---: |
| Jason's reported dashboard trips | 56,803 | 6,948 | 63,751 |
| V3 pickups at the selected 34 stations in the window | 55,179 | 7,064 | 62,243 |
| V3 returns at the selected 34 stations in the window | 55,234 | 7,092 | 62,326 |
| V3 distinct endpoint-relevant journeys | 56,807 | 7,167 | 63,974 |

These are different selection/counting definitions. Inbound trips, events crossing dates and the excluded SF station matter, but the exact dashboard discrepancy has not been explained. Jason should record station, date, duration and trip-selection filters. Use reproducible V3 cohort counts for the model; do not change local observations to match the dashboard or replace rider-specific coefficients with its weighted average.

For illustration, applying the base coefficients to V3's 62,243 selected-origin pickups gives `55,179*0.88 + 7,064*4.50 = USD 80,345.52`. This is a retrospective allocation across recorded pickups, not extra revenue, policy benefit or an optimization result.

### 5.3 Optional duration-fee scenario

Individual durations are required to study surcharges; an overall mean below 30 minutes does not imply zero fees. A candidate schedule, conditional on confirming the tariff and interpreting begun extra blocks as chargeable, is:

```text
u(d) = 0                                      for 0 < d <= 1,800 seconds
u(d) = 4                                      for 1,800 < d <= 3,600
u(d) = 4 + 7*ceil[(d - 3,600)/1,800]           for d > 3,600
```

Invalid/missing durations are unavailable, not zero-fee observations. Exact threshold conventions, caps, lost-bike rules, discounts and applicability remain unverified, so this is a **billing scenario**, not an implemented reconstruction of receipts. Long/flagged trips must not be extrapolated into unlimited charges without an explicit rule. In the main selected-origin records, 388 Subscriber and 2,248 Customer trips exceed 30 minutes; thirteen exceed 24 hours.

If approved, compute `mean fee_r = sum eligible training u(d) / number of eligible training trips of class r` and test `scenario value_r = allocated pass value_r + mean fee_r`. Report exclusions and denominators, use training observations only, and test handling of flagged trips. The duration mix of observed served trips need not match previously unserved requests. No usage-fee values have been added to the frozen exports by this report. The recommended initial base case retains 0.88/4.50 without surcharges.

## 6. Demand, objective and two-stage cost formulation

### 6.1 Attempted demand is a separate estimation step

Completed trips measure served requests. Empty/full exposure identifies constrained time, not the number of unsuccessful users. Fu Yan's proposed exposure-based approach remains part of the pipeline; Jason's simpler completed-trip proxy is an alternative assumption requiring an explicit team decision, not a completed change to the estimator. [Liu and Pelechrinis (2021)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0252894) supports the observed-versus-excess-demand distinction, not validation of our particular estimator.

For station `i`, rider class `r` and a pooled comparable training group `g`, a candidate pickup-rate estimator is:

```text
lambda_pickup(i,r,g) = 3600 * sum(matched available-exposure pickups)
                            / sum(bike_available_seconds)
```

The result is requests/hour under stated arrival-rate and availability assumptions. A modeled interval of `Delta` hours has expected requests `lambda_pickup * Delta`. Use pooled counts divided by pooled exposure, not an average of unstable hourly ratios. Pickup numerators must match bike-available denominators; descriptive return rates use matched return counts and dock-available seconds. Missing/tiny/zero exposure requires a validated pooled fallback and separate missingness treatment. Nothing here establishes observed lost demand.

Accepted internal rentals must generate their later destination returns and in-transit inventory. Independently imposing historical internal returns after rejecting different pickups would create inconsistent bike balances. External inflows/outflows need explicit shortage/overflow and valuation rules. Actual daily weather or realized requests from evaluation dates are not operationally available forecasts unless that information assumption is stated. [Chronological forecasting evaluation](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation).

### 6.2 Objective and trip counting

Let `Q_r(pi)` be served rentals of rider class `r` under policy `pi`, counted once at selected origins, `v_r` the stated per-trip scenario value, and `C(pi)` the redistribution cost under a consistent accounting scope. The proposed objective and baseline comparison are:

```text
J(pi) = sum_r[v_r * Q_r(pi)] - C(pi)
Delta J(pi) = sum_r{v_r * [Q_r(pi) - Q_r(no moves)]}
              - [C(pi) - C(no moves)]
```

For the base allocation scenario, `v_Subscriber=0.88` and `v_Customer=4.50` USD/trip. Returns earn no second trip value. Fixed external-origin arrivals supply stock but are not automatically counted as new selected-origin rentals. Model-served rentals are decision/simulation outcomes, not fixed historical counts inserted into the objective. Policy differences may be negative; do not count only improvements while ignoring lost service elsewhere.

The comparator is constant only within the same agreed scenario. No-moves redistribution cost is zero if the scope contains only discretionary redistribution; other common costs cancel. If trip-specific variable costs are modeled, use `v_r = allocated revenue proxy_r - variable trip cost_r` and document the terms. Otherwise describe `J` as allocated trip value less redistribution expense, not fully measured operating margin. Service improvement and movements should be reported alongside this conditional economic measure.

### 6.3 Stage 1: allocation on a time-expanded network

Station-hour nodes and inventory/transfer arcs support an integer allocation model. Joohee will define bike conservation, station bounds, accepted-rental/return timing, transfer lead times, truck activation and resource limits. With nonnegative integer moves `x_ijt`, the proposed cost is:

```text
C1 = sum_p(F_p*z_p)
     + sum_t sum_(i != j) [(h_t + k_t*d_ij/Lbar_t) * x_ijt]
```

Here `h_t` is combined loading/unloading cost in USD per relocated bike, `k_t` is the allocated variable travel cost in USD/truck-km, `d_ij` is directed road km and `Lbar_t > 0` is an assumed average number of bikes carried. Thus `k*d/Lbar` has units USD/bike. The travel coefficient's cost components must be documented so they do not overlap handling or activation.

`F_p` is USD per activation billing period and `z_p` is binary. This notation assumes one available truck; multiple trucks require vehicle indexing or a separately justified fleet-count formulation. A daily fee must not be charged every hour. Moves must be linked to available resources using a justified throughput bound. Average load, onboard truck capacity and bikes moved/hour are different parameters. Interstation flows alone do not certify a feasible truck tour.

The station balance has the schematic form `next stock = current stock - accepted pickups + linked customer returns - relocation departures + relocation arrivals`, with station stock between zero and the agreed dock bound. Relocation arrivals occur after their lead times, not automatically in their departure hour. This aggregate balance is necessary but does not prevent a temporary within-hour stockout or full station; Joohee must specify intermediate event-order/availability constraints. Opening observations initialize the experiment rather than resetting its stock each hour.

### 6.4 Stage 2: routing feasibility and route-cost accounting

For vehicle `v` and billing period `p`, define:

```text
C2 = sum_(v,p) [F_vp*z_vp + W_vp*H_crew_vp + V_vp*H_vehicle_vp
               + P_vp*G_vp + M_vp*D_vp + A_vp]

H_route_vp = driving_hours + stop_setup_hours
             + (t_load*N_loaded + t_unload*N_unloaded)/60
             + route_waiting_hours

H_crew_vp = H_route_vp + other_paid_crew_hours
H_vehicle_vp = H_route_vp + other_billable_vehicle_hours

G_vp = D_vp*q_vp/100
```

`D` is complete tour km, `q` litres/100 km and `G` litres. `P` is USD/litre. `W` is the combined assigned-crew cost in USD per paid crew-clock hour, including the chosen crew composition; `V` is non-overlapping incremental vehicle cost in USD per billable vehicle hour. `M` is any additional, otherwise uncounted USD/km expense. `A` contains direct fees not already counted. Handling times are minutes per loading/unloading operation. Count all actual operations, stops, depot legs and paid time. Inactive vehicles incur no variable tour activity; fixed commitments versus avoidable activation must be distinguished.

When crew and vehicle use the same paid-hour basis `H`, the time term reduces to the earlier `(W+V)*H`. The separate-hour form avoids imposing that equality where billing differs. Handling labor included in crew hours is not added again as a per-bike charge in `C2`. Fuel, labor, hire and mileage components must each appear once. If hire already covers some vehicle expenses, remove those from the other terms.

Existing wages or vehicle commitments that do not change between policies are common costs in the incremental comparison. Any alternative valuation of staff time as an opportunity cost must be stated separately from avoidable cash expense.

Stage 2 uses Stage 1's moves to check visit order, load evolution, pickup/delivery precedence where needed, stock/dock feasibility, timing and depot/end conditions. A TSP order is only a routing component. If movements are infeasible, revise them and recompute service/cost, or report the failure. Compare `C2-C1` only for the same executable operation and accounting scope. **Do not add C1 and C2.** Neither is an observed operator bill, neither is a proven bound on the other, and the sequential procedure does not guarantee a joint global optimum.

Numerical truck capacity, average load, throughput, handling/setup time, wage, vehicle, activation and related values remain to be agreed. Unknown parameter values are not zero. Jason's revenue update does not resolve these operating gaps.

## 7. Robustness datasets and evaluation protocol

The main case and five additions form a two-city by three-period comparison. All cases retain ten weeks, the exact 51-column hourly schema and all 21 core table schemas. SF has 34 stations and San Jose 16; dates were not extended and observations were not duplicated to manufacture equal row counts.

| Case | City | Inclusive dates | Stations | Station-hours | Unusable midnight stock records |
| --- | --- | --- | ---: | ---: | ---: |
| D0: main V3 | SF | 9 Feb-19 Apr 2015 | 34 | 57,120 | 0 |
| R1 | San Jose | 9 Feb-19 Apr 2015 | 16 | 26,880 | 0 |
| R2 | SF | 2 Jun-10 Aug 2014 | 34 | 57,120 | 4 |
| R3 | San Jose | 2 Jun-10 Aug 2014 | 16 | 26,880 | 0 |
| R4 | SF | 20 Apr-28 Jun 2015 | 34 | 57,120 | 4 |
| R5 | San Jose | 20 Apr-28 Jun 2015 | 16 | 26,880 | 0 |

Each added case has eight weeks labeled training and two labeled validation, intended for retrospective policy evaluation after settings are fixed. The suite contains 252,000 station-hours including D0. Shared dates, stations and source history make the cases dependent. Six cases is our project design choice, not a universal minimum or six independently collected systems. Prepared datasets do not establish robust model performance. [Optimization benchmarking guidance](https://arxiv.org/html/2007.03488v2).

Four unusable station-day opening stocks remain NULL/flagged in each additional SF case; one R4 record lies in its evaluation period. Agree a fallback or complete-day exclusion rule before inspecting policy outcomes. The files have not silently applied either. Current SF road estimates were reused, and the San Jose matrix was fetched once and cached. Robustness tariff/allocation tables are historical reference benchmarks. Case gasoline values remain unselected/NULL, with old reference values in notes. Use an explicit common price-year scenario or obtain period-matched costs before economic comparisons; do not treat 2015 figures as observed 2014 costs.

Within each case, compare no moves, a resource-matched simple rule and optimized allocation using the same initial stocks, in-transit bikes, requests, operating limits and information. Fit local inputs using that case's training history under the same estimator recipe. Distinguish this from transfer of a single already-trained SF predictor. Fix policy/estimator choices before policy evaluation; optimizing with realized future requests is a perfect-information benchmark, not normal operational performance.

Independent daily experiments may initialize all policies from the same historical midnight state; label those experiments accordingly. A continuous multi-day counterfactual must carry its own resulting inventory and in-transit stock forward instead of resetting to historical stocks. Final stock and truck end conditions must prevent artificial end-of-horizon benefits.

Six cases with up to fourteen evaluation days each give **84 city-days and 252 policy-day evaluations for three policies**, before exclusions, scenarios and stochastic replications. These counts are an experiment budget, not independent sample sizes or completed runs. Report paired policy differences while preserving day/week dependence; use common demand realizations/seeds where relevant and choose stochastic repetitions from a variability pilot.

Report trips served, estimated unmet requests, bikes moved, km, operating hours, estimated redistribution cost, conditional contribution, route feasibility, solve time/status and optimality gaps. Normalize service and cost comparisons across city sizes. Follow the base comparisons with selected demand, rider-value, handling-cost and truck-resource scenarios. Testing scenarios after solving is robustness/sensitivity evaluation; it does not itself turn the formulation into a robust-optimization model with explicit uncertainty sets.

## 8. Formal EDA, responsibilities and next actions

The full-source EDA and earlier subset diagnostics already exist. The next step is a **focused V3 EDA**, documenting the enriched inputs and checking their implications for the formulation. This report consolidates the handoff; it does not replace EDA or eliminate unresolved modeling choices. Data EDA can proceed before every cost value or demand estimate is finalized.

Carlo's focused EDA should cover:

1. Rider-specific hourly/weekday profiles and station-level pickups, returns and net flow, with training/validation dates marked.
2. Status coverage, empty/full exposure, matching-event coverage, opening inventories, capacity discrepancies and DST/long-trip flags, including affected dates.
3. Boundary-flow shares, OD timing and in-transit inventory; avoid double-counting internal/boundary events or unique journeys.
4. Weather/day-type patterns with sample counts, preserving missing/trace values and noting the small rain sample. Daily weather copied to station-hours is not independent station-hour evidence.
5. Descriptive comparisons across robustness cases using per-station/per-day or exposure-weighted measures; leave claims of policy robustness until the common models are run.

Use evaluation-date exploration transparently; it cannot be presented later as an untouched holdout. Keep descriptive case comparisons separate from tuning policies to favorable outcomes. Review stock/capacity/DST rules with Joohee before empirical policy claims, and record any resulting derived revision without silently overwriting this release.

| Process | Owner | Next output |
| --- | --- | --- |
| Observed-data QA, focused EDA and data section | Carlo, with Joohee on capacity/timing | Reconciled figures, flag-treatment register and EDA findings |
| Attempted-demand estimation | Fu Yan with Carlo | Training-based estimates, pooled fallback, validation and uncertainty |
| Revenue/cost evidence and parameter scenarios | Jason with Joohee | Corrected dashboard arithmetic/scope notes, agreed value interpretation and numerical operating inputs |
| Time-expanded integer formulation | Joohee | Objective, conservation, dock bounds, timing, boundary, activation and terminal rules |
| Optimization, baselines and executable routing | Hong Jin with Joohee | Small-instance checks, common evaluation implementation and reproducible results |
| Robustness and sensitivity evaluation | Joohee, Hong Jin and Fu Yan | Same-method comparisons across prepared cases and selected scenarios |
| Consolidation and final interpretation | Carlo with section owners | Consistent report, limitations and recommendations supported by results |

Formal writing can proceed now for the introduction, literature, observed-data preparation and proposed methodology. Final demand validation, formulation details, results and conclusions must follow their actual completion. There is no current evidence of recovered demand, an optimized executable schedule or a financial improvement.

## 9. GitHub handoff and reference notes

The existing published handoff is recorded at commit **a0fdb1816dc8f1607baed602e6ffe443db47d757**. This consolidated report was prepared locally afterward. GitHub links below point to the published project; the commit provides the inspected release reference.

- [Project repository](https://github.com/carloida/DBA5103_finalproject)
- [Main V3 inputs and loading guide](https://github.com/carloida/DBA5103_finalproject/tree/main/output/sf_bikeshare/model_inputs_v3)
- [Separate robustness packages and instructions](https://github.com/carloida/DBA5103_finalproject/tree/main/output/sf_bikeshare/robustness_testing)
- [Robustness case inventory](https://github.com/carloida/DBA5103_finalproject/blob/main/output/sf_bikeshare/robustness_testing/case_inventory.csv)
- [Dataset-iteration history](https://github.com/carloida/DBA5103_finalproject/blob/main/docs/SF_Bikeshare_Dataset_Iterations.md)
- [V3 transformation code](https://github.com/carloida/DBA5103_finalproject/blob/main/sf_bikeshare/enrich_model_inputs.py) and [robustness builder](https://github.com/carloida/DBA5103_finalproject/blob/main/sf_bikeshare/build_robustness_subsets.py)
- [Portable robustness validator](https://github.com/carloida/DBA5103_finalproject/blob/main/sf_bikeshare/validate_robustness_subsets.py)

The 21 core tables include local-only journey/event/calendar detail; **18 tables are exported as CSV/GZIP per case**. Dictionaries, manifests and validation files accompany them. Full raw sources and DuckDB databases remain local and excluded from GitHub. Reading scoped exports does not require those full databases; rebuilding the complete transformation requires the original local source database and documented references/caches.

Additional provenance includes the [April 2015 Air District release](https://www.baaqmd.gov/~/media/files/communications-and-outreach/publications/news-releases/2015/2015-022-babs-500000-041315.pdf), dated 16 April in the previously verified PDF despite its filename, and [EIA's California monthly gasoline series](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=M&n=PET&s=EMM_EPMR_PTE_SCA_DPG). These support historical benchmarks, not actual transactions. Jason's latest pasted inputs and the teammates' supplied comments are team evidence, distinguished from independently reproducible source observations.

Before using Jason's bibliography in the formal paper, correct **Raviv et al. (2013)** rather than Tal et al. ([publisher](https://link.springer.com/article/10.1007/s13676-012-0017-6)); **Zhang et al. (2021)** rather than Jie et al. ([author institution](https://research-information.bris.ac.uk/en/publications/a-data-driven-dynamic-repositioning-model-in-bicycle-sharing-syst/)); and the journal of Zhang et al. (2017) to **Transportation Research Part B: Methodological**, 103, 188-207 ([publisher](https://www.sciencedirect.com/science/article/abs/pii/S0191261516302697)). Their relevance should be explained against the team's eventual formulation rather than treating any cited method as already implemented.

## Appendix: exact hourly feature groups

This inventory documents the existing schema; it does not create new fields.

| Group | Exact column names |
| --- | --- |
| Station/time/split (9) | `station_id`, `city`, `hour_start`, `service_date`, `hour`, `iso_weekday`, `day_type`, `split`, `dst_transition_date_flag` |
| Total flows (3) | `departures`, `arrivals`, `net_outflow` |
| Rider counts (14) | `subscriber_pickups`, `subscriber_pickups_valid_exposure`, `subscriber_pickups_available_exposure`, `subscriber_returns`, `subscriber_returns_valid_exposure`, `subscriber_returns_available_exposure`, `customer_pickups`, `customer_pickups_valid_exposure`, `customer_pickups_available_exposure`, `customer_returns`, `customer_returns_valid_exposure`, `customer_returns_available_exposure`, `unknown_pickups`, `unknown_returns` |
| Boundary counts (4) | `internal_pickups`, `boundary_pickups`, `internal_returns`, `boundary_returns` |
| Exposure (10) | `observed_seconds`, `empty_seconds`, `full_seconds`, `low_bike_seconds`, `low_dock_seconds`, `status_coverage_fraction`, `bike_available_seconds`, `dock_available_seconds`, `empty_exposure_fraction`, `full_exposure_fraction` |
| Means (2) | `mean_bikes_available`, `mean_effective_capacity` |
| Quality (4) | `static_capacity_mismatch_seconds`, `timestamp_tied_events`, `status_exposure_missing`, `capacity_mismatch_flag` |
| Weather (5) | `weather_zip_code`, `trace_precipitation`, `temperature_c`, `wind_kmh`, `precipitation_mm` |
