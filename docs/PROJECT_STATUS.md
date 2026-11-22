# Project status - 22 November 2026

The [pipeline on main](SF_Bikeshare_Project_Pipeline_Report.md) is the team's main reference, as explicitly designated by Carlo. Its supporting reviews record outstanding report/model limitations alongside the completed work.

Routing update: [Carlo's saved re-solved transfer and route files](ROUTING_EVIDENCE_RECTIFICATION_2026-11-22.md) are published with qualified counts and estimated route-cost results. They do not verify Joohee's exact report schedules; original report flags remain False. Obtain her fixed transfer files for an exact-plan check, or use the documented conditional-evidence paragraph.

The team confirmed historical demand as the base and hybrid as sensitivity. Joohee confirmed that the report uses the published historical/hybrid CSVs, plus observed trips as a lower-demand comparison. Both estimated cases subtract trips already served during outages. See the [complete pipeline](SF_Bikeshare_Project_Pipeline_Report.md).

## Completed and published

- Carlo's frozen V3 observations, 34 SF stations x 70 days x 24 recorded slots, with metric inputs and the minute supplement.
- Fu Yan's complete historical/hybrid producer, support fallback tests and matched validation; both outputs reproduce the published snapshots.
- Hong Jin's allocation model, rule policy, independent replay and conditional route-check source. Earlier generated own-hour demand/results from PR #1 are superseded and excluded from the current report inputs.
- Joohee's unchanged 14-day historical, hybrid and observed policy tables; penalty, budget, fixed-schedule repricing, selected first-day reoptimizations and diversion outputs. No experiments were rerun for her file upload.
- A separate updated-cost integration experiment, clearly labelled apart from the report scenario.
- Five additional city/time observed-data packages, prepared for possible robustness work. They are not completed model experiments.

## Owners and remaining work

| Owner | Remaining work |
| --- | --- |
| Carlo | Manual final report edit, repository/data consistency and corrected conclusion wording |
| Fu Yan | Ensure Section 3 demand wording matches the published historical base, served-trip subtraction, support rules and validation scope |
| Jason | Finalize Sections 1–2 (Introduction and Literature Review); ensure Section 3.3 cost-source discussion identifies the executed approximate USD0.30/km scenario and distinguishes allocated trip values from cash |
| Joohee | Check formulation/assumptions against code; qualify route, service-allocation, diversion and perfect-information claims |
| Hong Jin | Check reported solver gaps, the USD0.50 penalty result and which exact route-audit artifacts support the draft |

The base result table reconciles, but the report is not yet fully reconciled. [Required corrections](REPORT_RECONCILIATION_2026-11-22.md) include -USD24.79 at penalty USD0.50, nonuniform cost-scenario percentages, missing route evidence and causal overinterpretation of the diversion ratio. The original source/results remain unchanged. See the [end-to-end review](PIPELINE_END_TO_END_REVIEW_2026-11-22.md) for objective alignment and priority actions.

No Google Doc was edited. No full cross-city/time robustness study or verified cash-profit result is claimed. The latest pipeline Markdown supersedes the earlier planning PDF/poster.
