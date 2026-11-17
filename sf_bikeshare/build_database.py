"""Build an analytical DuckDB database from the four original Bay Area CSV files.

Raw files stay external and unchanged. Status is scanned in full, never sampled.
Run: python sf_bikeshare/build_database.py --source "path/to/SF BAY AREA BIKESHARE DATA"
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import time
import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'sf_bikeshare'
SOURCE_DEFAULT = Path(os.environ.get('SF_BIKESHARE_DATA', ROOT.parents[1] / 'SF BAY AREA BIKESHARE DATA'))

def build(source=SOURCE_DEFAULT, rebuild=False, resume_from=1):
    source = Path(source).resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    files = {n: source / f'{n}.csv' for n in ['station', 'trip', 'weather', 'status']}
    if not all(p.is_file() for p in files.values()):
        raise FileNotFoundError(f'Expected station.csv, trip.csv, weather.csv and status.csv in {source}')
    db = OUT / 'sf_bikeshare.duckdb'
    meta_path = OUT / 'source_manifest.json'
    signature = {n: {'bytes': p.stat().st_size, 'mtime_ns': p.stat().st_mtime_ns} for n,p in files.items()}
    if db.exists() and meta_path.exists() and not rebuild:
        meta = json.loads(meta_path.read_text())
        if meta.get('signature') == signature and meta.get('build_version') == 1:
            print('Using verified, unchanged local database cache.', flush=True)
            return db
        raise ValueError('Source files or builder version changed. Run with --rebuild to refresh the database.')
    con = duckdb.connect(str(db))
    con.execute("SET memory_limit='2GB'")
    con.execute('SET threads=4')
    con.execute(f"SET temp_directory='{(OUT/'duckdb_temp').as_posix()}'")
    def run(label, sql):
        if label[0].isdigit() and int(label.split('/')[0]) < resume_from:
            return
        print(label, flush=True)
        started=time.perf_counter(); con.execute(sql)
        print(f'  completed in {time.perf_counter()-started:.1f}s', flush=True)
    def csv(n):
        return "read_csv('" + files[n].as_posix().replace("'","''") + "', all_varchar=true, nullstr='')"

    run('1/8 Loading station, trip, bike and weather tables', f"""
    CREATE OR REPLACE TABLE station AS
    SELECT try_cast(id AS INTEGER) station_id, name station_name,
           try_cast(lat AS DOUBLE) latitude, try_cast(long AS DOUBLE) longitude,
           try_cast(dock_count AS INTEGER) dock_count, city,
           try_strptime(installation_date,'%m/%d/%Y')::DATE installation_date
    FROM {csv('station')};
    CREATE OR REPLACE TABLE trip AS
    SELECT try_cast(id AS BIGINT) trip_id, try_cast(duration AS BIGINT) duration_seconds,
           try_strptime(start_date,'%m/%d/%Y %H:%M') started_at,
           start_station_name, try_cast(start_station_id AS INTEGER) start_station_id,
           try_strptime(end_date,'%m/%d/%Y %H:%M') ended_at,
           end_station_name, try_cast(end_station_id AS INTEGER) end_station_id,
           try_cast(bike_id AS INTEGER) bike_id, subscription_type,
           zip_code rider_zip_code
    FROM {csv('trip')};
    CREATE OR REPLACE TABLE bike AS SELECT DISTINCT bike_id FROM trip WHERE bike_id IS NOT NULL;
    CREATE OR REPLACE TABLE weather AS
    SELECT * EXCLUDE(date,zip_code), try_strptime(date,'%m/%d/%Y')::DATE weather_date,
           zip_code weather_zip_code,
           CASE WHEN precipitation_inches='T' THEN 0.0 ELSE try_cast(precipitation_inches AS DOUBLE) END precipitation_numeric_inches,
           precipitation_inches='T' trace_precipitation,
           try_cast(mean_temperature_f AS DOUBLE) temperature_f,
           try_cast(mean_wind_speed_mph AS DOUBLE) wind_mph
    FROM {csv('weather')};
    CREATE OR REPLACE TABLE city_weather_map(city VARCHAR PRIMARY KEY, weather_zip_code VARCHAR UNIQUE, mapping_basis VARCHAR);
    INSERT INTO city_weather_map VALUES
      ('San Francisco','94107','Analyst city-level weather proxy; not an observed station ZIP'),
      ('Redwood City','94063','Analyst city-level weather proxy; not an observed station ZIP'),
      ('Palo Alto','94301','Analyst city-level weather proxy; not an observed station ZIP'),
      ('Mountain View','94041','Analyst city-level weather proxy; not an observed station ZIP'),
      ('San Jose','95113','Analyst city-level weather proxy; not an observed station ZIP');
    """)
    # Index only the small dimensions/facts. Raw status key uniqueness is audited below.
    run('2/8 Auditing/enforcing small-table keys', """
    CREATE UNIQUE INDEX IF NOT EXISTS station_pk ON station(station_id);
    CREATE UNIQUE INDEX IF NOT EXISTS trip_pk ON trip(trip_id);
    CREATE UNIQUE INDEX IF NOT EXISTS bike_pk ON bike(bike_id);
    CREATE UNIQUE INDEX IF NOT EXISTS weather_pk ON weather(weather_zip_code,weather_date);
    CREATE OR REPLACE VIEW valid_trip AS
    SELECT t.*, s.city start_city, e.city end_city,
           t.duration_seconds/60.0 duration_minutes,
           t.duration_seconds>86400 long_trip,
           abs(date_diff('second',started_at,ended_at)-duration_seconds)>60 duration_clock_mismatch
    FROM trip t JOIN station s ON t.start_station_id=s.station_id JOIN station e ON t.end_station_id=e.station_id
    WHERE duration_seconds>0 AND ended_at>started_at;
    """)
    run('3/8 Reading ALL station-status observations (large file)', f"""
    CREATE OR REPLACE TABLE status AS
    SELECT try_cast(station_id AS INTEGER) station_id,
           try_cast(bikes_available AS INTEGER) bikes_available,
           try_cast(docks_available AS INTEGER) docks_available,
           coalesce(try_strptime(time,'%Y/%m/%d %H:%M:%S'),try_strptime(time,'%Y-%m-%d %H:%M:%S')) observed_at
    FROM {csv('status')};
    """)
    run('4/8 Auditing status composite keys (full scan)', """
    CREATE OR REPLACE TABLE status_duplicate_keys AS
    SELECT station_id,observed_at,count(*) records,
           count(DISTINCT (bikes_available,docks_available)) distinct_states
    FROM status GROUP BY station_id,observed_at HAVING count(*)>1;
    CREATE OR REPLACE TABLE status_quality AS
    SELECT count(*) source_rows,
      count(*) FILTER(WHERE observed_at IS NULL OR station_id IS NULL OR bikes_available IS NULL OR docks_available IS NULL) parse_or_missing,
      count(*) FILTER(WHERE s.station_id IS NULL) unknown_stations,
      count(*) FILTER(WHERE bikes_available<0 OR docks_available<0) negative_counts,
      count(*) FILTER(WHERE bikes_available=0 AND docks_available=0) both_zero,
      count(*) FILTER(WHERE bikes_available+docks_available<>s.dock_count) static_capacity_mismatches,
      min(observed_at) first_observation,max(observed_at) last_observation,
      count(DISTINCT st.station_id) stations
    FROM status st LEFT JOIN station s USING(station_id);
    """)
    dup = con.execute('SELECT count(*) FROM status_duplicate_keys').fetchone()[0]
    if dup:
        run('Quarantining conflicting status keys; collapsing identical copies', """
        CREATE OR REPLACE TABLE status_deduplicated AS
        SELECT station_id,observed_at,min(bikes_available) bikes_available,min(docks_available) docks_available
        FROM status GROUP BY station_id,observed_at
        HAVING count(DISTINCT (bikes_available,docks_available))=1;
        """)
        base='status_deduplicated'
    else:
        base='status'
    run('5/8 Building time intervals and coverage audits', f"""
    CREATE OR REPLACE TABLE status_intervals AS
    SELECT st.*, lead(observed_at) OVER(PARTITION BY st.station_id ORDER BY observed_at) next_observed_at,
      s.dock_count static_dock_count,
      (bikes_available>=0 AND docks_available>=0 AND bikes_available+docks_available>0
       AND bikes_available IS NOT NULL AND docks_available IS NOT NULL) valid_state
    FROM {base} st JOIN station s USING(station_id) WHERE observed_at IS NOT NULL;
    CREATE OR REPLACE TABLE interval_gap_audit AS
    SELECT CASE WHEN next_observed_at IS NULL THEN 'Last observation'
                WHEN date_diff('second',observed_at,next_observed_at)<=0 THEN 'Nonpositive'
                WHEN date_diff('second',observed_at,next_observed_at)<=90 THEN 'Within 90 seconds'
                WHEN date_diff('second',observed_at,next_observed_at)<=300 THEN '91 seconds to 5 minutes'
                WHEN date_diff('second',observed_at,next_observed_at)<=3600 THEN '5 to 60 minutes'
                ELSE 'Over 60 minutes' END gap_group,
           count(*) intervals,
           sum(date_diff('second',observed_at,next_observed_at)) elapsed_seconds
    FROM status_intervals GROUP BY 1;
    CREATE OR REPLACE TABLE status_month_coverage AS
    SELECT station_id,date_trunc('month',observed_at)::DATE AS month,count(*) observations,
           count(DISTINCT observed_at::DATE) observed_days,
           count(*) FILTER(WHERE NOT valid_state) invalid_or_zero_capacity_states
    FROM status_intervals GROUP BY 1,2;
    """)
    run('6/8 Aggregating bounded, time-weighted availability to station-hours', """
    CREATE OR REPLACE TABLE status_hourly AS
    WITH eligible AS (
      SELECT *,date_trunc('hour',observed_at) hour_start,
             date_trunc('hour',observed_at)+INTERVAL 1 HOUR hour_boundary
      FROM status_intervals WHERE valid_state
      AND date_diff('second',observed_at,next_observed_at)>0
      AND date_diff('second',observed_at,next_observed_at)<=90
    ), pieces AS (
      SELECT station_id,hour_start,bikes_available,docks_available,static_dock_count,
             date_diff('second',observed_at,least(next_observed_at,hour_boundary)) AS interval_seconds
      FROM eligible
      UNION ALL
      SELECT station_id,hour_boundary,bikes_available,docks_available,static_dock_count,
             date_diff('second',hour_boundary,next_observed_at) AS interval_seconds
      FROM eligible WHERE next_observed_at>hour_boundary
    )
    SELECT station_id,hour_start,sum(interval_seconds) observed_seconds,
      sum(CASE WHEN bikes_available=0 THEN interval_seconds ELSE 0 END) empty_seconds,
      sum(CASE WHEN docks_available=0 THEN interval_seconds ELSE 0 END) full_seconds,
      sum(CASE WHEN bikes_available<=2 THEN interval_seconds ELSE 0 END) low_bike_seconds,
      sum(CASE WHEN docks_available<=2 THEN interval_seconds ELSE 0 END) low_dock_seconds,
      sum(interval_seconds*bikes_available)*1.0/sum(interval_seconds) mean_bikes_available,
      sum(interval_seconds*(bikes_available+docks_available))*1.0/sum(interval_seconds) mean_effective_capacity,
      sum(CASE WHEN bikes_available+docks_available<>static_dock_count THEN interval_seconds ELSE 0 END) static_capacity_mismatch_seconds
    FROM pieces WHERE interval_seconds>0 GROUP BY 1,2;
    CREATE UNIQUE INDEX IF NOT EXISTS status_hourly_pk ON status_hourly(station_id,hour_start);
    """)
    run('7/8 Linking trips, availability and city-level weather without multiplying rows', """
    CREATE OR REPLACE TABLE trip_hourly AS
    WITH events AS (
      SELECT start_station_id station_id,date_trunc('hour',started_at) hour_start,1 departures,0 arrivals FROM valid_trip
      UNION ALL
      SELECT end_station_id,date_trunc('hour',ended_at),0,1 FROM valid_trip
    ) SELECT station_id,hour_start,sum(departures)::INTEGER departures,sum(arrivals)::INTEGER arrivals
    FROM events GROUP BY 1,2;
    CREATE OR REPLACE TABLE station_hour_panel AS
    WITH hours AS (
      SELECT unnest(generate_series(date_trunc('day',min(started_at)),date_trunc('day',max(started_at))+INTERVAL 23 HOURS,INTERVAL 1 HOUR)) hour_start
      FROM valid_trip
    )
    SELECT s.station_id,s.city,h.hour_start,
      CASE WHEN extract('isodow' FROM h.hour_start)<=5 THEN 'Weekday' ELSE 'Weekend' END day_type,
      extract('hour' FROM h.hour_start)::INTEGER AS hour,
      coalesce(t.departures,0)::INTEGER departures,coalesce(t.arrivals,0)::INTEGER arrivals,
      a.* EXCLUDE(station_id,hour_start),m.weather_zip_code,
      w.precipitation_numeric_inches,w.trace_precipitation,w.temperature_f,w.wind_mph
    FROM station s CROSS JOIN hours h
    LEFT JOIN trip_hourly t ON s.station_id=t.station_id AND h.hour_start=t.hour_start
    LEFT JOIN status_hourly a ON s.station_id=a.station_id AND h.hour_start=a.hour_start
    LEFT JOIN city_weather_map m ON s.city=m.city
    LEFT JOIN weather w ON m.weather_zip_code=w.weather_zip_code AND h.hour_start::DATE=w.weather_date
    WHERE h.hour_start::DATE>=s.installation_date;
    CREATE OR REPLACE TABLE station_daily AS
    SELECT station_id,city,hour_start::DATE AS date,day_type,
      sum(departures) departures,sum(arrivals) arrivals,
      sum(observed_seconds) observed_seconds,sum(empty_seconds) empty_seconds,sum(full_seconds) full_seconds,
      sum(low_bike_seconds) low_bike_seconds,sum(low_dock_seconds) low_dock_seconds,
      count(*) expected_hours,count(observed_seconds) hours_with_some_status,
      max(precipitation_numeric_inches) precipitation_numeric_inches,
      bool_or(trace_precipitation) trace_precipitation,
      max(temperature_f) temperature_f,max(wind_mph) wind_mph
    FROM station_hour_panel GROUP BY 1,2,3,4;
    """)
    run('8/8 Checking reconciliations and recording source hashes', """
    CREATE OR REPLACE TABLE key_audit AS
    SELECT 'station' table_name,'station_id' key_columns,count(*) AS rows,count(DISTINCT station_id) distinct_keys FROM station
    UNION ALL SELECT 'trip','trip_id',count(*),count(DISTINCT trip_id) FROM trip
    UNION ALL SELECT 'bike','bike_id',count(*),count(DISTINCT bike_id) FROM bike
    UNION ALL SELECT 'weather','weather_zip_code + weather_date',count(*),count(DISTINCT (weather_zip_code,weather_date)) FROM weather
    UNION ALL SELECT 'status','station_id + observed_at',count(*),count(*)-(SELECT coalesce(sum(records-1),0) FROM status_duplicate_keys) FROM status
    UNION ALL SELECT 'status_hourly','station_id + hour_start',count(*),count(DISTINCT (station_id,hour_start)) FROM status_hourly;
    """)
    for label,sql in [
      ('All trip origins refer to stations','SELECT count(*) FROM trip t ANTI JOIN station s ON t.start_station_id=s.station_id'),
      ('All trip destinations refer to stations','SELECT count(*) FROM trip t ANTI JOIN station s ON t.end_station_id=s.station_id'),
      ('No overlapping exposure within an hour','SELECT count(*) FROM status_hourly WHERE observed_seconds>3600.00001'),
      ('Departures reconcile','SELECT abs((SELECT sum(departures) FROM trip_hourly)-(SELECT count(*) FROM valid_trip))'),
      ('Arrivals reconcile','SELECT abs((SELECT sum(arrivals) FROM trip_hourly)-(SELECT count(*) FROM valid_trip))'),
      ('Weather keys are unique',"SELECT rows-distinct_keys FROM key_audit WHERE table_name='weather'"),
    ]:
        assert con.execute(sql).fetchone()[0]==0,label
    con.execute('CHECKPOINT')
    metadata={'build_version':1,'signature':signature,'files':{},'database':'sf_bikeshare.duckdb',
              'duckdb_version':duckdb.__version__,'status_duplicate_key_groups':dup,
              'interval_rule':'Carry previous state only to next observation if gap is positive and <=90 seconds; split at hour boundaries; no long-gap fill.',
              'weather_join':'Explicit analyst city-to-weather-ZIP map; never rider ZIP.',
              'validation':'All database reconciliation assertions passed'}
    for n,p in files.items():
        print(f'Hashing {n}.csv',flush=True)
        with p.open('rb') as stream: digest=hashlib.file_digest(stream,'sha256').hexdigest()
        metadata['files'][n]={'filename':p.name,'bytes':p.stat().st_size,'sha256':digest}
    meta_path.write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    con.close()
    return db

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,default=SOURCE_DEFAULT)
    parser.add_argument('--rebuild',action='store_true')
    parser.add_argument('--resume-from',type=int,choices=range(1,9),default=1,help='Resume a verified partial build; use with --rebuild')
    args=parser.parse_args()
    print(build(args.source,args.rebuild,args.resume_from),flush=True)
