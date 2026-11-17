# SF Bike Share: initial data preparation report

**Prepared by Carlo | 17 November 2026 | Draft for team review**

## Project objective

Based on the problem statement discussed at our meeting and recorded by Joohee, our project will study how to move bikes between stations to improve service and operating results.

The main question is:

> Given estimated demand at each station and time, how many bikes should we move, where should they go, and when should we move them to earn the highest additional operating contribution, within station and truck limits?

Additional operating contribution means the income from extra trips served, after any trip-related costs included in the model, minus the extra cost of redistribution. We will compare this with a clearly defined no-rebalancing baseline. Bicycle and dock purchase costs are outside the agreed scope.

This report covers the data preparation and checks completed so far. The subset, demand method and cost assumptions still need the team's approval. No optimized plan or financial improvement has been calculated yet.

## Original data and proposed subset

The source is [Ben Hamner's SF Bay Area Bike Share dataset on Kaggle](https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share), using the four supplied local files: trips, stations, station status and weather. The trip records cover 29 August 2013 to 31 August 2015. The largest file records bike and dock availability approximately every minute.

I audited the full files before extracting a smaller working dataset. The proposed pilot keeps **34 San Francisco stations installed by 29 August 2013** and **10 complete weeks from 9 February to 19 April 2015**. A fixed station group makes comparisons easier because stations are not being added midway through our selected period.

| Measure | Full dataset | Proposed subset |
| --- | ---: | ---: |
| Stations | 70 across 5 cities | 34 in San Francisco |
| Hourly table rows | 1,209,456 | 57,120, or 4.72% |
| Completed trips relevant to the selected stations/dates | 669,959 | 63,974, or 9.55% |
| File size | 2,070.35 MB across four raw CSVs | 0.247 MB in Parquet format |

Relevant subset trips have at least one pickup or return at a selected station during the selected dates. Each journey is counted once in the trip figure above. Individual journeys are summarized into hourly counts in the exported file; pickups and returns should not be added together to count unique trips.

The file uses about 99.988% less storage. This reduction comes from selecting fewer stations and dates, summarizing minute records into hours, removing individual-record detail from the export, and using a compressed file format. It does not mean that only 0.012% of the original observations were used.

The other cities and dates remain useful for broader analysis and stress tests. They are outside the proposed pilot, rather than being proven irrelevant or repetitive. The original files remain unchanged.

## How the data was processed

I checked station identifiers, timestamps, duplicate keys, missing periods and availability counts, then linked the files through station IDs and dates. Pickups use trip start times; returns use trip end times.

For availability, I carried a valid recorded state only to the next observation when the gap was positive and no longer than 90 seconds. I split these intervals at hour boundaries and added up the time observed, empty and full. Longer gaps were treated as unknown. Records showing both zero bikes and zero free docks were excluded from valid exposure because their meaning is unclear.

The resulting table has one row per station per hour, including hours with zero completed trips. Weather is linked through a documented city-level weather location and date. This is a geographic approximation, not a weather reading taken at each station.

| Information in the hourly table | What it helps us understand |
| --- | --- |
| Station ID, city, date and hour | Where and when activity happens |
| Pickups and returns | How bikes leave and arrive at stations |
| Valid observed time and empty/full time | Whether availability could have limited service |
| Average bikes and effective available capacity | General inventory conditions and capacity concerns |
| Weekday/weekend and weather fields | Differences between day types and weather conditions |
| Training/validation label | Which dates supply estimates and which dates check them |

These are counts, time totals, averages and calendar categories. They have not been normalized or standardized. We should keep meaningful units, such as bikes, seconds, hours and dollars, when building the optimization model.

Net flow can be calculated as **pickups minus returns**. A positive value means more bikes left than arrived during that hour. It is not currently a separate column in the exported candidate.

Exact opening inventory and reviewed physical dock capacity still need to be supplied separately. An hourly average is not the number of bikes available at the start of the hour. Trips crossing the pilot boundary remain in endpoint counts and will need explicit treatment in the model.

## Checks on patterns and unusual observations

To check the subset fairly, I compared the same 34 stations with the other 94 complete weeks in the broader data. The comparison calendar contains 104 complete weeks, from 2 September 2013 to 30 August 2015 inclusive. The reference excludes the selected 10 weeks.

Both periods show weekday pickup peaks around **8 am and 5 pm**. Their average hourly shapes are very similar, with a correlation of 0.997. However, the operating conditions are not identical.

| Measure | Other 94 weeks | Selected 10 weeks |
| --- | ---: | ---: |
| Average weekday pickups per day | 985 | 1,116 |
| Average weekend pickups per day | 344 | 323 |
| Valid observed time with no bikes | 1.16% | 1.85% |
| Valid observed time with no free docks | 0.72% | 0.86% |
| Days flagged for unusual daily usage | 46 of 658 | 1 of 70 |

Unusual daily usage was flagged using separate weekday and weekend ranges from the reference data. A day outside 1.5 times the interquartile range beyond the middle half of observations was flagged for review. This is a screening rule, not proof of an error. All flagged days were retained. The 13 relevant subset trips lasting longer than 24 hours were also retained with review flags in the trip data.

Only six stations appear in both periods' top-10 lists for empty/full time. This means that broad daily peaks repeat more closely than exact station priorities. The proposed subset is suitable for investigating a specific pilot; these checks do not prove that its results will represent every season or unusual day.

I also compared forecasts using one, two, four and eight weeks of history across three later validation periods. Four and eight weeks gave similar average errors: about 0.673 and 0.675 completed departures per station-hour. This supports testing both history lengths. It does not establish that they produce equivalent demand estimates or optimization results.

The current export contains eight weeks for building estimates, from 9 February to 5 April, followed by two weeks for exploratory checking, from 6 to 19 April. The eight-week period has only five measurable-rain days, so detailed rain effects at individual stations will be difficult to estimate reliably. A later period should also be reserved for policy evaluation; the current validation dates have already been examined.

## Demand and cost inputs still needed

Completed trips show requests that were served. They do not count people who found no bike or no free dock. Station status helps identify these restricted periods, but estimating missed requests requires assumptions. This distinction is also discussed by [Liu and Pelechrinis (2021)](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0252894).

Fu Yan will need to estimate demand using comparable periods when service was available. Counts and available-time denominators must refer to matching intervals. Very little or zero available time requires a pooled estimate from comparable observations. The method should be checked by hiding some known observations and testing whether it can recover them.

The dataset also has no actual truck routes, labor charges, redistribution expenses or customer payment records. The [proposed cost revision](SF_Bikeshare_Cost_Formula_Revision.md) provides a structure for these inputs, with supporting references and remaining evidence gaps. Costs should be kept in separate parameter and route tables rather than added as invented observations to historical customer trips.

## Planned comparison and next steps

The repository shares the candidate SF subset, supporting checks, reports and latest poster for team review. The earlier Citi Bike raw CSV and complete cleaned trip copy are excluded from current repository files, while their EDA is retained. After the team agrees on scope, features and cost assumptions, I will finish the focused subset EDA and finalize the model-input package.

| Work | Lead / dependency |
| --- | --- |
| Subset EDA, data quality checks and input handoff | Carlo, with input-format requirements from the modeling team |
| Demand estimation and its assumptions | Fu Yan |
| Cost/revenue evidence and literature | Jason, coordinated with Carlo and Fu Yan |
| Mathematical formulation and required inputs | Joohee |
| Optimization, baselines, experiments and results | Hong Jin |
| Final data consistency and report review | Carlo and the team |

The model will compare no rebalancing, a simple rule and an optimized plan using the same starting inventory, demand scenarios, capacities and operating assumptions. Historical station inventories already reflect existing operations, so they cannot automatically be treated as the no-rebalancing result.

The final graphs and tables should compare trips served, unmet requests, bikes moved, redistribution cost and additional operating contribution. These will be modeled results. We will test how they change with demand, costs, truck capacity, rain and unusual days before drawing recommendations. Advanced machine learning is optional; reliable inputs and fair policy comparisons are still required.

## Supporting files

- [Current poster](../output/sf_bikeshare/whatsapp/SF_Bikeshare_Subset_Poster.png)
- [Candidate hourly dataset](../output/sf_bikeshare/subset_assessment/candidate_observed_station_hours.parquet) and [station list](../output/sf_bikeshare/subset_assessment/candidate_stations.csv)
- [Full-data EDA and run instructions](../sf_bikeshare/README.md)
- [Source file manifest](../output/sf_bikeshare/source_manifest.json)
- [Subset pattern checks](../output/sf_bikeshare/subset_assessment/Pattern_Check_Findings.md)
- [Pattern/outlier audit code](../sf_bikeshare/validate_subset_patterns.py) and [history-window comparison code](../sf_bikeshare/assess_subset_windows.py)

The reported data counts and preliminary findings come from the local audit outputs. Team approval, final model inputs and optimization results remain outstanding.
