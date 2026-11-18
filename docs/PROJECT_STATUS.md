# Project status - 18 November 2026

Following the 16 November meeting, the modeling work focuses on SF Bay Area Bike Share. The earlier Citi Bike EDA remains as background. Joohee approved the 34-station, 10-week, hourly scope in the comments supplied on 18 November. Vehicle, demand, revenue and timing assumptions still require agreement. The repository provides the V3 scoped exports and supporting documentation; the full databases stay local. Shared Google Docs were read only and Carlo will upload information there manually.

## Completed

- Original Citi Bike notebook, code, charts, audit tables and findings retained.
- Full SF audit/EDA: 669,959 trips, 70 stations, 71,984,434 status snapshots and 3,665 weather location-days; saved notebook, 14 chart panels and reports.
- Candidate: 34 SF stations, 9 February-19 April 2015, 57,120 station-hours in a roughly 0.247 MB Parquet file.
- V3 enriched local database and scoped CSV/GZIP handoff: rider splits, opening stocks, capacity audit, OD/boundary/transit tables, current directed road matrix, historical tariff evidence and separate revenue-allocation scenarios. All V3 working physical measurements and the local cost formula now use metric units. 21 database tables; 43 reconciliation checks and 18 export row-count readbacks passed. Original database and V2 Parquet preserved.
- All 2,380 midnight opening stocks are fresh; 67 have effective/static capacity mismatches. All 34 stations have some capacity discrepancy. The 34 stale hourly openings coincide with the March DST transition and remain flagged/NULL.
- [Dataset progression and teammate-response table](SF_Bikeshare_Dataset_Iterations.md) and [V3 handoff guide](../output/sf_bikeshare/model_inputs_v3/README.md).
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

1. Scope confirmed by Joohee; agree boundary-flow failure rules, within-hour ordering, operating horizon and depot. The pilot does not establish that other periods are redundant.
2. Finish focused subset EDA; agree on four/eight-week estimation and later evaluation dates.
3. Fit/validate demand correction, including uncertainty and zero-exposure handling.
4. Resolve capacity interpretation and flagged DST/long-trip timing cases; propagate inventory and accepted-trip returns consistently. Opening stocks and OD/boundary/transit inputs are now extracted.
5. Finalize vehicle, staffing, handling and incremental trip-value inputs. Historical tariffs and Jason's allocated-revenue scenarios are recorded separately; allocations are not measured marginal receipts. Current road estimates are not historical truck logs.
6. Compare no moves, a simple rule and optimization using identical information/initial states.
7. Test demand, costs, capacity, rain/extremes and break-even conditions.

No optimized plan, measured recovered demand or profit gain is established. Current validation dates have already been examined and are exploratory, not a sealed final test.

## Timeline from the supplied minutes

Data/EDA target: 17 November. Demand/model review: 18 November. Coding: tentatively 19-20 November. Consolidation: 21 November. Submission: 22 November; resolve issues before Carlo's evening travel.

See the [initial report](SF_Bikeshare_Initial_Report.md), [cost revision](SF_Bikeshare_Cost_Formula_Revision.md), [subset guide](../output/sf_bikeshare/subset_assessment/README.md) and [poster](../output/sf_bikeshare/whatsapp/SF_Bikeshare_Subset_Poster.png).
