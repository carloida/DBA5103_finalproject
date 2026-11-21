# Demand case comparison evidence

Prepared 22 November 2026. This compact snapshot supports the [comparison overview](../../../docs/SF_Bikeshare_Demand_Estimation_Case_Comparison.md), [Case A Historical](../../../docs/supporting/SF_Bikeshare_Demand_Case_A_Historical.md) and [Case B Hybrid](../../../docs/supporting/SF_Bikeshare_Demand_Case_B_Hybrid.md).

**This folder contains comparison results, not station-hour demand.** Both full demand outputs are now [downloadable in a separate provisional snapshot](../demand_estimation_cases_2026-11-22/README.md). Frozen V3 observations are unchanged. Fu Yan's incomplete producer bundle and Hong Jin's unmerged model code remain outside this publication.

## Files

| File | Contents |
| --- | --- |
| [demand_totals.csv](demand_totals.csv) | Six side/scenario totals; original v1 is context |
| [matched_validation.csv](matched_validation.csv) | Twelve class/side/horizon comparisons on identical fully available validation targets |
| [validation_by_origin_group.csv](validation_by_origin_group.csv) | Actual case predictors for all eligible, weekday peak and common-three-hour origins |
| [policy_comparison.csv](policy_comparison.csv) | 24 illustrative daily policy results |
| [optimized_policy_bounds.csv](optimized_policy_bounds.csv) | Eight feasible additional contributions, upper bounds, solver status/gaps/times |
| [pilot_parameters.json](pilot_parameters.json) | Exact common provisional model settings |
| [audit_summary.json](audit_summary.json) | Numerical audit, interface, validation issues and source-file fingerprints |
| [manifest.json](manifest.json) | Byte counts and SHA-256 hashes |

Methods are case_a_historical and case_b_hybrid. original_predecessor_v1 appears only as demand-total context. The hybrid uses a 30-minute preceding window, minimum 20 available minutes, and a first-elapsed-hour switch. Its three-hour scores evaluate that actual switch.

Subscriber/customer mean member/casual. Errors are trips per target window; bias is prediction minus observed hidden count. In matched_validation.csv, historical/hybrid columns are Cases A/B respectively.

## Validation and model interpretation

Rates use 9 February-5 April 2015; validation uses 6-19 April. Targets require full valid availability under the positive <=90-second snapshot-gap rule. Near-outage samples are selected and small; long windows overlap. These are reconstruction checks on observable targets, not ground-truth unmet demand or a fresh untouched test.

The reports explain chronology, target-completeness and hour-crossing problems in the originally supplied v2 short-window validation. Published comparison tables use the independent corrected definitions.

Policy dates are 6, 10, 11 and 15 April. Costs and trip allocations are provisional; quantities are expected service/inventory; routes are unverified. Contribution is allocated value minus redistribution cost and failed-return penalties, not cash profit.

Status zero means the solver met its termination tolerance; status one indicates a time-limited feasible incumbent. Historical 6 April has a 3.18% gap. Blank solver fields for baseline/rule simulations are not failed solves. A larger demand estimate or contribution does not establish estimator accuracy.

## Integrity and reproduction boundary

Read the compact tables directly from a cloned repository. Full source databases are unnecessary for inspection. Audit hashes identify original local files without publishing those files or workstation paths.

To reproduce demand generation, obtain the complete selected-case builder, observed inputs and episode/rate/validation exports. The v2 wrapper alone cannot run because its revised core is absent. This snapshot does not claim a production command or code merge. Final implementation and robustness-study work remain in the reports.

Original dataset terms still apply. Research and course PDFs are cited, not copied here.
