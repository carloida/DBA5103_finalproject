# Exact historical report plans: verified conditional routing

Joohee supplied the original historical plan files and conditional route checks underlying the report's 766 moved bikes and USD202.316 Stage 1 gain. All **187 supplied CSVs and the original ZIP are published unchanged**. This closes the earlier exact-plan provenance/evidence gap. The old aggregate result CSVs retain their pre-audit `route_feasibility_checked=False` fields; use the new independent audit manifest for the later conditional check.

## Downloads

- [Original route_audit_exact_plans.zip](route_audit_exact_plans.zip) (about 0.41 MB; full repository-relative folder structure).
- [Original transfer, station-hour and setup-1/setup-2 route files](route_audit_historical/).
- [Original routing_sensitivity.csv](routing_sensitivity.csv).
- [Independent replay checks](exact_plan_replay_checks.csv).
- [Independent conditional route costs](exact_plan_route_costs.csv).
- [Provenance, hashes and verified totals](exact_plan_audit_manifest.json).

The ZIP's members match the supplied folder byte-for-byte. No extraction over existing report results and no allocation re-solve was performed. To verify this release:

```bash
python -m pip install -r requirements-integration.txt
python sf_bikeshare/check_exact_report_routing.py
```

The checker replays the fixed transfers against the published historical demand and midnight stocks, compares all 42 policy-day result/state tables, and validates supplied route-event certificates for all 56 policy/setup/day combinations. Event checks cover travel-time arithmetic, setup/handling, pickup/drop matching, precedence, onboard capacity, hour deadlines and inter-hour position continuity where a full chain is certified. Failed chains are not presented as full-day routes. It does not re-search or reoptimize allocations.

## Verified results

| Check | Result |
| --- | --- |
| Historical optimized moves | 766 bikes in 288 transfer instructions |
| Bikes per transfer instruction | 2.6597 (rounds to 2.7); not a measured average onboard load |
| One-minute setup, optimized | All 133 active hours on all 9 active days pass conditionally; 5 other days have no moves |
| Two-minute setup, optimized | 29 hours on 3 days uncertified: 7 on 6 April, 11 each on 15 and 16 April |
| One-minute setup, rule | 3/14 days pass; 179 of 249 active hours uncertified |
| Two-minute setup, rule | 1/14 days pass |
| Productive-activity route cost, optimized | USD2,400.00 over the exact 14-day report case |
| Productive-activity contribution change | -USD878.71 (rounds to -USD879) |
| Paid-span route cost, optimized | USD5,713.13 |
| Paid-span contribution change | -USD4,191.83 (rounds to -USD4,192) |

The original USD202.316 Stage 1 result is retained. These route scenarios reprice its exact fixed schedules, holding modeled hourly service/returns fixed. Productive activity includes driving, loading/unloading and setup. Paid span also charges gaps between first assignment and final completion. Neither is a certified worker shift or observed operator expense. No depot legs, parking, shift limits, overtime or event-level customer/station-inventory feasibility is established.

The earlier [Carlo re-solve evidence](../routing_evidence_2026-11-22/README.md) is separate: 8/9 active optimized days pass and its estimated changes are -USD703/-USD3,782 on 13 priced calendar days. It remains useful context, and does not replace this exact-plan audit.

See the [final-report v2 review](../../../docs/FINAL_REPORT_V2_REVIEW_2026-11-22.md) for verified corrections and the remaining wording edits. The supplied PDF was reviewed read-only; it was not edited or included in this audit archive.
