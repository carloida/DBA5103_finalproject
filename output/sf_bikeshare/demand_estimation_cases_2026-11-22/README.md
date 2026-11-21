# Downloadable historical and hybrid demand outputs

Prepared 22 November 2026. These are the two audited **demand-estimation output snapshots**, ready to inspect or load into separate provisional optimization runs. They share the same station-hour interface but contain different estimated-demand values.

**Status: provisional cases; final team selection and complete producer handoff remain pending.** These estimates supplement frozen observed V3. They are not new observed trips, final financial results, or optimization transfer plans. Publishing the output snapshots does not complete the missing v2 core-module handoff.

## Downloads

| Case | Plain CSV | Smaller gzip CSV | Detailed report |
| --- | --- | --- | --- |
| A Historical | [Download CSV](https://raw.githubusercontent.com/carloida/DBA5103_finalproject/main/output/sf_bikeshare/demand_estimation_cases_2026-11-22/historical_demand_station_hour.csv) | [Download CSV.gz](https://raw.githubusercontent.com/carloida/DBA5103_finalproject/main/output/sf_bikeshare/demand_estimation_cases_2026-11-22/historical_demand_station_hour.csv.gz) | [Case A](../../../docs/supporting/SF_Bikeshare_Demand_Case_A_Historical.md) |
| B Fu Yan v2 hybrid | [Download CSV](https://raw.githubusercontent.com/carloida/DBA5103_finalproject/main/output/sf_bikeshare/demand_estimation_cases_2026-11-22/estimated_demand_station_hour_hybrid.csv) | [Download CSV.gz](https://raw.githubusercontent.com/carloida/DBA5103_finalproject/main/output/sf_bikeshare/demand_estimation_cases_2026-11-22/estimated_demand_station_hour_hybrid.csv.gz) | [Case B](../../../docs/supporting/SF_Bikeshare_Demand_Case_B_Hybrid.md) |

Each plain CSV is approximately 11 MB. Compressed downloads are approximately **0.48 MB for historical** and **0.42 MB for hybrid**. Plain and compressed copies contain identical parsed data. For slow connections, use CSV.gz; pandas reads it directly.

The [comparison overview](../../../docs/SF_Bikeshare_Demand_Estimation_Case_Comparison.md) and [evidence tables](../demand_case_comparison_2026-11-22/README.md) explain the methods, validation, limitations and provisional model comparisons.

## What is in each output

- Same **57,120 rows x 31 columns**, covering 34 SF stations from 9 February through 19 April 2015.
- Same station/date/hour keys, observed pickup/return counts and shared V3 exposure/quality fields.
- Separate member/casual pickup and return estimates, missed-demand values and method labels.
- Different estimated/missed values because the rate assumptions differ.

| Quantity | Historical | Hybrid v2 |
| --- | ---: | ---: |
| Observed pickups | 62,243 | 62,243 |
| Estimated pickups | 64,573.775 | 66,589.924 |
| Observed returns | 62,326 | 62,326 |
| Estimated returns | 63,014.136 | 63,652.521 |

Historical uses training availability-adjusted profiles by station, clock hour, day type and rider. Hybrid uses the preceding 30-minute rate, with at least 20 available minutes, for the first elapsed hour of an outage, then historical rates. Both subtract served trips once per episode and allocate residual missed demand back to hours.

Exposure fields are seconds. Demand fields are expected trips/bikes and can be fractional. Dates remain recorded naive local times. The 34 missing-exposure DST-related station-hours preserve flags and observed counts; missing exposure is not an estimated zero for actual unmet demand. No currency or non-metric physical fields are added to these CSVs.

## Loading

From a cloned repository, with pandas installed:

    from pathlib import Path
    import pandas as pd

    folder = Path("output/sf_bikeshare/demand_estimation_cases_2026-11-22")
    historical = pd.read_csv(folder / "historical_demand_station_hour.csv.gz")
    hybrid = pd.read_csv(folder / "estimated_demand_station_hour_hybrid.csv.gz")
    print(historical.shape, hybrid.shape)  # both (57120, 31)

Select **one case per optimization run** and keep its identifier in the results. Do not concatenate the two tables as if they were different observations. In a local copy of the reviewed model, point its demand-file argument to the selected CSV or CSV.gz. Its required fields are estimated_subscriber_pickups, estimated_customer_pickups and estimated_total_returns; both outputs contain them with finite values.

Both cases also contain the rider-split return estimates and observed counts used for checking. Keep the common station, opening-stock and distance inputs from V3.

## Checks and provenance

The source fingerprints match the previously audited files. Both outputs passed unique-key, shape, finite-demand and plain/gzip readback checks. Shared observed/key fields match across cases. Earlier audits verified all 70 daily model loads and the hybrid numerical reconstruction; see the linked reports for scope.

The [manifest](manifest.json) records source and published hashes, byte sizes, columns, totals and checks. Record line endings were normalized to LF where necessary; parsed values are unchanged. Gzip copies use a fixed timestamp for stable packaging.

These files are frozen output snapshots for the two reviewed main-case methods. The historical trial reused an audited episode table; Fu Yan's supplied hybrid wrapper still needs its revised core module. Source-code reproducibility, corrected validation, final case choice, cost calibration, route checks and the full robustness study remain separate tasks. No producer or unmerged optimization code is included here.
