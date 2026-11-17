"""Compare contiguous history windows using cached hourly data, without raw scans.

Run with the project's Python environment: python sf_bikeshare/assess_subset_windows.py
These are exploratory validation results for completed-trip forecasts, not latent
demand estimates or optimization results. No final policy test is performed.
"""
from pathlib import Path
from datetime import datetime, timedelta
import json
import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'sf_bikeshare' / 'subset_assessment'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(OUT.parent / 'sf_bikeshare.duckdb'), read_only=True)
    cohort = con.execute("""
      SELECT * FROM station WHERE city='San Francisco'
      AND installation_date <= DATE '2013-08-29' ORDER BY station_id
    """).df()
    ids = cohort.station_id.tolist()
    con.register('cohort_ids', cohort[['station_id']])
    panel = con.execute("""
      SELECT p.* FROM station_hour_panel p JOIN cohort_ids c USING(station_id)
      WHERE hour_start >= TIMESTAMP '2014-12-08'
      AND hour_start < TIMESTAMP '2015-04-20'
      ORDER BY station_id,hour_start
    """).df()
    assert not panel.duplicated(['station_id', 'hour_start']).any()
    keys = ['station_id', 'day_type', 'hour']
    metrics = []
    for cutoff in ['2015-02-02', '2015-03-02', '2015-04-06']:
        end = datetime.fromisoformat(cutoff)
        valid = panel[(panel.hour_start >= end) &
                      (panel.hour_start < end + timedelta(days=14))]
        assert len(valid) == len(ids) * 24 * 14
        for weeks in [1, 2, 4, 8]:
            start = end - timedelta(weeks=weeks)
            train = panel[(panel.hour_start >= start) & (panel.hour_start < end)]
            assert len(train) == len(ids) * weeks * 7 * 24
            forecast = train.groupby(keys)[['departures', 'arrivals']].mean().add_suffix('_forecast')
            pred = valid.join(forecast, on=keys)
            assert pred.departures_forecast.notna().all()
            daily_weather = train.groupby(train.hour_start.dt.date).precipitation_numeric_inches.first()
            observed = float(train.observed_seconds.fillna(0).sum())
            metrics.append(dict(
                validation_start=cutoff, training_weeks=weeks,
                training_start=start.date().isoformat(), stations=len(ids),
                station_hours=len(train), observed_departures=int(train.departures.sum()),
                status_coverage_pct=100 * observed / (len(train)*3600),
                empty_exposure_pct=100*float(train.empty_seconds.fillna(0).sum())/observed,
                full_exposure_pct=100*float(train.full_seconds.fillna(0).sum())/observed,
                measurable_rain_days=int((daily_weather>0).sum()),
                missing_weather_days=int(daily_weather.isna().sum()),
                departure_mae=float((pred.departures-pred.departures_forecast).abs().mean()),
                arrival_mae=float((pred.arrivals-pred.arrivals_forecast).abs().mean()),
                peak_departure_mae=float((pred.loc[pred.hour.isin([7,8,9,16,17,18]), 'departures']-
                                          pred.loc[pred.hour.isin([7,8,9,16,17,18]), 'departures_forecast']).abs().mean()),
            ))
    result = pd.DataFrame(metrics)
    result.to_csv(OUT/'window_comparison.csv', index=False)
    summary = result.groupby('training_weeks')[['departure_mae','arrival_mae','peak_departure_mae']].mean()
    summary.to_csv(OUT/'mean_validation_metrics.csv')
    # Export an observed-data candidate, not a demand table or final scope decision.
    candidate = panel[(panel.hour_start >= '2015-02-09') & (panel.hour_start < '2015-04-20')].copy()
    candidate['split'] = 'training'
    candidate.loc[candidate.hour_start >= '2015-04-06', 'split'] = 'validation'
    con.register('candidate_export', candidate)
    path = OUT/'candidate_observed_station_hours.parquet'
    con.execute("COPY candidate_export TO ? (FORMAT PARQUET, COMPRESSION ZSTD)", [str(path)])
    cohort.to_csv(OUT/'candidate_stations.csv', index=False)
    metadata = dict(
        source_database='output/sf_bikeshare/sf_bikeshare.duckdb',
        cohort_rule='San Francisco stations installed by 2013-08-29',
        station_ids=ids, station_count=len(ids), candidate_rows=len(candidate),
        candidate_bytes=path.stat().st_size,
        training_interval='[2015-02-09, 2015-04-06)',
        validation_interval='[2015-04-06, 2015-04-20)',
        reserved_policy_test_suggestion='[2015-04-20, 2015-05-04); not read by this script; earlier full EDA may include these dates',
        forecast='Mean completed counts per station, hour and weekday/weekend; no weather fitting',
        limitations=['Exploratory validation, not a locked final test',
                     'Observed trips are censored; no latent demand fitted',
                     'Hourly mean inventory is not opening stock',
                     'No optimizer, policy savings, uncertainty interval or representativeness proof',
                     'All endpoint flows in the panel retained, including cohort boundary flows',
                     'Recorded local clock hours; unresolved DST ambiguity retained from source'],
    )
    (OUT/'assessment_manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(result.round(4).to_string(index=False))
    print('\nMean validation MAE:\n'+summary.round(4).to_string())
    print('\nCandidate:',len(candidate),'rows;',path.stat().st_size,'bytes')


if __name__ == '__main__':
    main()
