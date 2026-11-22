# Joohee's completed results handoff

Imported from the shared [github_upload_joohee Drive folder](https://drive.google.com/drive/folders/1Z8_gtGBwahZIVfOtBsJiadQGGWYPvZZS) into the temporary integration branch. All 13 supplied files are preserved byte-for-byte in their requested repository paths. No optimization or diversion experiment was rerun, no existing result set was overwritten, and Google Docs were not edited. Main and PRs #1/#2 remain unmerged.

The supplied report setup is historical base, hybrid sensitivity and observed trips as a lower-demand comparison. Importing these files does not make a new demand-case decision for Carlo.

## Code and dependencies

- [jh_lost_trips_model.py](../sf_bikeshare/jh_lost_trips_model.py): a copy of the allocation model extended with a lost-request objective and daily cost budget.
- [jh_run_experiments.py](../sf_bikeshare/jh_run_experiments.py): penalty/budget experiment runner, importing that model and Hong Jin's policy evaluator.
- [jh_diversion_check.py](../sf_bikeshare/jh_diversion_check.py): descriptive comparison of neighbouring-station returns during full-dock episodes against shifted-week windows.

Hong Jin's model/evaluator source from PR #1 and Fu Yan's producer from PR #2 are already present in this branch. A merge into main is not required to satisfy dependencies here. Scripts parse and the model/evaluator dependencies import successfully. The penalty/diversion runners execute experiments at top level, so they were inspected without importing or executing them.

## Supplied results

| File | Rows | Scope |
| --- | ---: | --- |
| [Historical daily policies](../output/sf_bikeshare/optimization_14days_2026-11-22/historical_daily_policy_comparison.csv) | 42 | 14 dates × 3 policies |
| [Hybrid daily policies](../output/sf_bikeshare/optimization_14days_2026-11-22/hybrid_daily_policy_comparison.csv) | 42 | Same dates and policies |
| [Observed daily policies](../output/sf_bikeshare/optimization_14days_2026-11-22/observed_daily_policy_comparison.csv) | 42 | Same dates and policies |
| [Fixed-schedule cost sensitivity](../output/sf_bikeshare/optimization_14days_2026-11-22/fixed_schedule_cost_sensitivity.csv) | 126 | Repricing existing schedules, not reoptimizing every case |
| [Reoptimization sensitivity](../output/sf_bikeshare/optimization_14days_2026-11-22/reoptimization_sensitivity.csv) | 4 | Four scenarios on 6 April only |
| [Fixed-schedule break-even](../output/sf_bikeshare/optimization_14days_2026-11-22/break_even_fixed_schedule.csv) | 14 | Missing thresholds on five zero-move days |
| [Penalty sensitivity](../output/sf_bikeshare/extra_experiments_2026-11-22/penalty_sensitivity.csv) | 252 | 14 dates × 6 penalties × 3 policies |
| [Lost-trip budget](../output/sf_bikeshare/extra_experiments_2026-11-22/lost_trip_budget.csv) | 84 | Baseline and five budgets per date |
| [Diversion episodes](../output/sf_bikeshare/extra_experiments_2026-11-22/diversion_episodes.csv) | 945 | 916 episodes with a placebo comparison |

Joohee's original [extra-experiments README](../output/sf_bikeshare/extra_experiments_2026-11-22/README.md) identifies the corresponding report sections and commands.

## Cost basis must stay explicit

These supplied runs use the earlier scenario:

$$
C_{\mathrm{supplied}}=60y+\sum_{ijt}\left(1.00+\frac{0.30d_{ij}}{15}\right)x_{ijt},
$$

with road distance in kilometres, USD costs, average load 15, throughput 15 bikes per hour and one available truck. They do not use the separate [updated-cost integration configuration](../sf_bikeshare/integration_cost_config.json), which has handling USD0.985667/bike and pair-specific vehicle plus driving-labour costs. The supplied experiment runner explicitly retains the earlier coefficients. Its published numbers have not been relabelled or converted into updated-cost results.

For the final report, the cost table, formula and numerical results need to identify the same scenario. This handoff adds the existing results; it does not establish that a rerun is needed or certify that the current Google Doc already reconciles these assumptions.

## Checks and interpretation

File sizes and hashes match the downloads. Daily keys/date coverage, demand totals against the published historical/hybrid outputs and observed V3, service accounting, financial accounting, penalties and budget limits pass table checks. Recorded daily optimized statuses are 0, with relative gaps below 1%; supplied replay errors are below 1e-4. These are inspections of supplied records, not independent reproductions of the solver runs.

All daily and extra-policy result rows say routing was not checked. This folder supplies no route certificate. The separate conditional routing experiments in [the integration review](INTEGRATION_REVIEW_2026-11-22.md) have different cost assumptions and must not be presented as certificates for Joohee's exact schedules.

The lost-trip model minimizes unmet pickups plus failed returns with an added 0.001 × cost preference. That weighted preference is not a strict lexicographic tie-break. The diversion analysis is descriptive, not a causal or fully independent estimate of rider substitution; its placebo selection and episode-resampling assumptions remain limitations. Source code is preserved rather than changed during this upload.

The [handoff manifest](JOOHEE_HANDOFF_MANIFEST_2026-11-22.json) records Drive provenance, SHA-256, file inventory, checks and limitations. The original report document was not included in the supplied folder and was not reviewed in this handoff.
