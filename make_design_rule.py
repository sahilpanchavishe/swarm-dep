# make_design_rule.py
# Sweeps the fail-safe timeout and measures the safety vs. nuisance trade-off.
# Produces the design-rule figure: how to choose the timeout.

import numpy as np
import csv
import matplotlib.pyplot as plt
from run_episode_supervised import run_episode_supervised

N = 8
LOSS = 0.2
TIMEOUTS = [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0]
SEEDS = 50

safety_rate = []     # fraction of episodes with a safety violation
nuisance_rate = []   # avg needless stops per episode (per robot)

for timeout in TIMEOUTS:
    viol = sum(run_episode_supervised(N, LOSS, timeout, seed=s, issue_stop=True)["violated"]
               for s in range(SEEDS))
    nuis = sum(run_episode_supervised(N, LOSS, timeout, seed=s, issue_stop=False)["nuisance_stops"]
               for s in range(SEEDS))
    safety_rate.append(viol / SEEDS * 100)            # % of episodes unsafe
    nuisance_rate.append(nuis / SEEDS / N * 100)      # % of robots needlessly stopped
    print(f"timeout={timeout:.2f}s  safety_viol={viol/SEEDS*100:5.1f}%  "
          f"nuisance={nuis/SEEDS/N*100:5.1f}%")

# Save the numbers.
with open("data/design_rule.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["timeout_s", "safety_violation_pct", "nuisance_stop_pct"])
    for t, s, n in zip(TIMEOUTS, safety_rate, nuisance_rate):
        w.writerow([t, round(s, 2), round(n, 2)])

# Plot both curves against timeout.
fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(TIMEOUTS, safety_rate, "o-", color="tab:red", label="Safety violations (%)")
ax.plot(TIMEOUTS, nuisance_rate, "s-", color="tab:blue", label="Nuisance stops (%)")
ax.set_xlabel("Fail-safe timeout (s)")
ax.set_ylabel("Rate (%)")
ax.set_title(f"Fail-safe design rule (N={N}, packet loss={int(LOSS*100)}%)")
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()
plt.savefig("data/figure_design_rule.png", dpi=200)
print("\nSaved data/figure_design_rule.png and data/design_rule.csv")
plt.show()