-- Open the local database using DuckDB, then run these queries.
SELECT * FROM key_audit;
SELECT * FROM status_quality;
SELECT * FROM status_duplicate_keys ORDER BY records DESC LIMIT 20;

-- Station-level observed availability. This does not count failed customers.
SELECT s.station_id, s.station_name, s.city,
       sum(a.observed_seconds)/3600.0 observed_hours,
       100.0*sum(a.empty_seconds)/sum(a.observed_seconds) empty_pct,
       100.0*sum(a.full_seconds)/sum(a.observed_seconds) full_pct
FROM status_hourly a JOIN station s USING(station_id)
GROUP BY 1,2,3 ORDER BY empty_pct+full_pct DESC;

-- Weather is joined through an explicit location proxy, never rider ZIP.
SELECT t.trip_id,t.started_at,s.city,t.rider_zip_code,
       m.weather_zip_code,w.precipitation_numeric_inches,w.trace_precipitation
FROM valid_trip t
JOIN station s ON t.start_station_id=s.station_id
LEFT JOIN city_weather_map m ON s.city=m.city
LEFT JOIN weather w ON m.weather_zip_code=w.weather_zip_code
                   AND t.started_at::DATE=w.weather_date
LIMIT 20;

-- A common station-hour grain preserves trip counts when facts are joined.
SELECT station_id,hour_start,departures,arrivals,
       observed_seconds/3600.0 coverage,empty_seconds,full_seconds,
       weather_zip_code,precipitation_numeric_inches
FROM station_hour_panel
WHERE city='San Francisco' AND hour BETWEEN 7 AND 9
ORDER BY hour_start,station_id LIMIT 100;

-- Unknown status is not replaced by zero available bicycles.
SELECT city,count(*) reference_station_hours,
       count(observed_seconds) hours_with_some_status,
       sum(observed_seconds)/(3600.0*count(*)) time_coverage
FROM station_hour_panel GROUP BY city;
