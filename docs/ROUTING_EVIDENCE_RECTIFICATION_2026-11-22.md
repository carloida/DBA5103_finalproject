# Routing evidence correction and exact scope

**Later evidence received:** Joohee's [exact plans and original ZIP](../output/sf_bikeshare/optimization_14days_2026-11-22/EXACT_PLAN_AUDIT_README.md) are now provided and independently verified, including the -USD879/-USD4,192 scenarios. The missing-evidence discussion and provisional paragraph below describe the earlier review. Current report edits are in the [v2 review](FINAL_REPORT_V2_REVIEW_2026-11-22.md).

Fu Yan's review correctly identifies an open gap: merged source code and a successful conditional check on a separate allocation do not certify the exact plans behind the report's USD202.316 result. This correction adopts the conditional-evidence option now. Joohee's original result CSVs and their `route_feasibility_checked=False` fields remain unchanged. No new allocation optimization was run for this correction. Google Docs were not edited.

## What was merged and what was excluded

PR #1 is a merge ancestor of main, but merge `0dd599e` intentionally retained the reviewed integration tree. Four Hong Jin source files were integrated; his earlier generated demand/pilot outputs were not copied into the current release. The earlier statement that his PR was merged should not be read as saying every generated file from that branch exists in main's current tree.

The original generated files remain downloadable at [Hong Jin's immutable PR #1 commit](https://github.com/carloida/DBA5103_finalproject/tree/244dda807805acbd28b33c56292e6eecb1de936a/output/sf_bikeshare/optimization). These include earlier transfer and route CSVs, with an earlier demand input and pilot scope. They are not the missing exact 14-day schedules behind Joohee's report and are not restored as current results.

The [new downloadable evidence package](../output/sf_bikeshare/routing_evidence_2026-11-22/README.md) publishes the **saved Carlo re-solved plans**, their route hours and events, source summaries, schedule comparisons and recheck manifest. These artifacts previously lived in the ignored temporary run folder. They have not been relabelled as Joohee's plans.

## Which schedules differ

Historical optimized bikes moved:

| Date | Reported allocation | Carlo's re-solved allocation |
| --- | ---: | ---: |
| 6 April | 88 | 87 |
| 8 April | 95 | 94 |
| 15 April | 103 | 105 |
| 16 April | 103 | 95 |
| 17 April | 68 | 66 |

The other nine optimized daily bike totals match. Rule-based bike totals match on all 14 days. **Matching daily totals do not establish identical station-pair/hour transfer rows.** Without the report's original transfer files, exact-plan identity is unverified on every day, including days with equal totals.

The re-solve also used different cost coefficients: pair-specific driving labour and handling USD0.985667/bike rather than the report's USD1.00/bike plus USD0.30/km scenario. Solver tolerances and alternate incumbents can change allocations, but the differences here cannot be attributed solely to tolerance while the objective coefficients also differ.

## What the conditional route checks establish

The saved plans use one truck, capacity 25 bikes, one minute per load/unload operation, one minute per stop, estimated directed road travel times, fixed pickup-before-delivery jobs and inter-hour location continuity. The initial approach/depot is free. Results are conditional on these assumptions.

| Historical policy | Calendar days | Days with moves | No-move days | Conditional pass days | Active pass days | Uncertified active days |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Re-solved optimized | 14 | 9 | 5 | 13 | 8 | 1 |
| Rule-based | 14 | 14 | 0 | 3 | 3 | 11 |

The optimized failure is 15 April. Thus “13 of 14 days pass” includes five days requiring no route; among nine active days, eight pass. A failed sequential chain is not proof that every alternative full-day route is infeasible.

Passing does not certify depot legs, shifts/overtime/breaks, parking, station inventory at exact visit times, customer timing within an hour or the Stage 1 assumption that all deliveries are available at hour start. These checks are not a globally minimum-cost vehicle-routing solution.

## Cost correction and denominator

On the **same 13 conditionally priced historical optimized days**, using the re-solved allocation and its corresponding no-rebalancing baseline:

| Accounting basis | Additional modeled contribution |
| --- | ---: |
| Re-solved Stage 1 approximation, same 13 days | +USD135.19 |
| Estimated route costs, productive-activity labour | -USD703.25 |
| Estimated route costs, paid-span labour | -USD3,782.26 |

The report's +USD202.32 is a **different allocation and a 14-day total**; the above numbers are not a direct repricing of that exact report result. The negative route scenarios do show that the re-solved Stage 1 gain is sensitive to route-cost treatment.

“Productive activity” includes driving, loading/unloading and stop setup, not driving alone. “Paid span” includes waiting between the first assigned hour and last completion; it is not a verified worker shift. Vehicle/fuel/wage inputs and road times are proxies, not observed operator expenses. Use **estimated route-cost scenarios**, not “actual” or “real” route costs. Incomplete routes have no invented full-day cost. Stage 1 and Stage 2 costs price the same operation and must not be added.

## Earlier provisional report wording, superseded by the exact-plan audit

> A separate historical-demand allocation was re-solved using the updated cost configuration and subjected to conditional pickup-and-delivery route checks. Thirteen of fourteen calendar days passed, including five no-move days; eight of nine active optimized days passed. The rule-based case passed on three of fourteen days. These checks do not certify the exact allocations underlying the reported USD202.32 Stage 1 gain. On the thirteen conditionally priced optimized days, additional modeled contribution was -USD703.25 with productive-activity labour and -USD3,782.26 with paid-span labour. These are estimated-cost scenarios, with no depot, worker-shift or minute-by-minute station-inventory certificate. Operational executability and positive real-world contribution are therefore not established.

For a stronger exact-report check, Joohee/Hong Jin must supply the original 14-day transfer CSVs and their matching demand, parameters and run provenance. Apply the route checker to those fixed transfers and publish the route-hour/event outputs. Calling the allocation optimizer again would generate new evidence, not verify the original plans. Until that handoff exists, retain the qualified paragraph above and the unchanged routing flags.

## Download and verification

- [Saved plans, route hours/events and comparison tables](../output/sf_bikeshare/routing_evidence_2026-11-22/README.md)
- [Report schedules versus re-solve daily totals](../output/sf_bikeshare/routing_evidence_2026-11-22/schedule_comparison.csv)
- [Rechecked day-level status and costs](../output/sf_bikeshare/routing_evidence_2026-11-22/route_day_summary.csv)
- [Recheck aggregates](../output/sf_bikeshare/routing_evidence_2026-11-22/aggregate_recheck.csv)

Run `python sf_bikeshare/check_published_routing.py` from the repo root with the project's dependencies installed. It replays the published fixed transfers, rechecks routes and verifies stored files; it never solves an allocation MILP.
