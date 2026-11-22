#!/usr/bin/env python3
"""Tests for build_demand_minute.py, focused on branches the main V3 case never exercises
(every V3 station/hour/day-type group has >= 60 available training minutes).

  python sf_bikeshare/test_demand_estimation.py                      # synthetic tests only
  python sf_bikeshare/test_demand_estimation.py \
      --hourly output/sf_bikeshare/model_inputs_v3/station_hour_observed.csv.gz \
      --minute-dir output/sf_bikeshare/demand_estimation_inputs_v3   # + real-data fallback tests
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_demand_minute as bd  # noqa: E402


def synthetic_hourly():
    """Two stations, clock hour 8, two day types, training + validation rows."""
    rows = []
    days = pd.date_range("2015-03-02", periods=7, freq="D")          # Mon-Sun, training
    for st in (1, 2):
        for d in list(days) + [pd.Timestamp("2015-04-06")]:          # + one validation Monday
            dt = "Weekend" if d.weekday() >= 5 else "Weekday"
            # station 1: weekend hour 8 has only 15 available minutes per day (2 days = 30 min);
            # station 2: every day has only 5 available minutes (7 days = 35 min in total).
            avail = 3600 if (st == 1 and dt == "Weekday") else (900 if st == 1 else 300)
            row = {"station_id": st, "hour_start": d + pd.Timedelta(hours=8), "service_date": d, "hour": 8,
                   "day_type": dt, "split": "validation" if d >= bd.VALIDATION_START else "training",
                   "status_exposure_missing": False, "bike_available_seconds": avail, "dock_available_seconds": avail}
            for side in bd.SIDES:
                for rider in bd.RIDERS:
                    row[f"{rider}_{side}_available_exposure"] = 2 if rider == "subscriber" else 1
            rows.append(row)
    return pd.DataFrame(rows)


def test_rate_support_levels():
    h = synthetic_hourly()
    rows, table = bd.historical_rates(h, min_exposure=3600)
    t = table[(table["side"] == "pickups") & (table["rider"] == "subscriber")].set_index(["station_id", "day_type"])
    # Station 1 weekday: 5 days x 3600 s, 2 events/day -> exact rate 10 / 18000.
    assert t.loc[(1, "Weekday"), "support_level"] == "exact"
    assert np.isclose(t.loc[(1, "Weekday"), "rate_per_second"], 10 / 18000)
    # Station 1 weekend: 1800 s < 3600 -> pooled across day types = 14 events / (18000 + 1800) s (ratio of sums).
    assert t.loc[(1, "Weekend"), "support_level"] == "pooled"
    assert np.isclose(t.loc[(1, "Weekend"), "rate_per_second"], 14 / 19800)
    # Station 2: 7 x 300 = 2100 s pooled < 3600 -> unresolved (NaN, never zero).
    assert (t.loc[2, "support_level"] == "none").all()
    assert t.loc[2, "rate_per_second"].isna().all()
    # Validation rows get training rates but never contribute to them.
    v = rows[rows["hour_start"] == pd.Timestamp("2015-04-06 08:00")].set_index("station_id")
    assert np.isclose(v.loc[1, "usual_subscriber_pickups"], 10 / 18000)
    assert np.isnan(v.loc[2, "usual_subscriber_pickups"]) and v.loc[2, "usual_level_subscriber_pickups"] == "none"


def test_hour_method_labels():
    assert bd.hour_method(pd.Series(["pre_stockout", "pre_stockout+historical"])) == "historical+pre_stockout"
    assert bd.hour_method(pd.Series(["historical", "unresolved"])) == "unresolved"
    assert bd.hour_method(pd.Series(["historical_station_hour_daytype"])) == "historical_station_hour_daytype"


def test_integral_and_hybrid_prediction():
    # One station, hourly rates 1/s at 08:00, 2/s at 09:00, NaN at 10:00.
    hs = pd.to_datetime(["2015-04-06 08:00", "2015-04-06 09:00", "2015-04-06 10:00"])
    rates = pd.DataFrame({"hour_start": hs, "r": [1.0, 2.0, np.nan]})
    f = bd.historical_integral(rates, "r")
    a = bd.to_seconds([pd.Timestamp("2015-04-06 08:55")])
    b = bd.to_seconds([pd.Timestamp("2015-04-06 09:05")])
    assert np.isclose(f(a, b)[0], 300 * 1 + 300 * 2)                  # integrates both hours
    c = bd.to_seconds([pd.Timestamp("2015-04-06 10:30")])
    assert np.isnan(f(a, c)[0])                                        # unsupported hour -> NaN
    # Hybrid on a 3-hour window from 08:00: pre-rate 0.5/s for the first hour, historical after it.
    a8 = bd.to_seconds([pd.Timestamp("2015-04-06 08:00")])
    cfg = dict(bd.CASES["hybrid"])
    p = bd.predict_window(a8, a8 + 7200, a8, cfg, np.array([1800.0]), np.array([900]), f)
    assert np.isclose(p[0], 0.5 * 3600 + 2.0 * 3600)
    # Insufficient pre-window exposure -> historical throughout.
    p = bd.predict_window(a8, a8 + 7200, a8, cfg, np.array([1000.0]), np.array([900]), f)
    assert np.isclose(p[0], 1.0 * 3600 + 2.0 * 3600)
    # Historical case never uses the pre-window.
    p = bd.predict_window(a8, a8 + 7200, a8, dict(bd.CASES["historical"]), np.array([1800.0]), np.array([900]), f)
    assert np.isclose(p[0], 1.0 * 3600 + 2.0 * 3600)


def real_data_tests(hourly_path, minute_dir):
    hourly = pd.read_csv(hourly_path)
    status = pd.read_csv(Path(minute_dir) / "status.csv.gz")
    status["time"] = pd.to_datetime(status["time"], format="%Y/%m/%d %H:%M:%S")
    events = pd.read_csv(Path(minute_dir) / "trip_events.csv.gz")
    cfg = bd.case_config("historical")

    # Pick a threshold just above the smallest exact-group exposure so at least one group must pool.
    base = bd.make_demand(hourly, status, events, cfg)
    exp = base["rate_table"]["training_available_seconds"]
    threshold = int(exp.min()) + 1
    r = bd.make_demand(hourly, status, events, cfg, min_exposure=threshold)
    lv = r["rate_table"]["support_level"].value_counts()
    assert lv.get("pooled", 0) > 0, "expected pooled groups"
    pooled = r["rate_table"][r["rate_table"]["support_level"].eq("pooled")]
    assert np.allclose(pooled["rate_per_second"], pooled["pooled_events"] / pooled["pooled_available_seconds"])
    print(f"  pooled branch: threshold {threshold} s -> {int(lv.get('pooled', 0))} pooled groups;",
          "hour labels:", sorted({m for c in r["result"].filter(like="method_") for m in r["result"][c].unique()}))

    # Threshold above every group -> nothing supported -> adjusted hours unresolved (NaN), never zero.
    r = bd.make_demand(hourly, status, events, cfg, min_exposure=10 ** 9)
    res = r["result"]
    for side, (_, _, _, unavail) in bd.SIDES.items():
        for rider in bd.RIDERS:
            m = res[f"method_{rider}_{side}"]
            adjusted = res[unavail].gt(0) & ~res["status_exposure_missing"]
            assert (m[adjusted] == "unresolved").all()
            assert res.loc[adjusted, f"estimated_{rider}_{side}"].isna().all()
            assert res.loc[~adjusted, f"estimated_{rider}_{side}"].notna().all()
            assert np.array_equal(res.loc[~adjusted, f"estimated_{rider}_{side}"], res.loc[~adjusted, f"observed_{rider}_{side}"])
    print(f"  unresolved branch: {int(res['method_subscriber_pickups'].eq('unresolved').sum())} pickup hours flagged, no zeros substituted")

    # Base case unchanged by the tests: every group exact, nothing unresolved.
    assert set(base["rate_table"]["support_level"]) == {"exact"}
    assert not base["result"].filter(like="method_").isin(["unresolved"]).any().any()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hourly")
    ap.add_argument("--minute-dir")
    args = ap.parse_args()
    for test in (test_rate_support_levels, test_hour_method_labels, test_integral_and_hybrid_prediction):
        test()
        print("PASS", test.__name__)
    if args.hourly and args.minute_dir:
        real_data_tests(args.hourly, args.minute_dir)
        print("PASS real_data_tests")
