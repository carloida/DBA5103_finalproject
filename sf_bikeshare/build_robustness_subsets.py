"""Build separate observed-data cases for ROBUSTNESS TESTING ONLY.

The frozen V3 reference builder and dataset remain unchanged. This case-aware
builder preserves all 21 V3 table schemas and the 51-column hourly feature schema.
Run: python sf_bikeshare/build_robustness_subsets.py --case all
Road cache fetch: add --fetch-road-matrix (one new matrix per station cohort).
No demand estimator, optimizer, policy evaluation or financial calibration is run.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import csv
import hashlib
import json
import math
import urllib.request

import duckdb

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'output/sf_bikeshare'
REFERENCE = BASE / 'model_inputs_v3'
SUITE = BASE / 'robustness_testing'
START = '2015-02-09'
END = '2015-04-20'
US_GALLON_LITRES = 3.785411784
TEAM_DOC = 'https://docs.google.com/document/d/12mtigIDA4NQ2ycOh-fxOVmE1-lP0h9YF6kfvWXMp1z0/edit'
BOARD = 'https://www.sfmta.com/sites/default/files/projects/10.16.2013%20Bike%20Share%20Open%20House%20Boards.pdf'
APRIL = 'https://www.baaqmd.gov/~/media/files/communications-and-outreach/publications/news-releases/2015/2015-022-babs-500000-041315.pdf'


CASES = {
 'R1_san_jose_2015_feb_apr': dict(city='San Jose',start='2015-02-09',stations=16,cutoff='2014-04-09'),
 'R2_sf_2014_jun_aug': dict(city='San Francisco',start='2014-06-02',stations=34,cutoff='2013-08-29'),
 'R3_san_jose_2014_jun_aug': dict(city='San Jose',start='2014-06-02',stations=16,cutoff='2014-04-09'),
 'R4_sf_2015_apr_jun': dict(city='San Francisco',start='2015-04-20',stations=34,cutoff='2013-08-29'),
 'R5_san_jose_2015_apr_jun': dict(city='San Jose',start='2015-04-20',stations=16,cutoff='2014-04-09'),
}

def dst_date_sql(start,end):
    dates=[]
    for year in range(int(start[:4]),int(end[:4])+1):
        # US rules in force throughout the 2013-2015 source history.
        march=datetime(year,3,8)
        november=datetime(year,11,1)
        for date in [march+timedelta(days=(6-march.weekday())%7),november+timedelta(days=(6-november.weekday())%7)]:
            dates.append("DATE '"+date.strftime('%Y-%m-%d')+"'")
    return ', '.join(dates)

def reference_schema():
    result={}
    with (REFERENCE/'data_dictionary.csv').open(encoding='utf-8',newline='') as stream:
        for r in csv.DictReader(stream):
            result.setdefault(r['table'],[]).append((r['column'],r['sql_type']))
    return result

def clone_reference_table(con,name,schemas):
    ddl=', '.join('"'+c+'" '+t for c,t in schemas[name])
    con.execute(f'CREATE OR REPLACE TABLE {name} ({ddl})')
    con.execute(f"INSERT INTO {name} SELECT * FROM read_csv_auto({quote((REFERENCE/(name+'.csv')).as_posix())})")


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def records(con, sql):
    cur = con.execute(sql)
    return [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]


def write_csv(path, rows, fields=None):
    fields = fields or list(rows[0])
    with Path(path).open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def road_matrix(stations, fetch, city):
    """Cache one response; never silently substitute air distances for road legs."""
    cache = ROOT / ('tmp/sf_v3_osrm' if city=='San Francisco' else 'tmp/sf_robustness_osrm/san_jose')
    cache.mkdir(parents=True, exist_ok=True)
    response_path = cache / 'response.json'
    metadata_path = cache / 'metadata.json'
    coords = ';'.join(f"{s['longitude']:.7f},{s['latitude']:.7f}" for s in stations)
    url = f'https://router.project-osrm.org/table/v1/driving/{coords}?annotations=distance,duration'
    signature = hashlib.sha256(coords.encode()).hexdigest()
    if response_path.exists() and metadata_path.exists():
        meta = json.loads(metadata_path.read_text(encoding='utf-8'))
        if meta.get('coordinate_sha256') == signature:
            assert meta['response_sha256'] == digest(response_path), 'Road cache checksum'
            return json.loads(response_path.read_text(encoding='utf-8')), meta
    if not fetch:
        return None, {'status': 'not_fetched', 'url': url}
    print(f'Fetching one {len(stations)}-by-{len(stations)} current driving matrix from OSRM', flush=True)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'SF-Bikeshare-Academic-Input-Preparation/3.0'})
        with urllib.request.urlopen(req, timeout=45) as response:
            raw = response.read()
        result = json.loads(raw)
        if result.get('code') != 'Ok':
            raise ValueError(f"OSRM response: {result.get('code')}")
        n = len(stations)
        if any(len(result[k]) != n or any(len(row) != n for row in result[k])
               for k in ['distances', 'durations']):
            raise ValueError('Unexpected road-matrix shape')
        response_path.write_bytes(raw)
        meta = dict(status='fetched', coordinate_sha256=signature,
                    response_sha256=digest(response_path), url=url,
                    accessed_at_utc=datetime.now(timezone.utc).isoformat(),
                    station_order=[s['station_id'] for s in stations],
                    data_version=result.get('data_version'), profile='driving',
                    interpretation='Current default driving estimates; not historical 2015 traffic or truck-access certification')
        metadata_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
        return result, meta
    except Exception as exc:
        return None, {'status': 'fetch_failed', 'url': url, 'error': str(exc),
                      'interpretation': 'Road distance/time left NULL; great-circle distances remain separately labeled'}


def build(case_id, fetch_road=False):
    cfg=CASES[case_id]
    OUT=SUITE/case_id
    START=cfg['start']
    END=(datetime.fromisoformat(START)+timedelta(weeks=10)).strftime('%Y-%m-%d')
    TRAIN_END=(datetime.fromisoformat(START)+timedelta(weeks=8)).strftime('%Y-%m-%d')
    N=cfg['stations']
    schemas=reference_schema()
    dst_sql=dst_date_sql(START,END)
    OUT.mkdir(parents=True, exist_ok=True)
    source = BASE / 'sf_bikeshare.duckdb'
    candidate = BASE / 'subset_assessment/candidate_observed_station_hours.parquet'
    source_stat = source.stat()
    original_candidate_hash = digest(candidate)
    con = duckdb.connect(str(OUT / 'robustness_case.duckdb'))
    con.execute("SET memory_limit='2GB'")
    con.execute('SET threads=4')
    con.execute(f'ATTACH {quote(source.as_posix())} AS source (READ_ONLY)')
    validations = []

    def check(name, sql, expected=0):
        actual = con.execute(sql).fetchone()[0]
        validations.append(dict(check=name, expected=expected, actual=actual, passed=actual == expected))
        if actual != expected:
            raise AssertionError(f'{name}: expected {expected}, got {actual}')

    print('Building V3 station, calendar and journey tables', flush=True)
    con.execute('BEGIN TRANSACTION')
    con.execute(f"""
    CREATE OR REPLACE TABLE station AS
    SELECT * FROM source.station WHERE city={quote(cfg['city'])}
      AND installation_date<=DATE {quote(cfg['cutoff'])} ORDER BY station_id;
    CREATE OR REPLACE TABLE model_calendar AS
    SELECT hour_start, hour_start::DATE service_date,
      extract('hour' FROM hour_start)::INTEGER AS "hour",
      extract('isodow' FROM hour_start)::INTEGER iso_weekday,
      CASE WHEN extract('isodow' FROM hour_start)<=5 THEN 'Weekday' ELSE 'Weekend' END day_type,
      CASE WHEN hour_start<TIMESTAMP '{TRAIN_END}' THEN 'training' ELSE 'validation' END split,
      hour_start::DATE IN ({dst_sql}) dst_transition_date_flag
    FROM generate_series(TIMESTAMP '{START}', TIMESTAMP '{END}'-INTERVAL 1 HOUR, INTERVAL 1 HOUR) h(hour_start);
    CREATE OR REPLACE TABLE customer_journeys_observed AS
    SELECT t.trip_id,t.start_station_id,t.end_station_id,t.started_at,t.ended_at,
      date_trunc('hour',t.started_at) departure_hour,
      date_trunc('hour',t.ended_at) arrival_hour,
      date_diff('hour',date_trunc('hour',t.started_at),date_trunc('hour',t.ended_at)) arrival_slot_offset_hours,
      t.duration_seconds, date_diff('second',t.started_at,t.ended_at) elapsed_clock_seconds,
      t.subscription_type,t.long_trip,t.duration_clock_mismatch,
      t.duration_seconds>1800 over_30_minutes,
      a.station_id IS NOT NULL origin_in_cohort,b.station_id IS NOT NULL destination_in_cohort,
      t.started_at>=TIMESTAMP '{START}' AND t.started_at<TIMESTAMP '{END}' departure_in_window,
      t.ended_at>=TIMESTAMP '{START}' AND t.ended_at<TIMESTAMP '{END}' arrival_in_window,
      CASE WHEN a.station_id IS NOT NULL AND b.station_id IS NOT NULL THEN 'internal'
           WHEN a.station_id IS NOT NULL THEN 'outbound' ELSE 'inbound' END boundary_type
    FROM source.valid_trip t LEFT JOIN station a ON t.start_station_id=a.station_id
      LEFT JOIN station b ON t.end_station_id=b.station_id
    WHERE (a.station_id IS NOT NULL OR b.station_id IS NOT NULL)
      AND t.started_at<TIMESTAMP '{END}' AND t.ended_at>=TIMESTAMP '{START}';
    CREATE OR REPLACE TEMP TABLE selected_status AS
    SELECT st.* FROM source.status_intervals st JOIN station s USING(station_id)
    WHERE observed_at>=TIMESTAMP '{START}'-INTERVAL 10 MINUTES AND observed_at<TIMESTAMP '{END}';
    CREATE OR REPLACE TEMP TABLE endpoint_events AS
    SELECT trip_id,start_station_id station_id,end_station_id other_station_id, started_at event_at,
      'pickup' event_type,subscription_type,boundary_type FROM customer_journeys_observed
      WHERE origin_in_cohort AND departure_in_window
    UNION ALL
    SELECT trip_id,end_station_id,start_station_id,ended_at,'return',subscription_type,boundary_type
      FROM customer_journeys_observed WHERE destination_in_cohort AND arrival_in_window;
    CREATE OR REPLACE TABLE observed_trip_events AS
    WITH joined AS (
      SELECT e.*,st.observed_at source_snapshot_time,st.next_observed_at,st.valid_state,
        st.bikes_available,st.docks_available,
        coalesce(st.valid_state AND e.event_at<st.next_observed_at
          AND date_diff('second',st.observed_at,st.next_observed_at)>0
          AND date_diff('second',st.observed_at,st.next_observed_at)<=90,FALSE) in_valid_exposure
      FROM endpoint_events e ASOF LEFT JOIN selected_status st
        ON e.station_id=st.station_id AND e.event_at>=st.observed_at
    ) SELECT trip_id,station_id,other_station_id,event_at,date_trunc('hour',event_at) hour_start,
      event_type,subscription_type,boundary_type,source_snapshot_time,in_valid_exposure,
      coalesce(in_valid_exposure AND bikes_available>0,FALSE) in_bike_available_exposure,
      coalesce(in_valid_exposure AND docks_available>0,FALSE) in_dock_available_exposure,
      source_snapshot_time=event_at snapshot_timestamp_tie
    FROM joined;
    """)

    print('Building dense rider-split panel and matched demand-estimation numerators', flush=True)
    aggregates = []
    for label, rider in [('subscriber', 'Subscriber'), ('customer', 'Customer'), ('unknown', None)]:
        clause = f'subscription_type={quote(rider)}' if rider else "coalesce(subscription_type,'') NOT IN ('Subscriber','Customer')"
        for event, noun in [('pickup', 'pickups'), ('return', 'returns')]:
            condition = f"event_type='{event}' AND {clause}"
            aggregates.append(f"count(*) FILTER(WHERE {condition})::INTEGER {label}_{noun}")
            if rider:
                aggregates.append(f"count(*) FILTER(WHERE {condition} AND in_valid_exposure)::INTEGER {label}_{noun}_valid_exposure")
                availability = 'in_bike_available_exposure' if event == 'pickup' else 'in_dock_available_exposure'
                aggregates.append(f"count(*) FILTER(WHERE {condition} AND {availability})::INTEGER {label}_{noun}_available_exposure")
    for event, noun in [('pickup', 'pickups'), ('return', 'returns')]:
        for scope in ['internal', 'boundary']:
            condition = "boundary_type='internal'" if scope == 'internal' else "boundary_type<>'internal'"
            aggregates.append(f"count(*) FILTER(WHERE event_type='{event}' AND {condition})::INTEGER {scope}_{noun}")
    aggregates.append('count(*) FILTER(WHERE snapshot_timestamp_tie)::INTEGER timestamp_tied_events')
    con.execute(f"CREATE OR REPLACE TEMP TABLE hourly_events AS SELECT station_id,hour_start,{','.join(aggregates)} FROM observed_trip_events GROUP BY 1,2")
    new_fields = [row[0] for row in con.execute('DESCRIBE hourly_events').fetchall() if row[0] not in ['station_id', 'hour_start']]
    coalesced = ','.join(f'coalesce(e.{n},0)::INTEGER {n}' for n in new_fields)
    con.execute(f"""
    CREATE OR REPLACE TABLE station_hour_observed AS
    SELECT p.* EXCLUDE(temperature_f,wind_mph,precipitation_numeric_inches),
      (p.temperature_f-32.0)*5.0/9.0 temperature_c,
      p.wind_mph*1.609344 wind_kmh,
      p.precipitation_numeric_inches*25.4 precipitation_mm,
      c.service_date,c.iso_weekday,c.split,c.dst_transition_date_flag,
      {coalesced},p.departures-p.arrivals net_outflow,
      p.observed_seconds/3600.0 status_coverage_fraction,
      p.observed_seconds-p.empty_seconds bike_available_seconds,
      p.observed_seconds-p.full_seconds dock_available_seconds,
      p.empty_seconds/nullif(p.observed_seconds,0) empty_exposure_fraction,
      p.full_seconds/nullif(p.observed_seconds,0) full_exposure_fraction,
      coalesce(p.observed_seconds,0)=0 status_exposure_missing,
      coalesce(p.static_capacity_mismatch_seconds,0)>0 capacity_mismatch_flag
    FROM source.station_hour_panel p JOIN station s USING(station_id)
      JOIN model_calendar c USING(hour_start) LEFT JOIN hourly_events e USING(station_id,hour_start);
    CREATE OR REPLACE TABLE boundary_flows_hourly AS
    SELECT p.station_id,p.hour_start,p.split,
      count(*) FILTER(WHERE e.event_type='pickup' AND e.subscription_type='Subscriber')::INTEGER subscriber_outflows,
      count(*) FILTER(WHERE e.event_type='pickup' AND e.subscription_type='Customer')::INTEGER customer_outflows,
      count(*) FILTER(WHERE e.event_type='return' AND e.subscription_type='Subscriber')::INTEGER subscriber_inflows,
      count(*) FILTER(WHERE e.event_type='return' AND e.subscription_type='Customer')::INTEGER customer_inflows,
      p.boundary_pickups total_outflows,p.boundary_returns total_inflows
    FROM station_hour_observed p LEFT JOIN observed_trip_events e
      ON p.station_id=e.station_id AND p.hour_start=e.hour_start AND e.boundary_type<>'internal'
    GROUP BY p.station_id,p.hour_start,p.split,p.boundary_pickups,p.boundary_returns;
    CREATE OR REPLACE TABLE customer_od_hourly_observed AS
    SELECT start_station_id,end_station_id,departure_hour,arrival_hour,arrival_slot_offset_hours,
      subscription_type,boundary_type,origin_in_cohort,destination_in_cohort,departure_in_window,arrival_in_window,
      count(*)::INTEGER observed_trips,avg(duration_seconds) mean_reported_duration_seconds,
      count(*) FILTER(WHERE long_trip)::INTEGER long_trips,
      count(*) FILTER(WHERE duration_clock_mismatch)::INTEGER duration_clock_mismatches
    FROM customer_journeys_observed GROUP BY ALL;
    """)

    print('Auditing capacity and selecting preceding opening snapshots', flush=True)
    con.execute(f"""
    CREATE OR REPLACE TABLE station_capacity_audit AS
    SELECT s.*,count(st.observed_at) valid_snapshot_count,
      count(*) FILTER(WHERE st.bikes_available+st.docks_available<>s.dock_count) capacity_mismatch_count,
      min(st.bikes_available+st.docks_available) min_effective_capacity,
      max(st.bikes_available+st.docks_available) max_effective_capacity,
      mode(st.bikes_available+st.docks_available) mode_effective_capacity,
      s.dock_count candidate_static_model_capacity,
      CASE WHEN count(st.observed_at)=0 THEN 'no_valid_status'
           WHEN count(*) FILTER(WHERE st.bikes_available+st.docks_available<>s.dock_count)>0
           THEN 'static_capacity_has_mismatches_review_required' ELSE 'static_capacity_matches_selected_status' END capacity_review_status,
      'station.csv dock_count; effective status totals are diagnostics, not verified physical overrides' capacity_basis
    FROM station s LEFT JOIN selected_status st ON s.station_id=st.station_id
      AND st.observed_at>=TIMESTAMP '{START}' AND st.valid_state GROUP BY ALL;
    CREATE OR REPLACE TABLE opening_inventory_hourly AS
    WITH joined AS (
      SELECT p.station_id,p.hour_start,p.service_date,p.split,s.dock_count,
        st.observed_at source_snapshot_time,st.bikes_available snapshot_bikes,
        st.docks_available snapshot_docks,st.valid_state,
        date_diff('second',st.observed_at,p.hour_start) snapshot_age_seconds
      FROM station_hour_observed p JOIN station s USING(station_id)
      ASOF LEFT JOIN selected_status st ON p.station_id=st.station_id AND p.hour_start>=st.observed_at
    ), flags AS (
      SELECT *,CASE WHEN source_snapshot_time IS NULL THEN 'missing_preceding_snapshot'
        WHEN NOT valid_state THEN 'invalid_latest_snapshot'
        WHEN snapshot_age_seconds>90 THEN 'stale_over_90_seconds' ELSE 'valid_within_90_seconds' END inventory_quality
      FROM joined
    ) SELECT station_id,hour_start,service_date,split,source_snapshot_time,snapshot_age_seconds,
      snapshot_bikes,snapshot_docks,snapshot_bikes+snapshot_docks snapshot_effective_capacity,
      dock_count static_dock_count,inventory_quality,
      CASE WHEN inventory_quality='valid_within_90_seconds' THEN snapshot_bikes END opening_bikes,
      CASE WHEN inventory_quality='valid_within_90_seconds' THEN snapshot_docks END opening_available_docks,
      coalesce(inventory_quality='valid_within_90_seconds' AND snapshot_bikes<=dock_count,FALSE) usable_with_static_bike_bounds,
      coalesce(snapshot_bikes+snapshot_docks<>dock_count,FALSE) static_capacity_mismatch,
      source_snapshot_time=hour_start snapshot_at_boundary_flag
    FROM flags;
    CREATE OR REPLACE TABLE opening_inventory_daily AS
    SELECT * EXCLUDE(hour_start) FROM opening_inventory_hourly WHERE extract('hour' FROM hour_start)=0;
    CREATE OR REPLACE TABLE day_boundary_calendar AS
    SELECT boundary_at FROM generate_series(TIMESTAMP '{START}',TIMESTAMP '{END}',INTERVAL 1 DAY) d(boundary_at);
    CREATE OR REPLACE TABLE customer_in_transit_day_boundaries AS
    SELECT d.boundary_at,j.start_station_id,j.end_station_id,j.subscription_type,j.boundary_type,
      j.origin_in_cohort,j.destination_in_cohort,j.arrival_hour,count(*)::INTEGER observed_trips_in_transit,
      count(*) FILTER(WHERE j.long_trip)::INTEGER long_trips,
      count(*) FILTER(WHERE j.duration_clock_mismatch)::INTEGER duration_clock_mismatches
    FROM day_boundary_calendar d JOIN customer_journeys_observed j
      ON j.started_at<d.boundary_at AND j.ended_at>d.boundary_at GROUP BY ALL;
    CREATE OR REPLACE TABLE customer_events_at_day_boundaries AS
    SELECT d.boundary_at,j.start_station_id,j.end_station_id,j.subscription_type,
      count(*) FILTER(WHERE j.started_at=d.boundary_at)::INTEGER departures_at_boundary,
      count(*) FILTER(WHERE j.ended_at=d.boundary_at)::INTEGER arrivals_at_boundary
    FROM day_boundary_calendar d JOIN customer_journeys_observed j
      ON j.started_at=d.boundary_at OR j.ended_at=d.boundary_at GROUP BY ALL;
    CREATE OR REPLACE TABLE station_day_quality AS
    SELECT p.station_id,p.service_date,p.split,count(*) station_hours,
      sum(p.departures) pickups,sum(p.arrivals) returns,
      sum(coalesce(p.observed_seconds,0))/(24*3600.0) status_coverage_fraction,
      sum(coalesce(p.empty_seconds,0))/nullif(sum(p.observed_seconds),0) empty_exposure_fraction,
      sum(coalesce(p.full_seconds,0))/nullif(sum(p.observed_seconds),0) full_exposure_fraction,
      count(*) FILTER(WHERE p.capacity_mismatch_flag) hours_with_capacity_mismatch,
      max(o.inventory_quality) opening_inventory_quality,
      max(o.opening_bikes) opening_bikes,max(o.opening_available_docks) opening_available_docks,
      bool_or(p.dst_transition_date_flag) dst_transition_date_flag
    FROM station_hour_observed p JOIN opening_inventory_daily o USING(station_id,service_date,split) GROUP BY ALL;
    """)

    stations = records(con, 'SELECT * FROM station ORDER BY station_id')
    road, road_meta = road_matrix(stations, fetch_road,cfg['city'])
    con.execute('''CREATE OR REPLACE TABLE station_distances (
      from_station_id INTEGER,to_station_id INTEGER,great_circle_km DOUBLE,
      road_distance_km DOUBLE,driving_minutes DOUBLE,
      origin_snap_distance_metres DOUBLE,destination_snap_distance_metres DOUBLE,
      road_source_id VARCHAR,road_profile VARCHAR,road_data_version VARCHAR,road_accessed_at_utc VARCHAR,
      distance_quality VARCHAR)''')
    distance_rows = []
    for i, a in enumerate(stations):
        for j, b in enumerate(stations):
            lat1, lat2 = math.radians(a['latitude']), math.radians(b['latitude'])
            delta_lat, delta_lon = lat2-lat1, math.radians(b['longitude']-a['longitude'])
            hav = math.sin(delta_lat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(delta_lon/2)**2
            km = 2*6371.0088*math.asin(math.sqrt(min(1.0, hav)))
            metres = road['distances'][i][j] if road else None
            seconds = road['durations'][i][j] if road else None
            origin_snap = road['sources'][i].get('distance') if road else None
            dest_snap = road['destinations'][j].get('distance') if road else None
            distance_rows.append((a['station_id'],b['station_id'],km,
              None if metres is None else metres/1000,
              None if seconds is None else seconds/60,origin_snap,dest_snap,
              'osrm_current_driving' if road else None,'driving' if road else None,
              road_meta.get('data_version'),road_meta.get('accessed_at_utc'),
              'current_car_routing_proxy_not_2015_truck_route' if metres is not None else 'great_circle_only_road_unknown'))
    con.executemany('INSERT INTO station_distances VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', distance_rows)

    print('Cloning reference table schemas and labeling case-specific gaps',flush=True)
    for table in ['external_sources','tariff_reference','revenue_allocation_scenarios',
                  'operating_parameter_register','teammate_requirements','model_decisions_required']:
        clone_reference_table(con,table,schemas)
    con.execute("UPDATE external_sources SET source_url=?, source_date=?, evidence_status=? WHERE source_id='osrm_current_driving'",
                [road_meta.get('url',''),road_meta.get('accessed_at_utc',''),road_meta['status']])
    con.execute("UPDATE tariff_reference SET evidence_status='historical_benchmark_case_applicability_review', interpretation=interpretation || ' Robustness case: verify geography, date, plan applicability and selected economic interpretation.'")
    con.execute("UPDATE operating_parameter_register SET notes=notes || ' Frozen V3 reference value was ' || cast(value AS VARCHAR) || ' USD/litre. No case-matched value is selected; agree a common-price benchmark or obtain period-specific evidence.', value=NULL, evidence_status='reference_only_case_value_unselected' WHERE parameter LIKE 'gasoline_%'")
    con.execute("UPDATE teammate_requirements SET status='reference_request_not_case_approval', remaining_action='Robustness data prepared separately; model decisions pending. ' || remaining_action")
    con.execute("INSERT INTO model_decisions_required VALUES ('Robustness case economic applicability','Jason/Joohee','pending_agreement','Do not treat frozen 2015 tariffs or gasoline entries as case-matched costs; values remain scenarios or unselected')")
    con.execute("INSERT INTO model_decisions_required VALUES ('Unusable daily opening rule','Carlo/Joohee','pending_agreement','Retain all observed rows and flags; agree common fallback or complete-day exclusion before policy evaluation')")
    con.execute(f"""CREATE OR REPLACE TEMP TABLE source_scope AS
      SELECT p.*,CASE WHEN hour_start<TIMESTAMP '{TRAIN_END}' THEN 'training' ELSE 'validation' END split
      FROM source.station_hour_panel p JOIN station s USING(station_id)
      WHERE hour_start>=TIMESTAMP '{START}' AND hour_start<TIMESTAMP '{END}'""")

    print('Checking independent endpoint, OD, exposure, opening and distance reconciliations', flush=True)
    check('expected station count','SELECT count(*) FROM station',N)
    check('1680 recorded calendar hours','SELECT count(*) FROM model_calendar',1680)
    check('complete dense station hours','SELECT count(*) FROM station_hour_observed',N*1680)
    check('station hour keys unique','SELECT count(*)-count(DISTINCT (station_id,hour_start)) FROM station_hour_observed')
    check('complete station-day opening grid','SELECT count(*) FROM opening_inventory_daily',N*70)
    check('hourly opening keys unique','SELECT count(*)-count(DISTINCT (station_id,hour_start)) FROM opening_inventory_hourly')
    check('daily opening keys unique','SELECT count(*)-count(DISTINCT (station_id,service_date)) FROM opening_inventory_daily')
    check('journey keys unique','SELECT count(*)-count(DISTINCT trip_id) FROM customer_journeys_observed')
    check('endpoint keys unique',"SELECT count(*)-count(DISTINCT (trip_id,event_type)) FROM observed_trip_events")
    check('rider splits reconcile row by row','SELECT count(*) FROM station_hour_observed WHERE subscriber_pickups+customer_pickups+unknown_pickups<>departures OR subscriber_returns+customer_returns+unknown_returns<>arrivals')
    check('no unexpected rider labels','SELECT sum(unknown_pickups+unknown_returns) FROM station_hour_observed')
    check('internal plus boundary reconciles','SELECT count(*) FROM station_hour_observed WHERE internal_pickups+boundary_pickups<>departures OR internal_returns+boundary_returns<>arrivals')
    check('all departures match original source scope',f"SELECT abs((SELECT sum(departures) FROM station_hour_observed)-(SELECT sum(departures) FROM source_scope))")
    check('all arrivals match original source scope',f"SELECT abs((SELECT sum(arrivals) FROM station_hour_observed)-(SELECT sum(arrivals) FROM source_scope))")
    check('original exposure fields unchanged',f"""SELECT count(*) FROM station_hour_observed a JOIN source_scope b USING(station_id,hour_start)
      WHERE a.observed_seconds IS DISTINCT FROM b.observed_seconds OR a.empty_seconds IS DISTINCT FROM b.empty_seconds
        OR a.full_seconds IS DISTINCT FROM b.full_seconds OR a.split IS DISTINCT FROM b.split""")
    for new_field, old_field, inverse in [
      ('temperature_c','temperature_f','a.temperature_c*9.0/5.0+32.0'),
      ('wind_kmh','wind_mph','a.wind_kmh/1.609344'),
      ('precipitation_mm','precipitation_numeric_inches','a.precipitation_mm/25.4'),
    ]:
        check(f'{new_field} round-trip values and missingness',f"""SELECT count(*) FROM station_hour_observed a
          JOIN source_scope b USING(station_id,hour_start)
          WHERE (a.{new_field} IS NULL)<>(b.{old_field} IS NULL)
             OR abs(({inverse})-b.{old_field})>1e-9""")
    check('working columns use metric measurements',"""SELECT count(*) FROM information_schema.columns
      WHERE table_catalog=current_database() AND column_name IN
      ('great_circle_miles','road_distance_miles','temperature_f','wind_mph','precipitation_numeric_inches')""")
    check('operating parameter units metric',"SELECT count(*) FROM operating_parameter_register WHERE unit IN ('USD/gallon','USD/mile','miles/gallon')")
    check('OD trips reconcile','SELECT abs((SELECT sum(observed_trips) FROM customer_od_hourly_observed)-(SELECT count(*) FROM customer_journeys_observed))')
    check('endpoint-relevant journeys match original trip records',f"""SELECT abs(
      (SELECT count(*) FROM customer_journeys_observed WHERE (origin_in_cohort AND departure_in_window) OR (destination_in_cohort AND arrival_in_window))-
      (SELECT count(*) FROM source.valid_trip WHERE
       (start_station_id IN (SELECT station_id FROM station) AND started_at>=TIMESTAMP '{START}' AND started_at<TIMESTAMP '{END}') OR
       (end_station_id IN (SELECT station_id FROM station) AND ended_at>=TIMESTAMP '{START}' AND ended_at<TIMESTAMP '{END}')))""")
    check('OD departure endpoints reconcile',"SELECT abs((SELECT sum(observed_trips) FROM customer_od_hourly_observed WHERE origin_in_cohort AND departure_in_window)-(SELECT sum(departures) FROM station_hour_observed))")
    check('OD arrival endpoints reconcile',"SELECT abs((SELECT sum(observed_trips) FROM customer_od_hourly_observed WHERE destination_in_cohort AND arrival_in_window)-(SELECT sum(arrivals) FROM station_hour_observed))")
    check('boundary class splits reconcile','SELECT count(*) FROM boundary_flows_hourly WHERE subscriber_outflows+customer_outflows<>total_outflows OR subscriber_inflows+customer_inflows<>total_inflows')
    for rider in ['Subscriber','Customer']:
        label=rider.lower()
        for event, noun, station_field, time_field in [('pickup','pickups','start_station_id','started_at'),('return','returns','end_station_id','ended_at')]:
            check(f'{rider} {event} totals match source trip records', f"""SELECT abs(
              (SELECT sum({label}_{noun}) FROM station_hour_observed)-
              (SELECT count(*) FROM source.valid_trip t JOIN station s ON t.{station_field}=s.station_id
                WHERE t.subscription_type={quote(rider)} AND t.{time_field}>=TIMESTAMP '{START}' AND t.{time_field}<TIMESTAMP '{END}'))""")
    check('bounded exposure','SELECT count(*) FROM station_hour_observed WHERE observed_seconds<0 OR observed_seconds>3600 OR bike_available_seconds<0 OR dock_available_seconds<0 OR empty_seconds>observed_seconds OR full_seconds>observed_seconds')
    for rider in ['subscriber','customer']:
        for noun in ['pickups','returns']:
            check(f'{rider} {noun} matched numerators bounded',f'SELECT count(*) FROM station_hour_observed WHERE {rider}_{noun}_available_exposure>{rider}_{noun}_valid_exposure OR {rider}_{noun}_valid_exposure>{rider}_{noun}')
    check('no future snapshot openings','SELECT count(*) FROM opening_inventory_hourly WHERE source_snapshot_time>hour_start')
    check('stale or invalid openings are NULL',"SELECT count(*) FROM opening_inventory_hourly WHERE inventory_quality<>'valid_within_90_seconds' AND (opening_bikes IS NOT NULL OR opening_available_docks IS NOT NULL)")
    check('valid opening counts nonnegative','SELECT count(*) FROM opening_inventory_hourly WHERE opening_bikes<0 OR opening_available_docks<0')
    check('distance pair keys unique','SELECT count(*)-count(DISTINCT (from_station_id,to_station_id)) FROM station_distances')
    check('complete directed distance pairs','SELECT count(*) FROM station_distances',N*N)
    check('zero air-distance diagonal','SELECT count(*) FROM station_distances WHERE from_station_id=to_station_id AND abs(great_circle_km)>0.000001')
    check('positive distinct-station air distances','SELECT count(*) FROM station_distances WHERE from_station_id<>to_station_id AND great_circle_km<=0')
    check('positive road values when present','SELECT count(*) FROM station_distances WHERE from_station_id<>to_station_id AND (road_distance_km<=0 OR driving_minutes<=0)')
    check('revenue allocation arithmetic','SELECT count(*) FROM revenue_allocation_scenarios WHERE abs(allocated_revenue_usd_per_trip-pass_price_usd/assumed_trips_per_pass)>0.000000001 OR use_as_marginal_cash_revenue')
    check('all directed road pairs populated','SELECT count(*) FROM station_distances WHERE road_distance_km IS NULL OR driving_minutes IS NULL')
    for table,expected in schemas.items():
        actual=[(r[0],r[1]) for r in con.execute(f'DESCRIBE {table}').fetchall()]
        validations.append(dict(check='exact V3 schema: '+table,expected='match',actual='match' if actual==expected else 'mismatch',passed=actual==expected))
        assert actual==expected,(case_id,table,actual,expected)
    con.execute('COMMIT')

    exports = {
      'station':'station.csv','model_calendar':'model_calendar.csv','station_capacity_audit':'station_capacity_audit.csv',
      'station_hour_observed':'station_hour_observed.csv.gz','opening_inventory_daily':'opening_inventory_daily.csv',
      'opening_inventory_hourly':'opening_inventory_hourly.csv.gz','boundary_flows_hourly':'boundary_flows_hourly.csv.gz',
      'customer_od_hourly_observed':'customer_od_hourly_observed.csv.gz',
      'customer_in_transit_day_boundaries':'customer_in_transit_day_boundaries.csv',
      'customer_events_at_day_boundaries':'customer_events_at_day_boundaries.csv',
      'station_distances':'station_distances.csv','station_day_quality':'station_day_quality.csv',
      'tariff_reference':'tariff_reference.csv','revenue_allocation_scenarios':'revenue_allocation_scenarios.csv',
      'operating_parameter_register':'operating_parameter_register.csv','external_sources':'external_sources.csv',
      'teammate_requirements':'teammate_requirements.csv','model_decisions_required':'model_decisions_required.csv',
    }
    keys = {
      'station':'station_id','model_calendar':'hour_start','station_capacity_audit':'station_id',
      'station_hour_observed':'station_id, hour_start','opening_inventory_daily':'station_id, service_date',
      'opening_inventory_hourly':'station_id, hour_start','boundary_flows_hourly':'station_id, hour_start',
      'customer_journeys_observed':'trip_id','observed_trip_events':'trip_id, event_type',
      'station_distances':'from_station_id, to_station_id','station_day_quality':'station_id, service_date',
      'external_sources':'source_id','tariff_reference':'tariff_id','revenue_allocation_scenarios':'subscription_type, scenario',
      'operating_parameter_register':'parameter','teammate_requirements':'requirement_id','model_decisions_required':'decision',
      'day_boundary_calendar':'boundary_at',
    }
    inventory = []
    dictionary = []
    for table_row in records(con,"SELECT table_name FROM information_schema.tables WHERE table_catalog=current_database() AND table_schema='main' AND table_type='BASE TABLE' ORDER BY table_name"):
        table = table_row['table_name']
        n = con.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
        columns = records(con,f'DESCRIBE {table}')
        inventory.append(dict(table=table,rows=n,columns=len(columns),key=keys.get(table,'all grouping dimensions'),export=exports.get(table,'local_database_only')))
        for col in columns:
            field = col['column_name']
            unit, meaning = field_info(table, field)
            dictionary.append(dict(table=table,column=field,sql_type=col['column_type'],unit=unit,meaning=meaning))
        if table in exports:
            filename = exports[table]
            compression = ", COMPRESSION GZIP" if filename.endswith('.gz') else ''
            # Ordering every exported table by all fields makes the handoff reproducible.
            con.execute(f'COPY (SELECT * FROM {table} ORDER BY ALL) TO {quote((OUT/filename).as_posix())} (FORMAT CSV, HEADER{compression})')
            loaded = con.execute(f'SELECT count(*) FROM read_csv_auto({quote((OUT/filename).as_posix())})').fetchone()[0]
            if loaded != n:
                raise AssertionError(f'Export readback row count for {table}')
    write_csv(OUT/'table_inventory.csv',inventory)
    write_csv(OUT/'data_dictionary.csv',dictionary)
    write_csv(OUT/'validation_checks.csv',validations)
    summary = dict(
      stations=con.execute('SELECT count(*) FROM station').fetchone()[0],
      station_hours=con.execute('SELECT count(*) FROM station_hour_observed').fetchone()[0],
      observed_journeys=con.execute('SELECT count(*) FROM customer_journeys_observed').fetchone()[0],
      endpoint_relevant_journeys=con.execute('SELECT count(*) FROM customer_journeys_observed WHERE (origin_in_cohort AND departure_in_window) OR (destination_in_cohort AND arrival_in_window)').fetchone()[0],
      supplemental_horizon_spanning_journeys=con.execute('SELECT count(*) FROM customer_journeys_observed WHERE NOT ((origin_in_cohort AND departure_in_window) OR (destination_in_cohort AND arrival_in_window))').fetchone()[0],
      long_journeys=con.execute('SELECT count(*) FROM customer_journeys_observed WHERE long_trip').fetchone()[0],
      journey_types=records(con,'SELECT boundary_type,count(*) trips FROM customer_journeys_observed GROUP BY 1 ORDER BY 1'),
      rider_totals=records(con,'SELECT sum(subscriber_pickups) subscriber_pickups,sum(customer_pickups) customer_pickups,sum(subscriber_returns) subscriber_returns,sum(customer_returns) customer_returns,sum(boundary_pickups) boundary_pickups,sum(boundary_returns) boundary_returns FROM station_hour_observed'),
      daily_opening_quality=records(con,'SELECT inventory_quality,count(*) station_days FROM opening_inventory_daily GROUP BY 1 ORDER BY 1'),
      hourly_opening_quality=records(con,'SELECT inventory_quality,count(*) station_hours FROM opening_inventory_hourly GROUP BY 1 ORDER BY 1'),
      capacity_review=records(con,'SELECT capacity_review_status,count(*) stations,sum(capacity_mismatch_count) mismatching_snapshots FROM station_capacity_audit GROUP BY 1 ORDER BY 1'),
      daily_static_capacity_mismatches=con.execute('SELECT count(*) FROM opening_inventory_daily WHERE static_capacity_mismatch').fetchone()[0],
      matched_event_quality=records(con,'SELECT event_type,count(*) events,count(*) FILTER(WHERE in_valid_exposure) in_valid_exposure,count(*) FILTER(WHERE snapshot_timestamp_tie) snapshot_timestamp_ties FROM observed_trip_events GROUP BY 1 ORDER BY 1'),
      road_pairs_available=con.execute('SELECT count(*) FROM station_distances WHERE road_distance_km IS NOT NULL AND driving_minutes IS NOT NULL').fetchone()[0],
      road_max_snap_metres=con.execute('SELECT max(greatest(origin_snap_distance_metres,destination_snap_distance_metres)) FROM station_distances').fetchone()[0],
    )
    definition=dict(case_id=case_id,purpose='ROBUSTNESS TESTING ONLY',city=cfg['city'],
      start=START,end_exclusive=END,training_end_exclusive=TRAIN_END,station_count=N,
      hourly_schema='exactly the 51 V3 columns and SQL types',
      reference_case='D0: output/sf_bikeshare/model_inputs_v3',
      evaluation_status='data_prepared_no_policy_results',
      opening_rule_status='flags preserved; no fallback or evaluation-day exclusions applied',
      economic_status='historical benchmark references only; case-matched operating values unselected')
    (OUT/'case_definition.json').write_text(json.dumps(definition,indent=2),encoding='utf-8')
    assert digest(candidate) == original_candidate_hash, 'V2 file changed'
    assert source.stat().st_size == source_stat.st_size and source.stat().st_mtime_ns == source_stat.st_mtime_ns, 'Source database changed'
    con.execute('DETACH source')
    con.execute('CHECKPOINT')
    con.close()
    files = [dict(path=str(p.relative_to(ROOT)).replace('\\','/'),bytes=p.stat().st_size,sha256=digest(p))
             for p in sorted(OUT.iterdir()) if p.is_file() and p.suffix not in ['.duckdb','.wal'] and p.name not in ['manifest.json','README.md']]
    manifest = dict(version='robustness_v1',case_id=case_id,purpose='ROBUSTNESS TESTING ONLY',city=cfg['city'],training_end_exclusive=TRAIN_END,revision='same_v3_metric_schema',prepared_on='2026-11-18',created_at_utc=datetime.now(timezone.utc).isoformat(),
      source_database='output/sf_bikeshare/sf_bikeshare.duckdb',source_database_opened_read_only=True,
      source_database_bytes=source_stat.st_size,source_manifest_sha256=digest(BASE/'source_manifest.json'),
      v2_sha256_unchanged=original_candidate_hash,script_sha256=digest(Path(__file__)),duckdb_version=duckdb.__version__,
      interval=f'[{START}, {END})',opening_snapshot_max_age_seconds=90,
      working_units=dict(distance='kilometres',snapping_distance='metres',temperature='degrees Celsius',
         wind_speed='kilometres/hour',precipitation='millimetres',fuel='litres',fuel_consumption='litres/100km',
         money='USD',time='seconds/minutes/hours as labeled',coordinates='decimal degrees'),
      unit_conversion_rules=dict(temperature_c='(temperature_f - 32) * 5 / 9',
         wind_kmh='wind_mph * 1.609344',precipitation_mm='precipitation_numeric_inches * 25.4',
         fuel_price_usd_per_litre='source USD/US gallon / 3.785411784',road_distance_km='OSRM metres / 1000'),
      opening_rule='Latest snapshot at or before boundary; invalid/latest stale state yields NULL; no future lookup or fallback imputation',
      trip_exposure_rule='Endpoint matched to preceding valid status interval, positive gap <=90 seconds; numerator uses same intervals as denominator',
      transit_rule='started_at < boundary_at < ended_at; exact-boundary events exported separately for event-order review',
      road_matrix=road_meta,summary=summary,validation_checks_passed=len(validations),
      export_row_count_readbacks_passed=len(exports),tables=inventory,files=files,
      verified_external_pdf_files=[dict(filename=p.name,bytes=p.stat().st_size,sha256=digest(p))
         for p in sorted((ROOT/'tmp/sf_v3_tariffs').glob('*.pdf'))],
      limitations=[
        'Recorded local-clock grid; relevant US DST dates are flagged, not repaired without source timezone evidence',
        'Status snapshots are historical operations, not counterfactual baseline inventory paths',
        'Static dock count retained; effective-capacity discrepancies require review, no invented overrides',
        'Matched endpoint/exposure statistics inherit minute-rounded trip times and snapshot timestamp ties',
        'Observed OD journeys are not latent attempted OD demand; counterfactual served trips must generate consistent later returns',
        'Revenue allocations are team assumptions; no actual payments or incremental contribution inferred',
        'Tariff/allocation tables are historical benchmark references; case-specific price/date applicability and operating values remain unselected',
        'No depot, historical truck route, optimized plan or profit result is created',
      ])
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2,default=str),encoding='utf-8')
    print(json.dumps(dict(summary=summary,checks_passed=len(validations),export_readbacks=len(exports),road_status=road_meta['status']),indent=2,default=str),flush=True)
    return manifest


def field_info(table, field):
    meanings = {
      'subscription_type':('category','Original Subscriber/Customer label; no customer or pass identity'),
      'split':('category','First eight weeks training; last two weeks validation for retrospective robustness evaluation; not a sealed test'),
      'opening_bikes':('bikes','Latest preceding valid snapshot within 90 seconds; NULL when invalid/stale; historical stock only'),
      'opening_available_docks':('docks','Free usable docks in accepted preceding snapshot; not necessarily static capacity minus bikes'),
      'inventory_quality':('category','Quality of latest preceding snapshot; no future lookup or silent fallback'),
      'usable_with_static_bike_bounds':('boolean','Fresh valid stock is at most listed dock_count; does not certify all effective-capacity assumptions'),
      'candidate_static_model_capacity':('docks','Listed station.csv dock count, preserved pending review; not a calibrated override'),
      'capacity_review_status':('category','Whether valid selected snapshots disagree with listed dock count'),
      'net_outflow':('bikes/hour','Completed pickups minus returns; not automatically required relocation volume'),
      'dst_transition_date_flag':('boolean','Relevant US DST transition date; recorded-clock grid retained, not a timezone repair'),
      'allocated_revenue_usd_per_trip':('USD/trip','Team pass-price/trips-per-pass allocation; not observed or incremental cash revenue'),
      'assumed_trips_per_pass':('trips/pass','Jason proposed scenario assumption, not estimated customer usage'),
      'use_as_marginal_cash_revenue':('boolean','False: allocation does not identify additional cash receipts from serving one more trip'),
      'arrival_slot_offset_hours':('recorded-clock hours','Arrival-hour index minus departure-hour index; zero means both events fall in same clock hour'),
      'boundary_type':('category','internal: both endpoints in cohort; outbound/inbound: one endpoint outside cohort'),
      'in_valid_exposure':('boolean','Event lies in a valid status interval whose next-observation gap is positive and <=90 seconds'),
      'snapshot_timestamp_tie':('boolean','Minute-rounded trip endpoint equals status timestamp; ordering within minute is unknown'),
      'snapshot_at_boundary_flag':('boolean','Snapshot recorded exactly at modeled boundary; order relative to tied trip events is unresolved'),
      'source_snapshot_time':('recorded local timestamp','Preceding status timestamp used for the opening/event match'),
      'snapshot_age_seconds':('seconds','Boundary time minus preceding snapshot time'),
      'observed_trips_in_transit':('trips','Observed trips strictly spanning boundary; arrivals/departures exactly at boundary are separate'),
      'great_circle_km':('kilometres','Haversine distance, mean Earth radius 6371.0088 km; not road-route length'),
      'road_distance_km':('kilometres','Directed current OSRM driving leg; NULL if not obtained; not historical truck access'),
      'temperature_c':('degrees Celsius','Existing city-level mean temperature converted as (source Fahrenheit - 32) * 5 / 9; NULL preserved'),
      'wind_kmh':('kilometres/hour','Existing city-level mean wind speed multiplied by 1.609344; NULL preserved'),
      'precipitation_mm':('millimetres','Existing city-level daily precipitation multiplied by 25.4; trace flag retained; NULL preserved'),
      'driving_minutes':('minutes','Current OSRM driving duration / 60; excludes stop setup, handling and historical congestion'),
      'observed_trips':('completed trips','Observed OD aggregate count; latent unmet requests are not included'),
      'status_exposure_missing':('boolean','No valid status exposure in hour; does not mean no demand'),
    }
    if field in meanings:
        return meanings[field]
    if field.endswith('_available_exposure'):
        return 'completed events','Class endpoint count matched to valid nonempty-bike (pickup) or nonfull-dock (return) intervals; use matching available seconds'
    if field.endswith('_valid_exposure'):
        return 'completed events','Class endpoint count restricted to same valid <=90-second status intervals used for observed_seconds'
    if field.endswith('_seconds'):
        return 'seconds','Observed time or duration; missing availability remains NULL'
    if field.endswith('_fraction'):
        return 'fraction 0-1','Ratio using stated valid observed-time denominator; NULL when denominator absent'
    if field.endswith('_pickups') or field.endswith('_returns') or field in ['departures','arrivals']:
        return 'completed events','Endpoint count in recorded local station-hour; zero-filled only for observed trip counts'
    if field.endswith('_inflows') or field.endswith('_outflows'):
        return 'completed events','Observed external-cohort boundary endpoints by arrival/departure hour'
    if field in ['hour_start','departure_hour','arrival_hour','started_at','ended_at','event_at','boundary_at']:
        return 'recorded local timestamp','Naive source clock, no Singapore conversion; DST ambiguity retained'
    if field.endswith('station_id') or field == 'trip_id':
        return 'identifier','Original dataset identifier; external endpoints may be outside the 34-station cohort'
    if field in ['latitude','longitude']:
        return 'decimal degrees','Station.csv coordinate; OSRM request order is longitude,latitude'
    if field in ['dock_count','static_dock_count']:
        return 'docks','Original station.csv listed dock count; status mismatches are retained and flagged'
    return 'see field name / source','Preserved source field or explicitly named diagnostic; see README and source_id links'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=['all']+list(CASES),default='all')
    parser.add_argument('--fetch-road-matrix',action='store_true')
    args=parser.parse_args()
    ids=list(CASES) if args.case=='all' else [args.case]
    SUITE.mkdir(parents=True,exist_ok=True)
    summaries=[]
    for case_id in ids:
        print('\nBUILDING '+case_id,flush=True)
        m=build(case_id,args.fetch_road_matrix)
        summaries.append(dict(case_id=case_id,city=m['city'],interval=m['interval'],
          station_hours=m['summary']['station_hours'],stations=m['summary']['stations'],
          checks=m['validation_checks_passed'],export_readbacks=m['export_row_count_readbacks_passed'],
          purpose='ROBUSTNESS TESTING ONLY'))
    if args.case=='all':
        write_csv(SUITE/'case_inventory.csv',summaries)
    print(json.dumps(summaries,indent=2),flush=True)

if __name__ == '__main__':
    main()
