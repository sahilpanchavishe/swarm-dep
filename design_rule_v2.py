# design_rule_v2.py - fail-safe heartbeat timeout under bursty loss, with 30 Hz rebroadcast.
# Analytic bound: a robot stuck in a loss burst still stops in time iff
#   timeout <= T_STOP - recognition_delay - V_MAX/A_MAX   ("slack").
# Below the bound the fail-safe removes loss-driven violations; the shared misread remains
# (no packet is missing, so no timeout can catch it). The price is nuisance stops, set by how
# often bursts exceed the timeout. Writes data/design_rule_v2.csv
import csv, json, itertools, math
from multiprocessing import Pool
from sim_v2 import run_episode_v2
from robot import V_MAX, A_MAX
from safety import T_STOP
PM = json.load(open("data/misread_vs_window.json"))["stop"][0]["p"]
SLACK = T_STOP - 0.033 - V_MAX / A_MAX
N, SEEDS = 8, 300
GRID = list(itertools.product([0.1, 0.3, 1.0], [0.05, 0.1, 0.2],
                              [None, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.7]))
def cell(a):
    burst, loss, timeout = a
    pl = sum(run_episode_v2(N, loss, burst, s, 0.0, timeout_s=timeout)["violated"] for s in range(SEEDS)) / SEEDS
    nu = sum(run_episode_v2(N, loss, burst, s + 10**6, 0.0, timeout_s=timeout, issue_stop=False)["nuisance_stops"]
             for s in range(SEEDS)) / (SEEDS * N)
    return {"burst_s": burst, "loss": loss, "timeout_s": "none" if timeout is None else timeout,
            "total_violation": round(PM + (1 - PM) * pl, 4), "loss_violation": round(pl, 4),
            "nuisance_per_robot_3s": round(nu, 4), "slack_bound_s": round(SLACK, 3)}
if __name__ == "__main__":
    with Pool() as p: rows = p.map(cell, GRID)
    with open("data/design_rule_v2.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"done; analytic timeout bound {SLACK:.3f} s")
