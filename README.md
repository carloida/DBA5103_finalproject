# DBA5103: SF Bike Share redistribution

This project studies where and when to move bikes between stations so that the extra trips served justify the moving cost. It follows the problem discussed at our meeting and recorded by Joohee:

> Given estimated demand at each station and time, how many bikes should we move, where should they go, and when should we move them to earn the highest additional operating contribution, within station and truck limits?

**Status:** full-data EDA and audits are complete. A small SF subset, preliminary checks and a poster are available. Final modeling scope and demand/cost assumptions still need team agreement. No optimized plan or financial gain has been calculated.

## Start here

- **[SF subset](output/sf_bikeshare/subset_assessment/candidate_observed_station_hours.parquet)** and [station details](output/sf_bikeshare/subset_assessment/candidate_stations.csv).
- **[Subset guide and field definitions](output/sf_bikeshare/subset_assessment/README.md)**: contents, splits, limitations and loading instructions.
- **[Latest portrait poster](output/sf_bikeshare/whatsapp/SF_Bikeshare_Subset_Poster.png)**: processing steps, file size and pattern comparisons.
- [Initial project report](docs/SF_Bikeshare_Initial_Report.md).
- [Cost-formula revision and references](docs/SF_Bikeshare_Cost_Formula_Revision.md).
- [Project status, responsibilities and next steps](docs/PROJECT_STATUS.md).
- [Data sources and publishing policy](docs/DATA_SOURCES.md).

## Shared dataset

The pilot keeps **34 San Francisco stations installed by 29 August 2013**, over **9 February-19 April 2015**. Each row represents one station during one hour.

| Measure | Full source / hourly table | Shared subset |
| --- | ---: | ---: |
| Stations | 70 in 5 cities | 34 in San Francisco |
| Hourly rows | 1,209,456 | 57,120 (4.72%) |
| Relevant completed trips | 669,959 | 63,974 (9.55%) |
| Storage | 2,070.35 MB raw CSVs | 0.247 MB Parquet |

Relevant trips have at least one selected endpoint event during the study window and are counted once in the trip figure. The file stores hourly counts, not individual journeys. Storage reduction includes smaller scope, aggregation and compression; it does not measure the percentage of observations used.

The table contains pickups, returns, valid observed time, time with no bikes/free docks, average availability and city-level weather. Net flow can be calculated as pickups minus returns. Features have not been normalized or standardized.

- **8 weeks for estimates:** 9 February-5 April, 45,696 rows labeled `training`.
- **2 weeks for exploratory checks:** 6-19 April, 11,424 rows labeled `validation`.

The full SF source files and local database are **not included**. The Citi Bike raw CSV and complete cleaned trip copy have been removed from current repository files; the original EDA is retained below. Git history has not been rewritten.

## Preliminary findings

The selected dates were compared with the other 94 complete weeks for the **same 34 stations**. Both show weekday peaks around 8 am and 5 pm, but operating conditions differ.

| Measure | Other 94 weeks | Selected 10 weeks |
| --- | ---: | ---: |
| Weekday pickups/day | 985 | 1,116 |
| Valid observed time with no bikes | 1.16% | 1.85% |
| Unusual daily totals flagged | 46 of 658 days | 1 of 70 days |

All unusual-usage days were kept. Only six stations overlap in the two top-10 empty/full-pressure lists. Similar broad peaks do not establish that every season or station risk is interchangeable. Four- and eight-week histories gave similar average completed-trip forecast errors, but equivalent optimization results have not been established. See [the full checks](output/sf_bikeshare/subset_assessment/Pattern_Check_Findings.md).

## Load the subset without the original data

Use Python 3.12 and install `duckdb` and `pandas` in a fresh environment:

```powershell
py -3.12 -m venv .venv
& ./.venv/Scripts/python.exe -m pip install duckdb pandas
```

From the repository root:

```python
import duckdb

path = "output/sf_bikeshare/subset_assessment/candidate_observed_station_hours.parquet"
df = duckdb.sql(f"SELECT * FROM read_parquet('{path}')").df()
training = df[df["split"] == "training"].copy()
validation = df[df["split"] == "validation"].copy()
training["net_outflow"] = training["departures"] - training["arrivals"]
print(df.shape)  # 57,120 rows
print(df.groupby("split").size())
```

Use training dates to estimate profiles and select priorities. Validation dates have already been explored, so agree on a later policy-evaluation period too. No raw CSV or database is needed to read this shared file.

## Demand, cost and optimization work

Completed trips are served requests, not all attempted demand. Fu Yan will estimate missed requests during empty/full periods using matching available-time exposure and explicit assumptions. Zero exposure needs a pooled fallback. The [cost revision](docs/SF_Bikeshare_Cost_Formula_Revision.md) covers vehicle activation, crew/vehicle time, fuel, mileage and fees, with sources and remaining gaps. Actual relocation expenses and customer payments are absent from the data.

Compare **no rebalancing, a simple rule and an optimized plan** under identical starting inventory, demand scenarios, capacities and operating assumptions. Report service, bikes moved, cost and additional contribution. Historical inventories reflect existing operations and cannot automatically serve as a no-rebalancing baseline. Advanced machine learning is optional; reliable inputs and stress tests are still needed.

Remaining inputs include reviewed capacities, exact opening stocks, travel/transfer timing, boundary flows and suitable financial assumptions. Hourly mean inventory is not opening stock. Only five measurable-rain days occur in the eight training weeks, limiting detailed rain estimates. Bicycle/dock capital purchases are outside the operational scope.

## Original EDA preserved

- [SF executed notebook](sf_bikeshare/SF_Bay_Area_Bikeshare_EDA.ipynb), [analysis code](sf_bikeshare/SF_Bay_Area_Bikeshare_EDA.py) and [full analysis guide](sf_bikeshare/README.md).
- [SF inferential report](output/sf_bikeshare/SF_Bikeshare_Inferential_Report.pdf) and [report with figures](output/sf_bikeshare/SF_Bikeshare_Inferential_Report.md).
- [Original Citi Bike notebook](CitiBike_JC_202609_EDA.ipynb), [code](CitiBike_JC_202609_EDA.py) and [findings](output/citibike_eda/EDA_Findings_and_Project_Options.md). Its saved charts and summary/audit tables remain in `output/citibike_eda/`.

Citi Bike's September 2026 Jersey City/Hoboken analysis is earlier background, separate from historical SF data. Saved notebooks can be viewed without source files. Re-running either full EDA requires obtaining the originals separately and can create large ignored local outputs.

To reproduce SF analysis, follow [the full-data instructions](sf_bikeshare/README.md). To recreate only the current poster, install `sf_bikeshare/requirements.txt` and run `sf_bikeshare/make_subset_poster_portrait.py`; it uses Windows Arial font paths.

## Publishing limits

Shared: code, saved EDA, reports, small summary tables, the named subset and the latest poster. Excluded: raw sources, complete cleaned trip copies, databases, bulk exports, temporary files, lecture PDFs, assignments and reference books. Only the named subset Parquet is permitted. [Release hashes](output/sf_bikeshare/subset_assessment/release_manifest.json) identify the shared files without distributing the originals.

SF source: [Ben Hamner's Kaggle dataset](https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share). Source terms still apply; no new license over original data is asserted here.
