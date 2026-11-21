"""Export scoped minute observations for V3 demand estimation; never fit demand.

Run from the repository root with duckdb installed:
    python sf_bikeshare/export_minute_demand_inputs.py
Source databases are attached read-only. Frozen V3 exports are never rewritten.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'output/sf_bikeshare'
OUT = BASE / 'demand_estimation_inputs_v3'
START = '2015-02-09 00:00:00'
END = '2015-04-20 00:00:00'
CONTEXT = '2015-02-08 23:30:00'


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frozen = BASE / 'model_inputs_v3'
    before = {p.name: sha256(p) for p in frozen.iterdir() if p.is_file()
              and p.suffix != '.duckdb'}
    c = duckdb.connect()
    c.execute(f"ATTACH {quote(BASE / 'sf_bikeshare.duckdb')} AS source (READ_ONLY)")
    c.execute(f"ATTACH {quote(frozen / 'sf_model_inputs_v3.duckdb')} AS v3 (READ_ONLY)")
    c.execute('CREATE TEMP VIEW cohort AS SELECT station_id FROM v3.station')
    c.execute(f"""CREATE TEMP TABLE snapshots AS
        SELECT s.* FROM source.status s JOIN cohort USING(station_id)
        WHERE observed_at >= TIMESTAMP '{CONTEXT}' - INTERVAL 90 SECOND
          AND observed_at <= TIMESTAMP '{END}' + INTERVAL 90 SECOND""")
    c.execute(f"""CREATE TEMP TABLE journeys AS
        SELECT * FROM source.valid_trip
        WHERE (start_station_id IN (SELECT * FROM cohort)
               AND started_at >= TIMESTAMP '{CONTEXT}' AND started_at < TIMESTAMP '{END}')
           OR (end_station_id IN (SELECT * FROM cohort)
               AND ended_at >= TIMESTAMP '{CONTEXT}' AND ended_at < TIMESTAMP '{END}')""")
    # Native column names and date formats accepted by Fu Yan's existing reader.
    c.execute("""CREATE TEMP VIEW status_export AS SELECT station_id,
        bikes_available, docks_available,
        strftime(observed_at, '%Y/%m/%d %H:%M:%S') AS time
        FROM snapshots""")
    c.execute("""CREATE TEMP VIEW trip_export AS SELECT trip_id AS id,
        duration_seconds AS duration,
        strftime(started_at, '%m/%d/%Y %H:%M') AS start_date,
        start_station_name, start_station_id,
        strftime(ended_at, '%m/%d/%Y %H:%M') AS end_date,
        end_station_name, end_station_id, bike_id, subscription_type
        FROM journeys""")
    c.execute(f"""CREATE TEMP VIEW events AS
        SELECT trip_id, start_station_id AS station_id, end_station_id AS other_station_id,
               started_at AS event_at, 'pickup' AS event_type, subscription_type
        FROM journeys WHERE start_station_id IN (SELECT * FROM cohort)
            AND started_at >= TIMESTAMP '{CONTEXT}' AND started_at < TIMESTAMP '{END}'
        UNION ALL
        SELECT trip_id, end_station_id, start_station_id, ended_at, 'return', subscription_type
        FROM journeys WHERE end_station_id IN (SELECT * FROM cohort)
            AND ended_at >= TIMESTAMP '{CONTEXT}' AND ended_at < TIMESTAMP '{END}'""")
    c.execute(f"""CREATE TEMP VIEW events_export AS SELECT *,
        event_at >= TIMESTAMP '{START}' AS in_study_window,
        CASE WHEN event_at < TIMESTAMP '{START}' THEN 'context'
             WHEN event_at < TIMESTAMP '2015-04-06' THEN 'training'
             ELSE 'validation' END AS split,
        CASE WHEN other_station_id IN (SELECT * FROM cohort) THEN 'internal'
             ELSE 'external' END AS boundary_type FROM events""")

    checks = []

    def check(name, actual, expected):
        ok = actual == expected
        checks.append(dict(check=name, actual=actual, expected=expected, passed=ok))
        if not ok:
            raise AssertionError(checks[-1])

    check('cohort_station_count', c.execute('SELECT count(*) FROM cohort').fetchone()[0], 34)
    check('snapshot_duplicate_keys', c.execute('''SELECT count(*) FROM
        (SELECT station_id, observed_at FROM snapshots GROUP BY ALL HAVING count(*)>1)''').fetchone()[0], 0)
    check('trip_timestamp_minute_precision', c.execute('''SELECT count(*) FROM journeys
        WHERE started_at != date_trunc('minute',started_at)
           OR ended_at != date_trunc('minute',ended_at)''').fetchone()[0], 0)
    exports = [
        ('status.csv.gz', 'status_export', 'station_id, time'),
        ('trip.csv.gz', 'trip_export', 'id'),
        ('trip_events.csv.gz', 'events_export', 'station_id, event_at, event_type, trip_id'),
    ]
    files = {}
    for name, view, order in exports:
        path = OUT / name
        c.execute(f"COPY (SELECT * FROM {view} ORDER BY {order}) TO {quote(path)} "
                  "(FORMAT CSV, HEADER, COMPRESSION GZIP)")
        # Read back as text to avoid parser-dependent date inference in native formats.
        c.execute(f"CREATE TEMP VIEW readback AS SELECT * FROM read_csv({quote(path)}, all_varchar=true)")
        n = c.execute(f'SELECT count(*) FROM {view}').fetchone()[0]
        check(name + '_row_count', c.execute('SELECT count(*) FROM readback').fetchone()[0], n)
        cols = [r[0] for r in c.execute(f'DESCRIBE {view}').fetchall()]
        strings = ', '.join('CAST(' + col + ' AS VARCHAR) AS ' + col for col in cols)
        check(name + '_exact_readback', c.execute(f'''SELECT count(*) FROM (
            (SELECT {strings} FROM {view} EXCEPT ALL SELECT * FROM readback)
            UNION ALL (SELECT * FROM readback EXCEPT ALL SELECT {strings} FROM {view}))''').fetchone()[0], 0)
        files[name] = dict(rows=n, bytes=path.stat().st_size, sha256=sha256(path), columns=cols)
        c.execute('DROP VIEW readback')

    # Compare every endpoint event with the already-published V3 event table.
    event_cols = 'trip_id, station_id, other_station_id, event_at, event_type, subscription_type'
    check('core_events_exactly_match_v3', c.execute(f'''SELECT count(*) FROM (
        (SELECT {event_cols} FROM events WHERE event_at >= TIMESTAMP '{START}'
         EXCEPT ALL SELECT {event_cols} FROM v3.observed_trip_events)
        UNION ALL
        (SELECT {event_cols} FROM v3.observed_trip_events EXCEPT ALL
         SELECT {event_cols} FROM events WHERE event_at >= TIMESTAMP '{START}'))''').fetchone()[0], 0)
    for kind, rider, column in [('pickup','Subscriber','subscriber_pickups'),
                                ('pickup','Customer','customer_pickups'),
                                ('return','Subscriber','subscriber_returns'),
                                ('return','Customer','customer_returns')]:
        check(column + '_all_station_hours', c.execute(f'''SELECT count(*) FROM
            v3.station_hour_observed h LEFT JOIN (
                SELECT station_id,date_trunc('hour',event_at) AS hour_start,count(*) AS n
                FROM events WHERE event_at >= TIMESTAMP '{START}'
                    AND event_type='{kind}' AND subscription_type='{rider}' GROUP BY ALL
            ) e USING(station_id,hour_start) WHERE h.{column} != coalesce(e.n,0)''').fetchone()[0], 0)

    # Reconstruct exposure from the exported snapshot range, including edge anchors.
    c.execute(f"""CREATE TEMP TABLE exposures AS
        WITH next AS (SELECT *,lead(observed_at) OVER
            (PARTITION BY station_id ORDER BY observed_at) AS next_at FROM snapshots),
        valid AS (SELECT * FROM next WHERE bikes_available >= 0 AND docks_available >= 0
            AND bikes_available+docks_available>0 AND next_at>observed_at
            AND next_at<=observed_at+INTERVAL 90 SECOND
            AND next_at>TIMESTAMP '{START}' AND observed_at<TIMESTAMP '{END}')
        SELECT station_id,hour_start,
            sum(date_diff('second',greatest(observed_at,hour_start,TIMESTAMP '{START}'),
                least(next_at,hour_start+INTERVAL 1 HOUR,TIMESTAMP '{END}'))) AS observed_seconds,
            sum(CASE WHEN bikes_available=0 THEN date_diff('second',
                greatest(observed_at,hour_start,TIMESTAMP '{START}'),
                least(next_at,hour_start+INTERVAL 1 HOUR,TIMESTAMP '{END}')) ELSE 0 END) AS empty_seconds,
            sum(CASE WHEN docks_available=0 THEN date_diff('second',
                greatest(observed_at,hour_start,TIMESTAMP '{START}'),
                least(next_at,hour_start+INTERVAL 1 HOUR,TIMESTAMP '{END}')) ELSE 0 END) AS full_seconds
        FROM valid, LATERAL generate_series(date_trunc('hour',greatest(observed_at,TIMESTAMP '{START}')),
            date_trunc('hour',least(next_at,TIMESTAMP '{END}')-INTERVAL 1 MICROSECOND),
            INTERVAL 1 HOUR) AS t(hour_start) GROUP BY ALL""")
    for column in ['observed_seconds','empty_seconds','full_seconds']:
        check(column + '_all_station_hours', c.execute(f'''SELECT count(*) FROM
            v3.station_hour_observed h LEFT JOIN exposures e USING(station_id,hour_start)
            WHERE h.{column} != coalesce(e.{column},0)''').fetchone()[0], 0)
    check('frozen_v3_files_unchanged',
          all(sha256(frozen / name) == value for name, value in before.items()), True)
    totals = c.execute(f"""SELECT event_type,subscription_type,count(*) AS events FROM events
        WHERE event_at>=TIMESTAMP '{START}' GROUP BY ALL ORDER BY ALL""").fetchall()
    manifest = dict(
        purpose='Observed minute supplement for demand estimation; no demand estimates or model code',
        created_at_utc=datetime.now(timezone.utc).isoformat(),
        script_sha256=sha256(__file__), duckdb_version=duckdb.__version__,
        source_database='output/sf_bikeshare/sf_bikeshare.duckdb',
        source_database_opened_read_only=True,
        source_manifest_sha256=sha256(BASE / 'source_manifest.json'),
        frozen_v3_manifest_sha256=sha256(frozen / 'manifest.json'),
        study_start_inclusive=START, study_end_exclusive=END,
        trip_event_context_start_inclusive=CONTEXT,
        status_lower_inclusive='2015-02-08 23:28:30',
        status_upper_inclusive='2015-04-20 00:01:30',
        status_anchor_padding_seconds=90,
        timestamp_basis='Recorded naive local times; DST ambiguity retained; not repaired',
        units=dict(duration='seconds',inventory='bikes/docks',time='recorded local time'),
        station_ids=[r[0] for r in c.execute('SELECT * FROM cohort ORDER BY station_id').fetchall()],
        status_invalid_rows_retained=c.execute('''SELECT count(*) FROM snapshots WHERE
            bikes_available IS NULL OR docks_available IS NULL OR bikes_available<0
            OR docks_available<0 OR bikes_available+docks_available<=0''').fetchone()[0],
        core_event_counts=[dict(event_type=k,subscription_type=r,events=n) for k,r,n in totals],
        files=files, validation_checks=checks,
    )
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(files=files, checks_passed=len(checks),core_event_counts=totals),indent=2))


if __name__ == '__main__':
    main()
