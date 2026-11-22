# Legacy PR #1 entry point; current integrated costs/demand use run_integrated_pipeline.py.
#!/usr/bin/env python3
"""Reproduce the availability-adjusted demand method in DBA5103 report §3.4.

Usage:
  python build_joohee_demand.py \
      --input output/sf_bikeshare/model_inputs_v3/station_hour_observed.csv.gz \
      --output output/sf_bikeshare/model_inputs_v3/estimated_demand_station_hour.csv

Retrospective reconstruction: the within-hour rate uses within-hour observed
activity, so the resulting estimates are not an ex-ante forecast.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

MIN_AVAILABLE_SECONDS = 600
KEYS = ["station_id", "hour", "day_type"]
FALLBACK_KEYS = ["station_id", "hour"]


def make_demand(source: pd.DataFrame, min_available_seconds: int = MIN_AVAILABLE_SECONDS) -> pd.DataFrame:
    df = source.copy()
    for column in ["hour_start", "service_date"]:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column])
    mandatory = ["station_id", "service_date", "hour", "day_type", "split", "observed_seconds", "empty_seconds", "full_seconds", "bike_available_seconds", "dock_available_seconds", "status_exposure_missing"]
    for side in ("pickups", "returns"):
        for rider in ("subscriber", "customer"):
            mandatory += [f"{rider}_{side}", f"{rider}_{side}_available_exposure"]
    missing = [c for c in mandatory if c not in df.columns]
    if missing:
        raise ValueError(f"Missing V3 fields: {missing}")
    assert not df.duplicated(["station_id", "service_date", "hour"]).any(), "Duplicate station-date-hour keys"

    result_cols = ["station_id", "service_date", "hour", "hour_start", "day_type", "split", "status_exposure_missing", "empty_seconds", "full_seconds", "bike_available_seconds", "dock_available_seconds"]
    result = df[[c for c in result_cols if c in df.columns]].copy()
    train = df["split"].astype(str).str.lower().eq("training")

    for side in ("pickups", "returns"):
        exposure_column = "bike_available_seconds" if side == "pickups" else "dock_available_seconds"
        missing_seconds_column = "empty_seconds" if side == "pickups" else "full_seconds"
        available = df[exposure_column].astype(float)
        absent_seconds = df[missing_seconds_column].astype(float)
        no_status = df["status_exposure_missing"].fillna(False).astype(bool)
        for rider in ("subscriber", "customer"):
            observed_col = f"{rider}_{side}"
            numerator_col = f"{rider}_{side}_available_exposure"
            observed = df[observed_col].astype(float)
            numerator = df[numerator_col].astype(float)

            # Pool matched observed pickups/returns and available exposure, on training days only.
            g = (df.loc[train, KEYS + [exposure_column, numerator_col]]
                   .groupby(KEYS, as_index=False)[[exposure_column, numerator_col]].sum())
            g["rate"] = g[numerator_col] / g[exposure_column].replace(0, np.nan)
            exact_rates = df[KEYS].merge(g[KEYS + ["rate"]], how="left", on=KEYS)["rate"].to_numpy()
            all_day = (df.loc[train, FALLBACK_KEYS + [exposure_column, numerator_col]]
                         .groupby(FALLBACK_KEYS, as_index=False)[[exposure_column, numerator_col]].sum())
            all_day["rate"] = all_day[numerator_col] / all_day[exposure_column].replace(0, np.nan)
            backup_rates = df[FALLBACK_KEYS].merge(all_day[FALLBACK_KEYS + ["rate"]], how="left", on=FALLBACK_KEYS)["rate"].to_numpy()
            pooled = pd.Series(exact_rates).fillna(pd.Series(backup_rates)).to_numpy()
            rate_own = np.divide(numerator, available, out=np.full(len(df), np.nan), where=available.ge(min_available_seconds))

            method = np.select(
                [no_status.to_numpy(), absent_seconds.eq(0).to_numpy(), available.ge(min_available_seconds).to_numpy(), np.isfinite(pooled)],
                ["no_status_observed", "observed", "own_hour", "pooled"],
                default="unresolved"
            )
            rate = np.where(method == "own_hour", rate_own, np.where(method == "pooled", pooled, np.nan))
            # Unknown must remain unknown; never silently turn missing demand into zero.
            increment = np.where(np.isin(method, ["observed", "no_status_observed"]), 0.0, rate * absent_seconds)
            estimate = observed + increment
            result[f"observed_{rider}_{side}"] = observed
            result[f"estimated_{rider}_{side}"] = estimate
            result[f"missed_{rider}_{side}"] = increment
            result[f"method_{rider}_{side}"] = method
    for side in ("pickups", "returns"):
        result[f"estimated_total_{side}"] = result[f"estimated_subscriber_{side}"] + result[f"estimated_customer_{side}"]
        result[f"observed_total_{side}"] = result[f"observed_subscriber_{side}"] + result[f"observed_customer_{side}"]
    result = result.sort_values(["service_date", "hour", "station_id"]).reset_index(drop=True)
    return result


def validate_pooled_rate(source: pd.DataFrame) -> dict:
    """Evaluate training pooled rate against *completed* pickups in fully-available holdout hours."""
    tr = source["split"].astype(str).str.lower().eq("training")
    va = source["split"].astype(str).str.lower().eq("validation")
    full = va & source["bike_available_seconds"].eq(3600) & source["observed_seconds"].eq(3600) & source["empty_seconds"].eq(0)
    results = {"n_fully_available_validation_hours": int(full.sum())}
    for rider in ("subscriber", "customer"):
        num = f"{rider}_pickups_available_exposure"
        obs = f"{rider}_pickups"
        pooled = (source.loc[tr, KEYS + [num, "bike_available_seconds"]]
                  .groupby(KEYS, as_index=False)[[num, "bike_available_seconds"]].sum())
        pooled["pred"] = pooled[num] / pooled["bike_available_seconds"].replace(0, np.nan) * 3600
        avg = source.loc[tr, KEYS + [obs]].groupby(KEYS, as_index=False)[obs].mean().rename(columns={obs:"avg"})
        check = source.loc[full, KEYS + [obs]].merge(pooled[KEYS + ["pred"]], how="left").merge(avg, how="left")
        # If a subgroup is absent, only report performance over predictions available for both methods.
        use = check["pred"].notna() & check["avg"].notna()
        results[rider] = {
            "n": int(use.sum()),
            "mean_actual": float(check.loc[use, obs].mean()),
            "mae_pooled": float((check.loc[use, obs] - check.loc[use, "pred"]).abs().mean()),
            "mae_training_mean": float((check.loc[use, obs] - check.loc[use, "avg"]).abs().mean()),
        }
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to Carlo's station_hour_observed.csv.gz")
    ap.add_argument("--output", required=True, help="Desired output CSV")
    args = ap.parse_args()
    source = pd.read_csv(args.input)
    result = make_demand(source)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(target, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print("Wrote", target, "rows=", len(result))
    for side in ("pickups", "returns"):
        for rider in ("subscriber", "customer"):
            c = f"estimated_{rider}_{side}"
            print(c, round(result[c].sum(), 4), "unresolved", (result[f"method_{rider}_{side}"] == "unresolved").sum())
    print("Validation:", validate_pooled_rate(source))

if __name__ == "__main__":
    main()
