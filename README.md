# DBA5103: SF Bike Share redistribution

This project studies where and when to move bikes between stations so that the extra trips served justify the moving cost. It follows the problem discussed at our meeting and recorded by Joohee:

> Given estimated demand at each station and time, how many bikes should we move, where should they go, and when should we move them to earn the highest additional operating contribution, within station and truck limits?

**Status (22 November):** main V3, its minute-data supplement and five separate robustness packages are published and preserved. Historical and hybrid demand scenarios have been compared locally; detailed case reports and compact evidence are published below. Historical rates are the proposed base, with final team selection and a complete demand producer still pending. Four-date model checks use provisional costs and unverified routes; they do not establish final financial gains or completed robustness testing. The focused V3 EDA figure is still planned. Shared Google Docs were read only; Carlo will upload information manually.

## Start here

- **[Demand estimation case comparison](docs/SF_Bikeshare_Demand_Estimation_Case_Comparison.md)** (22 November): separate detailed reports for [Case A Historical](docs/supporting/SF_Bikeshare_Demand_Case_A_Historical.md) and [Case B Hybrid](docs/supporting/SF_Bikeshare_Demand_Case_B_Hybrid.md), including formulas, reusable Section 3.4 text, matched validation, lecture/research references and release requirements. [Compact evidence tables](output/sf_bikeshare/demand_case_comparison_2026-11-22/README.md) support the reports; full trial demand inputs and unmerged model code are not released here.
- **[Minute status and trip supplement for V3 demand estimation](output/sf_bikeshare/demand_estimation_inputs_v3/README.md)** (21 November): same 34 stations and 70-day model window, with short preceding context and status anchors. Compressed minute observations for Fu Yan's estimator; all 18 checks passed. Frozen V3 files are unchanged; estimated demand remains pending reconciliation.
- **[20 November model-input handoff](docs/supporting/SF_Bikeshare_Model_Input_Handoff_2026-11-20.md)**: confirmed data rules, provisional metric cost benchmarks, accounting corrections and outstanding inputs before locking the full model configuration.
- **[Carlo's Section 3 draft and data-cleaning appendix](docs/SF_Bikeshare_Consolidated_Data_Preparation_Report.md)**: scoped to the shared data/demand section, with Fu Yan's estimation subsection pending. [Reference and feature review](docs/supporting/SF_Bikeshare_Reference_and_Feature_Review_2026-11-19.md) records the checks and remaining assumptions.
- **[Project pipeline report](docs/SF_Bikeshare_Project_Pipeline_Report.md)** ([PDF](output/pdf/SF_Bikeshare_Project_Pipeline_Report.pdf)) and **[portrait workflow poster](output/sf_bikeshare/pipeline/SF_Bikeshare_Project_Pipeline_Poster.png)**: team responsibilities, two-stage modeling, evaluation and report-writing plan.
- **[Robustness testing datasets](output/sf_bikeshare/robustness_testing/README.md)**: five separate observed-data cases, explicitly for robustness testing; same 51 hourly features and 21 core schemas as V3. All 325 build checks and 90 export readbacks passed. Experiments and results remain pending.
- **[V3 enriched model-input handoff](output/sf_bikeshare/model_inputs_v3/README.md)** and **[V1-V5 dataset progression](docs/SF_Bikeshare_Dataset_Iterations.md)**: new inputs, teammate requirements, verification and remaining decisions.
- **[SF subset](output/sf_bikeshare/subset_assessment/candidate_observed_station_hours.parquet)** and [station details](output/sf_bikeshare/subset_assessment/candidate_stations.csv).
- **[Subset guide and field definitions](output/sf_bikeshare/subset_assessment/README.md)**: contents, splits, limitations and loading instructions.
- **[Earlier subset poster](output/sf_bikeshare/whatsapp/SF_Bikeshare_Subset_Poster.png)**: processing steps, file size and pattern comparisons.
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

V3 now provides observed opening stocks, capacity diagnostics, boundary/OD flows and current road distances. Remaining decisions include effective versus physical capacity, travel/transfer and within-hour timing, depot/vehicle configuration, external-flow failure rules and suitable financial assumptions. Hourly mean inventory is not opening stock. Only five measurable-rain days occur in the eight training weeks, limiting detailed rain estimates. Bicycle/dock capital purchases are outside the operational scope.

## Original EDA preserved

- [SF executed notebook](sf_bikeshare/SF_Bay_Area_Bikeshare_EDA.ipynb), [analysis code](sf_bikeshare/SF_Bay_Area_Bikeshare_EDA.py) and [full analysis guide](sf_bikeshare/README.md).
- [SF inferential report](output/sf_bikeshare/SF_Bikeshare_Inferential_Report.pdf) and [report with figures](output/sf_bikeshare/SF_Bikeshare_Inferential_Report.md).
- [Original Citi Bike notebook](CitiBike_JC_202609_EDA.ipynb), [code](CitiBike_JC_202609_EDA.py) and [findings](output/citibike_eda/EDA_Findings_and_Project_Options.md). Its saved charts and summary/audit tables remain in `output/citibike_eda/`.

Citi Bike's September 2026 Jersey City/Hoboken analysis is earlier background, separate from historical SF data. Saved notebooks can be viewed without source files. Re-running either full EDA requires obtaining the originals separately and can create large ignored local outputs.

To reproduce SF analysis, follow [the full-data instructions](sf_bikeshare/README.md). To recreate only the current poster, install `sf_bikeshare/requirements.txt` and run `sf_bikeshare/make_subset_poster_portrait.py`; it uses Windows Arial font paths.

## Publishing limits

The repository provides code, saved EDA, reports, small summary tables, the named V2 subset, scoped V3 CSV/GZIP inputs and the latest poster. Excluded: raw sources, complete cleaned trip copies, databases, bulk full-system exports, temporary files, lecture PDFs, assignments and reference books. Only the named subset Parquet is permitted. [V2 release hashes](output/sf_bikeshare/subset_assessment/release_manifest.json) and the [V3 manifest](output/sf_bikeshare/model_inputs_v3/manifest.json) identify the corresponding files without distributing the originals.

SF source: [Ben Hamner's Kaggle dataset](https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share). Source terms still apply; no new license over original data is asserted here.
