# Project status - 22 November 2026

The [pipeline on main](SF_Bikeshare_Project_Pipeline_Report.md) is the team's main reference, as explicitly designated by Carlo. Its supporting reviews record outstanding report/model limitations alongside the completed work.

Routing update: [Joohee's exact reported plans and ZIP](../output/sf_bikeshare/optimization_14days_2026-11-22/EXACT_PLAN_AUDIT_README.md) are now published and independently checked. They reproduce the 766 bikes and USD202.316 Stage 1 gain; all 133 active hours pass conditionally at one-minute setup. Route-cost changes reproduce -USD878.71/-USD4,191.83. The [v2 review](FINAL_REPORT_V2_REVIEW_2026-11-22.md) lists four remaining interpretation edits; Carlo's different re-solve remains separate.

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

The base results and exact-plan conditional route/cost evidence reconcile. The final PDF v2 implements most earlier corrections. Four remaining interpretation edits are in the [current v2 review](FINAL_REPORT_V2_REVIEW_2026-11-22.md): finite-gap gains, route-level ranking, joint cost/service dependence and benefit-bias inference. Source result tables remain unchanged.

No Google Doc was edited. No full cross-city/time robustness study or verified cash-profit result is claimed. The latest pipeline Markdown supersedes the earlier planning PDF/poster.
