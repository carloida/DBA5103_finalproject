# R4_sf_2015_apr_jun

**ROBUSTNESS TESTING ONLY - retrospective observed-data subset**

This is a separate comparison case, not a replacement for the [main V3 SF dataset](../../model_inputs_v3/README.md).

- City: San Francisco.
- Dates: 20 Apr 2015 - 28 Jun 2015; hourly recorded-local-clock grid.
- Stations: 34; station-hours: 57,120.
- First eight weeks: `training`. Final two weeks: `validation`, for retrospective policy evaluation after model/estimator choices are fixed. These dates are not a sealed holdout.
- Same 51 hourly columns and exact SQL types as V3; all 21 core table schemas match V3.
- All working physical units are metric. Currency remains USD.
- Build checks: 65 passed; portable table row-count readbacks: 18 passed.
- Unusable midnight stocks: 4. They remain NULL/flagged; no fallback or evaluation-day exclusion has been applied.

Use `station_hour_observed.csv.gz` as the main panel and join other exported tables at their documented keys. The original source database and local case DuckDB file are excluded from GitHub. No attempted-demand estimates, optimized policies, executable truck routes or financial gains have been produced.

## Economic inputs and limits

Historical tariffs and Jason's allocation scenarios are reference benchmarks, not measured case payments. The three fixed 2015 gasoline entries from V3 retain their reference identifiers, but their case values are deliberately NULL with the old reference values in notes. Agree a common price-year scenario or source period-matched values before economic evaluation. Truck/cost values remain unselected.

Road estimates use current default driving conditions and include snapping diagnostics. They do not establish historical congestion, truck restrictions, depot legs or route feasibility. OD/availability/initial-stock flags must be handled consistently by every evaluated policy.

See [suite instructions](../README.md), `data_dictionary.csv`, `table_inventory.csv`, `validation_checks.csv`, `case_definition.json` and `manifest.json`. The manifest records all exported-file hashes and the build rules.
