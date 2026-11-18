# V3: enriched SF model-input handoff

Prepared 18 November 2026. This is Carlo's observed-data and evidence handoff for the two-stage allocation/routing proposal. Joohee approved the 34-station, 10-week, hourly scope in the comments supplied by Carlo. Demand, vehicle and economic assumptions still require their owners' decisions.

The original database and V2 Parquet were preserved. A separate local database, `sf_model_inputs_v3.duckdb`, contains 21 tables. Small scoped exports accompany it; no raw status history, rider ZIP codes or customer identifiers are exported. Shared Google Docs were read only; Carlo will upload information manually.

## Metric units

The V3 database, exports and local cost formula now use metric working measurements. The historical V1/V2 source files retain their original units for provenance. Currency remains USD, coordinates remain decimal degrees, and time remains seconds/minutes/hours as labeled.

| Measurement | V3 field / unit | Conversion or treatment |
| --- | --- | --- |
| Distance | `great_circle_km`, `road_distance_km`; snapping distances in metres | Road metres / 1,000; former mile columns removed |
| Temperature | `temperature_c` in degrees Celsius | `(source Fahrenheit - 32) * 5 / 9` |
| Wind speed | `wind_kmh` in kilometres/hour | Source mph multiplied by 1.609344 |
| Precipitation | `precipitation_mm` in millimetres | Source inches multiplied by 25.4; trace and missing-value flags preserved |
| Fuel price | USD/litre | Source USD/US gallon divided by 3.785411784 |
| Vehicle fuel consumption | Litres/100 km | Unagreed parameter remains blank; litres used = km * consumption / 100 |
| Vehicle distance cost | USD/km | Unagreed parameter remains blank |

The main hourly table still has 51 columns. Weather columns have been renamed as shown above. `great_circle_miles` and `road_distance_miles` were removed from the distance table, which now has 12 columns. Original-unit references survive only in conversion/source notes, not as V3 working measurements.

## Main files

| File / table | Grain and size | Purpose |
| --- | --- | --- |
| `station.csv` | 34 stations | Original ID, name, latitude, longitude, dock count, city and installation date |
| `station_hour_observed.csv.gz` | 57,120 station-hours; 51 columns | V2 observations plus rider splits, internal/external flows, matched-exposure counts, net outflow and quality flags |
| `opening_inventory_daily.csv` | 2,380 station-days | Midnight bikes/free docks with preceding snapshot, age, validity and capacity flags |
| `opening_inventory_hourly.csv.gz` | 57,120 station-hours | Same opening-stock diagnostics each hour; not permission to reset counterfactual inventory hourly |
| `station_capacity_audit.csv` | 34 stations | Listed capacity versus minimum, maximum and modal valid status totals; no invented overrides |
| `boundary_flows_hourly.csv.gz` | 57,120 station-hours | Dense observed inflows/outflows involving stations outside the cohort, split by rider type |
| `customer_od_hourly_observed.csv.gz` | 54,422 OD/hour/class groups | Origin, destination, departure/arrival hour, observed trip count, temporal/cohort flags and duration-review counts |
| `customer_in_transit_day_boundaries.csv` | 188 groups at midnight boundaries | Observed trips strictly spanning each day boundary; includes long-trip and duration-mismatch counts |
| `customer_events_at_day_boundaries.csv` | 12 groups | Trips exactly at midnight, exported separately for event-order decisions |
| `station_distances.csv` | 1,156 directed pairs, including 34 diagonal pairs | Great-circle distance, current OSRM road distance/time, snapping distances and provenance keys |
| `station_day_quality.csv` | 2,380 station-days | Opening stock, trip totals, coverage, empty/full exposure and capacity/DST flags |
| `tariff_reference.csv` | 7 tariff components | Historical pass prices and duration-fee benchmarks, with source and applicability status |
| `revenue_allocation_scenarios.csv` | 6 rider-class/scenario rows | Jason's proposed low/base/high allocations; explicitly not measured marginal cash revenue |
| `operating_parameter_register.csv` | 17 parameters | Three previously cited historical gasoline proxies and 14 explicitly unresolved operating/economic inputs |
| `teammate_requirements.csv` | 12 requirements | Maps Joohee, Jason and Fu Yan comments to inputs, evidence, status and remaining work |
| `model_decisions_required.csv` | 9 decisions | Owner and reason for the remaining modeling decisions |
| `data_dictionary.csv`, `table_inventory.csv` | All database fields/tables | Types, units, meanings, keys and export locations |
| `validation_checks.csv`, `manifest.json` | Build evidence | 43 checks, including weather conversion/missingness and metric-unit checks; 18 export row-count readbacks; checksums and provenance |
| `dataset_versions.csv` | V1-V5 progression | Existing products versus planned demand and policy stages |

Individual scoped journeys and matched endpoints are available only in the local database as `customer_journeys_observed` and `observed_trip_events`. OD exports aggregate records and contain no bike, payment or customer identity.

## Observed flow totals

| Rider label | Pickups | Returns |
| --- | ---: | ---: |
| Subscriber | 55,179 | 55,234 |
| Customer | 7,064 | 7,092 |
| Total | 62,243 | 62,326 |

These are endpoint events, not a count of distinct journeys. V2's 63,974 endpoint-relevant journeys remain unchanged. V3 additionally retains **one flagged trip spanning the entire horizon**, with neither endpoint in the pilot dates, to expose the initial/in-transit accounting issue. The local journey table therefore has 63,975 records: 60,599 internal, 1,729 inbound and 1,647 outbound. These scope categories do not imply every departure and arrival falls inside the date window.

There are 1,647 observed external-cohort departures and 1,729 external-cohort arrivals during the pilot. A trip between two cohort stations that crosses the date horizon is an internal trip with a temporal boundary, not an external-cohort trip.

## Opening inventory and capacity findings

- All 2,380 midnight opening snapshots are valid and at most 90 seconds old. Every opening bike count fits within its listed dock count.
- The latest snapshot is chosen at or before the boundary. A stale or invalid latest snapshot produces NULL model opening values; no later snapshot or older valid fallback is substituted.
- 67 midnight snapshots have `bikes + available docks != dock_count`. Across the selected 3,424,038 valid status snapshots, 177,539 have such discrepancies. Every station has at least one discrepancy.
- For all 34 stations, the modal and maximum valid status total equal the listed dock count. Lower totals therefore merit review as effective availability/possible disabled equipment; they do not by themselves establish that physical capacity changed.
- Retaining listed docks as a physical-capacity base is a possible team assumption. Respecting reduced effective capacity is a different operational scenario. No physical-capacity overrides were invented.
- The 34 stale hourly openings are all at **03:00 on 8 March 2015**, following the daylight-saving clock change; their preceding snapshots are 3,658 recorded-clock seconds old. The nonexistent/ambiguous clock exposure has not been repaired into an artificial measured hour. Midnight stocks are unaffected.

Status is historical inventory under operations that actually occurred. Initialize policies from common stocks, then propagate their simulated inventories. Do not replay the historical stock path as the no-rebalancing policy.

## Demand-estimation handoff

For each rider class, the panel includes three kinds of endpoint counts:

1. `subscriber_pickups`, `customer_pickups`, and the corresponding returns: all observed endpoint events.
2. `*_valid_exposure`: endpoint events in the same valid short-gap intervals used to calculate `observed_seconds`.
3. `*_available_exposure`: pickup events in valid intervals with bikes available, or return events in valid intervals with docks available.

Fu Yan can pool available-exposure numerators with `bike_available_seconds` or `dock_available_seconds` over training observations. The ordinary full-hour trip total must not be divided by a restricted valid-time denominator without matching intervals. Missing exposure and zero available exposure do not establish zero demand. No exposure-ratio estimate has been labeled true demand.

Trip timestamps are minute-rounded; status has seconds. There are 24 pickup and 20 return timestamp ties with status, and the ordering of those events is unknown. The matching convention is previous-state carry over `[observed_at,next_observed_at)`, with a positive gap no longer than 90 seconds, consistent with V2. Pooling, timestamp sensitivity, demand uncertainty and artificial-censoring validation remain Fu Yan's work.

## OD, transit and extreme durations

Departure and arrival hours are retained separately. `arrival_slot_offset_hours` is their recorded-clock difference; zero does not mean instantaneous travel. The model must choose within-hour order and transfer/customer lead times.

Trips in transit satisfy `started_at < boundary_at < ended_at`. Arrivals/departures exactly at the boundary are separate because their order relative to a snapshot is unresolved. The day-boundary event table records 9 departures and 4 arrivals across its 12 groups.

The original 13 endpoint-relevant trips over 24 hours remain flagged. The supplemental horizon-spanning record is also long and has a duration/clock mismatch, giving 14 long records in the expanded local journey table. Its recorded dates run from December 2014 to June 2015. This is a review case, not evidence that a bike was continuously ridden for that duration. Transit/OD exports retain diagnostic counts so the team can compare retaining versus excluding flagged long trips. Such a sensitivity changes the counts and must be reconciled explicitly; no observations were silently dropped.

Accepted internal customer trips must generate consistent later arrivals/in-transit stock in policy simulations. Fixed external-flow treatment still needs failure/overflow rules when a station lacks bikes/docks.

## Distances and routing

One OSRM Table request returned road distances and driving durations for all 34 coordinates, in documented station-ID order. There are 1,122 non-diagonal directed legs. Do not symmetrize the matrix: 1,082 directed rows differ in road distance from the reverse direction.

OSRM access timestamp and response SHA-256 are in `manifest.json`; the server did not report a map data version. Maximum station-to-road snapping distance is about 61.9 metres. The estimates use current road geometry and the default driving profile, not observed 2015 congestion or a certified truck profile. Durations exclude handling, parking and waiting. Depot legs remain unknown because no depot was specified.

Great-circle kilometres use the haversine formula with mean Earth radius 6,371.0088 km. Road and air distances have separate columns. Missing road values are never replaced silently with air distances. All V3 distance measurements use kilometres or metres.

The matrix supplies Stage 1's distance-cost approximation and Stage 2's route inputs. Neither a per-hour throughput bound nor a TSP tour alone proves pickup/delivery, onboard-load and time feasibility. These are model/evaluation responsibilities.

## Historical tariffs and Jason's scenarios

The SFMTA pricing board, PDF page 4, shows $9/24 hours, $22/3 days and $88/year. Its usage schedule includes the first 30 minutes, then $4 for a checkout over 30 through 60 minutes, and $7 for each subsequent 30-minute block. This is an October 2013 historical schedule; complete terms, caps, rounding and unchanged 2015 applicability remain to review. No surcharge is converted into an actual billed trip amount.

The Air District's April 2015 release confirms $9 daily, $88 annual and an additional $29.95 30-day trial option. **The date printed in the PDF is 16 April 2015**, despite `041315` in the filename and the earlier shared-document reference to 13 April. Both public PDFs were downloaded, text-checked and visually reviewed; hashes are recorded in the manifest.

| Rider label | Low allocation | Base allocation | High allocation |
| --- | ---: | ---: | ---: |
| Subscriber | $88 / 150 = $0.5867/trip | $88 / 100 = $0.88/trip | $88 / 50 = $1.76/trip |
| Customer | $9 / 4 = $2.25/trip | $9 / 2 = $4.50/trip | $9 / 1 = $9.00/trip |

These reproduce Jason's proposed assumptions at full precision. Actual trip frequency per customer, pass purchases, pass type, discounts and payments are not observed. In particular, `Customer` does not distinguish daily from three-day passes, and other plans exist. Allocated fees are suitable only for an explicitly labeled scenario/service-value interpretation unless the team supplies a defensible incremental contribution model. They are not measured additional cash receipts from each extra ride. Regression cannot recover charges when no charge observations exist.

Sources: [shared project document, read only](https://docs.google.com/document/d/12mtigIDA4NQ2ycOh-fxOVmE1-lP0h9YF6kfvWXMp1z0/edit), [SFMTA pricing board](https://www.sfmta.com/sites/default/files/projects/10.16.2013%20Bike%20Share%20Open%20House%20Boards.pdf), [2015 Air District release](https://www.baaqmd.gov/~/media/files/communications-and-outreach/publications/news-releases/2015/2015-022-babs-500000-041315.pdf), [OSRM Table documentation](https://project-osrm.org/docs/v5.24.0/api/#table-service). The three gasoline proxies retain their 17 November verification date and the cited EIA source from the existing cost note; they were not newly remeasured.

## Which additions came from outside the original dataset?

| Addition | External source | Status |
| --- | --- | --- |
| `road_distance_km`, `driving_minutes`, road-snapping distances and routing provenance | OSRM Table API | Retrieved for V3; current driving estimates, not measured historical truck journeys |
| Pass prices, included ride duration and duration-surcharge components | SFMTA historical pricing board and April 2015 Air District release | Newly integrated tariff evidence; individual payments and complete plan applicability remain unknown |
| Three historical gasoline price parameters, now in USD/litre | EIA California gasoline series, carried from the previously cited cost note | External state-level benchmarks checked on 17 November, not newly collected operator expenses |
| Assumed trips per pass and allocated revenue scenarios | Jason's shared team notes | Team assumptions recorded separately; not externally observed rider behavior or marginal cash revenue |

Station coordinates, dock counts, rider labels, trips, status and weather came from the original supplied files. The great-circle distances, rider splits, opening stocks, capacity/coverage flags and OD/boundary/transit counts are transformations of those files rather than newly sourced measurements.

## Load and reproduce

Use a Python 3.12 environment with `duckdb` and `pandas` installed. **For the GitHub handoff, load the CSV/GZIP exports directly.** The DuckDB databases are local files and are not uploaded. The existing full source database is needed only to rebuild the enriched inputs from source; it is not needed to read the shared exports.

```python
import duckdb

# GitHub handoff: DuckDB reads CSV gzip directly from the repository clone.
panel = duckdb.sql("""
    SELECT * FROM read_csv_auto(
      'output/sf_bikeshare/model_inputs_v3/station_hour_observed.csv.gz')
""").df()
training = panel[panel['split'] == 'training'].copy()

# Optional analyst-only local database, if it has been built on this machine:
# con = duckdb.connect(
#     "output/sf_bikeshare/model_inputs_v3/sf_model_inputs_v3.duckdb",
#     read_only=True,
# )
```

```powershell
python sf_bikeshare/enrich_model_inputs.py
# Optional: fetch/cache one current road matrix if no matching cache exists.
python sf_bikeshare/enrich_model_inputs.py --fetch-road-matrix
```

The local workspace venv points to a missing Python installation. This build used bundled Python 3.12.14 with the existing DuckDB 2.0.0 package. Normal team reproduction should install DuckDB into a working Python environment, as the code does not depend on that machine-specific workaround. The road cache is keyed by station order/coordinates and verified by checksum. A rebuild without a cache/fetch option leaves road columns NULL and records that status explicitly.

No latent demand, agreed vehicle configuration, depot, optimized plan, feasible truck schedule or profit gain is established by this handoff. See [dataset progression](../../../docs/SF_Bikeshare_Dataset_Iterations.md) for the boundary between V3 and the planned V4/V5 work.
