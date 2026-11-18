# Proposed revision to the bike redistribution cost formula

**Draft for Fu Yan's report | 17 November 2026; metric units and two-stage alignment updated 18 November 2026**

## Reason for the revision

The original formula, `C(n, D) = F + c_b * n`, is a useful starting point. It separates the cost of running a redistribution trip from the handling cost of moving bikes. We propose expanding it to represent a truck visiting several stations, with driving, parking, waiting, loading and unloading counted explicitly.

Published research supports considering vehicle, transportation and handling costs when evaluating redistribution. For example, [Ren et al. (2023), Section 4.2](https://www.mdpi.com/2071-1050/15/24/16634), includes these categories. The formula below is our proposed accounting model based on those categories. It has not been calibrated to the SF operator's actual expenses.

## Stage 1: proposed allocation-cost approximation

Fu Yan's multi-stop observation motivates route-level accounting. Joohee's subsequent proposal separates an hourly allocation model from a routing extension. The following makes that separation explicit; it is a proposed formulation for Joohee's review, not a fitted cost function or an implemented optimizer.

For a single-truck scenario:

`estimated_stage1_cost = sum_p(F_p * z_p) + sum_t sum_(i != j)[h_t + k_t * d_ij / Lbar_t] * x_ijt`

| Symbol | Meaning | Unit |
| --- | --- | --- |
| `x_ijt` | Integer bikes relocated from station i to j in hour t | Bikes |
| `d_ij` | Directed road distance between the two stations | Kilometres |
| `h_t` | Handling cost for one bike relocated, covering its loading and unloading | USD/bike |
| `k_t` | Variable truck travel cost per kilometre, with included components documented | USD/truck-km |
| `Lbar_t` | Assumed average bikes sharing the truck travel cost | Bikes; strictly positive |
| `F_p` | Avoidable activation charge for billing period p | USD/activated period |
| `z_p` | Whether the truck is activated in billing period p | Binary |

The dimensions of `k_t * d_ij / Lbar_t` are USD/bike. The handling and travel terms are multiplied by relocated bikes. Average load is an allocation assumption, distinct from onboard truck capacity and hourly throughput. Specify an appropriate average-load range and test sensitivity.

Link movements to activation, for example:

`sum_(i != j) x_ijt <= U_t * z_p(t)`

Here `U_t` is a justified maximum number of bikes relocated during the hour, and `p(t)` maps the hour to its activation billing period. If F is a daily hire fee, the same daily binary applies to all relevant hours and the fee is charged once that day. If F is genuinely a per-dispatch charge, define dispatches accordingly. A fleet model needs vehicle-indexed decisions or an appropriate vehicle-count formulation.

The Stage 1 coefficients must use the same accounting scope as Stage 2. For example, `k_t` may include fuel, maintenance and driving labor/vehicle time, while `h_t` includes handling time. Each component must appear once. Stop setup and depot travel are approximated only if the coefficient calibration explicitly includes them; otherwise disclose their omission from the approximation. No values for h, k, average load, throughput or activation charges have been selected here.

V3 supplies `road_distance_km` and `driving_minutes` in `station_distances`, plus parameter-register entries for handling, per-kilometre cost, average load and activation. The road matrix is a current driving proxy; it does not establish 2015 truck operations. This approximation does not guarantee an executable truck route.

## Stage 2: detailed route-cost accounting

For one vehicle over one operating shift or day:

`C = F * z + (W + V) * H + P * G + M * D + A`

In plain language, total cost equals fixed vehicle charges, crew and vehicle time, fuel, additional distance costs and other direct fees. Add the costs across vehicles and operating days to obtain the total. All working physical measurements use metric units; currency remains USD.

| Symbol | Meaning | Unit |
| --- | --- | --- |
| C | Total operating cost for the vehicle and period | USD |
| F | Fixed activation or hire charge for that period | USD/activated period |
| z | 1 when the vehicle/period is activated; otherwise 0 | Binary |
| W | Total crew cost, including employer benefits | USD/crew-hour |
| V | Additional hourly vehicle charge not already covered by F | USD/hour |
| H | Total paid or chargeable operating time | Hours |
| P | Price of the vehicle's fuel | USD/litre |
| G | Total fuel consumed | Litres |
| M | Additional distance cost, excluding fuel and costs already charged elsewhere | USD/km |
| D | Complete road distance traveled | Kilometres |
| A | Direct fees such as tolls and parking | USD |

If a driver and helper work the same hours, W is their combined loaded hourly cost. If their working hours differ, calculate each worker's cost separately. If the vehicle and crew are billed for different durations, use separate hour totals rather than the common H shown here.

When fuel-use records are unavailable, use `G = D * q / 100`, where `q` is fuel consumption in litres/100 km. The consumption figure must suit the chosen vehicle and operating conditions. If it measures driving only, engine idling may need additional treatment. Do not add idling fuel again if it is already included in measured route fuel use.

## Count all operating time

Using handling times measured in minutes:

`H = driving_hours + stop_setup_hours + (t_load * N_loaded + t_unload * N_unloaded) / 60 + other_paid_hours`

Stop setup covers activities such as parking and accessing the station, excluding bike handling. Other paid time covers attributable preparation or waiting not already counted. Loading and unloading must be counted separately: moving a bike from one station to another normally creates one loading operation and one unloading operation.

For example, 20 relocated bikes create 40 handling operations if each is loaded and unloaded once. Under an explicitly assumed one-minute-per-operation scenario, handling takes 40 minutes. This illustrates the calculation; it is not a measured SF handling rate.

[Pal and Zhang (2017), Section 8](https://www.sum-lab.org/uploads/5/9/0/3/59034329/free-floating_bike_sharing.pdf), tests 30, 60 and 90 seconds per handling operation in its Divvy experiments. These can support sensitivity scenarios, but they should not be described as observed SF values. The same study models vehicle loads and station visits, supporting the need to track capacity along a route.

## Changes from the original calculation

| Issue | Proposed treatment |
| --- | --- |
| A truck may visit several stations | Add the actual route legs, including the required depot travel. |
| Handling time affects paid hours | Include loading and unloading in H; do not charge the same labor again per bike. |
| Rental charges may cover a whole day | Charge daily hire once per activated day. Set V to zero if those hours are already included; model genuine excess-hour charges separately. |
| Distance charges may overlap with maintenance | Use only documented, non-overlapping cost components. |
| Total bikes moved can exceed truck capacity over a tour | Check onboard bikes after every visit. A truck can unload and reload during one tour. |

The number of tours therefore cannot generally be calculated as `ceiling(total bikes moved / truck capacity)`. That shortcut describes limited shuttle cases, not every multi-stop operation. The model must also specify the depot, starting load and end-of-route conditions.

## Evidence for the inputs

The available sources provide useful benchmarks, but they do not establish the operator's actual costs.

| Input | Evidence checked | How it should be used |
| --- | --- | --- |
| Driver wages | [BLS May 2016 SF-Redwood City-South SF estimates](https://www.bls.gov/oes/2016/may/oes_41884.htm), occupation 53-3033: mean $19.35/hour, median $16.19/hour | A local occupational proxy from 2016, not the operator's 2015 payroll. Use a period-matched source where available or disclose the year difference/adjustment. |
| Employer benefits | [BLS March 2015, Table 6](https://www.bls.gov/news.release/archives/ecec_06102015.htm): national private-industry transportation/material-moving compensation $27.55/hour, wages $18.03/hour | The ratio is about 1.528. Applying it to a local wage is a stated assumption, not an SF-specific benefits estimate. Do not add benefits again to an already-loaded labor rate. |
| Gasoline | [EIA California monthly regular gasoline prices](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=M&n=PET&s=EMM_EPMR_PTE_SCA_DPG): February, March and April 2015 convert to about $0.714850, $0.881806 and $0.847992/litre | Historical state proxies matching the selected months. Original source values were 2.706, 3.338 and 3.210 USD/US gallon, divided by the exact 3.785411784 litres/US gallon. These are not SF operator receipts or diesel prices. |
| Handling time | Pal and Zhang's published experimental values above | Scenario values until suitable observations are available. |
| Road distance and travel time | Vehicle logs or a documented routing service; [OSRM's Table service](https://project-osrm.org/docs/v5.24.0/api/#table-service) supplies distance and duration matrices | Routing estimates need their source, map date and vehicle profile recorded. Present-day routing does not establish 2015 traffic conditions or truck access. |
| Vehicle hire, capacity, fuel consumption and maintenance | A dated quote, vehicle specifications and suitable operating records | Still to be verified for the chosen vehicle. Record distance costs per kilometre and fuel consumption in litres/100 km; earlier suggested rates and capacity remain unverified. |

Because the proposed demand period is in 2015, the preferred base case uses compatible historical price assumptions. If current costs are used instead, the study should explicitly describe a hypothetical present-cost scenario and use consistent revenue assumptions. Combining different years without explanation weakens the financial interpretation.

## Match the formula with the model inputs

The customer-trip data does not contain redistribution truck journeys or expenses. Keep three linked tables:

1. **Station-hour data:** observed pickups, returns, availability and estimated demand. Carlo prepares the observations; Fu Yan supplies the demand estimates.
2. **Cost and vehicle inputs:** wages, benefits, hire terms, fuel, capacity, handling times and their sources. Carlo/Jason coordinate these with Fu Yan and Joohee.
3. **Route and policy outputs:** stations visited, bikes loaded/unloaded, kilometres, operating hours, fuel in litres and total cost. These come from the chosen model and evaluation, implemented by Hong Jin.

Every cost parameter should record its unit, price year, source, evidence status and tested range. Distinguish an actual observation from a published proxy or an assumed scenario. Unknown costs must be disclosed rather than silently treated as zero.

This formula evaluates a specified operation. Use the Stage 1 approximation above for allocation and this detailed formula for the routing extension, with the same vehicles, periods and included expenses. A flow allocation alone does not establish a feasible truck route.

## Comparing the two stages

For movements that can be executed within the stated operating rules:

`cost_difference = estimated_stage2_route_cost - estimated_stage1_cost`

The two costs evaluate the same redistribution operation, so do not add them together as separate operating expenses. Stage 2's value remains an estimate because historical truck logs and operator expenses are unavailable. The approximation is not established as either an upper or lower bound, and sequentially optimizing the two stages does not establish joint global optimality.

Before accepting the comparison, verify available bikes/docks at visits, onboard load, pickup/delivery sequencing where required, driving/handling/setup time, depot legs and end conditions. If a route is infeasible, revise the allocation and reassess service and cost, or report the example as an infeasible Stage 1 plan. A TSP visit order alone is insufficient to certify these operations.

## Use in the project objective

Compare each policy with the same no-rebalancing baseline:

`Additional operating contribution = contribution from extra trips served - (policy redistribution cost - baseline redistribution cost)`

Only expenses that change between the policies contribute to the cash-cost difference. Existing wages or vehicle commitments that stay the same cancel in that comparison. Staff time can still limit capacity or carry a separately stated opportunity cost. Bicycle and dock purchases remain outside the agreed scope.

Test low/base/high cost and handling scenarios, and report when rebalancing stops creating positive additional contribution. We cannot yet claim a final cost per relocated bike or a profit improvement because vehicle inputs, demand estimates and feasible operating plans are still incomplete.

## References

- Ren, C., Xu, H., Yin, C., Zhang, L., Chai, C., Meng, Q., and Fu, F. (2023). *Research on Hybrid Scheduling of Shared Bikes Based on MLP-GA Method*. Sustainability, 15(24), 16634. [Article and DOI](https://doi.org/10.3390/su152416634).
- Pal, A., and Zhang, Y. (2017). *Free-floating bike sharing: Solving real-life large-scale static rebalancing problems*. Transportation Research Part C, 80, 92-116. [DOI](https://doi.org/10.1016/j.trc.2017.03.016); [author-hosted full text](https://www.sum-lab.org/uploads/5/9/0/3/59034329/free-floating_bike_sharing.pdf).
- U.S. Bureau of Labor Statistics. *May 2016 Occupational Employment and Wage Estimates: San Francisco-Redwood City-South San Francisco*, occupation 53-3033. [Table](https://www.bls.gov/oes/2016/may/oes_41884.htm).
- U.S. Bureau of Labor Statistics. *Employer Costs for Employee Compensation, March 2015*, Table 6. Released 10 June 2015. [Release](https://www.bls.gov/news.release/archives/ecec_06102015.htm).
- U.S. Energy Information Administration. *California Regular All Formulations Retail Gasoline Prices*, monthly historical series. [Data](https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?f=M&n=PET&s=EMM_EPMR_PTE_SCA_DPG).
- Project OSRM. *HTTP API documentation: Table service*. [Documentation](https://project-osrm.org/docs/v5.24.0/api/#table-service).

Cost-category sources checked on 17 November 2026. The metric conversion and explicit two-stage equations were updated on 18 November using the comments supplied by Carlo. The published categories support the accounting structure; final SF parameter values and model assumptions remain subject to team review. No new numerical cost calibration or optimization was performed by this update.
