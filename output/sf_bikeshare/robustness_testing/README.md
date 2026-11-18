# Robustness testing datasets

**ROBUSTNESS TESTING ONLY - separate from the main V3 SF pilot**

These five observed-data subsets implement the approved preparation request. Together with the unchanged main V3 SF pilot, they form a two-city by three-period comparison design. Preparing these files does not establish model performance or approval of every operating assumption.

| Case | City | Inclusive dates | Stations | Station-hours | Unusable midnight stocks |
| --- | --- | --- | ---: | ---: | ---: |
| [R1_san_jose_2015_feb_apr](R1_san_jose_2015_feb_apr/README.md) | San Jose | 09 Feb 2015 - 19 Apr 2015 | 16 | 26,880 | 0 |
| [R2_sf_2014_jun_aug](R2_sf_2014_jun_aug/README.md) | San Francisco | 02 Jun 2014 - 10 Aug 2014 | 34 | 57,120 | 4 |
| [R3_san_jose_2014_jun_aug](R3_san_jose_2014_jun_aug/README.md) | San Jose | 02 Jun 2014 - 10 Aug 2014 | 16 | 26,880 | 0 |
| [R4_sf_2015_apr_jun](R4_sf_2015_apr_jun/README.md) | San Francisco | 20 Apr 2015 - 28 Jun 2015 | 34 | 57,120 | 4 |
| [R5_san_jose_2015_apr_jun](R5_san_jose_2015_apr_jun/README.md) | San Jose | 20 Apr 2015 - 28 Jun 2015 | 16 | 26,880 | 0 |

The main case is [V3 SF, 9 February-19 April 2015](../model_inputs_v3/README.md): 34 stations and 57,120 rows. It is not copied into this folder.

## Same features and validation

Every case preserves the exact 51-column hourly schema and all 21 V3 core table schemas. Natural row counts differ because SF has 34 stations and San Jose has 16. Each case spans ten weeks at hourly resolution. No observations were duplicated or padded with fictional stations. All five cases passed 65 checks and 18 export row-count readbacks each: 325 build checks and 90 readbacks in total.

Missing/stale opening stocks, effective-capacity discrepancies, duration issues and DST flags are preserved. One unusable SF opening affects the later window's final two weeks. Agree a fallback or complete-day exclusion rule before evaluating any policy; no such exclusions have been silently applied.

## Load a case

Install `duckdb` and `pandas`, then run from the repository root:

```python
import duckdb
path = "output/sf_bikeshare/robustness_testing/R1_san_jose_2015_feb_apr/station_hour_observed.csv.gz"
panel = duckdb.sql(f"SELECT * FROM read_csv_auto('{path}')").df()
training = panel[panel["split"] == "training"].copy()
evaluation = panel[panel["split"] == "validation"].copy()
```

The case DuckDB files and full source database stay local. All scoped CSV/GZIP tables needed for the observed-data handoff are included. Rebuilding from original sources requires the local source database and V3 reference schema/parameter exports.

```powershell
python sf_bikeshare/build_robustness_subsets.py --case all
# If a matching road cache is absent, add --fetch-road-matrix.
```

## Intended evaluation

Fit demand using preceding training observations under one agreed method. Compare no moves, a resource-matched rule and optimized allocation with common initial stocks, demand scenarios, information and operating limits within each city-day. Check route feasibility and avoid future-information leakage. Report service, movements, km, estimated cost, solve time and failures.

The six cases provide up to 84 evaluation city-days and 252 policy-day evaluations for three policies, before exclusions, scenarios and replications. Shared dates, stations and source history make these dependent cases; they are not six independently collected systems.

## Economic scope

Historical tariffs and allocated-revenue assumptions are reference benchmarks. Case-matched gasoline values are unselected; the old V3 benchmark values remain in parameter notes. Agree a common explicit price-year scenario or obtain period-specific inputs. None of the tables establishes actual charges, marginal trip revenue or historical truck expenditure.

## Provenance and status

The original database was opened read-only. The main V3 files and producer were preserved. New San Jose road estimates were requested once and cached by station coordinates/order; the SF cache was reused. Current driving estimates do not establish historical truck operations.

Data preparation is complete. Demand estimation, final formulation, vehicle/depot decisions, policy simulation and results remain team work. See [the pipeline report](../../../docs/SF_Bikeshare_Project_Pipeline_Report.md) and the case manifests for exact build evidence.
