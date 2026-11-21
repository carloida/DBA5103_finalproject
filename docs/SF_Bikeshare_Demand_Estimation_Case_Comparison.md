# SF Bike Share demand estimation case comparison

Prepared 22 November 2026. Carlo's data and integration review; final demand case selection to be reconciled with Fu Yan and Joohee.

**Recommendation: historical availability-adjusted rates are the stronger provisional base on the tested reconstruction errors. Fu Yan's v2 hybrid is a useful sensitivity scenario.** The hybrid improves the original unlimited predecessor extrapolation and has some short pre-outage advantages. True unmet demand is unobserved, so these results do not establish either case as the actual missing-customer count.

## 1 Report package and release status

| Resource | Purpose |
| --- | --- |
| [Case A detailed report](supporting/SF_Bikeshare_Demand_Case_A_Historical.md) | Historical-rate formulas, assumptions, numerical results, implementation contract and suggested Section 3.4 text |
| [Case B detailed report](supporting/SF_Bikeshare_Demand_Case_B_Hybrid.md) | Exact hybrid rule, audit, validation corrections, results and suggested Section 3.4 text |
| [Evidence snapshot](../output/sf_bikeshare/demand_case_comparison_2026-11-22/README.md) | Compact validation/policy tables, provisional parameters, bounds and audit fingerprints |
| [Frozen V3](../output/sf_bikeshare/model_inputs_v3/README.md) and [minute supplement](../output/sf_bikeshare/demand_estimation_inputs_v3/README.md) | Common observed inputs |

The reports are reusable case definitions, not a newly approved V4 release. Use the selected case's method in Section 3.4 and retain the other as sensitivity in Section 7. Update implementation and results statements to the final completed run. Full trial demand CSVs, Fu Yan's incomplete producer bundle and Hong Jin's unmerged model code are outside this publication. V3, robustness packages and shared Google Docs are unchanged.

## 2 Common data and different rate assumptions

Both cases cover 34 SF stations, 9 February-19 April 2015, with 57,120 station-hours. Rates use eight training weeks, 9 February-5 April. Validation uses 6-19 April, a previously explored period.

The 31-column demand interface supplements V3's 51-column observed table. Station-hour keys, observed counts and quality fields are preserved. Member/casual pickups and returns are estimated separately. Valid exposure uses preceding nonnegative, non-offline states over positive snapshot gaps at most 90 seconds. Rate numerators use the same available intervals as their denominators.

| Choice | Case A Historical | Case B Hybrid v2 |
| --- | --- | --- |
| Rate at episode onset | Historical station/hour/day-type/rider profile | Prior 30-minute rate if at least 20 available minutes |
| First elapsed hour | Historical profile, updated at clock boundaries | Preceding rate; historical fallback if support fails |
| Later duration | Current historical profile | Current historical profile |
| Historical support | Positive denominator, then station/hour pooling if zero | At least 60 training available minutes, then station/hour pooling |
| Served correction and allocation | Subtract served events once per episode, then allocate proportionally | Same |

All main-case primary groups have at least 840 bike-available or 780 dock-available training minutes, so the historical support difference does not affect these profiles. Other periods require separate support checks.

For either case, the common calculation is:

$$
\widehat\lambda^{H,s}_{i,h,d,r}
=\frac{\sum_{\text{matching training hours}}N^s_{itr}}
{\sum_{\text{matching training hours}}A^s_{it}},
\qquad
M^{c,s}_{er}=\max\left(0,\sum_tE^{c,s}_{etr}-S^s_{er}\right).
$$

Here $N$ is matched available-time events, $A$ available minutes, $E$ segment expected arrivals, $S$ recorded service during an episode, and $M$ missed demand. Allocate $M$ in proportion to segment expectations and add it to observed hourly service. Zero total expectation gives zero allocation. The case reports define the full notation and Case B's first-60-elapsed-minute split.

## 3 Main-case demand totals

| Scenario | Estimated pickups | Added pickups | Estimated returns | Added returns |
| --- | ---: | ---: | ---: | ---: |
| Observed service | 62,243 | 0 | 62,326 | 0 |
| Case A Historical | 64,573.775 | 2,330.775 | 63,014.136 | 688.136 |
| Case B Hybrid v2 | 66,589.924 | 4,346.924 | 63,652.521 | 1,326.521 |
| Original v1, context only | 69,145.528 | 6,902.528 | 64,663.263 | 2,337.263 |

The same 3,799 episodes are retained. For a 497-minute station-64 empty episode, original v1 adds about 231.93 pickups, Case B 15.09, and Case A 1.44. This demonstrates sensitivity to the extrapolation assumption; lower totals alone do not establish accuracy.

Both cases retain observed counts and flags in the 34 missing-exposure DST-related station-hours. They do not reconstruct unknown exposure. Separate pickup and return estimates are not a joint counterfactual journey model.

## 4 Independent matched validation

Targets require full valid availability. Historical rates are fitted only on training dates and integrated across each affected hour/day type. Preceding windows end before hidden targets; Case B falls back when its preceding support is insufficient.

- **Ten-minute pre-outage check:** hide the ten minutes immediately before an episode longer than 15 minutes. There are 163 eligible pickup and 54 return windows.
- **One-hour check:** predict a fully available hour from clock-hour origins; 10,867 pickup and 11,092 return targets.
- **Three-hour check:** predict three fully available hours; 10,178 pickup and 10,672 return targets. The hybrid actually switches after hour one.

| Target | Class/side | Historical MAE | Hybrid MAE | Historical RMSE | Hybrid RMSE |
| --- | --- | ---: | ---: | ---: | ---: |
| 10 min pre-outage | Member pickups | 0.805 | 0.855 | 1.077 | 1.219 |
| 10 min pre-outage | Casual pickups | 0.157 | 0.154 | 0.523 | 0.496 |
| 10 min pre-full | Member returns | 0.910 | 0.895 | 1.217 | 1.222 |
| 10 min pre-full | Casual returns | 0.167 | 0.186 | 0.498 | 0.529 |
| 1 hour | Member pickups | 0.544 | 0.926 | 0.954 | 1.907 |
| 1 hour | Casual pickups | 0.198 | 0.211 | 0.485 | 0.777 |
| 1 hour | Member returns | 0.556 | 0.938 | 1.011 | 1.918 |
| 1 hour | Casual returns | 0.190 | 0.212 | 0.473 | 0.788 |
| 3 hours | Member pickups | 0.958 | 1.267 | 1.545 | 2.187 |
| 3 hours | Casual pickups | 0.441 | 0.477 | 0.841 | 1.033 |
| 3 hours | Member returns | 1.005 | 1.331 | 1.760 | 2.377 |
| 3 hours | Casual returns | 0.432 | 0.467 | 0.837 | 1.032 |

Errors are trips per target window; compare methods within the same horizon. Historical has lower MAE/RMSE in all four categories at one and three hours. Short pre-outage results are mixed. The hybrid has less negative bias there; for member pickups, biases are approximately -0.55 versus -0.73 trips/window.

Both methods underpredict those selected busy windows. Artificial masking does not observe true unmet demand. Available long windows may exclude highly constrained conditions; the short sample is small; overlapping windows are correlated; and validation has been explored repeatedly. The evidence supports a provisional case choice with sensitivity analysis.

## 5 Supplied v2 audit and corrections

Every v2 30-minute exposure denominator, class numerator, use-pre flag, hybrid expected count, served correction and hourly missed-demand value was reconstructed independently. Differences were below $10^{-8}$. All 70 dates load into the model.

| Remaining issue | Evidence | Action |
| --- | --- | --- |
| Missing core module | Wrapper imports run() from a revised build_demand_minute.py; it is absent and the older copy lacks run() | Supply exact core and validation implementation |
| Mixed training/validation summary | 939 of 1,165 scored episode windows are training-period observations | Report held-out dates separately |
| Incomplete hidden targets | 39 scored targets have only 540 available seconds out of 600, including nine held-out targets | Require complete availability or explicitly redefine exposure-matched targets |
| Hour-crossing benchmark | Fully available targets use the starting-hour rate throughout | Integrate each affected hour |
| Horizon comparison | Constant preceding-rate forecasts alone do not evaluate the first-hour switch | Directly test the full hybrid |

The independent validation above corrects these target and benchmark definitions. Numerical agreement does not make the incomplete producer bundle a reproducible release. Recorded service inside actual outages is a censoring diagnostic, not unmet-demand accuracy.

## 6 Illustrative OR model sensitivity

The same prototype compared no rebalancing, equal occupancy and optimized moves: two cases x four dates x three policies = **24 evaluations**.

Common provisional settings are 24-hour independent days initialized from observed midnight stock; dock_count capacity; at most one truck; throughput 15 bikes/hour; average load 15; fixed cost USD60/truck-day; handling USD1/bike; distance coefficient USD0.30/km divided by average load; member/casual allocated values USD0.88/4.50; and failed-return penalty USD0.88/bike. Each origin has five nearest destinations. The MILP has a ten-second cap and 1% relative-gap target.

These are prototype settings, not a completed calibration to Jason's cost references.

| Date | Historical feasible additional contribution, USD | Hybrid feasible additional contribution, USD | Historical gap | Hybrid gap |
| --- | ---: | ---: | ---: | ---: |
| 6 April | 18.23 | 26.44 | 3.18% | 0.07% |
| 10 April | 2.97 | 8.00 | 0.19% | 0.09% |
| 11 April | 0.00 | 0.00 | 0.00% | 0.00% |
| 15 April | 42.56 | 57.26 | 0.60% | 0.73% |

Additional contribution is relative to no rebalancing within the same demand case. It is allocated trip value minus redistribution cost and failed-return penalties, not cash profit. Schedules replay under the separate policy evaluator. Both cases give positive feasible improvements on three dates and no moves on 11 April.

The historical 6 April run reached its time limit. Use [solver upper bounds](../output/sf_bikeshare/demand_case_comparison_2026-11-22/optimized_policy_bounds.csv), not incumbent differences alone, when assessing objective uncertainty. Status zero means termination within configured tolerance, not necessarily zero gap. More estimated demand or larger modelled contribution does not establish demand accuracy.

Routes remain unverified. Both cases retain same-hour aggregate transfers, pickups before fixed returns, proportional rider service, independent midnight resets and retrospective knowledge of daily demand. Fixed internal returns are not linked to accepted counterfactual rentals. These four dates were already reviewed; this is not a fresh sealed test or completed evaluation of all five robustness cases.

## 7 Course alignment and report placement

| Course material | Connection |
| --- | --- |
| Lecture 6 Network, pp. 17-18 | Flow conservation and capacities; demand estimates are inputs |
| Lecture 7 IP, p. 4 | Integer relocations can coexist with continuous expected service/stock |
| Lecture 4 Duality and Sensitivity, pp. 25-26 | Uncertain inputs motivate what-if analysis and re-solving |
| Project Guideline, p. 1 | Explain practical assumptions, robustness and complete implementation code |

The lectures support the OR framework; they do not establish statistical superiority of either demand estimator. LP sensitivity ranges are not a substitute for re-solving the mixed-integer model.

Use the selected method in Section 3.4, matching model assumptions in Section 4, solver/configuration in Section 5, final policy results in Section 6 and the alternative demand case/limitations in Section 7. Carlo's observed-data preparation remains distinct from estimated demand.

## 8 Adoption and handoff

| Owner | Deliverable before final release |
| --- | --- |
| Fu Yan | Complete core module; selected case options; rates, episodes and corrected validation; Section 3.4 |
| Joohee | Explicit case selection, aligned formulation/configuration and empirical reruns |
| Jason | Final numerical cost inputs, units and sources |
| Hong Jin | Solver/results review, final tables and sensitivity/robustness analysis |
| Carlo | Interface/provenance checks, reconciled release, data text and final edit |

Neither case is a published self-contained demand release yet: Case A's trial reused the audited episode export, and Case B needs its revised core. The reports provide complete mathematical definitions and checked evidence, while implementation handoff and team selection remain explicit tasks.

Keep Case A as provisional base and Case B as sensitivity unless the team chooses otherwise. Observed trips can form a lower-bound demand scenario. Freeze the rule/settings before further evaluation. Apply the same fitting protocol to robustness cases without using evaluation targets for fitting; parameterise dates and audit support/missing opening stocks for each case.

No further main-case feature engineering is required. Preserve V3, use metric physical units and USD, and release final estimated-demand outputs separately.

## 9 References

1. O'Mahony, E., and Shmoys, D. B. (2015). [Data Analysis and Optimization for (Citi)Bike Sharing](https://cdn.aaai.org/ojs/9245/9245-13-12773-1-2-20201228.pdf). Twenty-Ninth AAAI Conference on Artificial Intelligence, Section 3.
2. Freund, D., Norouzi-Fard, A., Paul, A., Wang, C., Henderson, S. G., and Shmoys, D. B. [Data-driven rebalancing methods for bike-share systems](https://people.orie.cornell.edu/shane/pubs/BSOvernight.pdf). Author-hosted manuscript, Section 3; accessed 22 November 2026.
3. NUS DBA5103 course materials supplied locally: Lecture 4 Duality and Sensitivity, pp. 25-26; Lecture 6 Network, pp. 17-18; Lecture 7 IP, p. 4; Project Guideline, p. 1. Course PDFs are not redistributed.
4. [V3](../output/sf_bikeshare/model_inputs_v3/README.md), [minute supplement](../output/sf_bikeshare/demand_estimation_inputs_v3/README.md) and [comparison manifest](../output/sf_bikeshare/demand_case_comparison_2026-11-22/manifest.json).

Operator-linked research motivates availability-conditioned inference and time-varying rates. The exact exposure weighting, rider split and hybrid thresholds are project adaptations. They are not claimed to reproduce Bay Area Bike Share's actual 2015 procedure.
