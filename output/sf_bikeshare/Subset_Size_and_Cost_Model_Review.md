# Subset size and cost model: review before proceeding

Prepared 17 November 2026. The candidate remains provisional. This note does not approve a final scope, change the EDA/model, or upload anything.

## Exact size comparison

The full raw files total 2,070,348,941 bytes: station 5,647; trip 80,208,848; weather 438,063; status 1,989,696,383. The candidate Parquet is 247,473 bytes.

| Basis | Full dataset | Candidate | Candidate share |
| --- | ---: | ---: | ---: |
| Listed stations | 70 | 34 | 48.57% |
| Installation-eligible hourly panel rows | 1,209,456 | 57,120 | 4.7228% |
| Distinct completed trips relevant to the station/time window | 669,959 | 63,974 | 9.5489% |
| Raw status snapshots in the selected station/time scope | 71,984,434 | 3,424,038 | 4.7566% |
| File storage, decimal MB | 2,070.348941 | 0.247473 | 0.0119532% |

Relevant trips have at least one selected endpoint event in [2015-02-09, 2015-04-20). They are counted once, including boundary trips; they are not exported as individual records in the candidate. The candidate contains 62,243 departure events and 62,326 arrival events, which must not be added together to count journeys. Status snapshot count describes source observations in scope, not rows stored in the hourly candidate.

The candidate is about 8,366 times smaller than the four raw CSVs, a 99.9880% storage reduction. This combines geography/time restriction, removal of raw record detail, hourly aggregation and compression. It does not mean the study uses only 0.012% of the original observations or that it retains every original variable. The full database still occupies 1,565,274,112 bytes and remains on disk; no raw files/database were deleted.

The current export has eight training weeks (9 February-5 April 2015) and two exploratory validation weeks (6-19 April): 45,696 and 11,424 rows respectively. Its four-week training alternative (9 March-5 April) has 22,848 rows, or 1.8891% of the full hourly panel. The earlier assessment found similar average completed-departure MAE for four and eight weeks; it did not test latent-demand accuracy or policy profit equivalence.

Evidence: local source_manifest.json, assessment_manifest.json and read-only DuckDB count queries. Percentages use the denominators shown above; MB/GB here are decimal units.

## EDA that can follow your review

The current subset is suitable for a focused operational EDA: hourly weekday/weekend pickups and returns; station heatmaps; net flow; empty/full exposure with valid-time denominators; missingness/coverage; capacity diagnostics; and descriptive weather comparisons. Show training and validation dates separately and select stations/targets using training information.

It cannot directly support individual ride-duration distributions, rider-class revenue analysis, exact opening stocks or within-hour event sequencing. Add only the corresponding filtered trip rows and bounded status observations if these are needed. The source trip file is about 80.21 MB; those additions do not require loading the entire status CSV into memory. Opening inventory requires a valid preceding snapshot plus its age, not an hourly mean. The eight-week training period has only five measurable-rain days, so station-specific rain effects will be weakly supported.

## Cost model to propose to the team

Use Fu Yan's cost categories as the starting point. Revise the calculation to cover complete multi-stop routes, separately identify payable time and avoid double counting. The following is an analyst-designed accounting formulation informed by [1] and [2], not an empirically calibrated Bay Area operator cost function.

For a vehicle v over an operating shift/day:

`C_v = F_v * z_v + (W_crew,v + V_hour,v) * H_v + P_v * G_v + M_v * D_v + A_v`

Total rebalancing cost is the sum over vehicles/shifts. Define:

- `z_v`: 1 if the relevant vehicle/shift is activated, otherwise 0.
- `F_v`: avoidable fixed activation/hire charge, USD per activated vehicle/shift. Specify its billing period. A daily rental belongs here once per day, not once at every station or on each route made that day.
- `W_crew,v`: total loaded hourly cost of the crew, USD/crew-hour; sum driver and helper compensation if both work the same hours. Use separate worker-hour terms if their paid hours differ.
- `V_hour,v`: additional vehicle cost per hour, excluding fuel, mileage and anything already in F. Set to zero if the fixed rental already covers those hours; add only genuine excess-hour charges as appropriate.
- `H_v`: all paid/chargeable hours attributable to the operation across the shift's routes.
- `P_v`: period-matched USD per gallon of the correct fuel.
- `G_v`: total gallons consumed. Prefer vehicle/route records. `D_v / MPG_v` is an approximation using a defined, applicable fuel-economy measure; driving-only economy needs additional treatment of engine idling. Do not add idling fuel again if the measured route MPG already includes it.
- `M_v`: incremental mileage cost, USD/mile, excluding fuel and items already included in hire or other charges. Do not substitute a heavy tractor-trailer maintenance figure for an urban van without evidence.
- `D_v`: complete road-route miles, including relevant depot access/return and intermediate legs.
- `A_v`: attributable parking, tolls and other documented cash fees. Unchanged general overhead is excluded from incremental policy comparisons.

Decompose time, all in hours:

`H_v = driving_hours + stop_setup_hours + alpha_load * N_loaded + alpha_unload * N_unloaded + other_paid_hours`

Stop setup is parking/access/administration time excluding bike handling. Other paid hours include attributable depot preparation and waiting not already counted. Account for every visit on a multi-stop route. A bike picked up and delivered once usually creates one load and one unload; a per-operation time must therefore be applied twice to that bike. Include extra handling only if it occurs. Enforce onboard load after each visit between zero and vehicle capacity. `ceil(total_bikes_moved / capacity)` is not a general tour-count formula because a vehicle can unload and reload on the same tour [2].

For the incremental-profit objective, use `C_policy - C_no_rebalancing` with the same accounting perspective. Existing committed wages or vehicle charges do not become additional cash expenses merely because time is allocated to rebalancing. They can still be modeled as capacity limits or separately labeled opportunity costs. Do not combine both treatments indiscriminately. Keep bicycle/dock capex outside the agreed scope.

## What is sourced, and what remains unknown?

| Parameter | Verified reference or acquisition method | Interpretation/status |
| --- | --- | --- |
| Cost categories | Ren et al. (2023), section 4.2 [1] | Supports vehicle, travel and handling categories; does not provide SF calibration for this study. |
| Driver wage | BLS May 2016 SF-Redwood City-South SF, SOC 53-3033: mean $19.35/hour, median $16.19/hour [3] | Verified nearby-period occupational proxy. It is 2016, not 2015, and is not the bike-share operator's payroll. Not adopted as an exact 2015 base value. Retrieve period-matched payroll/official 2015 wage data where available; otherwise disclose the proxy or harmonization. |
| Benefit loading | BLS March 2015, private-industry transportation/material-moving occupation group: total compensation $27.55/hour and wages $18.03/hour [4] | Derived multiplier 27.55/18.03 = about 1.528. National broad-occupation proxy, not an SF-specific driver benefit package. Benefits are about 52.8% of wages here; the percentage of total compensation is a different denominator. Applying this ratio to another wage is an assumption requiring sensitivity analysis. |
| Gasoline | EIA California regular gasoline monthly 2015: February $2.706, March $3.338, April $3.210 per gallon [5] | Verified historical state proxy matching candidate months. Not SF-specific, not diesel, and not actual operator receipts. Use date-specific values rather than a current price in a historical scenario. |
| Handling time | Pal and Zhang (2017), Divvy case study, section 8: experimental values 30/60/90 seconds per loading or unloading operation [2] | Literature-based sensitivity choices, not measured SF handling times. One load plus one unload gives 1/2/3 minutes per relocated bike at these rates. Prefer operator/timed observations. |
| Distance/time | Station/depot coordinates plus directed road-routing matrix or vehicle logs; OSRM Table service returns distance and duration matrices [6] | Routing outputs are estimates. Default driving profiles and present-day maps do not establish historical 2015 congestion or truck restrictions. Document provider/date/profile and scenario travel delays. |
| Vehicle hire | Actual dated rental/lease quote for a specified suitable vehicle, including term, mileage allowance and excess charges | No verified price selected. Do not retain the earlier $17-24/hour as an established fact. A fully historical study needs historical evidence or a disclosed price-year adjustment/proxy. |
| Capacity and fuel economy | Specific vehicle manufacturer data plus bike packing/loading configuration and applicable fuel-use records/test | Payload weight alone does not establish how many docked bikes fit. No 20/30/40-bike capacity or 14-MPG value is treated as observed. |
| Maintenance, stop time, depot and crew size | Operator records or documented measurements/appropriate vehicle evidence | Still uncalibrated. State exclusions and test ranges if evidence cannot be obtained. Zeroing an unknown is also an assumption, not evidence that it is free. |

There is not yet enough evidence to compute a defensible final dollar cost per bike. That quantity is an output `route_cost / relocated_bikes`, conditional on the route and nonzero throughput, rather than a universal input. Publication of a parameter in a simulation paper does not make it an empirical SF estimate.

## Cost features and their table grains

1. Keep the observed station-hour EDA table as observed data. Add quality flags and scope definitions as needed, not invented cost observations.
2. Create a separate **vehicle/period parameter table**: vehicle type, price year, crew, loaded wage, hire terms, fuel type/price, fuel economy, capacity, handling time, evidence URL, observed/proxy/assumed status and uncertainty.
3. Create a **directed station/depot-pair table**: from/to IDs, road miles, travel minutes, routing source/date/profile and restriction flags. Straight-line distance can be an explicitly labeled preliminary proxy.
4. Create a **policy/route result table** after optimization: route, bikes loaded/unloaded, miles, drive/stop/handling hours, fuel, labor/vehicle/total cost, cost per relocated bike, extra trips served and incremental contribution. The current data do not contain historical truck routes or actual rebalancing expenditure.

## Next moves, in order

1. Review the candidate's stations, dates, variables and new history-window comparison. The candidate is not yet the final team decision.
2. After your decision, freeze region, time bins, training/validation/evaluation dates and boundary-flow rules with the team.
3. Run a new subset EDA notebook using the compact panel and selected supplemental records only where needed. Keep the full EDA as context and an audit reference.
4. In parallel, Carlo/Jason prepare the sourced parameter register, identify a vehicle/depot scenario, and obtain the missing vehicle/handling evidence. Use clearly labeled ranges when records are unavailable.
5. Carlo hands observed flows/exposure to Fu Yan. Fu Yan estimates censored demand and flags weak/zero exposure; Joohee confirms how accepted trips and later returns conserve bicycles.
6. Hand the agreed inputs to Joohee/Hong Jin for identical-baseline comparison: no rebalancing, rule-based and optimized. Route-based costs require feasible routes; do not present a route-free flow model as a validated truck plan.
7. Hong Jin re-solves cost/capacity/demand scenarios and evaluates policy performance on later common scenarios; team reports uncertainty, break-even conditions and limitations. Review the notebook/results before any GitHub handoff.

## References checked

[1] Ren, C., Xu, H., Yin, C., Zhang, L., Chai, C., Meng, Q., and Fu, F. (2023). Research on Hybrid Scheduling of Shared Bikes Based on MLP-GA Method. Sustainability, 15(24), 16634. Section 4.2. https://doi.org/10.3390/su152416634

[2] Pal, A. and Zhang, Y. (2017). Free-floating bike sharing: Solving real-life large-scale static rebalancing problems. Transportation Research Part C, 80, 92-116. Sections 3 and 8. https://doi.org/10.1016/j.trc.2017.03.016 ; author-hosted full text: https://www.sum-lab.org/uploads/5/9/0/3/59034329/free-floating_bike_sharing.pdf

[3] U.S. Bureau of Labor Statistics. May 2016 OES, SF-Redwood City-South SF metropolitan division, Light Truck or Delivery Services Drivers, 53-3033. https://www.bls.gov/oes/2016/may/oes_41884.htm

[4] U.S. Bureau of Labor Statistics. Employer Costs for Employee Compensation, March 2015, Table 6, private industry, transportation and material moving. Released 10 June 2015. https://www.bls.gov/news.release/archives/ecec_06102015.htm

[5] U.S. Energy Information Administration. California Regular All Formulations Retail Gasoline Prices, monthly historical series, dollars per gallon. https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=M&n=PET&s=EMM_EPMR_PTE_SCA_DPG

[6] OSRM API documentation, Table service. https://project-osrm.org/docs/v5.24.0/api/#table-service

References checked online on 17 November 2026. No rental quote, SF operator-specific handling study or actual operator cost ledger was verified. The formula and numerical scenario choices must retain these limitations in the report.
