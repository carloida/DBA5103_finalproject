# Robustness datasets: research and read-only feasibility audit

> Historical research note. Carlo subsequently authorized preparing and publishing the five proposed cases on 18 November. The [robustness packages](../output/sf_bikeshare/robustness_testing/README.md) are now built and validated; the [pipeline report](SF_Bikeshare_Project_Pipeline_Report.md) describes the current status. Claims below that no extra cases/road matrix were created refer to the earlier research phase. No optimization experiment has been run.

**Prepared for Carlo | 18 November 2026 | Proposal awaiting decision**

## Recommendation

Prepare **five additional cases alongside the existing SF pilot**, giving **six total cases: two cities times three calendar windows**. Keep all cases hourly and 10 weeks long, with the same V3 feature definitions, metric units and eight-week training/two-week evaluation structure.

This is a practical project-scale recommendation, not a universal rule or a statistical guarantee. The source has a useful second-city case in San Jose, but it has fewer stations and much lower trip volume. Matching its natural row count to SF by extending its dates would change the experiment.

Only research, source queries and this feasibility note have been prepared. No new modeling dataset, demand estimate, road matrix, optimized plan or GitHub upload was created for the proposed cases. The existing V3 dataset is unchanged. The shared Google Doc was not edited.

## 1. What the research supports

**Choose experiments around a question, rather than a target file count.** Bartz-Beielstein et al.'s optimization-benchmarking survey links instance selection, experiment size, tuning, performance measures and computational resources to the study goal. It discusses factorial designs and warns that conclusions depend on the benchmark suite. I therefore recommend the small crossed city-by-period design below; the number six is our design choice. [Benchmarking in Optimization: Best Practice and Open Issues, Sections 3 and 7](https://arxiv.org/html/2007.03488v2).

**Use consistent formats and include variation in difficulty.** Kendall et al. recommend standard benchmark representations, validation procedures and instances spanning different sizes/complexity. Identical row totals are not their target. For this project, preserve the same feature meanings while allowing natural differences in stations, demand and network size. [Good Laboratory Practice for Optimization Research, Recommendations 6, 8 and 11](https://www.graham-kendall.com/papers/ketal2016.pdf).

**Preserve temporal order in demand estimation.** Forecasting cross-validation uses only observations preceding the forecasted period. Apply this to Fu Yan's estimator and select policy/estimator settings before evaluating later requests. Re-estimating local demand under a fixed recipe is allowed; retuning to favorable evaluation outcomes changes the claim. [Forecasting: Principles and Practice, Section 5.10](https://otexts.com/fpp3/toolbox.html#time-series-cross-validation).

**Evaluate implementation, not just optimization objectives.** A directly relevant bike-sharing study distinguishes training demand, test demand scenarios and repeated simulation runs. Its protocol evaluates the operational implementation of plans, which can differ from their optimization prediction. These are different counts: a historical city/window case is not a simulation replication. [Neumann-Saavedra, Mattfeld and Hewitt (2021), Section 6](https://doi.org/10.1016/j.tra.2021.06.003).

These sources support the protocol, not an assertion that five or six cases proves general validity. More days, more diverse operating contexts and uncertainty analysis can strengthen evidence; duplicating similar windows or repeatedly solving one unchanged deterministic instance does not supply equivalent new information.

## 2. What the original database can support

| City | Listed stations | Natural rows in 10 complete hourly weeks, if all stations were installed before the window |
| --- | ---: | ---: |
| San Francisco | 35; existing fixed pilot uses 34 | 57,120 for the 34-station pilot |
| San Jose | 16 | 26,880 |
| Mountain View | 7 | 11,760 |
| Redwood City | 7 | 11,760 |
| Palo Alto | 5 | 8,400 |

All source stations have coordinates and positive listed dock counts. SF's existing 34-station cohort is retained for consistency. San Jose's 16 stations were all installed by 9 April 2014, before the earliest recommended window. Applying SF's original August 2013 cutoff mechanically would retain only 14 San Jose stations; that restriction is not necessary for the proposed dates.

Earlier windows require installation checks. For example, including all 16 San Jose stations in the 10-week window starting 10 March 2014 produces only 26,160 eligible station-hours because some stations were not yet installed. The recommended windows avoid this partial-grid issue.

The original trip, status, station and city-weather relationships can support the same observed-data transformations in both recommended cities. Source availability is established here; exact output-schema equivalence remains a build acceptance check once approved.

## 3. Recommended cases: existing pilot plus five additions

Dates are inclusive below. Each window contains 70 recorded-calendar days at hourly resolution. Status coverage is valid short-gap observed seconds divided by the complete station-hour grid, following the existing V2/V3 rule. It is not a demand-service rate.

| Case | City | Dates | Stations | Station-hour rows | Observed pickups | Status coverage | Fresh midnight stocks / expected |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| D0 - existing V3 reference | San Francisco | 9 Feb-19 Apr 2015 | 34 | 57,120 | 62,243 | 99.901% | 2,380 / 2,380 |
| R1 - other location, same dates | San Jose | 9 Feb-19 Apr 2015 | 16 | 26,880 | 3,436 | 99.901% | 1,120 / 1,120 |
| R2 - other period, same location | San Francisco | 2 Jun-10 Aug 2014 | 34 | 57,120 | 60,741 | 99.835% | 2,376 / 2,380 |
| R3 - other city in that period | San Jose | 2 Jun-10 Aug 2014 | 16 | 26,880 | 4,551 | 99.967% | 1,120 / 1,120 |
| R4 - later period, same location | San Francisco | 20 Apr-28 Jun 2015 | 34 | 57,120 | 63,164 | 99.405% | 2,376 / 2,380 |
| R5 - other city in later period | San Jose | 20 Apr-28 Jun 2015 | 16 | 26,880 | 3,667 | 99.546% | 1,120 / 1,120 |

The three calendar windows do not overlap. Matching windows across the two cities deliberately share dates, so cases and city-days are not statistically independent. The selected dates and cohorts were screened for source availability and coverage before any policy results exist; they were not chosen for favorable optimization gains.

There are no missing city-weather fields in these proposed panels. Measurable-rain days are limited: respectively 7/5 for SF/San Jose in the existing window, 1/1 in summer 2014 and 3/4 in the later 2015 window. The design does not establish detailed station-specific rain effects.

### Opening-stock and capacity issues requiring a rule

The two proposed SF windows each contain four midnight snapshots that fail the existing valid/latest/90-second-age rule. None falls in summer 2014's last two weeks; one falls in the later 2015 window's last two weeks. Proposed San Jose windows have fresh stocks throughout. Do not silently fill those missing SF initial states or change the freshness threshold for one city only.

Before model evaluation, agree a common rule: a documented initial-stock scenario, or exclusion of an affected complete evaluation day for all compared policies. If exclusions are used, report the actual number of evaluated days and normalize appropriately. Do not choose the rule after seeing policy gains.

Fresh openings with effective capacity different from listed docks number 32/17 in SF/San Jose summer 2014, 67/31 in the existing window and 93/53 in the later window. No accepted opening bike count exceeds listed dock capacity. As in V3, these discrepancies require an explicit effective-versus-physical capacity treatment rather than invented dock overrides.

## 4. Should row counts be matched?

For a dense hourly panel:

`rows = number_of_stations * number_of_days * 24`

SF therefore has `34 * 70 * 24 = 57,120` rows. San Jose has `16 * 70 * 24 = 26,880` rows. Equal row counts across full cities are not possible under the same duration and resolution because the station counts differ.

One audited row-matching example is San Jose for **8 September 2014-1 February 2015**, covering 21 weeks: **56,448 rows**, only about 1.18% fewer than SF's pilot, with 99.364% valid status coverage. However, this changes the season span, training-history length and possible evaluation design. It is therefore a separate duration experiment, not my preferred way to make comparable city cases.

Do not duplicate observations, invent stations, merge geographically separated cities into one artificial operating network or change aggregation merely to reach 57,120 rows. Legitimate zero-trip rows in the real station-hour grid should still be retained.

If equal size is essential, alternatives are:

- Use several additional 34-station SF windows of 10 weeks each. This matches 57,120 rows but evaluates time variation rather than another location.
- Define a justified 16-station SF subnetwork and compare it with 16 San Jose stations over common 10-week windows. Both would have 26,880 rows, but the SF boundary and spatial scope change and require explicit selection rules.
- Retain natural city sizes and report performance by city/window, with normalized measures and problem dimensions. **This is the recommended approach.**

For daily optimization, the six recommended cases provide the same number of possible daily instances. Dense ordered transfer variables per 24-hour instance would be 26,928 for 34 SF stations versus 5,760 for 16 San Jose stations, before pruning, timing or scenario decisions. Equal historical row counts would not equalize this computational size.

## 5. How many cases and runs?

The recommendation is **six total city-window cases, including the existing pilot**, not five new data providers. The five additions would come from the same original database and do not represent independent systems collected by different operators.

With eight weeks for estimation and two weeks for evaluation in each case, there are up to 14 evaluation city-days per case. Across six cases that is up to 84 city-days and **252 policy-day evaluations** for no moves, a simple rule and optimization, before initial-stock exclusions, routing variants, scenarios or repetitions. The paired cities share 42 calendar evaluation days. These figures are workload estimates, not a claim of 84 independent observations or 252 optimizer solves.

For stochastic demand simulations or randomized heuristics, use common sampled requests/seeds across competing policies and estimate how many repetitions are needed from a preliminary variability study. Five cases is not a substitute for replication, and an arbitrary fixed repetition count is not a guarantee of precision. For deterministic solved-to-optimality instances, repeating the identical solve mainly measures computation variation rather than adding new demand evidence.

Keep initial comparisons modest. Agree solver time limits, gaps, resources and an attainable experiment budget, then add selected adverse cost/demand combinations. The two-city by three-period design already enables a structured comparison of location and period; do not multiply every parameter combination before runtime is known.

## 6. Same-feature contract if the build is approved

The working `station_hour_observed` table should retain the **same 51 V3 column names, order, SQL types, units and definitions**. Related tables should retain their existing schemas, although their natural row counts differ.

| Feature family | Required treatment for each case |
| --- | --- |
| Calendar and split | Same meanings, eight training/two evaluation weeks; recalculate date boundaries and relevant DST flags, not fixed SF dates |
| Rider flows and net outflow | Recount Subscriber/Customer endpoints by the correct departure/arrival hour; retain real zero-count hours |
| Availability and matched numerators | Recompute bounded valid exposure and event matches using the same <=90-second rules; preserve NULLs and quality flags |
| Opening stocks and capacity | Re-extract preceding snapshots, ages, validity and effective/static-capacity diagnostics; use the same review rules |
| OD, boundary and transit | Rebuild cohort membership and temporal boundaries for each case; retain duration-review flags and bike-conservation inputs |
| Coordinates and distance | Use actual station coordinates; new San Jose matrix required. Keep metric units and consistent provider/profile/provenance. A current driving estimate remains a proxy for every historical case |
| Weather | Use the documented city-specific weather proxy; convert to degrees Celsius, km/h and mm; do not copy SF weather to San Jose |
| Economic/vehicle tables | Same column meanings, but review price-year applicability, local cost assumptions, truck/depot rules and plan mix. Do not copy fixed 2015 monthly parameter names into a 2014 case as if they were period-matched evidence |
| Metadata and validation | Identify case/cohort/dates separately in manifests. Enforce unique keys, dense expected grids, endpoint/OD reconciliations, snapshot rules, metric conversion and file hashes |

For economic comparisons, the team may choose a common explicit price-year scenario across historical demand cases or research period-specific costs. Either choice must be disclosed; dated 2015 tariffs and SF operating proxies are not automatically verified summer-2014 San Jose inputs. Jason's allocated-revenue scenarios remain assumptions, not measured incremental payments.

## 7. Build work after Carlo's decision

1. Parameterize the current SF-specific enrichment script by city/cohort, dates, split and output directory. Preserve V3 as the reference release.
2. Implement the same-feature contract and agreed treatment of unusable opening stocks, capacity flags, DST and long trips.
3. Produce each scoped observed-data package and a schema/quality comparison report. Fetch/cache the new San Jose road matrix only when proceeding.
4. Have Fu Yan fit demand from each case's preceding training observations under the same agreed estimator recipe; do not train on its evaluation period. These remain retrospective cases because broader EDA has already examined the source history.
5. Run common policies with identical initial states, information and resources within each instance. Future realized requests cannot be used by the operational policy; a perfect-information solve must be labeled a benchmark.
6. Evaluate service, costs, movement, route feasibility, solver outcomes and uncertainty. San Jose's lower demand may legitimately make no redistribution attractive under fixed activation costs; do not discard such a result.
7. Publish only after the packages and experiment definitions are reviewed. No GitHub or shared-Doc changes are made by this research note.

## Audit provenance

The local original DuckDB database was opened read-only. Summary queries used the existing station-hour exposure table, installation dates and preceding status snapshots. A temporary local audit script and JSON-lines summary are under `tmp/`; no source records were modified and no candidate station-hour packages were exported. These checks establish candidate availability/quality, not a complete feature-level build validation or evidence of policy effectiveness.
