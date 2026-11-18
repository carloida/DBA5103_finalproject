# Data provenance and evidence gaps

The modeling work now uses an SF Bay Area pilot. The earlier Citi Bike EDA remains separate background analysis.

## SF sources and shared subset

- Source: [Ben Hamner, SF Bay Area Bike Share, Kaggle](https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share), using the four supplied local CSVs: station, trip, status and weather.
- Full audit: 70 stations, 669,959 completed trips, 71,984,434 status snapshots and 3,665 weather location-days. Original byte counts and SHA-256 hashes are in [source_manifest.json](../output/sf_bikeshare/source_manifest.json).
- Shared candidate: 34 SF stations installed by 29 August 2013, 9 February-19 April 2015, 57,120 station-hour rows. See the [subset guide](../output/sf_bikeshare/subset_assessment/README.md) and [release manifest](../output/sf_bikeshare/subset_assessment/release_manifest.json).
- Data is scoped, aggregated and compressed; unusual usage days are retained. Trips crossing the cohort boundary remain in endpoint counts. Weather is a city/date proxy, not a station measurement.
- The original V2 file contains observed counts/exposure, not fitted true demand, truck routes, actual costs, payments or profit. V3 now supplies separate opening-stock and capacity-audit tables; effective versus physical-capacity treatment remains a model decision.
- Full raw SF files, the approximately 1.57 GB source database, the separate V3 database and bulk full-system exports are excluded from Git. The roughly 0.247 MB named subset remains the only permitted Parquet export. V3 additionally supplies compact, scoped CSV/GZIP model-input exports. Source paths and mtimes in manifests describe the analyst's local build, not downloadable raw files.

## V3 enrichment - 18 November 2026

See the [dataset progression table](SF_Bikeshare_Dataset_Iterations.md), [handoff guide](../output/sf_bikeshare/model_inputs_v3/README.md) and [V3 manifest](../output/sf_bikeshare/model_inputs_v3/manifest.json). The builder opens the original database read-only and preserves the V2 Parquet checksum.

V3 working physical measurements use metric units: km/m, degrees Celsius, km/h, mm, litres and litres/100 km. Distance and fuel costs use USD/km and USD/litre. Original-unit source references are retained only in provenance/conversion notes; V1/V2 files remain unchanged. The manifest records conversion formulas and the data dictionary records field units.

| Input | Provenance | Interpretation |
| --- | --- | --- |
| Rider-split flows, OD/temporal/cohort boundary fields | Existing trip records and endpoint timestamps | Observed completed service; no customer, pass or payment identity |
| Opening inventory and effective capacity | Latest preceding selected status snapshot, maximum accepted age 90 seconds | Historical bikes/free docks; stale/invalid latest state produces NULL; static dock count retained separately |
| Matched demand-estimation numerators | Endpoint events matched to valid status intervals, same positive <=90-second gap rule as V2 exposure | Numerators and denominators refer to matching intervals; not an estimate of latent demand |
| Road distance and driving duration | One cached public [OSRM Table request](https://project-osrm.org/docs/v5.24.0/api/#table-service), 18 Nov 2026, 34 coordinates | Current directed driving estimates; not 2015 traffic, actual truck operations, a truck-access guarantee or depot travel |
| Historical membership/usage schedule | [SFMTA October 2013 board, PDF page 4](https://www.sfmta.com/sites/default/files/projects/10.16.2013%20Bike%20Share%20Open%20House%20Boards.pdf) | Historical tariff evidence; exact 2015 applicability and complete fee terms remain assumptions/review items |
| 2015 annual/day/trial pass prices | [Air District release 2015-022](https://www.baaqmd.gov/~/media/files/communications-and-outreach/publications/news-releases/2015/2015-022-babs-500000-041315.pdf), PDF pages 1-2 | Release dated 16 Apr 2015 despite filename; confirms $88 annual, $9 daily and $29.95 trial options, not individual receipts |
| Allocated revenue scenarios | Jason's proposed frequencies in the shared DBA5103 Project document, read 18 Nov | Annual price divided by assumed annual trips, or daily price divided by assumed daily trips; not observed marginal revenue |
| Operating-cost register | Existing cited cost revision plus explicit unknown entries | Three California 2015 gasoline proxies retain their prior verification date; unagreed vehicle/labor/handling values remain blank |

External PDFs were downloaded, extracted and visually checked locally; the manifest records their hashes. Public road-cache coordinates/order and response hashes are recorded. The shared project document was read only. Carlo will transfer information to Google Docs manually.

The local journey supplement contains one extreme-duration trip spanning the full pilot window in addition to the unchanged 63,974 endpoint-relevant journeys. Long-trip and duration-mismatch flags remain available in OD/transit outputs. Recorded-clock DST ambiguity is retained and flagged rather than silently repaired.

## Earlier Citi Bike CSV (not shared)

The raw CSV and complete cleaned trip copy have been removed from current repository files. The notebook, analysis code, charts and summary/audit tables remain. Original files stay unchanged locally; earlier commits remain in Git history.

- File: `JC-202609-citibike-tripdata.csv/JC-202609-citibike-tripdata.csv`.
- Analysis window: September 2026 starts, with September arrivals handled separately for station-event accounting.
- Source records: 106,628; valid September-start trips: 106,617.
- SHA-256: `7dceac4be4b3aec02a292a28ebfb5360bc4f8908a41b631689cc3aa8faebec1c`.
- Provenance: supplied local file. The filename and recorded timestamps define the analyzed period; the exact original download URL/date were not recorded.
- Official field descriptions and data access: https://citibikenyc.com/system-data.
- Refer to the publisher's terms for data reuse. No new license over the source dataset is asserted by this repository.

Original fields: ride ID, bicycle type, start/end timestamps, start/end station names and IDs, start/end latitude/longitude, and member/casual status. Ride ID identifies a trip, not an individual bicycle or a customer.

All fields begin as strings. Station IDs remain identifiers. Blank strings are treated as missing; exact-name recovery is allowed only where a name uniquely identifies an observed station ID, and recoveries are flagged. Long trips are flagged and retained, with a sensitivity scenario excluding them. The original CSV is unchanged.

Recorded timestamps have no explicit timezone metadata and are analyzed as recorded local clock time. No Singapore conversion is applied. The service domain is the 108 observed JC/HB origin IDs; it is not an inferred city boundary. The network remains open to external destinations and potentially unobserved incoming trips.

## Missing inputs

The following table describes the earlier Citi Bike trip-only workflow. For current SF V3 gaps, use the [model decision register](../output/sf_bikeshare/model_inputs_v3/model_decisions_required.csv) and [operating parameter register](../output/sf_bikeshare/model_inputs_v3/operating_parameter_register.csv); SF historical status and opening inventories are now available.

| Needed input | Status in the trip CSV | Potential treatment |
| --- | --- | --- |
| Historical bikes and empty docks at stations | Absent | Obtain aligned status histories or use labeled initial-stock assumptions |
| Station dock capacity and outages | Absent | Obtain station/availability data; current status cannot reconstruct historical inventory |
| Failed rentals and returns | Absent | Estimate censored demand using an explicit model; empty/full observations alone do not count lost customers |
| Bike/dock acquisition costs and useful lives | Absent | Procurement evidence or transparent scenario ranges |
| Maintenance, parts, charging, inspection and security costs | Absent | Operating reports, supplier evidence or explicit assumptions |
| Redistribution routes, staff, trucks, loading times and costs | Absent | Operator evidence or a simple labeled transfer-cost model |
| Billing plan, payments, discounts and refunds | Absent | Fare schedules support scenarios, not exact transaction reconstruction |
| Local revenue and profit | Absent | Financial benchmarks with geography, period and accounting scope clearly stated |

Keep capital expenditure, depreciation and cash operating costs conceptually distinct. Customer fares are operator revenue; do not double-count them as additional resource costs in a combined operator/customer economic objective. More member rides do not automatically create additional subscription revenue.

## External sources identified for further work

These are references and candidates, not data merged into the current EDA:

- Citi Bike operating reports: https://citibikenyc.com/system-data/operating-reports.
- NYC DOT 2025 financial report: https://home4.nyc.gov/html/dot/downloads/pdf/2025-report-bike-share-financial-data.pdf. It includes JC/Hoboken within combined program accounts, without a separate local profit statement. It is not a September 2026 JC/HB financial dataset.
- NJ pricing change effective 29 May 2026: https://citibikenyc.com/pricechange. Use the applicable date, geography and subscription rules when constructing a pricing scenario.
- SF Bay Area Bike Share: https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share. The supplied files have now been analyzed separately in `sf_bikeshare/`; no SF observations are merged into the Citi Bike EDA. Review its status/capacity audits and source terms before adopting the final modeling scope.

Public operating reports can contain preliminary figures and aggregate activity rather than individual work orders. Cost allocation assumptions must be documented; a system average is not an observed marginal relocation cost.

## Generated artifacts

### Separate robustness inputs - 18 November 2026

[Five derived cases](../output/sf_bikeshare/robustness_testing/README.md) were prepared from the existing source database opened read-only. They use two cities and three periods with the main V3 case, retain the same features and metric working units, and are explicitly for robustness testing. The main V3 package and original sources remain unchanged. Case manifests record source provenance, coordinates/order, checksums and validation. Current San Jose OSRM driving estimates were fetched once on 18 November 2026; the existing SF cache was reused. These are current road proxies, not historical truck observations. Historical tariff/allocation tables are reference benchmarks; case gasoline values are NULL until an economic scenario or period-matched source is agreed. The [pipeline report](SF_Bikeshare_Project_Pipeline_Report.md) explains the planned evaluation; no policy results have been generated.

The manifest records source hash, software versions and reconciliation status. The cleaning audit, flagged records, aliases, coordinate checks and sensitivity tables retain the cleaning trail. Forecast outputs are exploratory completed-trip predictions, not unconstrained demand forecasts.

The original long poster and its four-picture version summarize the EDA. They are communication artifacts, not additional data sources. The saved WhatsApp text is a draft; no messages were sent automatically.
