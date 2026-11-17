# Project status - 17 November 2026

Following the 16 November meeting, the modeling work focuses on SF Bay Area Bike Share. The earlier Citi Bike EDA remains as background. A 34-station SF subset is shared for review; publication does not mean every modeling assumption has been agreed.

## Completed

- Original Citi Bike notebook, code, charts, audit tables and findings retained.
- Full SF audit/EDA: 669,959 trips, 70 stations, 71,984,434 status snapshots and 3,665 weather location-days; saved notebook, 14 chart panels and reports.
- Candidate: 34 SF stations, 9 February-19 April 2015, 57,120 station-hours in a roughly 0.247 MB Parquet file.
- History-length, hourly-pattern, station-priority, coverage and outlier checks.
- Updated poster, initial report and cited cost-formula proposal.
- Raw Citi Bike CSV and complete cleaned trip copy removed from current repository files. Full SF sources and local database are excluded; Git history remains intact.

## Objective

Choose how many bikes to move, where and when, to maximize additional trip contribution minus additional redistribution cost relative to no rebalancing, under bike conservation, inventory, dock, timing and truck limits. Bicycle/dock purchases are outside the operational scope.

## Roles and dependencies

| Person | Responsibility | Needs |
| --- | --- | --- |
| Carlo | Scope, EDA, quality checks, data handoff and consistency edit | Input format/model requirements from Fu Yan, Joohee and Hong Jin |
| Fu Yan | Demand estimation and scenarios | Observed flows and valid exposure from Carlo |
| Jason | Cost/revenue evidence and literature | Vehicle scenario and accounting scope, with Carlo/Fu Yan |
| Joohee | Mathematical formulation and method | Agreed data definitions, demand and cost assumptions |
| Hong Jin | Implementation, baselines and results | Agreed data, demand, parameters and formulation |

## Still required

1. Confirm stations, dates, hourly slots and boundary-flow rules. The candidate is a pilot, not evidence that other periods are redundant.
2. Finish focused subset EDA; agree on four/eight-week estimation and later evaluation dates.
3. Fit/validate demand correction, including uncertainty and zero-exposure handling.
4. Review capacities/opening stock and conserve bikes across trips, returns and transit.
5. Verify vehicle, staffing, handling, travel and revenue inputs; label proxies and assumptions.
6. Compare no moves, a simple rule and optimization using identical information/initial states.
7. Test demand, costs, capacity, rain/extremes and break-even conditions.

No optimized plan, measured recovered demand or profit gain is established. Current validation dates have already been examined and are exploratory, not a sealed final test.

## Timeline from the supplied minutes

Data/EDA target: 17 November. Demand/model review: 18 November. Coding: tentatively 19-20 November. Consolidation: 21 November. Submission: 22 November; resolve issues before Carlo's evening travel.

See the [initial report](SF_Bikeshare_Initial_Report.md), [cost revision](SF_Bikeshare_Cost_Formula_Revision.md), [subset guide](../output/sf_bikeshare/subset_assessment/README.md) and [poster](../output/sf_bikeshare/whatsapp/SF_Bikeshare_Subset_Poster.png).
