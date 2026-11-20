# Figure plan aligned with Carlo's Section 3 draft

**19 November 2026 | Planning notes, not completed EDA results**

The [current draft](../SF_Bikeshare_Consolidated_Data_Preparation_Report.md) follows this sequence: source and scope, engineered inputs, quality/limitations, then Fu Yan's demand estimation. The figures should follow that same sequence. They should describe observed data rather than anticipate optimization results.

## Main-paper recommendation

Use **one compact two-panel figure**, provisionally called **Figure 3.1: Observed usage and station availability in the curated SF dataset**. Coordinate its size with Fu Yan because Section 3 has a shared two-page allowance. A figure does not create additional pages beyond that allowance.

| Draft location | Narrative purpose | Visual and placement |
| --- | --- | --- |
| 3.1 Data source and study scope | Define the 34 stations, ten weeks, row count and chronological split | Keep these facts in text; a separate map or V1-V3 progression diagram is unnecessary in the main section. |
| 3.2 Data preparation and feature engineering | Explain how raw records become hourly flows and exposure | Retain the existing feature table. Place the planned two-panel figure after the unit/measurement paragraph, before 3.3. |
| Figure 3.1A | Show temporal variation in completed usage | Average hourly pickups and returns across the network, distinguishing weekdays/weekends. Use colour for pickup/return and solid/dashed lines for day type. If the four lines are difficult to read at the final size, show weekdays here and move the weekend comparison to the appendix. |
| Figure 3.1B | Show which stations experience constrained availability | Paired horizontal bars for empty/full percentages at eight stations with the highest combined empty/full exposure. State the selection rule in the caption and show all 34 stations in supporting material. |
| 3.3 Validation and handoff | Explain quality flags and what the observations cannot establish | Retain the existing QA counts and limitations in text. Connect constrained availability to the distinction between completed trips and attempted requests. |
| 3.4 Demand estimation | Explain how Fu Yan estimates unobserved requests | Leave estimator/validation plots to Fu Yan once that method is implemented. Do not invent an observed-versus-estimated comparison now. |

The resulting argument is: **the curated observations describe when trips occur and where availability is constrained; these observations are inputs to demand estimation, not direct measurements of all requests.** Neither panel establishes the benefit of redistribution.

## Exact definitions for the planned figure

**Scope:** main V3 only, 34 stations, 9 February-19 April 2015 inclusive. Use the whole ten-week window for descriptive plots, label that scope and retain the existing statement that validation dates have been examined. Estimator calibration and policy-setting choices must use training data. These figures do not establish a sealed test.

**Panel A:** for each date and hour, sum `departures` and `arrivals` across the 34 stations; then average those network totals over dates of the same day type. Retain zero-trip hours. The y-axis is **mean completed trips per network-hour**, not a station-average rate mislabeled as a network total. Pickups and returns are separate endpoint series and must not be added to count unique journeys. The x-axis uses recorded local hour.

**Panel B:** for each station, calculate:

```text
empty percentage = 100 * sum(empty_seconds) / sum(observed_seconds)
full percentage  = 100 * sum(full_seconds) / sum(observed_seconds)
ranking score    = 100 * [sum(empty_seconds) + sum(full_seconds)]
                        / sum(observed_seconds)
```

Use valid observed exposure only; retain NULL when the denominator is absent. Rank the top eight by the combined score, with station ID as a deterministic tie-breaker. Use the same station order for both bars. Label the selection as highest observed exposure, not highest lost demand or proven relocation priority. Check and report coverage for selected stations in the supporting table; the short-gap rule and DST limitation remain applicable.

## Suggested linking text and caption

These are templates to finalize after creating and inspecting the graphs; no new numerical finding is claimed here.

**Lead-in at the end of 3.2:**

> Figure 3.1 summarizes the temporal distribution of completed trips and station-level empty/full exposure derived from the curated observations.

**Caption:**

> Figure 3.1. Observed usage and availability, 34 SF stations, 9 February-19 April 2015. (A) Mean hourly network pickups and returns by day type. (B) Empty/full percentages at the eight stations with the highest combined exposure, calculated from summed valid observed seconds. Trips represent completed activity; availability exposure does not directly count unsuccessful requests. Hours follow the recorded local-clock grid.

If Panel A is restricted to weekdays, update the caption accordingly. Describe peak times, station differences and magnitudes only after verifying the final V3 calculations. Remove redundant prose if needed to preserve space for Fu Yan.

**Bridge from 3.3 to 3.4:**

> Completed trips describe served requests, while empty/full exposure identifies constrained availability. Estimating the requests that were not served therefore requires the separate demand-estimation method described next.

This refines the existing final paragraph of 3.3 rather than adding a second explanation of the same distinction.

## Supporting figures and ownership

| Supporting visual | Connection to the draft | Placement |
| --- | --- | --- |
| Weekday station-hour net-flow heatmap, all 34 stations | Supports the `pickups - returns` feature; use a colour scale centred at zero | EDA appendix/supporting material; values are mean net departures per station-hour, not required moves |
| All-station empty/full exposure chart and coverage table | Documents the full population behind Panel B's selected stations | EDA appendix/supporting material |
| Daily opening-fill distributions | Supports opening inventory and capacity inputs; use only accepted opening snapshots and flag effective/static discrepancies | EDA appendix/supporting material; listed docks are an explicitly stated denominator |
| Station-by-date coverage heatmap | Supports missingness and the short-gap/DST discussion | Data-quality appendix/supporting material; coverage is relative to the nominal recorded-clock grid |
| Station map | Geographic context if space elsewhere permits | Supporting material, not an additional main-section requirement |
| Comparable descriptive profiles across robustness cases | Describes input differences across cities/periods | Supporting material for Section 7; model-performance comparisons remain Joohee/Hong Jin/Fu Yan's work |

Keep revenue plots, estimated savings, optimized routes and policy-performance graphs out of Carlo's current data contribution. Jason's coefficients are assumptions and no policy results exist yet. Regenerate any reused full-system figure for the stated V3 scope rather than presenting a broader source plot as the curated subset.
