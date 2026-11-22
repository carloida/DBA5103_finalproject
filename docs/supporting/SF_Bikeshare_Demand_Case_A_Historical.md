# Case A Historical availability adjusted demand

> **Release update:** historical is the team-confirmed base; hybrid is sensitivity. The complete PR #2 producer reproduces both outputs, and the reviewed model plus completed report results are published. Pending/missing-core findings below are dated development history. Use the [current pipeline](../SF_Bikeshare_Project_Pipeline_Report.md) for the agreed setup.

Prepared 22 November 2026 for the DBA5103 SF bike redistribution project.

**Status: proposed base case, supported by local comparative tests.** This case describes the historical-rate scenario already constructed and tested locally. Final team selection and a complete production builder remain pending. It supplements the frozen V3 observations; it does not replace them. The [comparison report](../SF_Bikeshare_Demand_Estimation_Case_Comparison.md) explains how to use this case alongside Fu Yan's v2 hybrid.

## 1 Purpose and modelling interpretation

Completed trips measure served requests. They omit riders who leave when no bike or dock is available. Case A estimates additional requests during valid empty/full episodes using historical rates measured while the relevant service was available.

Rates vary by station, clock hour, weekday/weekend and rider class. Consequently, an overnight outage follows the historical profile of each affected hour rather than preserving a brief preceding rate throughout the night. The estimates are expected counts under explicit assumptions; unsuccessful customer requests are not directly observed.

Demand estimation supplies inputs to the operations research model. It does not decide redistribution moves, certify truck routes, or calculate observed operator profit.

## 2 Common data scope and units

| Item | Definition |
| --- | --- |
| Cohort | Same 34 San Francisco stations as main V3 |
| Study interval | 9 February 2015 00:00 inclusive to 20 April 2015 00:00 exclusive |
| Training | 9 February-5 April 2015, eight weeks |
| Validation | 6-19 April 2015, two previously explored weeks |
| Output grain | Station-date-hour; 57,120 rows |
| Rider mapping | Subscriber = member; Customer = casual |
| Service sides | Pickups and returns estimated separately |
| Working units | Bikes/docks; seconds or minutes as labelled; downstream distance km, currency USD |
| Time basis | Recorded naive local timestamps; DST ambiguity retained |

The [V3 hourly table](../../output/sf_bikeshare/model_inputs_v3/README.md) provides observed counts and matched availability exposure. The [minute supplement](../../output/sf_bikeshare/demand_estimation_inputs_v3/README.md) provides snapshots and timestamped endpoint events. Boundary journeys retain selected-station endpoints even when the other station is outside the cohort.

An interval uses the preceding snapshot's state only when the state is nonnegative, not both zero, and the next-snapshot gap is positive and at most 90 seconds. The cutoff is an analytical assumption. Missing/offline/long-gap intervals are unknown exposure. Pickup availability requires bikes greater than zero; return availability requires free docks greater than zero.

Trips have minute precision and status observations have seconds. Match an endpoint to the containing preceding interval and preserve timestamp-tie diagnostics. Do not infer exact customer ordering within a recorded minute.

## 3 Rate estimation

Let:

- $i$ denote station, $t$ a dated hour, $h(t)$ its clock hour and $d(t)$ its weekday/weekend type;
- $r$ denote rider class and $s\in\{P,R\}$ pickup or return;
- $N^s_{itr}$ denote recorded events matched to valid, available intervals;
- $A^s_{it}$ denote the corresponding available minutes;
- $\mathcal T_{i,h,d}$ denote training hours in that station/hour/day-type group.

The historical rate, in requests per minute, is:

$$
\widehat{\lambda}^{H,s}_{i,h,d,r}
=\frac{\sum_{u\in\mathcal T_{i,h,d}}N^s_{iur}}
{\sum_{u\in\mathcal T_{i,h,d}}A^s_{iu}}.
$$

The implementation used events per second and exposure seconds, which is algebraically equivalent. The numerator and denominator must refer to the same valid available intervals. A simple average of daily rates would give unequal exposure inappropriate equal weight; the ratio of sums performs the required exposure weighting.

The local Case A trial uses a positive denominator as its support condition. If that denominator is zero, pool the same station and clock hour across day types. If the pooled denominator is also zero, preserve an unresolved rate and flag the affected estimate. A zero event numerator with positive exposure is a valid zero rate, not a missing-rate condition.

Case B specifies a stronger 60-minute historical support requirement. This does not change the profiles compared here: every primary group in main V3 has at least **840 training available minutes for pickups** and **780 for returns**. Other subsets need their own support audit.

## 4 Episode estimation and hourly allocation

An episode $e$ is a continuous sequence of valid empty intervals for pickups or full intervals for returns. Invalid intervals or long gaps break episodes. Let $i(e)$ be its station, $w^s_{et}$ its outage minutes intersecting dated hour $t$, and $S^s_{er}$ its recorded served events, restricted to the study window.

Expected arrivals in the episode's hourly segment are:

$$
E^{A,s}_{etr}=
\widehat{\lambda}^{H,s}_{i(e),h(t),d(t),r}\,w^s_{et}.
$$

Sum expected arrivals across the episode before applying the served-event correction:

$$
E^{A,s}_{er}=\sum_t E^{A,s}_{etr},
\qquad
M^{A,s}_{er}=\max\{0,E^{A,s}_{er}-S^s_{er}\}.
$$

This subtracts service already recorded during nominal empty/full intervals once per episode. Such service can occur between snapshots; it must not be added a second time as unmet demand.

Allocate missed demand in proportion to expected arrivals:

$$
M^{A,s}_{etr}=
\begin{cases}
M^{A,s}_{er}\,E^{A,s}_{etr}/E^{A,s}_{er}, & E^{A,s}_{er}>0,\\
0, & E^{A,s}_{er}=0.
\end{cases}
$$

Finally, with $O^s_{itr}$ the full observed count in the station-hour:

$$
\widehat D^{A,s}_{itr}
=O^s_{itr}+\sum_{e:i(e)=i}M^{A,s}_{etr}.
$$

The subtraction is at episode level; it is not independently clipped and subtracted again in every hour. This convention is shared with the audited Fu Yan estimator and matters for cross-hour episodes.

## 5 Assumptions

1. Training rates measured during available periods are a useful approximation for arrival rates during outages in comparable station/hour/day-type groups.
2. Expected arrival rates are constant within each clock-hour profile but may change at hour/day-type boundaries.
3. Additional demand is estimated only over valid observed outage exposure. Unknown exposure does not establish zero missed demand.
4. The reconstruction does not explicitly model waiting, walking to another station, or changed future customer behaviour.
5. Rates are estimated separately for member/casual and pickup/return. This does not construct a joint counterfactual journey linking each additional pickup to a later return.

Historical averaging may understate unusually busy outage days. Conversely, short preceding windows can be noisy. The validation and sensitivity comparisons assess that tradeoff; neither estimator observes the missing customers.

## 6 Main-case numerical results

| Quantity | Observed | Estimated | Added |
| --- | ---: | ---: | ---: |
| Pickups | 62,243 | 64,573.775 | 2,330.775 |
| Returns | 62,326 | 63,014.136 | 688.136 |

The same 3,799 outage episodes are used in both cases: 2,397 empty episodes and 1,402 full-dock episodes. A station-64 empty episode lasting 497 minutes from 1 March 23:15 to 2 March 07:32 adds approximately **1.44 pickups** in Case A. The original unlimited predecessor estimate added approximately 231.93; the v2 hybrid adds approximately 15.09. These are scenario differences, not observed missed-customer totals.

The 34 missing-exposure station-hours associated with the recorded 8 March DST gap retain observed counts and explicit quality flags. They are not complete unconstrained-demand estimates. All daily midnight stocks used for initialization remain usable in this main case.

## 7 Validation evidence

The independent comparison uses training-only profiles and the same hidden targets for both cases. Every target requires full valid availability. For Case B, the preceding window ends before the hidden target and falls back to historical rates when its available exposure is insufficient.

| Target and class | Windows | Case A MAE | Case B MAE | Case A RMSE | Case B RMSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| Next 1 hour, member pickups | 10,867 | 0.544 | 0.926 | 0.954 | 1.907 |
| Next 1 hour, casual pickups | 10,867 | 0.198 | 0.211 | 0.485 | 0.777 |
| Next 1 hour, member returns | 11,092 | 0.556 | 0.938 | 1.011 | 1.918 |
| Next 1 hour, casual returns | 11,092 | 0.190 | 0.212 | 0.473 | 0.788 |
| Next 3 hours, member pickups | 10,178 | 0.958 | 1.267 | 1.545 | 2.187 |
| Next 3 hours, casual pickups | 10,178 | 0.441 | 0.477 | 0.841 | 1.033 |
| Next 3 hours, member returns | 10,672 | 1.005 | 1.331 | 1.760 | 2.377 |
| Next 3 hours, casual returns | 10,672 | 0.432 | 0.467 | 0.837 | 1.032 |

Errors are trips per target window. The three-hour Case B predictor actually switches after hour one; it does not carry the preceding rate through all three hours.

Case A has lower MAE/RMSE in these longer-horizon comparisons. The ten-minute targets immediately before long outages give mixed results: Case B has small advantages for casual pickups and member-return MAE, and less negative bias in all four categories. Both cases underpredict those selected busy windows. See the [full matched validation table](../../output/sf_bikeshare/demand_case_comparison_2026-11-22/matched_validation.csv).

The validation period has been explored repeatedly, overlapping targets are correlated, and available periods may differ from actual outage periods. These results support a provisional scenario choice rather than proof of true unmet-demand accuracy. Freeze choices before further evaluation.

## 8 Model integration and readiness

The full [historical CSV and compressed download](../../output/sf_bikeshare/demand_estimation_cases_2026-11-22/README.md) are published as provisional output snapshots. They preserve the audited values and can be selected as the demand input for a local model run.

The Case A trial has the same 57,120-row, 31-column interface as the supplied demand files. Required fields include estimated_subscriber_pickups, estimated_customer_pickups and estimated_total_returns. All 70 dates pass the existing model loader.

Four illustrative daily checks compare no rebalancing, equal occupancy and optimized moves. Case A feasible additional allocated contribution is USD18.23, USD2.97, USD0 and USD42.56 on 6, 10, 11 and 15 April respectively. The first optimization reached its ten-second cap at a 3.18% gap; the others met the 1% relative-gap tolerance. These use provisional costs and unverified routes, not a final economic evaluation. [Parameters and bounds](../../output/sf_bikeshare/demand_case_comparison_2026-11-22/README.md).

To adopt Case A:

1. Implement this option in the complete shared demand builder and independently read back its exports.
2. Preserve the rate table, matched exposure, episode audit, chronological validation and quality flags.
3. Keep observed V3 files frozen; publish estimated-demand inputs as a separate, versioned product.
4. Agree cost/model settings and rerun the required policy evaluation, routing checks and robustness cases.

The local trial reused Fu Yan's audited episode table; a self-contained production command is not yet part of the shared repository. The downloadable demand output and supporting evidence do not complete the final producer/code handoff.

## 9 Suggested Section 3.4 wording

> We constructed an availability-adjusted historical-demand scenario from the first eight weeks of the selected period. For each station, clock hour, weekday/weekend type and rider class, the rate was the ratio of recorded events during valid available exposure to the corresponding exposure duration. Pickup and return rates were estimated separately. During valid empty/full episodes, these rates were applied to the outage duration in each affected hour, allowing the rate to change across hour and day-type boundaries. Recorded service during an episode was subtracted once from its expected arrivals, with nonnegative residual missed demand allocated to hourly records in proportion to expected arrivals. Observed trips plus allocated missed requests formed the station-hour demand input.
>
> Reconstruction checks used fully available windows in the later two weeks, with hidden counts compared with predictions. Historical rates had lower errors than the hybrid in the one- and three-hour comparisons, while short pre-outage results were mixed. Actual unmet demand remained unobserved, and both methods underpredicted the selected pre-outage windows. We therefore treat the estimates as demand scenarios and compare policy results under alternative demand assumptions.

Use the wording with the matching case label and actual experiment scope. Final production-code and evaluation statements must reflect the completed handoff.

## 10 Course and research references

- DBA5103 Lecture 6, Network, pp. 17-18: flow balance and capacity constraints. Both cases supply demand parameters to that framework.
- DBA5103 Lecture 7, IP, p. 4: mixed integer and continuous variables. Expected service/inventory can be continuous while relocation moves are integer, as explicitly specified in the prototype.
- DBA5103 Lecture 4, Duality and Sensitivity, pp. 25-26: uncertain data motivate what-if analysis. Alternative demand inputs require re-solving and comparing the model.
- [O'Mahony and Shmoys (2015), Data Analysis and Optimization for (Citi)Bike Sharing](https://cdn.aaai.org/ojs/9245/9245-13-12773-1-2-20201228.pdf), Section 3, motivates availability-conditioned historical demand inference.
- [Freund et al., Data-driven rebalancing methods for bike-share systems](https://people.orie.cornell.edu/shane/pubs/BSOvernight.pdf), author-hosted manuscript, Section 3, uses time-varying pickup/return rates.

The lecture PDFs are locally supplied course materials and are not redistributed here. The exact exposure-weighted, rider-split estimator is this project's adaptation; the sources do not establish Bay Area Bike Share's actual 2015 algorithm or certify this estimator's accuracy.
