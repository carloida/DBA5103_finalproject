-- Actual materialized-table DDL and indexes. Views and audited logical FKs are documented in the source builder.

CREATE TABLE bike(bike_id INTEGER);

CREATE TABLE city_weather_map(city VARCHAR PRIMARY KEY, weather_zip_code VARCHAR UNIQUE, mapping_basis VARCHAR);

CREATE TABLE interval_gap_audit(gap_group VARCHAR, intervals BIGINT, elapsed_seconds HUGEINT);

CREATE TABLE key_audit(table_name VARCHAR, key_columns VARCHAR, "rows" BIGINT, distinct_keys HUGEINT);

CREATE TABLE station(station_id INTEGER, station_name VARCHAR, latitude DOUBLE, longitude DOUBLE, dock_count INTEGER, city VARCHAR, installation_date DATE);

CREATE TABLE station_daily(station_id INTEGER, city VARCHAR, date DATE, day_type VARCHAR, departures HUGEINT, arrivals HUGEINT, observed_seconds HUGEINT, empty_seconds HUGEINT, full_seconds HUGEINT, low_bike_seconds HUGEINT, low_dock_seconds HUGEINT, expected_hours BIGINT, hours_with_some_status BIGINT, precipitation_numeric_inches DOUBLE, trace_precipitation BOOLEAN, temperature_f DOUBLE, wind_mph DOUBLE);

CREATE TABLE station_hour_panel(station_id INTEGER, city VARCHAR, hour_start TIMESTAMP, day_type VARCHAR, "hour" INTEGER, departures INTEGER, arrivals INTEGER, observed_seconds HUGEINT, empty_seconds HUGEINT, full_seconds HUGEINT, low_bike_seconds HUGEINT, low_dock_seconds HUGEINT, mean_bikes_available DOUBLE, mean_effective_capacity DOUBLE, static_capacity_mismatch_seconds HUGEINT, weather_zip_code VARCHAR, precipitation_numeric_inches DOUBLE, trace_precipitation BOOLEAN, temperature_f DOUBLE, wind_mph DOUBLE);

CREATE TABLE status(station_id INTEGER, bikes_available INTEGER, docks_available INTEGER, observed_at TIMESTAMP);

CREATE TABLE status_duplicate_keys(station_id INTEGER, observed_at TIMESTAMP, records BIGINT, distinct_states BIGINT);

CREATE TABLE status_hourly(station_id INTEGER, hour_start TIMESTAMP, observed_seconds HUGEINT, empty_seconds HUGEINT, full_seconds HUGEINT, low_bike_seconds HUGEINT, low_dock_seconds HUGEINT, mean_bikes_available DOUBLE, mean_effective_capacity DOUBLE, static_capacity_mismatch_seconds HUGEINT);

CREATE TABLE status_intervals(station_id INTEGER, bikes_available INTEGER, docks_available INTEGER, observed_at TIMESTAMP, next_observed_at TIMESTAMP, static_dock_count INTEGER, valid_state BOOLEAN);

CREATE TABLE status_month_coverage(station_id INTEGER, "month" DATE, observations BIGINT, observed_days BIGINT, invalid_or_zero_capacity_states BIGINT);

CREATE TABLE status_quality(source_rows BIGINT, parse_or_missing BIGINT, unknown_stations BIGINT, negative_counts BIGINT, both_zero BIGINT, static_capacity_mismatches BIGINT, first_observation TIMESTAMP, last_observation TIMESTAMP, stations BIGINT);

CREATE TABLE trip(trip_id BIGINT, duration_seconds BIGINT, started_at TIMESTAMP, start_station_name VARCHAR, start_station_id INTEGER, ended_at TIMESTAMP, end_station_name VARCHAR, end_station_id INTEGER, bike_id INTEGER, subscription_type VARCHAR, rider_zip_code VARCHAR);

CREATE TABLE trip_hourly(station_id INTEGER, hour_start TIMESTAMP, departures INTEGER, arrivals INTEGER);

CREATE TABLE weather(max_temperature_f VARCHAR, mean_temperature_f VARCHAR, min_temperature_f VARCHAR, max_dew_point_f VARCHAR, mean_dew_point_f VARCHAR, min_dew_point_f VARCHAR, max_humidity VARCHAR, mean_humidity VARCHAR, min_humidity VARCHAR, max_sea_level_pressure_inches VARCHAR, mean_sea_level_pressure_inches VARCHAR, min_sea_level_pressure_inches VARCHAR, max_visibility_miles VARCHAR, mean_visibility_miles VARCHAR, min_visibility_miles VARCHAR, max_wind_Speed_mph VARCHAR, mean_wind_speed_mph VARCHAR, max_gust_speed_mph VARCHAR, precipitation_inches VARCHAR, cloud_cover VARCHAR, events VARCHAR, wind_dir_degrees VARCHAR, weather_date DATE, weather_zip_code VARCHAR, precipitation_numeric_inches DOUBLE, trace_precipitation BOOLEAN, temperature_f DOUBLE, wind_mph DOUBLE);

CREATE UNIQUE INDEX bike_pk ON bike(bike_id);

CREATE UNIQUE INDEX station_pk ON station(station_id);

CREATE UNIQUE INDEX status_hourly_pk ON status_hourly(station_id, hour_start);

CREATE UNIQUE INDEX trip_pk ON trip(trip_id);

CREATE UNIQUE INDEX weather_pk ON weather(weather_zip_code, weather_date);