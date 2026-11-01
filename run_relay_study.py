# run_relay_study.py - broadcast vs peer relay of STOP, across where bursts occur (rx_fraction),
# burst length, loss rate and swarm size. Channel-only violation is simulated; the shared misread
# (which no relay can fix) is added exactly: total = p + (1-p) * P_loss. Writes data/relay_study.csv
import csv, json, itertools, math
from multiprocessing import Pool
from sim_v2 import run_episode_relay
PM = json.load(open("data/misread_vs_window.json"))["stop"][0]["p"]
SEEDS = 300
GRID = [(relay, f, b, l, N) for relay in (False, True)
        for f in (0.0, 0.25, 0.5, 0.75, 1.0)
        for b in (0.1, 0.3, 1.0) for l in (0.05, 0.1, 0.2) for N in (8, 16, 32)]
def cell(a):
    relay, f, b, l, N = a
    k = sum(run_episode_relay(N, l, b, s, 0.0, rx_fraction=f, relay=relay)["violated"] for s in range(SEEDS))
    pl = k / SEEDS
    return {"relay": int(relay), "rx_fraction": f, "burst_s": b, "loss": l, "N": N,
            "p_loss_violation": round(pl, 4), "ci95": round(1.96 * math.sqrt(pl * (1 - pl) / SEEDS), 4),
            "total_violation": round(PM + (1 - PM) * pl, 4), "seeds": SEEDS}
if __name__ == "__main__":
    with Pool() as p: rows = p.map(cell, GRID)
    with open("data/relay_study.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("done", len(rows))
