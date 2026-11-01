# run_study_v2.py - corrected sweep. Channel-only violation P_loss is simulated (misread off);
# the shared misread is a single swarm-wide event, so total = p + (1-p) * P_loss exactly.
# Writes data/study_v2.csv. Uses all CPU cores.
import csv, json, itertools, math
from multiprocessing import Pool
from sim_v2 import run_episode_v2, analytic_violation
PM = json.load(open("data/misread_vs_window.json"))["stop"][0]["p"]
SEEDS = 400
GRID = list(itertools.product([0.0, 0.5], [0.033, 0.1, 0.3, 1.0],
                              [0.0, 0.05, 0.1, 0.2, 0.3, 0.4], [8, 16, 32]))
def cell(args):
    common, burst, loss, N = args
    k = sum(run_episode_v2(N, loss, burst, s, 0.0, common=common)["violated"] for s in range(SEEDS))
    pl = k / SEEDS; se = math.sqrt(pl * (1 - pl) / SEEDS)
    a = analytic_violation(N, loss, burst, PM)[0] if common == 0 else ""
    return {"common": common, "burst_s": burst, "loss": loss, "N": N,
            "p_loss_violation": round(pl, 4), "ci95_loss": round(1.96 * se, 4),
            "total_violation": round(PM + (1 - PM) * pl, 4), "analytic_total": a if a == "" else round(a, 4),
            "p_misread": round(PM, 4), "seeds": SEEDS}
if __name__ == "__main__":
    with Pool() as p: rows = p.map(cell, GRID)
    with open("data/study_v2.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("done", len(rows))
