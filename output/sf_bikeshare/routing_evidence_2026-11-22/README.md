# Saved re-solved routing evidence

**These are Carlo's separate re-solved allocations, not Joohee's exact report schedules.** See the [routing correction and report-ready wording](../../../docs/ROUTING_EVIDENCE_RECTIFICATION_2026-11-22.md).

The 168 detail files contain historical and hybrid cases, 14 dates each, and optimized/rule-based policies. Each date/policy has:

- `*_transfers.csv`: fixed saved station-pair/hour relocation instructions.
- `*_route_hours.csv`: conditional checker status for each hour.
- `*_route_events.csv`: saved pickup/drop events, travel/setup/handling times and locations. A no-move day has an empty events CSV. After a chain fails, later independently passing hours do not constitute a continuous full-day route.

Browse the [historical files](historical/) or [hybrid files](hybrid/). The exact original report transfers were not supplied. Old PR #1 artifacts remain available at their [original commit](https://github.com/carloida/DBA5103_finalproject/tree/244dda807805acbd28b33c56292e6eecb1de936a/output/sf_bikeshare/optimization), with different demand/pilot provenance.

| File | Meaning |
| --- | --- |
| schedule_comparison.csv | Reported versus re-solved daily bike totals. Equal totals are not proof of identical instructions; exact_report_plan_verified stays False. |
| route_day_summary.csv | Replay/rechecked status and estimated costs of the saved plans only |
| aggregate_recheck.csv | Counts separate active and no-move days, plus cost changes on the same priced subset |
| source_daily_policy_comparison.csv | Unchanged original re-solve summaries, including the corresponding no-move baselines |
| source_conditional_route_comparison.csv | Unchanged original conditional route summaries |
| source_cost_configuration.json | Cost proxies and assumptions used for this separate re-solve |
| source_run_manifest.json | Original run provenance and input/source hashes, preserved as run at the time |
| manifest.json | Downloadable file hashes and fixed-plan recheck scope |

Historical optimized checks pass on 13 of 14 calendar days, including five no-move days: eight of nine active days pass. The rule passes three of fourteen days. Cost repricing on the 13 priced optimized days gives -USD703.25 with productive-activity labour and -USD3,782.26 with paid-span labour. Productive activity includes driving, handling and setup. These are estimated scenarios, not observed expenses or certified worker shifts, and not a direct repricing of the report's exact USD202 result.

`python sf_bikeshare/check_published_routing.py` verifies this release without an allocation re-solve. The package was copied from saved run files; Joohee's original result tables were not modified. Physical units are kilometres, minutes/hours and bikes; currency is USD.
