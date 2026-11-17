# What the subset does and does not represent

Prepared 17 November 2026. Current candidate is proposed, not a recorded team approval. No source records or candidate observations were removed by this audit.

## Clear objective and problem statement

**Objective:** Maximize the additional operating contribution created by bicycle redistribution relative to a no-rebalancing baseline.

**Problem statement:** Given estimated pickup requests and destination/return requirements by station and time, choose how many bikes to move, between which stations and when, to maximize additional trip contribution minus additional rebalancing cost, while respecting bike conservation, station inventory/dock limits, transfer timing and truck resources.

Trip contribution is the incremental trip revenue after any trip-related variable costs included in the model. Membership receipts should not automatically be treated as incremental revenue on every extra trip. Keep bicycle/dock capital costs outside the agreed operational scope. If contribution values remain unsupported, report service improvement under a budget as the main operational result and evaluate financial values as scenarios.

The pickup-return gap helps explain directional pressure. Required transfers also depend on opening inventory, dock limits, trip timing, in-transit bikes, demand variability and the chosen service level; transfers need not equal aggregate net flow exactly.

## Demand estimation is a separate step

1. Aggregate completed departures and arrivals at their respective endpoint times: these are served requests, not total attempted demand.
2. From bounded status intervals, calculate valid observed time and time with bikes/docks available. Missing observations and both-zero availability states are not assumed to mean no demand.
3. Estimate an attempted-request rate from comparable available periods. Match counted endpoint events to the same valid time exposure; pool station/hour/day-type observations before division where sparse. Estimate requests during observed empty/full periods under the stated arrival-process assumptions.
4. Construct training-derived pickup/return or OD scenarios, with uncertainty, and validate before passing them to the optimizer.

For a fully observed 60-minute slot, the illustrative 12 pickups in 40 available minutes implies a rate of 0.3/minute and an expected 18 requests under constant intensity. Six additional requests are an estimate, not an observed customer count. A fully empty slot gives no local rate estimate: use a documented pooled fallback, not zero or division by zero. Unknown status time requires a separate missingness assumption.

Walking to another station, changing destinations or abandoning a journey changes the interpretation of attempted demand. Its bias is not guaranteed to be small or always in one direction. Link accepted pickups to later returns/in-transit stocks so a counterfactual policy does not create bikes by replaying fixed historical returns after rejecting different rentals.

Methodological support: Liu and Pelechrinis (2021), [Excess demand prediction for bike sharing systems](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0252894). The paper establishes the observed-versus-excess-demand distinction and develops a different estimator; the team's simple exposure estimator has not been validated by citing it.

## How the present candidate was produced

- Source: the four supplied local CSVs associated with [Ben Hamner's SF Bay Area Bike Share dataset on Kaggle](https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share). Original files are unchanged and full hash/audit manifests already exist.
- Full audit/ETL: 669,959 valid trips, 71,984,434 minute-status snapshots, 70 station records and 3,665 weather location-days. Validate station IDs/timestamps, keys and gaps. Exposure carries a valid preceding state only across a positive gap of at most 90 seconds and splits at hour boundaries. Longer gaps are unknown.
- Scope: retain 34 San Francisco stations installed by 29 August 2013. There are 35 listed SF stations overall; the installation rule excludes the later-added one from this fixed cohort. The other cities are outside the proposed pilot, not declared irrelevant to the entire Bay Area.
- Dates: [9 February 2015, 20 April 2015), equivalent to 9 February-19 April inclusive. These are 10 complete Monday-Sunday calendar weeks.
- Aggregation: trips become station-hour departure/arrival counts. Status becomes observed/empty/full/low-inventory exposure and mean availability. Weather joins through the documented city/date proxy. Dense eligible hours include zero completed trips. These are recorded local clock hours; daylight-saving ambiguity in the source is unresolved.
- Splits: eight training weeks [9 February, 6 April), two exploratory validation weeks [6 April, 20 April). Four training weeks from 9 March are an alternative, not the content of the entire existing export.
- Boundary flows: endpoint counts include journeys with the other endpoint outside the cohort. The model needs explicit boundary accounting or a larger station set; dropping those trips silently changes the problem.
- Output: 57,120 station-hour rows (4.7228% of the full 1,209,456-row hourly panel), 247,473 bytes. Raw CSVs total 2,070,348,941 bytes. Smaller scope, lost raw detail, aggregation and compression all contribute to the file reduction. Relevant distinct journeys number 63,974, not the sum of departure and arrival events.

This is geographic/time scoping and aggregation. It is not evidence-based removal of statistically redundant periods. The original candidate was selected as a manageable demonstration window; it was not chosen by a comprehensive search for the most representative window.

## New comparisons: same stations, different periods

For a fair descriptive comparison, use the same 34 SF stations throughout. The broad comparison calendar contains 104 complete weeks, [2 September 2013, 31 August 2015). The reference excludes the candidate's 10 weeks, leaving 94 weeks/658 days. This avoids comparing SF usage with unrelated city usage or including the candidate on both sides. It still combines seasons and operational changes and is not a causal or statistical equivalence test.

| Measure | Other 94 weeks | Candidate 10 weeks |
| --- | ---: | ---: |
| Weekday completed departures/day | 984.83 | 1,115.58 |
| Weekend completed departures/day | 343.98 | 323.20 |
| Empty-time exposure, valid observed time | 1.1605% | 1.8529% |
| Full-time exposure, valid observed time | 0.7244% | 0.8562% |
| Status coverage over recorded clock grid | 98.8662% | 99.9013% |
| Measurable-rain days | 70 of 658 | 7 of 70 |
| Daily minimum/maximum departures | 58 / 1,354 | 162 / 1,264 |
| Station-hour 99th percentile / maximum departures | 9 / 52 | 10 / 44 |
| Daily IQR flags | 46 of 658 | 1 of 70 |

Both periods' weekday morning and afternoon peaks occur at 08:00 and 17:00. Pearson correlation of their 24 normalized hourly weekday profiles is 0.9965; weekend-profile correlation is 0.9916. These describe shape agreement, not the proportion of individual records that are identical or a confidence statement.

The candidate's weekday level is about 13.3% higher and weekend level about 6.0% lower. Empty exposure is about 0.69 percentage points higher. Station activity ranks are similar (Spearman 0.9743), but empty/full-pressure ranks are less stable (0.7791), with only six common stations in the two top-10 lists. Morning net-flow signs agree for 32 of 34 stations and afternoon signs for 33. Broad peaks therefore repeat better than exact station priorities or operating severity.

The four-week training variant has weekday-profile correlation 0.9969 but only four measured-rain days. The eight-week training variant has five measured-rain days. The earlier forecast-window comparison found similar average completed-trip errors for four and eight weeks across three validation starts; that is not a test of equivalence for latent demand, financial value or routes.

## Outliers and what was retained

Flag daily departure totals separately for weekdays/weekends using reference quartiles and Tukey fences: below Q1-1.5*IQR or above Q3+1.5*IQR. Reference weekday fences are 499.625 to 1,546.625; weekend fences are 135 to 543. The candidate's flagged day is 16 February 2015, with 476 completed departures. All flagged days remain in the data.

This screen is descriptive and is not adjusted for seasonality, weather, holidays or trends. It identifies days to review, not erroneous records. It also does not capture every station-level or within-hour extreme. Full-period extremes omitted by the candidate's date scope should be used for robustness scenarios where relevant.

Among the 63,974 relevant candidate journeys, 13 reported durations exceed 24 hours (maximum 350,903 seconds) and none has the existing over-60-second duration-clock mismatch flag. Long rides remain in the valid-trip source with review flags and their endpoint events contribute to the panel. The candidate hourly file does not contain individual trip durations. Audit code and separate results retain these diagnostics.

## Optimization versus machine learning

The main deliverable is a decision model, not a predictive-ML benchmark. Empirical station/hour/day-type means and a transparent censored-demand method can supply inputs; advanced ML is optional. Optimization instance size depends on stations, periods, feasible transfer/routing arcs, vehicles and scenarios, rather than the number of raw minute observations used to estimate inputs.

More historical data can improve input estimates and scenario coverage without making the final optimization instance larger. A compact input table can be derived from the full history. Conversely, a small dataset can omit rare conditions that materially affect feasibility and service, even without ML. Use scope and validation quality, not the absence of ML, to justify the subset.

Recommended next comparison: hold the 34 stations fixed, compare four- and eight-week training inputs, then evaluate identical policies on later common days plus selected rain/extreme-day scenarios. Report per-day/served-request metrics when horizons differ. Maintain a later policy-evaluation period; today's descriptive checks already examine the existing validation data, so it is exploratory rather than sealed.

## Files and reproduction

- Code: `sf_bikeshare/validate_subset_patterns.py` and `sf_bikeshare/make_subset_poster_portrait.py`.
- Data: `pattern_period_summary.csv`, `hourly_pattern_comparison.csv`, `profile_similarity.csv`, `station_pattern_stability.csv`, `daily_pattern_and_outlier_audit.csv`, `flagged_daily_extremes.csv`, `daily_outlier_thresholds.csv`, `pattern_audit_manifest.json` in this directory.
- Poster PNG: `output/sf_bikeshare/whatsapp/SF_Bikeshare_Subset_Poster.png`.
- The current shared poster is the 1800 x 3200 portrait PNG. Earlier poster PDFs and draft group messages stay local.

The database was read-only. Assertions check station-hour uniqueness and expected complete calendar rows. Poster layout assertions and rendered PDF inspection accompany the output. No optimization, latent-demand fitting, EDA rewrite or external message sending is performed by these scripts.
