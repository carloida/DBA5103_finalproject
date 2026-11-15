# DBA5103 Final Project: Bike Redistribution

**Status: EDA complete; final dataset and model scope still under discussion.**

This repository saves the Citi Bike project work from the `Operations research` course folder. The initial idea is to use operations research to plan bicycle redistribution between stations and compare **no redistribution, a rule-based/greedy policy, and an optimized policy**.

The current analysis uses the supplied **September 2026 Jersey City/Hoboken Citi Bike trip file**. The team may change the modeling dataset. A meeting is planned for **Monday evening, 16 November 2026 (Singapore time)** to finalize the direction, or at least the dataset choice.

## Start here

- [EDA notebook](CitiBike_JC_202609_EDA.ipynb): analysis, explanations and the original charts.
- [Findings and project options](output/citibike_eda/EDA_Findings_and_Project_Options.md): the detailed written summary.
- Phone summaries: [1. Data and usage](output/citibike_eda/whatsapp/CitiBike_EDA_1_of_4.png), [2. Bike movements](output/citibike_eda/whatsapp/CitiBike_EDA_2_of_4.png), [3. Timing](output/citibike_eda/whatsapp/CitiBike_EDA_3_of_4.png), [4. Business case](output/citibike_eda/whatsapp/CitiBike_EDA_4_of_4.png).
- [Current project status and meeting decisions](docs/PROJECT_STATUS.md).
- [Data sources, scope and missing inputs](docs/DATA_SOURCES.md).

## Initial problem

**How much can a budget-limited redistribution plan reduce peak-period inventory pressure, and how sensitive is its performance to uncertain flows and operating assumptions?**

A starting model is a transportation/min-cost-flow LP that chooses bike transfers between stations. A time-expanded model can represent hourly inventory balances. Integer decisions can represent truck activation, additional bikes or docks; routing is a possible later extension. These are proposed models, not implemented optimization results.

The intended comparison uses the same initial stocks, station capacities, demand scenarios and operating budget for every policy. Evaluate service proxies, relocation volume and operating cost, then vary uncertain assumptions.

## What the EDA found

| Measure | Current result |
| --- | --- |
| Source records | 106,628 |
| Valid September-start trips | 106,617 |
| Observed JC/HB origin stations | 108 |
| Member / electric-bike ride shares | 73.9% / 59.7% |
| Median trip duration | 6.40 minutes |
| Three busiest average weekday hours | 17:00, 18:00, 08:00 |
| Stations with opposite AM/PM average net-flow signs | 96 of 108 |
| Missing end IDs recovered / still unresolved | 49 / 284 |

The main insight is that monthly totals hide intraday direction changes. For example, Grove St PATH gains an average of 72.8 bikes in weekday mornings and loses 63.9 in weekday evenings. This is consistent with commuting patterns, but trip purpose is not observed. Small reversals are included in the 96-station count.

**Completed trips are observed usage, not all potential demand.** The file does not record failed rentals/returns, historical station inventories, dock capacities, staff redistribution or financial transactions. Cumulative customer net flow is not actual station stock, and it cannot establish actual lost demand or profit.

## Dataset choice is open

The team has proposed [SF Bay Area Bike Share on Kaggle](https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share) as an alternative because its advertised station/status data may support inventory and capacity analysis. It has **not been downloaded, audited or selected in this repository**. The existing Citi Bike EDA can remain as motivation if the modeling data change.

An observed empty/full station indicates an availability constraint; it does **not** directly count customers who wanted to rent/return. Lost demand would still require an estimation model. Citi Bike prices should not be transferred to historical San Francisco data as if they were observed fares.

## Repository contents

```text
CitiBike_JC_202609_EDA.py          Run the full EDA or its VS Code cells
CitiBike_JC_202609_EDA.ipynb       Notebook with saved analysis outputs
JC-202609-citibike-tripdata.csv/
  JC-202609-citibike-tripdata.csv  Original supplied raw CSV, unchanged
docs/                            Project status, data provenance and limitations
output/citibike_eda/
  figures/                       All 13 original EDA PNG figure panels
  whatsapp/                      Four shorter phone-friendly summary pictures
  *.csv                          Cleaning, flow, station and forecast tables
  cleaned_september_trips.csv.gz  Lossless compressed derived trip table
  analysis_manifest.json         Raw-data SHA-256, counts and software versions
  EDA_Findings_and_Project_Options.md
  build_mobile_poster.py          Source for the long summary poster
  split_whatsapp_poster.py        Source for its four-picture version
  WhatsApp_Team_Message.txt       Draft team update, not sent automatically
output/pdf/                      Original long poster in PNG/JPG/PDF formats
requirements.txt                 EDA dependencies
```

The compressed derived table preserves the full exported CSV while keeping the Git repository smaller. Running the EDA recreates the uncompressed local CSV. The source directory happens to end in `.csv`; the actual data file is inside it.

Course lecture slides, assignments, solutions, reference books, private chat transcripts, environment files and temporary previews are excluded.

## Run the EDA

Use Python 3.12 and a virtual environment. For example, from the repository root in Windows PowerShell:

```powershell
py -3.12 -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -r requirements.txt
& ./.venv/Scripts/python.exe CitiBike_JC_202609_EDA.py
```

Alternatively, open the notebook and choose the same environment as its kernel. The script locates the raw file relative to its own location, writes tables under `output/citibike_eda/`, and saves plots under `figures/`. Notebook cells show charts inline; a terminal run saves them to disk.

To rebuild the optional posters, also install `pillow`, `reportlab` and `pypdfium2`, then run:

```powershell
& ./.venv/Scripts/python.exe output/citibike_eda/build_mobile_poster.py
& ./.venv/Scripts/python.exe output/citibike_eda/split_whatsapp_poster.py
```

The poster builders currently use Windows Arial font files. Their full reproducibility on another operating system requires changing the font paths.

## Validation and next steps

The full EDA ran successfully and all reconciliation assertions passed. They check source-row accounting, the complete station-hour grid, event counts, net-flow identities and separation of forecast training/test timestamps. The forecasting exercise trains on 1-20 September and tests on 21-30 September; it is an exploratory baseline, not evidence of annual generalization.

Next: choose and audit the modeling dataset, define one clear optimization problem, collect or label missing inputs, implement the three policy baselines, and report sensitivity, limitations and practical implications. See [the meeting checklist](docs/PROJECT_STATUS.md).
