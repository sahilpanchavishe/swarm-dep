# make_figure.py
# Plots the headline figure: STOP-violation rate vs packet-loss rate,
# one curve per swarm size, with 95% confidence-interval bands.

import csv
import matplotlib.pyplot as plt
from collections import defaultdict

# Load results.
data = defaultdict(lambda: {"loss": [], "rate": [], "ci": []})
with open("data/study_results.csv") as f:
    for row in csv.DictReader(f):
        N = int(row["N"])
        data[N]["loss"].append(float(row["loss_rate"]) * 100)   # as percent
        data[N]["rate"].append(float(row["violation_rate"]) * 100)
        data[N]["ci"].append(float(row["ci95"]) * 100)

fig, ax = plt.subplots(figsize=(7, 5))
colors = {8: "tab:blue", 16: "tab:orange", 32: "tab:green"}

for N in sorted(data.keys()):
    d = data[N]
    loss = d["loss"]; rate = d["rate"]; ci = d["ci"]
    ax.plot(loss, rate, "o-", color=colors[N], label=f"N = {N}")
    lower = [r - c for r, c in zip(rate, ci)]
    upper = [r + c for r, c in zip(rate, ci)]
    ax.fill_between(loss, lower, upper, color=colors[N], alpha=0.15)

ax.set_xlabel("Packet loss rate (%)")
ax.set_ylabel("STOP-requirement violation rate (%)")
ax.set_title("Swarm dependability under packet loss and gesture errors")
ax.set_ylim(0, 105)
ax.grid(True, alpha=0.3)
ax.legend(title="Swarm size")
plt.tight_layout()
plt.savefig("data/figure_violation_vs_loss.png", dpi=200)
print("Saved data/figure_violation_vs_loss.png")
plt.show()