# SF Bay Area Bike Share EDA

This extends the initial Citi Bike redistribution project using the four newly supplied SF Bay Area files. All work is saved alongside the Citi Bike analysis in the Operations research workspace. Source CSVs remain unchanged in their original folder.

## Read first

- [Shared 34-station subset and field guide](../output/sf_bikeshare/subset_assessment/README.md): this small file can be used without downloading original data or building the full database.
- [Latest subset poster](../output/sf_bikeshare/whatsapp/SF_Bikeshare_Subset_Poster.png), [initial project report](../docs/SF_Bikeshare_Initial_Report.md) and [cost-formula revision](../docs/SF_Bikeshare_Cost_Formula_Revision.md).
- [Executed EDA notebook](SF_Bay_Area_Bikeshare_EDA.ipynb): 14 chart panels, their questions, cleaning definitions and calculated findings.
- [Inferential report (PDF)](../output/sf_bikeshare/SF_Bikeshare_Inferential_Report.pdf): nine pages on evidence, uncertainty, financial gaps and a focused OR model.
- [Full report with all figures (Markdown)](../output/sf_bikeshare/SF_Bikeshare_Inferential_Report.md).
- [Database relationships and safe joins](DATABASE_GUIDE.md).
- [Question-to-chart index](../output/sf_bikeshare/figure_questions_and_findings.csv).
- Short WhatsApp summary: [1. Usage](../output/sf_bikeshare/whatsapp/SF_Bikeshare_EDA_1_of_4.png), [2. Availability](../output/sf_bikeshare/whatsapp/SF_Bikeshare_EDA_2_of_4.png), [3. Statistical findings](../output/sf_bikeshare/whatsapp/SF_Bikeshare_EDA_3_of_4.png), [4. Remaining gaps](../output/sf_bikeshare/whatsapp/SF_Bikeshare_EDA_4_of_4.png).

## Main findings

| Item | Result |
| --- | --- |
| Trip observation period | 29 August 2013-31 August 2015 |
| Completed trips / stations / observed bike IDs | 669,959 / 70 / 700 |
| Raw status observations, all scanned | 71,984,434 |
| Weather location-days | 3,665 across 5 weather locations |
| Status composite keys repeated | 0 |
| Trip endpoints missing from station | 0 |
| AM/PM average-flow reversals | 62 of 70 stations |
| Empty / full exposure | 0.735% / 0.454% of valid observed time |
| Short-gap status coverage | 98.877% of installation-based reference time |
| Availability-total mismatch with static dock count | 3,403,916 snapshots, about 4.73% |
| Both available bikes and free docks zero | 240 snapshots, excluded as ambiguous |

The key improvement is historical availability and a capacity field. The key limitation remains: empty/full exposure does not count unfulfilled customer requests, and none of the four files contains actual costs, fares, revenue or profit. Station status captures the system under its existing operations; the file does not identify staff moves or a no-redistribution counterfactual.

Inferential findings are explicitly associative. A fixed 34-station SF cohort records about 655 more completed trips per weekday than weekend day; the 95% four-week-block interval is about 598-718. A calendar/weather-controlled daily regression associates measurable rain with about 21.6% fewer trips+1 (95% 28-lag HAC interval: 11.7%-30.4% fewer). Counting trace precipitation as rain changes the estimate. These findings do not establish causation or present-day applicability.

## Run locally

These commands rebuild the **full** historical analysis and require separately obtained source files. Raw CSVs and the local database are not distributed in this repository. For ordinary team work, start with the shared subset above. The candidate scope and financial/demand assumptions remain subject to team review.

Python 3.12 is used. From the repository root:

```powershell
& ./.venv/Scripts/python.exe -m pip install -r sf_bikeshare/requirements.txt
& ./.venv/Scripts/python.exe sf_bikeshare/build_database.py --source 'C:/path/to/SF BAY AREA BIKESHARE DATA'
```

The default source location is the Desktop folder named `SF BAY AREA BIKESHARE DATA`, relative to this course workspace. To override it consistently for database building, EDA and notebook execution:

```powershell
$env:SF_BIKESHARE_DATA = 'C:/path/to/SF BAY AREA BIKESHARE DATA'
& ./.venv/Scripts/python.exe sf_bikeshare/build_database.py
& ./.venv/Scripts/python.exe sf_bikeshare/SF_Bay_Area_Bikeshare_EDA.py
& ./.venv/Scripts/python.exe sf_bikeshare/make_notebook.py
```

`build_database.py` checks file size/mtime against the full source-hash manifest before reusing the local database. If input files change, rebuild explicitly using `--rebuild`. The builder uses four threads, a 2 GB memory limit and disk spill. Allow several GB of free disk space. The generated database is about 1.5 GB; it is excluded from Git along with temporary spill files. No second copy of the raw CSVs is made.

The notebook generator executes with the same Python environment that runs it, using a temporary kernel specification under `tmp/`. Its saved notebook opens as an ordinary Python notebook.

## Output definitions

- `source_manifest.json`: byte counts, full SHA-256 hashes and build signature.
- `key_audit.csv`, `column_quality.csv`, `trip_quality.csv`, `status_quality.csv`: source quality and key integrity.
- `capacity_audit.csv`, `station_coverage.csv`, `status_month_coverage.csv`, `interval_gap_audit.csv`: availability assumptions and missingness.
- `station_availability.csv`, `hourly_availability_profile.csv`, `station_priority_evidence.csv`: time-weighted exposure measures with explicit denominators.
- `coverage_sensitivity.csv`, `gap_tolerance_sensitivity.csv`: sensitivity to coverage and state-carry choices.
- `weekly_paired_comparison.csv`, `availability_block_intervals.csv`, `weather_regression.csv`: inferential inputs and estimates.
- `forecast_metrics.csv`, `forecast_system_hourly.csv`: chronological completed-trip forecast baselines.
- `business_case_gap_assessment.csv`, `financial_and_operating_inputs_template.csv`: observed evidence versus inputs still needed. Financial values are deliberately blank.
- `database_schema_actual.sql`, `example_queries.sql`: table/index definitions and safe join examples; see the guide for audited logical FKs.
- `analysis_manifest.json`, `artifact_validation.json`: computed headlines and validation outcomes.

## Cleaning and statistical choices

- All trips are retained after parsing/ID checks; long trips, duration inconsistencies, name aliases and bike-sequence discontinuities are separately audited.
- Status time is parsed across both supplied timestamp formats. Nonpositive/over-90-second next-snapshot gaps are not carried forward.
- Zero-total availability is treated as ambiguous. Effective available totals are not silently substituted for historical physical capacity.
- Time intervals are split at hour boundaries, and percentages use valid observed seconds. Missing exposure stays missing.
- Weather joins use an explicit city proxy plus date, never the rider ZIP field. Trace rain is flagged and sensitivity-tested.
- The fixed SF cohort and complete-week pairing limit station-growth confounding in the weekday comparison. Four-week moving blocks preserve some temporal dependence.
- Daily system availability intervals use seven-day blocks with station observations kept together. Weather regression uses 7- and 28-lag HAC sensitivity.
- Forecasting trains before 3 July 2015 and tests the final 60 calendar days. It predicts completed trips, not uncensored demand or the value of a redistribution decision.

## Next model

Start with one city, reviewed capacities and high-coverage dates. Compare no moves, a budget-matched greedy rule and an LP/network-flow transfer plan. Collect or label initial-stock, travel-time, relocation-cost and financial assumptions. Estimate censored demand separately before claiming lost orders or profit recovered. Link accepted OD trips and inventories consistently in any time-expanded simulation.

Source description: [Kaggle SF Bay Area Bike Share](https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share). A relevant methodological reference is [Liu and Pelechrinis (2021), Excess demand prediction for bike sharing systems](https://pmc.ncbi.nlm.nih.gov/articles/PMC8211247/). No externally sourced financial observations are merged into the EDA.
