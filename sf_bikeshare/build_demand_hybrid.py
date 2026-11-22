#!/usr/bin/env python3
"""Case B (sensitivity): hybrid demand. 30-minute pre-episode rate (>= 20 valid available minutes)
for the first 60 elapsed minutes of each empty/full episode, historical rates afterwards.

Thin wrapper around build_demand_minute.py --case hybrid; see that module for the method,
validation and outputs. Example (from the repository root):
  python sf_bikeshare/build_demand_hybrid.py \
      --hourly output/sf_bikeshare/model_inputs_v3/station_hour_observed.csv.gz \
      --minute-dir output/sf_bikeshare/demand_estimation_inputs_v3 \
      --output-dir output/sf_bikeshare/demand_estimation_build
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_demand_minute import run  # noqa: E402

if __name__ == "__main__":
    run(case="hybrid")
