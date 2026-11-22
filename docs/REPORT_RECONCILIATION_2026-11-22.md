# Report reconciliation before final submission

Reviewed against the report text supplied by Carlo on 22 November, the published demand snapshots, Joohee's unchanged CSVs and the actual source code. Google Docs were not edited. This review does not rerun the experiments or replace the supplied CSVs.

## Demand and base results are aligned

The team confirmed historical base, hybrid sensitivity and observed-only lower-demand comparison. Fu Yan's latest producer reproduces both published demand CSVs. Both methods subtract trips served during each outage once before allocating remaining missed demand to hours. The historical base is not Hong Jin's earlier own-hour input.

The historical result table reconciles: 766 bikes moved, 748.58 extra pickups served, 668.16 fewer failed returns and USD202.316 additional Stage 1 modeled contribution. These are retrospective results under the report's USD60/day, USD1/bike and USD0.30/km assumptions, not the separate updated-cost experiment.

## Corrections for the manual final edit

| Draft location | Finding | Required correction |
| --- | --- | --- |
| Abstract; Sections 7.3 and 8 | The excess-neighbour-return ratio is 0.8605, but intended destinations and individual diversions are not observed. | Say the excess is **equivalent to about 86% of estimated missed returns**, consistent with possible diversion. Do not say 86% of riders were shown to divert or that most failed returns are proven detours. |
| Sections 3.1 and 4, opening stock | “Last valid snapshot” can imply skipping an invalid latest snapshot. | Select the **latest preceding snapshot, then check validity and freshness**. The 90-second cutoff is an analytical rule. |
| Section 3.2 | Negative pre-stockout prediction bias does not prove conservative demand or conservative policy benefits during actual outages. | Say that both methods underpredict the observed pre-outage test windows; the direction of bias in actual unmet demand and policy benefits remains unknown. |
| Sections 3.3 and 4, travel cost | USD0.30/km is the executed scenario; the difference above USD0.2352/km vehicle cost is an assumed allowance, not demonstrated full driving-labour coverage. | Label it an **approximate travel-cost scenario**. Explicit travel-time labour and paid driver spans are excluded from these reported runs and assessed separately. |
| Section 6.4, Table 5, penalty USD0.50 | Supplied optimizer contribution is USD14,517.221 versus USD14,542.007 for no rebalancing. | Replace “approximately zero” with **−USD24.79** (rounded −USD25). This is a returned incumbent within the solver's tolerance; the feasible no-rebalancing policy performs better. |
| Sections 6.4 and 7.1 | The exact optimum cannot be worse than a feasible baseline, but a finite-gap returned incumbent can be. Relative gap applies to the full objective, not incremental gain. | Distinguish the mathematical optimum from the recorded incumbent; do not certify a USD0.50–0.65 break-even threshold from these runs. |
| Sections 7.1 and 8, cost scenarios | F and h change by ±50%, but k changes 0.30 to 0.20/0.40, or ±33.3%. | Say **combined low/base/high scenarios**, and list the coefficients rather than claiming every cost changes by ±50%. |
| Sections 6.5 and 7.3 | The code allocates served pickups proportionally by rider mix; it does not simulate event-level FCFS. | Use **work-conserving aggregate service with proportional rider allocation**. The model cannot choose riders within a station-hour, but can still favour locations with higher casual shares. |
| Section 6.5 | The lost-trip objective includes 0.001 × redistribution cost. | Describe a **small weighted cost preference**, not a strict lexicographic tie-break or a purely cost-free secondary objective. |
| Sections 5.3 and 7.2 | Supplied result rows have route_feasibility_checked=False; route schedules/certificates were not in Joohee's handoff. | Do not state that all reported plans are executable. Retain the claimed route pass counts only if the exact schedules, settings and route-audit files are supplied. |
| Section 7.3, perfect information | A finite-gap solution of a restricted graph with approximate returns is not a certified upper bound for a real dispatcher. | Call it a **retrospective perfect-information benchmark**; reserve upper-bound claims for a proven bound under identical feasible sets. |
| Whole report | The five additional city/time packages are prepared observations, not completed optimization experiments. | Report the completed demand/cost/penalty/budget checks; keep cross-city/time runs as future work. The 6–19 April dates are retrospective evaluation, not a sealed test. |

At penalty USD0 and USD0.30 the supplied optimizer returns no-rebalancing plans. With finite gaps this describes the returned solutions, rather than proving that no alternative active plan could improve the objective by a small amount.

## Suggested replacement for the economic and routing conclusion

For the full corrected route paragraph, exact schedule differences, active-day counts, cost denominator and downloadable saved route files, use the [routing evidence correction](ROUTING_EVIDENCE_RECTIFICATION_2026-11-22.md). The separate re-solve's 13/14 conditional passes do not certify Joohee's reported allocations; five passes are no-move days. Its -USD703.25/-USD3,782.26 scenarios cover thirteen priced days and estimated costs, not fourteen days of the report's exact plans or actual expenses.

“Under the report's approximate Stage 1 cost scenario, the historical-demand solution improves modeled contribution by USD202 over 14 retrospective evaluation days. This gain uses allocated trip values and an assumed failed-return penalty; it is not cash profit. Actual route costs, paid driving time, shift requirements and within-hour station inventory have not been certified for the supplied schedules. Separate route-cost experiments show that these assumptions can change the sign of modeled benefits.”

The [project pipeline](SF_Bikeshare_Project_Pipeline_Report.md) records the agreed inputs, commands, owners and result paths. The [Joohee handoff review](JOOHEE_HANDOFF_2026-11-22.md) and [updated-cost experiment](INTEGRATION_REVIEW_2026-11-22.md) preserve the evidence for their respective scopes.
