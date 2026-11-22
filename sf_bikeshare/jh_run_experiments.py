"""Extra experiments for the DBA5103 report (Sections 6.4 and 6.5). Run from the repository root.

penalty : failed-return penalty sensitivity (optimizer re-solved for each penalty)
losttrip: minimize unmet pickups + failed returns subject to a daily redistribution budget
Usage:
  python sf_bikeshare/jh_run_experiments.py penalty  <demand.csv> <out.csv> [0,0.3,0.5,0.65,0.88,4.5]
  python sf_bikeshare/jh_run_experiments.py losttrip <demand.csv> <out.csv>
Requires hj_optimization_model.py and hj_policy_routing.py (Hong Jin, PR #1) in sf_bikeshare/.
"""
import sys
from types import SimpleNamespace
import numpy as np
import pandas as pd

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from jh_lost_trips_model import read_day, solve_allocation          # noqa: E402
from hj_policy_routing import equal_occupancy_rule, evaluate_policy  # noqa: E402

BASE = 'output/sf_bikeshare/model_inputs_v3/'
DATES = pd.date_range('2015-04-06', '2015-04-19').strftime('%Y-%m-%d').tolist()
COST = dict(fixed=60.0, handling=1.0, km_cost=0.30, avg_load=15.0)
VAL = dict(member_value=0.88, casual_value=4.50)
exp, demand, out = sys.argv[1], sys.argv[2], sys.argv[3]
PENALTIES = tuple(float(x) for x in (sys.argv[4] if len(sys.argv) > 4 else '0,0.3,0.5,0.65,0.88,4.5').split(','))


rows = []
for date in DATES:
    reader = SimpleNamespace(stations=BASE + 'station.csv', opening=BASE + 'opening_inventory_daily.csv',
                             demand=demand, distances=BASE + 'station_distances.csv', date=date, hours=24)
    ids, caps, opening, sub, cas, ret, dist = read_day(reader)
    share_cas = np.divide(cas, sub + cas, out=np.zeros_like(cas), where=(sub + cas) > 0)
    pos = {sid: i for i, sid in enumerate(ids)}

    def run_eval(name, transfers, penalty, extra):
        summ, _, stock = evaluate_policy(name, ids, caps, opening, sub, cas, ret, dist, transfers,
                                         throughput=15, max_neighbors=5, **COST, **VAL,
                                         failed_return_penalty=penalty)
        ci = stock.station_id.map(pos).to_numpy()
        hi = stock.hour.to_numpy()
        summ['casual_served'] = float((stock.served_pickups.to_numpy() * share_cas[ci, hi]).sum())
        summ.update(date=date, **extra)
        rows.append(summ)

    if exp == 'penalty':
        rule = equal_occupancy_rule(ids, caps, opening, sub, cas, ret, dist, throughput=15, max_neighbors=5, tolerance=0.10)
        for p in PENALTIES:
            opt = solve_allocation(ids, caps, opening, sub, cas, ret, dist, **COST, **VAL, failed_return_penalty=p,
                                   throughput=15, max_trucks=1, max_neighbors=5, time_limit=30)
            run_eval('no_rebalancing', None, p, dict(penalty=p))
            run_eval('rule_based', rule, p, dict(penalty=p))
            run_eval('optimized', opt.transfers, p, dict(penalty=p, gap=opt.summary.get('solver_gap'), status=opt.summary.get('solver_status')))
            print(date, p, opt.summary.get('bikes_moved'), opt.summary.get('solver_gap'), flush=True)
    else:
        run_eval('no_rebalancing', None, 0.88, dict(budget=0))
        for bud in (75, 90, 120, 150, 200):
            opt = solve_allocation(ids, caps, opening, sub, cas, ret, dist, **COST, **VAL, failed_return_penalty=0.88,
                                   throughput=15, max_trucks=1, max_neighbors=5, time_limit=30,
                                   mode='lost_trips', budget=bud)
            run_eval('lost_trip_min', opt.transfers, 0.88, dict(budget=bud, gap=opt.summary.get('solver_gap'), status=opt.summary.get('solver_status')))
            print(date, bud, opt.summary.get('bikes_moved'), opt.summary.get('solver_gap'), flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
print('done')
