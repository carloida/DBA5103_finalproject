# Extra experiments for the final report (Joohee, 22 Nov 2026)

All runs use the 34 SF stations, 14 evaluation days (6–19 April 2015), base costs
(USD 60/truck-day, USD 1.00/bike handling, USD 0.30/km, average load 15, 15 bikes/hour, 1 truck)
and the historical demand case (`demand_estimation_cases_2026-11-22/historical_demand_station_hour.csv`).

| File | Report section | Produced by |
|---|---|---|
| `penalty_sensitivity.csv` | 6.4, Table 5 | `sf_bikeshare/jh_run_experiments.py penalty ...` (penalties 0, 0.3, 0.5, 0.65, 0.88, 4.5) |
| `lost_trip_budget.csv` | 6.5, Table 6 | `sf_bikeshare/jh_run_experiments.py losttrip ...` (budgets 75, 90, 120, 150, 200 USD/day) |
| `diversion_episodes.csv` | 7.3 | `sf_bikeshare/jh_diversion_check.py` |

The three-policy runs for Sections 6.1–6.3 and 7.1–7.2 are in `../optimization_14days_2026-11-22/`
(Hong Jin's `hj_multiday_sensitivity.py` with `--time-limit 30` and each demand file).

Example (from the repository root):

    python sf_bikeshare/jh_run_experiments.py penalty output/sf_bikeshare/demand_estimation_cases_2026-11-22/historical_demand_station_hour.csv output/sf_bikeshare/extra_experiments_2026-11-22/penalty_sensitivity.csv
