# Case B Hybrid predecessor and historical demand

> **Integration update:** PR #2 now supplies the complete core and reproduces the validation tables on this temporary branch. The missing-core findings below describe the earlier audit snapshot. See the [current integration review](../INTEGRATION_REVIEW_2026-11-22.md) for resolved items, updated costs and new model results.

Prepared 22 November 2026 for the DBA5103 SF bike redistribution project.

**Status: audited sensitivity candidate based on Fu Yan's v2 specification.** Its numerical demand outputs match the documented hybrid rule and load into the model. The supplied producer bundle is incomplete and its original validation needs corrections before final release. This report can also describe the base scenario if the team selects it, provided Case A remains a comparison and the assumptions are reported.

See the [comparison overview](../SF_Bikeshare_Demand_Estimation_Case_Comparison.md) and [Case A](SF_Bikeshare_Demand_Case_A_Historical.md).

## 1 Purpose and rationale

Case B combines recent station-specific activity with a historical time-of-day profile. The preceding rate responds to a potentially busy day, while the switch after one elapsed hour prevents a brief observed rate from continuing unchanged throughout a long overnight outage.

Fu Yan's v2 uses a **30-minute lookback**, requires at least **20 valid available minutes**, and limits predecessor extrapolation to the **first 60 elapsed minutes** of each episode. These are analytical choices to assess, not documented universal bike-share operating rules.

For an outage beginning at 23:40, the preceding rate can apply until 00:40, not merely until the next clock-hour boundary. Subsequent expected arrivals use the historical profile of each current hour/day type.

## 2 Common observations and time handling

The case uses the same 34 SF stations, 9 February-19 April 2015, eight training weeks and two validation weeks as Case A. It produces 57,120 station-hours with member/casual pickups and returns.

The [minute supplement](../../output/sf_bikeshare/demand_estimation_inputs_v3/README.md) preserves actual recorded snapshot seconds and trip minute precision. A status interval is valid only for a positive gap of at most 90 seconds and a nonnegative, non-offline preceding state. Exposure is computed by elapsed time, not snapshot row count.

Pickup rates use matched events while bikes are available; return rates use matched events while docks are available. Invalid states and long gaps are unknown. Trips with an outside-cohort endpoint retain the selected-station pickup or return. Recorded DST gaps are flagged rather than repaired.

## 3 Historical profile and preceding-window rate

Let $i,t,h(t),d(t),r,s$ denote station, dated hour, clock hour, day type, rider class and pickup/return side. Let $N^s_{itr}$ count served events matched to available exposure $A^s_{it}$, in minutes. For training group $\mathcal T_{i,h,d}$:

$$
\widehat{\lambda}^{H,s}_{i,h,d,r}
=\frac{\sum_{u\in\mathcal T_{i,h,d}}N^s_{iur}}
{\sum_{u\in\mathcal T_{i,h,d}}A^s_{iu}}.
$$

The v2 specification requires at least 60 available training minutes in the station/hour/day-type group. Otherwise pool across day types for the same station/hour, requiring the same support; if that fails, flag the rate unresolved. Every primary group in main V3 exceeds this threshold, so these fallback branches need separate tests before other cases are released.

For episode $e$ beginning at $\tau_e$, define preceding window:

$$
W_e=[\tau_e-30\text{ minutes},\tau_e).
$$

Let $a^s_e$ be valid available minutes in that window and $n^s_{er}$ matched available-time events for rider $r$. Then:

$$
\widehat{\lambda}^{pre,s}_{er}=\frac{n^s_{er}}{a^s_e}
\quad\text{when }a^s_e\ge20.
$$

The support rule is based on available exposure, not requiring a positive event count. Zero events during sufficient exposure produce a valid zero rate.

## 4 Hybrid expectation, served subtraction and allocation

Let $w^s_{et}$ be episode outage minutes within dated hour $t$. Define:

$$
v^s_{et}=
\begin{cases}
\left|e\cap t\cap[\tau_e,\tau_e+60\text{ minutes})\right|_{\text{minutes}},
& a^s_e\ge20,\\
0,&a^s_e<20.
\end{cases}
$$

Expected arrivals for the episode/hour/class segment are:

$$
E^{B,s}_{etr}
=\widehat{\lambda}^{pre,s}_{er}v^s_{et}
+\widehat{\lambda}^{H,s}_{i(e),h(t),d(t),r}
\left(w^s_{et}-v^s_{et}\right).
$$

When preceding support is insufficient, set the preceding component to zero and apply the historical profile throughout; do not evaluate an undefined preceding rate. At each clock boundary, split the historical portion using the current hour and day type.

With $S^s_{er}$ the actual served events in the episode's study-window portion:

$$
E^{B,s}_{er}=\sum_tE^{B,s}_{etr},
\qquad
M^{B,s}_{er}=\max\{0,E^{B,s}_{er}-S^s_{er}\}.
$$

Allocate $M^{B,s}_{er}$ to hours proportionally to $E^{B,s}_{etr}$, with zero allocation when total expected arrivals are zero. Add each allocated amount to the full observed station-hour count:

$$
\widehat D^{B,s}_{itr}=O^s_{itr}+
\sum_{e:i(e)=i}M^{B,s}_{etr}.
$$

The subtraction occurs once per episode, separately by class and service side. Repeated hourly subtraction would change the method and can double-count the correction.

## 5 Assumptions and interpretation

The preceding available-time rate approximates arrivals during the first elapsed hour, conditional on sufficient exposure. Historical patterns approximate the remaining duration. Riders encountering unavailable service are not explicitly modelled as waiting or redirecting elsewhere. Pickup and return reconstruction is separate, so additional estimated pickups are not linked to counterfactual later returns.

The 30-minute lookback reduces sampling noise relative to 15 minutes but does not remove it. The one-hour transition is a tested scenario setting, not a statistically identified optimum. Peak-only predecessor use would be an additional scenario requiring its own definition and validation; no off-peak missed demand is silently forced to zero here.

## 6 Main-case results and compatibility

The full [hybrid CSV and compressed download](../../output/sf_bikeshare/demand_estimation_cases_2026-11-22/README.md) are published as provisional output snapshots. This is the audited v2 output; publication does not resolve the missing producer module described below.

| Quantity | Observed | Estimated | Added |
| --- | ---: | ---: | ---: |
| Pickups | 62,243 | 66,589.924 | 4,346.924 |
| Returns | 62,326 | 63,652.521 | 1,326.521 |

The v2 output uses the same 57,120 rows and 31 columns as the earlier demand file. Observed counts, station-hour keys and V3 quality fields are unchanged. It retains the same 3,799 episodes and served-event counts.

The independent audit reconstructed every 30-minute availability denominator, matched class numerator, use-pre flag, hybrid expected count, served correction and hourly missed-demand value. Maximum numerical discrepancies were below $10^{-8}$. All 70 dates load through the previously reviewed model interface.

The 497-minute station-64 example adds approximately **15.09 pickups** here, compared with **231.93** in the original unlimited preceding-rate version and **1.44** in Case A. This demonstrates the effect of the transition, not the actual number of unsuccessful customers.

The 34 missing-exposure DST-related station-hours retain observed demand with explicit flags; unknown demand is not recovered there. Estimated counts remain fractional expected quantities.

## 7 Corrected matched validation

Targets must have valid availability throughout. The ten-minute pre-outage check selects episodes longer than 15 minutes, hides the ten minutes immediately before onset, and estimates the preceding rate from the 30 minutes before that target. Insufficient preceding exposure triggers historical fallback. Only targets fully within 6-19 April are scored.

One-hour and three-hour targets begin at clock-hour origins in the validation period. The historical benchmark integrates each affected hour's rate. The three-hour Case B predictor uses its preceding rate for hour one and historical rates thereafter.

| Target and rider | Windows | Case B MAE | Case A MAE | Case B RMSE | Case A RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 10 minutes before outage, member pickups | 163 | 0.855 | 0.805 | 1.219 | 1.077 |
| 10 minutes before outage, casual pickups | 163 | 0.154 | 0.157 | 0.496 | 0.523 |
| 10 minutes before full docks, member returns | 54 | 0.895 | 0.910 | 1.222 | 1.217 |
| 10 minutes before full docks, casual returns | 54 | 0.186 | 0.167 | 0.529 | 0.498 |
| Next 1 hour, member pickups | 10,867 | 0.926 | 0.544 | 1.907 | 0.954 |
| Next 1 hour, member returns | 11,092 | 0.938 | 0.556 | 1.918 | 1.011 |
| Next 3 hours, member pickups | 10,178 | 1.267 | 0.958 | 2.187 | 1.545 |
| Next 3 hours, member returns | 10,672 | 1.331 | 1.005 | 2.377 | 1.760 |

Case A has lower MAE and RMSE in all four class/side categories at one and three hours, including casual demand. Case B has small short-window advantages and less average underprediction near outages. For member pickups in the ten-minute targets, mean actual count is about 1.20; biases are approximately -0.55 for Case B and -0.73 for Case A. Neither fully captures the busy pre-outage population.

The full results, including casual demand, bias and alternative origin groups, are in the [evidence tables](../../output/sf_bikeshare/demand_case_comparison_2026-11-22/README.md). Available target periods differ from actual outages; the short sample is small; long targets overlap; and validation has been explored repeatedly. These are conditional reconstruction checks, not observed-unmet-demand accuracy.

## 8 Corrections required in the supplied validation

The original v2 short-window summary scores 1,165 episode windows, including 939 training-period windows. Its aggregate score is therefore not a clean chronological holdout result.

It also marks 39 targets valid despite having only 540 available seconds out of 600, including nine validation-period targets. These do not satisfy the agreed fully available target definition. Exclude them, or define and score an exposure-matched target explicitly.

For fully available held-out targets crossing a clock-hour boundary, the supplied historical benchmark equals the starting-hour rate multiplied by ten minutes. It should instead integrate both affected hourly rates, matching the actual Case A method and Case B's historical component.

The original horizon table compares constant preceding-rate forecasts with historical forecasts. It does not by itself evaluate the actual first-hour switch. The independent results above directly test the hybrid.

Predictions versus recorded service inside actual outages are descriptive censoring diagnostics. Missing customers leave no observed count, so those comparisons cannot be labelled unmet-demand accuracy.

## 9 Code handoff and implementation requirements

The supplied v2 file build_demand_hybrid.py imports run() from build_demand_minute.py. The revised core module is absent from the supplied v2 directory; the earlier parent-folder module defines main(), not the required run(). Executing the supplied wrapper fails with a missing-module error.

This is a producer-package completeness issue. The audited numerical CSV is usable for provisional model checks, but the supplied files alone do not reproduce it. Obtain the revised core module and validation implementation before final publication of model-ready demand or the code appendix.

The complete producer should accept historical/hybrid options, retain common exposure/episode logic, produce the same 31-column contract, and export the rate, episode and validation audits separately. Keep estimated demand outside the frozen observed V3 folder.

## 10 Model sensitivity and readiness

Four daily integration checks use the same observed midnight stock, dock_count, cost/resource assumptions and three policies as Case A. Case B feasible additional allocated contribution is **USD26.44, USD8.00, USD0 and USD57.26** on 6, 10, 11 and 15 April. All four optimization runs meet the 1% relative-gap tolerance.

These are provisional restricted-neighbour Stage 1 runs with routes unverified. Larger estimated demand or larger modelled contribution does not establish estimator accuracy or actual cash gain. The full cost specification and solver bounds are in the [evidence snapshot](../../output/sf_bikeshare/demand_case_comparison_2026-11-22/README.md).

If Case B is adopted as base, report the decision explicitly and retain Case A as a sensitivity case. If Case A is adopted as base, retain Case B to test the effect of recent-activity information and its larger estimated demand. Neither choice changes observed V3 features.

## 11 Suggested Section 3.4 wording

> We constructed a hybrid demand scenario using timestamped trips and valid status exposure. For each empty/full episode, the initial arrival rate was estimated separately by rider class from served events during valid available intervals in the preceding 30 minutes. At least 20 available minutes were required. The rate was applied to the episode's first 60 elapsed minutes; subsequent exposure used historical station/hour/day-type rates fitted on the first eight weeks. Insufficient preceding exposure triggered historical rates throughout. Expected arrivals were summed across the episode, recorded service during it was subtracted once, and nonnegative residual missed demand was allocated proportionally to hourly records.
>
> Validation used fully available hidden targets in the later two weeks, comparing both methods on identical windows. The hybrid showed some short pre-outage advantages and less negative bias, while historical-only rates had lower one- and three-hour errors. Actual unmet demand remained unobserved. We therefore evaluate the optimization under both demand scenarios and report sensitivity to the estimation assumptions.

This text describes the local scenario comparison. Complete the core-module handoff and corrected validation before presenting the producer as a final reproducible release.

## 12 Course and research references

- DBA5103 Lecture 6, Network, pp. 17-18: demand enters a balance/capacity model.
- DBA5103 Lecture 7, IP, p. 4: mixed integer/continuous formulation supports expected fractional service with integer relocation decisions.
- DBA5103 Lecture 4, Duality and Sensitivity, pp. 25-26: re-solve under alternative uncertain inputs and compare outcomes.
- [O'Mahony and Shmoys (2015)](https://cdn.aaai.org/ojs/9245/9245-13-12773-1-2-20201228.pdf), Section 3, provides related historical censoring correction.
- [Freund et al., Data-driven rebalancing methods for bike-share systems](https://people.orie.cornell.edu/shane/pubs/BSOvernight.pdf), author-hosted manuscript, Section 3, allows time-varying rates.

The course PDFs are not redistributed. These references do not prescribe the 30-minute lookback, 20-minute exposure minimum or one-hour switch; those remain this case's tested assumptions.
