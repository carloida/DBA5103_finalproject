#!/usr/bin/env python3
"""Core demand-estimation module for the DBA5103 SF bike redistribution project (report section 3.4).

One producer for both demand cases, built from the minute status snapshots and timestamped trip
events in output/sf_bikeshare/demand_estimation_inputs_v3 plus the frozen V3 hourly table:

  Case A  historical : historical availability-adjusted rate for every stockout minute.
  Case B  hybrid     : rate from the 30 minutes before the episode (>= 20 valid available minutes)
                       for the first 60 elapsed minutes, historical rate afterwards.
  (predecessor       : earlier unlimited pre-stockout rate, kept only for sensitivity checks.)

Historical rate (training weeks 9 Feb - 5 Apr 2015 only), by station x clock hour x day type x rider:
    rate = events recorded while service was available / valid available seconds
(bike-available time for pickups, dock-available time for returns). A group with fewer than
MIN_GROUP_EXPOSURE_SECONDS of available time is pooled across day types (same station/hour); if
that is also unsupported the rate is NaN and the affected hours are flagged 'unresolved'. Unknown
demand is never set to zero.

Episodes: a pickup episode is a continuous run of valid status intervals with 0 bikes; a return
episode is a run with 0 free docks. For each episode, side and rider:
    expected = pre_rate x (minutes in the first pre_horizon of the episode)
               + sum over affected clock hours of historical_rate x remaining minutes in that hour
    missed   = max(0, expected - events recorded during the episode)      (once per episode)
missed is allocated to clock hours in proportion to their expected arrivals and added to the
observed hourly count. Status intervals follow the V3 rule: an interval [t_k, t_k+1) takes the
state of snapshot k and is valid only if 0 < gap <= 90 s and the state is valid. Long gaps are
unknown exposure. An event belongs to the interval containing its timestamp.

Validation (identical for both cases, so the cases are compared on the same windows):
  Targets must be fully valid and available and lie entirely within 6-19 April 2015.
  - near_stockout_10min : the 10 minutes just before each episode longer than 15 minutes;
  - available_1hour     : fully available hours starting at clock-hour origins;
  - available_3hour     : fully available 3-hour windows starting at clock-hour origins.
  Each case predicts every target exactly as it would treat an episode starting at the target
  start: the hybrid uses its pre-window rate for the first hour and historical rates after it; the
  historical benchmark integrates each affected hour's rate. Reported for all eligible origins,
  weekday peak origins and the origins common to the 1- and 3-hour tests.
  The censoring diagnostic (prediction vs. trips recorded in the last 10 minutes INSIDE stockouts)
  is descriptive only: customers who find no bike leave no record, so it is not an accuracy test.

Usage (from the repository root):
  python sf_bikeshare/build_demand_minute.py --case historical \
      --hourly output/sf_bikeshare/model_inputs_v3/station_hour_observed.csv.gz \
      --minute-dir output/sf_bikeshare/demand_estimation_inputs_v3 \
      --output-dir output/sf_bikeshare/demand_estimation_build
  (or the thin wrappers build_demand_historical.py / build_demand_hybrid.py with the same arguments)

Outputs in --output-dir (never inside the frozen model_inputs_v3 folder):
  estimated_demand_station_hour_<case>.csv  31-column model input (same contract as before)
  stockout_episodes_<case>.csv              one row per episode: pre-window, served, expected, missed
  historical_rates.csv                      training rate table with support level per group
  matched_validation.csv                    case A vs case B, all eligible targets (wide)
  validation_by_origin_group.csv            every method x origin group x test (long)
  validation_targets.csv                    every scored target with actuals and predictions
  censoring_diagnostic_<case>.csv           descriptive stockout-interior comparison
  run_manifest_<case>.json                  parameters, checks, totals, input/output SHA-256
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- parameters
MAX_GAP_SECONDS = 90                       # V3 snapshot-gap rule
MIN_GROUP_EXPOSURE_SECONDS = 60 * 60       # historical group needs >= 60 valid available training minutes
STUDY_START = pd.Timestamp("2015-02-09 00:00:00")
VALIDATION_START = pd.Timestamp("2015-04-06 00:00:00")
STUDY_END = pd.Timestamp("2015-04-20 00:00:00")   # exclusive
INF = float("inf")

CASES = {
    # pre_window / min_pre: look-back window and its minimum valid available time (seconds)
    # pre_horizon: elapsed episode time covered by the pre-window rate (0 = never, inf = whole episode)
    "historical": dict(pre_window=30 * 60, min_pre=20 * 60, pre_horizon=0,
                       usual_label="historical_station_hour_daytype", pooled_label="historical_station_hour_pooled"),
    "hybrid": dict(pre_window=30 * 60, min_pre=20 * 60, pre_horizon=60 * 60,
                   usual_label="historical", pooled_label="historical_pooled_day_types"),
    "predecessor": dict(pre_window=15 * 60, min_pre=10 * 60, pre_horizon=INF,
                        usual_label="fallback_usual", pooled_label="fallback_usual_pooled_day_types"),
}
VALIDATION_METHODS = {"case_a_historical": "historical", "case_b_hybrid": "hybrid"}
NEAR_STOCKOUT_MIN_EPISODE_SECONDS = 15 * 60
NEAR_STOCKOUT_TARGET_SECONDS = 10 * 60
LONG_HORIZONS = {"available_1hour": 60 * 60, "available_3hour": 3 * 60 * 60}
PEAK_HOURS = (7, 8, 9, 16, 17, 18)         # weekday peak origin hours for the origin-group table

KEYS = ["station_id", "hour", "day_type"]
FALLBACK_KEYS = ["station_id", "hour"]
RIDERS = {"subscriber": "Subscriber", "customer": "Customer"}
SIDES = {
    # side: (event_type, status column that hits zero, V3 available-seconds column, V3 unavailable-seconds column)
    "pickups": ("pickup", "bikes_available", "bike_available_seconds", "empty_seconds"),
    "returns": ("return", "docks_available", "dock_available_seconds", "full_seconds"),
}
OUTPUT_COLUMNS = [
    "station_id", "service_date", "hour", "hour_start", "day_type", "split", "status_exposure_missing",
    "empty_seconds", "full_seconds", "bike_available_seconds", "dock_available_seconds",
] + [f"{kind}_{rider}_{side}" if kind != "method" else f"method_{rider}_{side}"
     for side in SIDES for rider in RIDERS
     for kind in ("observed", "estimated", "missed", "method")] + [
    "estimated_total_pickups", "observed_total_pickups", "estimated_total_returns", "observed_total_returns",
]
EPOCH = pd.Timestamp("1970-01-01")


def to_seconds(ts) -> np.ndarray:
    """Naive local timestamps -> integer seconds (no timezone shifting)."""
    return np.asarray((pd.to_datetime(pd.Series(ts)) - EPOCH) // pd.Timedelta(seconds=1), dtype="int64")


def to_timestamp(sec) -> pd.Series:
    return EPOCH + pd.to_timedelta(np.asarray(sec), unit="s")


T0, V0, T1 = (int(to_seconds([t])[0]) for t in (STUDY_START, VALIDATION_START, STUDY_END))


def case_config(case, **overrides):
    cfg = dict(CASES[case])
    cfg.update({k: v for k, v in overrides.items() if v is not None})
    return cfg


# --------------------------------------------------------------------------- status intervals and events
def build_intervals(status: pd.DataFrame) -> pd.DataFrame:
    s = status.sort_values(["station_id", "time"]).reset_index(drop=True)
    s["start"] = to_seconds(s["time"])
    s["end"] = s.groupby("station_id")["start"].shift(-1)
    gap = s["end"] - s["start"]
    b, d = s["bikes_available"], s["docks_available"]
    state_ok = b.notna() & d.notna() & b.ge(0) & d.ge(0) & ~(b.eq(0) & d.eq(0))
    s["valid"] = state_ok & gap.gt(0) & gap.le(MAX_GAP_SECONDS)
    s = s[s["end"].notna()].copy()
    s["end"] = s["end"].astype("int64")
    s["dur"] = s["end"] - s["start"]
    for side, (_, col, _, _) in SIDES.items():
        s[f"out_{side}"] = s["valid"] & s[col].eq(0)      # stockout / full
        s[f"ok_{side}"] = s["valid"] & s[col].gt(0)       # service available
    return s.reset_index(drop=True)


def label_episodes(iv: pd.DataFrame, side: str) -> pd.DataFrame:
    flag = iv[f"out_{side}"]
    new_run = flag & ~(flag.shift(fill_value=False) & iv["station_id"].eq(iv["station_id"].shift()))
    ep = new_run.cumsum().where(flag)
    iv[f"ep_{side}"] = ep
    episodes = (iv[flag].groupby(ep[flag])
                .agg(station_id=("station_id", "first"), start=("start", "min"), end=("end", "max"))
                .reset_index(names="episode_id"))
    episodes["episode_id"] = episodes["episode_id"].astype("int64")
    return episodes


def available_seconds_between(iv_station: pd.DataFrame, side: str, a, b) -> np.ndarray:
    """Valid, available seconds in [a, b) for one station, vectorised over windows."""
    starts = iv_station["start"].to_numpy()
    dur = iv_station["dur"].to_numpy()
    ok = iv_station[f"ok_{side}"].to_numpy().astype(float)
    cum_end = np.cumsum(ok * dur)
    cum_start = cum_end - ok * dur

    def F(t):
        t = np.asarray(t)
        i = np.searchsorted(starts, t, side="right") - 1
        inside = i >= 0
        i = np.clip(i, 0, None)
        return np.where(inside, cum_start[i] + ok[i] * np.clip(t - starts[i], 0, dur[i]), 0.0)

    return F(b) - F(a)


def attach_event_state(events: pd.DataFrame, iv: pd.DataFrame, side: str) -> pd.DataFrame:
    """Give each event the state of the status interval containing it."""
    ev = events.sort_values("t").copy()
    look = iv[["station_id", "start", "end", f"ok_{side}", f"ep_{side}"]].sort_values("start")
    ev = pd.merge_asof(ev, look, left_on="t", right_on="start", by="station_id", direction="backward")
    inside = ev["end"].notna() & ev["t"].lt(ev["end"])
    ev["state_ok"] = inside & ev[f"ok_{side}"].fillna(False).astype(bool)
    ev["episode_id"] = ev[f"ep_{side}"].where(inside)
    return ev.drop(columns=["start", "end", f"ok_{side}", f"ep_{side}"])


def event_times(ev: pd.DataFrame, station, label) -> np.ndarray:
    """Sorted times of available-state events for one station and rider label."""
    m = ev["state_ok"] & ev["station_id"].eq(station) & ev["subscription_type"].eq(label)
    return np.sort(ev.loc[m, "t"].to_numpy())


def count_between(times: np.ndarray, a, b) -> np.ndarray:
    return np.searchsorted(times, b, "left") - np.searchsorted(times, a, "left")


def window_stats(frame, a_col, b_col, iv, ev, side, prefix):
    """Add <prefix>_avail (available seconds) and <prefix>_<rider> (available-state event counts) for [a, b)."""
    frame[f"{prefix}_avail"] = 0.0
    for rider in RIDERS:
        frame[f"{prefix}_{rider}"] = 0
    for st, idx in frame.groupby("station_id").groups.items():
        a, b = frame.loc[idx, a_col].to_numpy(), frame.loc[idx, b_col].to_numpy()
        frame.loc[idx, f"{prefix}_avail"] = available_seconds_between(iv[iv["station_id"].eq(st)], side, a, b)
        for rider, label in RIDERS.items():
            frame.loc[idx, f"{prefix}_{rider}"] = count_between(event_times(ev, st, label), a, b)
    return frame


# --------------------------------------------------------------------------- historical rates
def historical_rates(hourly: pd.DataFrame, min_exposure=MIN_GROUP_EXPOSURE_SECONDS):
    """Return (row_rates, rate_table).

    row_rates : one row per station-hour of the hourly table, with usual_<rider>_<side> (per second)
                and usual_level_<rider>_<side> in {'exact', 'pooled', 'none'}.
    rate_table: one row per station x hour x day type x side x rider with training events,
                available seconds, exact and pooled rates, the rate used and its support level."""
    rows = hourly[["station_id", "hour_start", "hour", "day_type"]].copy()
    train = hourly["split"].astype(str).str.lower().eq("training")
    groups = hourly[KEYS].drop_duplicates().sort_values(KEYS).reset_index(drop=True)
    tables = []
    threshold = max(min_exposure, 1)
    for side, (_, _, avail_col, _) in SIDES.items():
        for rider in RIDERS:
            num = f"{rider}_{side}_available_exposure"
            g1 = hourly.loc[train].groupby(KEYS)[[num, avail_col]].sum()
            g2 = hourly.loc[train].groupby(FALLBACK_KEYS)[[num, avail_col]].sum()
            r1 = (g1[num] / g1[avail_col]).where(g1[avail_col].ge(threshold)).rename("exact_rate")
            r2 = (g2[num] / g2[avail_col]).where(g2[avail_col].ge(threshold)).rename("pooled_rate")
            t = (groups.join(g1.rename(columns={num: "training_events", avail_col: "training_available_seconds"}), on=KEYS)
                       .join(r1, on=KEYS)
                       .join(g2.rename(columns={num: "pooled_events", avail_col: "pooled_available_seconds"}), on=FALLBACK_KEYS)
                       .join(r2, on=FALLBACK_KEYS))
            t["rate_per_second"] = t["exact_rate"].fillna(t["pooled_rate"])
            t["support_level"] = np.where(t["exact_rate"].notna(), "exact",
                                          np.where(t["pooled_rate"].notna(), "pooled", "none"))
            t.insert(0, "rider", rider)
            t.insert(0, "side", side)
            tables.append(t)
            joined = rows[KEYS].merge(t[KEYS + ["rate_per_second", "support_level"]], on=KEYS, how="left")
            rows[f"usual_{rider}_{side}"] = joined["rate_per_second"].to_numpy()
            rows[f"usual_level_{rider}_{side}"] = joined["support_level"].fillna("none").to_numpy()
    table = pd.concat(tables, ignore_index=True)
    table["rate_per_hour"] = table["rate_per_second"] * 3600
    return rows, table


def historical_integral(rates_station: pd.DataFrame, col: str):
    """Return f(a, b) = expected events in [a, b) under the station's hourly historical rates
    (each affected clock hour uses its own rate); NaN if any affected hour is unsupported."""
    r = rates_station.sort_values("hour_start")
    h = to_seconds(r["hour_start"]) // 3600
    assert (np.diff(h) == 1).all(), "station-hour grid must be contiguous"
    rate = r[col].to_numpy(dtype=float)
    nan = np.isnan(rate)
    rate0 = np.where(nan, 0.0, rate)
    C = np.concatenate([[0.0], np.cumsum(rate0 * 3600)])
    N = np.concatenate([[0], np.cumsum(nan)])
    h0, n = h[0], len(h)

    def G(t):
        i = np.clip(t // 3600 - h0, 0, n - 1)
        return C[i] + rate0[i] * np.clip(t - (h0 + i) * 3600, 0, 3600), i

    def integral(a, b):
        a, b = np.asarray(a), np.asarray(b)
        ga, ia = G(a)
        gb, ib = G(np.maximum(b - 1, a))
        val = np.where(b > a, gb + rate0[ib] - ga, 0.0)    # b - 1 keeps b inside the grid
        bad = (b > a) & ((N[ib + 1] - N[ia]) > 0)
        return np.where(bad, np.nan, val)

    return integral


# --------------------------------------------------------------------------- episode estimation
def split_into_hours(episodes: pd.DataFrame) -> pd.DataFrame:
    """One row per episode x clock hour, clipped to the 70-day study window."""
    e = episodes.copy()
    e["s"] = e["start"].clip(lower=T0)
    e["e"] = e["end"].clip(upper=T1)
    e = e[e["e"] > e["s"]]
    first_h = e["s"] // 3600
    n = (e["e"] - 1) // 3600 - first_h + 1
    seg = e.loc[e.index.repeat(n)].copy()
    seg["h"] = first_h.loc[seg.index] + seg.groupby(level=0).cumcount()
    seg["seg_s"] = np.maximum(seg["s"], seg["h"] * 3600)
    seg["seg_e"] = np.minimum(seg["e"], (seg["h"] + 1) * 3600)
    seg["seconds"] = seg["seg_e"] - seg["seg_s"]
    seg["hour_start"] = to_timestamp(seg["h"] * 3600)
    return seg[["episode_id", "station_id", "hour_start", "seg_s", "seg_e", "seconds"]].reset_index(drop=True)


def estimate_side(side, iv, events, row_rates, cfg):
    event_type = SIDES[side][0]
    episodes = label_episodes(iv, side)
    ev = attach_event_state(events[events["event_type"].eq(event_type)], iv, side)

    # Pre-window available seconds and events (any split: the window may sit in the context period).
    episodes["pre_a"] = episodes["start"] - cfg["pre_window"]
    episodes = window_stats(episodes, "pre_a", "start", iv, ev, side, "pre").drop(columns="pre_a")
    episodes = episodes.rename(columns={"pre_avail": "pre_available_seconds"})
    horizon = cfg["pre_horizon"]
    episodes["use_pre_rate"] = episodes["pre_available_seconds"].ge(cfg["min_pre"]) & (horizon > 0)

    # Events actually recorded during each episode (study window only).
    served = (ev[ev["episode_id"].notna() & ev["in_study_window"]]
              .groupby(["episode_id", "subscription_type"]).size().unstack(fill_value=0))
    for rider, label in RIDERS.items():
        col = served[label] if label in served else pd.Series(dtype=float)
        episodes[f"served_{rider}"] = episodes["episode_id"].map(col).fillna(0).astype(int)

    seg = split_into_hours(episodes).merge(row_rates, on=["station_id", "hour_start"], how="left")
    seg = seg.merge(episodes, on=["episode_id", "station_id"], how="left")
    # Seconds of each hour-segment inside the pre-rate horizon [start, start + horizon).
    cut = seg["start"] + min(horizon, 10 ** 12)
    pre_sec = (np.minimum(seg["seg_e"], cut) - seg["seg_s"]).clip(lower=0).where(seg["use_pre_rate"], 0)
    hist_sec = seg["seconds"] - pre_sec
    for rider in RIDERS:
        pre_rate = seg[f"pre_{rider}"] / seg["pre_available_seconds"].replace(0, np.nan)
        hist_rate = seg[f"usual_{rider}_{side}"]
        seg[f"expected_{rider}"] = (np.where(pre_sec > 0, pre_rate * pre_sec, 0.0)
                                    + np.where(hist_sec > 0, hist_rate * hist_sec, 0.0))
        seg.loc[(hist_sec > 0) & hist_rate.isna(), f"expected_{rider}"] = np.nan   # unsupported -> unresolved
        g = seg.groupby("episode_id")[f"expected_{rider}"]
        any_nan = seg[f"expected_{rider}"].isna().groupby(seg["episode_id"]).transform("any")
        tot = g.transform("sum").where(~any_nan)
        unmet_ep = np.maximum(tot - seg[f"served_{rider}"], 0.0)
        share = np.where(tot > 0, seg[f"expected_{rider}"] / tot.where(tot > 0), 0.0)
        seg[f"unmet_{rider}"] = np.where(tot.notna(), unmet_ep * share, np.nan)
        level = seg[f"usual_level_{rider}_{side}"]
        hist_label = np.where(level.eq("exact"), cfg["usual_label"],
                              np.where(level.eq("pooled"), cfg["pooled_label"], "unresolved"))
        seg[f"method_{rider}"] = np.where(
            hist_sec.eq(0), "pre_stockout",
            np.where(pre_sec.gt(0), np.char.add("pre_stockout+", hist_label.astype(str)), hist_label))

    agg = seg.groupby("episode_id").agg(window_seconds=("seconds", "sum"),
                                        pre_rate_seconds=("seconds", lambda x: pre_sec[x.index].sum()),
                                        **{f"expected_{r}": (f"expected_{r}", lambda x: x.sum(min_count=len(x))) for r in RIDERS},
                                        **{f"unmet_{r}": (f"unmet_{r}", lambda x: x.sum(min_count=len(x))) for r in RIDERS})
    episodes = episodes.merge(agg, on="episode_id", how="inner")
    episodes.insert(1, "side", side)
    return seg, episodes, ev


def hour_method(methods: pd.Series) -> str:
    u = sorted({part for m in methods for part in str(m).split("+")})
    return "unresolved" if "unresolved" in u else "+".join(u)


def prepare_inputs(hourly, events):
    hourly = hourly.copy()
    hourly["hour_start"] = pd.to_datetime(hourly["hour_start"])
    hourly["service_date"] = pd.to_datetime(hourly["service_date"])
    assert not hourly.duplicated(["station_id", "hour_start"]).any(), "Duplicate station-hour keys"
    events = events.copy()
    events["t"] = to_seconds(events["event_at"])
    events["in_study_window"] = events["in_study_window"].astype(str).str.lower().eq("true")
    return hourly, events


def make_demand(hourly, status, events, cfg, min_exposure=MIN_GROUP_EXPOSURE_SECONDS):
    hourly, events = prepare_inputs(hourly, events)
    iv = build_intervals(status)
    row_rates, rate_table = historical_rates(hourly, min_exposure)

    result = hourly[OUTPUT_COLUMNS[:11]].copy()
    no_status = result["status_exposure_missing"].astype(str).str.lower().eq("true")
    result["status_exposure_missing"] = no_status
    audits, side_events, checks = [], {}, {}
    for side, (_, _, _, unavail_col) in SIDES.items():
        seg, episodes, ev = estimate_side(side, iv, events, row_rates, cfg)
        audits.append(episodes)
        side_events[side] = ev
        key = ["station_id", "hour_start"]
        per_hour = seg.groupby(key).agg(seconds=("seconds", "sum"),
                                        **{f"method_{r}": (f"method_{r}", hour_method) for r in RIDERS},
                                        **{f"unmet_{r}": (f"unmet_{r}", lambda x: x.sum(min_count=len(x))) for r in RIDERS})
        joined = hourly[key].join(per_hour, on=key)
        checks[f"max_abs_diff_{unavail_col}_vs_V3"] = float((joined["seconds"].fillna(0) - hourly[unavail_col]).abs().max())
        for rider in RIDERS:
            observed = hourly[f"{rider}_{side}"].astype(float)
            missed = joined[f"unmet_{rider}"]
            method = np.select(
                [no_status.to_numpy(), joined["seconds"].isna().to_numpy(), missed.isna().to_numpy()],
                ["no_status_observed", "observed", "unresolved"], default=joined[f"method_{rider}"].fillna("observed"))
            missed = missed.where(~np.isin(method, ["no_status_observed", "observed"]), 0.0)
            result[f"observed_{rider}_{side}"] = observed
            result[f"estimated_{rider}_{side}"] = observed + missed   # unresolved stays NaN on purpose
            result[f"missed_{rider}_{side}"] = missed
            result[f"method_{rider}_{side}"] = method
    for side in SIDES:
        result[f"estimated_total_{side}"] = result[f"estimated_subscriber_{side}"] + result[f"estimated_customer_{side}"]
        result[f"observed_total_{side}"] = result[f"observed_subscriber_{side}"] + result[f"observed_customer_{side}"]
    for c in OUTPUT_COLUMNS[7:11]:
        result[c] = result[c].astype(float)
    result = result[OUTPUT_COLUMNS].sort_values(["service_date", "hour", "station_id"]).reset_index(drop=True)
    episodes = pd.concat(audits, ignore_index=True)
    return dict(result=result, episodes=episodes, checks=checks, iv=iv, side_events=side_events,
                row_rates=row_rates, rate_table=rate_table, hourly=hourly)


# --------------------------------------------------------------------------- prediction for any window
def predict_window(a, b, origin, cfg, pre_avail, pre_counts, integral):
    """Expected events in [a, b) for a (pseudo) episode that starts at `origin`, under case cfg.
    pre_avail / pre_counts describe the window [origin - pre_window, origin)."""
    use_pre = (pre_avail >= cfg["min_pre"]) & (cfg["pre_horizon"] > 0)
    cut = np.clip(origin + min(cfg["pre_horizon"], 10 ** 12), a, b)          # end of pre-rate part
    pre_rate = pre_counts / np.where(pre_avail > 0, pre_avail, np.nan)
    with_pre = np.where(cut > a, pre_rate * (cut - a), 0.0) + integral(cut, b)
    return np.where(use_pre, with_pre, integral(a, b))


# --------------------------------------------------------------------------- matched validation
def validation_targets(hourly, iv, episodes, side):
    stations = np.sort(hourly["station_id"].unique())
    e = episodes[episodes["side"].eq(side) & (episodes["end"] - episodes["start"]).gt(NEAR_STOCKOUT_MIN_EPISODE_SECONDS)]
    parts = [pd.DataFrame({"station_id": e["station_id"].to_numpy(), "test": "near_stockout_10min",
                           "a": (e["start"] - NEAR_STOCKOUT_TARGET_SECONDS).to_numpy(), "b": e["start"].to_numpy(),
                           "episode_id": e["episode_id"].to_numpy()})]
    for test, H in LONG_HORIZONS.items():
        origins = np.arange(V0, T1 - H + 1, 3600)
        parts.append(pd.DataFrame({"station_id": np.repeat(stations, len(origins)), "test": test,
                                   "a": np.tile(origins, len(stations)),
                                   "b": np.tile(origins, len(stations)) + H, "episode_id": -1}))
    t = pd.concat(parts, ignore_index=True)
    t = t[t["a"].ge(V0) & t["b"].le(T1)].copy()            # held-out dates only
    t["target_avail"] = 0.0
    for st, idx in t.groupby("station_id").groups.items():
        t.loc[idx, "target_avail"] = available_seconds_between(
            iv[iv["station_id"].eq(st)], side, t.loc[idx, "a"].to_numpy(), t.loc[idx, "b"].to_numpy())
    return t[t["target_avail"].eq(t["b"] - t["a"])].reset_index(drop=True)   # fully valid and available


def matched_validation(run, methods=VALIDATION_METHODS):
    hourly, iv, side_events, row_rates = run["hourly"], run["iv"], run["side_events"], run["row_rates"]
    day_type = hourly.set_index(["station_id", "hour_start"])["day_type"]
    out = []
    for side in SIDES:
        ev = side_events[side]
        t = validation_targets(hourly, iv, run["episodes"], side)
        t.insert(1, "side", side)
        for st, idx in t.groupby("station_id").groups.items():
            a, b = t.loc[idx, "a"].to_numpy(), t.loc[idx, "b"].to_numpy()
            iv_st = iv[iv["station_id"].eq(st)]
            r_st = row_rates[row_rates["station_id"].eq(st)]
            for rider, label in RIDERS.items():
                times = event_times(ev, st, label)
                t.loc[idx, f"actual_{rider}"] = count_between(times, a, b)
                integral = historical_integral(r_st, f"usual_{rider}_{side}")
                for name, case in methods.items():
                    cfg = CASES[case]
                    pa = available_seconds_between(iv_st, side, a - cfg["pre_window"], a)
                    pc = count_between(times, a - cfg["pre_window"], a)
                    t.loc[idx, f"pred_{name}_{rider}"] = predict_window(a, b, a, cfg, pa, pc, integral)
                    t.loc[idx, f"used_pre_{name}"] = (pa >= cfg["min_pre"]) & (cfg["pre_horizon"] > 0)
        out.append(t)
    t = pd.concat(out, ignore_index=True)
    t["origin"] = to_timestamp(t["a"])
    t["origin_day_type"] = day_type.reindex(pd.MultiIndex.from_arrays(
        [t["station_id"], to_timestamp((t["a"] // 3600) * 3600)])).to_numpy()
    t["weekday_peak"] = t["origin_day_type"].eq("Weekday") & t["origin"].dt.hour.isin(PEAK_HOURS)
    three = t.loc[t["test"].eq("available_3hour"), ["side", "station_id", "a"]].assign(common=True)
    t = t.merge(three, on=["side", "station_id", "a"], how="left")
    t["common_3hour_origin"] = t["common"].fillna(False).astype(bool) & t["test"].ne("near_stockout_10min")
    return t.drop(columns="common")


def summarise_validation(t, methods=VALIDATION_METHODS):
    groups = {"all_eligible": t, "weekday_peak": t[t["weekday_peak"]], "common_3hour_origins": t[t["common_3hour_origin"]]}
    rows = []
    for gname, g in groups.items():
        for (test, side), s in g.groupby(["test", "side"]):
            for rider in RIDERS:
                # Unsupported rates must not cause different methods to be scored on different targets.
                paired = s[f"actual_{rider}"].notna()
                for name in methods:
                    paired &= s[f"pred_{name}_{rider}"].notna()
                act = s.loc[paired, f"actual_{rider}"]
                for name in methods:
                    err = s.loc[paired, f"pred_{name}_{rider}"] - act
                    ok = err.notna()
                    rows.append({"group": gname, "test": test, "side": side, "rider": rider, "method": name,
                                 "n": int(ok.sum()), "mean_actual": act[ok].mean(), "mae": err[ok].abs().mean(),
                                 "rmse": float(np.sqrt((err[ok] ** 2).mean())), "bias": err[ok].mean()})
    long = pd.DataFrame(rows).sort_values(["group", "test", "side", "rider", "method"]).reset_index(drop=True)
    a = long[long["group"].eq("all_eligible")]
    keys = ["test", "side", "rider"]
    historical = a[a["method"].eq("case_a_historical")].set_index(keys)
    hybrid = a[a["method"].eq("case_b_hybrid")].set_index(keys)
    out = pd.DataFrame(index=hybrid.index)
    out["n"] = hybrid["n"].astype(int)
    for stat in ("mae", "rmse", "bias"):
        out[f"hybrid_{stat}"] = hybrid[stat]
        out[f"historical_{stat}"] = historical[stat].reindex(out.index)
    out = out[["n", "hybrid_mae", "historical_mae", "hybrid_rmse", "historical_rmse", "hybrid_bias", "historical_bias"]]
    return long, out.reset_index()


def censoring_diagnostic(run, cfg):
    """Descriptive only: the case's prediction for the last 10 minutes INSIDE stockouts longer than
    15 minutes vs. trips recorded there. Recorded trips are censored by the stockout itself."""
    ep, iv, row_rates = run["episodes"], run["iv"], run["row_rates"]
    rows = []
    H = NEAR_STOCKOUT_TARGET_SECONDS
    for side in SIDES:
        e = ep[ep["side"].eq(side) & (ep["end"] - ep["start"]).gt(NEAR_STOCKOUT_MIN_EPISODE_SECONDS)
               & ep["start"].ge(T0) & ep["end"].le(T1)].copy()
        ev = run["side_events"][side]
        e["a"], e["b"] = e["end"] - H, e["end"]
        for st, idx in e.groupby("station_id").groups.items():
            r_st = row_rates[row_rates["station_id"].eq(st)]
            for rider, label in RIDERS.items():
                inside = ev[ev["station_id"].eq(st) & ev["subscription_type"].eq(label)]["t"].sort_values().to_numpy()
                a, b = e.loc[idx, "a"].to_numpy(), e.loc[idx, "b"].to_numpy()
                e.loc[idx, f"recorded_{rider}"] = count_between(inside, a, b)
                e.loc[idx, f"predicted_{rider}"] = predict_window(
                    a, b, e.loc[idx, "start"].to_numpy(), cfg, e.loc[idx, "pre_available_seconds"].to_numpy(),
                    e.loc[idx, f"pre_{rider}"].to_numpy(), historical_integral(r_st, f"usual_{rider}_{side}"))
        e["split"] = np.where(e["a"] >= V0, "validation", "training")
        rows.append(e)
    out = pd.concat(rows, ignore_index=True)
    out["start"], out["end"] = to_timestamp(out["start"]), to_timestamp(out["end"])
    keep = ["episode_id", "side", "station_id", "start", "end", "split", "use_pre_rate"] + \
           [f"{k}_{r}" for r in RIDERS for k in ("predicted", "recorded")]
    return out[keep]


# --------------------------------------------------------------------------- CLI
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(case="hybrid", argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--case", choices=tuple(CASES), default=case)
    ap.add_argument("--hourly", required=True, help="model_inputs_v3/station_hour_observed.csv.gz")
    ap.add_argument("--minute-dir", required=True, help="demand_estimation_inputs_v3 folder")
    ap.add_argument("--output-dir", required=True, help="folder for all outputs (not model_inputs_v3)")
    ap.add_argument("--pre-window-seconds", type=int, help="override the case look-back window")
    ap.add_argument("--min-pre-available-seconds", type=int, help="override the case minimum available time")
    ap.add_argument("--min-group-exposure-seconds", type=int, default=MIN_GROUP_EXPOSURE_SECONDS)
    ap.add_argument("--skip-validation", action="store_true")
    args = ap.parse_args(argv)

    out_dir = Path(args.output_dir).resolve()
    if "model_inputs_v3" in out_dir.parts:
        raise SystemExit("Refusing to write estimated demand into the frozen model_inputs_v3 folder.")
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = case_config(args.case, pre_window=args.pre_window_seconds, min_pre=args.min_pre_available_seconds)
    horizon_txt = {0: "never", INF: "whole episode"}.get(cfg["pre_horizon"], f"first {cfg['pre_horizon'] / 60:.0f} min")
    print(f"Case = {args.case}: pre-window {cfg['pre_window'] / 60:.0f} min (min {cfg['min_pre'] / 60:.0f} min "
          f"available), pre-rate used for {horizon_txt}; historical groups need >= "
          f"{args.min_group_exposure_seconds / 60:.0f} available training minutes")

    folder = Path(args.minute_dir)
    inputs = {"hourly": Path(args.hourly), "status": folder / "status.csv.gz", "trip_events": folder / "trip_events.csv.gz"}
    hourly = pd.read_csv(inputs["hourly"])
    status = pd.read_csv(inputs["status"])
    status["time"] = pd.to_datetime(status["time"], format="%Y/%m/%d %H:%M:%S")
    events = pd.read_csv(inputs["trip_events"])

    r = make_demand(hourly, status, events, cfg, args.min_group_exposure_seconds)
    result, episodes = r["result"], r["episodes"]
    files = {}

    def save(df, name):
        path = out_dir / name
        df.to_csv(path, index=False, date_format="%Y-%m-%d %H:%M:%S", lineterminator="\n")
        files[name] = path

    save(result, f"estimated_demand_station_hour_{args.case}.csv")
    ep = episodes.copy()
    ep["start"], ep["end"] = to_timestamp(ep["start"]), to_timestamp(ep["end"])
    save(ep, f"stockout_episodes_{args.case}.csv")
    save(r["rate_table"], "historical_rates.csv")

    print("\nChecks (should be 0):", r["checks"])
    totals = {}
    for side in SIDES:
        e = episodes[episodes["side"].eq(side)]
        print(f"{side}: {len(e)} episodes, pre-window rate used in {e['use_pre_rate'].mean():.1%}")
        for rider in RIDERS:
            o, est = result[f"observed_{rider}_{side}"].sum(), result[f"estimated_{rider}_{side}"].sum()
            unresolved = int(result[f"method_{rider}_{side}"].eq("unresolved").sum())
            totals[f"{rider}_{side}"] = {"observed": float(o), "estimated": float(est), "unresolved_hours": unresolved}
            print(f"  {rider:<10} observed {o:>8,.0f}  estimated {est:>10,.1f}  (+{(est / o - 1):.1%})  "
                  f"unresolved hours {unresolved}")
    support = r["rate_table"]["support_level"].value_counts().to_dict()
    print("Historical rate support levels:", support)

    if not args.skip_validation:
        targets = matched_validation(r)
        long, wide = summarise_validation(targets)
        save(targets.drop(columns=["a", "b"]), "validation_targets.csv")
        save(long, "validation_by_origin_group.csv")
        save(wide, "matched_validation.csv")
        save(censoring_diagnostic(r, cfg), f"censoring_diagnostic_{args.case}.csv")
        with pd.option_context("display.width", 200, "display.precision", 3):
            print("\nMatched validation (held-out 6-19 April, fully available targets, same windows for both cases):")
            print(wide.to_string(index=False))

    manifest = {
        "case": args.case, "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "parameters": {**{k: (None if v == INF else v) for k, v in cfg.items()},
                       "min_group_exposure_seconds": args.min_group_exposure_seconds,
                       "max_gap_seconds": MAX_GAP_SECONDS, "study_start": str(STUDY_START),
                       "validation_start": str(VALIDATION_START), "study_end_exclusive": str(STUDY_END),
                       "weekday_peak_hours": list(PEAK_HOURS)},
        "checks": r["checks"], "totals": totals, "historical_rate_support": support,
        "episodes": {s: int(episodes["side"].eq(s).sum()) for s in SIDES}, "rows": int(len(result)),
        "inputs_sha256": {k: sha256(p) for k, p in inputs.items()},
        "outputs_sha256": {k: sha256(p) for k, p in files.items()},
        "code_sha256": sha256(__file__),
    }
    (out_dir / f"run_manifest_{args.case}.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nWrote {len(files) + 1} files to {out_dir}")
    return r


if __name__ == "__main__":
    run()
