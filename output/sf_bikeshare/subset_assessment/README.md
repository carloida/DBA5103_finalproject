# SF Bike Share subset

Use [candidate_observed_station_hours.parquet](candidate_observed_station_hours.parquet) for the proposed pilot without downloading the original CSVs or local database. The file is 247,473 bytes (0.247 MB) and contains **57,120 rows**. Each row is one station during one recorded local-clock hour.

## Scope and split

- 34 San Francisco stations installed by 29 August 2013; IDs and static station details are in [candidate_stations.csv](candidate_stations.csv).
- 9 February-19 April 2015 inclusive, 10 complete calendar weeks.
- `training`: 9 February-5 April, 45,696 rows.
- `validation`: 6-19 April, 11,424 rows.

The scope is a candidate for team review. The validation dates have already been explored; reserve a later period for policy evaluation. The four-week alternative uses training rows from 9 March onward; the whole export still contains eight training and two validation weeks.

## Field guide

| Columns | Meaning / unit |
| --- | --- |
| `station_id`, `city` | Station identifier and supplied city |
| `hour_start`, `hour` | Recorded local hour start and hour of day, 0-23; source DST ambiguity is unresolved |
| `day_type` | `Weekday` or `Weekend`, derived from the calendar |
| `departures`, `arrivals` | Completed pickup/return events, counted at their respective endpoint times |
| `observed_seconds` | Valid short-gap status exposure in the hour; missing does not mean no demand |
| `empty_seconds`, `full_seconds` | Valid time with no bikes / no free docks |
| `low_bike_seconds`, `low_dock_seconds` | Valid time with at most two available bikes / free docks |
| `mean_bikes_available` | Time-weighted mean bikes during valid exposure; not opening stock |
| `mean_effective_capacity` | Time-weighted mean bikes plus free docks; not automatically physical dock capacity |
| `static_capacity_mismatch_seconds` | Valid time when bikes plus docks differs from the supplied static dock count |
| `weather_zip_code` | Documented city-level weather-location proxy; not a rider ZIP |
| `precipitation_numeric_inches` | Daily precipitation in inches; trace values are numeric zero with a separate flag |
| `trace_precipitation` | Whether the supplied precipitation is recorded as trace |
| `temperature_f`, `wind_mph` | Daily mean temperature (Fahrenheit) and wind speed (mph) |
| `split` | `training` or `validation` |

Station names, coordinates, installation dates and static `dock_count` are supplied separately in the station CSV. All features retain their meaningful units; they have not been normalized or standardized. Derive `net_outflow = departures - arrivals` when needed. Keep source fields unchanged and label new estimates separately.

## How it was made

The full files were audited and linked first. Trip events were grouped by station and hour. Valid status states were carried only to the next observation across positive gaps of at most 90 seconds and split at hour boundaries. Longer gaps and both-zero states did not contribute inferred exposure. Weather was joined by city proxy and date. Dense eligible hours include zero completed trips.

This export selects the station/date scope from the cached full hourly table. It does not randomly sample minutes or remove unusually busy/quiet days. Endpoint counts include journeys crossing the pilot boundary; the optimization model must account for those flows explicitly.

## Load it

From the repository root, after installing `duckdb` and `pandas`:

```python
import duckdb

path = "output/sf_bikeshare/subset_assessment/candidate_observed_station_hours.parquet"
df = duckdb.sql(f"SELECT * FROM read_parquet('{path}')").df()
training = df[df["split"] == "training"].copy()
validation = df[df["split"] == "validation"].copy()
print(df.shape)
```

## Limits and supporting checks

The table contains observed service and availability, not total attempted demand, actual staff relocations, cost or revenue. Corrected demand, exact opening stocks, reviewed capacities, timing/boundary assumptions and cost parameters remain model inputs to develop. The selected eight training weeks have only five measurable-rain days. Broad peaks resemble other periods, but weekday levels, empty exposure and station priorities differ.

- [Pattern and outlier findings](Pattern_Check_Findings.md), [period comparison](pattern_period_summary.csv) and [daily flags](flagged_daily_extremes.csv).
- [History-window comparison](window_comparison.csv) and [mean validation errors](mean_validation_metrics.csv).
- [Selection manifest](assessment_manifest.json), [audit manifest](pattern_audit_manifest.json) and [shared-file hashes](release_manifest.json).
- [Initial report](../../../docs/SF_Bikeshare_Initial_Report.md) and [cost proposal](../../../docs/SF_Bikeshare_Cost_Formula_Revision.md).

Only this named Parquet subset is shared. Full SF sources and the analytical database remain excluded from Git. Source: [Ben Hamner's SF Bay Area Bike Share dataset](https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share); source terms apply.
