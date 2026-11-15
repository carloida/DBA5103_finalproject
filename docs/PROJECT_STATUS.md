# Project status - 15 November 2026

## Completed

- Audited and analyzed the supplied September 2026 JC/HB Citi Bike file.
- Saved the Python script, executed notebook, cleaning audit, manifest, flow tables and forecast baselines.
- Generated 13 original figure panels and a four-picture phone summary.
- Identified data limitations and possible LP, network-flow, time-expanded and integer-programming extensions.
- Fixed terminal chart warnings, terminal narrative display and data lookup from other working directories.
- No redistribution optimizer, truck-route solver, profit model or measured shortage estimate has been implemented yet.

## Initial direction

Use observed station flows to motivate a budget-limited bicycle redistribution model. Compare no redistribution, a rule-based/greedy policy and an optimized policy under common assumptions. Examine costs, inventory pressure and robustness across days.

## Dataset decision remains open

The team suggested SF Bay Area Bike Share as a candidate for its reported historical station-status and capacity information, with weather as a possible additional input. These details still need verification against the actual downloaded files. No SF data are included yet.

If that dataset is suitable, retain Citi Bike as descriptive motivation and use SF data for modeling. Keep the systems, periods and financial assumptions clearly separated. Empty/full station observations improve visibility of availability, but do not directly measure unmet customer demand.

Supply Chain Logistics Problem Dataset (Brunel/Kaggle) was raised as a backup topic. It has not been selected or evaluated here.

## Monday evening meeting - 16 November 2026, Singapore time

1. Choose the dataset: retain Citi Bike, use SF Bay Area Bike Share, or pursue another option.
2. Confirm the exact question and decision horizon: initial redistribution, repeated hourly moves, or a capacity investment decision.
3. Audit coverage: timestamps, station identifiers, capacities, status gaps, outages and alignment between trip/status records.
4. Decide how to estimate rental/return demand during empty/full periods; distinguish observations from assumptions.
5. Select a manageable station subset and define stocks, dock limits, relocation budgets and transfer timing.
6. Collect cost inputs or agree on transparent ranges for relocation, labor, vehicles, maintenance and additional equipment.
7. Specify policy baselines, a chronological evaluation split and sensitivity scenarios.
8. Assign model, data, implementation and writing tasks after scope is agreed.

No exact meeting time has been recorded.

## Course requirements to address

Based on the supplied DBA5103 project guideline:

- Explain motivation, the practical problem, the data/process and the assumptions.
- Define a mathematical model, objective, decision variables and every constraint.
- Identify the problem class and explain the algorithm/methodology and course connections.
- Explain results, policy implications, sensitivity and limitations; cite relevant sources.
- Attach implementation code as an appendix and write a focused, consistently formatted report.
- The guideline suggests roughly 8-14 narrative pages, but prioritizes a clear point over length and imposes no strict page limit. Its suggested formatting is 12-point Times, double spacing and one-inch margins; other consistent, clear formats are allowed.

The original course PDFs remain in the local course folder and are not redistributed here.
