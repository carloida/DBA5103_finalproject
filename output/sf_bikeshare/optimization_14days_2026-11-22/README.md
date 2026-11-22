# Supplied 14-day results from Joohee

These are Joohee's completed runs, imported unchanged from Drive. See the [handoff review](../../../docs/JOOHEE_HANDOFF_2026-11-22.md) for file descriptions, checks, cost assumptions and dependency notes. No experiments were rerun for this upload.

**Exact routing remains unverified:** this handoff contains aggregate policy tables, not the original station-pair/hour transfer plans. The [published routing evidence](../../../docs/ROUTING_EVIDENCE_RECTIFICATION_2026-11-22.md) is for Carlo's different re-solved allocations and must not be used as a certificate for these reported plans. The unchanged routing fields remain False.

- [Historical policies](historical_daily_policy_comparison.csv)
- [Hybrid policies](hybrid_daily_policy_comparison.csv)
- [Observed-trip policies](observed_daily_policy_comparison.csv)
- [Fixed-schedule cost repricing](fixed_schedule_cost_sensitivity.csv)
- [Four first-date reoptimizations](reoptimization_sensitivity.csv)
- [Fixed-schedule break-even thresholds](break_even_fixed_schedule.csv)
- [Additional penalty, budget and diversion experiments](../extra_experiments_2026-11-22/README.md)

The base scenario uses USD60 per truck-day, USD1 per moved bike plus USD0.30/km divided by an average load of 15. These files are separate from the updated-cost experiments in `integration_review_2026-11-22`. Costs and contributions are Stage 1 estimates, not verified cash profits or route-feasibility results.
