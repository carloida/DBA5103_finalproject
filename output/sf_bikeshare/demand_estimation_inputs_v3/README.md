# Minute observations for V3 demand estimation

Prepared 21 November 2026 for Fu Yan's predecessor-period estimator. These are scoped observations from the existing source database, supplied separately because the frozen V3 export contains hourly summaries rather than minute status history. **This supplement does not contain estimated demand. The existing V3 files and Hong Jin's unmerged draft are unchanged.**

The cohort is the same **34 San Francisco stations** as V3. The model window is **9 February 2015 00:00 inclusive to 20 April 2015 00:00 exclusive**, with the existing training/validation split at 6 April. Five robustness packages remain separate; this minute supplement covers the main case only.

## Files and formats

| File | Rows | Compressed size | Contents |
| --- | ---: | ---: | --- |
| [status.csv.gz](status.csv.gz) | 3,425,160 | 8.97 MB | Recorded snapshots: `station_id`, `bikes_available`, `docks_available`, `time` |
| [trip.csv.gz](trip.csv.gz) | 63,974 | 0.96 MB | Relevant complete journey records, retaining outside-cohort endpoints and rider class |
| [trip_events.csv.gz](trip_events.csv.gz) | 124,569 | 0.99 MB | Selected-station pickup/return events, rider class, other station, time, split and boundary flags |
| [manifest.json](manifest.json) | — | — | Source identifiers, station IDs, exact time bounds, SHA-256 hashes, columns, counts and 18 passed checks |

`status.csv.gz` is the requested `status.csv`, compressed with gzip. Pandas can read it directly. Status `time` uses `%Y/%m/%d %H:%M:%S`; original recorded seconds are retained. It is not a filled one-row-per-minute grid. Missing snapshots, long gaps and invalid/offline states must be treated explicitly by the estimator.

The trip file uses the original reader's field names: `id`, `duration`, `start_date`, `start_station_name`, `start_station_id`, `end_date`, `end_station_name`, `end_station_id`, `bike_id`, `subscription_type`. Dates use `%m/%d/%Y %H:%M`; `duration` is **seconds**. Rider ZIP codes are omitted. `Subscriber` means member; `Customer` means casual. The extra event file uses ISO local timestamps, `pickup`/`return`, and `internal`/`external` boundary labels. Its `split` is `context`, `training` or `validation`.

Use the existing [V3 station dimension](../model_inputs_v3/station.csv) for station names, coordinates and `dock_count`.

## Scope and matching rules

- Events are selected from **8 February 2015 23:30 onward** to allow up to 30 minutes of preceding context at the study boundary. Status includes an additional 90-second anchor margin: **8 February 23:28:30 through 20 April 00:01:30 inclusive**. Context and anchors are observations only; exclude them from the 70-day output and evaluation. The manifest records actual exported counts.
- A complete trip is retained if either selected-station endpoint falls in the event window. Its other endpoint may be outside the 34 stations or outside the time window. Filter **each endpoint separately** when constructing demand. Do not discard a boundary trip just because its other station is outside the cohort. The supplied `trip_events.csv.gz` has already applied the endpoint scope and is easier to use for this purpose.
- V3 exposure uses a valid preceding state and a positive snapshot gap of at most **90 seconds**. Both-zero, negative and missing states are not valid availability. A long gap is unknown exposure, not a continuous stockout. Keep rate numerators and exposure denominators on the same valid intervals. The 90-second rule is an analytical assumption, not a guaranteed sampling frequency.
- Timestamps remain recorded naive local time. **8 March 2015 is the DST transition day**; preserve and flag the recorded gap. No timestamps have been repaired or shifted. Trip timestamps have minute precision, while status has seconds: document alignment and ties, and reconcile observed trips during empty/full periods before estimating missed demand.
- Preserve the chronological split. Fit historical fallback rates using training information only; predecessor windows must use only information available before the episode. Context availability does not guarantee enough usable preceding observations, so retain the agreed fallback and quality flags.

The agreed estimator still needs Fu Yan and Hong Jin to reconcile predecessor-period rates, historical fallback, served-trip subtraction, return demand, rider splits and validation, then produce the model-compatible station-date-hour demand CSV. Supplying these observations does not approve or finalize either estimator.

## Loading

From a cloned repository, with pandas installed:

```python
from pathlib import Path
import pandas as pd

folder = Path('output/sf_bikeshare/demand_estimation_inputs_v3')
status = pd.read_csv(folder / 'status.csv.gz')
status['time'] = pd.to_datetime(status['time'], format='%Y/%m/%d %H:%M:%S')
trips = pd.read_csv(folder / 'trip.csv.gz')
events = pd.read_csv(folder / 'trip_events.csv.gz', parse_dates=['event_at'])
core_events = events.loc[events['in_study_window']].copy()
```

Fu Yan's existing reader accepts the gzip paths directly because `pandas.read_csv` infers compression. It still needs the agreed estimator changes. If a tool strictly requires uncompressed filenames, decompress these two files locally; keep full source files and uncompressed copies out of Git.

## Verification and reproduction

All **18 checks passed**: three file row-count and exact-value readbacks; cohort, uniqueness and timestamp checks; exact agreement with V3 endpoint events; member/casual pickup/return counts in every station-hour; reconstruction of V3 observed, empty and full exposure in every station-hour; and unchanged frozen V3 files.

Core totals are **55,179 member + 7,064 casual pickups = 62,243**, and **55,234 member + 7,092 casual returns = 62,326**. These are completed service, not unconstrained demand. Snapshot and event extracts preserve the existing source observations without imputation.

With the original local source database and V3 database available, run:

```powershell
python sf_bikeshare/export_minute_demand_inputs.py
```

The [exporter](../../../sf_bikeshare/export_minute_demand_inputs.py) opens both databases read-only and writes only this separate supplement. Source provenance remains in [source_manifest.json](../source_manifest.json); original dataset terms still apply. No external data was added.
