# run_study.py
# Full dependability sweep: violation rate vs packet-loss rate,
# at swarm sizes N = 8, 16, 32. Saves results to data/ for plotting.
# This is the main experiment that produces the headline figure.

import numpy as np
import csv
import os
from run_episode import run_episode

os.makedirs("data", exist_ok=True)

LOSS_RATES = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
SWARM_SIZES = [8, 16, 32]
SEEDS = 200                 # episodes per (N, loss) cell; more = tighter CIs
BURST_LEN = 5

rows = []
for N in SWARM_SIZES:
    for loss in LOSS_RATES:
        violations = 0
        for s in range(SEEDS):
            r = run_episode(N=N, loss_rate=loss, burst_len=BURST_LEN, seed=s)
            violations += r["violated"]
        rate = violations / SEEDS
        # Wald 95% confidence interval for a proportion.
        se = np.sqrt(rate * (1 - rate) / SEEDS)
        ci = 1.96 * se
        rows.append({"N": N, "loss_rate": loss,
                     "violation_rate": round(rate, 4),
                     "ci95": round(ci, 4),
                     "n_seeds": SEEDS})
        print(f"N={N:2d}  loss={loss:.2f}  violation_rate={rate:.2f} +/- {ci:.2f}")

# Save to CSV for plotting and for the paper.
with open("data/study_results.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["N", "loss_rate", "violation_rate", "ci95", "n_seeds"])
    writer.writeheader()
    writer.writerows(rows)

print("\nSaved to data/study_results.csv")