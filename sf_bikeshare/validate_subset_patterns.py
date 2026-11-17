"""Audit candidate pattern stability and extremes; preserve all source records."""
from pathlib import Path
import json
import duckdb
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'output/sf_bikeshare/subset_assessment'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(OUT.parent/'sf_bikeshare.duckdb'), read_only=True)
    panel = con.execute("""
      SELECT p.* FROM station_hour_panel p JOIN station s USING(station_id)
      WHERE s.city='San Francisco' AND s.installation_date<=DATE '2013-08-29'
      AND hour_start>=TIMESTAMP '2013-09-02' AND hour_start<TIMESTAMP '2015-08-31'
      ORDER BY p.station_id,hour_start
    """).df()
    panel['date'] = panel.hour_start.dt.normalize()
    candidate_mask = (panel.hour_start >= '2015-02-09') & (panel.hour_start < '2015-04-20')
    candidate = panel[candidate_mask].copy()
    reference = panel[~candidate_mask].copy()
    train8 = candidate[candidate.hour_start < '2015-04-06'].copy()
    train4 = train8[train8.hour_start >= '2015-03-09'].copy()
    assert not panel.duplicated(['station_id','hour_start']).any()
    assert len(panel) == 34*728*24
    assert len(candidate) == 57120

    def daily(df):
        return df.groupby(['date','day_type'],as_index=False).agg(
            departures=('departures','sum'),arrivals=('arrivals','sum'),
            observed_seconds=('observed_seconds','sum'),empty_seconds=('empty_seconds','sum'),
            full_seconds=('full_seconds','sum'),rain=('precipitation_numeric_inches','first'))

    refday = daily(reference)
    thresholds = refday.groupby('day_type').departures.quantile([.25,.5,.75]).unstack()
    thresholds.columns = ['q1','median','q3']
    thresholds['lower'] = (thresholds.q1-1.5*(thresholds.q3-thresholds.q1)).clip(lower=0)
    thresholds['upper'] = thresholds.q3+1.5*(thresholds.q3-thresholds.q1)
    thresholds.to_csv(OUT/'daily_outlier_thresholds.csv')
    all_daily = daily(panel).merge(thresholds[['lower','upper']],left_on='day_type',right_index=True)
    all_daily['iqr_flag'] = (all_daily.departures<all_daily.lower)|(all_daily.departures>all_daily.upper)
    all_daily['candidate'] = (all_daily.date >= '2015-02-09') & (all_daily.date < '2015-04-20')
    all_daily.to_csv(OUT/'daily_pattern_and_outlier_audit.csv',index=False)
    all_daily[all_daily.iqr_flag].to_csv(OUT/'flagged_daily_extremes.csv',index=False)

    def stats(df,label):
        d=daily(df)
        observed=float(df.observed_seconds.fillna(0).sum())
        flags=d.merge(thresholds[['lower','upper']],left_on='day_type',right_index=True)
        return dict(period=label,days=len(d),station_hours=len(df),
                    weekday_departures_per_day=float(d.loc[d.day_type.eq('Weekday'),'departures'].mean()),
                    weekend_departures_per_day=float(d.loc[d.day_type.eq('Weekend'),'departures'].mean()),
                    daily_min=int(d.departures.min()),daily_max=int(d.departures.max()),
                    station_hour_p95=float(df.departures.quantile(.95)),
                    station_hour_p99=float(df.departures.quantile(.99)),station_hour_max=int(df.departures.max()),
                    coverage_pct=100*observed/(len(df)*3600),
                    empty_pct=100*float(df.empty_seconds.fillna(0).sum())/observed,
                    full_pct=100*float(df.full_seconds.fillna(0).sum())/observed,
                    rain_days=int((d.rain>0).sum()),missing_weather_days=int(d.rain.isna().sum()),
                    iqr_flagged_days=int(((flags.departures<flags.lower)|(flags.departures>flags.upper)).sum()))

    summaries=pd.DataFrame([stats(panel,'Full 104 complete weeks'),
                            stats(reference,'Other 94 weeks (reference)'),
                            stats(candidate,'Candidate 10 weeks'),stats(train8,'Training 8 weeks'),stats(train4,'Training 4 weeks')])
    summaries.to_csv(OUT/'pattern_period_summary.csv',index=False)

    profiles=[]
    station_stats={}
    for label,df in [('Reference',reference),('Candidate',candidate),('Training 8w',train8),('Training 4w',train4)]:
        p=df.groupby(['day_type','hour']).departures.mean().reset_index()
        p['share_pct']=100*p.departures/p.groupby('day_type').departures.transform('sum')
        p['period']=label;profiles.append(p)
        s=df.groupby('station_id').agg(departures=('departures','sum'),observed=('observed_seconds','sum'),
                                       empty=('empty_seconds','sum'),full=('full_seconds','sum'))
        s['pressure_pct']=100*(s['empty']+s['full'])/s.observed
        # Signed mean customer outflow; positive means bikes leave faster than return.
        for name,hours in [('am',[7,8,9]),('pm',[16,17,18])]:
            f=df[df.hour.isin(hours)].groupby('station_id')[['departures','arrivals']].mean()
            s[name+'_net']=f.departures-f.arrivals
        station_stats[label]=s
    profiles=pd.concat(profiles,ignore_index=True)
    profiles.to_csv(OUT/'hourly_pattern_comparison.csv',index=False)
    comparisons=[]
    ref=station_stats['Reference']
    for label in ['Candidate','Training 8w','Training 4w']:
        s=station_stats[label]
        for day in ['Weekday','Weekend']:
            a=profiles[(profiles.period=='Reference')&(profiles.day_type==day)].set_index('hour')
            b=profiles[(profiles.period==label)&(profiles.day_type==day)].set_index('hour')
            comparisons.append(dict(period=label,day_type=day,
                hourly_shape_pearson=float(a.share_pct.corr(b.share_pct)),
                shape_l1_pp=float((a.share_pct-b.share_pct).abs().sum()),
                reference_am_peak=int(a.loc[[6,7,8,9,10],'departures'].idxmax()),
                candidate_am_peak=int(b.loc[[6,7,8,9,10],'departures'].idxmax()),
                reference_pm_peak=int(a.loc[[15,16,17,18,19],'departures'].idxmax()),
                candidate_pm_peak=int(b.loc[[15,16,17,18,19],'departures'].idxmax())))
    comp=pd.DataFrame(comparisons);comp.to_csv(OUT/'profile_similarity.csv',index=False)
    station_comparisons=[]
    for label in ['Candidate','Training 8w','Training 4w']:
        s=station_stats[label]
        station_comparisons.append(dict(period=label,
            activity_rank_spearman=float(ref.departures.rank().corr(s.departures.rank())),
            pressure_rank_spearman=float(ref.pressure_pct.rank().corr(s.pressure_pct.rank())),
            top10_pressure_overlap=len(set(ref.nlargest(10,'pressure_pct').index)&set(s.nlargest(10,'pressure_pct').index)),
            am_net_sign_matches=int((np.sign(ref.am_net)==np.sign(s.am_net)).sum()),
            pm_net_sign_matches=int((np.sign(ref.pm_net)==np.sign(s.pm_net)).sum()),
            station_count=len(s)))
        s.to_csv(OUT/('station_pattern_'+label.lower().replace(' ','_')+'.csv'))
    pd.DataFrame(station_comparisons).to_csv(OUT/'station_pattern_stability.csv',index=False)
    duration=con.execute("""
      SELECT count(*) relevant_trips,
       count(*) FILTER(WHERE long_trip) duration_over_24h,
       count(*) FILTER(WHERE duration_clock_mismatch) duration_clock_mismatch,
       max(duration_seconds) max_duration_seconds
      FROM valid_trip WHERE
      (start_station_id IN(SELECT station_id FROM station WHERE city='San Francisco' AND installation_date<=DATE '2013-08-29')
       AND started_at>=TIMESTAMP '2015-02-09' AND started_at<TIMESTAMP '2015-04-20') OR
      (end_station_id IN(SELECT station_id FROM station WHERE city='San Francisco' AND installation_date<=DATE '2013-08-29')
       AND ended_at>=TIMESTAMP '2015-02-09' AND ended_at<TIMESTAMP '2015-04-20')
    """).df().iloc[0].to_dict()
    manifest=dict(reference='Same 34 SF stations; complete weeks [2013-09-02,2015-08-31), excluding candidate dates',
                  candidate='[2015-02-09,2015-04-20)',
                  method='Descriptive comparisons, not an equivalence test or final policy validation',
                  outlier_method='Daily completed departures flagged outside weekday/weekend-specific reference Q1-1.5*IQR and Q3+1.5*IQR; retained, not removed',
                  date_caveat='Recorded local clock; source DST ambiguity unresolved',
                  duration_audit={k:int(v) for k,v in duration.items()},
                  no_rows_removed_for_extreme_usage=True,
                  limitations=['Reference covers changing seasons and operations',
                               'Candidate was not selected by an optimization of representativeness',
                               'This descriptive audit uses validation dates; it is not a sealed test',
                               'No equivalence of profit or latent demand established'])
    (OUT/'pattern_audit_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(summaries.round(4).to_string(index=False))
    print('\nProfile similarity:\n'+comp.round(4).to_string(index=False))
    print('\nStation stability:\n'+pd.DataFrame(station_comparisons).round(4).to_string(index=False))
    print('\nDuration:',manifest['duration_audit'])
    print('\nExtreme dates:\n'+all_daily[all_daily.iqr_flag][['date','day_type','departures','candidate']].to_string(index=False))


if __name__=='__main__':main()
