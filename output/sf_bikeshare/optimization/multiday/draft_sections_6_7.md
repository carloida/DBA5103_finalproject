# DBA5103: Draft Section 6 and Section 7 results (exploratory)

> **Status:** computational Stage 1 scenarios, not actual financial performance. All numerical results use provisional costs and retrospective estimated demand; routes are not fully certified.

## Section 6 — Results and comparison

The analysis evaluated 4 selected days (2015-04-06, 2015-04-10, 2015-04-11, 2015-04-15), each with 34 stations and 24 hourly periods. The same midnight inventory, estimated pickup and return demand, station capacities and provisional cost assumptions were applied to the no-rebalancing, equal-occupancy heuristic and optimized policies. The latter solves a mixed-integer program with the five-nearest-destination restriction per origin and a one-truck, 15-bike/hour throughput constraint.

Across the selected days, the optimized Stage 1 solution improved modeled contribution relative to the no-rebalancing counterfactual by $87.57 in total, or $21.89 per day (range $0.00 to $57.60). The unweighted mean reduction in estimated unmet pickups was 36.2% across days. This is a descriptive calculation on selected dates, not a population estimate or out-of-sample policy performance claim.

Daily modeled contribution (USD):

| Date | No rebalancing | Equal-occupancy rule | Optimized | Increment vs no rebalance |
|---|---:|---:|---:|---:|
| 2015-04-06 | $988.74 | $844.66 | $1,015.19 | $+26.45 |
| 2015-04-10 | $1,161.61 | $1,043.03 | $1,165.13 | $+3.52 |
| 2015-04-11 | $691.44 | $589.62 | $691.44 | $+0.00 |
| 2015-04-15 | $1,064.91 | $912.57 | $1,122.51 | $+57.60 |

The equal-occupancy policy is a simple heuristic that moves whole bikes toward a common dock-occupancy fraction. It is not optimized for marginal demand or economic contribution. It is evaluated through the same station-hour stock and trip-service equations as the optimization, without assuming historic inventory is a no-rebalancing trajectory.

## Section 7 — Sensitivity, routing and limitations

For a **fixed optimized transfer schedule**, the break-even fixed truck activation cost is the extra allocated trip value plus the avoided return-failure penalty, less variable transfer costs. It is a schedule-specific accounting threshold and does not establish a global break-even tariff or cash profit.

| Date | Fixed schedule: break-even daily truck charge | Break-even handling USD/bike |
|---|---:|---:|
| 2015-04-06 | $86.45 | $1.252 |
| 2015-04-10 | $63.52 | $1.068 |
| 2015-04-11 | n/a | n/a |
| 2015-04-15 | $117.60 | $1.476 |

On 2015-04-06, the following sensitivity cases were **reoptimized**: throughput_low, throughput_high. Their solver statuses and MIP gaps are in `reoptimization_sensitivity.csv`. Other cost scenarios shown here reprice the fixed original schedules only.

### Interpretation and limitations

1. The retrospective own-hour availability adjustment uses observed arrivals from within the hour; it is **not** a prospective forecast. The two April validation weeks were already examined during method development and are not a sealed holdout.
2. Estimated pickups and returns are fractional expected counts; the model uses proportional service by rider type. Returns are treated as fixed even when the policy blocks departures, so counterfactual network conservation is approximate.
3. Stage 1 permits only each station’s five nearest destination arcs and assumes transfers arrive at the start of their assigned hour. Thus its MIP gap does not measure the gap to the unrestricted fleet-routing problem.
4. The Stage 2 check does not enforce the exact minute of customer pickups, depot or daily shift/depot costs. Passing it is a **conditional** result, not full operational certification; no route-adjusted profit was estimated.
5. Monetary quantities are allocated rider-pass values and scenario cost proxies, not observed marginal revenue or actual redistribution expenditure. The sensitivity ranges are illustrative rather than statistically calibrated.

### Required before final report

Confirm cost parameters and cite their sources; verify each solver status and gap; choose how to handle failed returns and in-transit rides; report routing failures explicitly; use any untouched held-out date set only after generating demand estimates without look-ahead.
