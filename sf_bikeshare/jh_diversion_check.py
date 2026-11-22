"""Run from the repository root: python sf_bikeshare/jh_diversion_check.py (Section 7.3)

Do riders who meet a full station return their bike at a nearby station instead?

For each full-dock episode at station i (>= 5 min, inside the study window), count returns at
i's 3 nearest stations during the episode (+5 min). Compare with the same clock window one week
earlier and one week later (placebo), when i was not full in that window. The excess estimates
diverted returns. Compare it with the estimated missed returns at i (historical return rate x
full minutes, training rates).
"""
import numpy as np
import pandas as pd

M = 'output/sf_bikeshare/demand_estimation_inputs_v3/'
V = 'output/sf_bikeshare/model_inputs_v3/'
T0, T1 = pd.Timestamp('2015-02-09'), pd.Timestamp('2015-04-20')

st = pd.read_csv(M + 'status.csv.gz')
st['t'] = pd.to_datetime(st.time, format='%Y/%m/%d %H:%M:%S')
st = st.sort_values(['station_id', 't'])
st['t_next'] = st.groupby('station_id').t.shift(-1)
gap = (st.t_next - st.t).dt.total_seconds()
valid = gap.gt(0) & gap.le(90) & st.bikes_available.ge(0) & st.docks_available.ge(0) & ~(st.bikes_available.eq(0) & st.docks_available.eq(0))
st['full'] = valid & st.docks_available.eq(0)
st = st[st.t_next.notna()]
# full episodes
new = st.full & ~(st.full.shift(fill_value=False) & st.station_id.eq(st.station_id.shift()))
st['ep'] = new.cumsum().where(st.full)
ep = st[st.full].groupby('ep').agg(station_id=('station_id', 'first'), start=('t', 'min'), end=('t_next', 'max')).reset_index(drop=True)
ep = ep[(ep.start >= T0) & (ep.end <= T1)]
ep['minutes'] = (ep.end - ep.start).dt.total_seconds() / 60
ep = ep[ep.minutes >= 5].reset_index(drop=True)

# full-interval lookup to test whether a station was full in a placebo window
full_iv = st[st.full][['station_id', 't', 't_next']]

def was_full(sid, a, b):
    f = full_iv[(full_iv.station_id == sid)]
    return bool(((f.t < b) & (f.t_next > a)).any())

ev = pd.read_csv(M + 'trip_events.csv.gz', parse_dates=['event_at'])
ret = ev[ev.event_type.eq('return')][['station_id', 'event_at']]
ret_by = {s: np.sort(g.event_at.values) for s, g in ret.groupby('station_id')}

def count(sid, a, b):
    arr = ret_by.get(sid)
    if arr is None:
        return 0
    return int(np.searchsorted(arr, np.datetime64(b), 'left') - np.searchsorted(arr, np.datetime64(a), 'left'))

dist = pd.read_csv(V + 'station_distances.csv')
dist = dist[dist.from_station_id != dist.to_station_id]
near = dist.sort_values('road_distance_km').groupby('from_station_id').head(3)
nbrs = near.groupby('from_station_id').to_station_id.apply(list).to_dict()
ndist = near.groupby('from_station_id').road_distance_km.mean().to_dict()

# training return rate at i while docks available (per second), by station x hour x day type
h = pd.read_csv(V + 'station_hour_observed.csv.gz')
tr = h[h.split == 'training']
g = tr.groupby(['station_id', 'hour', 'day_type'])[['subscriber_returns_available_exposure', 'customer_returns_available_exposure', 'dock_available_seconds']].sum()
rate = ((g.subscriber_returns_available_exposure + g.customer_returns_available_exposure) / g.dock_available_seconds.replace(0, np.nan)).to_dict()

rec = []
for e in ep.itertuples(index=False):
    a, b = e.start, e.end + pd.Timedelta(minutes=5)
    obs = sum(count(n, a, b) for n in nbrs[e.station_id])
    plac = []
    for wk in (-7, 7):
        pa, pb = a + pd.Timedelta(days=wk), b + pd.Timedelta(days=wk)
        if pa < T0 or pb > T1 or was_full(e.station_id, pa, pb):
            continue
        plac.append(sum(count(n, pa, pb) for n in nbrs[e.station_id]))
    # expected missed returns at i during the episode (split by clock hour)
    miss, t = 0.0, e.start
    while t < e.end:
        nxt = min(e.end, t.floor('h') + pd.Timedelta(hours=1))
        dt = 'Weekend' if t.dayofweek >= 5 else 'Weekday'
        miss += rate.get((e.station_id, t.hour, dt), 0.0) * (nxt - t).total_seconds()
        t = nxt
    served_at_i = count(e.station_id, e.start, e.end)
    rec.append(dict(station_id=e.station_id, start=e.start, minutes=e.minutes, nbr_returns=obs,
                    placebo=np.mean(plac) if plac else np.nan, est_missed_at_i=max(0.0, miss - served_at_i)))
r = pd.DataFrame(rec)
ok = r.dropna(subset=['placebo'])
excess = ok.nbr_returns.sum() - ok.placebo.sum()
print(f'full episodes >=5 min: {len(r)}, with placebo: {len(ok)}, total full hours: {r.minutes.sum()/60:.1f}')
print(f'neighbour returns during episodes: {ok.nbr_returns.sum():.0f}; placebo (same window, other week): {ok.placebo.sum():.1f}; excess: {excess:.1f}')
print(f'estimated missed returns at full station in same episodes: {ok.est_missed_at_i.sum():.1f}')
print(f'share of missed returns seen as extra returns at 3 nearest stations: {excess/ok.est_missed_at_i.sum():.0%}')
print(f'mean distance to the 3 nearest stations: {np.mean([ndist[s] for s in ok.station_id]):.2f} km')
# bootstrap CI over episodes
rng = np.random.default_rng(0)
vals = []
for _ in range(2000):
    s = ok.sample(len(ok), replace=True, random_state=rng.integers(1e9))
    vals.append((s.nbr_returns.sum() - s.placebo.sum()) / s.est_missed_at_i.sum())
print('95% interval of share:', np.percentile(vals, [2.5, 97.5]).round(2))
r.to_csv('output/sf_bikeshare/extra_experiments_2026-11-22/diversion_episodes.csv', index=False)
