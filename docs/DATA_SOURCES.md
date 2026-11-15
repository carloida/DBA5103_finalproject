# Data provenance and evidence gaps

## Current source: supplied Citi Bike CSV

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
- SF Bay Area Bike Share candidate: https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share. Download, inspect actual tables, check terms and audit trip/status/capacity alignment before adopting it.

Public operating reports can contain preliminary figures and aggregate activity rather than individual work orders. Cost allocation assumptions must be documented; a system average is not an observed marginal relocation cost.

## Generated artifacts

The manifest records source hash, software versions and reconciliation status. The cleaning audit, flagged records, aliases, coordinate checks and sensitivity tables retain the cleaning trail. Forecast outputs are exploratory completed-trip predictions, not unconstrained demand forecasts.

The original long poster and its four-picture version summarize the EDA. They are communication artifacts, not additional data sources. The saved WhatsApp text is a draft; no messages were sent automatically.
