# Temporary integration results

These files belong to the isolated integration branch. They are retrospective experiments on 6–19 April 2015, not a new sealed test or final operator financial results. See the [executed report](../../../docs/INTEGRATION_REVIEW_2026-11-22.md) and [methods and reproduction commands](../../../docs/INTEGRATION_METHODS_2026-11-22.md).

| File | Contents |
| --- | --- |
| artifact_reconciliation.csv | Previous published demand outputs versus the latest PR #2 producer: three artifact versions, two distinct cases |
| matched_validation.csv | Historical/hybrid errors on the same fully observed hidden windows |
| validation_by_origin_group.csv | Validation split by observed origin-availability group |
| station_pair_costs.csv | Directed road kilometres, driving minutes and Stage 1 USD per moved bike |
| daily_policy_comparison.csv | 84 evaluations: two demand cases × 14 dates × three policies |
| aggregate_policy_comparison.csv | Stage 1 policy totals by case |
| conditional_route_comparison.csv | 56 route checks; incomplete routes have no full-day cost |
| route_cost_sensitivity.csv | Paid-span versus productive-time route repricing, with paired baseline differences |
| aggregate_route_comparison.csv | Route totals with priced-day counts and Stage 1 gains on the same days |
| break_even_costs.csv | Daily total/variable cost per moved bike supported by incremental allocated service value |
| additional_sensitivity.csv | Equal-service budget and closing-stock checks, first evaluation date only |
| cost_configuration.json | Adopted inputs, source/proxy notes and derived metric coefficients |
| run_manifest.json | Executed software, inputs, original run source hashes, solver statuses/gaps and scope |
| post_run_checks.json | Subsequent invariant checks and publication source hashes; original run hashes remain intact |
| evidence_manifest.json | SHA-256 of the other files in this folder |

Download the two full model-ready demand outputs from the existing [case-output folder](../demand_estimation_cases_2026-11-22/):

- [Historical demand CSV](../demand_estimation_cases_2026-11-22/historical_demand_station_hour.csv), also [gzip](../demand_estimation_cases_2026-11-22/historical_demand_station_hour.csv.gz).
- [Hybrid demand CSV](../demand_estimation_cases_2026-11-22/estimated_demand_station_hour_hybrid.csv), also [gzip](../demand_estimation_cases_2026-11-22/estimated_demand_station_hour_hybrid.csv.gz).

The latest producer reproduces these values; separate duplicate copies are unnecessary. Generated minute audits, validation targets and detailed dispatch/state tables can be rebuilt using the methods guide and are kept under ignored `tmp/`. Stage 1 and Stage 2 price the same operation; their costs must not be added. Physical model units are metric and money is USD.
