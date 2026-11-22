# Final report v2: numerical verification and remaining edits

Reviewed the supplied `DBA5103_Final_Report v.2.pdf` (34 pages), its extracted text and rendered pages, and Joohee's original `route_audit_exact_plans.zip`. The PDF fingerprint is recorded in the [exact-plan audit manifest](../output/sf_bikeshare/optimization_14days_2026-11-22/exact_plan_audit_manifest.json). The PDF and Google Docs were not edited. Only the explicitly requested audit package and verification/supporting files are published here.

## Main finding

The original missing-schedule gap is **closed**. The exact transfers reproduce the report's historical 14-day service/contribution totals and all supplied station-hour states. The original conditional certificates validate for the stated travel/setup/handling assumptions. Detailed route-cost figures also reproduce independently. The study can be presented as a conditional retrospective OR benchmark, with a few final wording edits below. No allocation re-solve is needed for those edits.

## Verified corrections

| Topic | PDF location | Review outcome |
| --- | --- | --- |
| Exact reported schedules | Sections 5.3 and 7.2, pp. 14-15 and 20 | Fixed plans now supplied and independently replayed: 766 bikes; 42 policy-day state/result tables match |
| Optimized one-minute route check | Section 7.2, p. 20 | All 133 active hours on 9 active days pass conditionally; five additional days have no moves |
| Two-minute sensitivity | Section 7.2, p. 20 | 29 uncertified hours on three days, as reported |
| Rule route status | Section 7.2, p. 20 | 3/14 days pass at one minute, 1/14 at two minutes; 179/249 active hours uncertified at one minute |
| Exact-plan route costs | Section 7.2, pp. 20-21 | USD2,400.00 productive-activity cost; changes -USD878.71 / -USD4,191.83 reproduce the rounded -879/-4,192 |
| Separate re-solve | Section 7.2, pp. 20-21 | Distinct allocation, 13 priced days and -703/-3,782 are clearly identified |
| USD0.50 penalty | Section 6.4, p. 18 | Table now -USD25; text correctly identifies -USD24.79 and finite solver tolerance |
| Proportional service | Sections 4.4/4.6/6.5, pp. 10-13 and 19 | FCFS claim replaced in the main narrative; casual-heavy station preference acknowledged |
| Information advantage and daily resets | Sections 4.6/4.7/6.1/7.3 | Whole-day look-ahead, A9 resets and non-strict benchmark interpretation are disclosed |
| Cost scenarios | Section 7.1, p. 19 | Hire/handling +/-50%, distance +/-33%; Low/Base/High labels corrected |
| Diversion | Abstract and Section 7.3, pp. 2 and 21-22 | Now explicitly describes a descriptive excess-return ratio, not identified individual diversions |
| Operational limits | Sections 5.3/7.2/7.3 | Depot, shifts, parking/customer timing and A10 limitations are acknowledged |
| Front matter | p. 1 | Team names/IDs and AI declaration are present; not republished in this audit |

The 2.7 figure is 766/288, **bikes per transfer instruction**, not time- or distance-weighted onboard truck load. The larger-load comparison remains an assumption/scope discussion, not a measured truck-loading statistic.

## Four final wording changes before sign-off

1. **Section 7.1, p. 19: qualify “the optimizer's gain is never negative.”** This still conflicts with the returned -USD24.79 solution in Section 6.4. Replace with: “The exact mathematical optimum cannot be worse than the feasible no-rebalancing baseline. A finite-gap returned incumbent can be, as the USD0.50 penalty scenario shows.”

2. **Section 7.2, p. 21: remove the unverified full route-cost ranking claim.** The sentence saying the ranking is unaffected because the rule has more scattered moves is not established by complete, equally feasible 14-day routes: most rule days are uncertified and not fully priced. Replace with: “The optimized policy outperforms the occupancy rule under the Stage 1 scenarios tested. A full route-cost ranking over all 14 days is not established because most rule-based days fail the conditional routing check.”

3. **Conclusion, p. 23: let both service value and operating costs determine viability.** Replace “that choice, not the truck cost” with “both that service valuation and the route/operating costs.” Qualify the earlier two-thirds-of-a-member-trip threshold with “under the Stage 1 cost approximation.” The detailed base route-cost scenarios are negative at the same USD0.88 penalty, so the Stage 1 threshold is not a demonstrated route-level break-even.

4. **Section 3.2, p. 7: remove the remaining benefit-bias inference.** The new wording still infers that historical pre-outage underprediction suggests benefits are not overstated. Hidden available windows do not identify the direction of bias in actual outage demand or intervention benefit. Replace with: “Both methods underpredict the observed pre-stockout windows. The direction of bias during actual stockouts, and its effect on estimated rebalancing benefits, remains unknown.”

These edits change interpretation, not data, code or numerical experiments.

## Small accuracy/formatting improvements

- Section 3.1, p. 5, and the opening-stock parameter table still say “last valid snapshot.” Use “latest preceding snapshot, accepted only if valid and fresh.” All main-case midnight stocks are fresh, so the reported numerical initialization does not change.
- Section 7.2, p. 20: call 2.7 “bikes per transfer instruction.” Multiple instructions can share a truck route; it is not the observed average onboard load or proof that each transfer creates an independent truck trip.
- A3, p. 13: use “some riders may dock nearby” rather than the unqualified “in reality most.” The empirical comparison is descriptive. Section 7.3 already gives the appropriate caveats.
- The depot/truck-inventory extension on p. 22 could enable batching and lower costs; it has not been tested here and is not a guaranteed improvement or the only cause of small transfers. “Could” is the appropriate wording.
- The weighted epsilon term on p. 13 is transparent in the equation; “small weighted cost preference” is more precise than implying a strict lexicographic tie-break.
- The document has 34 total pages; main text ends on p. 24, references occupy pp. 25-27 and appendices pp. 28-34. The supplied guideline's 8-14 pages is indicative, not a strict cap. Consider tightening pagination and the sparse final narrative/reference pages if time allows. Rendered equations/tables were inspected; no broad clipping or missing-glyph defect was observed.

## Reference files

- [Download original ZIP and exact audit data](../output/sf_bikeshare/optimization_14days_2026-11-22/EXACT_PLAN_AUDIT_README.md)
- [Independent route-cost CSV](../output/sf_bikeshare/optimization_14days_2026-11-22/exact_plan_route_costs.csv)
- [Independent replay CSV](../output/sf_bikeshare/optimization_14days_2026-11-22/exact_plan_replay_checks.csv)
- [Audit provenance and SHA-256](../output/sf_bikeshare/optimization_14days_2026-11-22/exact_plan_audit_manifest.json)

Run `python sf_bikeshare/check_exact_report_routing.py` to repeat fixed-plan replay and certificate validation. It does not solve another allocation or search for a replacement route.
