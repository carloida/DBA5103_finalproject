#!/usr/bin/env python3
"""Case A (proposed base): historical availability-adjusted demand.

Thin wrapper around build_demand_minute.py --case historical; see that module for the method,
validation and outputs. Example (from the repository root):
  python sf_bikeshare/build_demand_historical.py \
      --hourly output/sf_bikeshare/model_inputs_v3/station_hour_observed.csv.gz \
      --minute-dir output/sf_bikeshare/demand_estimation_inputs_v3 \
      --output-dir output/sf_bikeshare/demand_estimation_build
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_demand_minute import run  # noqa: E402

if __name__ == "__main__":
    run(case="historical")
