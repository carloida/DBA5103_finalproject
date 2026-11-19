# Reference and feature-engineering review

**Reviewed 19 November 2026 | Supporting evidence, outside the paper's Section 3 allowance**

## Finding and scope

The revised [Section 3 draft](../SF_Bikeshare_Consolidated_Data_Preparation_Report.md) is suitable for publication as an observed-data handoff. Its reported transformations agree with the inspected code and prepared data. The course material supports the network/inventory modeling direction, explicit units, model validation and evaluation under changed assumptions. It does **not** establish that every project-specific assumption is empirically correct or that a final demand estimator/model has been validated.

The review covered the relevant sections of the project guideline, Lectures 4, 6 and 7, and the three supplied reference books. Selected pages were freshly extracted from the original local PDFs and rendered for inspection. This is a targeted review, not a claim to have audited every page or proved the eventual optimization model correct. The local PDF files are not republished in GitHub.

## Course and textbook evidence

Page positions below are one-based PDF pages; printed book pages are supplied where applicable.

| Supplied source | Inspected pages | Supported application and boundary |
| --- | --- | --- |
| `Project_Guideline.pdf` | PDF 1-4 | Requires the problem, analyzed data/process, model, methodology and code appendix. Practical projects should relate assumptions to reality and assess changed conditions. Its 8-14 narrative pages are indicative; section allocations are the team's plan. |
| `Lecture4 DualitySensitivity.pdf` | PDF 24-26 | Supports what-if evaluation when inputs/resources are uncertain or changed. It does not prescribe five robustness files or automatically validate an integer solution's sensitivity through LP shadow prices. |
| `Lecture6 Network.pdf` | PDF 44-45, 58 | Container repositioning uses initial stock, time-expanded nodes and travel lead times. Repeated solves under sampled demand illustrate scenario evaluation. Bike/dock bounds, rejected trips, information timing and boundary rules require application-specific extensions. The lecture example's assumption that all demand is satisfied must not be imported automatically. |
| `Lecture7 IP.pdf` | PDF 4, 6, 11, 22, 24, 27-28 | Mixed/integer and binary modeling, implication bounds and TSP concepts support allocation/activation and a routing extension. The symmetric TSP example does not justify symmetrizing our directed road matrix. Visit-order constraints alone do not enforce truck loads or time feasibility. |
| Hillier and Lieberman, supplied `Hiller_Liberman_Introduction to Operations Research.pdf` | PDF 32, 34, 41-42; printed 7, 9, 16-17 | Separates problem/data preparation from model testing; discusses imperfect data, dimensional consistency, retrospective validation and its limitations. Supports transparent data assumptions and retaining a distinct model-validation stage. |
| Bradley, Hax and Magnanti, `Applied Mathematical Programming.pdf` | PDF/printed 12-13 | Defines decision-variable units and scales objective/constraint coefficients consistently. Supports preserving interpretable physical units and ensuring model coefficients match them; metric units are our chosen convention. |
| Bertsimas and Tsitsiklis, supplied first-five-chapters PDF | PDF 219-220; printed 202-203 | Chapter 5 studies LP sensitivity in costs, requirements and coefficients, including conditions for maintaining a basis. For our integer model, re-solve stated scenarios rather than claiming LP basis ranges establish global IP sensitivity. |

## Engineering checks and interpretations

| Prepared feature/input | Review outcome |
| --- | --- |
| Dense station-hour grid and rider flows | Counts reconcile by class and internal/boundary categories. A zero recorded-trip count is not zero attempted demand. The fixed ten-week cohort is a manageable case, not proof of representativeness. |
| Status intervals and weighted means | The implemented rule retains valid preceding states over positive gaps at most 90 seconds and splits at hour boundaries. Weighting uses interval duration. This is internally consistent; the threshold and both-zero exclusion remain analytical choices needing sensitivity/interpretation. |
| Empty/full/available exposure | `available bike seconds = observed-empty`; dock availability uses `observed-full`. Empty/full fractions use observed time and remain NULL without it. Aggregate fractions must use sums of exposure, not an unweighted mean of percentages. Low-inventory time overlaps empty/full time. |
| Matched event numerators | Counts are restricted to the same valid/available intervals as their denominators. Snapshot timestamp ties remain flagged; the minute-rounded data do not resolve within-minute event order. Estimator assumptions and zero-exposure fallback remain Fu Yan's work. |
| Opening stock | The code first selects the latest preceding snapshot. It accepts that reading only if valid and no more than 90 seconds old; it does not skip an invalid latest reading in favor of an older valid one or look into the future. The shorter draft's wording was corrected accordingly. |
| Capacity | Listed docks and effective bikes-plus-free-docks totals remain separate. Main V3 has 67 midnight discrepancies; this does not prove physical dock changes or establish the final model's capacity rule. |
| Timing, OD and in-transit stock | Recorded timestamps, arrivals/departures and boundary flags are retained. DST is flagged, not repaired. Counterfactual accepted rentals must produce their linked returns; historical hourly stocks must not reset a no-moves simulation. |
| Distances | Great-circle distances are geographic derivations. OSRM values are directed current driving proxies, with km/minute conversions and provenance; they are not historical truck routes or a complete routing-feasibility certificate. |
| Metric weather and city proxy | Conversion formulas agree with the source panel. City/date weather is an approximation. If used operationally, full-day realized weather is not automatically an available forecast. The fixed source unit conversion does not require statistical standardization. |
| Revenue and costs | Jason's pass allocations are labeled scenarios, not measured marginal receipts. Dashboard totals remain scope-unreconciled. Missing costs are not zero, duration-derived billing remains optional/unimplemented, and Stage 1/2 estimates must not be added for the same operation. |
| Robustness branch | Five additions retain the same schemas and natural city sizes. Their preparation is complete; experiments, parameter applicability and flagged-stock treatment remain pending. The cases share source history and calendar dates, so they are not six independent systems or sealed holdouts. |

The report therefore distinguishes **reconciled transformations**, **defensible but unvalidated assumptions**, and **pending modeling decisions**. Publication does not remove that distinction.

## Independent verification performed

- Rechecked main V3 export checksums, producer/V2 hashes, 43 recorded build checks, rider totals/splits, road/fuel conversions and 18 exported-table row-count readbacks.
- Re-ran the portable five-case validator: 325 recorded build checks and 90 export row-count readbacks, with matching 51 hourly columns and 21 core schemas.
- Independently queried all six local case databases read-only: **18 formula/bounds checks per case, 108 checks across 252,000 station-hours, zero mismatches**. These covered net flow, exposure/coverage fractions, available seconds, rider/internal-boundary totals, matched-count bounds, mean/exposure bounds, opening acceptance and weather conversions against the source panel.
- Inspected the status-interval, event-matching, weighted-aggregation and opening-snapshot code. The independent checks verify the specified transformation, not the empirical truth of assumptions or unobserved demand.

Existing inputs and source databases were not rebuilt or modified. No optimization, fee reconstruction, demand fitting or gap-threshold sensitivity experiment was performed in this review. The section remains deliberately limited to Carlo's assigned work.

## Changes made before publication

1. Corrected the opening-snapshot selection description.
2. Labeled the 90-second cutoff as an analytical assumption, rather than attributing it to lectures.
3. Clarified exposure-weighted group ratios and the unrepaired local-clock/DST limitation.
4. Distinguished historical initialization from counterfactual inventory paths.
5. Preserved Fu Yan's pending demand subsection and the team's separate formulation/result ownership. Broader technical notes remain supporting material, outside the two-page shared Section 3 target.

## Remaining decisions before policy evaluation

Review status-gap sensitivity and timestamp ties; agree effective/physical capacity and flagged opening-stock handling; validate the demand estimator and fallback; define lead times, within-hour order, accepted-trip returns, external-flow failures and terminal conditions; and agree vehicle/depot/cost/value scenarios. These do not prevent the focused observed-data EDA or publication of a qualified data-section draft.

See the [current data section](../SF_Bikeshare_Consolidated_Data_Preparation_Report.md), [main input guide](../../output/sf_bikeshare/model_inputs_v3/README.md), [robustness guide](../../output/sf_bikeshare/robustness_testing/README.md), [model-decision register](../../output/sf_bikeshare/model_inputs_v3/model_decisions_required.csv) and [operating-parameter register](../../output/sf_bikeshare/model_inputs_v3/operating_parameter_register.csv).
