# Section 3: Data and demand estimation

**Carlo's data contribution | Updated 20 November 2026 | Draft for integration with Fu Yan's subsection**

**Scope:** Section 3 has a shared two-page allowance. Subsections 3.1-3.3 below cover Carlo's data work; Fu Yan will complete 3.4. The data-cleaning appendix and internal checklist follow separately. Cost assumptions, formulation, solution methods and robustness results belong to their assigned sections.

## 3.1 Data source and study scope

The study uses the supplied SF Bay Area Bike Share trip, station, historical station-status and weather files, associated with [Ben Hamner's dataset](https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share). The full source contains 669,959 completed trips, 70 stations across five cities and 71,984,434 status snapshots, with trip starts spanning August 2013-August 2015.

The approved main case retains **34 San Francisco stations installed by 29 August 2013**, over **9 February-19 April 2015**. The fixed cohort avoids changes in station membership within the study. The hourly grid contains **57,120 station-hours**. The first eight weeks are labeled training and the final two weeks exploratory validation. These dates have already been examined and are not an untouched holdout.

The dataset progressed from the full audited source (V1), to the scoped hourly pilot (V2), to enriched model inputs (V3). V3 retains the same main-case observations and expands the hourly panel from 21 to **51 columns**, with **21 related core tables** for inputs at different aggregation levels. Original source files and V2 remain preserved.

## 3.2 Data preparation and feature engineering

Records were linked through station identifiers and timestamps. Pickups were assigned to departure hours and returns to arrival hours. A dense grid retains zero recorded-trip hours; missing availability remains unknown. Weather was linked through a documented city/date proxy rather than station-level measurements.

For exposure calculations, valid states were defined as nonnegative, nonmissing bikes and free docks with a positive combined total. States were carried only to the next observation across positive gaps of at most 90 seconds, splitting intervals at hour boundaries. Longer gaps were not filled. The cutoff is an analytical assumption, not a lecture-prescribed rule. This produces time-weighted availability rather than treating irregular observations equally.

| Prepared inputs | Transformation and purpose |
| --- | --- |
| Rider flows | Subscriber/Customer pickups and returns, with counts matched to valid and available status intervals for demand estimation |
| Availability and net flow | Observed, empty/full and low-inventory seconds; time-weighted mean bikes/capacity; net outflow = pickups minus returns |
| Opening stocks and capacity | Observed midnight stock initializes each daily model; latest preceding snapshots are accepted only if valid and at most 90 seconds old. Base capacity uses `dock_count`; effective-capacity discrepancies support a separate sensitivity |
| OD, boundary and transit records | Origin/destination and departure/arrival timing, including outside-cohort endpoints and trips crossing day boundaries |
| Distance and weather | Derived great-circle distances; externally obtained current directed OSRM driving estimates; weather converted to metric units |

Empty/full fractions divide the relevant seconds by valid observed seconds; coverage divides observed seconds by 3,600. Group summaries divide summed seconds by summed exposure. Ratios without valid denominators remain missing. Opening stocks are separate from hourly means. Net flow describes station pressure and does not directly determine required relocations.

Working units are km/m, degrees Celsius, km/h, mm and litres; currency is USD. No standardization was applied. Road estimates are current driving proxies, not historical truck logs. Jason's financial scenarios are kept separately from observed station data.

## 3.3 Validation and handoff

V3 passed **43 reconciliation checks and 18 export row-count readbacks**. The main cohort records **55,179 Subscriber and 7,064 Customer pickups**. The 63,974 distinct journeys with a selected endpoint in the window are a different counting population; pickups and returns must not be summed to count journeys.

All **2,380 midnight opening stocks** are fresh. There are 67 station-day effective/static-capacity discrepancies, retained for a lower-capacity sensitivity whose exact definition remains to be agreed. The 34 stale hourly openings around the March DST transition are diagnostics, not initialization inputs to the daily model. Recorded local-clock timestamps remain unchanged; DST flags do not repair elapsed time. Long-duration journeys and unusual days were retained with diagnostics. Historical stock initializes separate daily experiments rather than a continuous no-rebalancing stock path.

Five additional same-schema cases covering San Jose and other periods were prepared separately for **robustness evaluation**, described in Section 7. Preparing these inputs does not establish policy performance. Completed trips measure served requests; estimating attempted demand remains Fu Yan's task. The [main V3 package](https://github.com/carloida/DBA5103_finalproject/tree/main/output/sf_bikeshare/model_inputs_v3) provides the reconciled observations and matched-exposure inputs for that work.

## 3.4 Demand estimation — Fu Yan

**Pending Fu Yan's contribution:** specify the estimator, pooling and zero-exposure fallback; explain how estimated requests link to destinations/returns; report training-based validation and uncertainty. This subsection must describe the method actually implemented. No fitted demand results are supplied by Carlo's data preparation.

---

## Appendix contribution: data-cleaning and transformation code

**Owner: Carlo.** Include the following code or references, alongside Hong Jin's model code and Fu Yan's demand-estimation code:

- [Source database preparation](https://github.com/carloida/DBA5103_finalproject/blob/main/sf_bikeshare/build_database.py)
- [V3 input transformations](https://github.com/carloida/DBA5103_finalproject/blob/main/sf_bikeshare/enrich_model_inputs.py)
- [Robustness subset preparation](https://github.com/carloida/DBA5103_finalproject/blob/main/sf_bikeshare/build_robustness_subsets.py)
- [Portable robustness validation](https://github.com/carloida/DBA5103_finalproject/blob/main/sf_bikeshare/validate_robustness_subsets.py)

The [project repository](https://github.com/carloida/DBA5103_finalproject), [main data dictionary](https://github.com/carloida/DBA5103_finalproject/blob/main/output/sf_bikeshare/model_inputs_v3/data_dictionary.csv) and [separate robustness folder](https://github.com/carloida/DBA5103_finalproject/tree/main/output/sf_bikeshare/robustness_testing) provide the handoff. Full raw files and local DuckDB databases are excluded. Reading the scoped exports does not require those databases; rebuilding does require the documented local source inputs.

## Carlo's remaining checklist — internal, outside the paper text

1. Finish the focused V3 EDA using the [section-aligned figure plan](supporting/SF_Bikeshare_Section3_Figure_Plan.md): one compact figure combining hourly completed-trip profiles and station-level empty/full exposure, placed after 3.2. Retain the feature table and reserve space for Fu Yan; move detailed diagnostics to supporting material. The figure is planned, not yet generated.
2. Integrate Fu Yan's completed demand subsection, review sensitivity to the status-gap cutoff, and confirm the exact lower-capacity sensitivity and flagged-day rules. Carlo confirmed `dock_count` as the base capacity on 20 November; the model uses observed midnight stock.
3. Write Section 8 jointly with Hong Jin after results are available; its **0.5-page allowance is shared**, not a separate full conclusion from each owner.
4. Supply the data-cleaning appendix and complete the final edit for flow, notation, units, references and formatting across the paper.

The longer [technical notes](supporting/SF_Bikeshare_Data_Preparation_Technical_Notes_2026-11-19.md) retain the detailed feature inventory, formulas, Jason-input review and robustness protocol. They support the team and are not intended to be pasted wholesale into Carlo's Section 3 contribution.

The [reference and feature-engineering review](supporting/SF_Bikeshare_Reference_and_Feature_Review_2026-11-19.md) records the lecture/textbook evidence, independently checked transformations and remaining assumptions. It is supporting material outside Section 3's page allowance.

The [20 November handoff](supporting/SF_Bikeshare_Model_Input_Handoff_2026-11-20.md) records the latest confirmed data decisions, provisional cost benchmarks and outstanding model inputs. It supplements the frozen V3 exports; it does not replace them or certify all model assumptions as agreed.
