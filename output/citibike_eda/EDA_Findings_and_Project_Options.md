# Citi Bike EDA findings and project options

This analysis uses the supplied local trip file. Start with `CitiBike_JC_202609_EDA.ipynb` for the code, explanations and 13 figure panels. The source CSV is unchanged. The source hash and software versions are in `analysis_manifest.json`.

## Data coverage and cleaning

- Raw file: **106,628 trips**, 13 fields. **106,617 valid September-start trips** after the declared time rules.
- **108 origin IDs, 222 destination IDs**, 222 in the union. The service domain is the 108 observed JC/HB origin stations.
- **333 blank destination IDs** originally. **49** recovered using unique exact-name matches; **284** remain unresolved. Recovered IDs are flagged. Coordinates are not filled.
- **11 starts outside September**. Their September arrivals remain in the event view.
- **0 exact duplicate rows**, **0 conflicting ride IDs**; **0 nonpositive durations**.
- **37 trips over 24 hours** are flagged and retained, with a sensitivity comparison. No automatic outlier winsorization/deletion.
- Among September starts, **35 of 36 trips over 24 hours have unresolved end IDs**. Missingness and extreme duration are associated, so complete-case deletion can distort the duration profile. No cause is assumed.
- **274 known outside-domain arrivals**. Missing destinations and external endpoints prevent treating this as a fully observed closed system.
- Timestamps have no timezone metadata. Analyze clock times as recorded; no Singapore conversion. Calendar weekdays include holidays.

## Observed patterns

- Member share: **73.9%**; electric-bike share: **59.7%**; median duration: **6.40 min**.
- Three highest average weekday departure hours: **17:00, 18:00, 8:00**.
- Daily September-start counts range from **652 on 27 Sep** to **4,817 on 12 Sep**. Investigate causes; low days are not deleted.
- **96/108 stations** reverse the sign of average net flow between 07:00–09:59 and 16:00–18:59 on weekdays. Tiny reversals count; inspect magnitude and daily consistency.
- Largest monthly observed net outflow: **Oakland Ave [JC022], -216**. Largest net inflow: **River St & 1 St [HB609], +316**.
- Strongest minimum-magnitude AM/PM reversal: **Grove St PATH [JC115]**, morning **+72.8**, evening **-63.9 bicycles per weekday**.

These are descriptive patterns consistent with directional commuting. Trip purpose, empty/full stations and actual lost rentals are not observed. Cumulative net-flow graphs are not actual inventory trajectories.

## Recommended project direction

Lead with **optimization**. Start with a peak-window transportation/min-cost-flow redistribution model, then test a time-expanded or scenario-based extension if feasible. Compare no redistribution, a budget-matched greedy surplus-to-deficit policy and the optimized policy using identical stock/capacity/cost assumptions and held-out days.

The question could be: **How much can budget-limited bicycle redistribution reduce peak-period inventory pressure, and how robust is that plan to uncertain flows and operating assumptions?**

1. **LP/network flow:** strongest baseline connection to Lecture6. Decide bicycle transfers and target shortfalls. Study relocation limits, target buffers and cost sensitivity. Pure network structure supports LP integrality with integral data; do not assume extensions preserve it.
2. **Time-expanded LP:** model hourly inventory conservation and transfer timing, drawing on the container example in Lecture6. Initial stock, station capacity and transit lead times need evidence or labeled assumptions.
3. **Stochastic/SAA or robust optimization:** directly related to Lecture5, Lecture7 slides19–20 and Assignment3 Q1–2. Preserve dependence by using joint day scenarios. Use common first-stage decisions and held-out evaluation.
4. **Truck-routing MIP:** optional and substantially harder. Need road times, depots, truck capacities, shifts and loading times. Begin with a small station subset. Report bounds, gaps and runtime, not merely a route.
5. **ML + optimization:** optional forecasting layer, not required for a strong OR paper. Compare transparent profiles with count/tree models only after obtaining enough history. Evaluate both forecasting accuracy and downstream decision value. Full-network inventory DP has an impractically large state space.

## Exploratory forecasting check

Train 1–20 September; evaluate 21–30 September. Target: recorded station-hour departures, including zero-event hours. This is a small holdout, not robust evidence of seasonal generalization. Only these transparent forecasting baselines are fitted; no advanced ML model is included.

| method | station_hour_MAE | station_hour_RMSE | bias_predicted_minus_actual | test_station_hours |
| --- | --- | --- | --- | --- |
| Station + hour average | 0.969 | 1.663 | 0.224 | 25920 |
| Station + day type + hour average | 0.899 | 1.495 | 0.251 | 25920 |

## Missing inputs and claims to avoid

Trip records do not contain station capacities, initial stocks, redistribution logs, failed rentals/returns, truck costs or availability. Shortage reductions therefore need additional data or a clearly labeled simulation model. Current GBFS cannot reconstruct September inventory histories. Straight-line separation is not road/truck distance. Observed demand can be constrained by availability, and incoming boundary trips outside this extract may be missing. One month cannot establish annual seasonality or weather causation.

## Main files

- Notebook and matching Python script in the project root.
- `data_quality.csv`, `cleaning_audit.csv`, `flagged_records.csv`, `cleaning_sensitivity.csv` document data handling.
- `cleaned_september_trips.csv` preserves original columns plus parsed/resolved fields and flags.
- `station_hourly_observed_flows.csv` has a complete 108 × 720 grid; `station_day_pressure.csv` gives replay proxies, not measured shortages.
- `station_summary.csv`, `weekday_peak_window_flows.csv`, `morning_evening_reversal.csv`, `observed_od_counts.csv`, and forecasting tables support later modeling.
- `figures/` contains the 13 PNG panels, also embedded in the notebook.

## Source references

- Supplied local CSV: `JC-202609-citibike-tripdata.csv\JC-202609-citibike-tripdata.csv`. Every empirical number above is computed from it.
- [Official Citi Bike system-data description](https://citibikenyc.com/system-data), accessed 13 November 2026: field definitions and pointer to GBFS. No external data merged.
- Local `Lecture4 DualitySensitivity.pdf`, slides24–41; `Lecture5 LPCases.pdf`; `Lecture6 Network.pdf`, slides17–29 and44–61; `Lecture7 IP.pdf`, slides14–37 and63–79; `Lecture8 DP.pdf`; `Assignment_3.pdf`, Q1–2; and `Project_Guideline.pdf`, pp1–4.
- Reference-book map: local Hillier/Lieberman, seventh edition (2001), chapters8–9,11–12,22; Bradley/Hax/Magnanti chapters8,9,11; Bertsimas/Tsitsiklis (1997), supplied chapters1–5. These support the stated model families; verify original passages when writing the final paper.

The guideline emphasizes a clear model, defensible methodology, sensitivity/limitations and interpretation. It permits an applied problem with explicit assumptions; a machine-learning component is not necessary.
